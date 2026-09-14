"""问题一：圆柱药材径向传热传质的守恒有限体积求解器。

空间采用含 ``r=0`` 与 ``r=R`` 节点的节点中心有限体积网格，首尾节点
对应半控制体；时间采用 Crank--Nicolson。温度方程每步直接求解，非线性
水分方程采用 Picard 迭代，并在界面使用扩散系数的调和平均。
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import solve_banded


# 题目参数（内部统一使用 SI 单位）。
RADIUS_M = 0.02
LENGTH_M = 0.25  # 轴向长度在一维径向守恒式中与 2π 公共约因子相消
DENSITY_KG_M3 = 820.0
HEAT_CAPACITY_J_KG_K = 2600.0
THERMAL_CONDUCTIVITY_W_M_K = 0.36
HEAT_TRANSFER_W_M2_K = 25.0
MASS_TRANSFER_M_S = 8.0e-7
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE_KGKG = 2.55

BASE_DR_M = 0.00005
BASE_DT_S = 0.25
END_TIME_S = 1800.0
OUTPUT_DT_S = 1.0
OUTPUT_DR_M = 0.001
KEY_TIMES_S = np.array([100, 300, 600, 900, 1200, 1500, 1800], dtype=float)
KEY_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
PICARD_TOL = 1.0e-10
PICARD_MAX_ITERATIONS = 50
LINEAR_RESIDUAL_TOL = 1.0e-10
BOUNDARY_DIRECTION_TOL = 1.0e-8

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
)
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "answer" / "task1_result.csv"
DEFAULT_KEY_PATH = (
    Path(__file__).resolve().parents[1] / "answer" / "task1_key_results.csv"
)
DEFAULT_DIAGNOSTICS_JSON = (
    Path(__file__).resolve().parents[1] / "answer" / "task1_diagnostics.json"
)
DEFAULT_DIAGNOSTICS_CSV = (
    Path(__file__).resolve().parents[1] / "answer" / "task1_diagnostics.csv"
)
CSV_TIME_COUNT = 1801
CSV_RADIUS_COUNT = 21
CSV_DATA_ROW_COUNT = CSV_TIME_COUNT * CSV_RADIUS_COUNT


def load_air_data(
    path: str | Path = DEFAULT_DATA_PATH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取附件1的时间、空气温度和空气水分浓度三列。"""

    frame = pd.read_excel(Path(path))
    column_map = {str(column).strip(): column for column in frame.columns}
    required = ("时间", "温度", "水分浓度")
    missing = [column for column in required if column not in column_map]
    if missing:
        raise ValueError(f"附件1缺少必需列: {missing}; 实际列为 {list(frame.columns)!r}")

    selected = frame[[column_map[column] for column in required]].copy()
    selected.columns = required
    for column in required:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")

    time_s = selected["时间"].to_numpy(dtype=float)
    air_temperature_C = selected["温度"].to_numpy(dtype=float)
    air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
    all_values = np.column_stack((time_s, air_temperature_C, air_moisture_kgkg))
    if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
        raise ValueError("附件1的时间列必须包含至少两个严格递增的时间点")
    if not np.all(np.isfinite(all_values)):
        raise ValueError("附件1包含非有限数值")
    if time_s[0] > 0.0 or time_s[-1] < END_TIME_S:
        raise ValueError("附件1边界数据必须覆盖 0--1800 s")
    return time_s, air_temperature_C, air_moisture_kgkg


def _integer_count(value: float, *, label: str) -> int:
    """将应为整数的浮点比值安全转换为正整数。"""

    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label}必须为有限正值")
    count = int(round(value))
    if count < 1 or not np.isclose(value, count, rtol=0.0, atol=1.0e-10):
        raise ValueError(f"{label}必须为整数，实际为 {value:.16g}")
    return count


def radial_grid(
    radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
) -> np.ndarray:
    """返回包含 ``0`` 和 ``radius_m`` 的均匀径向节点网格。"""

    if not np.isfinite(radius_m) or radius_m <= 0.0:
        raise ValueError("半径必须为有限正值")
    if not np.isfinite(dr_m) or dr_m <= 0.0:
        raise ValueError("空间步长必须为有限正值")
    intervals = _integer_count(radius_m / dr_m, label="半径/空间步长")
    if not np.isclose(
        intervals * dr_m, radius_m, rtol=0.0, atol=max(1.0e-14, radius_m * 1.0e-12)
    ):
        raise ValueError("当前有限体积网格要求半径可由整数个 dr 划分")
    return np.linspace(0.0, radius_m, intervals + 1)


