"""A题问题三：继承问题二模型的长期烘干求解器。

问题三从 t=0 连续推进问题二的固定半径、动态物性热质耦合模型，
在每个 dt=1 s 的内部时间步检查完整径向水分场，首次满足
max_r C(r,t) < 0.15 kg/kg 时停止。输出文件只保留题目要求的
60 s 时间网格；精确终止时刻和终止状态用于表5及验证报告。
"""

from __future__ import annotations

import argparse
import csv
import sys
import time as wall_time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl import load_workbook


# 直接复用问题二的数值核心和模型常量，不改变问题二算法。
TASK2_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "task2" / "script"
if str(TASK2_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TASK2_SCRIPT_DIR))
import solve_task2 as task2  # noqa: E402


RADIUS_M = task2.RADIUS_M
BASE_DR_M = task2.BASE_DR_M
INITIAL_TEMPERATURE_C = task2.INITIAL_TEMPERATURE_C
INITIAL_MOISTURE_KGKG = task2.INITIAL_MOISTURE_KGKG
HEAT_TRANSFER_W_M2_K = task2.HEAT_TRANSFER_W_M2_K
MASS_TRANSFER_M_S = task2.MASS_TRANSFER_M_S
PICARD_MAX_ITER = task2.PICARD_MAX_ITER
OUTPUT_RADIUS_CM = task2.OUTPUT_RADIUS_CM.copy()

TIME_STEP_S = 1.0
OUTPUT_DT_S = 60.0
TABLE5_DT_S = 6.0 * 3600.0
DRYING_THRESHOLD_KGKG = 0.15
# 题目说明过程一般持续2--3天；上限仅用于防止异常情况下无限循环。
DEFAULT_MAX_TIME_S = 7.0 * 24.0 * 3600.0

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "problem" / "附件" / "附件3" / "result3.xlsx"
DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result3.xlsx"
DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[1] / "answer" / "task3_all_results.csv"
)
DEFAULT_TASK2_CSV_PATH = (
    REPO_ROOT / "solution" / "task2" / "answer" / "task2_all_results.csv"
)

KEY_RADIUS_INDICES = np.array([0, 5, 10, 15, 20], dtype=int)


def _output_indices(radii_m: np.ndarray) -> np.ndarray:
    """取得题目要求的0--2 cm、每0.1 cm输出位置。"""

    target_m = OUTPUT_RADIUS_CM / 100.0
    indices = np.array([int(np.argmin(np.abs(radii_m - r))) for r in target_m])
    if not np.allclose(radii_m[indices], target_m, atol=1.0e-12, rtol=0.0):
        raise ValueError("当前内部网格不能精确包含题目要求的0.1 cm输出位置")
    return indices


