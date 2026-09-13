# Figures 目录整理设计

## 目标

在不改变数值结果内容的前提下，整理当前仓库的 `figures/` 目录：按用途区分流程图、正式交付图、探索性图件和归档副本；统一流程图文件名；同步修正文档与脚本中的路径；保留所有有来源价值的旧文件。

## 已确认范围

- 允许移动和重命名 `figures/` 内文件。
- 允许同步修改引用这些文件的 Markdown、Python 和 shell 文件。
- 不搬动 `solution/sensitivity/figures/`，因为它是灵敏度脚本的直接输出目录，属于独立的数值复现边界。
- 不修改 `solution/task*/` 的求解器、答案表和诊断内容。
- 不删除重复或旧版图件；无法作为当前主入口的副本移入归档目录。
- 清理本次整理涉及的 `.DS_Store`，不把系统元数据保留在正式目录中。

## 目标结构

```text
figures/
├── README.md
├── flowcharts/
│   ├── problem_flows/
│   ├── algorithm_flows/
│   └── overview/
├── publication/
│   ├── main/
│   ├── analysis/
│   ├── tables/
│   └── docs/
├── exploratory/
│   └── independent/
│       ├── plot_independent_figures.py
│       ├── source_hashes.json
│       └── outputs/
└── archive/
    └── duplicated_flowcharts/
```

同一张正式图的多个格式继续并列放在同一目录，不按扩展名拆分。正式图文件名 `fig01_…` 至 `fig11_…` 保持不变，以避免破坏既有图表索引和论文引用。

## 文件映射

### 流程图

| 当前路径 | 目标路径 | 处理方式 |
|---|---|---|
| `figures/task1_问题一流程图.svg` | `figures/flowcharts/problem_flows/problem1_flowchart.svg` | 规范化命名 |
| `figures/task2_问题二流程图.svg` | `figures/flowcharts/problem_flows/problem2_flowchart.svg` | 规范化命名 |
| `figures/task3_问题三流程图.svg` | `figures/flowcharts/problem_flows/problem3_flowchart.svg` | 规范化命名 |
| `figures/task4_问题四流程图.svg` | `figures/flowcharts/problem_flows/problem4_flowchart.svg` | 规范化命名 |
| `figures/**1_边界插值_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm01_boundary_interpolation.svg` | 去除特殊前缀并改为稳定英文文件名 |
| `figures/**2_温度和水分方程_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm02_temperature_moisture_equations.svg` | 同上 |
| `figures/3_FVM_CN_Picard_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm03_fvm_cn_picard.svg` | 同上 |
| `figures/**4_热湿双向耦合_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm04_heat_moisture_coupling.svg` | 同上 |
| `figures/*5_移动边界热湿模型_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm05_moving_boundary_model.svg` | 同上 |
| `figures/**6_计算水分场_算法流程 .svg` | `figures/flowcharts/algorithm_flows/algorithm06_moisture_field.svg` | 去除文件名尾部空格 |
| `figures/7_二分定位_算法流程.svg` | `figures/flowcharts/algorithm_flows/algorithm07_bisection_end_time.svg` | 同上 |
| `figures/A题_问题一至问题四_可编辑文字版.svg` | `figures/flowcharts/overview/problem1_to_problem4_editable.svg` | 归入总览 |

当前 `figures/问题流程图&算法流程图2/` 中与上述文件同名的副本或历史版本全部移入 `figures/archive/duplicated_flowcharts/`，并以 `legacy_` 前缀保存，避免正式入口出现重复文件；其中算法 4 的两个版本内容不同，均保留并以历史版本归档。

### 正式交付图和表格

- `figures/图/deliverables/figures/fig01_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig02_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig03_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig04_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig05_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig06_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig07_*.{png,pdf,svg,tiff}` → `figures/publication/main/`
- `figures/图/deliverables/figures/fig08_*.{png,pdf}` → `figures/publication/analysis/`
- `figures/图/deliverables/figures/fig09_*.{png,pdf}` → `figures/publication/analysis/`
- `figures/图/deliverables/figures/fig10_*.{png,pdf}` → `figures/publication/analysis/`
- `figures/图/deliverables/figures/fig11_*.{png,pdf}` → `figures/publication/analysis/`
- `figures/图/deliverables/result1.xlsx` … `result4.xlsx` → `figures/publication/tables/`
- `figures/图/deliverables/README.md`、`复核报告.md`、`核心图表使用建议.md` → `figures/publication/docs/`

`figures/publication/docs/README.md` 中的图路径改为相对于 `figures/publication/` 的新路径，并补充入口说明。

### 独立可视化

整体移动 `figures/independent_visualization/` → `figures/exploratory/independent/`，保持脚本、`source_hashes.json` 和 `outputs/` 的相对关系不变。脚本中的 `OUT = ... / "outputs"` 因此无需改变，只需同步仓库入口 README 的路径。

## 根目录说明

新增 `figures/README.md` 作为唯一图件入口，说明：

1. 正式投稿图在 `publication/main/` 和 `publication/analysis/`。
2. 问题与算法流程图在 `flowcharts/`。
3. 独立可视化在 `exploratory/independent/`，其输出由同目录脚本生成。
4. `archive/` 内容不作为正文或正式交付入口。
5. 灵敏度专用图仍在 `solution/sensitivity/figures/`，不能与正式投稿图混用。

## 路径与内容验证

整理完成后执行以下检查：

1. `find figures -name '.DS_Store' -o -path '*/问题流程图&算法流程图2*' -o -name '图'` 不返回正式目录中的残留入口。
2. 用 `shasum -a 256` 对移动前后的同名图件比对，确认内容未改变；对重复副本确认哈希一致，对算法 4 的历史版本记录哈希差异并保留两份文件。
3. `rg -n 'figures/图|figures/deliverables|figures/independent_visualization|问题流程图&算法流程图2' --glob '!*.md' --glob '!*.json'` 不返回失效代码路径；Markdown 中的旧路径全部更新或明确标为历史路径。
4. 执行 `python figures/exploratory/independent/plot_independent_figures.py`，确认四张独立可视化仍写入 `figures/exploratory/independent/outputs/`。
5. 对所有新增或修改的 Markdown 执行链接路径检查，确认 README 中的主图、表格和复核文档均可读。

## 不在本次范围内

- 不重算任何问题一至四的数值结果。
- 不修改灵敏度分析的输出格式、指标定义或绘图脚本逻辑。
- 不将 `solution/task1-add/figures/` 合并到正式投稿图目录；它属于问题一附加实验的独立产物。
- 不清理 `solution/` 中已有的实验日志、诊断文件或压缩包。