def control_volume_geometry(
    radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """返回节点、内界面及各控制体的径向测度 ``integral(r dr)``。"""

    radius_m = radial_grid(radius_m, dr_m)
    physical_radius_m = float(radius_m[-1])
    face_radius_m = 0.5 * (radius_m[:-1] + radius_m[1:])
    measure_m2 = np.empty_like(radius_m)
    measure_m2[0] = 0.5 * face_radius_m[0] ** 2
    measure_m2[1:-1] = 0.5 * (
        face_radius_m[1:] ** 2 - face_radius_m[:-1] ** 2
    )
    measure_m2[-1] = 0.5 * (physical_radius_m**2 - face_radius_m[-1] ** 2)
    if not np.all(measure_m2 > 0.0):
        raise RuntimeError("有限体积径向测度必须为正")
    return radius_m, face_radius_m, measure_m2


def moisture_diffusivity(moisture_kgkg: np.ndarray) -> np.ndarray:
    """计算严格为正的经验扩散系数 ``7e-9 exp(-0.89/C)``。"""

    concentration = np.asarray(moisture_kgkg, dtype=float)
    if np.any(~np.isfinite(concentration)) or np.any(concentration <= 0.0):
        raise RuntimeError("水分浓度必须为有限正值，无法计算扩散系数")
    diffusivity = 7.0e-9 * np.exp(-0.89 / concentration)
    return np.maximum(diffusivity, np.finfo(float).tiny)


def harmonic_mean_positive(
    left: np.ndarray, right: np.ndarray
) -> np.ndarray:
    """对两个严格正的数组逐元素计算调和平均。"""

    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if left.shape != right.shape:
        raise ValueError("调和平均的左右输入形状必须一致")
    if (
        np.any(~np.isfinite(left))
        or np.any(~np.isfinite(right))
        or np.any(left <= 0.0)
        or np.any(right <= 0.0)
    ):
        raise ValueError("调和平均要求左右输入均为有限严格正值")
    faces = 2.0 * left * right / (left + right)
    if np.any(~np.isfinite(faces)) or np.any(faces <= 0.0):
        raise RuntimeError("界面扩散系数的调和平均必须严格为正")
    return faces


def _harmonic_face_values(node_values: np.ndarray) -> np.ndarray:
    """用严格正值调和平均计算相邻节点界面系数。"""

    values = np.asarray(node_values, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("界面调和平均至少需要两个一维节点值")
    return harmonic_mean_positive(values[:-1], values[1:])


def _operator_diagonals(
    conductance: np.ndarray, surface_transfer: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """构造守恒扩散算子 ``L`` 的下、主、上三条对角线。"""

    conductance = np.asarray(conductance, dtype=float)
    if conductance.ndim != 1 or conductance.size < 1:
        raise ValueError("界面导纳必须是一维且至少包含一个界面")
    if np.any(~np.isfinite(conductance)) or np.any(conductance <= 0.0):
        raise ValueError("内部界面导纳必须为有限正值")
    if not np.isfinite(surface_transfer) or surface_transfer < 0.0:
        raise ValueError("表面传递系数必须为有限非负值")
    node_count = conductance.size + 1
    lower = conductance.copy()
    upper = conductance.copy()
    diagonal = np.empty(node_count, dtype=float)
    diagonal[0] = -conductance[0]
    diagonal[1:-1] = -(conductance[:-1] + conductance[1:])
    diagonal[-1] = -(conductance[-1] + surface_transfer)
    return lower, diagonal, upper


def _tridiagonal_product(
    lower: np.ndarray,
    diagonal: np.ndarray,
    upper: np.ndarray,
    values: np.ndarray,
) -> np.ndarray:
    result = diagonal * values
    result[1:] += lower * values[:-1]
    result[:-1] += upper * values[1:]
    return result


def _banded_product(matrix: np.ndarray, values: np.ndarray) -> np.ndarray:
    result = matrix[1] * values
    result[1:] += matrix[2, :-1] * values[:-1]
    result[:-1] += matrix[0, 1:] * values[1:]
    return result


def _solve_cn_step(
    old_values: np.ndarray,
    capacity: np.ndarray,
    old_operator: tuple[np.ndarray, np.ndarray, np.ndarray],
    new_operator: tuple[np.ndarray, np.ndarray, np.ndarray],
    old_boundary_source: float,
    new_boundary_source: float,
    dt_s: float,
) -> tuple[np.ndarray, float]:
    """求解一个 CN 三对角系统并返回归一化无穷残差。"""

    old_values = np.asarray(old_values, dtype=float)
    capacity = np.asarray(capacity, dtype=float)
    if old_values.ndim != 1 or capacity.shape != old_values.shape:
        raise ValueError("CN 状态和控制体容量必须为同形一维数组")
    if np.any(~np.isfinite(old_values)) or np.any(~np.isfinite(capacity)):
        raise ValueError("CN 状态和控制体容量不能包含 NaN 或 Inf")
    if np.any(capacity <= 0.0) or not np.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("CN 控制体容量和时间步长必须为有限正值")
    if not np.isfinite(old_boundary_source) or not np.isfinite(new_boundary_source):
        raise ValueError("CN Robin 边界源项不能包含 NaN 或 Inf")
    old_lower, old_diagonal, old_upper = old_operator
    new_lower, new_diagonal, new_upper = new_operator
    if (
        old_lower.shape != new_lower.shape
        or old_upper.shape != new_upper.shape
        or old_diagonal.shape != new_diagonal.shape
        or old_diagonal.shape != old_values.shape
        or old_lower.size != old_values.size - 1
    ):
        raise ValueError("CN 三对角算子与状态数组形状不一致")
    mass_rate = capacity / dt_s
    right_hand_side = mass_rate * old_values
    right_hand_side += 0.5 * _tridiagonal_product(
        old_lower, old_diagonal, old_upper, old_values
    )
    right_hand_side[-1] += 0.5 * (old_boundary_source + new_boundary_source)

    matrix = np.zeros((3, old_values.size), dtype=float)
    matrix[0, 1:] = -0.5 * new_upper
    matrix[1] = mass_rate - 0.5 * new_diagonal
    matrix[2, :-1] = -0.5 * new_lower
    new_values = solve_banded((1, 1), matrix, right_hand_side, check_finite=False)
    residual = _banded_product(matrix, new_values) - right_hand_side
    row_sums = np.abs(matrix[1]).copy()
    row_sums[1:] += np.abs(matrix[2, :-1])
    row_sums[:-1] += np.abs(matrix[0, 1:])
    denominator = (
        float(np.max(row_sums)) * float(np.linalg.norm(new_values, ord=np.inf))
        + float(np.linalg.norm(right_hand_side, ord=np.inf))
    )
    denominator = max(denominator, np.finfo(float).tiny)
    normalized_residual = float(np.linalg.norm(residual, ord=np.inf) / denominator)
    if not np.isfinite(normalized_residual) or normalized_residual > LINEAR_RESIDUAL_TOL:
        raise RuntimeError(
            f"CN 三对角求解归一化无穷残差超限: {normalized_residual:.3e}"
        )
    return new_values, normalized_residual


def solve_task1(
    data_path: str | Path = DEFAULT_DATA_PATH,
    *,
    dr_m: float = BASE_DR_M,
    dt_s: float = BASE_DT_S,
    t_end_s: float = END_TIME_S,
    output_dt_s: float = OUTPUT_DT_S,
) -> dict[str, object]:
    """求解问题一，并以 1 s、0.1 cm 网格返回场和逐步诊断。

    ``dr_m`` 和 ``dt_s`` 可用于网格/时间步敏感性分析；只要二者分别整除
    ``RADIUS_M`` 和输出时间步长，返回数组的输出形状保持为 ``(1801, 21)``。
    """

    for value, label in (
        (dr_m, "空间步长 dr_m"),
        (dt_s, "时间步长 dt_s"),
        (t_end_s, "终止时间 t_end_s"),
        (output_dt_s, "输出时间步长 output_dt_s"),
    ):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(f"{label}必须为有限正值")
    if t_end_s > END_TIME_S + 1.0e-10:
        raise ValueError("当前附件和输出契约只支持 0--1800 s")

    data_time_s, data_air_temperature_C, data_air_moisture_kgkg = load_air_data(
        data_path
    )
    if t_end_s > data_time_s[-1] + 1.0e-10:
        raise ValueError(
            f"附件1边界数据只覆盖到 {data_time_s[-1]:g} s，无法计算到 {t_end_s:g} s"
        )

    step_count = _integer_count(t_end_s / dt_s, label="终止时间/时间步长")
    save_stride = _integer_count(output_dt_s / dt_s, label="输出时间步长/时间步长")
    output_count = _integer_count(t_end_s / output_dt_s, label="终止时间/输出时间步长") + 1
    if save_stride < 1:
        raise ValueError("内部时间步长不能大于输出时间步长")
    if (
        output_count != CSV_TIME_COUNT
        or not np.isclose(output_dt_s, OUTPUT_DT_S, rtol=0.0, atol=1.0e-12)
        or not np.isclose(t_end_s, END_TIME_S, rtol=0.0, atol=1.0e-10)
    ):
        raise ValueError("问题一标准输出必须覆盖 0--1800 s、每隔 1 s")

    radius_m, face_radius_m, measure_m2 = control_volume_geometry(RADIUS_M, dr_m)
    node_count = radius_m.size
    output_radius_cm = np.arange(CSV_RADIUS_COUNT, dtype=float) / 10.0
    output_radius_m = output_radius_cm * 1.0e-2
    output_node_float = output_radius_m / dr_m
    output_node_indices = np.rint(output_node_float).astype(int)
    if (
        np.any(output_node_indices < 0)
        or np.any(output_node_indices >= node_count)
        or not np.allclose(
            output_node_indices * dr_m,
            output_radius_m,
            rtol=0.0,
            atol=max(1.0e-13, dr_m * 1.0e-9),
        )
    ):
        raise ValueError("当前 dr_m 无法在内部网格上精确采样 0.1 cm 输出节点")
    output_time_s = output_dt_s * np.arange(output_count, dtype=float)
    output_time_s[-1] = t_end_s

    temperature = np.full(node_count, INITIAL_TEMPERATURE_C, dtype=float)
    moisture = np.full(node_count, INITIAL_MOISTURE_KGKG, dtype=float)
    temperature_output = np.empty((output_count, CSV_RADIUS_COUNT), dtype=float)
    moisture_output = np.empty_like(temperature_output)
    temperature_output[0] = temperature[output_node_indices]
    moisture_output[0] = moisture[output_node_indices]

    picard_iterations = np.empty(step_count, dtype=int)
    picard_deltas = np.empty(step_count, dtype=float)
    temperature_linear_residuals = np.empty(step_count, dtype=float)
    moisture_linear_residuals = np.empty(step_count, dtype=float)
    moisture_balance_residuals = np.empty(step_count, dtype=float)
    energy_balance_residuals = np.empty(step_count, dtype=float)
    moisture_boundary_fluxes = np.empty(step_count, dtype=float)
    energy_boundary_fluxes = np.empty(step_count, dtype=float)

    heat_capacity = DENSITY_KG_M3 * HEAT_CAPACITY_J_KG_K * measure_m2
    heat_conductance = THERMAL_CONDUCTIVITY_W_M_K * face_radius_m / dr_m
    heat_surface_transfer = RADIUS_M * HEAT_TRANSFER_W_M2_K
    heat_operator = _operator_diagonals(heat_conductance, heat_surface_transfer)

    moisture_capacity = measure_m2
    moisture_surface_transfer = RADIUS_M * MASS_TRANSFER_M_S
    for step in range(step_count):
        current_time_s = step * dt_s
        next_time_s = (step + 1) * dt_s
        old_air_temperature = float(
            np.interp(current_time_s, data_time_s, data_air_temperature_C)
        )
        new_air_temperature = float(
            np.interp(next_time_s, data_time_s, data_air_temperature_C)
        )
        previous_temperature = temperature
        temperature, temperature_linear_residuals[step] = _solve_cn_step(
            temperature,
            heat_capacity,
            heat_operator,
            heat_operator,
            heat_surface_transfer * old_air_temperature,
            heat_surface_transfer * new_air_temperature,
            dt_s,
        )
        # 能量守恒：约去 2πL 后，全域焓变应等于 CN 加权的表面 Robin 热流。
        energy_flux = heat_surface_transfer * (
            0.5 * (old_air_temperature + new_air_temperature)
            - 0.5 * (previous_temperature[-1] + temperature[-1])
        )
        energy_boundary_fluxes[step] = energy_flux
        energy_balance_residuals[step] = float(
            heat_capacity @ (temperature - previous_temperature)
        ) / dt_s - energy_flux

        old_air_moisture = float(
            np.interp(current_time_s, data_time_s, data_air_moisture_kgkg)
        )
        new_air_moisture = float(
            np.interp(next_time_s, data_time_s, data_air_moisture_kgkg)
        )
        previous_moisture = moisture
        old_diffusivity = moisture_diffusivity(moisture)
        old_face_diffusivity = _harmonic_face_values(old_diffusivity)
        old_conductance = old_face_diffusivity * face_radius_m / dr_m
        old_moisture_operator = _operator_diagonals(
            old_conductance, moisture_surface_transfer
        )

        guess = moisture.copy()
        converged = False
        delta = np.inf
        residual = np.inf
        for iteration in range(1, PICARD_MAX_ITERATIONS + 1):
            guess_diffusivity = moisture_diffusivity(guess)
            guess_face_diffusivity = _harmonic_face_values(guess_diffusivity)
            guess_conductance = guess_face_diffusivity * face_radius_m / dr_m
            guess_operator = _operator_diagonals(
                guess_conductance, moisture_surface_transfer
            )
            updated, residual = _solve_cn_step(
                moisture,
                moisture_capacity,
                old_moisture_operator,
                guess_operator,
                moisture_surface_transfer * old_air_moisture,
                moisture_surface_transfer * new_air_moisture,
                dt_s,
            )
            delta = float(np.max(np.abs(updated - guess)))
            guess = updated
            if delta < PICARD_TOL:
                converged = True
                break
        if not converged:
            raise RuntimeError(
                f"水分 Picard 在 t={next_time_s:g} s 的 {PICARD_MAX_ITERATIONS} 次迭代内未收敛; "
                f"最终 delta={delta:.3e}, 容差={PICARD_TOL:.3e}"
            )
        moisture = guess
        if np.any(~np.isfinite(moisture)) or np.any(moisture <= 0.0):
            raise RuntimeError(f"水分在 t={next_time_s:g} s 出现非有限或非正值")
        picard_iterations[step] = iteration
        picard_deltas[step] = delta
        moisture_linear_residuals[step] = residual
        # 水分质量守恒：全域水分储量变化应等于 CN 加权的表面 Robin 质流。
        moisture_flux = moisture_surface_transfer * (
            0.5 * (old_air_moisture + new_air_moisture)
            - 0.5 * (previous_moisture[-1] + moisture[-1])
        )
        moisture_boundary_fluxes[step] = moisture_flux
        moisture_balance_residuals[step] = (
            float(moisture_capacity @ (moisture - previous_moisture)) / dt_s
            - moisture_flux
        )

        if (step + 1) % save_stride == 0:
            save_position = (step + 1) // save_stride
            temperature_output[save_position] = temperature[output_node_indices]
            moisture_output[save_position] = moisture[output_node_indices]

    expected_save_position = output_count - 1
    actual_save_position = step_count // save_stride
    if actual_save_position != expected_save_position:
        raise RuntimeError(
            f"输出时间层数错误: 期望最后索引 {expected_save_position}, 实际 {actual_save_position}"
        )
    air_temperature_output = np.interp(
        output_time_s, data_time_s, data_air_temperature_C
    )
    air_moisture_output = np.interp(
        output_time_s, data_time_s, data_air_moisture_kgkg
    )
    linear_residuals = np.maximum(
        temperature_linear_residuals, moisture_linear_residuals
    )
    output_measure_m2 = control_volume_geometry(RADIUS_M, OUTPUT_DR_M)[2]
    volume_average_moisture = (
        moisture_output @ output_measure_m2 / float(np.sum(output_measure_m2))
    )
    return {
        "time_s": output_time_s,
        "radius_cm": output_radius_cm,
        "temperature_C": temperature_output,
        "moisture_kgkg": moisture_output,
        "air_temperature_C": air_temperature_output,
        "air_moisture_kgkg": air_moisture_output,
        "time_step_s": dt_s,
        "dt_s": dt_s,
        "dr_m": dr_m,
        "picard_iterations": picard_iterations,
        "picard_deltas": picard_deltas,
        "linear_residuals": linear_residuals,
        "temperature_linear_residuals": temperature_linear_residuals,
        "moisture_linear_residuals": moisture_linear_residuals,
        "moisture_balance_residuals": moisture_balance_residuals,
        "energy_balance_residuals": energy_balance_residuals,
        "moisture_boundary_fluxes": moisture_boundary_fluxes,
        "energy_boundary_fluxes": energy_boundary_fluxes,
        "volume_average_moisture_kgkg": volume_average_moisture,
        "center_inner_face_radius_m": 0.0,
    }


def validate_solution(solution: dict[str, object]) -> None:
    """检查输出契约、数值有限性、代数收敛、边界方向和物理趋势。"""

    required_keys = (
        "time_s",
        "radius_cm",
        "temperature_C",
        "moisture_kgkg",
        "air_temperature_C",
        "air_moisture_kgkg",
        "picard_iterations",
        "picard_deltas",
        "linear_residuals",
        "temperature_linear_residuals",
        "moisture_linear_residuals",
        "volume_average_moisture_kgkg",
    )
    missing = [key for key in required_keys if key not in solution]
    if missing:
        raise ValueError(f"问题一结果缺少 {missing}")

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    air_temperature = np.asarray(solution["air_temperature_C"], dtype=float)
    air_moisture = np.asarray(solution["air_moisture_kgkg"], dtype=float)
    if time_s.shape != (CSV_TIME_COUNT,) or radius_cm.shape != (CSV_RADIUS_COUNT,):
        raise ValueError(
            f"输出坐标 shape 错误: 期望 time=({CSV_TIME_COUNT},), radius=({CSV_RADIUS_COUNT},), "
            f"实际 time={time_s.shape}, radius={radius_cm.shape}"
        )
    expected_field_shape = (CSV_TIME_COUNT, CSV_RADIUS_COUNT)
    if temperature.shape != expected_field_shape or moisture.shape != expected_field_shape:
        raise ValueError(
            f"场数组 shape 错误: 期望 {expected_field_shape}, "
            f"实际 T={temperature.shape}, C={moisture.shape}"
        )
    if air_temperature.shape != (CSV_TIME_COUNT,) or air_moisture.shape != (CSV_TIME_COUNT,):
        raise ValueError("空气边界数组 shape 错误")

    dt_value = float(solution.get("time_step_s", solution.get("dt_s", np.nan)))
    dr_value = float(solution.get("dr_m", np.nan))
    if not np.isfinite(dt_value) or dt_value <= 0.0:
        raise ValueError("结果缺少有限正的 time_step_s")
    if not np.isfinite(dr_value) or dr_value <= 0.0:
        raise ValueError("结果缺少有限正的 dr_m")
    if "dt_s" in solution and not np.isclose(
        float(solution["dt_s"]), dt_value, rtol=0.0, atol=1.0e-14
    ):
        raise ValueError("time_step_s 与 dt_s 不一致")
    step_count = _integer_count(END_TIME_S / dt_value, label="终止时间/时间步长")
    intervals = _integer_count(RADIUS_M / dr_value, label="半径/空间步长")
    if not np.isclose(
        intervals * dr_value, RADIUS_M, rtol=0.0, atol=max(1.0e-14, RADIUS_M * 1.0e-12)
    ):
        raise ValueError("结果 dr_m 无法整除圆柱半径")

    diagnostics = {
        "picard_iterations": (np.asarray(solution["picard_iterations"]), int),
        "picard_deltas": (np.asarray(solution["picard_deltas"], dtype=float), float),
        "linear_residuals": (np.asarray(solution["linear_residuals"], dtype=float), float),
        "temperature_linear_residuals": (
            np.asarray(solution["temperature_linear_residuals"], dtype=float),
            float,
        ),
        "moisture_linear_residuals": (
            np.asarray(solution["moisture_linear_residuals"], dtype=float),
            float,
        ),
    }
    for key, (array, _) in diagnostics.items():
        if array.shape != (step_count,):
            raise ValueError(
                f"{key} shape 错误: 期望 ({step_count},), 实际 {array.shape}"
            )
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{key} 包含 NaN 或 Inf")
    volume_average = np.asarray(solution["volume_average_moisture_kgkg"], dtype=float)
    if volume_average.shape != (CSV_TIME_COUNT,) or not np.all(np.isfinite(volume_average)):
        raise ValueError("体积平均水分数组 shape 或数值错误")
    for key, array in (
        ("time_s", time_s),
        ("radius_cm", radius_cm),
        ("temperature_C", temperature),
        ("moisture_kgkg", moisture),
        ("air_temperature_C", air_temperature),
        ("air_moisture_kgkg", air_moisture),
    ):
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{key} 包含 NaN 或 Inf")

    if not np.allclose(time_s, np.arange(CSV_TIME_COUNT, dtype=float), rtol=0.0, atol=1.0e-12):
        raise ValueError("输出时间必须为 0--1800 s、步长 1 s")
    if not np.allclose(
        radius_cm, np.arange(CSV_RADIUS_COUNT, dtype=float) / 10.0, rtol=0.0, atol=1.0e-14
    ):
        raise ValueError("输出半径必须为 0--2 cm、步长 0.1 cm")
    if float(solution.get("center_inner_face_radius_m", np.nan)) != 0.0:
        raise ValueError("中心内侧面半径必须严格等于 0")
    if np.min(diagnostics["picard_iterations"][0]) < 1 or np.max(
        diagnostics["picard_iterations"][0]
    ) > PICARD_MAX_ITERATIONS:
        raise ValueError("Picard 迭代次数超出允许范围")
    if np.min(diagnostics["picard_deltas"][0]) < 0.0 or np.max(
        diagnostics["picard_deltas"][0]
    ) >= PICARD_TOL:
        raise ValueError("Picard 最终 delta 未严格小于容差")
    all_linear_residuals = np.concatenate(
        [diagnostics[name][0] for name in (
            "linear_residuals",
            "temperature_linear_residuals",
            "moisture_linear_residuals",
        )]
    )
    if np.max(all_linear_residuals) > LINEAR_RESIDUAL_TOL:
        raise ValueError("线性系统归一化无穷残差超过 1e-10")
    if not np.allclose(
        diagnostics["linear_residuals"][0],
        np.maximum(
            diagnostics["temperature_linear_residuals"][0],
            diagnostics["moisture_linear_residuals"][0],
        ),
        rtol=0.0,
        atol=1.0e-30,
    ):
        raise ValueError("linear_residuals 未覆盖温度和水分两类线性残差")

    if not np.allclose(temperature[0], INITIAL_TEMPERATURE_C, rtol=0.0, atol=1.0e-12):
        raise ValueError("初始温度场不是 28 C")
    if not np.allclose(moisture[0], INITIAL_MOISTURE_KGKG, rtol=0.0, atol=1.0e-12):
        raise ValueError("初始水分场不是 2.55 kg/kg")
    if np.min(moisture) <= 0.0:
        raise ValueError("水分场出现非正值")

    heat_driver = air_temperature - temperature[:, -1]
    moisture_driver = air_moisture - moisture[:, -1]
    if np.min(heat_driver) < -BOUNDARY_DIRECTION_TOL:
        raise ValueError(
            f"热 Robin 驱动方向错误: min(T_air-T_surface)={np.min(heat_driver):.6g}"
        )
    if np.max(moisture_driver) > BOUNDARY_DIRECTION_TOL:
        raise ValueError(
            f"质 Robin 驱动方向错误: max(C_air-C_surface)={np.max(moisture_driver):.6g}"
        )
    if temperature[-1, -1] <= temperature[-1, 0]:
        raise ValueError("末时刻表面温度未高于中心温度")
    if moisture[-1, -1] >= moisture[-1, 0]:
        raise ValueError("末时刻表面水分未低于中心水分")

    output_measure_m2 = control_volume_geometry(RADIUS_M, OUTPUT_DR_M)[2]
    calculated_volume_average = (
        moisture @ output_measure_m2 / float(np.sum(output_measure_m2))
    )
    if not np.allclose(
        volume_average, calculated_volume_average, rtol=0.0, atol=1.0e-12
    ):
        raise ValueError("返回的体积平均水分与场数组不一致")
    if volume_average[-1] >= volume_average[0]:
        raise ValueError(
            f"体积加权平均水分未下降: {volume_average[0]:.6g} -> {volume_average[-1]:.6g}"
        )


def write_solution_csv(
    solution: dict[str, object], output_path: str | Path = DEFAULT_OUTPUT_PATH
) -> tuple[Path, int]:
    """把已求得的固定采样结果写成长表 CSV；本模块不会自动调用它。"""

    validate_solution(solution)
    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("time_s", "radius_cm", "temperature_C", "moisture_kgkg"))
        for time_index, time_value in enumerate(time_s):
            for radius_index, radius_value in enumerate(radius_cm):
                writer.writerow(
                    (
                        str(int(time_value)),
                        f"{radius_value:.1f}",
                        f"{temperature[time_index, radius_index]:.4f}",
                        f"{moisture[time_index, radius_index]:.4f}",
                    )
                )
                row_count += 1
    if row_count != CSV_DATA_ROW_COUNT:
        raise RuntimeError(
            f"CSV 数据行数错误: 期望 {CSV_DATA_ROW_COUNT}, 实际 {row_count}"
        )
    return destination, row_count


def _key_sample_arrays(
    solution: dict[str, object],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """从完整 1 s / 0.1 cm 场中提取表 1、表 2 的关键时间与半径。"""

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    time_indices = np.array(
        [int(np.argmin(np.abs(time_s - target))) for target in KEY_TIMES_S], dtype=int
    )
    if not np.allclose(time_s[time_indices], KEY_TIMES_S, rtol=0.0, atol=1.0e-10):
        raise ValueError("问题一完整结果缺少表 1、表 2 要求的时间点")
    radius_indices = np.array(
        [int(np.argmin(np.abs(radius_cm - target))) for target in KEY_RADII_CM],
        dtype=int,
    )
    if not np.allclose(
        radius_cm[radius_indices], KEY_RADII_CM, rtol=0.0, atol=1.0e-12
    ):
        raise ValueError("问题一完整结果缺少表 1、表 2 要求的径向位置")
    return (
        KEY_TIMES_S.copy(),
        KEY_RADII_CM.copy(),
        temperature[np.ix_(time_indices, radius_indices)],
        moisture[np.ix_(time_indices, radius_indices)],
    )


def write_key_results_csv(
    solution: dict[str, object], output_path: str | Path = DEFAULT_KEY_PATH
) -> tuple[Path, int]:
    """写出表 1、表 2 来源的关键时间/半径长表。"""

    time_values, radius_values, temperature, moisture = _key_sample_arrays(solution)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("time_s", "radius_cm", "temperature_C", "moisture_kgkg"))
        for time_index, time_value in enumerate(time_values):
            for radius_index, radius_value in enumerate(radius_values):
                writer.writerow(
                    (
                        str(int(time_value)),
                        f"{radius_value:.1f}",
                        f"{temperature[time_index, radius_index]:.4f}",
                        f"{moisture[time_index, radius_index]:.4f}",
                    )
                )
                row_count += 1
    expected_rows = KEY_TIMES_S.size * KEY_RADII_CM.size
    if row_count != expected_rows:
        raise RuntimeError(f"关键点 CSV 行数错误: 期望 {expected_rows}, 实际 {row_count}")
    return destination, row_count


def diagnostics_summary(solution: dict[str, object]) -> dict[str, object]:
    """汇总 Picard 统计、物理约束与守恒残差，形成可持久化日志。"""

    time_s = np.asarray(solution["time_s"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    air_temperature = np.asarray(solution["air_temperature_C"], dtype=float)
    air_moisture = np.asarray(solution["air_moisture_kgkg"], dtype=float)
    iterations = np.asarray(solution["picard_iterations"], dtype=int)
    picard_deltas = np.asarray(solution["picard_deltas"], dtype=float)
    linear_residuals = np.asarray(solution["linear_residuals"], dtype=float)
    mass_residuals = np.asarray(solution["moisture_balance_residuals"], dtype=float)
    energy_residuals = np.asarray(solution["energy_balance_residuals"], dtype=float)
    mass_fluxes = np.asarray(solution["moisture_boundary_fluxes"], dtype=float)
    energy_fluxes = np.asarray(solution["energy_boundary_fluxes"], dtype=float)

    heat_driver = air_temperature - temperature[:, -1]
    moisture_driver = air_moisture - moisture[:, -1]
    volume_average = np.asarray(solution["volume_average_moisture_kgkg"], dtype=float)

    def _relative(residuals: np.ndarray, fluxes: np.ndarray) -> tuple[float, float]:
        scale = np.maximum.reduce(
            [
                np.abs(residuals),
                np.abs(fluxes),
                np.full_like(residuals, np.finfo(float).tiny),
            ]
        )
        relative = np.abs(residuals) / scale
        index = int(np.argmax(np.abs(residuals)))
        dt_value = float(solution["time_step_s"])
        return float(np.max(relative)), float((index + 1) * dt_value)

    mass_relative, mass_worst_time = _relative(mass_residuals, mass_fluxes)
    energy_relative, energy_worst_time = _relative(energy_residuals, energy_fluxes)
    dt_value = float(solution["time_step_s"])
    return {
        "task": 1,
        "caliber": {
            "spatial_game": "守恒型径向有限体积（含中心半控制体）",
            "temporal": "Crank-Nicolson",
            "interface_property": "调和平均",
            "nonlinear": "Picard（水分扩散系数）",
            "dr_m": float(solution.get("dr_m", np.nan)),
            "dt_s": float(solution.get("time_step_s", np.nan)),
            "n_steps": int(iterations.size),
            "output_shape": [int(moisture.shape[0]), int(moisture.shape[1])],
            "picard_tol": float(PICARD_TOL),
            "linear_residual_tol": float(LINEAR_RESIDUAL_TOL),
        },
        "picard": {
            "max_iterations": int(np.max(iterations)),
            "mean_iterations": float(np.mean(iterations)),
            "max_final_delta": float(np.max(picard_deltas)),
            "converged_steps": int(np.sum(picard_deltas < PICARD_TOL)),
            "failed_steps": int(np.sum(picard_deltas >= PICARD_TOL)),
        },
        "linear_solver": {
            "max_normalized_inf_residual": float(np.max(linear_residuals)),
            "tol": float(LINEAR_RESIDUAL_TOL),
        },
        "physics": {
            "temperature_min_C": float(np.min(temperature)),
            "temperature_max_C": float(np.max(temperature)),
            "moisture_min_kgkg": float(np.min(moisture)),
            "moisture_max_kgkg": float(np.max(moisture)),
            "moisture_positive": bool(np.min(moisture) > 0.0),
            "finite": bool(
                np.all(np.isfinite(temperature)) and np.all(np.isfinite(moisture))
            ),
            "center_inner_face_radius_m": float(
                solution.get("center_inner_face_radius_m", np.nan)
            ),
            "min_heat_boundary_driver_C": float(np.min(heat_driver)),
            "max_moisture_boundary_driver_kgkg": float(np.max(moisture_driver)),
            "final_surface_center_temperature_gap_C": float(
                temperature[-1, -1] - temperature[-1, 0]
            ),
            "final_center_surface_moisture_gap_kgkg": float(
                moisture[-1, 0] - moisture[-1, -1]
            ),
            "volume_average_moisture_initial_kgkg": float(volume_average[0]),
            "volume_average_moisture_final_kgkg": float(volume_average[-1]),
            "volume_average_moisture_monotone_decreasing": bool(
                np.all(np.diff(volume_average) <= 1.0e-12)
            ),
        },
        "conservation": {
            "moisture": {
                "quantity": "约去 2πL 的全域水分储量 Σ V_i C_i",
                "max_abs_balance_residual": float(np.max(np.abs(mass_residuals))),
                "max_relative_balance_residual": mass_relative,
                "worst_time_s": mass_worst_time,
                "boundary_flux_integral": float(np.sum(mass_fluxes) * dt_value),
                "volume_average_change_kgkg": float(volume_average[0] - volume_average[-1]),
            },
            "energy": {
                "quantity": "约去 2πL 的全域焓 Σ V_i ρc_p T_i（恒物性）",
                "max_abs_balance_residual": float(np.max(np.abs(energy_residuals))),
                "max_relative_balance_residual": energy_relative,
                "worst_time_s": energy_worst_time,
                "boundary_flux_integral": float(np.sum(energy_fluxes) * dt_value),
            },
        },
    }


def write_diagnostics(
    solution: dict[str, object],
    json_path: str | Path = DEFAULT_DIAGNOSTICS_JSON,
    csv_path: str | Path = DEFAULT_DIAGNOSTICS_CSV,
) -> tuple[Path, Path]:
    """把逐步 Picard/线性/守恒日志写为 CSV，并写汇总 JSON。"""

    import json

    summary = diagnostics_summary(solution)
    json_destination = Path(json_path)
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    time_s = np.asarray(solution["time_s"], dtype=float)
    step_count = np.asarray(solution["picard_iterations"]).size
    dt_value = float(solution["time_step_s"])
    iterations = np.asarray(solution["picard_iterations"], dtype=int)
    picard_deltas = np.asarray(solution["picard_deltas"], dtype=float)
    linear_residuals = np.asarray(solution["linear_residuals"], dtype=float)
    mass_residuals = np.asarray(solution["moisture_balance_residuals"], dtype=float)
    energy_residuals = np.asarray(solution["energy_balance_residuals"], dtype=float)
    csv_destination = Path(csv_path)
    csv_destination.parent.mkdir(parents=True, exist_ok=True)
    with csv_destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "step",
                "time_s",
                "picard_iterations",
                "picard_final_delta",
                "linear_normalized_inf_residual",
                "moisture_balance_residual",
                "energy_balance_residual",
            )
        )
        for step in range(step_count):
            writer.writerow(
                (
                    step + 1,
                    f"{(step + 1) * dt_value:.6f}",
                    int(iterations[step]),
                    f"{picard_deltas[step]:.6e}",
                    f"{linear_residuals[step]:.6e}",
                    f"{mass_residuals[step]:.6e}",
                    f"{energy_residuals[step]:.6e}",
                )
            )
    return json_destination, csv_destination


def main() -> None:
    """求解问题一并生成完整结果、表 1/表 2 来源与诊断日志。"""

    result = solve_task1()
    validate_solution(result)
    csv_path, csv_rows = write_solution_csv(result)
    key_path, key_rows = write_key_results_csv(result)
    json_path, diagnostics_path = write_diagnostics(result)
    summary = diagnostics_summary(result)
    print("问题一求解/验证: PASS")
    print(f"完整结果: {csv_path} ({csv_rows} 行)")
    print(f"表 1/表 2 来源: {key_path} ({key_rows} 行)")
    print(f"诊断日志: {json_path}, {diagnostics_path}")
    print(
        "Picard: max={} mean={:.3f}; 守恒最大相对残差: 水分={:.3e}, 能量={:.3e}".format(
            summary["picard"]["max_iterations"],
            summary["picard"]["mean_iterations"],
            summary["conservation"]["moisture"]["max_relative_balance_residual"],
            summary["conservation"]["energy"]["max_relative_balance_residual"],
        )
    )


if __name__ == "__main__":
    main()