def solve_task3(
    data_path: str | Path = DEFAULT_DATA_PATH,
    max_time_s: float = DEFAULT_MAX_TIME_S,
    time_step_s: float = TIME_STEP_S,
    output_dt_s: float = OUTPUT_DT_S,
    dr_m: float = BASE_DR_M,
    progress: bool = False,
) -> dict[str, Any]:
    """从 t=0 连续推进问题二状态，直到完整场严格低于阈值。"""

    if max_time_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
        raise ValueError("时间上限、时间步和输出间隔必须为正")
    max_steps_float = max_time_s / time_step_s
    max_steps = int(np.floor(max_steps_float + 1.0e-10))
    if max_steps < 1 or not np.isclose(max_steps_float, max_steps, atol=1.0e-10):
        raise ValueError("时间上限必须由整数个内部时间步组成")
    output_ratio = output_dt_s / time_step_s
    output_stride = int(round(output_ratio))
    if not np.isclose(output_ratio, output_stride, atol=1.0e-10):
        raise ValueError("输出间隔必须是内部时间步的整数倍")

    # 附件1只覆盖初期，np.interp 在末点以后按题目要求保持最后边界值。
    air_time_s, air_temperature, air_moisture = task2.load_air_data(
        data_path, required_end_s=0.0
    )
    air_temperature_interp = lambda t: float(np.interp(t, air_time_s, air_temperature))
    air_moisture_interp = lambda t: float(np.interp(t, air_time_s, air_moisture))

    radii_m, faces_m, radial_measure_m2 = task2.control_volume_geometry(RADIUS_M, dr_m)
    output_indices = _output_indices(radii_m)
    n_nodes = radii_m.size

    current_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
    current_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)

    sampled_times: list[float] = [0.0]
    sampled_moisture: list[np.ndarray] = [current_moisture[output_indices].copy()]
    first_3h_moisture = np.full((10801, output_indices.size), np.nan, dtype=float)
    first_3h_moisture[0] = current_moisture[output_indices]
    table5_times: list[float] = []
    table5_values: list[np.ndarray] = []

    iteration_counts: list[int] = []
    picard_delta_temperature: list[float] = []
    picard_delta_moisture: list[float] = []
    max_positive_step_change = -np.inf
    max_abs_step_change = 0.0
    min_internal_moisture = float(np.min(current_moisture))
    max_internal_moisture = float(np.max(current_moisture))
    previous_max_moisture = float(np.max(current_moisture))
    termination_time_s: float | None = None
    termination_state: np.ndarray | None = None
    termination_previous_state: np.ndarray | None = None
    termination_previous_max = np.nan
    termination_max = np.nan

    for step in range(1, max_steps + 1):
        time_new_s = step * time_step_s
        previous_moisture = current_moisture
        (
            current_temperature,
            current_moisture,
            iterations,
            delta_temperature,
            delta_moisture,
        ) = task2._picard_step(
            current_temperature,
            previous_moisture,
            time_new_s,
            time_step_s,
            radial_measure_m2,
            faces_m,
            dr_m,
            air_temperature_interp(time_new_s),
            air_moisture_interp(time_new_s),
        )
        iteration_counts.append(int(iterations))
        picard_delta_temperature.append(float(delta_temperature))
        picard_delta_moisture.append(float(delta_moisture))

        change = current_moisture - previous_moisture
        max_positive_step_change = max(max_positive_step_change, float(np.max(change)))
        max_abs_step_change = max(max_abs_step_change, float(np.max(np.abs(change))))
        min_internal_moisture = min(min_internal_moisture, float(np.min(current_moisture)))
        max_internal_moisture = max(max_internal_moisture, float(np.max(current_moisture)))

        if time_new_s <= 10800.0 + 1.0e-10:
            first_3h_moisture[step] = current_moisture[output_indices]

        # 先写入题目60 s网格上的状态，再依据完整内部场判定终止。
        if step % output_stride == 0:
            sampled_times.append(float(time_new_s))
            sampled_moisture.append(current_moisture[output_indices].copy())

        current_max = float(np.max(current_moisture))
        if current_max < DRYING_THRESHOLD_KGKG:
            # 严格小于阈值；前一整步状态和当前整场状态都保留供验收。
            termination_time_s = float(time_new_s)
            termination_state = current_moisture.copy()
            termination_previous_state = previous_moisture.copy()
            termination_previous_max = previous_max_moisture
            termination_max = current_max
            break

        if time_new_s % TABLE5_DT_S == 0.0:
            table5_times.append(float(time_new_s))
            table5_values.append(current_moisture[output_indices[KEY_RADIUS_INDICES]].copy())

        previous_max_moisture = current_max
        if progress and (step == 1 or step % int(TABLE5_DT_S / time_step_s) == 0):
            print(
                f"  已推进 {time_new_s / 3600.0:.1f} h，"
                f"max C={current_max:.8f}，Picard={iterations}"
            )

    if termination_time_s is None or termination_state is None:
        raise RuntimeError(
            f"在{max_time_s / 3600.0:g} h内未达到全场严格阈值 "
            f"max C < {DRYING_THRESHOLD_KGKG:g}"
        )

    return {
        "time_s": np.asarray(sampled_times, dtype=float),
        "radius_cm": OUTPUT_RADIUS_CM.copy(),
        "moisture_kgkg": np.asarray(sampled_moisture, dtype=float),
        "radii_m_internal": radii_m,
        "termination_time_s": termination_time_s,
        "termination_state_internal": termination_state,
        "termination_previous_state_internal": termination_previous_state,
        "termination_previous_max_kgkg": float(termination_previous_max),
        "termination_max_kgkg": float(termination_max),
        "first_3h_moisture_kgkg": first_3h_moisture,
        "iteration_counts": np.asarray(iteration_counts, dtype=int),
        "picard_delta_temperature": np.asarray(picard_delta_temperature, dtype=float),
        "picard_delta_moisture": np.asarray(picard_delta_moisture, dtype=float),
        "max_positive_step_change_kgkg": float(max_positive_step_change),
        "max_abs_step_change_kgkg": float(max_abs_step_change),
        "min_internal_moisture_kgkg": float(min_internal_moisture),
        "max_internal_moisture_kgkg": float(max_internal_moisture),
        "table5_times_s": np.asarray(table5_times, dtype=float),
        "table5_values_kgkg": np.asarray(table5_values, dtype=float)
        if table5_values
        else np.empty((0, KEY_RADIUS_INDICES.size), dtype=float),
    }


