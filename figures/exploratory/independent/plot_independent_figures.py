"""Independent publication figures for the medicinal-material drying model.

This script is deliberately built from the validated ``solution`` outputs and
the problem statement.  It does not import or inspect any existing figure
script or rendered figure.  The four figures form a compact visual argument:

* preheating establishes a surface-first radial gradient;
* the full-process solution couples temperature and moisture in state space;
* the drying threshold is reached earlier when shrinkage is allowed; and
* the moving-boundary field is best read in material coordinates and then
  mapped back to physical radius.

All plots, previews, and exports use Python/matplotlib only.  The source CSV
files remain untouched; interpolation in the material-coordinate heatmap is
used only to display the supplied discrete states continuously.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter


def _register_chinese_font() -> tuple[str | None, str]:
    """Register the first available CJK font and return its path and family."""

    candidates = (
        Path.home() / ".fonts" / "SimHei.ttf",
        Path.home() / "Library" / "Fonts" / "SimHei.ttf",
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    )
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            family = font_manager.FontProperties(fname=str(path)).get_name()
            return str(path), family
    return None, "DejaVu Sans"


CHINESE_FONT_PATH, CHINESE_FONT_FAMILY = _register_chinese_font()
FONT_FALLBACK = [
    CHINESE_FONT_FAMILY,
    "Hiragino Sans GB",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]


# Nature-figure Python contract: editable SVG text and TrueType PDF text.
mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": FONT_FALLBACK,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        # Use the ASCII minus sign so tick labels remain reliable across CJK
        # fonts whose math fallback does not provide U+2212.
        "axes.unicode_minus": False,
        "ps.fonttype": 42,
        "font.size": 8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.75,
        "legend.frameon": False,
        "axes.titleweight": "semibold",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


# ``independent`` is nested under ``figures/exploratory``; the repository root
# is therefore three parents above this file.
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "outputs"

Q1_PATH = ROOT / "solution" / "task1" / "answer" / "task1_result.csv"
Q2_PATH = ROOT / "solution" / "task2" / "answer" / "task2_all_results.csv"
Q3_PATH = ROOT / "solution" / "task3" / "answer" / "task3_all_results.csv"
Q4_PATH = ROOT / "solution" / "task4" / "answer" / "task4_all_answers.csv"
Q3_SUMMARY_PATH = ROOT / "solution" / "sensitivity" / "results" / "sensitivity_summary.csv"
SOURCE_MANIFEST_PATH = Path(__file__).resolve().parent / "source_hashes.json"


# A low-saturation semantic palette: cool tones for the material state,
# warm tones for time/threshold annotations, and charcoal for structure.
INK = "#24333D"
SLATE = "#567487"
BLUE = "#3E708F"
TEAL = "#4F9690"
WARM = "#B56E59"
GOLD = "#B98B50"
THRESHOLD = "#B34D49"
MID = "#A9B4B9"

TIME_CMAP = LinearSegmentedColormap.from_list(
    "independent_time", ["#91A7B2", "#5D8394", "#4F9690", "#B98B50", "#B56E59"]
)
MOISTURE_CMAP = LinearSegmentedColormap.from_list(
    "independent_moisture", ["#F1F4F4", "#C8DFDD", "#6FA9A1", "#315D76"]
)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read only the current solution tables used by the figures."""

    q1 = pd.read_csv(Q1_PATH)
    q2 = pd.read_csv(Q2_PATH)
    q3 = pd.read_csv(Q3_PATH)
    q4 = pd.read_csv(Q4_PATH)
    return q1, q2, q3, q4


def write_source_manifest() -> None:
    """Record exact answer-table hashes used by this independent figure run."""

    manifest: dict[str, object] = {}
    for path in (Q1_PATH, Q2_PATH, Q3_PATH, Q4_PATH):
        frame = pd.read_csv(path)
        manifest[str(path.relative_to(ROOT))] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
        }
    SOURCE_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def q3_event_hours(q3: pd.DataFrame) -> float:
    """Return the current problem-3 threshold event from the solution audit.

    The requested 60-s result table ends at the last regular sample before the
    event.  The solver's validated audit table records the sub-step event.  A
    fallback to the last regular sample keeps the plotting script usable if
    that optional audit file is absent, while retaining the fact that the
    plotted source table itself is never modified.
    """

    if Q3_SUMMARY_PATH.exists():
        summary = pd.read_csv(Q3_SUMMARY_PATH)
        values = summary["value"].astype(str).str.strip()
        match = summary.loc[
            (summary["task"] == 3)
            & (summary["parameter"] == "STABLE_START_S")
            & values.eq("9000"),
            "base_termination_time_h",
        ]
        if not match.empty and np.isfinite(float(match.iloc[0])):
            return float(match.iloc[0])
    return float(q3["time_s"].max() / 3600.0)


