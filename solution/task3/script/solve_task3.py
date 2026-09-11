"""A题问题三：固定半径圆柱的长期热质耦合烘干求解器。

本脚本独立实现 handoff/task3_handoff.md 规定的守恒径向有限体积模型：
界面物性使用调和平均，时间方向使用 Crank--Nicolson，非线性物性在
半时间层通过 Picard 迭代更新。前 14400 s 采用附件1分段线性边界，
之后采用附件1稳定段(9000--14400 s)均值。程序从 t=0 连续积分，
对完整内部水分场检查阈值，并用跨越步线性插值报告精确烘干时刻。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import time as wall_time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy.linalg import solve_banded


# 题设几何、初值和问题二/三沿用的传递参数。
RADIUS_M = 0.02
LENGTH_M = 0.25
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE_KGKG = 2.55
HEAT_TRANSFER_W_M2_K = 25.0
MASS_TRANSFER_M_S = 8.0e-7

# handoff/task3_handoff.md 的最终离散规格。
N_DEFAULT = 1600
TIME_STEP_EARLY_S = 1.0
TIME_STEP_LONG_DEFAULT_S = 10.0
OUTPUT_DT_S = 60.0
STABLE_START_S = 9000.0
AIR_DATA_END_S = 14400.0
TABLE5_DT_S = 6.0 * 3600.0
DRYING_THRESHOLD_KGKG = 0.15
DEFAULT_MAX_TIME_S = 7.0 * 24.0 * 3600.0

PICARD_TOL_T_C = 1.0e-8
PICARD_TOL_C_KGKG = 1.0e-10
PICARD_MAX_ITER = 50

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "problem" / "附件" / "附件3" / "result3.xlsx"
DEFAULT_ANSWER_DIR = Path(__file__).resolve().parents[1] / "answer"
DEFAULT_XLSX_PATH = DEFAULT_ANSWER_DIR / "result3.xlsx"
DEFAULT_CSV_PATH = DEFAULT_ANSWER_DIR / "task3_all_results.csv"
DEFAULT_TASK2_CSV_PATH = REPO_ROOT / "solution" / "task2" / "answer" / "task2_all_results.csv"

OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
KEY_RADIUS_INDICES = np.array([0, 5, 10, 15, 20], dtype=int)


def load_air_data(
    path: str | Path = DEFAULT_DATA_PATH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取附件1的时间、烘房温度和烘房水分浓度。"""

    frame = pd.read_excel(Path(path))
    columns = {str(column).strip(): column for column in frame.columns}
    required = ("时间", "温度", "水分浓度")
    missing = [name for name in required if name not in columns]
    if missing:
        raise ValueError(f"附件1缺少必需列: {missing}")
    selected = frame[[columns[name] for name in required]].copy()
    selected.columns = required
    for column in required:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
    time_s = selected["时间"].to_numpy(dtype=float)
    temperature_C = selected["温度"].to_numpy(dtype=float)
    moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
    values = np.column_stack((time_s, temperature_C, moisture_kgkg))
    if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
        raise ValueError("附件1时间必须包含至少两个严格递增时间点")
    if time_s[0] > 1.0e-10 or time_s[-1] < AIR_DATA_END_S - 1.0e-10:
        raise ValueError("附件1未覆盖到14400 s")
    if not np.all(np.isfinite(values)):
        raise ValueError("附件1数据包含NaN或Inf")
    return time_s, temperature_C, moisture_kgkg


def stable_air_means(
    time_s: np.ndarray,
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
) -> tuple[float, float, int]:
    """实时计算附件1在9000--14400 s（含端点）的统计均值。"""

    stable = (time_s >= STABLE_START_S - 1.0e-10) & (
        time_s <= AIR_DATA_END_S + 1.0e-10
    )
    if not np.any(stable):
        raise ValueError("附件1没有9000--14400 s稳定段数据")
    stable_temperature = float(np.mean(temperature_C[stable]))
    stable_moisture = float(np.mean(moisture_kgkg[stable]))
    return stable_temperature, stable_moisture, int(np.count_nonzero(stable))


def air_at(
    time_value_s: float,
    time_s: np.ndarray,
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
    stable_temperature_C: float,
    stable_moisture_kgkg: float,
) -> tuple[float, float]:
    """附件范围内分段线性；14400 s 后使用稳定段均值。"""

    if time_value_s <= AIR_DATA_END_S + 1.0e-10:
        clipped = min(max(float(time_value_s), float(time_s[0])), AIR_DATA_END_S)
        return (
            float(np.interp(clipped, time_s, temperature_C)),
            float(np.interp(clipped, time_s, moisture_kgkg)),
        )
    return stable_temperature_C, stable_moisture_kgkg