def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
    """执行问题三所需的最低限度数值、终止和结构检查。"""

    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    termination_state = np.asarray(solution["termination_state_internal"], dtype=float)
    previous_state = np.asarray(solution["termination_previous_state_internal"], dtype=float)
    if moisture.shape != (time_s.size, radius_cm.size):
        raise ValueError("问题三输出数组形状错误")
    if termination_state.shape != previous_state.shape:
        raise ValueError("终止前后内部场形状不一致")
    all_arrays = (time_s, radius_cm, moisture, termination_state, previous_state)
    if not all(np.all(np.isfinite(array)) for array in all_arrays):
        raise ValueError("问题三结果包含 NaN 或 Inf")
    if float(np.min(moisture)) < -1.0e-10 or float(np.min(termination_state)) < -1.0e-10:
        raise ValueError("问题三结果包含明显负水分浓度")
    if time_s.size < 1 or not np.isclose(time_s[0], 0.0, atol=1.0e-12):
        raise ValueError("输出时间未从0 s开始")
    if time_s.size > 1 and not np.allclose(np.diff(time_s), OUTPUT_DT_S, atol=1.0e-10):
        raise ValueError("输出时间间隔不是60 s")
    if radius_cm.size != 21 or not np.allclose(
        radius_cm, np.arange(0.0, 2.0000001, 0.1), atol=1.0e-12
    ):
        raise ValueError("输出半径不是0--2 cm、每0.1 cm")

    previous_max = float(solution["termination_previous_max_kgkg"])
    termination_max = float(solution["termination_max_kgkg"])
    if previous_max < DRYING_THRESHOLD_KGKG:
        raise ValueError("终止前一秒已低于阈值，终止记录不符合首次判定")
    if not termination_max < DRYING_THRESHOLD_KGKG:
        raise ValueError("终止时完整内部场未严格低于阈值")
    if not np.isclose(previous_max, float(np.max(previous_state)), atol=1.0e-12):
        raise ValueError("终止前最大水分浓度不是完整内部场最大值")
    if not np.isclose(termination_max, float(np.max(termination_state)), atol=1.0e-12):
        raise ValueError("终止时最大水分浓度不是完整内部场最大值")

    sampled_delta = np.diff(moisture, axis=0)
    max_positive_sampled_change = (
        float(np.max(sampled_delta)) if sampled_delta.size else 0.0
    )
    radial_delta = np.diff(moisture, axis=1)
    max_radial_increase = float(np.max(radial_delta)) if radial_delta.size else 0.0
    iterations = np.asarray(solution["iteration_counts"], dtype=int)
    if iterations.size == 0 or np.max(iterations) > PICARD_MAX_ITER:
        raise ValueError("Picard迭代记录为空或超出上限")

    return {
        "termination_time_s": float(solution["termination_time_s"]),
        "termination_time_h": float(solution["termination_time_s"]) / 3600.0,
        "termination_previous_max_kgkg": previous_max,
        "termination_max_kgkg": termination_max,
        "max_positive_step_change_kgkg": float(
            solution["max_positive_step_change_kgkg"]
        ),
        "max_positive_sampled_change_kgkg": max_positive_sampled_change,
        "max_abs_step_change_kgkg": float(solution["max_abs_step_change_kgkg"]),
        "max_radial_increase_kgkg": max_radial_increase,
        "min_internal_moisture_kgkg": float(solution["min_internal_moisture_kgkg"]),
        "max_internal_moisture_kgkg": float(solution["max_internal_moisture_kgkg"]),
        "max_picard_iterations": int(np.max(iterations)),
        "mean_picard_iterations": float(np.mean(iterations)),
        "sample_count": int(time_s.size),
        "internal_node_count": int(termination_state.size),
    }


