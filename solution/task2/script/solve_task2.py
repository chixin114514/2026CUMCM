"""A题问题二：动态物性圆柱径向热质耦合求解。

模型沿用问题一的圆柱径向守恒有限体积离散，时间方向使用后向欧拉。
问题二的 rho、cp、k、D 在每个时间步的 Picard 迭代中由当前 T、C 更新，
从而得到当前时间步内的自洽隐式解。内部网格含 r=0 和 r=R 两个节点，
两端为半控制体积；输出网格为每 1 s、每 0.1 cm。
"""

from __future__ import annotations

import argparse
import csv
import time as wall_time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy.linalg import solve_banded


# 几何、初始状态和输出约定（内部长度统一使用 m）。
RADIUS_M = 0.02
LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录。
BASE_DR_M = 0.000125
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE_KGKG = 2.55
AIR_PREHEAT_END_S = 1800.0
FINAL_TIME_S = 10800.0
OUTPUT_DT_S = 1.0
OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)

# 问题一沿用的边界传递参数。
HEAT_TRANSFER_W_M2_K = 25.0
MASS_TRANSFER_M_S = 8.0e-7

# Picard 收敛参数。绝对阈值足以保证四位小数输出稳定，同时避免无意义地
# 将迭代压到机器精度。
PICARD_TOL_T_C = 1.0e-8
PICARD_TOL_C_KGKG = 1.0e-10
PICARD_MAX_ITER = 50

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
)
DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "problem"
    / "附件"
    / "附件3"
    / "result2.xlsx"
)
DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result2.xlsx"
DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[1] / "answer" / "task2_all_results.csv"
)


