from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/deliverables"
OUT = ROOT / "deliverables/figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["PingFang SC", "Arial Unicode MS", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 140,
    "savefig.dpi": 320,
    "savefig.bbox": "tight",
})

BLUE = "#2563EB"
ORANGE = "#EA580C"
TEAL = "#0F766E"
RED = "#DC2626"
PURPLE = "#7C3AED"
GRAY = "#64748B"


def load_problem(number):
    return json.loads((BUILD / f"problem{number}.json").read_text(encoding="utf-8"))


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.png")
    fig.savefig(OUT / f"{stem}.pdf")
    plt.close(fig)
    print(f"created {stem}", flush=True)


def style_axis(ax):
    ax.grid(True, color="#CBD5E1", linewidth=0.6, alpha=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def nearest_index(times, target):
    return int(np.argmin(np.abs(times - target)))


p1 = load_problem(1)
t1 = np.array(p1["time_s"]) / 60.0
r1 = np.array(p1["radius_cm"])
temp1 = np.array(p1["temperature_C"])
moist1 = np.array(p1["moisture_kgkg"])

for values, title, cbar, stem, cmap in [
    (temp1, "问题1：药材温度的时空分布", "温度 / °C", "fig01_q1_temperature_heatmap", "inferno"),
    (moist1, "问题1：药材含水率的时空分布", "干基含水率 / (kg/kg)", "fig02_q1_moisture_heatmap", "YlGnBu"),
]:
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    mesh = ax.pcolormesh(t1, r1, values.T, shading="auto", cmap=cmap, rasterized=True)
    fig.colorbar(mesh, ax=ax, label=cbar)
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("到药材中心的距离 / cm")
    ax.set_title(title)
    save(fig, stem)


p2 = load_problem(2)
t2 = np.array(p2["time_s"]) / 3600.0
temp2 = np.array(p2["temperature_C"])
moist2 = np.array(p2["moisture_kgkg"])
fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
axes[0].plot(t2, temp2[:, 0], color=BLUE, lw=2, label="中心")
axes[0].plot(t2, temp2[:, -1], color=ORANGE, lw=2, label="表面")
axes[0].set(xlabel="时间 / h", ylabel="温度 / °C", title="问题2：中心与表面温度")
axes[0].legend(frameon=False)
style_axis(axes[0])
axes[1].plot(t2, moist2[:, 0], color=BLUE, lw=2, label="中心")
axes[1].plot(t2, moist2[:, -1], color=ORANGE, lw=2, label="表面")
axes[1].set(xlabel="时间 / h", ylabel="干基含水率 / (kg/kg)", title="问题2：中心与表面含水率")
axes[1].legend(frameon=False)
style_axis(axes[1])
fig.tight_layout()
save(fig, "fig03_q2_center_surface")


p3 = load_problem(3)
t3 = np.array(p3["time_s"]) / 3600.0
r3 = np.array(p3["radius_cm"])
temp3 = np.array(p3["temperature_C"])
moist3 = np.array(p3["moisture_kgkg"])

fig, ax = plt.subplots(figsize=(7.2, 4.5))
ax.plot(t3, moist3[:, 0], color=BLUE, lw=2.2, label="全域最大值（中心）")
ax.plot(t3, moist3[:, -1], color=ORANGE, lw=1.8, label="表面")
ax.axhline(0.15, color=RED, ls="--", lw=1.5, label="达标阈值 0.15")
ax.scatter([p3["end_time_h"]], [0.15], color=RED, zorder=5)
ax.annotate(f"{p3['end_time_h']:.4f} h", (p3["end_time_h"], 0.15),
            xytext=(-64, 18), textcoords="offset points", color=RED,
            arrowprops={"arrowstyle": "->", "color": RED})
ax.set(xlabel="时间 / h", ylabel="干基含水率 / (kg/kg)", title="问题3：全域达标时刻")
ax.set_xlim(0, p3["end_time_h"] * 1.02)
ax.legend(frameon=False)
style_axis(ax)
save(fig, "fig04_q3_threshold")

fig, ax = plt.subplots(figsize=(7.2, 4.5))
colors = plt.cm.viridis(np.linspace(0.08, 0.92, 6))
targets = [6, 12, 24, 36, 48, p3["end_time_h"]]
for target, color in zip(targets, colors):
    profile = moist3[nearest_index(t3, target)]
    label = "结束" if target == p3["end_time_h"] else f"{target:g} h"
    ax.plot(r3, profile, lw=1.8, color=color, label=label)
ax.axhline(0.15, color=RED, ls="--", lw=1.2)
ax.set(xlabel="到药材中心的距离 / cm", ylabel="干基含水率 / (kg/kg)", title="问题3：6 h 后的径向含水率演化")
ax.legend(ncol=2, frameon=False)
style_axis(ax)
save(fig, "fig05_q3_radial_profiles")

fig, ax = plt.subplots(figsize=(7.2, 4.5))
mesh = ax.pcolormesh(t3, r3, moist3.T, shading="auto", cmap="YlGnBu", rasterized=True)
fig.colorbar(mesh, ax=ax, label="干基含水率 / (kg/kg)")
ax.set(xlabel="时间 / h", ylabel="到药材中心的距离 / cm", title="问题3：全过程含水率时空分布")
save(fig, "fig06_q3_moisture_heatmap")


p4 = load_problem(4)
t4 = np.array(p4["time_s"]) / 3600.0
moist4 = np.array(p4["moisture_kgkg"], dtype=object)
center4 = np.array([float(row[0]) for row in moist4])
surface4 = np.array([float(row[-1]) for row in moist4])
radius4 = np.array(p4["current_radius_cm"])
fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
axes[0].plot(t4, radius4, color=TEAL, lw=2.2)
axes[0].set(xlabel="时间 / h", ylabel="半径 / cm", title="问题4：药材半径变化")
style_axis(axes[0])
axes[1].plot(t4, center4, color=BLUE, lw=2, label="中心")
axes[1].plot(t4, surface4, color=ORANGE, lw=1.8, label="动态表面")
axes[1].axhline(0.15, color=RED, ls="--", lw=1.2, label="达标阈值")
axes[1].set(xlabel="时间 / h", ylabel="干基含水率 / (kg/kg)", title="问题4：收缩条件下含水率")
axes[1].legend(frameon=False)
style_axis(axes[1])
fig.tight_layout()
save(fig, "fig07_q4_shrinkage")


innovation = json.loads((ROOT / "results/innovation-analysis.json").read_text(encoding="utf-8"))
factor = innovation["factorial"]
labels = ["固定+P3", "收缩+P3", "固定+P4", "收缩+P4"]
keys = ["A_fixed_P3", "B_shrink_P3", "C_fixed_P4", "D_shrink_P4"]
times = [factor[k]["end_time_h"] for k in keys]
fig, ax = plt.subplots(figsize=(7.2, 4.5))
bars = ax.bar(labels, times, color=[BLUE, TEAL, ORANGE, PURPLE], width=0.62)
ax.bar_label(bars, labels=[f"{v:.2f}" for v in times], padding=3)
ax.set(ylabel="达标时间 / h", title="几何与物性的四组合对照")
ax.set_ylim(0, max(times) * 1.16)
style_axis(ax)
save(fig, "fig08_factorial_times")


effects = innovation["effects"]
effect_labels = ["收缩效应\n(P3)", "收缩效应\n(P4)", "物性效应\n(固定)", "物性效应\n(收缩)", "交互效应"]
effect_values = [effects["geometry_under_P3_h"], effects["geometry_under_P4_h"],
                 effects["property_under_fixed_h"], effects["property_under_shrink_h"],
                 effects["interaction_h"]]
fig, ax = plt.subplots(figsize=(8.0, 4.6))
bars = ax.bar(effect_labels, effect_values, color=[TEAL if v < 0 else ORANGE for v in effect_values], width=0.62)
ax.axhline(0, color="#334155", lw=0.9)
for bar, value in zip(bars, effect_values):
    ax.text(bar.get_x() + bar.get_width()/2, value + (2.2 if value >= 0 else -4.6), f"{value:+.2f}", ha="center")
ax.set(ylabel="达标时间变化 / h", title="几何、物性及交互效应")
style_axis(ax)
save(fig, "fig09_factorial_effects")


diagnostics = innovation["diagnostics"]
diag_keys = ["diag_full_N200", "diag_isothermal", "diag_constant", "diag_hm_x2", "diag_hm_x10_refined"]
diag_labels = ["完整模型", "等温", "常物性", "$h_m$×2", "$h_m$×10"]
diag_times = [diagnostics[k]["end_time_h"] for k in diag_keys]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
bars = ax.bar(diag_labels, diag_times, color=[BLUE, TEAL, GRAY, ORANGE, RED], width=0.62)
ax.bar_label(bars, labels=[f"{v:.2f}" for v in diag_times], padding=3)
ax.set(ylabel="达标时间 / h", title="烘干瓶颈诊断模型对照")
ax.set_ylim(0, max(diag_times) * 1.15)
style_axis(ax)
save(fig, "fig10_bottleneck_diagnostics")


environment = innovation["environment"]
env_keys = ["env_T_low", "env_T_high", "env_C_dry", "env_C_humid", "env_fast_combined", "env_slow_combined"]
env_labels = ["低温", "高温", "较干空气", "较湿空气", "高温+较干", "低温+较湿"]
baseline = environment["baseline_common_grid"]["end_time_h"]
env_delta_min = [(environment[k]["end_time_h"] - baseline) * 60 for k in env_keys]
fig, ax = plt.subplots(figsize=(8.0, 4.6))
bars = ax.bar(env_labels, env_delta_min, color=[ORANGE if v > 0 else TEAL for v in env_delta_min], width=0.62)
ax.axhline(0, color="#334155", lw=0.9)
for bar, value in zip(bars, env_delta_min):
    ax.text(bar.get_x() + bar.get_width()/2, value + (1.2 if value >= 0 else -2.5), f"{value:+.1f}", ha="center")
ax.set(ylabel="相对基准的时间变化 / min", title="长期环境延拓敏感性")
style_axis(ax)
save(fig, "fig11_environment_sensitivity")

print(f"created figures in {OUT}")
