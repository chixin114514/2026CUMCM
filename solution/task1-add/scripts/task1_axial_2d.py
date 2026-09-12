"""Independent 2-D axial-temperature check for Problem 1.

This module is deliberately isolated from ``solution/task1``.  It solves only
the constant-property temperature equation on the axisymmetric half-domain
``0 <= r <= R`` and ``0 <= z <= L/2``.  The formal one-dimensional CSV is
read-only comparison data; the formal solver is never called to regenerate it.

The spatial discretisation is a node-centred, conservative finite-volume
operator.  The time integrator is Crank--Nicolson.  The only boundary data are
the attachment-1 air-temperature values, interpolated with the same
``load_air_data`` and ``numpy.interp`` convention as Problem 1.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
    }
)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse import linalg as spla


# ---------------------------------------------------------------------------
# Paths and fixed Problem-1 parameters.  These are intentionally explicit so
# that this experiment cannot accidentally inherit state-dependent properties
# or a water/moisture equation from another task.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
ADD_DIR = ROOT / "solution" / "task1-add"
FORMAL_SCRIPT_DIR = ROOT / "solution" / "task1" / "script"
FORMAL_RESULT_PATH = ROOT / "solution" / "task1" / "answer" / "task1_result.csv"
DATA_DIR = ADD_DIR / "data"
FIGURE_DIR = ADD_DIR / "figures"

RADIUS_M = 0.02
LENGTH_M = 0.25
HALF_LENGTH_M = LENGTH_M / 2.0
INITIAL_TEMPERATURE_C = 28.0
DENSITY_KG_M3 = 820.0
HEAT_CAPACITY_J_KG_K = 2600.0
THERMAL_CONDUCTIVITY_W_M_K = 0.36
HEAT_TRANSFER_W_M2_K = 25.0

KEY_TIMES_S = np.array([100, 300, 600, 900, 1200, 1500, 1800], dtype=float)
KEY_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
AXIAL_PROFILE_RADII_CM = np.array([0.0, 1.5], dtype=float)
AXIAL_SAMPLE_Z_CM = np.array([0.0, 0.25, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 12.5])
END_EFFECT_THRESHOLD_C = 0.1


def _load_formal_air_loader() -> tuple[Callable, Path]:
    """Import the existing Problem-1 attachment loader without changing it."""

    script_dir_text = str(FORMAL_SCRIPT_DIR)
    if script_dir_text not in sys.path:
        sys.path.insert(0, script_dir_text)
    formal_module = importlib.import_module("solve_task1")
    return formal_module.load_air_data, Path(formal_module.DEFAULT_DATA_PATH)


@dataclass(frozen=True)
class Grid2D:
    """Uniform node grid and the metric measures of its half-cell controls."""

    r_m: np.ndarray
    z_m: np.ndarray
    r_faces_m: np.ndarray
    radial_measure_m2: np.ndarray
    axial_measure_m: np.ndarray
    dr_m: float
    dz_m: float

    @property
    def nr(self) -> int:
        return self.r_m.size

    @property
    def nz(self) -> int:
        return self.z_m.size

    @property
    def size(self) -> int:
        return self.nr * self.nz


@dataclass(frozen=True)
class LinearSystem:
    """Constant linear spatial operator and the time-dependent boundary source."""

    operator: sparse.csr_matrix
    boundary_source: np.ndarray


@dataclass(frozen=True)
class CNRun:
    """Selected fields returned by a CN run."""

    grid: Grid2D
    dt_s: float
    fields_C: Mapping[int, np.ndarray]
    trace_times_s: np.ndarray | None = None
    trace_temperature_C: np.ndarray | None = None


def _uniform_nodes(length_m: float, step_m: float, label: str) -> np.ndarray:
    if length_m <= 0.0 or step_m <= 0.0:
        raise ValueError(f"{label} 的长度和步长必须为正")
    intervals = int(round(length_m / step_m))
    if intervals < 1 or not np.isclose(
        intervals * step_m, length_m, rtol=0.0, atol=1.0e-12
    ):
        raise ValueError(f"{label} 必须可以由整数个均匀步长划分")
    return np.linspace(0.0, length_m, intervals + 1)


def build_grid(dr_m: float, dz_m: float) -> Grid2D:
    """Build node locations and cylindrical half-control-volume measures."""

    r_m = _uniform_nodes(RADIUS_M, dr_m, "径向区域")
    z_m = _uniform_nodes(HALF_LENGTH_M, dz_m, "轴向半域")
    actual_dr = float(r_m[1] - r_m[0])
    actual_dz = float(z_m[1] - z_m[0])
    r_faces_m = 0.5 * (r_m[:-1] + r_m[1:])

    radial_measure = np.empty(r_m.size, dtype=float)
    radial_measure[0] = 0.5 * r_faces_m[0] ** 2
    radial_measure[1:-1] = 0.5 * (
        r_faces_m[1:] ** 2 - r_faces_m[:-1] ** 2
    )
    radial_measure[-1] = 0.5 * (RADIUS_M**2 - r_faces_m[-1] ** 2)

    axial_measure = np.full(z_m.size, actual_dz, dtype=float)
    axial_measure[0] = 0.5 * actual_dz
    axial_measure[-1] = 0.5 * actual_dz

    if not np.all(radial_measure > 0.0) or not np.all(axial_measure > 0.0):
        raise RuntimeError("二维控制体积测度必须全部为正")
    return Grid2D(
        r_m=r_m,
        z_m=z_m,
        r_faces_m=r_faces_m,
        radial_measure_m2=radial_measure,
        axial_measure_m=axial_measure,
        dr_m=actual_dr,
        dz_m=actual_dz,
    )


def _index(i: int, j: int, nz: int) -> int:
    """Flatten ``(radial index, axial index)`` in C order."""

    return i * nz + j


def assemble_2d_system(grid: Grid2D, z0_convection: bool = True) -> LinearSystem:
    """Assemble the conservative 2-D temperature operator.

    The operator has units of 1/s and a negative diagonal.  Its off-diagonal
    entries are conductive couplings.  ``boundary_source`` multiplies the
    interpolated air temperature and contains only the side surface and, when
    requested, the real ``z=0`` end face.  The ``z=L/2`` face is always the
    symmetry plane and has zero flux.
    """

    nr, nz = grid.nr, grid.nz
    n = grid.size
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    boundary_source = np.zeros(n, dtype=float)
    rho_cp = DENSITY_KG_M3 * HEAT_CAPACITY_J_KG_K

    for i in range(nr):
        radial_measure = grid.radial_measure_m2[i]
        for j in range(nz):
            row = _index(i, j, nz)
            control_measure = radial_measure * grid.axial_measure_m[j]
            mass = rho_cp * control_measure
            diagonal = 0.0

            # Radial internal faces.  At r=0 there is no inner face because
            # its cylindrical measure is exactly zero; no 1/r expression is
            # evaluated.
            if i > 0:
                conductance = (
                    THERMAL_CONDUCTIVITY_W_M_K
                    * grid.r_faces_m[i - 1]
                    * grid.axial_measure_m[j]
                    / grid.dr_m
                )
                rows.append(row)
                cols.append(_index(i - 1, j, nz))
                values.append(conductance / mass)
                diagonal -= conductance / mass
            if i < nr - 1:
                conductance = (
                    THERMAL_CONDUCTIVITY_W_M_K
                    * grid.r_faces_m[i]
                    * grid.axial_measure_m[j]
                    / grid.dr_m
                )
                rows.append(row)
                cols.append(_index(i + 1, j, nz))
                values.append(conductance / mass)
                diagonal -= conductance / mass

            # Axial internal faces.  At z=L/2 the missing outer face is the
            # symmetry zero-flux boundary.
            if j > 0:
                conductance = (
                    THERMAL_CONDUCTIVITY_W_M_K
                    * radial_measure
                    / grid.dz_m
                )
                rows.append(row)
                cols.append(_index(i, j - 1, nz))
                values.append(conductance / mass)
                diagonal -= conductance / mass
            if j < nz - 1:
                conductance = (
                    THERMAL_CONDUCTIVITY_W_M_K
                    * radial_measure
                    / grid.dz_m
                )
                rows.append(row)
                cols.append(_index(i, j + 1, nz))
                values.append(conductance / mass)
                diagonal -= conductance / mass

            # r=R side-surface Robin flux, written in the same inward-positive
            # convention as the formal Problem-1 temperature RHS.
            if i == nr - 1:
                conductance = (
                    HEAT_TRANSFER_W_M2_K
                    * RADIUS_M
                    * grid.axial_measure_m[j]
                )
                diagonal -= conductance / mass
                boundary_source[row] += conductance / mass

            # z=0 is the physical end face in the half-domain.  The other end
            # is the symmetry plane and intentionally has no Robin term.
            if z0_convection and j == 0:
                conductance = HEAT_TRANSFER_W_M2_K * radial_measure
                diagonal -= conductance / mass
                boundary_source[row] += conductance / mass

            rows.append(row)
            cols.append(row)
            values.append(diagonal)

    operator = sparse.coo_matrix(
        (np.asarray(values), (np.asarray(rows), np.asarray(cols))),
        shape=(n, n),
    ).tocsr()
    return LinearSystem(operator=operator, boundary_source=boundary_source)


def assemble_1d_radial_system(grid: Grid2D) -> tuple[sparse.csr_matrix, np.ndarray]:
    """Assemble the matching 1-D radial CN operator for the adiabatic check."""

    nr = grid.nr
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    boundary_source = np.zeros(nr, dtype=float)
    rho_cp = DENSITY_KG_M3 * HEAT_CAPACITY_J_KG_K

    for i in range(nr):
        mass = rho_cp * grid.radial_measure_m2[i]
        diagonal = 0.0
        if i > 0:
            conductance = (
                THERMAL_CONDUCTIVITY_W_M_K
                * grid.r_faces_m[i - 1]
                / grid.dr_m
            )
            rows.append(i)
            cols.append(i - 1)
            values.append(conductance / mass)
            diagonal -= conductance / mass
        if i < nr - 1:
            conductance = (
                THERMAL_CONDUCTIVITY_W_M_K
                * grid.r_faces_m[i]
                / grid.dr_m
            )
            rows.append(i)
            cols.append(i + 1)
            values.append(conductance / mass)
            diagonal -= conductance / mass
        if i == nr - 1:
            conductance = HEAT_TRANSFER_W_M2_K * RADIUS_M
            diagonal -= conductance / mass
            boundary_source[i] += conductance / mass
        rows.append(i)
        cols.append(i)
        values.append(diagonal)

    operator = sparse.coo_matrix(
        (np.asarray(values), (np.asarray(rows), np.asarray(cols))),
        shape=(nr, nr),
    ).tocsr()
    return operator, boundary_source


def _cn_matrices(operator: sparse.csr_matrix, dt_s: float) -> tuple[sparse.csr_matrix, sparse.csr_matrix, Callable]:
    identity = sparse.eye(operator.shape[0], format="csc")
    left = identity - 0.5 * dt_s * operator
    right = (identity + 0.5 * dt_s * operator).tocsr()
    solve_left = spla.factorized(left)
    return left, right, solve_left


def run_cn(
    system: LinearSystem | tuple[sparse.csr_matrix, np.ndarray],
    grid: Grid2D,
    air_time_s: np.ndarray,
    air_temperature_C: np.ndarray,
    dt_s: float,
    t_end_s: float,
    save_times_s: np.ndarray,
    trace_state_indices: np.ndarray | None = None,
) -> CNRun | dict[int, np.ndarray]:
    """Advance one constant-property system with Crank--Nicolson.

    ``trace_state_indices`` optionally records only selected state entries at
    every time step.  This is used for the continuous midplane plot and avoids
    retaining the full 2-D field history.
    """

    if isinstance(system, LinearSystem):
        operator = system.operator
        boundary_source = system.boundary_source
        is_2d = True
    else:
        operator, boundary_source = system
        is_2d = False
    if dt_s <= 0.0 or t_end_s <= 0.0:
        raise ValueError("时间步和终止时间必须为正")
    steps_float = t_end_s / dt_s
    n_steps = int(round(steps_float))
    if not np.isclose(n_steps * dt_s, t_end_s, rtol=0.0, atol=1.0e-10):
        raise ValueError("终止时间必须能由整数个时间步达到")

    save_steps: dict[int, float] = {}
    for time_s in np.asarray(save_times_s, dtype=float):
        step = int(round(time_s / dt_s))
        if step < 0 or step > n_steps or not np.isclose(
            step * dt_s, time_s, rtol=0.0, atol=1.0e-9
        ):
            raise ValueError(f"保存时刻 {time_s:g} s 不是当前时间网格节点")
        save_steps[step] = float(time_s)

    _, right, solve_left = _cn_matrices(operator, dt_s)
    state = np.full(operator.shape[0], INITIAL_TEMPERATURE_C, dtype=float)
    saved: dict[int, np.ndarray] = {}
    trace_indices = None
    trace_temperature = None
    if trace_state_indices is not None:
        trace_indices = np.asarray(trace_state_indices, dtype=int)
        if trace_indices.ndim != 1 or np.any(trace_indices < 0) or np.any(
            trace_indices >= state.size
        ):
            raise ValueError("连续轨迹索引超出 CN 状态向量范围")
        trace_temperature = np.empty((n_steps + 1, trace_indices.size), dtype=float)
        trace_temperature[0] = state[trace_indices]
    if 0 in save_steps:
        saved[0] = state.copy()
    air_at_steps = np.interp(
        dt_s * np.arange(n_steps + 1, dtype=float),
        air_time_s,
        air_temperature_C,
    )

    for step in range(n_steps):
        boundary_average = 0.5 * (air_at_steps[step] + air_at_steps[step + 1])
        rhs = right.dot(state) + dt_s * boundary_source * boundary_average
        state = np.asarray(solve_left(rhs), dtype=float)
        if trace_temperature is not None:
            trace_temperature[step + 1] = state[trace_indices]
        if step + 1 in save_steps:
            saved[step + 1] = state.copy()

    if is_2d:
        fields = {
            step: state_vector.reshape(grid.nr, grid.nz)
            for step, state_vector in saved.items()
        }
        trace_times = (
            dt_s * np.arange(n_steps + 1, dtype=float)
            if trace_temperature is not None
            else None
        )
        return CNRun(
            grid=grid,
            dt_s=dt_s,
            fields_C=fields,
            trace_times_s=trace_times,
            trace_temperature_C=trace_temperature,
        )
    return saved


def load_formal_baseline() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Read and validate the formal 1-D CSV without recomputing it."""

    if not FORMAL_RESULT_PATH.exists():
        raise FileNotFoundError(f"找不到正式一维基准: {FORMAL_RESULT_PATH}")
    frame = pd.read_csv(FORMAL_RESULT_PATH)
    required = {"time_s", "radius_cm", "temperature_C", "moisture_kgkg"}
    if not required.issubset(frame.columns):
        raise ValueError(f"正式 CSV 缺少列 {sorted(required - set(frame.columns))}")
    frame = frame.copy()
    for column in ("time_s", "radius_cm", "temperature_C", "moisture_kgkg"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame.duplicated(["time_s", "radius_cm"]).any():
        raise ValueError("正式 CSV 存在重复的 (time_s, radius_cm) 键")
    times = np.arange(1801, dtype=float)
    # The formal CSV stores one-decimal centimetre labels.  Round the
    # generated labels so values such as 0.30000000000000004 do not miss the
    # corresponding 0.3 CSV column during an exact pandas reindex.
    radii_cm = np.round(np.linspace(0.0, 2.0, 21), 1)
    pivot = frame.pivot(index="time_s", columns="radius_cm", values="temperature_C")
    pivot = pivot.reindex(index=times, columns=radii_cm)
    if pivot.isna().any().any():
        raise ValueError("正式 CSV 未完整覆盖 0..1800 s、0..2 cm 的一维温度基准")
    moisture_pivot = frame.pivot(
        index="time_s", columns="radius_cm", values="moisture_kgkg"
    ).reindex(index=times, columns=radii_cm)
    if moisture_pivot.isna().any().any():
        raise ValueError("正式 CSV 未完整覆盖 0..1800 s、0..2 cm 的一维湿度基准")
    return frame, times, radii_cm


def _required_index(values: np.ndarray, target: float, label: str) -> int:
    indices = np.flatnonzero(np.isclose(values, target, rtol=0.0, atol=1.0e-12))
    if indices.size != 1:
        raise ValueError(f"{label}={target:g} 未在二维网格上精确找到")
    return int(indices[0])


def _check_field_values(run: CNRun, air_temperature_max_C: float) -> None:
    for time_step, field in run.fields_C.items():
        if field.shape != (run.grid.nr, run.grid.nz):
            raise RuntimeError(f"t={time_step} 的二维场形状错误: {field.shape}")
        if not np.all(np.isfinite(field)):
            raise RuntimeError(f"t={time_step} 的二维场包含 NaN/Inf")
        if np.min(field) < INITIAL_TEMPERATURE_C - 1.0e-8:
            raise RuntimeError(f"t={time_step} 的温度低于初始温度")
        if np.max(field) > air_temperature_max_C + 1.0e-7:
            raise RuntimeError(f"t={time_step} 的温度超过附件1外界最高温度")


def run_adiabatic_correctness_check(
    air_time_s: np.ndarray, air_temperature_C: np.ndarray, grid: Grid2D
) -> dict[str, float | str]:
    """Compare a z-adiabatic 2-D solve with the identical 1-D CN solve."""

    check_end_s = 20.0
    dt_s = 1.0
    two_d_system = assemble_2d_system(grid, z0_convection=False)
    one_d_operator, one_d_source = assemble_1d_radial_system(grid)
    two_d_run = run_cn(
        two_d_system,
        grid,
        air_time_s,
        air_temperature_C,
        dt_s,
        check_end_s,
        np.array([check_end_s]),
    )
    one_d_saved = run_cn(
        (one_d_operator, one_d_source),
        grid,
        air_time_s,
        air_temperature_C,
        dt_s,
        check_end_s,
        np.array([check_end_s]),
    )
    two_d_end = np.asarray(two_d_run.fields_C[int(check_end_s)], dtype=float)
    one_d_end = np.asarray(one_d_saved[int(check_end_s)], dtype=float)
    difference = two_d_end - one_d_end[:, None]
    max_abs = float(np.max(np.abs(difference)))
    mean_abs = float(np.mean(np.abs(difference)))
    return {
        "check": "adiabatic_2d_vs_matching_1d_CN",
        "time_s": check_end_s,
        "max_abs_error_C": max_abs,
        "mean_abs_error_C": mean_abs,
        "status": "pass" if max_abs < 1.0e-11 else "fail",
    }


def _midplane_values(
    run: CNRun, times_s: np.ndarray, radii_cm: np.ndarray
) -> np.ndarray:
    z_index = _required_index(run.grid.z_m, HALF_LENGTH_M, "z 中截面")
    r_indices = [
        _required_index(run.grid.r_m, radius_cm * 1.0e-2, "r")
        for radius_cm in radii_cm
    ]
    values = np.empty((times_s.size, radii_cm.size), dtype=float)
    for row, time_s in enumerate(times_s):
        values[row] = run.fields_C[int(round(time_s / run.dt_s))][
            r_indices, z_index
        ]
    return values


def _write_midplane_comparison(
    run: CNRun,
    baseline_pivot: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    two_d = _midplane_values(run, KEY_TIMES_S, KEY_RADII_CM)
    one_d = baseline_pivot.loc[KEY_TIMES_S, KEY_RADII_CM].to_numpy(dtype=float)
    rows: list[dict[str, float]] = []
    for ti, time_s in enumerate(KEY_TIMES_S):
        for ri, radius_cm in enumerate(KEY_RADII_CM):
            signed = float(two_d[ti, ri] - one_d[ti, ri])
            rows.append(
                {
                    "time_s": float(time_s),
                    "radius_cm": float(radius_cm),
                    "temperature_1d_C": float(one_d[ti, ri]),
                    "temperature_2d_midplane_C": float(two_d[ti, ri]),
                    "signed_error_2d_minus_1d_C": signed,
                    "abs_error_C": abs(signed),
                }
            )
    result = pd.DataFrame(rows)
    result.to_csv(output_path, index=False, float_format="%.10g")
    return result


def _write_error_statistics(comparison: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []

    def summary(scope: str, subset: pd.DataFrame, time_s: float | None) -> dict[str, float | str]:
        max_idx = subset["abs_error_C"].idxmax()
        max_row = subset.loc[max_idx]
        return {
            "scope": scope,
            "time_s": np.nan if time_s is None else float(time_s),
            "n_points": int(len(subset)),
            "max_abs_error_C": float(subset["abs_error_C"].max()),
            "mean_abs_error_C": float(subset["abs_error_C"].mean()),
            "max_signed_error_2d_minus_1d_C": float(
                subset["signed_error_2d_minus_1d_C"].abs().max()
            ),
            "max_error_radius_cm": float(max_row["radius_cm"]),
            "max_error_time_s": float(max_row["time_s"]),
        }

    rows.append(summary("overall", comparison, None))
    for time_s, subset in comparison.groupby("time_s", sort=True):
        rows.append(summary("by_time", subset, float(time_s)))
    result = pd.DataFrame(rows)
    result.to_csv(output_path, index=False, float_format="%.10g")
    return result


def _write_axial_profiles(run: CNRun, output_path: Path) -> pd.DataFrame:
    rows: list[dict[str, float | bool]] = []
    for time_s in KEY_TIMES_S:
        field = run.fields_C[int(round(time_s / run.dt_s))]
        for radius_cm in AXIAL_PROFILE_RADII_CM:
            r_index = _required_index(run.grid.r_m, radius_cm * 1.0e-2, "轴向剖面 r")
            profile = field[r_index, :]
            delta = np.abs(profile - profile[-1])
            for z_index, z_m in enumerate(run.grid.z_m):
                z_cm = z_m * 100.0
                rows.append(
                    {
                        "time_s": float(time_s),
                        "radius_cm": float(radius_cm),
                        "z_cm": float(z_cm),
                        "temperature_C": float(profile[z_index]),
                        "delta_from_midplane_C": float(delta[z_index]),
                        "is_requested_sample_z": bool(
                            np.any(np.isclose(AXIAL_SAMPLE_Z_CM, z_cm, atol=1.0e-10))
                        ),
                    }
                )
    result = pd.DataFrame(rows)
    result.to_csv(output_path, index=False, float_format="%.10g")
    return result


def _threshold_distance(z_m: np.ndarray, delta_C: np.ndarray, threshold_C: float) -> tuple[float, str]:
    above = np.flatnonzero(delta_C >= threshold_C)
    if above.size == 0:
        return 0.0, "below_threshold_everywhere"
    last = int(above[-1])
    if last == len(z_m) - 1:
        return float(z_m[-1]), "reaches_midplane"
    next_index = last + 1
    d0 = float(delta_C[last])
    d1 = float(delta_C[next_index])
    if np.isclose(d1, d0, rtol=0.0, atol=1.0e-15):
        crossing = float(z_m[last])
    else:
        fraction = (threshold_C - d0) / (d1 - d0)
        fraction = float(np.clip(fraction, 0.0, 1.0))
        crossing = float(z_m[last] + fraction * (z_m[next_index] - z_m[last]))
    return crossing, "threshold_crossed"


def _write_end_effect_range(run: CNRun, output_path: Path) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for time_s in KEY_TIMES_S:
        field = run.fields_C[int(round(time_s / run.dt_s))]
        for radius_cm in AXIAL_PROFILE_RADII_CM:
            r_index = _required_index(run.grid.r_m, radius_cm * 1.0e-2, "端部效应 r")
            profile = field[r_index, :]
            midplane = float(profile[-1])
            delta = np.abs(profile - midplane)
            distance_m, status = _threshold_distance(
                run.grid.z_m, delta, END_EFFECT_THRESHOLD_C
            )
            rows.append(
                {
                    "time_s": float(time_s),
                    "radius_cm": float(radius_cm),
                    "threshold_C": END_EFFECT_THRESHOLD_C,
                    "temperature_end_C": float(profile[0]),
                    "temperature_midplane_C": midplane,
                    "delta_at_end_C": float(delta[0]),
                    "delta_at_midplane_C": float(delta[-1]),
                    "propagation_distance_cm": distance_m * 100.0,
                    "status": status,
                }
            )
    result = pd.DataFrame(rows)
    result.to_csv(output_path, index=False, float_format="%.10g")
    return result


def _write_sensitivity(
    base_run: CNRun, refined_run: CNRun, output_path: Path
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []

    base_mid = _midplane_values(base_run, KEY_TIMES_S, KEY_RADII_CM)
    refined_mid = _midplane_values(refined_run, KEY_TIMES_S, KEY_RADII_CM)
    mid_diff = np.abs(refined_mid - base_mid)
    mid_location = np.unravel_index(int(np.argmax(mid_diff)), mid_diff.shape)
    rows.append(
        {
            "comparison": "midplane_key_points",
            "base_grid": f"dr={base_run.grid.dr_m:g};dz={base_run.grid.dz_m:g};dt={base_run.dt_s:g}",
            "refined_grid": f"dr={refined_run.grid.dr_m:g};dz={refined_run.grid.dz_m:g};dt={refined_run.dt_s:g}",
            "n_points": int(mid_diff.size),
            "max_abs_difference_C": float(np.max(mid_diff)),
            "mean_abs_difference_C": float(np.mean(mid_diff)),
            "max_time_s": float(KEY_TIMES_S[mid_location[0]]),
            "max_radius_cm": float(KEY_RADII_CM[mid_location[1]]),
            "max_z_cm": 12.5,
        }
    )

    z_samples_m = AXIAL_SAMPLE_Z_CM * 1.0e-2
    axial_base: list[float] = []
    axial_refined: list[float] = []
    axial_locations: list[tuple[float, float, float]] = []
    for time_s in KEY_TIMES_S:
        base_field = base_run.fields_C[int(round(time_s / base_run.dt_s))]
        refined_field = refined_run.fields_C[int(round(time_s / refined_run.dt_s))]
        for radius_cm in AXIAL_PROFILE_RADII_CM:
            r_base = _required_index(base_run.grid.r_m, radius_cm * 1.0e-2, "敏感性 base r")
            r_refined = _required_index(
                refined_run.grid.r_m, radius_cm * 1.0e-2, "敏感性 refined r"
            )
            for z_m in z_samples_m:
                z_base = _required_index(base_run.grid.z_m, z_m, "敏感性 base z")
                z_refined = _required_index(
                    refined_run.grid.z_m, z_m, "敏感性 refined z"
                )
                axial_base.append(float(base_field[r_base, z_base]))
                axial_refined.append(float(refined_field[r_refined, z_refined]))
                axial_locations.append((float(time_s), float(radius_cm), float(z_m * 100.0)))
    axial_diff = np.abs(np.asarray(axial_refined) - np.asarray(axial_base))
    axial_location = axial_locations[int(np.argmax(axial_diff))]
    rows.append(
        {
            "comparison": "axial_profile_sample_points",
            "base_grid": f"dr={base_run.grid.dr_m:g};dz={base_run.grid.dz_m:g};dt={base_run.dt_s:g}",
            "refined_grid": f"dr={refined_run.grid.dr_m:g};dz={refined_run.grid.dz_m:g};dt={refined_run.dt_s:g}",
            "n_points": int(axial_diff.size),
            "max_abs_difference_C": float(np.max(axial_diff)),
            "mean_abs_difference_C": float(np.mean(axial_diff)),
            "max_time_s": axial_location[0],
            "max_radius_cm": axial_location[1],
            "max_z_cm": axial_location[2],
        }
    )
    result = pd.DataFrame(rows)
    result.to_csv(output_path, index=False, float_format="%.10g")
    return result


def _plot_difference_evidence(
    run: CNRun,
    temperature_1d: pd.DataFrame,
    radii_cm: np.ndarray,
) -> dict[str, object]:
    """Plot quantitative evidence against the formal output resolution.

    The hero panel shows a 60-s centered rolling mean of the absolute
    difference for readability.  The lower panel summarizes all raw 1-s
    samples, so no data are discarded and no moisture curve is fabricated.
    """

    if run.trace_times_s is None or run.trace_temperature_C is None:
        raise RuntimeError("连续中截面温度轨迹未记录，无法生成差值证据图")
    times_s = np.asarray(run.trace_times_s, dtype=float)
    temperature_1d_values = temperature_1d.reindex(
        index=times_s, columns=radii_cm
    ).to_numpy(dtype=float)
    temperature_2d_values = np.asarray(run.trace_temperature_C, dtype=float)
    if temperature_1d_values.shape != temperature_2d_values.shape:
        raise RuntimeError(
            "正式一维与二维连续轨迹形状不一致: "
            f"1D={temperature_1d_values.shape}, 2D={temperature_2d_values.shape}"
        )
    if not np.all(np.isfinite(temperature_1d_values)) or not np.all(
        np.isfinite(temperature_2d_values)
    ):
        raise RuntimeError("温度差值证据图输入包含 NaN/Inf")

    signed_difference_C = temperature_2d_values - temperature_1d_values
    absolute_difference_C = np.abs(signed_difference_C)
    rolling_abs_scaled = (
        pd.DataFrame(absolute_difference_C)
        .rolling(window=61, center=True, min_periods=1)
        .mean()
        .to_numpy(dtype=float)
        * 1.0e5
    )
    mean_abs_C = np.mean(absolute_difference_C, axis=0)
    max_abs_C = np.max(absolute_difference_C, axis=0)
    mean_abs_percent = mean_abs_C / 1.0e-4 * 100.0
    max_abs_percent = max_abs_C / 1.0e-4 * 100.0
    global_max_abs_C = float(np.max(absolute_difference_C))
    reporting_increment_C = 1.0e-4
    if global_max_abs_C >= reporting_increment_C:
        raise RuntimeError(
            "二维/一维中截面最大差达到或超过正式 CSV 输出分辨率: "
            f"{global_max_abs_C:.10e} °C"
        )

    colors = np.asarray(
        ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"]
    )
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(7.2, 6.6),
        gridspec_kw={"height_ratios": [1.45, 1.0]},
    )
    time_ax, summary_ax = axes

    for color, radius_cm, rolling_trace in zip(
        colors, radii_cm, rolling_abs_scaled.T
    ):
        time_ax.plot(
            times_s,
            rolling_trace,
            color=color,
            lw=1.45,
            label=f"r={radius_cm:g} cm",
            zorder=2,
        )
    time_ax.text(
        0.015,
        0.96,
        "60-s rolling mean for readability; all 1-s samples retained for summary below.",
        transform=time_ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.5,
        color="#4f565e",
    )
    time_ax.axhline(
        10.0,
        color="#737b84",
        ls="--",
        lw=1.0,
        label="1-D CSV output increment = 10^-4 °C",
    )
    time_ax.set_title("60-s centered rolling mean of absolute difference")
    time_ax.set_ylabel("Mean absolute difference ×10^-5 °C")
    time_ax.set_xlim(0.0, 1800.0)
    time_ax.set_ylim(0.0, 10.5)
    time_ax.grid(alpha=0.18, zorder=0)
    time_ax.text(
        0.985,
        0.90,
        "1-D CSV output increment = 10^-4 °C",
        transform=time_ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        color="#5f666d",
    )

    x = np.arange(radii_cm.size, dtype=float)
    width = 0.34
    mean_bars = summary_ax.bar(
        x - width / 2.0,
        mean_abs_percent,
        width,
        color=colors,
        alpha=0.48,
        edgecolor=colors,
        linewidth=0.8,
        label="mean |difference|",
    )
    max_bars = summary_ax.bar(
        x + width / 2.0,
        max_abs_percent,
        width,
        color=colors,
        alpha=0.96,
        edgecolor="#20252b",
        linewidth=0.7,
        label="max |difference|",
    )
    summary_ax.axhline(
        100.0,
        color="#737b84",
        ls="--",
        lw=1.0,
        label="100% = 10^-4 °C output increment",
    )
    summary_ax.text(
        x[-1] + 0.42,
        100.8,
        "output increment",
        ha="right",
        va="bottom",
        fontsize=8,
        color="#5f666d",
    )
    summary_ax.bar_label(
        mean_bars,
        labels=[f"{value:.1f}%" for value in mean_abs_percent],
        padding=2,
        fontsize=7,
    )
    summary_ax.bar_label(
        max_bars,
        labels=[f"{value:.1f}%" for value in max_abs_percent],
        padding=2,
        fontsize=7,
    )
    summary_ax.set_xticks(x, [f"r={radius_cm:g} cm" for radius_cm in radii_cm])
    summary_ax.set_ylabel("% of 10^-4 °C output increment")
    summary_ax.set_ylim(0.0, 105.0)
    summary_ax.set_title(
        "Raw 1-s error summary versus the 1-D reporting resolution",
        pad=9,
    )
    summary_ax.grid(axis="y", alpha=0.18, zorder=0)
    summary_ax.legend(ncol=3, loc="upper left", fontsize=8, frameon=False)
    for tick, color in zip(summary_ax.get_xticklabels(), colors):
        tick.set_color(color)

    from matplotlib.lines import Line2D

    radius_handles = [
        Line2D([0], [0], color=color, lw=2.0, label=f"r={radius_cm:g} cm")
        for color, radius_cm in zip(colors, radii_cm)
    ]
    fig.legend(
        handles=radius_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=5,
        fontsize=7.5,
        frameon=False,
        title="Radial position",
    )
    fig.suptitle(
        "2-D midplane difference stays below the 1-D reporting resolution",
        fontsize=13,
        y=0.985,
    )
    fig.subplots_adjust(top=0.77, bottom=0.12, hspace=0.48)
    output_stem = FIGURE_DIR / "temperature_difference_evidence"
    fig.savefig(output_stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
    # The user-facing contract is PNG-only.  Keep vector export available for
    # the static figure preflight and optional journal packaging, but do not
    # create SVG/PDF files during the formal run unless explicitly requested.
    if os.environ.get("TASK1_EXPORT_VECTOR") == "1":
        fig.savefig(output_stem.with_suffix(".svg"), bbox_inches="tight")
        fig.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return {
        "n_times": int(times_s.size),
        "n_radii": int(radii_cm.size),
        "time_start_s": float(times_s[0]),
        "time_end_s": float(times_s[-1]),
        "global_max_abs_C": global_max_abs_C,
        "global_mean_signed_C": float(np.mean(signed_difference_C)),
        "global_mean_abs_C": float(np.mean(absolute_difference_C)),
        "mean_abs_percent": mean_abs_percent,
        "max_abs_percent": max_abs_percent,
    }


def _format_summary(
    correctness: Mapping[str, float | str],
    error_statistics: pd.DataFrame,
    end_effect: pd.DataFrame,
    sensitivity: pd.DataFrame,
    difference_summary: Mapping[str, object],
) -> str:
    overall = error_statistics.loc[error_statistics["scope"] == "overall"].iloc[0]
    lines = [
        "二维轴向温度对照实验完成。",
        f"绝热二维/一维 CN 一致性: max={correctness['max_abs_error_C']:.6e} °C, status={correctness['status']}",
        f"正式一维 vs 二维中截面: max={overall['max_abs_error_C']:.6e} °C, mean={overall['mean_abs_error_C']:.6e} °C",
        f"连续差值轨迹: n={difference_summary['n_times']}×{difference_summary['n_radii']}, max={difference_summary['global_max_abs_C']:.6e} °C (<1e-4), mean signed={difference_summary['global_mean_signed_C']:.6e} °C",
    ]
    for radius_cm in AXIAL_PROFILE_RADII_CM:
        subset = end_effect[end_effect["radius_cm"] == radius_cm]
        max_distance = subset["propagation_distance_cm"].max()
        max_delta = subset["delta_at_end_C"].max()
        lines.append(
            f"r={radius_cm:g} cm 端部阈值传播距离最大={max_distance:.6g} cm, 端面最大ΔT={max_delta:.6e} °C"
        )
    for _, row in sensitivity.iterrows():
        lines.append(
            f"敏感性 {row['comparison']}: max={row['max_abs_difference_C']:.6e} °C, mean={row['mean_abs_difference_C']:.6e} °C"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-refined",
        action="store_true",
        help="仅调试基准网格；正式验收不要使用",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    baseline_frame, baseline_times, radii_cm = load_formal_baseline()
    baseline_temperature = baseline_frame.pivot(
        index="time_s", columns="radius_cm", values="temperature_C"
    ).reindex(index=baseline_times, columns=radii_cm)

    load_air_data, attachment_path = _load_formal_air_loader()
    air_time_s, air_temperature_C, _ = load_air_data(attachment_path)
    if air_time_s[-1] < KEY_TIMES_S[-1]:
        raise ValueError("附件1温度数据未覆盖到 1800 s")

    base_grid = build_grid(dr_m=0.000125, dz_m=0.00125)
    correctness = run_adiabatic_correctness_check(
        air_time_s, air_temperature_C, base_grid
    )
    pd.DataFrame([correctness]).to_csv(
        DATA_DIR / "numerical_correctness_check.csv", index=False, float_format="%.10g"
    )
    if correctness["status"] != "pass":
        raise RuntimeError(f"绝热二维/一维一致性检查失败: {correctness}")

    requested_times_with_zero = KEY_TIMES_S
    base_system = assemble_2d_system(base_grid, z0_convection=True)
    trace_r_indices = np.asarray(
        [
            _required_index(base_grid.r_m, radius_cm * 1.0e-2, "连续轨迹 r")
            for radius_cm in KEY_RADII_CM
        ],
        dtype=int,
    )
    trace_state_indices = np.asarray(
        [_index(i, base_grid.nz - 1, base_grid.nz) for i in trace_r_indices],
        dtype=int,
    )
    base_run = run_cn(
        base_system,
        base_grid,
        air_time_s,
        air_temperature_C,
        dt_s=1.0,
        t_end_s=1800.0,
        save_times_s=requested_times_with_zero,
        trace_state_indices=trace_state_indices,
    )
    _check_field_values(base_run, float(np.max(air_temperature_C)))

    midplane_path = DATA_DIR / "midplane_1d_vs_2d.csv"
    error_path = DATA_DIR / "error_statistics.csv"
    axial_path = DATA_DIR / "axial_profiles.csv"
    end_effect_path = DATA_DIR / "end_effect_range.csv"
    sensitivity_path = DATA_DIR / "numerical_sensitivity.csv"
    comparison = _write_midplane_comparison(base_run, baseline_temperature, midplane_path)
    error_statistics = _write_error_statistics(comparison, error_path)
    _write_axial_profiles(base_run, axial_path)
    end_effect = _write_end_effect_range(base_run, end_effect_path)
    difference_summary = _plot_difference_evidence(
        base_run,
        baseline_temperature.loc[:, KEY_RADII_CM],
        KEY_RADII_CM,
    )

    if args.skip_refined:
        sensitivity = pd.DataFrame(
            [
                {
                    "comparison": "skipped_by_cli",
                    "base_grid": "",
                    "refined_grid": "",
                    "n_points": 0,
                    "max_abs_difference_C": np.nan,
                    "mean_abs_difference_C": np.nan,
                    "max_time_s": np.nan,
                    "max_radius_cm": np.nan,
                    "max_z_cm": np.nan,
                }
            ]
        )
        sensitivity.to_csv(sensitivity_path, index=False)
    else:
        refined_grid = build_grid(dr_m=0.000125, dz_m=0.000625)
        refined_system = assemble_2d_system(refined_grid, z0_convection=True)
        refined_run = run_cn(
            refined_system,
            refined_grid,
            air_time_s,
            air_temperature_C,
            dt_s=0.5,
            t_end_s=1800.0,
            save_times_s=requested_times_with_zero,
        )
        _check_field_values(refined_run, float(np.max(air_temperature_C)))
        sensitivity = _write_sensitivity(base_run, refined_run, sensitivity_path)

    print(
        _format_summary(
            correctness,
            error_statistics,
            end_effect,
            sensitivity,
            difference_summary,
        )
    )
    print(f"附件1: {attachment_path}")
    print(f"正式一维基准（只读）: {FORMAL_RESULT_PATH}")
    print(f"二维基准网格: nr={base_grid.nr}, nz={base_grid.nz}, dt=1 s")
    print(f"输出目录: {ADD_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
