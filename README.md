# 2026 CUMCM A 题：药材烘干数值建模

本项目针对 2026 年高教社杯全国大学生数学建模竞赛 A 题“药材的烘干问题”，建立圆柱形药材内部温度场与水分浓度场的数值模型，完成问题一至问题四的计算、结果导出、敏感度分析和论文图件整理。

题面与附件见 [`problem/`](problem/)，已生成的正式结果见 [`solution/`](solution/)，图件入口见 [`figures/README.md`](figures/README.md)。

## 计算结论概览

| 问题 | 计算范围与模型 | 正式结果 | 主要输出 |
|---|---|---|---|
| 问题一 | 预热平衡阶段，固定半径，0–1800 s | 温度和水分浓度的径向时空场 | `task1_result.csv`、关键点表、诊断日志 |
| 问题二 | 固定半径热质耦合，0–3 h | 3 h 内温度和水分浓度 | `result2.xlsx`、完整 CSV、表 3/表 4 |
| 问题三 | 固定半径长期烘干，阈值 `max(C) < 0.15 kg/kg` | **57.471940 h** | `result3.xlsx`、完整 CSV、诊断日志 |
| 问题四 | 考虑附件 2 半径变化的移动边界模型 | **51.087435 h**；终止时半径约 **1.2 cm** | `result4.xlsx`、表 6、完整 CSV、诊断日志 |

表中的数值对应当前 `solution/*/answer/` 下的结果文件；修改输入、离散参数或求解器后，应重新生成并复核全部结果。

## 模型与数值方法

### 物理模型

- 药材初始为长 `25 cm`、半径 `2 cm` 的圆柱，初始温度 `28 °C`，初始干基含水率 `2.55 kg/kg`。
- 利用轴对称一维径向模型描述内部状态。问题一至问题三采用固定半径；问题四在材料坐标 `ξ = r/R(t)` 下处理半径收缩。
- 内部传热采用 Fourier 导热，水分迁移采用 Fick 型有效扩散；表面分别施加 Robin 换热和传质边界，中心采用零通量对称边界。
- 烘房温度和水分浓度由附件 1 提供并进行时间插值；进入长期稳定阶段后使用稳定段均值。问题四的实时半径 `R(t)` 由附件 2 分段线性插值。

### 离散与求解

1. 守恒型径向有限体积法，中心和表面使用半控制体积。
2. 时间方向采用 Crank–Nicolson 格式。
3. 相邻控制体界面物性使用严格正值调和平均。
4. 非线性物性在时间中点通过同步 Picard 迭代冻结并更新。
5. 每个场形成三对角线性系统，并检查线性残差、守恒残差和物理范围。
6. 问题三、问题四逐时间层检查全空间水分阈值；跨越阈值后从前一状态局部二分重积分定位终止时刻，而不是直接对终止量线性插值。

物性公式按题面附录选择：问题一使用附录 2，问题二和问题三使用附录 3，问题四使用附录 4。

## 快速开始

请在仓库根目录执行命令。项目没有单独的依赖锁定文件，可使用 Python 3.10 及以上版本创建环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy pandas scipy openpyxl matplotlib
```

按问题顺序运行正式求解器：

```bash
# 问题一：生成 0–1800 s 的完整场、关键点表和诊断日志
python solution/task1/script/solve_task1.py

# 问题二：生成 result2.xlsx、完整 CSV、表 3/表 4
python solution/task2/script/solve_task2.py --skip-sensitivity

# 问题三：读取问题二完整 CSV，继续积分并定位全域达标时刻
python solution/task3/script/solve_task3.py --skip-sensitivity

