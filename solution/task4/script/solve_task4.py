"""A题问题四：药材收缩条件下的移动边界热湿耦合求解器。

空间坐标采用固定的

    xi = r / R(t), 0 <= xi <= 1,

并在固定 xi 网格上用径向控制体积法离散。时间方向采用后向欧拉；每个
内部时间步内用 Picard 迭代更新附录 4 的状态相关物性。半径 R(t) 来自
附件 2 的分段线性插值，移动坐标项 b*xi*T_xi（b=-Rdot/R）用一阶后向
迎风差分，并与扩散项一起隐式求解。

求解器同时提供 result4.xlsx、论文表6和完整长表CSV的生成与独立回读
验收；--no-write 可只运行数值求解和计算验证而不创建答案文件。
"""

from __future__ import annotations

import argparse
import csv
import re
import time as wall_time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from scipy.linalg import solve_banded


# 题目和问题二/三已确定的环境、初始条件及边界传递参数。
RADIUS_INITIAL_M = 0.02
LENGTH_M = 0.25
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE_KGKG = 2.55
HEAT_TRANSFER_W_M2_K = 25.0
MASS_TRANSFER_M_S = 8.0e-7

# 问题四数值默认值：最终结果采用加密网格；粗解仅作为对照。
N_DEFAULT = 320  # xi 区间数，dxi=1/320
TIME_STEP_S_DEFAULT = 0.5
OUTPUT_DT_S = 60.0
DRYING_THRESHOLD_KGKG = 0.15
EVENT_TOL_S = 1.0e-3

PICARD_TOL_T_C = 1.0e-8
PICARD_TOL_C_KGKG = 1.0e-10
PICARD_MAX_ITER = 50

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AIR_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
DEFAULT_RADIUS_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件2.xlsx"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "problem" / "附件" / "附件3" / "result4.xlsx"
DEFAULT_ANSWER_DIR = Path(__file__).resolve().parents[1] / "answer"
DEFAULT_XLSX_PATH = DEFAULT_ANSWER_DIR / "result4.xlsx"
DEFAULT_PAPER_PATH = DEFAULT_ANSWER_DIR / "task4_paper_table.xlsx"
DEFAULT_CSV_PATH = DEFAULT_ANSWER_DIR / "task4_all_answers.csv"
# 附件 2 的最后一个数据时刻；求解不会超出该时刻，也不会外推 R(t)。
DEFAULT_MAX_TIME_S = 259200.0

OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
PAPER_RADIUS_CM = np.array([0.0, 0.5, 1.0], dtype=float)
CSV_COLUMNS = [
    "record_type",
    "time_s",
    "time_h",
    "radius_cm",
    "r_cm",
    "is_surface",
    "temperature_C",
    "moisture_kgkg",
]


def _required_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> dict[str, Any]:
    """按去除首尾空格后的中文列名返回原始列映射。"""

    mapping = {str(column).strip(): column for column in frame.columns}
    missing = [name for name in required if name not in mapping]
    if missing:
        raise ValueError(
            f"附件缺少必需列 {missing!r}；实际列为 {list(frame.columns)!r}"
        )
    return mapping