def style_axis(ax: mpl.axes.Axes, *, grid: bool = False) -> None:
    """Apply restrained journal axes styling."""

    ax.tick_params(axis="both", which="major", direction="out", length=3, width=0.7, labelsize=7)
    ax.tick_params(axis="both", which="minor", direction="out", length=2, width=0.5)
    ax.margins(x=0.02, y=0.04)
    if grid:
        ax.grid(axis="y", color="#DDE3E5", linewidth=0.45, zorder=0)
    else:
        ax.grid(False)


def panel_label(ax: mpl.axes.Axes, label: str) -> None:
    ax.text(
        -0.10,
        1.04,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )


def save_publication_figure(fig: mpl.figure.Figure, stem: str) -> None:
    """Write the four requested publication formats at the final figure size."""

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / stem
    fig.savefig(path.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def time_colour(value: float, low: float, high: float) -> tuple[float, float, float, float]:
    return TIME_CMAP(float(np.clip((value - low) / (high - low), 0.0, 1.0)))


def q1_profile(df: pd.DataFrame, time_s: float, field: str) -> tuple[np.ndarray, np.ndarray]:
    row = df.loc[np.isclose(df["time_s"], time_s)].sort_values("radius_cm")
    return row["radius_cm"].to_numpy(), row[field].to_numpy()


def make_figure_a(q1: pd.DataFrame) -> None:
    """Preheating: radial profiles plus the two measured contrasts."""

    selected_times = [100, 600, 1200, 1800]
    colours = [time_colour(t, selected_times[0], selected_times[-1]) for t in selected_times]
    fig = plt.figure(figsize=(7.2, 4.65))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.65, 1.0], height_ratios=[1.0, 1.0], wspace=0.34, hspace=0.38)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    for time_s, colour in zip(selected_times, colours):
        radius, moisture = q1_profile(q1, time_s, "moisture_kgkg")
        _, temperature = q1_profile(q1, time_s, "temperature_C")
        ax_a.plot(radius, moisture, color=colour, lw=1.7, solid_capstyle="round")
        ax_b.plot(radius, temperature, color=colour, lw=1.5, solid_capstyle="round")
        ax_a.text(2.04, moisture[-1], f"{time_s} s", color=colour, fontsize=7, va="center")
        ax_b.text(2.04, temperature[-1], f"{time_s} s", color=colour, fontsize=7, va="center")

    # The hero panel is the moisture field's radial readout.
    ax_a.scatter([0, 2], [q1_profile(q1, 1800, "moisture_kgkg")[1][0], q1_profile(q1, 1800, "moisture_kgkg")[1][-1]], s=13, color=WARM, zorder=4)
    ax_a.set_xlim(0, 2.34)
    ax_a.set_ylim(1.43, 2.62)
    ax_a.set_xlabel("距中心距离，r (cm)")
    ax_a.set_ylabel("含水率，C (kg kg$^{-1}$)")
    ax_a.set_title("表面优先失水", loc="left", fontsize=8.5, pad=6)
    ax_a.annotate(
        "1800 s：ΔC = 1.040",
        xy=(2.0, 1.5103),
        xytext=(1.02, 1.56),
        color=WARM,
        fontsize=7,
        arrowprops=dict(arrowstyle="-", lw=0.7, color=WARM),
    )

    ax_b.set_xlim(0, 2.34)
    ax_b.set_ylim(27.8, 37.8)
    ax_b.set_xlabel("距中心距离，r (cm)")
    ax_b.set_ylabel("温度，T (°C)")
    ax_b.set_title("热量渗透", loc="left", fontsize=8.5, pad=6)

    times_all = np.sort(q1["time_s"].unique())
    centre = q1.loc[np.isclose(q1["radius_cm"], 0.0)].sort_values("time_s")
    surface = q1.loc[np.isclose(q1["radius_cm"], 2.0)].sort_values("time_s")
    gap_t = surface["temperature_C"].to_numpy() - centre["temperature_C"].to_numpy()
    gap_c = centre["moisture_kgkg"].to_numpy() - surface["moisture_kgkg"].to_numpy()
    ax_c.plot(times_all / 60.0, gap_t / gap_t[-1], color=BLUE, lw=1.6, label="温度差异")
    ax_c.plot(times_all / 60.0, gap_c / gap_c[-1], color=WARM, lw=1.6, label="含水率差异")
    ax_c.axhline(1.0, color=MID, lw=0.7, ls=(0, (2, 2)))
    ax_c.text(0.98, 0.26, "ΔT / ΔT$_{1800}$", transform=ax_c.transAxes, ha="right", color=BLUE, fontsize=7)
    ax_c.text(0.98, 0.12, "ΔC / ΔC$_{1800}$", transform=ax_c.transAxes, ha="right", color=WARM, fontsize=7)
    ax_c.set_xlim(0, 30)
    ax_c.set_ylim(-0.04, 1.08)
    ax_c.set_xlabel("时间 (min)")
    ax_c.set_ylabel("径向差异 / 终态差异")
    ax_c.set_title("差异增长", loc="left", fontsize=8.5, pad=6)

    for ax, label in ((ax_a, "a"), (ax_b, "b"), (ax_c, "c")):
        style_axis(ax)
        panel_label(ax, label)
    fig.suptitle(
        "预热形成表面优先的温度与含水率梯度\n"
        "问题1：FVM–CN–Picard；dr=0.05 mm，dt=0.25 s",
        x=0.03,
        ha="left",
        y=0.995,
        fontsize=10,
        fontweight="semibold",
        color=INK,
    )
    fig.subplots_adjust(top=0.88, left=0.09, right=0.96, bottom=0.12)
    save_publication_figure(fig, "figure_a_preheating_gradient")