def compare_with_task2(
    solution: dict[str, Any], task2_csv_path: str | Path = DEFAULT_TASK2_CSV_PATH
) -> dict[str, float | int]:
    """比较问题三在0--3 h的1 s输出与问题二最终CSV。"""

    first_3h = np.asarray(solution["first_3h_moisture_kgkg"], dtype=float)
    if not np.all(np.isfinite(first_3h)):
        raise ValueError("问题三未完整记录0--3 h场，无法与问题二比较")
    frame = pd.read_csv(Path(task2_csv_path))
    required_columns = {"time_s", "radius_cm", "moisture_kgkg"}
    if not required_columns.issubset(frame.columns):
        raise ValueError("问题二CSV缺少比较所需列")
    expected_rows = 10801 * 21
    if len(frame) != expected_rows:
        raise ValueError(f"问题二CSV记录数为{len(frame)}，不是{expected_rows}")
    task2_moisture = frame["moisture_kgkg"].to_numpy(dtype=float).reshape((10801, 21))
    raw_difference = np.abs(first_3h - task2_moisture)
    rounded_difference = np.abs(np.round(first_3h, 4) - np.round(task2_moisture, 4))
    return {
        "rows_compared": expected_rows,
        "max_abs_difference_raw_kgkg": float(np.max(raw_difference)),
        "max_abs_difference_4dp_kgkg": float(np.max(rounded_difference)),
    }


def write_result_xlsx(
    solution: dict[str, Any],
    output_path: str | Path = DEFAULT_XLSX_PATH,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> None:
    """复制问题三模板结构并写入60 s采样水分场。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(Path(template_path))
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"问题三模板工作表不符合要求: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    if time_s.size != moisture.shape[0] or radius_cm.size != moisture.shape[1]:
        raise ValueError("xlsx写入数组形状错误")

    header_style = copy(worksheet.cell(row=1, column=2)._style)
    time_style = copy(worksheet.cell(row=2, column=1)._style)
    value_style = copy(worksheet.cell(row=2, column=2)._style)
    if worksheet.max_row > 1:
        worksheet.delete_rows(2, worksheet.max_row - 1)
    for column_index, radius in enumerate(radius_cm, start=2):
        cell = worksheet.cell(row=1, column=column_index, value=round(float(radius), 1))
        cell._style = copy(header_style)
        cell.number_format = "0.0"
    for row_index, time_value in enumerate(time_s, start=2):
        time_cell = worksheet.cell(row=row_index, column=1, value=int(round(time_value)))
        time_cell._style = copy(time_style)
        time_cell.number_format = "0"
        for column_index, value in enumerate(moisture[row_index - 2], start=2):
            cell = worksheet.cell(
                row=row_index,
                column=column_index,
                value=float(f"{float(value):.4f}"),
            )
            cell._style = copy(value_style)
            cell.number_format = "0.0000"
    workbook.save(output_path)


def write_result_csv(
    solution: dict[str, Any], output_path: str | Path = DEFAULT_CSV_PATH
) -> None:
    """写入问题三要求的long-format三列CSV。"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    time_s = np.asarray(solution["time_s"], dtype=float)
    radius_cm = np.asarray(solution["radius_cm"], dtype=float)
    moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "radius_cm", "moisture_kgkg"])
        for time_index, time_value in enumerate(time_s):
            for radius_index, radius_value in enumerate(radius_cm):
                writer.writerow(
                    [
                        int(round(time_value)),
                        f"{radius_value:.1f}",
                        f"{moisture[time_index, radius_index]:.4f}",
                    ]
                )


