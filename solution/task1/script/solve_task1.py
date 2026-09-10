"""Problem 1 numerical model for the medicinal-material drying problem.

The material is represented by a one-dimensional, axisymmetric radial cylinder.
Temperature and moisture are solved independently with a cell-centred-at-node
finite-volume discretisation.  The nodes include both ``r=0`` and ``r=R``;
the first and last nodes therefore represent half control volumes.

This stage intentionally only returns the one-second solution arrays.  Writing
the final CSV is handled by a later stage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp


# Geometry and initial state (SI units internally).
RADIUS_M = 0.02
LENGTH_M = 0.25  # retained as a documented problem parameter; it cancels in 1-D radial balance
BASE_DR_M = 0.000125
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE_KGKG = 2.55

# Problem 1 material and transfer parameters.
DENSITY_KG_M3 = 820.0
HEAT_CAPACITY_J_KG_K = 2600.0
THERMAL_CONDUCTIVITY_W_M_K = 0.36
HEAT_TRANSFER_W_M2_K = 25.0
MASS_TRANSFER_M_S = 8.0e-7

KEY_TIMES_S = np.array([100, 300, 600, 900, 1200, 1500, 1800], dtype=float)
KEY_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
)


def load_air_data(path: str | Path = DEFAULT_DATA_PATH) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read the trusted boundary data from attachment 1.

    The workbook's first sheet contains the three columns ``时间``, ``温度`` and
    ``水分浓度``.  Values are sorted by time and are returned as numeric arrays
    for piecewise-linear interpolation.
    """

    data_path = Path(path)
    frame = pd.read_excel(data_path)
    # Strip accidental surrounding spaces while preserving the actual Chinese
    # column names used by the attachment.
    column_map = {str(column).strip(): column for column in frame.columns}
    required = ("时间", "温度", "水分浓度")
    missing = [column for column in required if column not in column_map]
    if missing:
        raise ValueError(
            f"附件1缺少必需列: {missing}; 实际列为 {list(frame.columns)!r}"
        )

    selected = frame[[column_map[column] for column in required]].copy()
    selected.columns = required
    for column in required:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")

    time_s = selected["时间"].to_numpy(dtype=float)
    air_temperature_C = selected["温度"].to_numpy(dtype=float)
    air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)

    if time_s.size < 2 or np.any(np.diff(time_s) <= 0):
        raise ValueError("附件1的时间列必须包含至少两个严格递增的时间点")
    if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
        raise ValueError("附件1包含非有限数值")

    return time_s, air_temperature_C, air_moisture_kgkg


def radial_grid(radius_m: float = RADIUS_M, dr: float = BASE_DR_M) -> np.ndarray:
    """Return a uniform node grid including exactly ``0`` and ``radius_m``."""

    if radius_m <= 0.0 or dr <= 0.0:
        raise ValueError("半径和空间步长必须为正")
    n_intervals = int(round(radius_m / dr))
    if not np.isclose(n_intervals * dr, radius_m, rtol=0.0, atol=1.0e-12):
        raise ValueError("当前有限体积网格要求半径可由整数个 dr 划分")
    return np.linspace(0.0, radius_m, n_intervals + 1)


