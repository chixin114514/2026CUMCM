"""绘制敏感度分析的三幅主图。

本脚本只读取 ``../results`` 下由 ``sensitivity_summary.csv`` 列出的敏感度
工况及其逐点结果，不修改原始数据。三类主图分别展示关键点归一化误差增益、
烘干时间相对变化和表格水分相对偏差。绘图前会重新审计所有逐点文件，并核对
汇总表中的最大偏差；结果目录中遗留的旧版/重复文件不会被误读。
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

# Matplotlib 字体缓存放在临时目录，避免污染项目目录。
_MPL_CONFIG = Path("/private/tmp/nature_figure_mplconfig")
_MPL_CONFIG.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(_MPL_CONFIG)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize
from matplotlib.ticker import NullFormatter
import numpy as np


plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["SimHei", "Arial Unicode MS", "DejaVu Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.size": 8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
        "axes.unicode_minus": False,
        "savefig.facecolor": "white",
    }
)

_FONT_PATHS = (
    Path("/Users/jiaqiaosu/.fonts/SimHei.ttf"),
    Path("/Users/jiaqiaosu/Library/Fonts/SimHei.ttf"),
)
for _font_path in _FONT_PATHS:
    if _font_path.exists():
        font_manager.fontManager.addfont(str(_font_path))
        _font_name = font_manager.FontProperties(fname=str(_font_path)).get_name()
        plt.rcParams["font.sans-serif"] = [_font_name, "Arial Unicode MS", "DejaVu Sans"]
        break


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results"
OUTPUT_DIR = Path(__file__).resolve().parent

TASK_LABELS = {1: "一", 2: "二", 3: "三", 4: "四"}

PARAM_LABELS = {
    (1, "dr_m"): "空间步长",
    (1, "dt_s"): "时间步长",
    (1, "picard_tol_C"): "Picard 容差",
    (1, "linear_residual_tol"): "线性残差容差",
    (2, "time_step_s"): "时间步长",
    (2, "dr_m"): "空间步长",
    (2, "picard_tol_T"): "温度迭代容差",
    (2, "picard_tol_C"): "水分迭代容差",
    (3, "n_intervals"): "径向网格数",
    (3, "time_step_long_s"): "长时步长",
    (3, "TIME_STEP_EARLY_S"): "前段步长",
    (3, "STABLE_START_S"): "稳定段起点",
    (3, "picard_tol"): "联合迭代容差",
    (4, "n_intervals"): "径向网格数",
    (4, "time_step_long_s"): "长时步长",
    (4, "time_step_early_s"): "前段步长",
    (4, "STABLE_START_S"): "稳定段起点",
    (4, "event_tol_s"): "事件定位容差",
    (4, "picard_tol"): "联合迭代容差",
}

PARAM_ORDER = {
    1: ["dr_m", "dt_s", "picard_tol_C", "linear_residual_tol"],
    2: ["time_step_s", "dr_m", "picard_tol_T", "picard_tol_C"],
    3: [
        "n_intervals",
        "STABLE_START_S",
        "time_step_long_s",
        "TIME_STEP_EARLY_S",
        "picard_tol",
    ],
    4: [
        "n_intervals",
        "STABLE_START_S",
        "time_step_long_s",
        "time_step_early_s",
        "event_tol_s",
        "picard_tol",
    ],
}

BASELINE_VALUES: dict[tuple[int, str], float | None] = {
    (1, "dr_m"): 0.00005,
    (1, "dt_s"): 0.25,
    (1, "picard_tol_C"): 1e-10,
    (1, "linear_residual_tol"): 1e-10,
    (2, "time_step_s"): 1.0,
    (2, "dr_m"): 0.0000125,
    (2, "picard_tol_T"): 1e-8,
    (2, "picard_tol_C"): 1e-10,
    (3, "n_intervals"): 1600.0,
    (3, "time_step_long_s"): 10.0,
    (3, "TIME_STEP_EARLY_S"): 1.0,
    (3, "STABLE_START_S"): 9000.0,
    (3, "picard_tol"): None,
    (4, "n_intervals"): 800.0,
    (4, "time_step_long_s"): 5.0,
    (4, "time_step_early_s"): 1.0,
    (4, "STABLE_START_S"): 9000.0,
    (4, "event_tol_s"): 0.1,
    (4, "picard_tol"): None,
}

BASELINE_FILES = {
    1: "task1-dr_m-0.00005.csv",
    2: "task2-dr_m-0.0000125.csv",
    3: "task3-n_intervals-1600.csv",
    4: "task4-n_intervals-800.csv",
}

EXPECTED_SHAPE = {1: (7, 5), 2: (6, 5), 3: (9, 5), 4: (8, 4)}

SUMMARY_HEADER = {
    "task",
    "parameter",
    "value",
    "status",
    "run_file",
    "termination_time_h",
    "base_termination_time_h",
    "diff_termination_h",
    "max_abs_dT_C",
    "max_abs_dC_kgkg",
    "max_abs_table_dC_kgkg",
    "max_picard_iterations",
    "mean_picard_iterations",
    "runtime_s",
}


def _finite_float(value: str | float, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} 不是数值：{value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} 不是有限数：{value!r}")
    return number


def _decimal(value: float, digits: int = 6) -> str:
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def _power_label(value: float) -> str:
    if value == 0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    coefficient = value / (10.0**exponent)
    if math.isclose(abs(coefficient), 1.0, rel_tol=1e-8, abs_tol=0.0):
        return f"10^{exponent}"
    return f"{_decimal(abs(coefficient), 2)}×10^{exponent}"


def _factor_label(ratio: float) -> str:
    return f"{_decimal(ratio, 4)}倍"


def _percent_label(value: float) -> str:
    if abs(value) < 1e-12:
        return "0%"
    sign = "+" if value > 0 else "-"
    magnitude = abs(value)
    number = f"{magnitude:.3g}" if magnitude >= 0.01 else _power_label(magnitude)
    return f"{sign}{number}%"


def _magnitude_percent_label(value: float) -> str:
    if abs(value) < 1e-12:
        return "0%"
    magnitude = abs(value)
    number = f"{magnitude:.3g}" if magnitude >= 0.01 else _power_label(magnitude)
    return f"{number}%"


def _parameter_value_label(task: int, parameter: str, value: str) -> str:
    if parameter == "picard_tol":
        return {"loosen100x": "放宽100倍", "tighten100x": "收紧100倍"}.get(value, value)
    number = _finite_float(value, f"问题{TASK_LABELS[task]} {parameter}取值")
    if parameter == "dr_m":
        return f"{_decimal(number * 1000.0)}毫米"
    if parameter in {
        "time_step_s",
        "dt_s",
        "time_step_long_s",
        "TIME_STEP_EARLY_S",
        "time_step_early_s",
        "STABLE_START_S",
        "event_tol_s",
    }:
        return f"{_decimal(number)}秒"
    if parameter in {
        "picard_tol_T",
        "picard_tol_C",
        "linear_residual_tol",
    }:
        return _power_label(number)
    if parameter == "n_intervals":
        return _decimal(number)
    return _decimal(number)


def _is_baseline(task: int, parameter: str, value: str) -> bool:
    baseline = BASELINE_VALUES.get((task, parameter))
    if baseline is None:
        return False
    try:
        return math.isclose(float(value), baseline, rel_tol=1e-9, abs_tol=1e-14)
    except (TypeError, ValueError):
        return False


def _radius_key(value: str) -> float:
    if value == "surface":
        return 2.0
    return _finite_float(value, "半径")


def _detail_columns(task: int) -> set[str]:
    if task in (1, 2):
        return {
            "task",
            "parameter",
            "value",
            "time_s",
            "radius_cm",
            "temperature_C",
            "moisture_kgkg",
            "base_temperature_C",
            "base_moisture_kgkg",
            "abs_dT_C",
            "abs_dC_kgkg",
        }
    return {
        "task",
        "parameter",
        "value",
        "time_h",
        "radius_cm",
        "moisture_kgkg",
        "base_moisture_kgkg",
        "abs_dC_kgkg",
    }


def audit_results() -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    """完整审计汇总表和逐点文件，并返回原始行。"""

    summary_path = RESULT_DIR / "sensitivity_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"缺少汇总表：{summary_path}")
    with summary_path.open(newline="", encoding="utf-8-sig") as stream:
        summary_rows = list(csv.DictReader(stream))
    if len(summary_rows) != 56:
        raise ValueError(f"汇总工况数为 {len(summary_rows)}，期望 56")
    if set(summary_rows[0]) != SUMMARY_HEADER:
        raise ValueError("汇总表列集合不符合预期")
    if any(row["status"] != "ok" for row in summary_rows):
        bad = [row["run_file"] for row in summary_rows if row["status"] != "ok"]
        raise ValueError(f"存在非成功工况：{bad}")
    if len({row["run_file"] for row in summary_rows}) != len(summary_rows):
        raise ValueError("汇总表存在重复结果文件名")

    detail_paths = [RESULT_DIR / row["run_file"] for row in summary_rows]
    if any(not path.is_file() for path in detail_paths):
        missing = [path.name for path in detail_paths if not path.is_file()]
        raise ValueError(f"汇总表列出的逐点结果文件缺失：{missing}")
    if len(detail_paths) != 56 or len({path.name for path in detail_paths}) != 56:
        raise ValueError(
            f"汇总表列出的逐点结果文件数为 {len(detail_paths)}，期望 56 且不得重复"
        )
    if list(RESULT_DIR.glob("*.err")):
        raise ValueError("结果目录存在错误记录文件")

    details: dict[str, list[dict[str, str]]] = {}
    detail_max: dict[str, dict[str, float]] = {}
    for path in detail_paths:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError(f"逐点文件为空：{path.name}")
        task = int(rows[0]["task"])
        if task not in EXPECTED_SHAPE:
            raise ValueError(f"未知任务编号：{path.name}")
        if set(rows[0]) != _detail_columns(task):
            raise ValueError(f"{path.name} 列集合不符合预期")
        expected_time, expected_radius = EXPECTED_SHAPE[task]
        time_column = "time_s" if task in (1, 2) else "time_h"
        numeric_columns = (
            (
                "time_s",
                "temperature_C",
                "moisture_kgkg",
                "base_temperature_C",
                "base_moisture_kgkg",
                "abs_dT_C",
                "abs_dC_kgkg",
            )
            if task in (1, 2)
            else ("time_h", "moisture_kgkg", "base_moisture_kgkg", "abs_dC_kgkg")
        )
        times: list[float] = []
        radii: list[float] = []
        pairs: list[tuple[float, float]] = []
        for row in rows:
            if (
                int(row["task"]) != task
                or row["parameter"] != rows[0]["parameter"]
                or row["value"] != rows[0]["value"]
            ):
                raise ValueError(f"{path.name} 元数据在行间不一致")
            if any(row[column].strip() == "" for column in row):
                raise ValueError(f"{path.name} 存在缺失字段")
            time_value = _finite_float(row[time_column], f"{path.name} 时间")
            radius_value = _radius_key(row["radius_cm"])
            times.append(time_value)
            radii.append(radius_value)
            pairs.append((time_value, radius_value))
            for column in numeric_columns:
                _finite_float(row[column], f"{path.name} {column}")
            if task in (1, 2):
                comparisons = (
                    ("temperature_C", "base_temperature_C", "abs_dT_C"),
                    ("moisture_kgkg", "base_moisture_kgkg", "abs_dC_kgkg"),
                )
            else:
                comparisons = (("moisture_kgkg", "base_moisture_kgkg", "abs_dC_kgkg"),)
            for value_column, base_column, difference_column in comparisons:
                value = float(row[value_column])
                base = float(row[base_column])
                difference = float(row[difference_column])
                tolerance = max(1e-12, 1e-8 * max(1.0, abs(value), abs(base)))
                if difference < -1e-15 or abs(difference - abs(value - base)) > tolerance:
                    raise ValueError(f"{path.name} {difference_column} 与原始差值不一致")
        if len(rows) != expected_time * expected_radius:
            raise ValueError(f"{path.name} 行数为 {len(rows)}，期望 {expected_time * expected_radius}")
        if len(set(times)) != expected_time or len(set(radii)) != expected_radius:
            raise ValueError(f"{path.name} 时间点或半径点数量不符合预期")
        if times != sorted(times) or len(set(pairs)) != len(pairs):
            raise ValueError(f"{path.name} 时间顺序或时空点重复")
        details[path.name] = rows
        if task in (1, 2):
            detail_max[path.name] = {
                "max_abs_dT_C": max(float(row["abs_dT_C"]) for row in rows),
                "max_abs_dC_kgkg": max(float(row["abs_dC_kgkg"]) for row in rows),
            }
        else:
            detail_max[path.name] = {
                "max_abs_table_dC_kgkg": max(float(row["abs_dC_kgkg"]) for row in rows),
            }

    summary_by_file = {row["run_file"]: row for row in summary_rows}
    if set(summary_by_file) != set(details):
        raise ValueError("汇总表与逐点文件集合不一致")
    for filename, maxima in detail_max.items():
        summary = summary_by_file[filename]
        for column, value in maxima.items():
            summary_value = _finite_float(summary[column], f"汇总 {filename} {column}")
            if not math.isclose(summary_value, value, rel_tol=1e-8, abs_tol=1e-14):
                raise ValueError(f"{filename} 的 {column} 与逐点重算不一致")

    counts = defaultdict(int)
    for row in summary_rows:
        counts[int(row["task"])] += 1
    count_text = "、".join(f"问题{TASK_LABELS[task]} {counts[task]} 个" for task in (1, 2, 3, 4))
    print(f"数据审计通过：56 个工况、56 个逐点文件；{count_text}；全部状态为成功。")
    return summary_rows, details


def _baseline_scales(details: dict[str, list[dict[str, str]]]) -> dict[int, dict[str, float]]:
    scales: dict[int, dict[str, float]] = {}
    for task, filename in BASELINE_FILES.items():
        rows = details[filename]
        if task in (1, 2):
            scales[task] = {
                "temperature": max(abs(float(row["base_temperature_C"])) for row in rows),
                "moisture": max(abs(float(row["base_moisture_kgkg"])) for row in rows),
            }
        else:
            scales[task] = {"moisture": max(abs(float(row["base_moisture_kgkg"])) for row in rows)}
    return scales


def build_records(
    summary_rows: list[dict[str, str]], details: dict[str, list[dict[str, str]]]
) -> list[dict[str, Any]]:
    """把每个工况转换成绘图所需的归一化记录。"""

    scales = _baseline_scales(details)
    records: list[dict[str, Any]] = []
    for row in summary_rows:
        task = int(row["task"])
        parameter = row["parameter"]
        value = row["value"]
        baseline = BASELINE_VALUES.get((task, parameter))
        ratio = None if baseline is None else float(value) / baseline
        is_base = _is_baseline(task, parameter, value)
        record: dict[str, Any] = {
            "task": task,
            "parameter": parameter,
            "value": value,
            "ratio": ratio,
            "is_baseline": is_base,
            "is_synthetic": False,
            "level_label": (
                "基准" if is_base else _parameter_value_label(task, parameter, value)
            ),
            "summary": row,
        }
        if task in (1, 2):
            relative_parameter_change = 0.0 if ratio is None else ratio - 1.0
            if abs(relative_parameter_change) < 1e-15:
                gain_temperature = 0.0
                gain_moisture = 0.0
            else:
                gain_temperature = (
                    float(row["max_abs_dT_C"])
                    / scales[task]["temperature"]
                    / abs(relative_parameter_change)
                )
                gain_moisture = (
                    float(row["max_abs_dC_kgkg"])
                    / scales[task]["moisture"]
                    / abs(relative_parameter_change)
                )
            record.update(
                {
                    "gain_temperature": gain_temperature,
                    "gain_moisture": gain_moisture,
                }
            )
        else:
            base_time = float(row["base_termination_time_h"])
            time_relative = float(row["diff_termination_h"]) / base_time
            moisture_relative = (
                float(row["max_abs_table_dC_kgkg"]) / scales[task]["moisture"]
            )
            record.update(
                {
                    "time_relative": time_relative,
                    "moisture_relative": moisture_relative,
                }
            )
        records.append(record)
    return records


def _group_records(records: list[dict[str, Any]], tasks: tuple[int, ...]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["task"] in tasks:
            grouped[(record["task"], record["parameter"])].append(record)
    return dict(grouped)


def _group_sort_key(key: tuple[int, str]) -> tuple[int, int]:
    task, parameter = key
    return task, PARAM_ORDER[task].index(parameter)


def _pair_rows(records: list[dict[str, Any]]) -> tuple[list[str], np.ndarray, list[list[str]]]:
    grouped = _group_records(records, (1, 2))
    groups = sorted(grouped, key=_group_sort_key)
    groups.sort(
        key=lambda key: (
            -max(
                max(item["gain_temperature"] for item in grouped[key]),
                max(item["gain_moisture"] for item in grouped[key]),
            ),
            *_group_sort_key(key),
        )
    )
    labels: list[str] = []
    values: list[list[float]] = []
    annotations: list[list[str]] = []
    for key in groups:
        task, parameter = key
        group = grouped[key]
        labels.append(f"问题{TASK_LABELS[task]}｜{PARAM_LABELS[key]}")
        row_values: list[float] = []
        row_annotations: list[str] = []
        for metric, label in (("gain_temperature", "温度"), ("gain_moisture", "水分")):
            worst = max(group, key=lambda item: item[metric])
            value = float(worst[metric])
            row_values.append(value)
            if value == 0:
                row_annotations.append("0\n各水平均为零")
            else:
                level = _factor_label(worst["ratio"]) if worst["ratio"] is not None else worst["level_label"]
                row_annotations.append(f"{_power_label(value)}\n最坏：{level}")
        values.append(row_values)
        annotations.append(row_annotations)
    return labels, np.asarray(values, dtype=float), annotations


def _single_metric_rows(
    records: list[dict[str, Any]], metric: str, percent: bool = False
) -> tuple[list[str], np.ndarray, list[str]]:
    grouped = _group_records(records, (3, 4))
    groups = sorted(grouped, key=_group_sort_key)
    if metric == "time_relative":
        groups.sort(
            key=lambda key: (
                -max(abs(item[metric]) for item in grouped[key]),
                *_group_sort_key(key),
            )
        )
    else:
        groups.sort(
            key=lambda key: (-max(item[metric] for item in grouped[key]), *_group_sort_key(key))
        )
    labels: list[str] = []
    values: list[float] = []
    annotations: list[str] = []
    for key in groups:
        task, parameter = key
        group = grouped[key]
        labels.append(f"问题{TASK_LABELS[task]}｜{PARAM_LABELS[key]}")
        if metric == "time_relative":
            worst = max(group, key=lambda item: abs(item[metric]))
        else:
            worst = max(group, key=lambda item: item[metric])
        value = float(worst[metric])
        values.append(value * 100.0 if percent else value)
        if abs(value) < 1e-15:
            annotations.append("0\n无差异")
            continue
        if metric == "time_relative":
            shown = _percent_label(value * 100.0)
        else:
            shown = _magnitude_percent_label(value * 100.0)
        level = (
            _factor_label(worst["ratio"]) if worst["ratio"] is not None else worst["level_label"]
        )
        annotations.append(f"{shown}\n最坏：{level}")
    return labels, np.asarray(values, dtype=float), annotations


def _sequential_cmap() -> LinearSegmentedColormap:
    cmap = LinearSegmentedColormap.from_list(
        "归一化单向色",
        ["#F4F7FB", "#C7D9EA", "#6B9BC5", "#174A7A"],
    )
    cmap.set_bad("#EEEEEE")
    return cmap


def _diverging_cmap() -> LinearSegmentedColormap:
    cmap = LinearSegmentedColormap.from_list(
        "时间变化发散色",
        ["#245B8A", "#BFD2E1", "#F5F5F5", "#E7B6A9", "#A63D3D"],
    )
    cmap.set_bad("#EEEEEE")
    return cmap


def _log_ticks(vmin: float, vmax: float) -> list[float]:
    if not 0 < vmin <= vmax:
        return []
    low = int(math.floor(math.log10(vmin)))
    high = int(math.ceil(math.log10(vmax)))
    span = high - low
    step = max(1, int(math.ceil(span / 5)))
    ticks = [10.0**exponent for exponent in range(low, high + 1, step)]
    if not ticks or ticks[-1] < vmax * 0.8:
        ticks.append(10.0**high)
    return sorted({tick for tick in ticks if vmin * 0.5 <= tick <= vmax * 2.0})


def _draw_heatmap(
    ax: mpl.axes.Axes,
    data: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    annotations: list[list[str]],
    *,
    kind: str,
    colorbar_label: str,
) -> None:
    if kind == "log":
        positive = data[np.isfinite(data) & (data > 0)]
        if positive.size == 0:
            positive = np.asarray([1.0])
        vmin = float(np.min(positive))
        vmax = float(np.max(positive))
        if math.isclose(vmin, vmax):
            vmax = vmin * 10.0
        norm: mpl.colors.Normalize = LogNorm(vmin=vmin, vmax=vmax)
        display_data = np.ma.masked_where(~np.isfinite(data) | (data <= 0), data)
        cmap = _sequential_cmap()
    elif kind == "diverging":
        bound = max(float(np.max(np.abs(data))), 1e-12)
        norm = Normalize(vmin=-bound, vmax=bound)
        display_data = np.ma.masked_invalid(data)
        cmap = _diverging_cmap()
    else:
        raise ValueError(f"未知热图类型：{kind}")

    image = ax.imshow(display_data, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks(np.arange(len(column_labels)))
    ax.set_xticklabels(column_labels, fontsize=7.5)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=7.1)
    ax.tick_params(axis="both", length=0, pad=3)
    ax.set_xlim(-0.5, len(column_labels) - 0.5)
    ax.set_ylim(len(row_labels) - 0.5, -0.5)
    for row_index, row in enumerate(annotations):
        for column_index, annotation in enumerate(row):
            value = float(data[row_index, column_index])
            if kind == "log" and value > 0:
                ratio = (math.log10(value) - math.log10(norm.vmin)) / max(
                    1e-12, math.log10(norm.vmax) - math.log10(norm.vmin)
                )
                text_color = "white" if ratio > 0.58 else "#1E2A35"
            elif kind == "diverging":
                text_color = "#1E2A35"
            else:
                text_color = "#1E2A35"
            ax.text(
                column_index,
                row_index,
                annotation,
                ha="center",
                va="center",
                fontsize=6.3,
                color=text_color,
                linespacing=1.15,
            )
    ax.grid(False)
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    colorbar.ax.tick_params(labelsize=6.8, length=2)
    if kind == "log":
        ticks = _log_ticks(float(norm.vmin), float(norm.vmax))
        if ticks:
            colorbar.set_ticks(ticks)
            colorbar.set_ticklabels([_power_label(tick) for tick in ticks])
    else:
        bound = float(norm.vmax)
        ticks = np.linspace(-bound, bound, 5)
        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels([_percent_label(tick) for tick in ticks])
    colorbar.set_label(colorbar_label, fontsize=7.2, labelpad=8)


def _save_publication_figure(fig: mpl.figure.Figure, stem_name: str) -> None:
    stem = OUTPUT_DIR / stem_name
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _main_heatmap(records: list[dict[str, Any]]) -> None:
    q12_labels, q12_data, q12_annotations = _pair_rows(records)
    time_labels, time_data, time_annotations = _single_metric_rows(
        records, "time_relative", percent=True
    )
    moisture_labels, moisture_data, moisture_annotations = _single_metric_rows(
        records, "moisture_relative", percent=True
    )

    panels = [
        (
            q12_data,
            q12_labels,
            ["温度偏差", "水分偏差"],
            q12_annotations,
            "log",
            "归一化误差增益（对数十倍）",
            "问题一、二：关键点归一化误差增益",
            "主图_问题一二_关键点归一化误差增益",
        ),
        (
            time_data[:, None],
            time_labels,
            ["烘干时间相对变化"],
            [[annotation] for annotation in time_annotations],
            "diverging",
            "烘干时间相对变化（百分比）",
            "问题三、四：烘干时间相对变化",
            "主图_问题三四_烘干时间相对变化",
        ),
        (
            moisture_data[:, None],
            moisture_labels,
            ["表格水分相对偏差"],
            [[annotation] for annotation in moisture_annotations],
            "log",
            "表格水分相对偏差（百分比，对数色阶）",
            "问题三、四：表格水分相对偏差",
            "主图_问题三四_表格水分相对偏差",
        ),
    ]

    for data, row_labels, column_labels, annotations, kind, colorbar_label, title, stem in panels:
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        _draw_heatmap(
            ax,
            data,
            row_labels,
            column_labels,
            annotations,
            kind=kind,
            colorbar_label=colorbar_label,
        )
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=8)
        fig.subplots_adjust(left=0.32, right=0.96, top=0.86, bottom=0.12)
        _save_publication_figure(fig, stem)


def _with_joint_baseline(group: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not group or group[0]["parameter"] != "picard_tol":
        return list(group)
    if any(item.get("is_synthetic", False) for item in group):
        return list(group)
    synthetic = dict(group[0])
    synthetic.update(
        {
            "value": "基准",
            "ratio": 1.0,
            "is_baseline": True,
            "is_synthetic": True,
            "level_label": "基准",
            "time_relative": 0.0,
            "moisture_relative": 0.0,
            "gain_temperature": 0.0,
            "gain_moisture": 0.0,
        }
    )
    return list(group) + [synthetic]


def _sorted_response_group(group: list[dict[str, Any]]) -> list[dict[str, Any]]:
    group = _with_joint_baseline(group)
    if group and group[0]["parameter"] == "picard_tol":
        order = {"loosen100x": 0, "基准": 1, "tighten100x": 2}
        return sorted(group, key=lambda item: order.get(item["value"], 9))
    return sorted(group, key=lambda item: float(item["ratio"]))


def _configure_x_axis(ax: mpl.axes.Axes, group: list[dict[str, Any]]) -> None:
    group = _sorted_response_group(group)
    parameter = group[0]["parameter"]
    if parameter == "picard_tol":
        positions = np.arange(len(group), dtype=float)
        labels = [item["level_label"] for item in group]
        ax.set_xlim(-0.25, len(group) - 0.75)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=6.4)
        ax.axvline(1.0, color="#767676", linewidth=0.7, zorder=0)
        return
    ratios = [float(item["ratio"]) for item in group]
    if max(ratios) / min(ratios) >= 4.0:
        ax.set_xscale("log")
    ax.set_xticks(ratios)
    ax.set_xticklabels([_factor_label(ratio) for ratio in ratios], fontsize=6.7)
    if ax.get_xscale() == "log":
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.tick_params(axis="x", which="minor", labelbottom=False)
    ax.axvline(1.0, color="#767676", linewidth=0.7, zorder=0)
    margin = 0.08
    if ax.get_xscale() == "log":
        ax.set_xlim(min(ratios) / (1.0 + margin), max(ratios) * (1.0 + margin))
    else:
        span = max(ratios) - min(ratios)
        span = max(span, 0.2)
        ax.set_xlim(min(ratios) - span * margin, max(ratios) + span * margin)


def _set_safe_symlog_ticks(ax: mpl.axes.Axes, bound: float) -> None:
    """为对称对数纵轴设置不依赖数学字体的数量级刻度。"""

    bound = max(abs(float(bound)), 1e-14)
    linthresh = max(bound * 1e-6, 1e-14)
    exponent_high = int(math.floor(math.log10(bound)))
    positive_ticks: list[float] = []
    for exponent in range(exponent_high, exponent_high - 9, -2):
        tick = 10.0**exponent
        if tick >= linthresh * 1.01 and tick <= bound * 1.05:
            positive_ticks.append(tick)
    positive_ticks = sorted(set(positive_ticks))
    ticks = [0.0] + positive_ticks
    ax.set_yticks(ticks)
    ax.set_yticklabels(["0"] + [_power_label(tick) for tick in positive_ticks])


def _draw_gain_panel(ax: mpl.axes.Axes, group: list[dict[str, Any]], ymax: float) -> None:
    group = _sorted_response_group(group)
    x = np.arange(len(group), dtype=float) if group[0]["parameter"] == "picard_tol" else np.asarray([item["ratio"] for item in group], dtype=float)
    if group[0]["parameter"] != "picard_tol" and max(x) / min(x) >= 4.0:
        ax.set_xscale("log")
    ax.plot(
        x,
        [item["gain_temperature"] for item in group],
        color="#245B8A",
        marker="o",
        markersize=3.5,
        linewidth=1.1,
        label="温度偏差",
    )
    ax.plot(
        x,
        [item["gain_moisture"] for item in group],
        color="#C77A3B",
        marker="o",
        markersize=3.5,
        linewidth=1.1,
        label="水分偏差",
    )
    ax.axhline(0.0, color="#9B9B9B", linewidth=0.65, zorder=0)
    ax.set_yscale("symlog", linthresh=max(ymax * 1e-6, 1e-14), linscale=0.8)
    ax.set_ylim(-max(ymax * 0.06, 1e-14), ymax * 1.14)
    _set_safe_symlog_ticks(ax, ymax)
    _configure_x_axis(ax, group)
    task = group[0]["task"]
    parameter = group[0]["parameter"]
    ax.set_title(f"问题{TASK_LABELS[task]}｜{PARAM_LABELS[(task, parameter)]}", fontsize=8.2, pad=5)
    ax.tick_params(axis="both", labelsize=6.5, length=2, width=0.65)
    ax.grid(axis="y", color="#E2E2E2", linewidth=0.45)


def _draw_single_response_panel(
    ax: mpl.axes.Axes,
    group: list[dict[str, Any]],
    metric: str,
    ymax: float,
) -> None:
    group = _sorted_response_group(group)
    categorical = group[0]["parameter"] == "picard_tol"
    x = np.arange(len(group), dtype=float) if categorical else np.asarray([item["ratio"] for item in group], dtype=float)
    if not categorical and max(x) / min(x) >= 10.0:
        ax.set_xscale("log")
    values = np.asarray([float(item[metric]) * 100.0 for item in group], dtype=float)
    if metric == "time_relative":
        ax.plot(x, values, color="#A63D3D", marker="o", markersize=3.7, linewidth=1.1)
        ax.axhline(0.0, color="#767676", linewidth=0.75, zorder=0)
        ax.set_ylim(-max(ymax * 1.16, 1e-8), max(ymax * 1.16, 1e-8))
        percent_ticks = np.linspace(-ymax, ymax, 5)
        ax.set_yticks(percent_ticks)
        ax.set_yticklabels([_percent_label(tick) for tick in percent_ticks])
    else:
        ax.plot(x, values, color="#2A8C8C", marker="o", markersize=3.7, linewidth=1.1)
        ax.axhline(0.0, color="#767676", linewidth=0.75, zorder=0)
        ax.set_yscale("symlog", linthresh=max(ymax * 1e-6, 1e-10), linscale=0.8)
        ax.set_ylim(-max(ymax * 0.06, 1e-10), max(ymax * 1.16, 1e-10))
        _set_safe_symlog_ticks(ax, ymax)
    _configure_x_axis(ax, group)
    task = group[0]["task"]
    parameter = group[0]["parameter"]
    ax.set_title(f"问题{TASK_LABELS[task]}｜{PARAM_LABELS[(task, parameter)]}", fontsize=8.0, pad=5)
    ax.tick_params(axis="both", labelsize=6.3, length=2, width=0.65)
    ax.grid(axis="y", color="#E2E2E2", linewidth=0.45)


def _response_figure_one(records: list[dict[str, Any]]) -> None:
    grouped = _group_records(records, (1, 2))
    groups = [grouped[key] for key in sorted(grouped, key=_group_sort_key)]
    ymax_by_task = {
        task: max(
            max(
                max(item["gain_temperature"] for item in group),
                max(item["gain_moisture"] for item in group),
            )
            for key, group in grouped.items()
            if key[0] == task
        )
        for task in (1, 2)
    }
    ymax_by_task = {task: max(value, 1e-12) for task, value in ymax_by_task.items()}
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 7.8), squeeze=False)
    for ax, group in zip(axes.flat, groups):
        _draw_gain_panel(ax, group, ymax_by_task[group[0]["task"]])
    for ax in axes[:, 0]:
        ax.set_ylabel("归一化误差增益", fontsize=7.1)
    for ax in axes[-1, :]:
        ax.set_xlabel("参数取值/基准取值", fontsize=7.1)
    handles = [
        mpl.lines.Line2D([], [], color="#245B8A", marker="o", linewidth=1.1, markersize=3.5, label="温度偏差"),
        mpl.lines.Line2D([], [], color="#C77A3B", marker="o", linewidth=1.1, markersize=3.5, label="水分偏差"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.973), fontsize=7.1)
    fig.suptitle("补图一：问题一和问题二各参数的归一化误差增益响应", fontsize=12, fontweight="bold", y=0.995)
    fig.text(
        0.5,
        0.008,
        "归一化误差增益＝归一化结果偏差÷相对参数扰动；每个面板包含该参数的全部测试水平，灰色竖线为基准取值；同一问题使用统一纵轴范围。",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color="#4D4D4D",
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.91, bottom=0.075, hspace=0.48, wspace=0.35)
    _save_publication_figure(fig, "补图一_问题一二_归一化误差增益响应")


def _response_figure_single_metric(
    records: list[dict[str, Any]], metric: str, stem: str, title: str, ylabel: str
) -> None:
    grouped = _group_records(records, (3, 4))
    groups = [grouped[key] for key in sorted(grouped, key=_group_sort_key)]
    all_values = [abs(float(item[metric]) * 100.0) for group in groups for item in group]
    ymax_by_task = {
        task: max(
            max(
                abs(float(item[metric]) * 100.0)
                for key, group in grouped.items()
                if key[0] == task
                for item in group
            ),
            1e-8,
        )
        for task in (3, 4)
    }
    fig, axes = plt.subplots(4, 3, figsize=(7.2, 10.7), squeeze=False)
    axes_flat = list(axes.flat)
    for ax, group in zip(axes_flat, groups):
        _draw_single_response_panel(ax, group, metric, ymax_by_task[group[0]["task"]])
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel, fontsize=7.0)
    for ax in axes[-1, :]:
        ax.set_xlabel("参数取值/基准取值", fontsize=7.0)
    for ax in axes_flat[len(groups) :]:
        ax.remove()
    fig.suptitle(title, fontsize=12, fontweight="bold", y=0.995)
    if metric == "time_relative":
        note = "烘干时间相对变化＝（扰动烘干时间减基准烘干时间）÷基准烘干时间；正值表示延长，负值表示缩短。"
    else:
        note = "表格水分相对偏差＝最大绝对水分差÷基准水分最大值；每个面板包含该参数的全部测试水平。"
    note += "同一问题使用统一纵轴范围，跨问题比较以主图为准。"
    fig.text(0.5, 0.008, note, ha="center", va="bottom", fontsize=7.2, color="#4D4D4D")
    fig.subplots_adjust(left=0.095, right=0.98, top=0.955, bottom=0.06, hspace=0.66, wspace=0.42)
    _save_publication_figure(fig, stem)


def main() -> None:
    summary_rows, details = audit_results()
    records = build_records(summary_rows, details)
    _main_heatmap(records)
    print("已生成 3 张主图；每张图均输出 SVG、PDF 和 PNG。")


if __name__ == "__main__":
    main()