def fixed_geometry(
    n_intervals: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """构造固定半径圆柱的径向节点、面和半控制体积测度。"""

    if n_intervals < 2:
        raise ValueError("径向区间数至少为2")
    dr_m = RADIUS_M / float(n_intervals)
    radii_m = np.linspace(0.0, RADIUS_M, n_intervals + 1)
    faces_m = 0.5 * (radii_m[:-1] + radii_m[1:])
    measure = np.empty_like(radii_m)
    measure[0] = 0.5 * faces_m[0] ** 2
    measure[1:-1] = 0.5 * (faces_m[1:] ** 2 - faces_m[:-1] ** 2)
    measure[-1] = 0.5 * (RADIUS_M**2 - faces_m[-1] ** 2)
    if not np.isclose(np.sum(measure), 0.5 * RADIUS_M**2, atol=1.0e-18):
        raise ValueError("径向控制体测度未覆盖整个圆柱截面")
    return radii_m, faces_m, measure, dr_m


def output_indices(radii_m: np.ndarray) -> np.ndarray:
    """返回0--2 cm、每0.1 cm输出位置对应的内部节点。"""

    target_m = OUTPUT_RADIUS_CM / 100.0
    indices = np.array([int(np.argmin(np.abs(radii_m - r))) for r in target_m])
    if not np.allclose(radii_m[indices], target_m, rtol=0.0, atol=1.0e-14):
        raise ValueError("当前N不能精确包含0.1 cm输出位置")
    return indices


def material_properties(
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """按附录3计算动态物性，扩散系数温度使用K。"""

    temperature_C = np.asarray(temperature_C, dtype=float)
    moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
    concentration = np.maximum(moisture_kgkg, 1.0e-12)
    temperature_K = temperature_C + 273.15
    if np.any(~np.isfinite(temperature_K)) or np.any(temperature_K <= 0.0):
        raise ValueError("物性计算遇到非正或非有限Kelvin温度")
    rho = 650.0 + 128.0 * concentration
    cp = 1450.0 + 2736.0 * concentration / (concentration + 1.0)
    conductivity = 0.21 + 0.38 * concentration / (concentration + 1.0)
    diffusivity = 2.4e-3 * np.exp(-0.45 / concentration) * np.exp(
        -3850.0 / temperature_K
    )
    return rho, cp, conductivity, diffusivity


def harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """返回正物性的界面调和平均。"""

    denominator = left + right
    if np.any(denominator <= 0.0) or not np.all(np.isfinite(denominator)):
        raise ValueError("界面物性非正或非有限")
    return 2.0 * left * right / denominator


def solve_tridiagonal(
    lower: np.ndarray,
    diagonal: np.ndarray,
    upper: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    """求解三对角线性系统。"""

    n = diagonal.size
    banded = np.zeros((3, n), dtype=float)
    banded[0, 1:] = upper
    banded[1] = diagonal
    banded[2, :-1] = lower
    result = solve_banded((1, 1), banded, rhs, check_finite=False)
    if not np.all(np.isfinite(result)):
        raise RuntimeError("三对角线性系统求解得到NaN或Inf")
    return result


def solve_cn_field(
    old_field: np.ndarray,
    storage: np.ndarray,
    face_property: np.ndarray,
    faces_m: np.ndarray,
    dr_m: float,
    dt_s: float,
    boundary_conductance: float,
    air_value: float,
) -> np.ndarray:
    """用冻结的半时间层物性求解一个守恒FVM的CN场。

    令 K 为正的扩散/Robin离散矩阵，空间算子为 ``-K u+b``。
    因而 CN 方程为

        (S+dt*K/2)u_new=(S-dt*K/2)u_old+dt*b_mid,

    其中边界值明确取 t+dt/2。
    """

    conductance = face_property * faces_m / dr_m
    diagonal_K = np.empty_like(storage)
    diagonal_K[0] = conductance[0]
    diagonal_K[1:-1] = conductance[:-1] + conductance[1:]
    diagonal_K[-1] = conductance[-1] + boundary_conductance

    half_dt = 0.5 * dt_s
    diagonal = storage + half_dt * diagonal_K
    lower = -half_dt * conductance
    upper = -half_dt * conductance

    # (S - dt*K/2) old 的三对角乘积；表面Robin源项为 dt*b_mid。
    rhs = (storage - half_dt * diagonal_K) * old_field
    rhs[:-1] += half_dt * conductance * old_field[1:]
    rhs[1:] += half_dt * conductance * old_field[:-1]
    rhs[-1] += dt_s * boundary_conductance * air_value
    return solve_tridiagonal(lower, diagonal, upper, rhs)


def picard_step(
    old_temperature_C: np.ndarray,
    old_moisture_kgkg: np.ndarray,
    faces_m: np.ndarray,
    measure: np.ndarray,
    dr_m: float,
    dt_s: float,
    air_temperature_C: float,
    air_moisture_kgkg: float,
) -> tuple[np.ndarray, np.ndarray, int, float, float]:
    """一个时间步的CN热质耦合Picard迭代。"""

    guess_temperature_C = old_temperature_C.copy()
    guess_moisture_kgkg = old_moisture_kgkg.copy()
    last_delta_temperature = np.inf
    last_delta_moisture = np.inf

    for iteration in range(1, PICARD_MAX_ITER + 1):
        # 物性严格由 old 与当前 new guess 的半时间层状态更新。
        midpoint_temperature_C = 0.5 * (old_temperature_C + guess_temperature_C)
        midpoint_moisture_kgkg = 0.5 * (old_moisture_kgkg + guess_moisture_kgkg)
        rho, cp, conductivity, diffusivity = material_properties(
            midpoint_temperature_C, midpoint_moisture_kgkg
        )
        midpoint_k = harmonic_mean(conductivity[:-1], conductivity[1:])
        midpoint_D = harmonic_mean(diffusivity[:-1], diffusivity[1:])

        new_temperature_C = solve_cn_field(
            old_temperature_C,
            rho * cp * measure,
            midpoint_k,
            faces_m,
            dr_m,
            dt_s,
            RADIUS_M * HEAT_TRANSFER_W_M2_K,
            air_temperature_C,
        )
        new_moisture_kgkg = solve_cn_field(
            old_moisture_kgkg,
            measure,
            midpoint_D,
            faces_m,
            dr_m,
            dt_s,
            RADIUS_M * MASS_TRANSFER_M_S,
            air_moisture_kgkg,
        )
        if np.min(new_moisture_kgkg) < -1.0e-10:
            raise RuntimeError("CN Picard步得到明显负水分浓度")
        new_moisture_kgkg = np.maximum(new_moisture_kgkg, 0.0)
        last_delta_temperature = float(
            np.max(np.abs(new_temperature_C - guess_temperature_C))
        )
        last_delta_moisture = float(
            np.max(np.abs(new_moisture_kgkg - guess_moisture_kgkg))
        )
        if (
            last_delta_temperature <= PICARD_TOL_T_C
            and last_delta_moisture <= PICARD_TOL_C_KGKG
        ):
            return (
                new_temperature_C,
                new_moisture_kgkg,
                iteration,
                last_delta_temperature,
                last_delta_moisture,
            )
        guess_temperature_C = new_temperature_C
        guess_moisture_kgkg = new_moisture_kgkg

    raise RuntimeError(
        "CN Picard迭代未收敛: "
        f"dt={dt_s:g}s, iter={PICARD_MAX_ITER}, "
        f"max|dT|={last_delta_temperature:.3e}, "
        f"max|dC|={last_delta_moisture:.3e}"
    )


def is_multiple(time_value_s: float, interval_s: float) -> bool:
    """判断浮点时间是否为给定间隔的整数倍。"""

    quotient = time_value_s / interval_s
    return abs(quotient - round(quotient)) <= 1.0e-9


def solve_task3(
    data_path: str | Path = DEFAULT_DATA_PATH,
    n_intervals: int = N_DEFAULT,
    time_step_long_s: float = TIME_STEP_LONG_DEFAULT_S,
    output_dt_s: float = OUTPUT_DT_S,
    max_time_s: float = DEFAULT_MAX_TIME_S,
    progress: bool = False,
    collect_first3: bool = True,
) -> dict[str, Any]:
    """从 t=0 连续积分，返回规则采样、终止括号和验证所需状态。"""

    if time_step_long_s <= 0.0 or output_dt_s <= 0.0 or max_time_s <= 0.0:
        raise ValueError("时间步、输出间隔和时间上限必须为正")
    if not is_multiple(output_dt_s, time_step_long_s) or not is_multiple(
        output_dt_s, TIME_STEP_EARLY_S
    ):
        raise ValueError("60 s输出间隔必须同时整除两段时间步")
    air_time_s, air_temperature, air_moisture = load_air_data(data_path)
    stable_temperature_C, stable_moisture_kgkg, stable_count = stable_air_means(
        air_time_s, air_temperature, air_moisture
    )
    radii_m, faces_m, measure, dr_m = fixed_geometry(n_intervals)
    indices = output_indices(radii_m)
    key_indices = indices[KEY_RADIUS_INDICES]
    n_nodes = radii_m.size

    current_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
    current_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)
    current_time_s = 0.0

    sampled_times: list[float] = [0.0]
    sampled_moisture: list[np.ndarray] = [current_moisture[indices].copy()]
    first3 = (
        np.full((10801, indices.size), np.nan, dtype=float)
        if collect_first3
        else None
    )
    if first3 is not None:
        first3[0] = current_moisture[indices]
    table5_times: list[float] = []
    table5_values: list[np.ndarray] = []
    iteration_counts: list[int] = []
    delta_temperature: list[float] = []
    delta_moisture: list[float] = []

    previous_max = float(np.max(current_moisture))
    max_positive_step_change = -np.inf
    max_positive_average_change = -np.inf
    max_abs_step_change = 0.0
    max_radial_increase = -np.inf
    volume_measure = float(np.sum(measure))
    previous_average = float(np.sum(measure * current_moisture) / volume_measure)
    min_moisture = float(np.min(current_moisture))
    max_moisture = float(np.max(current_moisture))
    min_temperature = float(np.min(current_temperature))
    max_temperature = float(np.max(current_temperature))
    early_steps = 0
    long_steps = 0

    termination_time_s: float | None = None
    termination_alpha: float | None = None
    termination_lower_time_s: float | None = None
    termination_lower_temperature: np.ndarray | None = None
    termination_lower_moisture: np.ndarray | None = None
    termination_upper_temperature: np.ndarray | None = None
    termination_upper_moisture: np.ndarray | None = None
    termination_lower_max = np.nan
    termination_upper_max = np.nan

    max_steps_guard = int(np.ceil(max_time_s / TIME_STEP_EARLY_S)) + 1
    for _ in range(max_steps_guard):
        if current_time_s >= max_time_s - 1.0e-10:
            break
        if current_time_s < AIR_DATA_END_S - 1.0e-10:
            dt_s = min(TIME_STEP_EARLY_S, AIR_DATA_END_S - current_time_s)
            early_steps += 1
        else:
            dt_s = time_step_long_s
            long_steps += 1
        time_new_s = current_time_s + dt_s
        midpoint_air = air_at(
            current_time_s + 0.5 * dt_s,
            air_time_s,
            air_temperature,
            air_moisture,
            stable_temperature_C,
            stable_moisture_kgkg,
        )
        old_temperature = current_temperature
        old_moisture = current_moisture
        (
            current_temperature,
            current_moisture,
            iterations,
            step_delta_temperature,
            step_delta_moisture,
        ) = picard_step(
            old_temperature,
            old_moisture,
            faces_m,
            measure,
            dr_m,
            dt_s,
            midpoint_air[0],
            midpoint_air[1],
        )
        iteration_counts.append(iterations)
        delta_temperature.append(step_delta_temperature)
        delta_moisture.append(step_delta_moisture)

        change = current_moisture - old_moisture
        average = float(np.sum(measure * current_moisture) / volume_measure)
        max_positive_step_change = max(max_positive_step_change, float(np.max(change)))
        max_positive_average_change = max(
            max_positive_average_change, average - previous_average
        )
        max_abs_step_change = max(max_abs_step_change, float(np.max(np.abs(change))))
        max_radial_increase = max(max_radial_increase, float(np.max(np.diff(current_moisture))))
        previous_average = average
        min_moisture = min(min_moisture, float(np.min(current_moisture)))
        max_moisture = max(max_moisture, float(np.max(current_moisture)))
        min_temperature = min(min_temperature, float(np.min(current_temperature)))
        max_temperature = max(max_temperature, float(np.max(current_temperature)))

        if first3 is not None and time_new_s <= 10800.0 + 1.0e-10:
            first3[int(round(time_new_s))] = current_moisture[indices]

        current_max = float(np.max(current_moisture))
        crossing = previous_max >= DRYING_THRESHOLD_KGKG and current_max < DRYING_THRESHOLD_KGKG
        if crossing:
            denominator = previous_max - current_max
            if denominator <= 0.0:
                raise RuntimeError("阈值跨越步的最大水分没有下降")
            alpha = (previous_max - DRYING_THRESHOLD_KGKG) / denominator
            alpha = float(np.clip(alpha, 0.0, 1.0))
            termination_time_s = current_time_s + alpha * dt_s
            termination_alpha = alpha
            termination_lower_time_s = current_time_s
            termination_lower_temperature = old_temperature.copy()
            termination_lower_moisture = old_moisture.copy()
            termination_upper_temperature = current_temperature.copy()
            termination_upper_moisture = current_moisture.copy()
            termination_lower_max = previous_max
            termination_upper_max = current_max
            # 当前跨越步终点若在烘干时刻之后，不写入60 s结果网格。
            if is_multiple(time_new_s, output_dt_s) and time_new_s <= termination_time_s + 1.0e-9:
                sampled_times.append(float(time_new_s))
                sampled_moisture.append(current_moisture[indices].copy())
            break

        if is_multiple(time_new_s, output_dt_s):
            sampled_times.append(float(time_new_s))
            sampled_moisture.append(current_moisture[indices].copy())
        if is_multiple(time_new_s, TABLE5_DT_S):
            table5_times.append(float(time_new_s))
            table5_values.append(current_moisture[key_indices].copy())

        current_time_s = time_new_s
        previous_max = current_max
        if progress and (is_multiple(time_new_s, TABLE5_DT_S) or time_new_s <= 1.0):
            print(
                f"  已推进 {time_new_s / 3600.0:.4f} h，"
                f"max C={current_max:.10f}，Picard={iterations}"
            )
    else:
        raise RuntimeError("超过时间步保护上限仍未达到烘干阈值")

    if termination_time_s is None:
        raise RuntimeError(
            f"在{max_time_s / 3600.0:g} h内未达到全场阈值 "
            f"max C < {DRYING_THRESHOLD_KGKG:g}"
        )
    assert termination_lower_temperature is not None
    assert termination_lower_moisture is not None
    assert termination_upper_temperature is not None
    assert termination_upper_moisture is not None
    assert termination_alpha is not None

    event_temperature = termination_lower_temperature + termination_alpha * (
        termination_upper_temperature - termination_lower_temperature
    )
    event_moisture = termination_lower_moisture + termination_alpha * (
        termination_upper_moisture - termination_lower_moisture
    )

    return {
        "n_intervals": int(n_intervals),
        "dr_m": float(dr_m),
        "time_step_early_s": float(TIME_STEP_EARLY_S),
        "time_step_long_s": float(time_step_long_s),
        "output_dt_s": float(output_dt_s),
        "radii_m_internal": radii_m,
        "key_indices": key_indices,
        "time_s": np.asarray(sampled_times, dtype=float),
        "radius_cm": OUTPUT_RADIUS_CM.copy(),
        "moisture_kgkg": np.asarray(sampled_moisture, dtype=float),
        "first3_moisture_kgkg": first3,
        "table5_times_s": np.asarray(table5_times, dtype=float),
        "table5_values_kgkg": np.asarray(table5_values, dtype=float)
        if table5_values
        else np.empty((0, KEY_RADIUS_INDICES.size), dtype=float),
        "termination_time_s": float(termination_time_s),
        "termination_alpha": float(termination_alpha),
        "termination_lower_time_s": float(termination_lower_time_s),
        "termination_lower_temperature_C": termination_lower_temperature,
        "termination_lower_moisture_kgkg": termination_lower_moisture,
        "termination_upper_temperature_C": termination_upper_temperature,
        "termination_upper_moisture_kgkg": termination_upper_moisture,
        "termination_event_temperature_C": event_temperature,
        "termination_event_moisture_kgkg": event_moisture,
        "termination_lower_max_kgkg": float(termination_lower_max),
        "termination_upper_max_kgkg": float(termination_upper_max),
        "stable_temperature_C": stable_temperature_C,
        "stable_moisture_kgkg": stable_moisture_kgkg,
        "stable_count": stable_count,
        "iteration_counts": np.asarray(iteration_counts, dtype=int),
        "picard_delta_temperature": np.asarray(delta_temperature, dtype=float),
        "picard_delta_moisture": np.asarray(delta_moisture, dtype=float),
        "early_steps": int(early_steps),
        "long_steps": int(long_steps),
        "min_internal_moisture_kgkg": float(min_moisture),
        "max_internal_moisture_kgkg": float(max_moisture),
        "min_temperature_C": float(min_temperature),
        "max_temperature_C": float(max_temperature),
        "max_positive_step_change_kgkg": float(max_positive_step_change),
        "max_positive_average_change_kgkg": float(max_positive_average_change),
        "max_abs_step_change_kgkg": float(max_abs_step_change),
        "max_radial_increase_kgkg": float(max_radial_increase),
    }


def validate_solution(
    solution: dict[str, Any],
    require_first3: bool = True,
) -> dict[str, Any]:
    """执行终止、有限性、采样、单调性和CN结果的最低检查。"""

    times = np.asarray(solution["time_s"], dtype=float)
    radii = np.asarray(solution["radius_cm"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    lower_C = np.asarray(solution["termination_lower_moisture_kgkg"], dtype=float)
    upper_C = np.asarray(solution["termination_upper_moisture_kgkg"], dtype=float)
    event_C = np.asarray(solution["termination_event_moisture_kgkg"], dtype=float)
    lower_T = np.asarray(solution["termination_lower_temperature_C"], dtype=float)
    upper_T = np.asarray(solution["termination_upper_temperature_C"], dtype=float)
    event_T = np.asarray(solution["termination_event_temperature_C"], dtype=float)
    arrays = (times, radii, moisture, lower_C, upper_C, event_C, lower_T, upper_T, event_T)
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise ValueError("结果包含NaN或Inf")
    if moisture.shape != (times.size, radii.size):
        raise ValueError("规则采样水分场形状错误")
    if times.size < 1 or not np.isclose(times[0], 0.0, atol=1.0e-12):
        raise ValueError("输出时间未从0 s开始")
    if times.size > 1 and not np.allclose(np.diff(times), OUTPUT_DT_S, atol=1.0e-8):
        raise ValueError("输出时间间隔不是60 s")
    termination_time = float(solution["termination_time_s"])
    expected_last = np.floor(termination_time / OUTPUT_DT_S + 1.0e-12) * OUTPUT_DT_S
    if not np.isclose(times[-1], expected_last, atol=1.0e-8):
        raise ValueError("规则采样未止于烘干结束前最后一个60 s网格")
    expected_radii = np.arange(0.0, 2.0000001, 0.1)
    if radii.size != 21 or not np.allclose(radii, expected_radii, atol=1.0e-12):
        raise ValueError("输出半径不是0--2 cm每0.1 cm")
    if np.min(moisture) < -1.0e-10 or np.min(lower_C) < -1.0e-10 or np.min(upper_C) < -1.0e-10:
        raise ValueError("水分场出现明显负值")

    threshold = DRYING_THRESHOLD_KGKG
    lower_max = float(solution["termination_lower_max_kgkg"])
    upper_max = float(solution["termination_upper_max_kgkg"])
    event_max = float(np.max(event_C))
    if not lower_max >= threshold:
        raise ValueError("终止前层没有保持max C >= 0.15")
    if not upper_max < threshold:
        raise ValueError("终止后层没有满足全场max C < 0.15")
    if not np.isclose(lower_max, np.max(lower_C), atol=1.0e-12):
        raise ValueError("终止前max C不是完整内部场最大值")
    if not np.isclose(upper_max, np.max(upper_C), atol=1.0e-12):
        raise ValueError("终止后max C不是完整内部场最大值")
    if abs(event_max - threshold) > 1.0e-8:
        raise ValueError(f"插值终止场max C偏离阈值过大: {event_max:.12g}")

    if require_first3:
        first3 = solution["first3_moisture_kgkg"]
        if first3 is None or not np.all(np.isfinite(first3)):
            raise ValueError("未完整记录0--3 h连续状态")
    sampled_delta = np.diff(moisture, axis=0)
    max_positive_sampled = float(np.max(sampled_delta)) if sampled_delta.size else 0.0
    if np.min(event_C) < -1.0e-10:
        raise ValueError("插值终止场出现明显负值")
    iterations = np.asarray(solution["iteration_counts"], dtype=int)
    if iterations.size == 0 or int(np.max(iterations)) > PICARD_MAX_ITER:
        raise ValueError("Picard迭代记录错误")

    return {
        "n_intervals": int(solution["n_intervals"]),
        "dr_cm": float(solution["dr_m"]) * 100.0,
        "time_step_early_s": float(solution["time_step_early_s"]),
        "time_step_long_s": float(solution["time_step_long_s"]),
        "termination_time_s": termination_time,
        "termination_time_h": termination_time / 3600.0,
        "termination_lower_time_s": float(solution["termination_lower_time_s"]),
        "termination_upper_time_s": float(solution["termination_lower_time_s"])
        + (
            float(solution["time_step_long_s"])
            if float(solution["termination_lower_time_s"]) >= AIR_DATA_END_S - 1.0e-10
            else TIME_STEP_EARLY_S
        ),
        "termination_lower_max_kgkg": lower_max,
        "termination_upper_max_kgkg": upper_max,
        "termination_event_max_kgkg": event_max,
        "termination_event_max_index": int(np.argmax(event_C)),
        "termination_event_center_kgkg": float(event_C[0]),
        "termination_event_surface_kgkg": float(event_C[-1]),
        "min_internal_moisture_kgkg": float(solution["min_internal_moisture_kgkg"]),
        "max_internal_moisture_kgkg": float(solution["max_internal_moisture_kgkg"]),
        "min_temperature_C": float(solution["min_temperature_C"]),
        "max_temperature_C": float(solution["max_temperature_C"]),
        "max_positive_step_change_kgkg": float(solution["max_positive_step_change_kgkg"]),
        "max_positive_average_change_kgkg": float(
            solution["max_positive_average_change_kgkg"]
        ),
        "max_positive_sampled_change_kgkg": max_positive_sampled,
        "max_abs_step_change_kgkg": float(solution["max_abs_step_change_kgkg"]),
        "max_radial_increase_kgkg": float(solution["max_radial_increase_kgkg"]),
        "max_picard_iterations": int(np.max(iterations)),
        "mean_picard_iterations": float(np.mean(iterations)),
        "sample_count": int(times.size),
        "internal_node_count": int(upper_C.size),
        "stable_temperature_C": float(solution["stable_temperature_C"]),
        "stable_moisture_kgkg": float(solution["stable_moisture_kgkg"]),
        "stable_count": int(solution["stable_count"]),
        "early_steps": int(solution["early_steps"]),
        "long_steps": int(solution["long_steps"]),
    }


def compare_with_task2(
    solution: dict[str, Any],
    task2_csv_path: str | Path = DEFAULT_TASK2_CSV_PATH,
) -> dict[str, Any]:
    """将本轮N=1600 CN结果的0--3 h 1 s网格与既有task2 CSV对照。"""

    first3 = solution["first3_moisture_kgkg"]
    if first3 is None or not np.all(np.isfinite(first3)):
        raise ValueError("缺少问题三0--3 h连续场")
    frame = pd.read_csv(Path(task2_csv_path))
    required = {"time_s", "radius_cm", "moisture_kgkg"}
    if not required.issubset(frame.columns):
        raise ValueError("问题二CSV缺少比较字段")
    expected_rows = 10801 * 21
    if len(frame) != expected_rows:
        raise ValueError(f"问题二CSV记录数为{len(frame)}，不是{expected_rows}")
    task2_values = frame["moisture_kgkg"].to_numpy(dtype=float).reshape((10801, 21))
    raw_diff = np.abs(first3 - task2_values)
    rounded_diff = np.abs(np.round(first3, 4) - np.round(task2_values, 4))
    return {
        "rows_compared": expected_rows,
        "max_abs_difference_raw_kgkg": float(np.max(raw_diff)),
        "max_abs_difference_4dp_kgkg": float(np.max(rounded_diff)),
    }


def table5_from_solution(solution: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """返回表5常规6 h行和插值终止行。"""

    regular_times = np.asarray(solution["table5_times_s"], dtype=float)
    regular_values = np.asarray(solution["table5_values_kgkg"], dtype=float)
    event = np.asarray(solution["termination_event_moisture_kgkg"], dtype=float)
    event_indices = np.asarray(solution["key_indices"], dtype=int)
    event_values = event[event_indices]
    if regular_values.ndim != 2 or regular_values.shape[1] != KEY_RADIUS_INDICES.size:
        raise ValueError("表5常规行形状错误")
    return regular_times, np.vstack((regular_values, event_values))


def print_table5(solution: dict[str, Any]) -> None:
    """打印论文表5：6 h行至结束前，以及精确插值结束行。"""

    regular_times, rows = table5_from_solution(solution)
    termination_time_h = float(solution["termination_time_s"]) / 3600.0
    print("表5 水分浓度 / kg/kg（列为0、0.5、1.0、1.5、2.0 cm）")
    print("时间/h,0 cm,0.5 cm,1.0 cm,1.5 cm,2.0 cm")
    for index, time_value in enumerate(regular_times):
        print(
            f"{time_value / 3600.0:.1f},"
            + ",".join(f"{float(value):.4f}" for value in rows[index])
        )
    print(
        f"烘干结束时间 ({termination_time_h:.6f} h),"
        + ",".join(f"{float(value):.4f}" for value in rows[-1])
    )


def write_result_xlsx(
    solution: dict[str, Any],
    output_path: str | Path = DEFAULT_XLSX_PATH,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> None:
    """以result3模板为基础写入60 s水分结果。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(Path(template_path))
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"result3模板工作表错误: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    times = np.asarray(solution["time_s"], dtype=float)
    radii = np.asarray(solution["radius_cm"], dtype=float)
    values = np.asarray(solution["moisture_kgkg"], dtype=float)
    header_style = copy(worksheet.cell(row=1, column=2)._style)
    time_style = copy(worksheet.cell(row=2, column=1)._style)
    value_style = copy(worksheet.cell(row=2, column=2)._style)
    if worksheet.max_row > 1:
        worksheet.delete_rows(2, worksheet.max_row - 1)
    for column, radius in enumerate(radii, start=2):
        cell = worksheet.cell(row=1, column=column, value=round(float(radius), 1))
        cell._style = copy(header_style)
        cell.number_format = "0.0"
    for row, time_value in enumerate(times, start=2):
        time_cell = worksheet.cell(row=row, column=1, value=int(round(time_value)))
        time_cell._style = copy(time_style)
        time_cell.number_format = "0"
        for column, value in enumerate(values[row - 2], start=2):
            cell = worksheet.cell(
                row=row,
                column=column,
                value=float(f"{float(value):.4f}"),
            )
            cell._style = copy(value_style)
            cell.number_format = "0.0000"
    workbook.save(output_path)


def write_result_csv(
    solution: dict[str, Any],
    output_path: str | Path = DEFAULT_CSV_PATH,
) -> None:
    """写入题目要求的三列long-format CSV。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    times = np.asarray(solution["time_s"], dtype=float)
    radii = np.asarray(solution["radius_cm"], dtype=float)
    values = np.asarray(solution["moisture_kgkg"], dtype=float)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "radius_cm", "moisture_kgkg"])
        for time_index, time_value in enumerate(times):
            for radius_index, radius_value in enumerate(radii):
                writer.writerow(
                    [
                        int(round(time_value)),
                        f"{radius_value:.1f}",
                        f"{values[time_index, radius_index]:.4f}",
                    ]
                )


def validate_written_outputs(
    solution: dict[str, Any],
    xlsx_path: str | Path = DEFAULT_XLSX_PATH,
    csv_path: str | Path = DEFAULT_CSV_PATH,
) -> dict[str, Any]:
    """回读CSV/XLSX，检查结构和全部对应水分值。"""

    expected = np.round(np.asarray(solution["moisture_kgkg"], dtype=float), 4)
    expected_times = np.asarray(solution["time_s"], dtype=int)
    expected_radii = np.asarray(solution["radius_cm"], dtype=float)
    frame = pd.read_csv(Path(csv_path))
    expected_columns = ["time_s", "radius_cm", "moisture_kgkg"]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"CSV字段错误: {list(frame.columns)}")
    expected_rows = expected_times.size * expected_radii.size
    if len(frame) != expected_rows:
        raise ValueError(f"CSV行数为{len(frame)}，不是{expected_rows}")
    csv_times = frame["time_s"].to_numpy(dtype=int)
    csv_radii = frame["radius_cm"].to_numpy(dtype=float)
    csv_values = frame["moisture_kgkg"].to_numpy(dtype=float).reshape(expected.shape)
    if not np.array_equal(csv_times, np.repeat(expected_times, expected_radii.size)):
        raise ValueError("CSV时间结构错误")
    if not np.allclose(csv_radii, np.tile(expected_radii, expected_times.size), atol=1.0e-12):
        raise ValueError("CSV半径结构错误")

    workbook = load_workbook(Path(xlsx_path), read_only=True, data_only=True)
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"XLSX工作表错误: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    if (worksheet.max_row, worksheet.max_column) != (
        expected_times.size + 1,
        expected_radii.size + 1,
    ):
        raise ValueError("XLSX尺寸错误")
    rows = list(
        worksheet.iter_rows(
            min_row=1,
            max_row=worksheet.max_row,
            min_col=1,
            max_col=worksheet.max_column,
            values_only=True,
        )
    )
    xlsx_times = np.asarray([row[0] for row in rows[1:]], dtype=int)
    xlsx_radii = np.asarray(rows[0][1:], dtype=float)
    xlsx_values = np.asarray([row[1:] for row in rows[1:]], dtype=float)
    if not np.array_equal(xlsx_times, expected_times) or not np.allclose(
        xlsx_radii, expected_radii, atol=1.0e-12
    ):
        raise ValueError("XLSX时间或半径结构错误")
    xlsx_values = np.round(xlsx_values, 4)
    if not np.array_equal(csv_values, xlsx_values):
        raise ValueError("CSV与XLSX对应值不一致")
    if not np.array_equal(csv_values, expected):
        raise ValueError("答案文件与求解器采样值不一致")
    return {
        "csv_rows": int(len(frame)),
        "xlsx_shape": (int(worksheet.max_row), int(worksheet.max_column)),
        "max_abs_csv_xlsx_difference_kgkg": float(np.max(np.abs(csv_values - xlsx_values))),
        "max_abs_file_solver_difference_kgkg": float(np.max(np.abs(csv_values - expected))),
    }


def compare_sensitivity_tables(
    base: dict[str, Any], other: dict[str, Any]
) -> dict[str, float]:
    """比较两个解在相同6 h表5行上的终止时刻和水分值。"""

    base_times, base_rows = table5_from_solution(base)
    other_times, other_rows = table5_from_solution(other)
    common = min(base_times.size, other_times.size)
    if common == 0:
        table_difference = 0.0
    else:
        table_difference = float(np.max(np.abs(base_rows[:common] - other_rows[:common])))
    return {
        "termination_time_difference_h": float(
            other["termination_time_s"] - base["termination_time_s"]
        )
        / 3600.0,
        "table5_common_max_abs_difference_kgkg": table_difference,
        "common_regular_rows": int(common),
    }


def run_grid_sensitivity(
    data_path: str | Path,
    max_time_s: float,
    progress: bool = False,
) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """运行N=200/400/800/1600的同一CN模型空间加密检查。"""

    grid_solutions: dict[int, dict[str, Any]] = {}
    grid_summaries: dict[int, dict[str, Any]] = {}
    for n in (200, 400, 800, 1600):
        started = wall_time.perf_counter()
        candidate = solve_task3(
            data_path=data_path,
            n_intervals=n,
            time_step_long_s=TIME_STEP_LONG_DEFAULT_S,
            output_dt_s=OUTPUT_DT_S,
            max_time_s=max_time_s,
            progress=progress,
            collect_first3=False,
        )
        candidate_summary = validate_solution(candidate, require_first3=False)
        grid_solutions[n] = candidate
        grid_summaries[n] = {
            **candidate_summary,
            "runtime_s": wall_time.perf_counter() - started,
        }
        print(
            f"空间网格 N={n}: t_dry={candidate_summary['termination_time_h']:.8f} h, "
            f"耗时={grid_summaries[n]['runtime_s']:.2f} s"
        )
    return grid_solutions, grid_summaries


def print_grid_sensitivity(grid_summaries: dict[int, dict[str, Any]]) -> None:
    print("空间网格收敛（同一CN/调和平均/1 s+10 s模型）")
    previous = None
    for n in sorted(grid_summaries):
        summary = grid_summaries[n]
        difference = "—" if previous is None else f"{summary['termination_time_h'] - previous:.8f}"
        print(
            f"N={n:4d}, dr={summary['dr_cm']:.5f} cm, "
            f"t_dry={summary['termination_time_h']:.8f} h, "
            f"相对前一网格={difference} h"
        )
        previous = summary["termination_time_h"]


def main() -> None:
    parser = argparse.ArgumentParser(description="求解A题问题三CN长期烘干模型")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--task2-csv", type=Path, default=DEFAULT_TASK2_CSV_PATH)
    parser.add_argument("--n", type=int, default=N_DEFAULT)
    parser.add_argument("--time-step-long", type=float, default=TIME_STEP_LONG_DEFAULT_S)
    parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
    parser.add_argument("--no-write", action="store_true", help="不生成答案文件")
    parser.add_argument("--skip-sensitivity", action="store_true", help="跳过N/长期时间步敏感性")
    parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
    args = parser.parse_args()

    started = wall_time.perf_counter()
    print(
        "问题三CN求解开始: "
        f"N={args.n}, dr={RADIUS_M / args.n:g}m, "
        f"dt_early={TIME_STEP_EARLY_S:g}s, dt_long={args.time_step_long:g}s, "
        f"output_dt={OUTPUT_DT_S:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
    )
    solution = solve_task3(
        data_path=args.data_path,
        n_intervals=args.n,
        time_step_long_s=args.time_step_long,
        output_dt_s=OUTPUT_DT_S,
        max_time_s=args.max_time,
        progress=args.progress,
        collect_first3=True,
    )
    summary = validate_solution(solution, require_first3=True)
    air_time, air_temperature, air_moisture = load_air_data(args.data_path)
    stable_T, stable_C, stable_count = stable_air_means(air_time, air_temperature, air_moisture)
    print(
        f"稳定段均值（附件实时计算，{STABLE_START_S:g}--{AIR_DATA_END_S:g}s，"
        f"{stable_count}点）: T_air={stable_T:.12f} C, C_air={stable_C:.12f} kg/kg"
    )
    print(f"基本数值检查: {summary}")
    comparison = compare_with_task2(solution, args.task2_csv)
    print(f"0--3 h连续状态与既有task2 CSV全量比较: {comparison}")

    if not args.skip_sensitivity:
        _grid_solutions, grid_summaries = run_grid_sensitivity(
            args.data_path, args.max_time, progress=False
        )
        print_grid_sensitivity(grid_summaries)
        long5_started = wall_time.perf_counter()
        long5_solution = solve_task3(
            data_path=args.data_path,
            n_intervals=args.n,
            time_step_long_s=5.0,
            output_dt_s=OUTPUT_DT_S,
            max_time_s=args.max_time,
            progress=False,
            collect_first3=False,
        )
        long5_summary = validate_solution(long5_solution, require_first3=False)
        long5_difference = compare_sensitivity_tables(solution, long5_solution)
        print(
            "N={:d} 长期时间步敏感性: dt_long=10 s -> 5 s, "
            "t_dry={:.8f} h -> {:.8f} h, 差={:.8f} h, "
            "表5公共行最大差={:.8g} kg/kg, 耗时={:.2f} s".format(
                args.n,
                summary["termination_time_h"],
                long5_summary["termination_time_h"],
                long5_difference["termination_time_difference_h"],
                long5_difference["table5_common_max_abs_difference_kgkg"],
                wall_time.perf_counter() - long5_started,
            )
        )
    else:
        print("已跳过空间网格和长期时间步敏感性")

    if not args.no_write:
        template_hash_before = hashlib.sha256(DEFAULT_TEMPLATE_PATH.read_bytes()).hexdigest()
        write_result_xlsx(solution)
        write_result_csv(solution)
        output_summary = validate_written_outputs(solution)
        template_hash_after = hashlib.sha256(DEFAULT_TEMPLATE_PATH.read_bytes()).hexdigest()
        if template_hash_before != template_hash_after:
            raise RuntimeError("result3模板在输出过程中被修改")
        print(f"答案文件回读验收: {output_summary}")
        print(f"模板SHA-256（前后相同）: {template_hash_after}")
        print(f"已生成: {DEFAULT_XLSX_PATH}")
        print(f"已生成: {DEFAULT_CSV_PATH}")
    else:
        print("--no-write: 未生成或覆盖答案文件")

    print_table5(solution)
    print(f"烘干结束时间 = {summary['termination_time_h']:.8f} h")
    print(f"总耗时: {wall_time.perf_counter() - started:.2f} s")


if __name__ == "__main__":
    main()