def validate_written_outputs(
    solution: dict[str, Any],
    xlsx_path: str | Path = DEFAULT_XLSX_PATH,
    csv_path: str | Path = DEFAULT_CSV_PATH,
) -> dict[str, Any]:
    """读取答案文件并检查结构及CSV/XLSX四位小数一致性。"""

    expected = np.round(np.asarray(solution["moisture_kgkg"], dtype=float), 4)
    expected_times = np.asarray(solution["time_s"], dtype=int)
    expected_radius = np.asarray(solution["radius_cm"], dtype=float)

    frame = pd.read_csv(Path(csv_path))
    if list(frame.columns) != ["time_s", "radius_cm", "moisture_kgkg"]:
        raise ValueError(f"问题三CSV字段不符合要求: {list(frame.columns)}")
    expected_rows = expected_times.size * expected_radius.size
    if len(frame) != expected_rows:
        raise ValueError(f"问题三CSV行数为{len(frame)}，不是{expected_rows}")
    csv_times = frame["time_s"].to_numpy(dtype=int)
    csv_radius = frame["radius_cm"].to_numpy(dtype=float)
    csv_values = frame["moisture_kgkg"].to_numpy(dtype=float).reshape(expected.shape)
    if not np.array_equal(csv_times, np.repeat(expected_times, expected_radius.size)):
        raise ValueError("问题三CSV时间结构错误")
    if not np.allclose(csv_radius, np.tile(expected_radius, expected_times.size), atol=1.0e-12):
        raise ValueError("问题三CSV半径结构错误")

    workbook = load_workbook(Path(xlsx_path), read_only=True, data_only=True)
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError(f"问题三答案工作表错误: {workbook.sheetnames}")
    worksheet = workbook["Sheet1"]
    if worksheet.max_row != expected_times.size + 1 or worksheet.max_column != expected_radius.size + 1:
        raise ValueError("问题三答案xlsx尺寸错误")
    # ReadOnlyWorksheet.cell() restarts the XML parser for every cell.  Consume
    # the worksheet once by rows so validation remains fast for the long file.
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
    xlsx_radius = np.asarray(rows[0][1:], dtype=float)
    xlsx_values = np.asarray([row[1:] for row in rows[1:]], dtype=float)
    if not np.array_equal(xlsx_times, expected_times) or not np.allclose(
        xlsx_radius, expected_radius, atol=1.0e-12
    ):
        raise ValueError("问题三答案xlsx时间或半径结构错误")
    xlsx_values = np.round(xlsx_values, 4)
    if not np.array_equal(csv_values, xlsx_values):
        raise ValueError("问题三CSV与xlsx对应水分值不一致")
    if not np.array_equal(csv_values, expected):
        raise ValueError("问题三答案文件与求解器采样值不一致")
    return {
        "rows": int(expected_rows),
        "xlsx_shape": (int(worksheet.max_row), int(worksheet.max_column)),
        "max_abs_csv_xlsx_difference_kgkg": float(np.max(np.abs(csv_values - xlsx_values))),
    }


def _print_table5(solution: dict[str, Any]) -> None:
    """打印每6 h采样和精确终止状态对应的表5。"""

    regular_times = np.asarray(solution["table5_times_s"], dtype=float)
    regular_values = np.asarray(solution["table5_values_kgkg"], dtype=float)
    termination_time = float(solution["termination_time_s"])
    termination_state = np.asarray(solution["termination_state_internal"], dtype=float)
    termination_values = termination_state[
        task2._output_indices(np.asarray(solution["radii_m_internal"], dtype=float))[KEY_RADIUS_INDICES]
    ]
    print("表5 水分浓度 / kg/kg（列为0、0.5、1.0、1.5、2.0 cm）")
    print("时间/h,0 cm,0.5 cm,1.0 cm,1.5 cm,2.0 cm")
    for time_value, row in zip(regular_times, regular_values):
        print(
            f"{time_value / 3600.0:.1f},"
            + ",".join(f"{float(value):.4f}" for value in row)
        )
    print(
        f"烘干结束时间 ({termination_time / 3600.0:.6f} h),"
        + ",".join(f"{float(value):.4f}" for value in termination_values)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="求解A题问题三")
    parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
    parser.add_argument("--time-step", type=float, default=TIME_STEP_S)
    parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--task2-csv", type=Path, default=DEFAULT_TASK2_CSV_PATH)
    parser.add_argument("--no-write", action="store_true", help="只求解和验证，不写答案文件")
    args = parser.parse_args()

    started = wall_time.perf_counter()
    print(
        f"问题三求解开始: dt={args.time_step:g}s, output_dt={args.output_dt:g}s, "
        f"dr={BASE_DR_M:g}m, threshold C<{DRYING_THRESHOLD_KGKG:g}"
    )
    solution = solve_task3(
        data_path=args.data_path,
        max_time_s=args.max_time,
        time_step_s=args.time_step,
        output_dt_s=args.output_dt,
        progress=True,
    )
    summary = validate_solution(solution)
    comparison = compare_with_task2(solution, args.task2_csv)
    print(f"基本数值检查: {summary}")
    print(f"0--3 h与问题二CSV全量比较: {comparison}")
    if not args.no_write:
        write_result_xlsx(solution)
        write_result_csv(solution)
        output_check = validate_written_outputs(solution)
        print(f"答案文件检查: {output_check}")
        print(f"已生成: {DEFAULT_XLSX_PATH}")
        print(f"已生成: {DEFAULT_CSV_PATH}")
    _print_table5(solution)
    print(f"烘干结束时间 = {summary['termination_time_h']:.6f} h")
    print(f"总耗时: {wall_time.perf_counter() - started:.2f} s")


if __name__ == "__main__":
    main()