# 问题四：读取附件 1 和附件 2，求解材料坐标移动边界模型
python solution/task4/script/solve_task4.py --skip-sensitivity
```

默认命令会写入相应 `solution/taskN/answer/` 目录，并可能覆盖已有答案文件。问题三要求先存在问题二的 `task2_all_results.csv`；若只做算法检查而不写文件，可使用各脚本提供的 `--no-write` 选项。

完整重算还需要保留 `problem/附件/附件3/` 下的 `result1.xlsx`–`result4.xlsx` 模板；若当前工作区存在未提交的模板删除或替换，请先恢复与题面匹配的模板，再运行会写入答案的命令。

## 敏感度分析与图件

### 敏感度分析

统一入口为 [`solution/sensitivity/run_sensitivity.py`](solution/sensitivity/run_sensitivity.py)：

```bash
python solution/sensitivity/run_sensitivity.py --tasks 1 2 3 4 --jobs 4
```

结果写入 `solution/sensitivity/results/`，汇总表为 [`sensitivity_summary.csv`](solution/sensitivity/results/sensitivity_summary.csv)，来源和参数哈希记录在 `sensitivity_provenance.json`。正式敏感度主图由以下脚本生成：

```bash
python solution/sensitivity/figures/plot_sensitivity.py
```

敏感度脚本会重新审计逐点结果文件；问题一、问题二的零基准误差使用“归一化误差增益”，问题三、问题四分别报告烘干时间相对变化和表格水分相对偏差。

### 独立可视化

基于当前四个问题的已验证 CSV 重新生成四张独立复核图：

```bash
python figures/exploratory/independent/plot_independent_figures.py
```

输出位于 `figures/exploratory/independent/outputs/`，脚本同时更新 `source_hashes.json`，记录所读取答案表的 SHA-256、行数和列名。正式投稿图、分析图、流程图及图件用途说明集中在 [`figures/publication/docs/README.md`](figures/publication/docs/README.md)。

## 目录结构

```text
.
├── problem/
│   ├── A题.md                         # 题面 Markdown
│   └── 附件/                          # 附件 1、附件 2 和结果模板
├── solution/
│   ├── task1/{script,answer}/          # 问题一求解器与结果
│   ├── task2/{script,answer}/          # 问题二求解器与结果
│   ├── task3/{script,answer}/          # 问题三求解器与结果
│   ├── task4/{script,answer}/          # 问题四求解器与结果
│   └── sensitivity/                    # 敏感度计算、汇总和图件
├── figures/
│   ├── flowcharts/                     # 问题流程图和算法流程图
│   ├── publication/                    # 正式主图、分析图、表格和图件文档
│   └── exploratory/independent/        # 独立可视化脚本与输出
```

## 结果文件索引

### 问题一

- [完整温度/水分 CSV](solution/task1/answer/task1_result.csv)：1801 个时间层 × 21 个径向位置。
- [关键点结果](solution/task1/answer/task1_key_results.csv)：题目要求的 7 个时间点和 5 个半径位置。
- [诊断 CSV](solution/task1/answer/task1_diagnostics.csv) / [诊断 JSON](solution/task1/answer/task1_diagnostics.json)：Picard、线性残差和守恒检查。
- [求解器](solution/task1/script/solve_task1.py)。

### 问题二

- [Excel 正式结果](solution/task2/answer/result2.xlsx)：工作表“温度”和“水分浓度”，每 1 s、每 0.1 cm 输出。
- [完整 CSV](solution/task2/answer/task2_all_results.csv)。
- [表 3 温度](solution/task2/answer/table3_temperature.csv) / [表 4 水分浓度](solution/task2/answer/table4_moisture.csv)。
- [诊断 CSV](solution/task2/answer/task2_diagnostics.csv) / [诊断 JSON](solution/task2/answer/task2_diagnostics.json)。
- [求解器](solution/task2/script/solve_task2.py)。

### 问题三

- [Excel 正式结果](solution/task3/answer/result3.xlsx)：每 60 s 输出，并在工作表末尾保留精确达标时刻。
- [完整水分 CSV](solution/task3/answer/task3_all_results.csv)。
- [诊断 CSV](solution/task3/answer/task3_diagnostics.csv) / [诊断 JSON](solution/task3/answer/task3_diagnostics.json)：包含阈值区间、二分定位和问题二重叠时段一致性检查。
- [求解器](solution/task3/script/solve_task3.py)。

### 问题四

- [Excel 正式结果](solution/task4/answer/result4.xlsx)：按真实物理半径映射输出，收缩后位于当前表面之外的位置留空，动态表面单独记录。
- [表 6 论文表格](solution/task4/answer/task4_paper_table.xlsx)。
- [完整 CSV](solution/task4/answer/task4_all_answers.csv)：包含固定径向采样点、动态表面和终止事件记录。
- [诊断 CSV](solution/task4/answer/task4_diagnostics.csv) / [诊断 JSON](solution/task4/answer/task4_diagnostics.json)。
- [求解器](solution/task4/script/solve_task4.py)。

## 验证与复现约定

- 所有内部长度统一使用 m，结果文件中的径向位置使用 cm；温度使用 °C，水分浓度使用 kg/kg。
- 输出结果保留四位小数；诊断文件保留更高精度，用于残差、守恒和事件定位复核。
- 求解器会检查输入列、时间覆盖范围、网格可整除性、数组形状、有限性、非负水分、Picard 收敛和三对角系统残差。
- 运行敏感度分析或修改求解器后，应同时检查 `sensitivity_summary.csv`、各问题 `taskN_diagnostics.*` 以及图件脚本生成的来源哈希，避免混用不同参数或不同版本的结果。
- `figures/publication/docs/README.md` 提供正式图表、结果 Excel 的工作表结构与输出尺寸复核；[`problem/A题.md`](problem/A题.md) 是唯一题面入口。

## 备注

本仓库的脚本、数值结果和图件面向竞赛建模复核与论文整理使用。若仅需要阅读结论，优先查看本 README 的“计算结论概览”和 `figures/publication/docs/README.md`；若需要重算，请从题面附件重新运行对应求解器，并保留同一批输入、源码和诊断文件。