def gradient_path(ax: mpl.axes.Axes, x: np.ndarray, y: np.ndarray, times_h: np.ndarray, linestyle: str) -> None:
    points = np.column_stack((x, y)).reshape(-1, 1, 2)
    segments = np.concatenate((points[:-1], points[1:]), axis=1)
    collection = LineCollection(segments, cmap=TIME_CMAP, norm=Normalize(float(times_h.min()), float(times_h.max())))
    collection.set_array(times_h[:-1])
    collection.set_linewidth(1.8)
    collection.set_linestyle(linestyle)
    collection.set_capstyle("round")
    ax.add_collection(collection)


def make_figure_b(q2: pd.DataFrame) -> None:
    """Full-process coupled state trajectory and radial support profiles."""

    centre = q2.loc[np.isclose(q2["radius_cm"], 0.0)].sort_values("time_s")
    surface = q2.loc[np.isclose(q2["radius_cm"], 2.0)].sort_values("time_s")
    key_hours = np.array([0.0, 0.5, 1.0, 2.0, 3.0])
    key_seconds = (key_hours * 3600).astype(int)
    fig = plt.figure(figsize=(7.2, 4.85))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.15, 0.88], height_ratios=[1, 1], wspace=0.40, hspace=0.40)
    ax_a = fig.add_subplot(gs[:, :2])
    ax_b = fig.add_subplot(gs[0, 2])
    ax_c = fig.add_subplot(gs[1, 2])

    t_h = centre["time_h"].to_numpy()
    gradient_path(ax_a, centre["temperature_C"].to_numpy(), centre["moisture_kgkg"].to_numpy(), t_h, "-")
    gradient_path(ax_a, surface["temperature_C"].to_numpy(), surface["moisture_kgkg"].to_numpy(), t_h, (0, (3, 2)))
    for h, sec in zip(key_hours, key_seconds):
        c_row = centre.loc[centre["time_s"] == sec].iloc[0]
        s_row = surface.loc[surface["time_s"] == sec].iloc[0]
        colour = time_colour(h, 0.0, 3.0)
        ax_a.scatter(c_row["temperature_C"], c_row["moisture_kgkg"], s=17, marker="o", color=colour, edgecolor="white", linewidth=0.45, zorder=4)
        ax_a.scatter(s_row["temperature_C"], s_row["moisture_kgkg"], s=17, marker="s", color=colour, edgecolor="white", linewidth=0.45, zorder=4)
        if h in (0.5, 3.0):
            ax_a.text(c_row["temperature_C"] - 0.55, c_row["moisture_kgkg"] + 0.055, f"{h:g} h", color=colour, fontsize=7, ha="right")
    ax_a.text(0.98, 0.08, "中心", transform=ax_a.transAxes, ha="right", color=BLUE, fontsize=7)
    ax_a.text(0.98, 0.14, "表面", transform=ax_a.transAxes, ha="right", color=WARM, fontsize=7)
    ax_a.set_xlim(27.7, 51.4)
    ax_a.set_ylim(0.90, 2.64)
    ax_a.set_xlabel("温度，T (°C)")
    ax_a.set_ylabel("含水率，C (kg kg$^{-1}$)")
    ax_a.set_title("温度–含水率状态轨迹", loc="left", fontsize=8.5, pad=6)
    sm = mpl.cm.ScalarMappable(norm=Normalize(0.0, 3.0), cmap=TIME_CMAP)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_a, fraction=0.034, pad=0.025)
    cbar.set_label("时间 (h)", fontsize=7)
    cbar.ax.tick_params(labelsize=6, length=2)

    profile_hours = [0.5, 1.5, 3.0]
    profile_colours = [time_colour(h, 0.0, 3.0) for h in profile_hours]
    for h, colour in zip(profile_hours, profile_colours):
        sec = int(round(h * 3600))
        profile = q2.loc[q2["time_s"] == sec].sort_values("radius_cm")
        ax_b.plot(profile["radius_cm"], profile["temperature_C"], color=colour, lw=1.5)
        ax_c.plot(profile["radius_cm"], profile["moisture_kgkg"], color=colour, lw=1.5)
        ax_b.text(2.03, profile["temperature_C"].iloc[-1], f"{h:g} h", color=colour, fontsize=6.8, va="center")
        ax_c.text(2.03, profile["moisture_kgkg"].iloc[-1], f"{h:g} h", color=colour, fontsize=6.8, va="center")

    ax_b.set_xlim(0, 2.28)
    ax_b.set_ylim(31, 51.2)
    ax_b.set_xlabel("径向位置，r (cm)")
    ax_b.set_ylabel("T (°C)")
    ax_b.set_title("温度剖面", loc="left", fontsize=8.5, pad=6)
    ax_c.set_xlim(0, 2.28)
    ax_c.set_ylim(0.92, 2.62)
    ax_c.set_xlabel("径向位置，r (cm)")
    ax_c.set_ylabel("C (kg kg$^{-1}$)")
    ax_c.set_title("含水率剖面", loc="left", fontsize=8.5, pad=6)

    for ax, label in ((ax_a, "a"), (ax_b, "b"), (ax_c, "c")):
        style_axis(ax)
        panel_label(ax, label)
    fig.suptitle(
        "耦合升温与失水使中心和表面状态逐渐分离\n"
        "问题2：同步 Picard–CN；N=1600，dt=1 s",
        x=0.03,
        ha="left",
        y=0.995,
        fontsize=10,
        fontweight="semibold",
        color=INK,
    )
    fig.subplots_adjust(top=0.87, left=0.09, right=0.96, bottom=0.12)
    save_publication_figure(fig, "figure_b_coupled_state_trajectory")