def control_volume_geometry(
    radius_m: float, dr: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return radial face positions and ``∫_CV r dr`` for every node.

    With a node at each control-volume centre, the end nodes have half-width
    control volumes.  The radial measure is kept without the common ``2π``
    factor, which cancels from both sides of the radial balance.
    """

    radii = radial_grid(radius_m, dr)
    faces = 0.5 * (radii[:-1] + radii[1:])
    measure = np.empty(radii.size, dtype=float)
    measure[0] = 0.5 * faces[0] ** 2
    measure[1:-1] = 0.5 * (faces[1:] ** 2 - faces[:-1] ** 2)
    measure[-1] = 0.5 * (radius_m**2 - faces[-1] ** 2)
    return radii, faces, measure


def moisture_diffusivity(moisture_kgkg: np.ndarray) -> np.ndarray:
    """Evaluate the positive empirical diffusivity ``D(C)`` in m²/s."""

    # Physical solutions have C>0.  The lower bound only protects a nonlinear
    # RHS evaluation if a solver trial state briefly crosses zero; it is not an
    # r=0 treatment and has no effect on the returned physical solution.
    concentration = np.maximum(np.asarray(moisture_kgkg, dtype=float), 1.0e-12)
    return 7.0e-9 * np.exp(-0.89 / concentration)


def _piecewise_linear(values_t: np.ndarray, values: np.ndarray) -> Callable[[float], float]:
    """Create a scalar piecewise-linear interpolator with endpoint hold."""

    def interpolate(time_s: float) -> float:
        return float(np.interp(time_s, values_t, values))

    return interpolate


def _temperature_rhs(
    time_s: float,
    temperature_C: np.ndarray,
    radius_m: np.ndarray,
    faces_m: np.ndarray,
    radial_measure_m2: np.ndarray,
    air_temperature: Callable[[float], float],
    dr: float,
) -> np.ndarray:
    """Finite-volume RHS for the radial heat equation.

    The outward face flux is ``k*r*dT/dr``.  At the surface the Robin
    condition is used directly as ``R*h*(T_air-T_surface)``; hence a hotter
    air stream gives a positive inward contribution to the surface control
    volume.
    """

    temperature = np.asarray(temperature_C, dtype=float)
    internal_flux = (
        THERMAL_CONDUCTIVITY_W_M_K
        * faces_m
        * np.diff(temperature)
        / dr
    )
    divergence = np.empty_like(temperature)

    # At r=0, the inner face area is zero.  This is the exact finite-volume
    # centre balance and is equivalent to the axisymmetric limit
    # 4*k*(T_1-T_0)/dr², with no division by r or epsilon regularisation.
    divergence[0] = internal_flux[0]
    divergence[1:-1] = internal_flux[1:] - internal_flux[:-1]

    # k*dT/dr = h*(T_air-T_surface), in the outward-flux convention.
    surface_flux = radius_m[-1] * HEAT_TRANSFER_W_M2_K * (
        air_temperature(time_s) - temperature[-1]
    )
    divergence[-1] = surface_flux - internal_flux[-1]
    return divergence / (DENSITY_KG_M3 * HEAT_CAPACITY_J_KG_K * radial_measure_m2)


def _moisture_rhs(
    time_s: float,
    moisture_kgkg: np.ndarray,
    radius_m: np.ndarray,
    faces_m: np.ndarray,
    radial_measure_m2: np.ndarray,
    air_moisture: Callable[[float], float],
    dr: float,
) -> np.ndarray:
    """Finite-volume RHS for nonlinear radial moisture diffusion."""

    moisture = np.asarray(moisture_kgkg, dtype=float)
    node_diffusivity = moisture_diffusivity(moisture)
    # Arithmetic averaging is positive for positive nodal D and is consistent
    # with the face-centred flux used by the finite-volume balance.
    face_diffusivity = 0.5 * (node_diffusivity[:-1] + node_diffusivity[1:])
    internal_flux = face_diffusivity * faces_m * np.diff(moisture) / dr
    divergence = np.empty_like(moisture)

    # Zero inner-face flux is the exact r=0 symmetry condition.
    divergence[0] = internal_flux[0]
    divergence[1:-1] = internal_flux[1:] - internal_flux[:-1]

    # -D*dC/dr = hm*(C_surface-C_air) gives the outward-flux form
    # D*dC/dr = hm*(C_air-C_surface).
    surface_flux = radius_m[-1] * MASS_TRANSFER_M_S * (
        air_moisture(time_s) - moisture[-1]
    )
    divergence[-1] = surface_flux - internal_flux[-1]
    return divergence / radial_measure_m2


def solve_task1(
    data_path: str | Path = DEFAULT_DATA_PATH,
    t_end_s: float = 1800.0,
    output_dt_s: float = 1.0,
    dr_m: float = BASE_DR_M,
    rtol: float = 1.0e-8,
    atol: float = 1.0e-10,
    max_step_s: float = 30.0,
) -> dict[str, np.ndarray | object]:
    """Solve Problem 1 and return arrays sampled every ``output_dt_s``.

    Returned arrays have shape ``(n_times, n_radial_nodes)`` for temperature
    and moisture.  No result file is written by this function.
    """

    if t_end_s <= 0.0 or output_dt_s <= 0.0:
        raise ValueError("终止时间和输出时间步长必须为正")
    if rtol <= 0.0 or atol <= 0.0 or max_step_s <= 0.0:
        raise ValueError("求解器容差和最大步长必须为正")

    data_t, data_air_T, data_air_C = load_air_data(data_path)
    if t_end_s > data_t[-1]:
        raise ValueError(
            f"附件1边界数据只覆盖到 {data_t[-1]:g} s，无法计算到 {t_end_s:g} s"
        )

    radii_m, faces_m, radial_measure_m2 = control_volume_geometry(RADIUS_M, dr_m)
    n_nodes = radii_m.size
    if not np.all(radial_measure_m2 > 0.0):
        raise RuntimeError("有限体积控制体积径向测度必须为正")

    # Include t_end exactly while retaining the requested one-second output
    # grid for the standard run.
    n_outputs = int(np.floor(t_end_s / output_dt_s + 1.0e-10))
    output_times = output_dt_s * np.arange(n_outputs + 1, dtype=float)
    if output_times[-1] < t_end_s - 1.0e-10:
        output_times = np.append(output_times, t_end_s)
    else:
        output_times[-1] = t_end_s

    air_temperature = _piecewise_linear(data_t, data_air_T)
    air_moisture = _piecewise_linear(data_t, data_air_C)

    initial_state = np.concatenate(
        (
            np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float),
            np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float),
        )
    )

    def rhs(time_s: float, state: np.ndarray) -> np.ndarray:
        temperature = state[:n_nodes]
        moisture = state[n_nodes:]
        d_temperature = _temperature_rhs(
            time_s,
            temperature,
            radii_m,
            faces_m,
            radial_measure_m2,
            air_temperature,
            dr_m,
        )
        d_moisture = _moisture_rhs(
            time_s,
            moisture,
            radii_m,
            faces_m,
            radial_measure_m2,
            air_moisture,
            dr_m,
        )
        return np.concatenate((d_temperature, d_moisture))

    result = solve_ivp(
        rhs,
        (0.0, float(t_end_s)),
        initial_state,
        method="BDF",
        t_eval=output_times,
        rtol=rtol,
        atol=atol,
        max_step=max_step_s,
    )
    if not result.success:
        raise RuntimeError(f"问题1 BDF 求解失败: {result.message}")
    if result.y.shape != (2 * n_nodes, output_times.size):
        raise RuntimeError("求解器输出形状与网格不一致")

    return {
        "time_s": result.t,
        "radius_m": radii_m,
        "temperature_C": result.y[:n_nodes].T,
        "moisture_kgkg": result.y[n_nodes:].T,
        "solver_result": result,
    }


def validate_solution(solution: dict[str, np.ndarray | object]) -> None:
    """Run the direct numerical and physical checks for the computed result."""

    required = ("time_s", "radius_m", "temperature_C", "moisture_kgkg")
    if any(key not in solution for key in required):
        raise ValueError("问题1结果缺少必需数组")

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_m = np.asarray(solution["radius_m"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    if time_s.ndim != 1 or radius_m.ndim != 1 or time_s.size < 2 or radius_m.size < 2:
        raise ValueError("问题1时间和半径网格形状错误")
    expected_shape = (time_s.size, radius_m.size)
    if temperature.shape != expected_shape or moisture.shape != expected_shape:
        raise ValueError(
            f"问题1场数组 shape 错误: 期望 {expected_shape}, "
            f"实际 T={temperature.shape}, C={moisture.shape}"
        )
    if not all(np.all(np.isfinite(array)) for array in (time_s, radius_m, temperature, moisture)):
        raise ValueError("问题1结果包含 NaN 或 Inf")
    if np.any(np.diff(time_s) <= 0.0) or np.any(np.diff(radius_m) <= 0.0):
        raise ValueError("问题1时间和半径必须严格递增")

    if not np.allclose(temperature[0], INITIAL_TEMPERATURE_C, atol=1.0e-8, rtol=0.0):
        raise ValueError("问题1初始温度未全场等于 28 C")
    if not np.allclose(moisture[0], INITIAL_MOISTURE_KGKG, atol=1.0e-8, rtol=0.0):
        raise ValueError("问题1初始水分未全场等于 2.55 kg/kg")
    if np.min(moisture) < 0.0:
        raise ValueError(f"问题1水分出现负值: {moisture.min():.6g} kg/kg")

    temperature_step_min = float(np.min(np.diff(temperature, axis=0)))
    moisture_step_max = float(np.max(np.diff(moisture, axis=0)))
    if temperature_step_min < -1.0e-5:
        raise ValueError(f"问题1温度逐时明显下降: 最小变化 {temperature_step_min:.6g} C")
    if moisture_step_max > 1.0e-5:
        raise ValueError(f"问题1水分逐时明显增加: 最大变化 {moisture_step_max:.6g} kg/kg")

    if temperature[-1, -1] <= temperature[-1, 0]:
        raise ValueError("问题1末时刻表面温度未高于中心")
    if moisture[-1, -1] >= moisture[-1, 0]:
        raise ValueError("问题1末时刻表面水分未低于中心")

    dr_m = float(np.mean(np.diff(radius_m)))
    if not np.allclose(np.diff(radius_m), dr_m, atol=1.0e-12, rtol=0.0):
        raise ValueError("问题1半径网格必须均匀以计算体积加权平均")
    radial_measure = control_volume_geometry(radius_m[-1], dr_m)[2]
    average_initial = float(np.dot(radial_measure, moisture[0]) / radial_measure.sum())
    average_final = float(np.dot(radial_measure, moisture[-1]) / radial_measure.sum())
    if average_final >= average_initial:
        raise ValueError(
            f"问题1体积加权平均水分未下降: {average_initial:.6g} -> {average_final:.6g}"
        )


def print_key_samples(solution: dict[str, np.ndarray | object]) -> None:
    """Print temperature and moisture at the requested time/radius points."""

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_m = np.asarray(solution["radius_m"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    time_indices = np.searchsorted(time_s, KEY_TIMES_S, side="left")
    radius_indices = np.searchsorted(radius_m, KEY_RADII_CM * 1.0e-2, side="left")
    if np.any(time_indices >= time_s.size) or np.any(radius_indices >= radius_m.size):
        raise ValueError("问题1关键采样点不在结果网格内")
    if not np.allclose(time_s[time_indices], KEY_TIMES_S, atol=1.0e-12, rtol=0.0):
        raise ValueError("问题1关键时间未命中精确输出节点")
    if not np.allclose(
        radius_m[radius_indices], KEY_RADII_CM * 1.0e-2, atol=1.0e-12, rtol=0.0
    ):
        raise ValueError("问题1关键半径未命中精确空间节点")
    print("temperature_C (columns: radius_cm=" + ",".join(f"{r:g}" for r in KEY_RADII_CM) + ")")
    for i, target in zip(time_indices, KEY_TIMES_S):
        values = " ".join(f"{value:.4f}" for value in temperature[i, radius_indices])
        print(f"t={target:4.0f} s | {values}")
    print("moisture_kgkg (columns: radius_cm=" + ",".join(f"{r:g}" for r in KEY_RADII_CM) + ")")
    for i, target in zip(time_indices, KEY_TIMES_S):
        values = " ".join(f"{value:.4f}" for value in moisture[i, radius_indices])
        print(f"t={target:4.0f} s | {values}")


def run_grid_sensitivity(
    base_solution: dict[str, np.ndarray | object],
) -> dict[str, object]:
    """Compare the base grid with a refined ``dr=0.0000625 m`` grid."""

    refined_solution = solve_task1(
        t_end_s=1800.0,
        output_dt_s=1.0,
        dr_m=0.0000625,
        rtol=1.0e-8,
        atol=1.0e-10,
        max_step_s=30.0,
    )
    validate_solution(refined_solution)
    comparison_times = KEY_TIMES_S
    comparison_radii_cm = KEY_RADII_CM
    target_radii_m = comparison_radii_cm * 1.0e-2

    def exact_indices(grid: np.ndarray, targets: np.ndarray, label: str) -> np.ndarray:
        indices = np.searchsorted(grid, targets, side="left")
        if np.any(indices >= grid.size) or not np.allclose(
            grid[indices[indices < grid.size]],
            targets[indices < grid.size],
            atol=1.0e-12,
            rtol=0.0,
        ):
            raise ValueError(f"{label}缺少指定的精确比较节点")
        return indices

    base_time = np.asarray(base_solution["time_s"], dtype=float)
    refined_time = np.asarray(refined_solution["time_s"], dtype=float)
    base_radius = np.asarray(base_solution["radius_m"], dtype=float)
    refined_radius = np.asarray(refined_solution["radius_m"], dtype=float)
    base_indices = (
        exact_indices(base_time, comparison_times, "基准时间网格"),
        exact_indices(base_radius, target_radii_m, "基准半径网格"),
    )
    refined_indices = (
        exact_indices(refined_time, comparison_times, "细化时间网格"),
        exact_indices(refined_radius, target_radii_m, "细化半径网格"),
    )

    def max_difference(key: str) -> tuple[float, dict[str, float]]:
        base_values = np.asarray(base_solution[key], dtype=float)[np.ix_(*base_indices)]
        refined_values = np.asarray(refined_solution[key], dtype=float)[
            np.ix_(*refined_indices)
        ]
        difference = np.abs(refined_values - base_values)
        location = np.unravel_index(int(np.argmax(difference)), difference.shape)
        return float(difference[location]), {
            "time_s": float(comparison_times[location[0]]),
            "radius_cm": float(comparison_radii_cm[location[1]]),
        }

    max_temperature_difference, temperature_location = max_difference("temperature_C")
    max_moisture_difference, moisture_location = max_difference("moisture_kgkg")
    print(
        "grid sensitivity (dr=0.0000625 m vs 0.000125 m): "
        f"max |delta T|={max_temperature_difference:.10e} C at "
        f"t={temperature_location['time_s']:.0f} s, "
        f"r={temperature_location['radius_cm']:g} cm; "
        f"max |delta C|={max_moisture_difference:.10e} kg/kg at "
        f"t={moisture_location['time_s']:.0f} s, "
        f"r={moisture_location['radius_cm']:g} cm"
    )
    return {
        "max_abs_temperature_difference_C": max_temperature_difference,
        "max_abs_moisture_difference_kgkg": max_moisture_difference,
        "temperature_max_location": temperature_location,
        "moisture_max_location": moisture_location,
    }


if __name__ == "__main__":
    try:
        result = solve_task1()
        validate_solution(result)
        print("validation: PASS")
        print_key_samples(result)
        run_grid_sensitivity(result)
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"问题1求解/验证失败: {error}") from error