def load_air_data(
    path: str | Path = DEFAULT_AIR_DATA_PATH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取附件 1；求解区间外的边界值由 np.interp 保持末值。"""

    frame = pd.read_excel(Path(path))
    columns = _required_columns(frame, ("时间", "温度", "水分浓度"))
    selected = frame[[columns["时间"], columns["温度"], columns["水分浓度"]]].copy()
    selected.columns = ["时间", "温度", "水分浓度"]
    for column in selected.columns:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
    time_s = selected["时间"].to_numpy(dtype=float)
    temperature_C = selected["温度"].to_numpy(dtype=float)
    moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
    values = np.column_stack((time_s, temperature_C, moisture_kgkg))
    if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
        raise ValueError("附件1时间必须包含至少两个严格递增时间点")
    if time_s[0] > 1.0e-10 or not np.all(np.isfinite(values)):
        raise ValueError("附件1时间必须从0开始且数据必须有限")
    return time_s, temperature_C, moisture_kgkg


def load_radius_data(
    path: str | Path = DEFAULT_RADIUS_DATA_PATH,
) -> tuple[np.ndarray, np.ndarray]:
    """读取附件 2 的时间/半径，并将半径从 cm 转为 m。"""

    frame = pd.read_excel(Path(path))
    columns = _required_columns(frame, ("时间", "半径"))
    selected = frame[[columns["时间"], columns["半径"]]].copy()
    selected.columns = ["时间", "半径"]
    for column in selected.columns:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
    time_s = selected["时间"].to_numpy(dtype=float)
    radius_cm = selected["半径"].to_numpy(dtype=float)
    radius_m = radius_cm / 100.0
    values = np.column_stack((time_s, radius_cm, radius_m))
    if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
        raise ValueError("附件2时间必须包含至少两个严格递增时间点")
    if time_s[0] > 1.0e-10 or not np.all(np.isfinite(values)):
        raise ValueError("附件2时间必须从0开始且数据必须有限")
    if np.any(radius_m <= 0.0):
        raise ValueError("附件2半径必须为正")
    if not np.isclose(radius_m[0], RADIUS_INITIAL_M, rtol=0.0, atol=1.0e-12):
        raise ValueError(
            f"附件2初始半径为 {radius_cm[0]:g} cm，不是题设的 2 cm"
        )
    if np.any(np.diff(radius_m) > 1.0e-12):
        raise ValueError("附件2半径必须单调不增，不能为移动边界使用非物理膨胀数据")
    return time_s, radius_m


def radius_at(time_s: float, radius_time_s: np.ndarray, radius_m: np.ndarray) -> float:
    """在附件2覆盖范围内分段线性插值 R(t)，不允许无说明外推。"""

    if time_s < radius_time_s[0] - 1.0e-10 or time_s > radius_time_s[-1] + 1.0e-10:
        raise ValueError(
            f"求解时刻 {time_s:g}s 超出附件2的 [{radius_time_s[0]:g}, "
            f"{radius_time_s[-1]:g}]s 覆盖范围，禁止外推半径"
        )
    clipped_time = min(max(float(time_s), float(radius_time_s[0])), float(radius_time_s[-1]))
    return float(np.interp(clipped_time, radius_time_s, radius_m))


def _air_at(time_s: float, air_time_s: np.ndarray, values: np.ndarray) -> float:
    """附件1内分段线性，14400 s 后保持最后观测值。"""

    return float(np.interp(float(time_s), air_time_s, values))


def fixed_xi_geometry(n_intervals: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """返回 xi 节点、xi 面、固定 xi 控制体测度和 dxi。"""

    if n_intervals < 2:
        raise ValueError("xi 区间数至少为2")
    dxi = 1.0 / float(n_intervals)
    xi = np.linspace(0.0, 1.0, n_intervals + 1)
    faces = 0.5 * (xi[:-1] + xi[1:])
    measure = np.empty_like(xi)
    measure[0] = 0.5 * faces[0] ** 2
    measure[1:-1] = 0.5 * (faces[1:] ** 2 - faces[:-1] ** 2)
    measure[-1] = 0.5 * (1.0 - faces[-1] ** 2)
    if not np.isclose(np.sum(measure), 0.5, rtol=0.0, atol=1.0e-14):
        raise ValueError("固定xi控制体测度未覆盖 [0,1] 的径向积分测度")
    return xi, faces, measure, dxi


def material_properties(
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """附录4物性；指数公式中的温度显式转换为 Kelvin。"""

    temperature_C = np.asarray(temperature_C, dtype=float)
    moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
    if temperature_C.shape != moisture_kgkg.shape:
        raise ValueError("温度和水分数组形状不一致")
    concentration = np.maximum(moisture_kgkg, 1.0e-12)
    temperature_K = temperature_C + 273.15
    if np.any(~np.isfinite(temperature_K)) or np.any(temperature_K <= 0.0):
        raise ValueError("附录4物性计算遇到非正或非有限 Kelvin 温度")

    rho = 760.0 + 90.0 * concentration
    cp = 1850.0 + 2150.0 * concentration / (concentration + 1.0)
    conductivity = 0.12 + 0.20 * concentration / (concentration + 1.0)
    diffusivity = 4.2e-4 * np.exp(-0.30 / concentration) * np.exp(
        -3850.0 / temperature_K
    )
    return rho, cp, conductivity, diffusivity


def _solve_tridiagonal(
    lower: np.ndarray,
    diagonal: np.ndarray,
    upper: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    """解三对角系统；输入 lower/upper 长度为 n-1。"""

    n = diagonal.size
    banded = np.zeros((3, n), dtype=float)
    banded[0, 1:] = upper
    banded[1, :] = diagonal
    banded[2, :-1] = lower
    solution = solve_banded((1, 1), banded, rhs, check_finite=False)
    if not np.all(np.isfinite(solution)):
        raise RuntimeError("三对角线性系统求解得到 NaN 或 Inf")
    return solution


def _assemble_temperature_system(
    old_temperature_C: np.ndarray,
    guess_temperature_C: np.ndarray,
    guess_moisture_kgkg: np.ndarray,
    xi: np.ndarray,
    faces: np.ndarray,
    measure: np.ndarray,
    dxi: float,
    radius_m: float,
    radius_rate_m_s: float,
    dt_s: float,
    air_temperature_C: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """组装固定xi坐标下的温度后向欧拉矩阵。"""

    rho, cp, conductivity, _ = material_properties(
        guess_temperature_C, guess_moisture_kgkg
    )
    storage = rho * cp * measure
    # 继承 task2/task3 实际求解器的界面物性算术平均；问题四只改变
    # 题目指定的物性公式和移动边界，不额外改变固定边界模型的界面离散。
    face_conductivity = 0.5 * (conductivity[:-1] + conductivity[1:])
    # 固定xi控制体扩散导通量：1/R^2 * xi_face*k_face/dxi。
    conductance = face_conductivity * faces / (radius_m**2 * dxi)
    b = -radius_rate_m_s / radius_m
    if b < -1.0e-12:
        raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
    b = max(0.0, b)
    # PDE 的移动项为 b*xi*T_xi，b>=0 时使用 (T_j-T_{j-1})/dxi。
    advection = storage * b * xi / dxi

    diagonal = storage.copy()
    lower = np.zeros(storage.size - 1, dtype=float)
    upper = np.zeros(storage.size - 1, dtype=float)
    rhs = storage * old_temperature_C
    diagonal += dt_s * advection
    lower -= dt_s * advection[1:]

    # 中心自然零通量；中心项没有左邻接、没有移动项（xi=0）。
    diagonal[0] += dt_s * conductance[0]
    upper[0] -= dt_s * conductance[0]
    # 内部控制体。
    if storage.size > 2:
        left = conductance[:-1]
        right = conductance[1:]
        diagonal[1:-1] += dt_s * (left + right)
        # row j=1..n-2 的下/上三对角项分别对应 g_{j-1}/g_j。
        lower[:-1] -= dt_s * left
        upper[1:] -= dt_s * right
    # 移动表面 Robin：-(k/R)T_xi=h(Ts-Tair)，换成 h/R 的边界导通量。
    boundary_conductance = HEAT_TRANSFER_W_M2_K / radius_m
    diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
    lower[-1] -= dt_s * conductance[-1]
    rhs[-1] += dt_s * boundary_conductance * air_temperature_C
    return lower, diagonal, upper, rhs


def _assemble_moisture_system(
    old_moisture_kgkg: np.ndarray,
    guess_temperature_C: np.ndarray,
    guess_moisture_kgkg: np.ndarray,
    xi: np.ndarray,
    faces: np.ndarray,
    measure: np.ndarray,
    dxi: float,
    radius_m: float,
    radius_rate_m_s: float,
    dt_s: float,
    air_moisture_kgkg: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """组装固定xi坐标下的水分后向欧拉矩阵。"""

    _, _, _, diffusivity = material_properties(
        guess_temperature_C, guess_moisture_kgkg
    )
    storage = measure.copy()
    # 同 task2/task3，界面扩散系数使用算术平均。
    face_diffusivity = 0.5 * (diffusivity[:-1] + diffusivity[1:])
    conductance = face_diffusivity * faces / (radius_m**2 * dxi)
    b = -radius_rate_m_s / radius_m
    if b < -1.0e-12:
        raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
    b = max(0.0, b)
    advection = storage * b * xi / dxi

    diagonal = storage.copy()
    lower = np.zeros(storage.size - 1, dtype=float)
    upper = np.zeros(storage.size - 1, dtype=float)
    rhs = storage * old_moisture_kgkg
    diagonal += dt_s * advection
    lower -= dt_s * advection[1:]

    diagonal[0] += dt_s * conductance[0]
    upper[0] -= dt_s * conductance[0]
    if storage.size > 2:
        left = conductance[:-1]
        right = conductance[1:]
        diagonal[1:-1] += dt_s * (left + right)
        lower[:-1] -= dt_s * left
        upper[1:] -= dt_s * right
    boundary_conductance = MASS_TRANSFER_M_S / radius_m
    diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
    lower[-1] -= dt_s * conductance[-1]
    rhs[-1] += dt_s * boundary_conductance * air_moisture_kgkg
    return lower, diagonal, upper, rhs


def _picard_step(
    old_temperature_C: np.ndarray,
    old_moisture_kgkg: np.ndarray,
    xi: np.ndarray,
    faces: np.ndarray,
    measure: np.ndarray,
    dxi: float,
    radius_old_m: float,
    radius_new_m: float,
    dt_s: float,
    air_temperature_C: float,
    air_moisture_kgkg: float,
) -> tuple[np.ndarray, np.ndarray, int, float, float]:
    """一个移动边界时间步内的 Picard 热湿耦合迭代。"""

    if dt_s <= 0.0:
        raise ValueError("Picard 时间步必须为正")
    radius_rate_m_s = (radius_new_m - radius_old_m) / dt_s
    guess_temperature_C = old_temperature_C.copy()
    guess_moisture_kgkg = old_moisture_kgkg.copy()
    last_delta_temperature = np.inf
    last_delta_moisture = np.inf

    for iteration in range(1, PICARD_MAX_ITER + 1):
        lower_T, diagonal_T, upper_T, rhs_T = _assemble_temperature_system(
            old_temperature_C,
            guess_temperature_C,
            guess_moisture_kgkg,
            xi,
            faces,
            measure,
            dxi,
            radius_new_m,
            radius_rate_m_s,
            dt_s,
            air_temperature_C,
        )
        new_temperature_C = _solve_tridiagonal(
            lower_T, diagonal_T, upper_T, rhs_T
        )
        lower_C, diagonal_C, upper_C, rhs_C = _assemble_moisture_system(
            old_moisture_kgkg,
            guess_temperature_C,
            guess_moisture_kgkg,
            xi,
            faces,
            measure,
            dxi,
            radius_new_m,
            radius_rate_m_s,
            dt_s,
            air_moisture_kgkg,
        )
        new_moisture_kgkg = _solve_tridiagonal(
            lower_C, diagonal_C, upper_C, rhs_C
        )
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
            if np.min(new_moisture_kgkg) < -1.0e-10:
                raise RuntimeError("Picard 步得到明显负水分浓度")
            return (
                new_temperature_C,
                np.maximum(new_moisture_kgkg, 0.0),
                iteration,
                last_delta_temperature,
                last_delta_moisture,
            )
        guess_temperature_C = new_temperature_C
        guess_moisture_kgkg = new_moisture_kgkg

    raise RuntimeError(
        "问题四 Picard 迭代未收敛: "
        f"dt={dt_s:g}s, iter={PICARD_MAX_ITER}, "
        f"max|dT|={last_delta_temperature:.3e}, "
        f"max|dC|={last_delta_moisture:.3e}"
    )


def _max_info(
    moisture_kgkg: np.ndarray,
    xi: np.ndarray,
    radius_m: float,
) -> tuple[float, int, float, float]:
    index = int(np.argmax(moisture_kgkg))
    maximum = float(moisture_kgkg[index])
    xi_position = float(xi[index])
    radius_position_m = xi_position * radius_m
    return maximum, index, xi_position, radius_position_m


def _event_bisection(
    lower_time_s: float,
    lower_temperature_C: np.ndarray,
    lower_moisture_kgkg: np.ndarray,
    lower_max_kgkg: float,
    upper_time_s: float,
    upper_temperature_C: np.ndarray,
    upper_moisture_kgkg: np.ndarray,
    upper_max_kgkg: float,
    xi: np.ndarray,
    faces: np.ndarray,
    measure: np.ndarray,
    dxi: float,
    radius_time_s: np.ndarray,
    radius_m: np.ndarray,
    air_time_s: np.ndarray,
    air_temperature_C: np.ndarray,
    air_moisture_kgkg: np.ndarray,
) -> dict[str, Any]:
    """首次跨阈值后，从固定 base 状态二分终止时刻。

    每个候选时刻都计算统一函数

        F(t) = max_xi C(t; base_state -> t) - 0.15,

    其中 ``base_state`` 是首次跨阈值时间步前的状态。lower/upper 只更新
    候选时刻及其由 base_state 直接积分得到的状态，不能把更新后的 lower
    状态作为下一次候选的起点。
    """

    if not (lower_max_kgkg >= DRYING_THRESHOLD_KGKG):
        raise ValueError("事件二分下端不在阈值上方")
    if not (upper_max_kgkg < DRYING_THRESHOLD_KGKG):
        raise ValueError("事件二分上端未严格低于阈值")
    # 固定首次跨阈值前的 base 状态；所有候选都从它重新推进。
    base_time = float(lower_time_s)
    base_temperature = lower_temperature_C.copy()
    base_moisture = lower_moisture_kgkg.copy()
    base_radius = radius_at(base_time, radius_time_s, radius_m)

    lower_time = base_time
    upper_time = float(upper_time_s)
    lower_temperature = base_temperature.copy()
    lower_moisture = base_moisture.copy()
    lower_max = float(lower_max_kgkg)
    upper_temperature = upper_temperature_C.copy()
    upper_moisture = upper_moisture_kgkg.copy()
    upper_max = float(upper_max_kgkg)

    while upper_time - lower_time > EVENT_TOL_S:
        midpoint = 0.5 * (lower_time + upper_time)
        midpoint_radius = radius_at(midpoint, radius_time_s, radius_m)
        midpoint_temperature, midpoint_moisture, _, _, _ = _picard_step(
            base_temperature,
            base_moisture,
            xi,
            faces,
            measure,
            dxi,
            base_radius,
            midpoint_radius,
            midpoint - base_time,
            _air_at(midpoint, air_time_s, air_temperature_C),
            _air_at(midpoint, air_time_s, air_moisture_kgkg),
        )
        midpoint_max, _, _, _ = _max_info(
            midpoint_moisture, xi, midpoint_radius
        )
        if midpoint_max < DRYING_THRESHOLD_KGKG:
            upper_time = midpoint
            upper_temperature = midpoint_temperature
            upper_moisture = midpoint_moisture
            upper_max = midpoint_max
        else:
            lower_time = midpoint
            lower_temperature = midpoint_temperature
            lower_moisture = midpoint_moisture
            lower_max = midpoint_max

    upper_radius = radius_at(upper_time, radius_time_s, radius_m)
    maximum, index, xi_position, radius_position_m = _max_info(
        upper_moisture, xi, upper_radius
    )
    lower_radius = radius_at(lower_time, radius_time_s, radius_m)
    lower_max_check, lower_index, lower_xi, lower_position_m = _max_info(
        lower_moisture, xi, lower_radius
    )
    if not np.isclose(maximum, upper_max, rtol=0.0, atol=1.0e-12):
        raise RuntimeError("事件二分上端最大值记录不一致")
    if not np.isclose(lower_max_check, lower_max, rtol=0.0, atol=1.0e-12):
        raise RuntimeError("事件二分下端最大值记录不一致")
    return {
        "termination_time_s": float(upper_time),
        "termination_temperature_internal_C": upper_temperature,
        "termination_moisture_internal_kgkg": upper_moisture,
        "termination_max_kgkg": float(maximum),
        "termination_max_index": int(index),
        "termination_max_xi": float(xi_position),
        "termination_max_radius_m": float(radius_position_m),
        "termination_radius_m": float(upper_radius),
        "termination_lower_time_s": float(lower_time),
        "termination_lower_temperature_internal_C": lower_temperature,
        "termination_lower_moisture_internal_kgkg": lower_moisture,
        "termination_lower_max_kgkg": float(lower_max_check),
        "termination_lower_max_index": int(lower_index),
        "termination_lower_max_xi": float(lower_xi),
        "termination_lower_max_radius_m": float(lower_position_m),
        "termination_lower_radius_m": float(lower_radius),
        "termination_bracket_width_s": float(upper_time - lower_time),
    }


def solve_task4(
    air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
    radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
    max_time_s: float = DEFAULT_MAX_TIME_S,
    time_step_s: float = TIME_STEP_S_DEFAULT,
    output_dt_s: float = OUTPUT_DT_S,
    n_intervals: int = N_DEFAULT,
    progress: bool = False,
) -> dict[str, Any]:
    """运行问题四基线求解，返回每60 s完整xi状态和精确终止状态。"""

    if max_time_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
        raise ValueError("最大时间、内部时间步和输出间隔必须为正")
    output_ratio = output_dt_s / time_step_s
    output_stride = int(round(output_ratio))
    if not np.isclose(output_ratio, output_stride, rtol=0.0, atol=1.0e-10):
        raise ValueError("输出间隔必须是内部时间步的整数倍")
    max_steps_float = max_time_s / time_step_s
    max_steps = int(round(max_steps_float))
    if not np.isclose(max_steps_float, max_steps, rtol=0.0, atol=1.0e-8):
        raise ValueError("最大时间必须是内部时间步的整数倍")

    air_time_s, air_temperature, air_moisture = load_air_data(air_data_path)
    radius_time_s, radius_values_m = load_radius_data(radius_data_path)
    if max_time_s > radius_time_s[-1] + 1.0e-10:
        raise ValueError(
            f"请求求解至 {max_time_s:g}s，但附件2只覆盖到 {radius_time_s[-1]:g}s，"
            "禁止无说明外推"
        )
    xi, faces, measure, dxi = fixed_xi_geometry(n_intervals)
    initial_temperature = np.full(xi.size, INITIAL_TEMPERATURE_C, dtype=float)
    initial_moisture = np.full(xi.size, INITIAL_MOISTURE_KGKG, dtype=float)
    current_temperature = initial_temperature.copy()
    current_moisture = initial_moisture.copy()
    current_time = 0.0
    current_radius = radius_at(current_time, radius_time_s, radius_values_m)
    current_max, _, _, _ = _max_info(current_moisture, xi, current_radius)

    sampled_times: list[float] = [0.0]
    sampled_radius_m: list[float] = [current_radius]
    sampled_temperature: list[np.ndarray] = [current_temperature.copy()]
    sampled_moisture: list[np.ndarray] = [current_moisture.copy()]
    sampled_max: list[float] = [current_max]
    iteration_counts: list[int] = []
    picard_delta_temperature: list[float] = []
    picard_delta_moisture: list[float] = []
    min_temperature = float(np.min(current_temperature))
    max_temperature = float(np.max(current_temperature))
    min_moisture = float(np.min(current_moisture))
    max_moisture = float(np.max(current_moisture))
    progress_next_time = 0.0
    termination: dict[str, Any] | None = None

    for step in range(1, max_steps + 1):
        time_new = min(float(step * time_step_s), float(max_time_s))
        dt_current = time_new - current_time
        if dt_current <= 0.0:
            break
        radius_new = radius_at(time_new, radius_time_s, radius_values_m)
        temperature_new, moisture_new, iterations, delta_T, delta_C = _picard_step(
            current_temperature,
            current_moisture,
            xi,
            faces,
            measure,
            dxi,
            current_radius,
            radius_new,
            dt_current,
            _air_at(time_new, air_time_s, air_temperature),
            _air_at(time_new, air_time_s, air_moisture),
        )
        iteration_counts.append(int(iterations))
        picard_delta_temperature.append(float(delta_T))
        picard_delta_moisture.append(float(delta_C))
        step_max, _, _, _ = _max_info(moisture_new, xi, radius_new)
        min_temperature = min(min_temperature, float(np.min(temperature_new)))
        max_temperature = max(max_temperature, float(np.max(temperature_new)))
        min_moisture = min(min_moisture, float(np.min(moisture_new)))
        max_moisture = max(max_moisture, float(np.max(moisture_new)))

        # 保留每60 s时刻的完整 xi 场，供后续绝对r和真实表面插值。
        if step % output_stride == 0:
            sampled_times.append(float(time_new))
            sampled_radius_m.append(float(radius_new))
            sampled_temperature.append(temperature_new.copy())
            sampled_moisture.append(moisture_new.copy())
            sampled_max.append(float(step_max))

        if progress and (
            step == 1 or time_new >= progress_next_time or time_new >= max_time_s
        ):
            print(
                f"  已推进 {time_new / 3600.0:.2f} h，R={radius_new * 100:.4f} cm，"
                f"max C={step_max:.8f}，Picard={iterations}"
            )
            while progress_next_time <= time_new + 1.0e-10:
                progress_next_time += 6.0 * 3600.0

        if step_max < DRYING_THRESHOLD_KGKG:
            termination = _event_bisection(
                current_time,
                current_temperature,
                current_moisture,
                current_max,
                time_new,
                temperature_new,
                moisture_new,
                step_max,
                xi,
                faces,
                measure,
                dxi,
                radius_time_s,
                radius_values_m,
                air_time_s,
                air_temperature,
                air_moisture,
            )
            break

        current_time = time_new
        current_radius = radius_new
        current_temperature = temperature_new
        current_moisture = moisture_new
        current_max = step_max

    if termination is None:
        raise RuntimeError(
            f"在 {max_time_s / 3600.0:g} h 附件2覆盖范围内未达到全场严格阈值 "
            f"max C < {DRYING_THRESHOLD_KGKG:g}"
        )

    result: dict[str, Any] = {
        "xi": xi,
        "dxi": float(dxi),
        "time_step_s": float(time_step_s),
        "output_dt_s": float(output_dt_s),
        "n_intervals": int(n_intervals),
        "radius_data_time_s": radius_time_s.copy(),
        "radius_data_m": radius_values_m.copy(),
        "air_data_time_s": air_time_s.copy(),
        "air_temperature_C": air_temperature.copy(),
        "air_moisture_kgkg": air_moisture.copy(),
        "sampled_times_s": np.asarray(sampled_times, dtype=float),
        "sampled_radius_m": np.asarray(sampled_radius_m, dtype=float),
        "sampled_temperature_internal_C": np.asarray(sampled_temperature, dtype=float),
        "sampled_moisture_internal_kgkg": np.asarray(sampled_moisture, dtype=float),
        "sampled_max_kgkg": np.asarray(sampled_max, dtype=float),
        "iteration_counts": np.asarray(iteration_counts, dtype=int),
        "picard_delta_temperature": np.asarray(picard_delta_temperature, dtype=float),
        "picard_delta_moisture": np.asarray(picard_delta_moisture, dtype=float),
        "min_temperature_C": float(min_temperature),
        "max_temperature_C": float(max_temperature),
        "min_internal_moisture_kgkg": float(min_moisture),
        "max_internal_moisture_kgkg": float(max_moisture),
    }
    result.update(termination)
    return result


def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
    """检查输入半径、离散边界、物性单位、采样和终止阈值。"""

    xi = np.asarray(solution["xi"], dtype=float)
    radius_data_time_s = np.asarray(solution["radius_data_time_s"], dtype=float)
    radius_data_m = np.asarray(solution["radius_data_m"], dtype=float)
    sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
    sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
    sampled_temperature = np.asarray(
        solution["sampled_temperature_internal_C"], dtype=float
    )
    sampled_moisture = np.asarray(
        solution["sampled_moisture_internal_kgkg"], dtype=float
    )
    termination_temperature = np.asarray(
        solution["termination_temperature_internal_C"], dtype=float
    )
    termination_moisture = np.asarray(
        solution["termination_moisture_internal_kgkg"], dtype=float
    )
    lower_temperature = np.asarray(
        solution["termination_lower_temperature_internal_C"], dtype=float
    )
    lower_moisture = np.asarray(
        solution["termination_lower_moisture_internal_kgkg"], dtype=float
    )
    all_arrays = (
        xi,
        radius_data_time_s,
        radius_data_m,
        sampled_times,
        sampled_radius,
        sampled_temperature,
        sampled_moisture,
        termination_temperature,
        termination_moisture,
        lower_temperature,
        lower_moisture,
    )
    if not all(np.all(np.isfinite(array)) for array in all_arrays):
        raise ValueError("问题四结果包含 NaN 或 Inf")
    if xi.ndim != 1 or xi.size < 3 or not np.isclose(xi[0], 0.0) or not np.isclose(xi[-1], 1.0):
        raise ValueError("固定xi网格端点错误")
    if np.any(np.diff(xi) <= 0.0):
        raise ValueError("固定xi网格不是严格递增")
    if not np.isclose(radius_data_m[0], RADIUS_INITIAL_M, atol=1.0e-12):
        raise ValueError("附件2初始半径读取错误")
    if np.any(np.diff(radius_data_m) > 1.0e-12):
        raise ValueError("附件2半径不是单调不增")
    if not np.isclose(sampled_times[0], 0.0, atol=1.0e-12):
        raise ValueError("60 s采样未从0 s开始")
    if sampled_times.size > 1 and not np.allclose(
        np.diff(sampled_times), OUTPUT_DT_S, rtol=0.0, atol=1.0e-8
    ):
        raise ValueError("60 s采样时间间隔错误")
    if sampled_temperature.shape != (sampled_times.size, xi.size):
        raise ValueError("每60 s温度完整xi状态形状错误")
    if sampled_moisture.shape != sampled_temperature.shape:
        raise ValueError("每60 s温度/水分完整xi状态形状不一致")
    if sampled_radius.shape != sampled_times.shape:
        raise ValueError("每60 s半径状态形状错误")
    expected_radius = np.array(
        [radius_at(t, radius_data_time_s, radius_data_m) for t in sampled_times]
    )
    if not np.allclose(sampled_radius, expected_radius, rtol=0.0, atol=1.0e-12):
        raise ValueError("每60 s半径没有使用附件2分段线性 R(t)")
    if np.min(sampled_moisture) < -1.0e-10 or np.min(termination_moisture) < -1.0e-10:
        raise ValueError("水分场出现明显负值")
    if termination_temperature.shape != xi.shape or termination_moisture.shape != xi.shape:
        raise ValueError("终止状态不是完整xi网格")
    if lower_temperature.shape != xi.shape or lower_moisture.shape != xi.shape:
        raise ValueError("终止下端状态不是完整xi网格")

    # 附件2的每个已知数据点都必须被原样读取；半径单位检查同时覆盖 cm->m。
    interpolated_known = np.array(
        [radius_at(t, radius_data_time_s, radius_data_m) for t in radius_data_time_s]
    )
    known_radius_error = float(np.max(np.abs(interpolated_known - radius_data_m)))
    if known_radius_error > 1.0e-14:
        raise ValueError("附件2已知时间点半径插值不一致")

    # 用一个独立计算的 Kelvin 表达式检查物性温度单位没有误用摄氏度。
    reference_T = np.array([50.0])
    reference_C = np.array([0.10])
    _, _, _, computed_D = material_properties(reference_T, reference_C)
    expected_D = 4.2e-4 * np.exp(-0.30 / 0.10) * np.exp(-3850.0 / (50.0 + 273.15))
    if not np.isclose(computed_D[0], expected_D, rtol=1.0e-13, atol=0.0):
        raise ValueError("D 的 Kelvin 温度验证失败")

    lower_max = float(solution["termination_lower_max_kgkg"])
    upper_max = float(solution["termination_max_kgkg"])
    lower_time = float(solution["termination_lower_time_s"])
    upper_time = float(solution["termination_time_s"])
    if not lower_max >= DRYING_THRESHOLD_KGKG:
        raise ValueError("终止括号下端已低于阈值")
    if not upper_max < DRYING_THRESHOLD_KGKG:
        raise ValueError("终止状态没有严格低于阈值")
    if not (lower_time < upper_time and upper_time - lower_time <= EVENT_TOL_S + 1.0e-10):
        raise ValueError("终止时刻括号不满足二分精度")
    if not np.isclose(lower_max, np.max(lower_moisture), atol=1.0e-12, rtol=0.0):
        raise ValueError("终止下端 max C 不是全xi场最大值")
    if not np.isclose(upper_max, np.max(termination_moisture), atol=1.0e-12, rtol=0.0):
        raise ValueError("终止上端 max C 不是全xi场最大值")
    upper_index = int(np.argmax(termination_moisture))
    if upper_index != int(solution["termination_max_index"]):
        raise ValueError("终止 max C 位置记录不一致")
    expected_upper_position = xi[upper_index] * float(solution["termination_radius_m"])
    if not np.isclose(
        expected_upper_position,
        float(solution["termination_max_radius_m"]),
        atol=1.0e-14,
        rtol=0.0,
    ):
        raise ValueError("终止 max C 的物理半径位置记录不一致")

    # 中心离散语义：xi=0，advection=b*xi/dxi=0，左侧扩散通量为空。
    if not np.isclose(xi[0], 0.0, atol=1.0e-14):
        raise ValueError("中心xi不是0")
    center_boundary_ok = True

    return {
        "termination_time_s": upper_time,
        "termination_time_h": upper_time / 3600.0,
        "termination_radius_cm": float(solution["termination_radius_m"]) * 100.0,
        "termination_max_kgkg": upper_max,
        "termination_max_xi": float(solution["termination_max_xi"]),
        "termination_max_radius_cm": float(solution["termination_max_radius_m"]) * 100.0,
        "termination_lower_time_s": lower_time,
        "termination_lower_max_kgkg": lower_max,
        "termination_bracket_width_s": upper_time - lower_time,
        "radius_known_point_max_error_m": known_radius_error,
        "radius_known_point_count": int(radius_data_time_s.size),
        "temperature_min_C": float(solution["min_temperature_C"]),
        "temperature_max_C": float(solution["max_temperature_C"]),
        "moisture_min_kgkg": float(solution["min_internal_moisture_kgkg"]),
        "moisture_max_kgkg": float(solution["max_internal_moisture_kgkg"]),
        "max_picard_iterations": int(np.max(solution["iteration_counts"])),
        "mean_picard_iterations": float(np.mean(solution["iteration_counts"])),
        "sample_count": int(sampled_times.size),
        "internal_node_count": int(xi.size),
        "center_boundary_zero_flux_and_zero_advection": center_boundary_ok,
        "kelvin_reference_D_m2_s": float(computed_D[0]),
    }


def _regular_sample_indices(solution: dict[str, Any]) -> np.ndarray:
    """返回 result4/CSV 使用的 60 s 状态索引（严格从60 s开始）。"""

    times = np.asarray(solution["sampled_times_s"], dtype=float)
    termination_time = float(solution["termination_time_s"])
    last_time = np.floor(termination_time / OUTPUT_DT_S + 1.0e-12) * OUTPUT_DT_S
    indices = np.flatnonzero(
        (times >= OUTPUT_DT_S - 1.0e-8) & (times <= last_time + 1.0e-8)
    )
    selected = times[indices]
    if selected.size and not np.allclose(
        selected, np.arange(OUTPUT_DT_S, last_time + 0.1, OUTPUT_DT_S), atol=1.0e-8
    ):
        raise ValueError("求解器60 s状态与结果文件采样网格不一致")
    return indices


def _paper_regular_hours(solution: dict[str, Any]) -> list[int]:
    """返回表6中的6 h、12 h、...常规行。"""

    termination_hours = float(solution["termination_time_s"]) / 3600.0
    last_regular_hour = int(np.floor(termination_hours / 6.0 + 1.0e-12) * 6)
    return list(range(6, last_regular_hour + 1, 6))


def _sample_index_at_time(solution: dict[str, Any], time_s: float) -> int:
    times = np.asarray(solution["sampled_times_s"], dtype=float)
    matches = np.flatnonzero(np.isclose(times, time_s, rtol=0.0, atol=1.0e-8))
    if matches.size != 1:
        raise ValueError(f"缺少精确的 {time_s:g}s 完整xi状态")
    return int(matches[0])


def _fixed_state_values(
    xi: np.ndarray,
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
    radius_m: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """按绝对半径采样；返回温度、水分和有效位置掩码。"""

    fixed_temperature = np.full(OUTPUT_RADIUS_CM.size, np.nan, dtype=float)
    fixed_moisture = np.full(OUTPUT_RADIUS_CM.size, np.nan, dtype=float)
    valid = OUTPUT_RADIUS_CM / 100.0 <= radius_m + 1.0e-12
    for index, radius_cm in enumerate(OUTPUT_RADIUS_CM):
        if not valid[index]:
            continue
        xi_target = min(1.0, (radius_cm / 100.0) / radius_m)
        fixed_temperature[index] = float(np.interp(xi_target, xi, temperature_C))
        fixed_moisture[index] = float(np.interp(xi_target, xi, moisture_kgkg))
    return fixed_temperature, fixed_moisture, valid


def _surface_values(
    temperature_C: np.ndarray, moisture_kgkg: np.ndarray
) -> tuple[float, float]:
    """药材表面直接取固定xi网格的 xi=1 节点。"""

    return float(temperature_C[-1]), float(moisture_kgkg[-1])


def write_result_xlsx(
    solution: dict[str, Any],
    output_path: str | Path = DEFAULT_XLSX_PATH,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> None:
    """复制 result4 模板并写入60 s固定绝对位置和真实移动表面。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(Path(template_path))
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"result4模板工作表不符合要求: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    header_style = copy(worksheet.cell(row=1, column=2)._style)
    time_style = copy(worksheet.cell(row=2, column=1)._style)
    value_style = copy(worksheet.cell(row=2, column=2)._style)
    if worksheet.max_row > 1:
        worksheet.delete_rows(2, worksheet.max_row - 1)

    # A1 保留官方模板语义；B:V 是固定绝对位置，W 是真实移动表面。
    worksheet.cell(row=1, column=1).value = "时间\\到药材中心的距离"
    for column_index, radius_cm in enumerate(OUTPUT_RADIUS_CM, start=2):
        cell = worksheet.cell(row=1, column=column_index, value=float(radius_cm))
        cell._style = copy(header_style)
        cell.number_format = "0.0"
    surface_header = worksheet.cell(row=1, column=OUTPUT_RADIUS_CM.size + 2, value="药材表面")
    surface_header._style = copy(header_style)

    xi = np.asarray(solution["xi"], dtype=float)
    sampled_indices = _regular_sample_indices(solution)
    sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
    sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
    sampled_temperature = np.asarray(
        solution["sampled_temperature_internal_C"], dtype=float
    )
    sampled_moisture = np.asarray(
        solution["sampled_moisture_internal_kgkg"], dtype=float
    )
    for row_index, state_index in enumerate(sampled_indices, start=2):
        time_cell = worksheet.cell(row=row_index, column=1, value=int(round(sampled_times[state_index])))
        time_cell._style = copy(time_style)
        time_cell.number_format = "0"
        _, fixed_moisture, valid = _fixed_state_values(
            xi,
            sampled_temperature[state_index],
            sampled_moisture[state_index],
            float(sampled_radius[state_index]),
        )
        for column_index, (value, is_valid) in enumerate(
            zip(fixed_moisture, valid), start=2
        ):
            cell = worksheet.cell(row=row_index, column=column_index)
            cell._style = copy(value_style)
            if is_valid:
                cell.value = float(f"{value:.4f}")
                cell.number_format = "0.0000"
            else:
                cell.value = None
        surface_value = float(f"{sampled_moisture[state_index, -1]:.4f}")
        surface_cell = worksheet.cell(
            row=row_index, column=OUTPUT_RADIUS_CM.size + 2, value=surface_value
        )
        surface_cell._style = copy(value_style)
        surface_cell.number_format = "0.0000"
    workbook.save(output_path)


def _csv_state_rows(
    record_prefix: str,
    time_s: float,
    radius_m: float,
    temperature_C: np.ndarray,
    moisture_kgkg: np.ndarray,
    xi: np.ndarray,
    sample_time: bool,
) -> list[dict[str, str]]:
    """将一个完整xi状态展开为固定位置记录和单独表面记录。"""

    fixed_temperature, fixed_moisture, valid = _fixed_state_values(
        xi, temperature_C, moisture_kgkg, radius_m
    )
    if sample_time:
        time_token = str(int(round(time_s)))
        fixed_type = "sample_fixed"
        surface_type = "sample_surface"
    else:
        time_token = f"{time_s:.6f}"
        fixed_type = "drying_end_fixed"
        surface_type = "drying_end_surface"
    hour_token = f"{time_s / 3600.0:.8f}"
    radius_token = f"{radius_m * 100.0:.4f}"
    rows: list[dict[str, str]] = []
    for index, radius_cm in enumerate(OUTPUT_RADIUS_CM):
        if not valid[index]:
            continue
        rows.append(
            {
                "record_type": fixed_type,
                "time_s": time_token,
                "time_h": hour_token,
                "radius_cm": radius_token,
                "r_cm": f"{radius_cm:.4f}",
                "is_surface": "0",
                "temperature_C": f"{fixed_temperature[index]:.4f}",
                "moisture_kgkg": f"{fixed_moisture[index]:.4f}",
            }
        )
    surface_temperature, surface_moisture = _surface_values(
        temperature_C, moisture_kgkg
    )
    rows.append(
        {
            "record_type": surface_type,
            "time_s": time_token,
            "time_h": hour_token,
            "radius_cm": radius_token,
            "r_cm": radius_token,
            "is_surface": "1",
            "temperature_C": f"{surface_temperature:.4f}",
            "moisture_kgkg": f"{surface_moisture:.4f}",
        }
    )
    return rows


def write_result_csv(
    solution: dict[str, Any], output_path: str | Path = DEFAULT_CSV_PATH
) -> None:
    """写入包含固定位置、真实表面和终止状态的完整长表CSV。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xi = np.asarray(solution["xi"], dtype=float)
    sampled_indices = _regular_sample_indices(solution)
    sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
    sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
    sampled_temperature = np.asarray(
        solution["sampled_temperature_internal_C"], dtype=float
    )
    sampled_moisture = np.asarray(
        solution["sampled_moisture_internal_kgkg"], dtype=float
    )
    rows: list[dict[str, str]] = []
    for state_index in sampled_indices:
        rows.extend(
            _csv_state_rows(
                "sample",
                float(sampled_times[state_index]),
                float(sampled_radius[state_index]),
                sampled_temperature[state_index],
                sampled_moisture[state_index],
                xi,
                sample_time=True,
            )
        )
    rows.extend(
        _csv_state_rows(
            "drying_end",
            float(solution["termination_time_s"]),
            float(solution["termination_radius_m"]),
            np.asarray(solution["termination_temperature_internal_C"], dtype=float),
            np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float),
            xi,
            sample_time=False,
        )
    )
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _paper_rows(solution: dict[str, Any]) -> list[list[Any]]:
    """生成表6的常规6 h行和精确终止行。"""

    xi = np.asarray(solution["xi"], dtype=float)
    sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
    sampled_temperature = np.asarray(
        solution["sampled_temperature_internal_C"], dtype=float
    )
    sampled_moisture = np.asarray(
        solution["sampled_moisture_internal_kgkg"], dtype=float
    )
    rows: list[list[Any]] = []
    for hour in _paper_regular_hours(solution):
        state_index = _sample_index_at_time(solution, hour * 3600.0)
        _, fixed_moisture, valid = _fixed_state_values(
            xi,
            sampled_temperature[state_index],
            sampled_moisture[state_index],
            float(sampled_radius[state_index]),
        )
        _, surface_moisture = _surface_values(
            sampled_temperature[state_index], sampled_moisture[state_index]
        )
        rows.append(
            [
                float(hour),
                float(fixed_moisture[0]) if valid[0] else None,
                float(fixed_moisture[5]) if valid[5] else None,
                float(fixed_moisture[10]) if valid[10] else None,
                float(surface_moisture),
            ]
        )
    termination_moisture = np.asarray(
        solution["termination_moisture_internal_kgkg"], dtype=float
    )
    termination_temperature = np.asarray(
        solution["termination_temperature_internal_C"], dtype=float
    )
    _, fixed_moisture, valid = _fixed_state_values(
        xi,
        termination_temperature,
        termination_moisture,
        float(solution["termination_radius_m"]),
    )
    _, surface_moisture = _surface_values(termination_temperature, termination_moisture)
    termination_hours = float(solution["termination_time_s"]) / 3600.0
    rows.append(
        [
            f"烘干结束时间（{termination_hours:.4f} h）",
            float(fixed_moisture[0]) if valid[0] else None,
            float(fixed_moisture[5]) if valid[5] else None,
            float(fixed_moisture[10]) if valid[10] else None,
            float(surface_moisture),
        ]
    )
    return rows


def write_paper_table(
    solution: dict[str, Any], output_path: str | Path = DEFAULT_PAPER_PATH
) -> None:
    """生成论文表6工作表，不把绝对位置之外的数值外推到表格中。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "表6"
    headers = ["时间/h", "0 cm", "0.5 cm", "1.0 cm", "药材表面"]
    for column_index, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=1, column=column_index, value=header)
        cell.font = Font(bold=True)
    for row_index, row_values in enumerate(_paper_rows(solution), start=2):
        for column_index, value in enumerate(row_values, start=1):
            cell = worksheet.cell(row=row_index, column=column_index, value=value)
            if column_index == 1 and isinstance(value, (int, float)):
                cell.number_format = "0.0"
            elif column_index > 1 and value is not None:
                cell.value = float(f"{float(value):.4f}")
                cell.number_format = "0.0000"
    summary_row = 2 + len(_paper_rows(solution)) + 1
    worksheet.cell(row=summary_row, column=1, value="最终烘干时长/h")
    duration_cell = worksheet.cell(
        row=summary_row,
        column=2,
        value=float(f"{float(solution['termination_time_s']) / 3600.0:.4f}"),
    )
    duration_cell.number_format = "0.0000"
    workbook.save(output_path)