def make_figure_c(q3: pd.DataFrame, q4: pd.DataFrame, q3_event_h: float) -> None:
    """Fixed-radius versus shrinking-radius threshold comparison."""

    q3_max = q3.groupby("time_s", sort=True)["moisture_kgkg"].max().reset_index()
    q3_h = q3_max["time_s"].to_numpy() / 3600.0
    q3_c = q3_max["moisture_kgkg"].to_numpy()
    q4_sample = q4.loc[q4["record_type"].isin(["sample_fixed", "sample_surface"])]
    q4_max = q4_sample.groupby("time_h", sort=True)["moisture_kgkg"].max().reset_index()
    q4_h = q4_max["time_h"].to_numpy()
    q4_c = q4_max["moisture_kgkg"].to_numpy()
    q4_event = q4.loc[q4["record_type"] == "drying_end_surface"].iloc[0]
    q4_event_h = float(q4_event["time_h"])

    fig = plt.figure(figsize=(7.2, 4.75))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.65, 0.8, 0.8], height_ratios=[1.0, 1.0], wspace=0.42, hspace=0.42)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1:])
    ax_c = fig.add_subplot(gs[1, 1:])

    q3_x = np.append(q3_h, q3_event_h)
    q3_y = np.append(q3_c, 0.15)
    q4_x = np.append(q4_h, q4_event_h)
    q4_y = np.append(q4_c, 0.15)
    ax_a.plot(q3_x, q3_y, color=SLATE, lw=1.8, label="固定半径")
    ax_a.plot(q4_x, q4_y, color=TEAL, lw=1.8, label="半径收缩")
    ax_a.axhline(0.15, color=THRESHOLD, lw=1.0, ls=(0, (3, 2)))
    ax_a.text(0.98, 0.18, "阈值  C = 0.15", transform=ax_a.transAxes, ha="right", color=THRESHOLD, fontsize=7)
    ax_a.scatter([q3_event_h, q4_event_h], [0.15, 0.15], color=[SLATE, TEAL], s=23, zorder=4, edgecolor="white", linewidth=0.5)
    ax_a.annotate(f"{q3_event_h:.2f} h", xy=(q3_event_h, 0.15), xytext=(q3_event_h - 2.6, 0.40), color=SLATE, fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.7, color=SLATE))
    ax_a.annotate(f"{q4_event_h:.2f} h", xy=(q4_event_h, 0.15), xytext=(q4_event_h + 1.1, 0.31), color=TEAL, fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.7, color=TEAL))
    ax_a.set_xlim(0, 60)
    ax_a.set_ylim(0.0, 2.68)
    ax_a.set_xlabel("时间 (h)")
    ax_a.set_ylabel("内部最大含水率，C$_{max}$ (kg kg$^{-1}$)")
    ax_a.set_title("阈值由中心含水率控制", loc="left", fontsize=8.5, pad=6)
    ax_a.text(0.97, 0.93, "固定半径", transform=ax_a.transAxes, ha="right", color=SLATE, fontsize=7)
    ax_a.text(0.97, 0.87, "半径收缩", transform=ax_a.transAxes, ha="right", color=TEAL, fontsize=7)

    labels = ["固定半径", "半径收缩"]
    duration = [q3_event_h, q4_event_h]
    bars = ax_b.barh(labels, duration, color=[SLATE, TEAL], height=0.42)
    ax_b.set_xlim(0, 64)
    ax_b.set_xlabel("达到 C$_{max}$ < 0.15 的时间 (h)")
    ax_b.set_title("干燥时间对比", loc="left", fontsize=8.5, pad=6)
    for bar, value in zip(bars, duration):
        ax_b.text(value + 0.8, bar.get_y() + bar.get_height() / 2, f"{value:.2f} h", va="center", fontsize=7, color=INK)
    speedup = q3_event_h - q4_event_h
    ax_b.text(0.98, 0.50, f"收缩使完成时间提前 {speedup:.2f} h", transform=ax_b.transAxes, ha="right", va="center", color=TEAL, fontsize=7, zorder=5)

    radius = q4_sample.groupby("time_h", sort=True)["radius_cm"].first().reset_index()
    ax_c.plot(radius["time_h"], radius["radius_cm"], color=GOLD, lw=1.8)
    ax_c.scatter([0, q4_event_h], [2.0, float(q4_event["radius_cm"])], color=GOLD, s=18, zorder=4, edgecolor="white", linewidth=0.45)
    ax_c.axhline(1.2, color=MID, lw=0.7, ls=(0, (2, 2)))
    ax_c.text(q4_event_h - 0.4, 1.235, "1.20 cm", ha="right", color=GOLD, fontsize=7)
    ax_c.set_xlim(0, 60)
    ax_c.set_ylim(1.12, 2.08)
    ax_c.set_xlabel("时间 (h)")
    ax_c.set_ylabel("半径 R(t) (cm)")
    ax_c.set_title("实测收缩", loc="left", fontsize=8.5, pad=6)

    for ax, label in ((ax_a, "a"), (ax_b, "b"), (ax_c, "c")):
        style_axis(ax)
        panel_label(ax, label)
    fig.suptitle("考虑收缩可使干燥阈值提前达到", x=0.03, ha="left", y=0.995, fontsize=10, fontweight="semibold", color=INK)
    fig.subplots_adjust(top=0.87, left=0.10, right=0.97, bottom=0.12)
    save_publication_figure(fig, "figure_c_fixed_vs_shrinking_threshold")