def load_air_data(
    path: str | Path = DEFAULT_DATA_PATH,
    preheat_end_s: float = AIR_PREHEAT_END_S,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取附件1的预热段，并对 1800 s 后使用末端值保持。

    附件中可能还包含 1800 s 以后的记录；问题二按题目给出的最小假设，
    只把 0--1800 s 作为预热边界，后续时间由 np.interp 的端点保持处理。
    """

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
    selected = selected[selected["时间"] <= preheat_end_s + 1.0e-10]

    time_s = selected["时间"].to_numpy(dtype=float)
    air_temperature_C = selected["温度"].to_numpy(dtype=float)
    air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
    if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
        raise ValueError("附件1预热段时间必须包含至少两个严格递增时间点")
    if time_s[0] > 1.0e-10 or time_s[-1] < preheat_end_s - 1.0e-10:
        raise ValueError("附件1预热段未覆盖 0--1800 s")
    if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
        raise ValueError("附件1预热段包含非有限数值")
    return time_s, air_temperature_C, air_moisture_kgkg


def control_volume_geometry(
    radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """返回含两端半控制体积的节点、面和径向测度。"""

    if radius_m <= 0.0 or dr_m <= 0.0:
        raise ValueError("半径和空间步长必须为正")
    n_intervals = int(round(radius_m / dr_m))
    if not np.isclose(n_intervals * dr_m, radius_m, rtol=0.0, atol=1.0e-12):
        raise ValueError("当前网格要求半径可由整数个 dr 划分")
    radii_m = np.linspace(0.0, radius_m, n_intervals + 1)
    faces_m = 0.5 * (radii_m[:-1] + radii_m[1:])
    radial_measure_m2 = np.empty_like(radii_m)
    radial_measure_m2[0] = 0.5 * faces_m[0] ** 2
    radial_measure_m2[1:-1] = 0.5 * (faces_m[1:] ** 2 - faces_m[:-1] ** 2)
    radial_measure_m2[-1] = 0.5 * (radius_m**2 - faces_m[-1] ** 2)
    return radii_m, faces_m, radial_measure_m2


def material_properties(
    temperature_C: np.ndarray, moisture_kgkg: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """按当前 Picard 状态计算 rho、cp、k 和 D（SI 单位）。"""

    temperature_C = np.asarray(temperature_C, dtype=float)
    moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
    concentration = np.maximum(moisture_kgkg, 1.0e-12)
    temperature_K = temperature_C + 273.15
    if np.any(temperature_K <= 0.0):
        raise ValueError("动态物性计算遇到非正 Kelvin 温度")

    rho = 650.0 + 128.0 * concentration
    cp = 1450.0 + 2736.0 * concentration / (concentration + 1.0)
    k = 0.21 + 0.38 * concentration / (concentration + 1.0)
    diffusivity = 2.4e-3 * np.exp(-0.45 / concentration) * np.exp(
        -3850.0 / temperature_K
    )
    return rho, cp, k, diffusivity


def _solve_tridiagonal(
    lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray, rhs: np.ndarray
) -> np.ndarray:
    """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""

    n = diagonal.size
    banded = np.zeros((3, n), dtype=float)
    banded[0, 1:] = upper
    banded[1, :] = diagonal
    banded[2, :-1] = lower
    return solve_banded((1, 1), banded, rhs, check_finite=False)


def _solve_temperature_linear(
    old_temperature_C: np.ndarray,
    guess_temperature_C: np.ndarray,
    guess_moisture_kgkg: np.ndarray,
    radial_measure_m2: np.ndarray,
    faces_m: np.ndarray,
    dr_m: float,
    dt_s: float,
    air_temperature_C: float,
) -> np.ndarray:
    """在给定 Picard 物性下求解一个后向欧拉温度步。"""

    rho, cp, conductivity, _ = material_properties(
        guess_temperature_C, guess_moisture_kgkg
    )
    storage = rho * cp * radial_measure_m2
    face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
    conductance = face_k * faces_m / dr_m

    diagonal = storage.copy()
    diagonal[0] += dt_s * conductance[0]
    diagonal[1:-1] += dt_s * (conductance[:-1] + conductance[1:])
    diagonal[-1] += dt_s * (
        conductance[-1] + RADIUS_M * HEAT_TRANSFER_W_M2_K
    )
    lower = -dt_s * conductance.copy()
    upper = -dt_s * conductance.copy()
    rhs = storage * old_temperature_C
    rhs[-1] += dt_s * RADIUS_M * HEAT_TRANSFER_W_M2_K * air_temperature_C
    return _solve_tridiagonal(lower, diagonal, upper, rhs)


def _solve_moisture_linear(
    old_moisture_kgkg: np.ndarray,
    guess_temperature_C: np.ndarray,
    guess_moisture_kgkg: np.ndarray,
    radial_measure_m2: np.ndarray,
    faces_m: np.ndarray,
    dr_m: float,
    dt_s: float,
    air_moisture_kgkg: float,
) -> np.ndarray:
    """在给定 Picard 物性下求解一个后向欧拉水分步。"""

    _, _, _, diffusivity = material_properties(
        guess_temperature_C, guess_moisture_kgkg
    )
    storage = radial_measure_m2
    face_D = 0.5 * (diffusivity[:-1] + diffusivity[1:])
    conductance = face_D * faces_m / dr_m

    diagonal = storage.copy()
    diagonal[0] += dt_s * conductance[0]
    diagonal[1:-1] += dt_s * (conductance[:-1] + conductance[1:])
    diagonal[-1] += dt_s * (conductance[-1] + RADIUS_M * MASS_TRANSFER_M_S)
    lower = -dt_s * conductance.copy()
    upper = -dt_s * conductance.copy()
    rhs = storage * old_moisture_kgkg
    rhs[-1] += dt_s * RADIUS_M * MASS_TRANSFER_M_S * air_moisture_kgkg
    return _solve_tridiagonal(lower, diagonal, upper, rhs)


def _picard_step(
    old_temperature_C: np.ndarray,
    old_moisture_kgkg: np.ndarray,
    time_new_s: float,
    dt_s: float,
    radial_measure_m2: np.ndarray,
    faces_m: np.ndarray,
    dr_m: float,
    air_temperature_C: float,
    air_moisture_kgkg: float,
    tol_temperature_C: float = PICARD_TOL_T_C,
    tol_moisture_kgkg: float = PICARD_TOL_C_KGKG,
    max_iter: int = PICARD_MAX_ITER,
) -> tuple[np.ndarray, np.ndarray, int, float, float]:
    """使用当前时间步内的 Picard 外迭代求 T、C 自洽解。"""

    # time_new_s 同时用于异常信息，明确边界取值属于当前时间步。
    guess_temperature_C = old_temperature_C.copy()
    guess_moisture_kgkg = old_moisture_kgkg.copy()
    last_delta_temperature = np.inf
    last_delta_moisture = np.inf

    for iteration in range(1, max_iter + 1):
        new_temperature_C = _solve_temperature_linear(
            old_temperature_C,
            guess_temperature_C,
            guess_moisture_kgkg,
            radial_measure_m2,
            faces_m,
            dr_m,
            dt_s,
            air_temperature_C,
        )
        new_moisture_kgkg = _solve_moisture_linear(
            old_moisture_kgkg,
            guess_temperature_C,
            guess_moisture_kgkg,
            radial_measure_m2,
            faces_m,
            dr_m,
            dt_s,
            air_moisture_kgkg,
        )
        last_delta_temperature = float(
            np.max(np.abs(new_temperature_C - guess_temperature_C))
        )
        last_delta_moisture = float(
            np.max(np.abs(new_moisture_kgkg - guess_moisture_kgkg))
        )
        if (
            last_delta_temperature <= tol_temperature_C
            and last_delta_moisture <= tol_moisture_kgkg
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
        "问题二 Picard 迭代未收敛: "
        f"t={time_new_s:g}s, iter={max_iter}, "
        f"max|dT|={last_delta_temperature:.3e}, "
        f"max|dC|={last_delta_moisture:.3e}"
    )


def _output_indices(radii_m: np.ndarray) -> np.ndarray:
    """取得 0--2 cm 每 0.1 cm 输出位置对应的内部节点。"""

    target_m = OUTPUT_RADIUS_CM / 100.0
    indices = np.array([int(np.argmin(np.abs(radii_m - r))) for r in target_m])
    if not np.allclose(radii_m[indices], target_m, atol=1.0e-12, rtol=0.0):
        raise ValueError("当前内部网格不能精确包含题目要求的 0.1 cm 输出位置")
    return indices


def solve_task2(
    data_path: str | Path = DEFAULT_DATA_PATH,
    t_end_s: float = FINAL_TIME_S,
    time_step_s: float = 1.0,
    output_dt_s: float = OUTPUT_DT_S,
    dr_m: float = BASE_DR_M,
    progress: bool = False,
) -> dict[str, Any]:
    """求解问题二并返回输出网格上的完整数值场。"""

    if t_end_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
        raise ValueError("终止时间、时间步和输出间隔必须为正")
    n_steps_float = t_end_s / time_step_s
    n_outputs_float = t_end_s / output_dt_s
    n_steps = int(round(n_steps_float))
    n_outputs = int(round(n_outputs_float))
    if not np.isclose(n_steps_float, n_steps, atol=1.0e-10):
        raise ValueError("终止时间必须由整数个求解时间步组成")
    if not np.isclose(n_outputs_float, n_outputs, atol=1.0e-10):
        raise ValueError("终止时间必须由整数个输出间隔组成")
    ratio = output_dt_s / time_step_s
    output_stride = int(round(ratio))
    if not np.isclose(ratio, output_stride, atol=1.0e-10):
        raise ValueError("为避免额外插值，output_dt_s 必须是 time_step_s 的整数倍")

    air_time_s, air_temperature, air_moisture = load_air_data(data_path)
    radii_m, faces_m, radial_measure_m2 = control_volume_geometry(RADIUS_M, dr_m)
    output_indices = _output_indices(radii_m)
    n_nodes = radii_m.size
    n_outputs_total = n_outputs + 1
    output_times = output_dt_s * np.arange(n_outputs_total, dtype=float)
    temperature_output = np.empty((n_outputs_total, output_indices.size), dtype=float)
    moisture_output = np.empty_like(temperature_output)
    initial_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
    initial_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)
    current_temperature = initial_temperature.copy()
    current_moisture = initial_moisture.copy()
    temperature_output[0] = current_temperature[output_indices]
    moisture_output[0] = current_moisture[output_indices]
    iteration_counts = np.empty(n_steps, dtype=int)
    picard_delta_temperature = np.empty(n_steps, dtype=float)
    picard_delta_moisture = np.empty(n_steps, dtype=float)
    air_temperature_interp = lambda t: float(np.interp(t, air_time_s, air_temperature))
    air_moisture_interp = lambda t: float(np.interp(t, air_time_s, air_moisture))

    for step in range(1, n_steps + 1):
        time_new_s = step * time_step_s
        (
            current_temperature,
            current_moisture,
            iteration_counts[step - 1],
            picard_delta_temperature[step - 1],
            picard_delta_moisture[step - 1],
        ) = _picard_step(
            current_temperature,
            current_moisture,
            time_new_s,
            time_step_s,
            radial_measure_m2,
            faces_m,
            dr_m,
            air_temperature_interp(time_new_s),
            air_moisture_interp(time_new_s),
        )
        if step % output_stride == 0:
            output_index = step // output_stride
            temperature_output[output_index] = current_temperature[output_indices]
            moisture_output[output_index] = current_moisture[output_indices]
        if progress and (step == 1 or step == n_steps or step % max(1, n_steps // 10) == 0):
            print(f"  已完成 {time_new_s:.1f}/{t_end_s:.1f} s")

    return {
        "time_s": output_times,
        "radius_cm": OUTPUT_RADIUS_CM.copy(),
        "temperature_C": temperature_output,
        "moisture_kgkg": moisture_output,
        "radius_m_internal": radii_m,
        "time_step_s": float(time_step_s),
        "dr_m": float(dr_m),
        "iteration_counts": iteration_counts,
        "picard_delta_temperature": picard_delta_temperature,
        "picard_delta_moisture": picard_delta_moisture,
        "air_temperature_last_C": air_temperature_interp(t_end_s),
        "air_moisture_last_kgkg": air_moisture_interp(t_end_s),
    }


def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
    """执行最低限度的数值和物理 sanity check，并返回摘要。"""

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    if temperature.shape != (time_s.size, radius_cm.size):
        raise ValueError("温度输出数组形状错误")
    if moisture.shape != temperature.shape:
        raise ValueError("温度和水分输出数组形状不一致")
    if not np.all(np.isfinite(np.column_stack((temperature.ravel(), moisture.ravel())))):
        raise ValueError("结果包含 NaN 或 Inf")
    if np.min(moisture) < -1.0e-10:
        raise ValueError(f"结果包含负水分浓度: min={np.min(moisture):.6g}")
    if not np.isclose(temperature[0, 0], INITIAL_TEMPERATURE_C, atol=1.0e-12):
        raise ValueError("初始中心温度不符合题设")
    if not np.isclose(moisture[0, 0], INITIAL_MOISTURE_KGKG, atol=1.0e-12):
        raise ValueError("初始中心水分不符合题设")
    if not np.all(np.diff(time_s) > 0.0):
        raise ValueError("输出时间没有严格递增")
    if not np.isclose(radius_cm[0], 0.0) or not np.isclose(radius_cm[-1], 2.0):
        raise ValueError("输出半径范围不符合 0--2 cm")

    final_temperature = temperature[-1]
    final_moisture = moisture[-1]
    if final_temperature[-1] <= final_temperature[0]:
        raise ValueError("末时刻表面温度未高于中心，检查热边界符号")
    if final_moisture[-1] >= final_moisture[0]:
        raise ValueError("末时刻表面水分未低于中心，检查传质边界符号")
    if np.max(temperature) > max(temperature[-1, -1], 60.0) + 20.0:
        raise ValueError("温度出现明显数值爆炸")
    if np.max(np.abs(np.diff(temperature, axis=0))) > 5.0:
        raise ValueError("相邻输出时刻温度出现明显跳变")
    if np.max(np.abs(np.diff(moisture, axis=0))) > 0.2:
        raise ValueError("相邻输出时刻水分出现明显跳变")

    iterations = np.asarray(solution["iteration_counts"], dtype=int)
    if iterations.size and np.max(iterations) > PICARD_MAX_ITER:
        raise ValueError("Picard 迭代次数超出上限")
    return {
        "time_end_s": float(time_s[-1]),
        "temperature_min_C": float(np.min(temperature)),
        "temperature_max_C": float(np.max(temperature)),
        "moisture_min_kgkg": float(np.min(moisture)),
        "moisture_max_kgkg": float(np.max(moisture)),
        "max_picard_iterations": int(np.max(iterations)) if iterations.size else 0,
        "mean_picard_iterations": float(np.mean(iterations)) if iterations.size else 0.0,
        "center_surface_temperature_gap_C": float(final_temperature[-1] - final_temperature[0]),
        "center_surface_moisture_gap_kgkg": float(final_moisture[0] - final_moisture[-1]),
        "center_flux_zero_discretisation": True,
    }


def write_result_xlsx(
    solution: dict[str, Any],
    output_path: str | Path = DEFAULT_XLSX_PATH,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> None:
    """以 result2.xlsx 为模板，写入两张完整结果表。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(Path(template_path))
    required_sheets = ("温度", "水分浓度")
    if tuple(workbook.sheetnames) != required_sheets:
        raise ValueError(f"result2.xlsx 模板工作表不符合要求: {workbook.sheetnames}")

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    if time_s.size != 10801 or radius_cm.size != 21:
        raise ValueError("最终 xlsx 必须为 10801 个时间点和 21 个半径点")

    for sheet_name, values in (("温度", temperature), ("水分浓度", moisture)):
        worksheet = workbook[sheet_name]
        # 模板的两张表字体略有不同；在删除示例数据行前分别保存三类
        # 参考样式，确保扩展出的完整结果仍与对应模板一致。
        header_style = copy(worksheet.cell(row=1, column=2)._style)
        time_style = copy(worksheet.cell(row=2, column=1)._style)
        value_style = copy(worksheet.cell(row=2, column=2)._style)
        if worksheet.max_row > 1:
            worksheet.delete_rows(2, worksheet.max_row - 1)
        # 保留模板左上角的文字；距离表头按题目要求改为完整的 0--2 cm。
        for column_index, radius in enumerate(radius_cm, start=2):
            cell = worksheet.cell(
                row=1, column=column_index, value=round(float(radius), 1)
            )
            cell._style = copy(header_style)
            cell.number_format = "0.0"
        for row_index, time_value in enumerate(time_s, start=2):
            time_cell = worksheet.cell(row=row_index, column=1, value=int(round(time_value)))
            time_cell._style = copy(time_style)
            time_cell.number_format = "0"
            for column_index, value in enumerate(values[row_index - 2], start=2):
                cell = worksheet.cell(
                    row=row_index, column=column_index, value=float(np.round(value, 4))
                )
                cell._style = copy(value_style)
                cell.number_format = "0.0000"
    workbook.save(output_path)


def write_result_csv(
    solution: dict[str, Any], output_path: str | Path = DEFAULT_CSV_PATH
) -> None:
    """写入问题二全部时间/半径结果的 long-format CSV。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    temperature = np.asarray(solution["temperature_C"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["time_s", "time_h", "radius_cm", "temperature_C", "moisture_kgkg"]
        )
        for time_index, time_value in enumerate(time_s):
            for radius_index, radius_value in enumerate(radius_cm):
                writer.writerow(
                    [
                        int(round(time_value)),
                        f"{time_value / 3600.0:.6f}",
                        f"{radius_value:.1f}",
                        f"{temperature[time_index, radius_index]:.4f}",
                        f"{moisture[time_index, radius_index]:.4f}",
                    ]
                )


def key_tables(solution: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """提取表3、表4的 6 个时间和 5 个半径结果。"""

    target_times = np.array([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
    time_s = np.asarray(solution["time_s"], dtype=float)
    indices = np.array([int(np.argmin(np.abs(time_s - t))) for t in target_times])
    if not np.allclose(time_s[indices], target_times, atol=1.0e-10):
        raise ValueError("完整结果中缺少表3/表4要求的时间点")
    temperature = np.round(np.asarray(solution["temperature_C"])[indices], 4)
    moisture = np.round(np.asarray(solution["moisture_kgkg"])[indices], 4)
    return target_times, temperature, moisture


def time_step_sensitivity(
    base_solution: dict[str, Any],
    data_path: str | Path = DEFAULT_DATA_PATH,
) -> dict[str, Any]:
    """比较 dt=1 s 与 dt=0.5 s 在表3/表4点的差异。"""

    fine_solution = solve_task2(
        data_path=data_path,
        t_end_s=FINAL_TIME_S,
        time_step_s=0.5,
        output_dt_s=1.0,
        dr_m=BASE_DR_M,
        progress=True,
    )
    key_times_s = np.array([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
    key_radius_indices = np.array([0, 5, 10, 15, 20], dtype=int)
    base_time_indices = np.array(
        [int(np.argmin(np.abs(np.asarray(base_solution["time_s"]) - t))) for t in key_times_s]
    )
    fine_time_indices = np.array(
        [int(np.argmin(np.abs(np.asarray(fine_solution["time_s"]) - t))) for t in key_times_s]
    )
    base_temperature = np.asarray(base_solution["temperature_C"])[
        base_time_indices[:, None], key_radius_indices[None, :]
    ]
    fine_temperature = np.asarray(fine_solution["temperature_C"])[
        fine_time_indices[:, None], key_radius_indices[None, :]
    ]
    base_moisture = np.asarray(base_solution["moisture_kgkg"])[
        base_time_indices[:, None], key_radius_indices[None, :]
    ]
    fine_moisture = np.asarray(fine_solution["moisture_kgkg"])[
        fine_time_indices[:, None], key_radius_indices[None, :]
    ]
    temperature_difference = np.abs(fine_temperature - base_temperature)
    moisture_difference = np.abs(fine_moisture - base_moisture)
    temperature_position = np.unravel_index(
        int(np.argmax(temperature_difference)), temperature_difference.shape
    )
    moisture_position = np.unravel_index(
        int(np.argmax(moisture_difference)), moisture_difference.shape
    )
    return {
        "fine_solution": fine_solution,
        "key_times_s": key_times_s,
        "temperature_max_abs_difference_C": float(np.max(temperature_difference)),
        "temperature_difference_position": (
            float(key_times_s[temperature_position[0]]),
            float(OUTPUT_RADIUS_CM[key_radius_indices[temperature_position[1]]]),
        ),
        "moisture_max_abs_difference_kgkg": float(np.max(moisture_difference)),
        "moisture_difference_position": (
            float(key_times_s[moisture_position[0]]),
            float(OUTPUT_RADIUS_CM[key_radius_indices[moisture_position[1]]]),
        ),
    }


def _print_key_tables(solution: dict[str, Any]) -> None:
    target_times, temperature, moisture = key_tables(solution)
    print("表3 温度 / °C（行依次为 0.5--3.0 h，列为 0--2 cm）")
    print("时间/h," + ",".join(f"{r:.1f} cm" for r in OUTPUT_RADIUS_CM[[0, 5, 10, 15, 20]]))
    for time_value, row in zip(target_times, temperature):
        print(f"{time_value / 3600.0:.1f}," + ",".join(f"{x:.4f}" for x in row[[0, 5, 10, 15, 20]]))
    print("表4 水分浓度 / kg/kg（行依次为 0.5--3.0 h，列为 0--2 cm）")
    print("时间/h," + ",".join(f"{r:.1f} cm" for r in OUTPUT_RADIUS_CM[[0, 5, 10, 15, 20]]))
    for time_value, row in zip(target_times, moisture):
        print(f"{time_value / 3600.0:.1f}," + ",".join(f"{x:.4f}" for x in row[[0, 5, 10, 15, 20]]))


def main() -> None:
    parser = argparse.ArgumentParser(description="求解 A题问题二")
    parser.add_argument("--t-end", type=float, default=FINAL_TIME_S)
    parser.add_argument("--time-step", type=float, default=1.0)
    parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
    parser.add_argument("--no-write", action="store_true", help="只求解和检查，不写答案文件")
    parser.add_argument("--skip-sensitivity", action="store_true")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()

    started = wall_time.perf_counter()
    print(
        f"问题二求解开始: t_end={args.t_end:g}s, dt={args.time_step:g}s, "
        f"dr={BASE_DR_M:g}m"
    )
    solution = solve_task2(
        data_path=args.data_path,
        t_end_s=args.t_end,
        time_step_s=args.time_step,
        output_dt_s=args.output_dt,
        progress=True,
    )
    summary = validate_solution(solution)
    print(f"基本数值检查: {summary}")
    if not args.no_write:
        write_result_xlsx(solution)
        write_result_csv(solution)
        print(f"已生成: {DEFAULT_XLSX_PATH}")
        print(f"已生成: {DEFAULT_CSV_PATH}")
    if (
        not args.skip_sensitivity
        and np.isclose(args.t_end, FINAL_TIME_S)
        and np.isclose(args.time_step, 1.0)
    ):
        sensitivity = time_step_sensitivity(solution, data_path=args.data_path)
        print(
            "时间步敏感性（dt=1 s 对比 dt=0.5 s，表3/表4点）: "
            f"max|dT|={sensitivity['temperature_max_abs_difference_C']:.6e} °C "
            f"at (t,r)={sensitivity['temperature_difference_position']}; "
            f"max|dC|={sensitivity['moisture_max_abs_difference_kgkg']:.6e} kg/kg "
            f"at (t,r)={sensitivity['moisture_difference_position']}"
        )
        _print_key_tables(solution)
    print(f"总耗时: {wall_time.perf_counter() - started:.2f} s")


if __name__ == "__main__":
    main()