def _fixed_valid_count(
    radius_m: float,
) -> int:
    return int(np.count_nonzero(OUTPUT_RADIUS_CM / 100.0 <= radius_m + 1.0e-12))


def _format_pattern_ok(value: str, decimals: int) -> bool:
    return re.fullmatch(rf"\d+\.\d{{{decimals}}}", value) is not None


def validate_written_outputs(
    solution: dict[str, Any],
    xlsx_path: str | Path = DEFAULT_XLSX_PATH,
    paper_path: str | Path = DEFAULT_PAPER_PATH,
    csv_path: str | Path = DEFAULT_CSV_PATH,
) -> dict[str, Any]:
    """独立回读三个文件并检查结构、掩码、格式及全量数值一致性。"""

    summary = validate_solution(solution)
    xi = np.asarray(solution["xi"], dtype=float)
    sampled_indices = _regular_sample_indices(solution)
    sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
    sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
    sampled_temperature = np.asarray(
        solution["sampled_temperature_internal_C"], dtype=float
    )
    sampled_moisture = np.asarray(
        solution["sampled_moisture_internal_kgkg"], dtype=float
    )

    workbook = load_workbook(Path(xlsx_path), read_only=True, data_only=True)
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"result4答案工作表错误: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    xlsx_rows = list(
        worksheet.iter_rows(
            min_row=1,
            max_row=worksheet.max_row,
            min_col=1,
            max_col=worksheet.max_column,
            values_only=True,
        )
    )
    expected_xlsx_rows = sampled_indices.size + 1
    expected_xlsx_columns = OUTPUT_RADIUS_CM.size + 2
    if worksheet.max_row != expected_xlsx_rows or worksheet.max_column != expected_xlsx_columns:
        raise ValueError(
            f"result4尺寸错误: {(worksheet.max_row, worksheet.max_column)}，"
            f"期望 {(expected_xlsx_rows, expected_xlsx_columns)}"
        )
    header = xlsx_rows[0]
    expected_header = ["时间\\到药材中心的距离"] + [
        float(radius) for radius in OUTPUT_RADIUS_CM
    ] + ["药材表面"]
    header_positions_ok = (
        len(header) == len(expected_header)
        and header[0] == expected_header[0]
        and header[-1] == expected_header[-1]
        and np.allclose(
            np.asarray(header[1:-1], dtype=float), OUTPUT_RADIUS_CM, rtol=0.0, atol=1.0e-12
        )
    )
    if not header_positions_ok:
        raise ValueError(f"result4表头错误: {header!r}")
    fixed_blank_count = 0
    max_xlsx_expected_difference = 0.0
    xlsx_fixed_map: dict[tuple[int, str], float] = {}
    xlsx_surface_map: dict[int, float] = {}
    for row_offset, state_index in enumerate(sampled_indices, start=1):
        row = xlsx_rows[row_offset]
        expected_time = int(round(sampled_times[state_index]))
        if row[0] != expected_time:
            raise ValueError("result4时间行不是严格60 s整数网格")
        fixed_temperature, expected_moisture, valid = _fixed_state_values(
            xi,
            sampled_temperature[state_index],
            sampled_moisture[state_index],
            float(sampled_radius[state_index]),
        )
        del fixed_temperature
        for position_index, is_valid in enumerate(valid):
            value = row[position_index + 1]
            if not is_valid:
                fixed_blank_count += 1
                if value is not None:
                    raise ValueError("result4在移动表面之外存在外推值")
                continue
            if value is None or not np.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError("result4固定位置包含空值、非有限值或负水分")
            expected_value = float(f"{expected_moisture[position_index]:.4f}")
            max_xlsx_expected_difference = max(
                max_xlsx_expected_difference, abs(float(value) - expected_value)
            )
            xlsx_fixed_map[(expected_time, f"{OUTPUT_RADIUS_CM[position_index]:.4f}")] = float(value)
        surface_value = row[-1]
        if surface_value is None or not np.isfinite(float(surface_value)) or float(surface_value) < 0.0:
            raise ValueError("result4表面列包含无效水分")
        expected_surface = float(f"{sampled_moisture[state_index, -1]:.4f}")
        max_xlsx_expected_difference = max(
            max_xlsx_expected_difference, abs(float(surface_value) - expected_surface)
        )
        xlsx_surface_map[expected_time] = float(surface_value)
    if max_xlsx_expected_difference > 0.0:
        raise ValueError("result4回读值与求解器四位小数结果不一致")

    with Path(csv_path).open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != CSV_COLUMNS:
            raise ValueError(f"CSV字段错误: {reader.fieldnames!r}")
        csv_rows = list(reader)
    termination_radius = float(solution["termination_radius_m"])
    expected_csv_rows = int(
        sum(_fixed_valid_count(float(sampled_radius[index])) + 1 for index in sampled_indices)
        + _fixed_valid_count(termination_radius)
        + 1
    )
    if len(csv_rows) != expected_csv_rows:
        raise ValueError(f"CSV行数为 {len(csv_rows)}，期望 {expected_csv_rows}")
    record_counts = {
        record_type: sum(row["record_type"] == record_type for row in csv_rows)
        for record_type in (
            "sample_fixed",
            "sample_surface",
            "drying_end_fixed",
            "drying_end_surface",
        )
    }
    expected_record_counts = {
        "sample_fixed": int(sum(_fixed_valid_count(float(sampled_radius[index])) for index in sampled_indices)),
        "sample_surface": int(sampled_indices.size),
        "drying_end_fixed": _fixed_valid_count(termination_radius),
        "drying_end_surface": 1,
    }
    if record_counts != expected_record_counts:
        raise ValueError(f"CSV record_type结构错误: {record_counts!r}")
    csv_seen: set[tuple[str, str, str]] = set()
    max_csv_xlsx_difference = 0.0
    for row in csv_rows:
        record_type = row["record_type"]
        if record_type not in expected_record_counts:
            raise ValueError(f"CSV包含未知record_type: {record_type}")
        if not _format_pattern_ok(row["time_h"], 8):
            raise ValueError("CSV time_h 不是八位小数")
        if not np.isclose(
            float(row["time_h"]), float(row["time_s"]) / 3600.0, rtol=0.0, atol=5.0e-9
        ):
            raise ValueError("CSV time_h 与 time_s 不一致")
        if not _format_pattern_ok(row["radius_cm"], 4) or not _format_pattern_ok(row["r_cm"], 4):
            raise ValueError("CSV半径字段不是四位小数")
        if not _format_pattern_ok(row["temperature_C"], 4) or not _format_pattern_ok(row["moisture_kgkg"], 4):
            raise ValueError("CSV温度/水分不是四位小数字符串")
        if row["is_surface"] not in {"0", "1"}:
            raise ValueError("CSV is_surface 不是0/1")
        if record_type.startswith("sample_"):
            if re.fullmatch(r"\d+", row["time_s"]) is None:
                raise ValueError("CSV sample time_s 不是整数秒")
            sample_time = int(row["time_s"])
            if sample_time not in xlsx_surface_map and record_type == "sample_surface":
                raise ValueError("CSV sample表面时刻无法对应result4")
            sample_matches = np.flatnonzero(
                np.isclose(sampled_times, sample_time, rtol=0.0, atol=1.0e-8)
            )
            if sample_matches.size != 1:
                raise ValueError("CSV sample时刻无法对应求解器状态")
            expected_sample_radius_cm = float(sampled_radius[sample_matches[0]]) * 100.0
            if not np.isclose(
                float(row["radius_cm"]), expected_sample_radius_cm, rtol=0.0, atol=5.0e-5
            ):
                raise ValueError("CSV sample radius_cm 与 R(t) 不一致")
            if record_type == "sample_fixed":
                key = (sample_time, row["r_cm"])
                if key not in xlsx_fixed_map:
                    raise ValueError("CSV fixed记录无法对应result4固定位置")
                if row["is_surface"] != "0":
                    raise ValueError("CSV fixed记录的is_surface必须为0")
                expected_moisture = xlsx_fixed_map[key]
            else:
                if not np.isclose(
                    float(row["r_cm"]), expected_sample_radius_cm, rtol=0.0, atol=5.0e-5
                ):
                    raise ValueError("CSV sample表面 r_cm 与 R(t) 不一致")
                expected_moisture = xlsx_surface_map[sample_time]
        else:
            if re.fullmatch(r"\d+\.\d{6}", row["time_s"]) is None:
                raise ValueError("CSV终止 time_s 不是六位小数")
            termination_time = float(row["time_s"])
            if not np.isclose(termination_time, float(solution["termination_time_s"]), atol=5.0e-7, rtol=0.0):
                raise ValueError("CSV终止时刻与求解器不一致")
            if not np.isclose(
                float(row["radius_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
            ):
                raise ValueError("CSV终止 radius_cm 与真实表面半径不一致")
            termination_temperature = np.asarray(solution["termination_temperature_internal_C"], dtype=float)
            termination_moisture_array = np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float)
            fixed_temperature, fixed_moisture, valid = _fixed_state_values(
                xi, termination_temperature, termination_moisture_array, termination_radius
            )
            del fixed_temperature
            if record_type == "drying_end_fixed":
                radius_index = int(round(float(row["r_cm"]) * 10.0))
                if (
                    radius_index < 0
                    or radius_index >= OUTPUT_RADIUS_CM.size
                    or not valid[radius_index]
                    or not np.isclose(
                        float(row["r_cm"]),
                        float(OUTPUT_RADIUS_CM[radius_index]),
                        rtol=0.0,
                        atol=5.0e-5,
                    )
                ):
                    raise ValueError("CSV终止固定位置无效")
                if row["is_surface"] != "0":
                    raise ValueError("CSV终止fixed记录的is_surface必须为0")
                expected_moisture = float(f"{fixed_moisture[radius_index]:.4f}")
            else:
                if not np.isclose(
                    float(row["radius_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
                ) or not np.isclose(
                    float(row["r_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
                ):
                    raise ValueError("CSV终止表面半径字段错误")
                expected_moisture = float(f"{termination_moisture_array[-1]:.4f}")
        key = (record_type, row["time_s"], row["r_cm"])
        if key in csv_seen:
            raise ValueError("CSV存在重复记录")
        csv_seen.add(key)
        if (record_type.endswith("surface")) != (row["is_surface"] == "1"):
            raise ValueError("CSV surface标记与record_type不一致")
        actual_moisture = float(row["moisture_kgkg"])
        if not np.isfinite(actual_moisture) or actual_moisture < 0.0:
            raise ValueError("CSV水分包含非有限值或负值")
        max_csv_xlsx_difference = max(
            max_csv_xlsx_difference, abs(actual_moisture - expected_moisture)
        )
    if max_csv_xlsx_difference > 0.0:
        raise ValueError("CSV与result4对应水分值不一致")

    paper_workbook = load_workbook(Path(paper_path), read_only=True, data_only=True)
    if paper_workbook.sheetnames != ["表6"]:
        raise ValueError(f"论文表工作表错误: {paper_workbook.sheetnames}")
    paper_sheet = paper_workbook["表6"]
    paper_rows = list(
        paper_sheet.iter_rows(
            min_row=1,
            max_row=paper_sheet.max_row,
            min_col=1,
            max_col=paper_sheet.max_column,
            values_only=True,
        )
    )
    paper_hours = _paper_regular_hours(solution)
    # 表头 + 常规行 + 终止行 + 一个空行 + 最终时长摘要行。
    expected_paper_rows = len(paper_hours) + 4
    if paper_sheet.max_row != expected_paper_rows or paper_sheet.max_column != 5:
        raise ValueError(
            f"论文表尺寸错误: {(paper_sheet.max_row, paper_sheet.max_column)}，"
            f"期望 {(expected_paper_rows, 5)}"
        )
    if list(paper_rows[0]) != ["时间/h", "0 cm", "0.5 cm", "1.0 cm", "药材表面"]:
        raise ValueError("论文表表头错误")
    max_paper_difference = 0.0
    for row_index, hour in enumerate(paper_hours, start=1):
        row = paper_rows[row_index]
        if not np.isclose(float(row[0]), hour, atol=1.0e-12, rtol=0.0):
            raise ValueError("论文表常规时间行错误")
        expected_index = _sample_index_at_time(solution, hour * 3600.0)
        _, fixed_moisture, valid = _fixed_state_values(
            xi,
            sampled_temperature[expected_index],
            sampled_moisture[expected_index],
            float(sampled_radius[expected_index]),
        )
        expected_values = [fixed_moisture[0], fixed_moisture[5], fixed_moisture[10], sampled_moisture[expected_index, -1]]
        for column_index, expected_value in enumerate(expected_values, start=1):
            if expected_value is None or (column_index <= 3 and not valid[[0, 5, 10][column_index - 1]]):
                continue
            actual_value = row[column_index]
            if actual_value is None or not np.isfinite(float(actual_value)):
                raise ValueError("论文表常规水分为空或非有限")
            max_paper_difference = max(
                max_paper_difference,
                abs(float(actual_value) - float(f"{expected_value:.4f}")),
            )
    termination_row_index = 1 + len(paper_hours) + 0
    termination_row = paper_rows[termination_row_index]
    expected_termination_text = f"烘干结束时间（{float(solution['termination_time_s']) / 3600.0:.4f} h）"
    if termination_row[0] != expected_termination_text:
        raise ValueError("论文表终止时间文本错误")
    termination_temperature = np.asarray(solution["termination_temperature_internal_C"], dtype=float)
    termination_moisture_array = np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float)
    _, fixed_moisture, valid = _fixed_state_values(
        xi, termination_temperature, termination_moisture_array, termination_radius
    )
    expected_values = [fixed_moisture[0], fixed_moisture[5], fixed_moisture[10], termination_moisture_array[-1]]
    for column_index, expected_value in enumerate(expected_values, start=1):
        if column_index <= 3 and not valid[[0, 5, 10][column_index - 1]]:
            continue
        actual_value = termination_row[column_index]
        if actual_value is None or not np.isfinite(float(actual_value)):
            raise ValueError("论文表终止水分为空或非有限")
        max_paper_difference = max(
            max_paper_difference,
            abs(float(actual_value) - float(f"{expected_value:.4f}")),
        )
    summary_row = paper_rows[-1]
    if summary_row[0] != "最终烘干时长/h" or not np.isclose(
        float(summary_row[1]), float(solution["termination_time_s"]) / 3600.0, atol=5.0e-5
    ):
        raise ValueError("论文表最终烘干时长摘要错误")
    if max_paper_difference > 0.0:
        raise ValueError("论文表水分值与求解器结果不一致")

    return {
        **summary,
        "xlsx_rows": int(worksheet.max_row),
        "xlsx_columns": int(worksheet.max_column),
        "csv_rows": int(len(csv_rows)),
        "paper_rows": int(paper_sheet.max_row),
        "paper_columns": int(paper_sheet.max_column),
        "sample_start_s": int(round(sampled_times[sampled_indices[0]])) if sampled_indices.size else None,
        "sample_end_s": int(round(sampled_times[sampled_indices[-1]])) if sampled_indices.size else None,
        "sample_count": int(sampled_indices.size),
        "fixed_blank_count": int(fixed_blank_count),
        "max_abs_xlsx_expected_difference": float(max_xlsx_expected_difference),
        "max_abs_csv_xlsx_difference": float(max_csv_xlsx_difference),
        "max_abs_paper_difference": float(max_paper_difference),
        "csv_record_counts": record_counts,
    }


def run_coarse_comparison(
    air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
    radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
    max_time_s: float = DEFAULT_MAX_TIME_S,
    progress: bool = False,
) -> dict[str, Any]:
    """运行 N=160、dt=1 s 的粗网格对照解。"""

    solution = solve_task4(
        air_data_path=air_data_path,
        radius_data_path=radius_data_path,
        max_time_s=max_time_s,
        time_step_s=1.0,
        output_dt_s=OUTPUT_DT_S,
        n_intervals=160,
        progress=progress,
    )
    return validate_solution(solution)


def main() -> None:
    parser = argparse.ArgumentParser(description="求解A题问题四移动边界模型")
    parser.add_argument("--air-data-path", type=Path, default=DEFAULT_AIR_DATA_PATH)
    parser.add_argument("--radius-data-path", type=Path, default=DEFAULT_RADIUS_DATA_PATH)
    parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
    parser.add_argument("--time-step", type=float, default=TIME_STEP_S_DEFAULT)
    parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
    parser.add_argument("--n", type=int, default=N_DEFAULT)
    parser.add_argument("--no-write", action="store_true", help="本阶段不生成答案文件")
    parser.add_argument(
        "--skip-sensitivity",
        action="store_true",
        help="跳过 N=160、dt=1 s 的粗网格对照计算",
    )
    parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
    args = parser.parse_args()

    started = wall_time.perf_counter()
    print(
        "问题四最终加密解开始: "
        f"N={args.n}, dxi={1.0 / args.n:g}, dt={args.time_step:g}s, "
        f"output_dt={args.output_dt:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
    )
    solution = solve_task4(
        air_data_path=args.air_data_path,
        radius_data_path=args.radius_data_path,
        max_time_s=args.max_time,
        time_step_s=args.time_step,
        output_dt_s=args.output_dt,
        n_intervals=args.n,
        progress=args.progress,
    )
    summary = validate_solution(solution)
    print(f"最终加密解数值检查: {summary}")
    print(
        "终止证据: "
        f"lower t={summary['termination_lower_time_s']:.6f}s "
        f"max C={summary['termination_lower_max_kgkg']:.8f}; "
        f"upper t={summary['termination_time_s']:.6f}s "
        f"max C={summary['termination_max_kgkg']:.8f}; "
        f"R={summary['termination_radius_cm']:.6f}cm, "
        f"max位置 r={summary['termination_max_radius_cm']:.6f}cm "
        f"(xi={summary['termination_max_xi']:.6f})"
    )
    if not args.skip_sensitivity:
        coarse_started = wall_time.perf_counter()
        coarse_summary = run_coarse_comparison(
            air_data_path=args.air_data_path,
            radius_data_path=args.radius_data_path,
            max_time_s=args.max_time,
            progress=args.progress,
        )
        print(f"N=160, dt=1s 粗网格对照: {coarse_summary}")
        print(
            f"结束时间差（加密-粗解）: "
            f"{summary['termination_time_h'] - coarse_summary['termination_time_h']:.8f} h"
        )
        print(
            f"粗网格对照耗时: {wall_time.perf_counter() - coarse_started:.2f}s"
        )
    if args.no_write:
        print("--no-write: 本阶段未生成任何 answer 文件")
    else:
        write_result_xlsx(solution)
        write_result_csv(solution)
        write_paper_table(solution)
        output_summary = validate_written_outputs(solution)
        print(f"答案文件回读验收: {output_summary}")
        print(f"已生成: {DEFAULT_XLSX_PATH}")
        print(f"已生成: {DEFAULT_PAPER_PATH}")
        print(f"已生成: {DEFAULT_CSV_PATH}")
    print(f"总耗时: {wall_time.perf_counter() - started:.2f}s")


if __name__ == "__main__":
    main()
