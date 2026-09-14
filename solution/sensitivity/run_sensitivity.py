"""A题敏感度分析驱动。

对问题一至问题四逐一扰动一个数值参数（其余参数保持当前代码值），
把每次扰动相对基准工况的结果差写成 ``taskN-参数-取值.csv``，并把所有
标量指标汇总到 ``sensitivity_summary.csv``。

设计要点：
- 通过显式路径 importlib 加载四个 solver 脚本，绝不执行它们的 __main__；
- 任务三/四的 STABLE_START_S、TIME_STEP_EARLY_S、PICARD_* 是模块级全局，
  运行前临时改写即可（解释器在函数调用时读取）；
- 任务二 Picard 容差是 ``_picard_step`` 的默认参数（定义时已绑定），
  必须同时改写模块全局和 ``__defaults__``；
- 每个 work 在独立进程里重新加载模块，避免全局改写相互污染。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

MODULE_PATHS = {
    1: ROOT / "solution" / "task1" / "script" / "solve_task1.py",
    2: ROOT / "solution" / "task2" / "script" / "solve_task2.py",
    3: ROOT / "solution" / "task3" / "script" / "solve_task3.py",
    4: ROOT / "solution" / "task4" / "script" / "solve_task4.py",
}

KEY_TIMES_S = np.array([100, 300, 600, 900, 1200, 1500, 1800], dtype=float)
KEY_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
T2_TIMES_S = np.array([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
TABLE5_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
TABLE6_RADII_LABEL = ["0.0", "0.5", "1.0", "surface"]

# ---------------------------------------------------------------------------
# 参数配置：default 即题目要求的“当前代码值”，knobs 每项为 (标签, 覆写字典)。
# 问题一、二的基准口径与 handoff 正文一致：
#   问题一 守恒 FVM + CN + Picard，dr=5e-5 m，dt=0.25 s；
#   问题二 守恒 FVM + CN + 同步 Picard，N=1600（dr=1.25e-5 m），dt=1 s。
# ---------------------------------------------------------------------------
T1_DEFAULT = dict(dr_m=0.00005, dt_s=0.25, picard_tol_C=1e-10, linear_residual_tol=1e-10)
T1_KNOBS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "dr_m": [("0.0001", dict(dr_m=0.0001)), ("0.00005", dict(dr_m=0.00005)), ("0.000025", dict(dr_m=0.000025))],
    "dt_s": [("0.5", dict(dt_s=0.5)), ("0.25", dict(dt_s=0.25)), ("0.125", dict(dt_s=0.125))],
    "picard_tol_C": [("1e-08", dict(picard_tol_C=1e-8)), ("1e-10", dict(picard_tol_C=1e-10)), ("1e-12", dict(picard_tol_C=1e-12))],
    "linear_residual_tol": [("1e-08", dict(linear_residual_tol=1e-8)), ("1e-10", dict(linear_residual_tol=1e-10)), ("1e-12", dict(linear_residual_tol=1e-12))],
}

T2_DEFAULT = dict(time_step_s=1.0, dr_m=0.0000125, picard_t=1e-8, picard_c=1e-10)
T2_KNOBS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "time_step_s": [("1", dict(time_step_s=1.0)), ("0.5", dict(time_step_s=0.5)), ("0.25", dict(time_step_s=0.25))],
    "dr_m": [("0.000025", dict(dr_m=0.000025)), ("0.0000125", dict(dr_m=0.0000125)), ("0.00000625", dict(dr_m=0.00000625))],
    "picard_tol_T": [("1e-06", dict(picard_t=1e-6)), ("1e-08", dict(picard_t=1e-8)), ("1e-10", dict(picard_t=1e-10))],
    "picard_tol_C": [("1e-08", dict(picard_c=1e-8)), ("1e-10", dict(picard_c=1e-10)), ("1e-12", dict(picard_c=1e-12))],
}

T3_DEFAULT = dict(n_intervals=1600, time_step_long_s=10.0, time_step_early_s=1.0, stable_start=9000.0, picard_t=1e-8, picard_c=1e-10)
T3_KNOBS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "n_intervals": [("200", dict(n_intervals=200)), ("400", dict(n_intervals=400)), ("800", dict(n_intervals=800)), ("1600", dict(n_intervals=1600))],
    "time_step_long_s": [("20", dict(time_step_long_s=20.0)), ("10", dict(time_step_long_s=10.0)), ("5", dict(time_step_long_s=5.0))],
    "TIME_STEP_EARLY_S": [("2", dict(time_step_early_s=2.0)), ("1", dict(time_step_early_s=1.0)), ("0.5", dict(time_step_early_s=0.5))],
    "STABLE_START_S": [("7200", dict(stable_start=7200.0)), ("9000", dict(stable_start=9000.0)), ("10800", dict(stable_start=10800.0))],
    "picard_tol": [("loosen100x", dict(picard_t=1e-6, picard_c=1e-8)), ("tighten100x", dict(picard_t=1e-10, picard_c=1e-12))],
}

T4_DEFAULT = dict(n_intervals=800, time_step_long_s=5.0, time_step_early_s=1.0, stable_start=9000.0, event_tol_s=0.1, picard_t=1e-8, picard_c=1e-10)
T4_KNOBS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "n_intervals": [("400", dict(n_intervals=400)), ("800", dict(n_intervals=800)), ("1600", dict(n_intervals=1600))],
    "time_step_long_s": [("10", dict(time_step_long_s=10.0)), ("5", dict(time_step_long_s=5.0)), ("2.5", dict(time_step_long_s=2.5))],
    "time_step_early_s": [("2", dict(time_step_early_s=2.0)), ("1", dict(time_step_early_s=1.0)), ("0.5", dict(time_step_early_s=0.5))],
    "STABLE_START_S": [("7200", dict(stable_start=7200.0)), ("9000", dict(stable_start=9000.0)), ("10800", dict(stable_start=10800.0))],
    "event_tol_s": [("1", dict(event_tol_s=1.0)), ("0.1", dict(event_tol_s=0.1)), ("0.01", dict(event_tol_s=0.01))],
    "picard_tol": [("loosen100x", dict(picard_t=1e-6, picard_c=1e-8)), ("tighten100x", dict(picard_t=1e-10, picard_c=1e-12))],
}

DEFAULTS = {1: T1_DEFAULT, 2: T2_DEFAULT, 3: T3_DEFAULT, 4: T4_DEFAULT}
KNOBS = {1: T1_KNOBS, 2: T2_KNOBS, 3: T3_KNOBS, 4: T4_KNOBS}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_provenance(out_dir: Path, tasks: list[int]) -> None:
    """Persist the exact source files and numerical defaults used by a run."""

    source_paths: dict[str, Path] = {
        "sensitivity_runner": Path(__file__).resolve(),
        "attachment_1": ROOT / "problem" / "附件" / "附件1.xlsx",
    }
    for task in tasks:
        source_paths[f"task{task}_solver"] = MODULE_PATHS[task]
        handoff = ROOT / "handoff" / f"task{task}_handoff.md"
        if handoff.is_file():
            source_paths[f"task{task}_handoff"] = handoff
    payload = {
        "tasks": tasks,
        "defaults": {str(task): DEFAULTS[task] for task in tasks},
        "source_sha256": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in source_paths.items()
            if path.is_file()
        },
    }
    (out_dir / "sensitivity_provenance.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load(task: int, unique: str) -> Any:
    spec = importlib.util.spec_from_file_location(f"solver_task{task}_{unique}", MODULE_PATHS[task])
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载任务{task}求解器 {MODULE_PATHS[task]}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cfg(task: int, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(DEFAULTS[task])
    if overrides:
        config.update(overrides)
    return config


# ---------------------------------------------------------------------------
# 基准小结果：只保留后续比较需要的少量数组/标量。
# ---------------------------------------------------------------------------
def _base_task1() -> dict[str, Any]:
    m = _load(1, "base")
    sol = _t1_solve(m, T1_DEFAULT)
    T, C = _t1_key(sol)
    m.validate_solution(sol)
    return {"T": T, "C": C}


def _base_task2() -> dict[str, Any]:
    m = _load(2, "base")
    sol = _t2_solve(m, T2_DEFAULT)
    T, C = _t2_key(m, sol)
    m.validate_solution(sol)
    return {"T": T, "C": C}


def _base_task3() -> dict[str, Any]:
    m = _load(3, "base")
    sol, _summary = _t3_solve(m, T3_DEFAULT)
    times, rows = m.table5_from_solution(sol)
    regular = np.asarray(rows[:-1], dtype=float)
    return {"t_dry_h": float(sol["termination_time_s"]) / 3600.0, "times_h": (np.asarray(times, dtype=float) / 3600.0), "rows": regular}


def _base_task4() -> dict[str, Any]:
    m = _load(4, "base")
    sol, _summary = _t4_solve(m, T4_DEFAULT)
    rows = m._paper_rows(sol)
    hours = np.asarray([float(r[0]) for r in rows[:-1]], dtype=float)
    values = np.asarray([[float(x) for x in r[1:]] for r in rows[:-1]], dtype=float)
    return {"t_dry_h": float(sol["termination_time_s"]) / 3600.0, "hours": hours, "values": values}


def _t1_solve(m: Any, config: dict[str, Any]) -> dict[str, Any]:
    # 问题一的 Picard 容差与线性残差容差是模块级全局，运行前临时改写。
    m.PICARD_TOL = config["picard_tol_C"]
    m.LINEAR_RESIDUAL_TOL = config["linear_residual_tol"]
    return m.solve_task1(dr_m=config["dr_m"], dt_s=config["dt_s"])


def _t1_key(sol: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    time_s = np.asarray(sol["time_s"], dtype=float)
    t_idx = np.searchsorted(time_s, KEY_TIMES_S, side="left")
    if not np.allclose(time_s[t_idx], KEY_TIMES_S, rtol=0.0, atol=1.0e-9):
        raise ValueError("问题一输出缺少关键时间点")
    r_idx = np.array([0, 5, 10, 15, 20], dtype=int)
    T = np.asarray(sol["temperature_C"], dtype=float)[np.ix_(t_idx, r_idx)]
    C = np.asarray(sol["moisture_kgkg"], dtype=float)[np.ix_(t_idx, r_idx)]
    return T, C


def _t2_key(m: Any, sol: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    _times, _radii, T, C = m._key_point_values(sol)
    return np.asarray(T, dtype=float), np.asarray(C, dtype=float)


def _t2_solve(m: Any, config: dict[str, Any]) -> dict[str, Any]:
    # Picard 容差是默认参数，必须同时改写全局与 __defaults__。
    m.PICARD_TOL_T_C = config["picard_t"]
    m.PICARD_TOL_C_KGKG = config["picard_c"]
    m._picard_step.__defaults__ = (config["picard_t"], config["picard_c"], m.PICARD_MAX_ITER)
    return m.solve_task2(time_step_s=config["time_step_s"], dr_m=config["dr_m"])


def _t3_solve(m: Any, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m.STABLE_START_S = config["stable_start"]
    m.TIME_STEP_EARLY_S = config["time_step_early_s"]
    m.PICARD_TOL_T_C = config["picard_t"]
    m.PICARD_TOL_C_KGKG = config["picard_c"]
    sol = m.solve_task3(n_intervals=config["n_intervals"], time_step_long_s=config["time_step_long_s"], collect_first3=False)
    summary = m.validate_solution(sol, require_first3=False)
    return sol, summary


def _t4_solve(m: Any, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    m.STABLE_START_S = config["stable_start"]
    m.PICARD_TOL_T_C = config["picard_t"]
    m.PICARD_TOL_C_KGKG = config["picard_c"]
    sol = m.solve_task4(n_intervals=config["n_intervals"], time_step_long_s=config["time_step_long_s"], time_step_early_s=config["time_step_early_s"], event_tol_s=config["event_tol_s"])
    summary = m.validate_solution(sol)
    return sol, summary


def _write_task12_diagnostics(
    module: Any,
    solution: dict[str, Any],
    out_dir: Path,
    stem: str,
) -> None:
    """Persist the solver's Picard/physics/conservation audit for one run.

    The formal answer diagnostics live beside each task answer.  Sensitivity
    runs are independent numerical experiments, so keep their per-step logs
    under a dedicated subdirectory instead of mixing them with the pointwise
    comparison CSV files consumed by the plotting audit.
    """

    diagnostics_dir = out_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    write_diagnostics = getattr(module, "write_diagnostics", None)
    diagnostics_summary = getattr(module, "diagnostics_summary", None)
    if not callable(write_diagnostics) or not callable(diagnostics_summary):
        raise AttributeError("当前 Task1/Task2 solver 未提供诊断日志接口")
    write_diagnostics(
        solution,
        diagnostics_dir / f"{stem}.json",
        diagnostics_dir / f"{stem}.csv",
    )


# ---------------------------------------------------------------------------
# 单次运行：返回标量摘要，并在需要时写出逐点比较 CSV。
# ---------------------------------------------------------------------------
def _execute(job: dict[str, Any]) -> dict[str, Any]:
    if job["kind"] == "base":
        funcs = {1: _base_task1, 2: _base_task2, 3: _base_task3, 4: _base_task4}
        return {"task": job["task"], "kind": "base", "base": funcs[job["task"]]()}

    task = job["task"]
    parameter = job["parameter"]
    label = job["label"]
    config = job["config"]
    base = job["base"]
    out_dir = Path(job["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    row: dict[str, Any] = {
        "task": task,
        "parameter": parameter,
        "value": label,
        "status": "ok",
        "run_file": f"task{task}-{parameter}-{label}.csv",
        "termination_time_h": "",
        "base_termination_time_h": "",
        "diff_termination_h": "",
        "max_abs_dT_C": "",
        "max_abs_dC_kgkg": "",
        "max_abs_table_dC_kgkg": "",
        "max_picard_iterations": "",
        "mean_picard_iterations": "",
        "runtime_s": "",
    }
    try:
        if task == 1:
            m = _load(1, f"{parameter}_{label}")
            sol = _t1_solve(m, config)
            T, C = _t1_key(sol)
            _write_task12_csv(out_dir / row["run_file"], task, parameter, label, KEY_TIMES_S, KEY_RADII_CM, T, C, base["T"], base["C"])
            row["max_abs_dT_C"] = float(np.max(np.abs(T - base["T"])))
            row["max_abs_dC_kgkg"] = float(np.max(np.abs(C - base["C"])))
            iterations = np.asarray(sol["picard_iterations"], dtype=int)
            row["max_picard_iterations"] = int(np.max(iterations))
            row["mean_picard_iterations"] = float(np.mean(iterations))
            m.validate_solution(sol)
            _write_task12_diagnostics(
                m,
                sol,
                out_dir,
                f"task1-{parameter}-{label}",
            )
        elif task == 2:
            m = _load(2, f"{parameter}_{label}")
            sol = _t2_solve(m, config)
            T, C = _t2_key(m, sol)
            _write_task12_csv(out_dir / row["run_file"], task, parameter, label, T2_TIMES_S, KEY_RADII_CM, T, C, base["T"], base["C"])
            row["max_abs_dT_C"] = float(np.max(np.abs(T - base["T"])))
            row["max_abs_dC_kgkg"] = float(np.max(np.abs(C - base["C"])))
            iterations = np.asarray(sol["iteration_counts"], dtype=int)
            row["max_picard_iterations"] = int(np.max(iterations))
            row["mean_picard_iterations"] = float(np.mean(iterations))
            m.validate_solution(sol)
            _write_task12_diagnostics(
                m,
                sol,
                out_dir,
                f"task2-{parameter}-{label}",
            )
        elif task == 3:
            m = _load(3, f"{parameter}_{label}")
            sol, summary = _t3_solve(m, config)
            times_h, rows = m.table5_from_solution(sol)
            regular_times_h = np.asarray(times_h, dtype=float) / 3600.0
            regular_rows = np.asarray(rows[:-1], dtype=float)
            row["termination_time_h"] = float(sol["termination_time_s"]) / 3600.0
            row["base_termination_time_h"] = base["t_dry_h"]
            row["diff_termination_h"] = row["termination_time_h"] - base["t_dry_h"]
            table_diff = _common_table_diff(base["times_h"], base["rows"], regular_times_h, regular_rows)
            row["max_abs_table_dC_kgkg"] = table_diff
            _write_task34_csv(out_dir / row["run_file"], task, parameter, label, regular_times_h, TABLE5_RADII_CM, regular_rows, base["times_h"], base["rows"])
            row["max_picard_iterations"] = int(summary["max_picard_iterations"])
            row["mean_picard_iterations"] = float(summary["mean_picard_iterations"])
        elif task == 4:
            m = _load(4, f"{parameter}_{label}")
            sol, summary = _t4_solve(m, config)
            paper = m._paper_rows(sol)
            hours = np.asarray([float(r[0]) for r in paper[:-1]], dtype=float)
            values = np.asarray([[float(x) for x in r[1:]] for r in paper[:-1]], dtype=float)
            row["termination_time_h"] = float(sol["termination_time_s"]) / 3600.0
            row["base_termination_time_h"] = base["t_dry_h"]
            row["diff_termination_h"] = row["termination_time_h"] - base["t_dry_h"]
            row["max_abs_table_dC_kgkg"] = _common_table_diff(base["hours"], base["values"], hours, values)
            _write_task34_csv(out_dir / row["run_file"], task, parameter, label, hours, TABLE6_RADII_LABEL, values, base["hours"], base["values"])
            row["max_picard_iterations"] = int(summary["max_picard_iterations"])
            row["mean_picard_iterations"] = float(summary["mean_picard_iterations"])
        else:
            raise ValueError(f"未知任务编号 {task}")
    except Exception as exc:  # noqa: BLE001 - 记录任何数值失败但不终止整批
        row["status"] = "error"
        row["error"] = f"{type(exc).__name__}: {exc}"
        (out_dir / f"task{task}-{parameter}-{label}.err").write_text(traceback.format_exc(), encoding="utf-8")
    row["runtime_s"] = round(time.perf_counter() - started, 3)
    return {"task": task, "kind": "run", "summary": row}


def _common_table_diff(base_times: np.ndarray, base_rows: np.ndarray, run_times: np.ndarray, run_rows: np.ndarray) -> float:
    base_times = np.asarray(base_times, dtype=float)
    run_times = np.asarray(run_times, dtype=float)
    base_rows = np.atleast_2d(np.asarray(base_rows, dtype=float))
    run_rows = np.atleast_2d(np.asarray(run_rows, dtype=float))
    max_diff = 0.0
    for i, t in enumerate(run_times):
        matches = np.flatnonzero(np.isclose(base_times, t, atol=1e-6, rtol=0.0))
        if matches.size != 1:
            continue
        diff = np.abs(run_rows[i] - base_rows[int(matches[0])])
        max_diff = max(max_diff, float(np.max(diff)))
    return max_diff


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def _write_task12_csv(path: Path, task: int, parameter: str, label: str, times: np.ndarray, radii: np.ndarray, T: np.ndarray, C: np.ndarray, base_T: np.ndarray, base_C: np.ndarray) -> None:
    rows: list[list[Any]] = []
    for ti, time_s in enumerate(times):
        for ri, radius_cm in enumerate(radii):
            rows.append([
                task, parameter, label, f"{time_s:.0f}", f"{radius_cm:.1f}",
                f"{T[ti, ri]:.10g}", f"{C[ti, ri]:.10g}",
                f"{base_T[ti, ri]:.10g}", f"{base_C[ti, ri]:.10g}",
                f"{abs(T[ti, ri] - base_T[ti, ri]):.10g}", f"{abs(C[ti, ri] - base_C[ti, ri]):.10g}",
            ])
    _write_csv(path, ["task", "parameter", "value", "time_s", "radius_cm", "temperature_C", "moisture_kgkg", "base_temperature_C", "base_moisture_kgkg", "abs_dT_C", "abs_dC_kgkg"], rows)


def _write_task34_csv(path: Path, task: int, parameter: str, label: str, times: np.ndarray, radii: Any, values: np.ndarray, base_times: np.ndarray, base_values: np.ndarray) -> None:
    rows: list[list[Any]] = []
    for ti, time_value in enumerate(times):
        matches = np.flatnonzero(np.isclose(np.asarray(base_times, dtype=float), float(time_value), atol=1e-6, rtol=0.0))
        base_row = np.asarray(base_values, dtype=float)[int(matches[0])] if matches.size == 1 else np.full(np.asarray(values).shape[1], np.nan)
        for ri, radius in enumerate(radii):
            rows.append([
                task, parameter, label, f"{float(time_value):.6g}", str(radius),
                f"{values[ti, ri]:.10g}", f"{base_row[ri]:.10g}", f"{abs(values[ti, ri] - base_row[ri]):.10g}",
            ])
    _write_csv(path, ["task", "parameter", "value", "time_h", "radius_cm", "moisture_kgkg", "base_moisture_kgkg", "abs_dC_kgkg"], rows)


SUMMARY_HEADER = [
    "task", "parameter", "value", "status", "run_file",
    "termination_time_h", "base_termination_time_h", "diff_termination_h",
    "max_abs_dT_C", "max_abs_dC_kgkg", "max_abs_table_dC_kgkg",
    "max_picard_iterations", "mean_picard_iterations", "runtime_s",
]


def _build_jobs(tasks: list[int], out_dir: Path, bases: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for task in tasks:
        for parameter, entries in KNOBS[task].items():
            for label, overrides in entries:
                config = _cfg(task, overrides)
                if config == DEFAULTS[task]:
                    jobs.append({
                        "kind": "run", "task": task, "parameter": parameter, "label": label,
                        "config": config, "base": bases[task], "out_dir": str(out_dir), "reuse_base": True,
                    })
                else:
                    jobs.append({
                        "kind": "run", "task": task, "parameter": parameter, "label": label,
                        "config": config, "base": bases[task], "out_dir": str(out_dir), "reuse_base": False,
                    })
    return jobs


def _run_base_reuse(job: dict[str, Any]) -> dict[str, Any]:
    task = job["task"]
    base = job["base"]
    started = time.perf_counter()
    row = {
        "task": task, "parameter": job["parameter"], "value": job["label"], "status": "ok",
        "run_file": f"task{task}-{job['parameter']}-{job['label']}.csv",
        "termination_time_h": "", "base_termination_time_h": "", "diff_termination_h": "",
        "max_abs_dT_C": "", "max_abs_dC_kgkg": "", "max_abs_table_dC_kgkg": "",
        "max_picard_iterations": "", "mean_picard_iterations": "",
        "runtime_s": round(time.perf_counter() - started, 3),
    }
    if task == 1:
        _write_task12_csv(Path(job["out_dir"]) / row["run_file"], 1, job["parameter"], job["label"], KEY_TIMES_S, KEY_RADII_CM, base["T"], base["C"], base["T"], base["C"])
        row["max_abs_dT_C"] = 0.0
        row["max_abs_dC_kgkg"] = 0.0
    elif task == 2:
        _write_task12_csv(Path(job["out_dir"]) / row["run_file"], 2, job["parameter"], job["label"], T2_TIMES_S, KEY_RADII_CM, base["T"], base["C"], base["T"], base["C"])
        row["max_abs_dT_C"] = 0.0
        row["max_abs_dC_kgkg"] = 0.0
    elif task == 3:
        row["termination_time_h"] = base["t_dry_h"]
        row["base_termination_time_h"] = base["t_dry_h"]
        row["diff_termination_h"] = 0.0
        row["max_abs_table_dC_kgkg"] = 0.0
        _write_task34_csv(Path(job["out_dir"]) / row["run_file"], 3, job["parameter"], job["label"], base["times_h"], TABLE5_RADII_CM, base["rows"], base["times_h"], base["rows"])
    elif task == 4:
        row["termination_time_h"] = base["t_dry_h"]
        row["base_termination_time_h"] = base["t_dry_h"]
        row["diff_termination_h"] = 0.0
        row["max_abs_table_dC_kgkg"] = 0.0
        _write_task34_csv(Path(job["out_dir"]) / row["run_file"], 4, job["parameter"], job["label"], base["hours"], TABLE6_RADII_LABEL, base["values"], base["hours"], base["values"])
    return {"task": task, "kind": "run", "summary": row}


def run(tasks: list[int], out_dir: Path, jobs: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_provenance(out_dir, tasks)
    bases: dict[int, dict[str, Any]] = {}

    print(f"[sensitivity] 计算基准工况: tasks={tasks}, workers={jobs}", flush=True)
    if jobs > 1 and len(tasks) > 1:
        with ProcessPoolExecutor(max_workers=min(jobs, len(tasks))) as pool:
            futures = {pool.submit(_execute, {"kind": "base", "task": t}): t for t in tasks}
            for future in as_completed(futures):
                result = future.result()
                bases[result["task"]] = result["base"]
                print(f"  base task{result['task']} 完成", flush=True)
    else:
        for task in tasks:
            result = _execute({"kind": "base", "task": task})
            bases[task] = result["base"]
            print(f"  base task{task} 完成", flush=True)

    all_jobs = _build_jobs(tasks, out_dir, bases)
    # 基准工况自身直接复用，避免重复求解。
    reuse_jobs = [job for job in all_jobs if job.get("reuse_base")]
    run_jobs = [job for job in all_jobs if not job.get("reuse_base")]
    summaries: list[dict[str, Any]] = [_run_base_reuse(job)["summary"] for job in reuse_jobs]

    print(f"[sensitivity] 开始 {len(run_jobs)} 个扰动工况，workers={jobs}", flush=True)
    if jobs > 1 and run_jobs:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(_execute, job): job for job in run_jobs}
            for future in as_completed(futures):
                result = future.result()
                summaries.append(result["summary"])
                summary = result["summary"]
                print(
                    f"  [{summary['status']}] task{summary['task']} {summary['parameter']}={summary['value']} "
                    f"dT={summary['max_abs_dT_C']} dC={summary['max_abs_dC_kgkg']} "
                    f"t_dry={summary['termination_time_h']} diff_h={summary['diff_termination_h']} "
                    f"({summary['runtime_s']}s)",
                    flush=True,
                )
    else:
        for job in run_jobs:
            result = _execute(job)
            summaries.append(result["summary"])
            summary = result["summary"]
            print(
                f"  [{summary['status']}] task{summary['task']} {summary['parameter']}={summary['value']} "
                f"dT={summary['max_abs_dT_C']} dC={summary['max_abs_dC_kgkg']} "
                f"t_dry={summary['termination_time_h']} diff_h={summary['diff_termination_h']} "
                f"({summary['runtime_s']}s)",
                flush=True,
            )

    summaries.sort(key=lambda item: (int(item["task"]), str(item["parameter"]), str(item["value"])))
    summary_path = out_dir / "sensitivity_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_HEADER)
        writer.writeheader()
        for summary in summaries:
            writer.writerow({key: summary.get(key, "") for key in SUMMARY_HEADER})
    print(f"[sensitivity] 汇总已写入 {summary_path}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="A题问题一至问题四敏感度分析")
    parser.add_argument("--tasks", type=int, nargs="+", default=[1, 2, 3, 4], choices=[1, 2, 3, 4])
    parser.add_argument("--jobs", type=int, default=4, help="并行进程数（默认4）")
    parser.add_argument("--out", type=Path, default=ROOT / "solution" / "sensitivity" / "results")
    args = parser.parse_args()
    tasks = sorted(set(args.tasks))
    print(json.dumps({"tasks": tasks, "jobs": args.jobs, "out": str(args.out)}, ensure_ascii=False), flush=True)
    run(tasks, args.out, max(1, args.jobs))


if __name__ == "__main__":
    main()