def state_on_xi(group: pd.DataFrame, xi_grid: np.ndarray, field: str) -> np.ndarray:
    """Interpolate supplied physical-radius samples onto material coordinate ξ."""

    radius_cm = float(group["radius_cm"].iloc[0])
    xi = group["r_cm"].to_numpy(dtype=float) / radius_cm
    values = group[field].to_numpy(dtype=float)
    order = np.argsort(xi)
    xi, values = xi[order], values[order]
    unique_xi, unique_indices = np.unique(xi, return_index=True)
    values = values[unique_indices]
    if unique_xi[0] > 0.0 or unique_xi[-1] < 1.0:
        raise ValueError("task4 sample rows do not span the material interval [0, 1]")
    return np.interp(xi_grid, unique_xi, values)


def q4_profile(df: pd.DataFrame, time_h: float, *, terminal: bool = False) -> pd.DataFrame:
    if terminal:
        rows = df.loc[df["record_type"].isin(["drying_end_fixed", "drying_end_surface"])].copy()
    else:
        rows = df.loc[
            df["record_type"].isin(["sample_fixed", "sample_surface"])
            & np.isclose(df["time_h"], time_h, atol=1.0e-5)
        ].copy()
    rows = rows.sort_values("r_cm").drop_duplicates("r_cm", keep="last")
    return rows


def make_figure_d(q4: pd.DataFrame) -> None:
    """Moving-boundary solution in material and physical coordinates."""

    sample = q4.loc[q4["record_type"].isin(["sample_fixed", "sample_surface"])].copy()
    xi_grid = np.linspace(0.0, 1.0, 121)
    sample_times_s: list[float] = []
    sample_radii: list[float] = []
    moisture_grid: list[np.ndarray] = []
    temperature_grid: list[np.ndarray] = []
    for time_s, group in sample.groupby("time_s", sort=True):
        sample_times_s.append(float(time_s))
        sample_radii.append(float(group["radius_cm"].iloc[0]))
        moisture_grid.append(state_on_xi(group, xi_grid, "moisture_kgkg"))
        temperature_grid.append(state_on_xi(group, xi_grid, "temperature_C"))
    times_h = np.asarray(sample_times_s) / 3600.0
    radii = np.asarray(sample_radii)
    moisture = np.vstack(moisture_grid)
    temperature = np.vstack(temperature_grid)

    fig = plt.figure(figsize=(7.2, 5.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.25, 0.95], height_ratios=[1.08, 0.92], wspace=0.38, hspace=0.43)
    ax_a = fig.add_subplot(gs[0, :2])
    ax_b = fig.add_subplot(gs[0, 2])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1:])

    mesh = ax_a.pcolormesh(times_h, xi_grid, moisture.T, shading="auto", cmap=MOISTURE_CMAP, norm=LogNorm(vmin=0.05, vmax=2.55))
    threshold_contour = ax_a.contour(times_h, xi_grid, moisture.T, levels=[0.15], colors=[THRESHOLD], linewidths=1.2)
    ax_a.clabel(threshold_contour, fmt={0.15: "C = 0.15"}, inline=True, fontsize=6.5, colors=[THRESHOLD], manual=[(34.0, 0.72)])
    ax_a.set_xlabel("时间 (h)")
    ax_a.set_ylabel("材料坐标，ξ = r / R(t)")
    ax_a.set_title("收缩体内的含水率场", loc="left", fontsize=8.5, pad=6)
    cbar = fig.colorbar(mesh, ax=ax_a, fraction=0.032, pad=0.025)
    cbar.set_label("C (kg kg$^{-1}$；对数刻度)", fontsize=7)
    # Keep logarithmic tick labels as ordinary decimals so the CJK font does
    # not need a mathtext Unicode-minus glyph for the exponent.
    cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    cbar.ax.tick_params(labelsize=6, length=2)
    ax_a.text(0.99, 0.04, "ξ = 1：移动表面", transform=ax_a.transAxes, ha="right", color=INK, fontsize=6.8)

    centre_T = temperature[:, 0]
    surface_T = temperature[:, -1]
    ax_b.plot(times_h, centre_T, color=BLUE, lw=1.6)
    ax_b.plot(times_h, surface_T, color=WARM, lw=1.6, ls=(0, (3, 2)))
    ax_b.text(0.97, 0.84, "中心", transform=ax_b.transAxes, ha="right", color=BLUE, fontsize=7)
    ax_b.text(0.97, 0.72, "表面", transform=ax_b.transAxes, ha="right", color=WARM, fontsize=7)
    ax_b.set_xlim(0, float(times_h[-1]))
    ax_b.set_ylim(27.5, 51.0)
    ax_b.set_xlabel("时间 (h)")
    ax_b.set_ylabel("T (°C)")
    ax_b.set_title("热响应", loc="left", fontsize=8.5, pad=6)

    ax_c.plot(times_h, radii, color=GOLD, lw=1.8)
    ax_c.scatter([times_h[0], times_h[-1]], [radii[0], radii[-1]], color=GOLD, s=17, zorder=4, edgecolor="white", linewidth=0.5)
    ax_c.set_xlim(0, float(times_h[-1]))
    ax_c.set_ylim(1.14, 2.06)
    ax_c.set_xlabel("时间 (h)")
    ax_c.set_ylabel("R(t) (cm)")
    ax_c.set_title("实际半径", loc="left", fontsize=8.5, pad=6)
    ax_c.text(0.98, 0.12, f"2.00 → {radii[-1]:.2f} cm", transform=ax_c.transAxes, ha="right", color=GOLD, fontsize=7)

    profile_hours = [6.0, 24.0, 42.0, 48.0]
    profile_colours = [time_colour(h, 0.0, 51.1) for h in profile_hours]
    profile_handles: list[mpl.lines.Line2D] = []
    for h, colour in zip(profile_hours, profile_colours):
        profile = q4_profile(q4, h)
        line, = ax_d.plot(profile["r_cm"], profile["moisture_kgkg"], color=colour, lw=1.45, label=f"{h:g} h")
        profile_handles.append(line)
    terminal = q4_profile(q4, 0.0, terminal=True)
    terminal_line, = ax_d.plot(terminal["r_cm"], terminal["moisture_kgkg"], color=THRESHOLD, lw=1.8, label="51.09 h（终点）")
    ax_d.axhline(0.15, color=THRESHOLD, lw=0.8, ls=(0, (3, 2)))
    ax_d.legend(handles=profile_handles + [terminal_line], loc="upper right", ncol=2, fontsize=6.2, handlelength=1.8, columnspacing=0.9, borderaxespad=0.2)
    ax_d.text(0.98, 0.08, "阈值 C = 0.15", transform=ax_d.transAxes, ha="right", color=THRESHOLD, fontsize=6.8)
    ax_d.set_xlim(0, 2.06)
    ax_d.set_ylim(0.0, 2.64)
    ax_d.set_xlabel("距中心的实际距离，r (cm)")
    ax_d.set_ylabel("C (kg kg$^{-1}$)")
    ax_d.set_title("映射回实际半径后的剖面", loc="left", fontsize=8.5, pad=6)

    for ax, label in ((ax_a, "a"), (ax_b, "b"), (ax_c, "c"), (ax_d, "d")):
        style_axis(ax)
        panel_label(ax, label)
    fig.suptitle("移动边界在材料坐标与实际空间中的表达", x=0.03, ha="left", y=0.995, fontsize=10, fontweight="semibold", color=INK)
    fig.subplots_adjust(top=0.87, left=0.09, right=0.96, bottom=0.12)
    save_publication_figure(fig, "figure_d_moving_boundary_coordinates")


def main() -> None:
    write_source_manifest()
    q1, q2, q3, q4 = load_data()
    event_h = q3_event_hours(q3)
    make_figure_a(q1)
    make_figure_b(q2)
    make_figure_c(q3, q4, event_h)
    make_figure_d(q4)
    print(f"Generated 4 independent figures in {OUT}")
    print(f"Problem 3 threshold event used for annotation: {event_h:.8f} h")


if __name__ == "__main__":
    main()
