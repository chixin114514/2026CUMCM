# A题计算结果与图表索引

## 结果 Excel

| 文件 | 对应问题 | 工作表 | 数据范围 |
|---|---|---|---|
| [`result1.xlsx`](../tables/result1.xlsx) | 问题1 | `温度`、`水分浓度` | 1–1800 s；半径 0–2 cm，步长 0.1 cm |
| [`result2.xlsx`](../tables/result2.xlsx) | 问题2 | `温度`、`水分浓度` | 1–10800 s；半径 0–2 cm，步长 0.1 cm |
| [`result3.xlsx`](../tables/result3.xlsx) | 问题3 | `Sheet1` | 每 60 s 输出，并保留精确达标时刻 206898.8989 s（57.4719 h） |
| [`result4.xlsx`](../tables/result4.xlsx) | 问题4 | `Sheet1` | 每 60 s 输出，并保留精确达标时刻 183914.6757 s（51.0874 h） |

四份文件均沿用附件3的文件名、工作表名和表头结构。问题4中，药材收缩后位于当前表面之外的固定半径采样点留空，最后一列“药材表面”始终记录动态表面值。

## 主问题图表

| 编号 | 文件 | 表达内容 | 建议用途 |
|---|---|---|---|
| 图1 | [`fig01_q1_temperature_heatmap`](../main/fig01_q1_temperature_heatmap.pdf) | 问题1温度随时间和半径的分布 | 展示预热阶段热量由表面向中心传递 |
| 图2 | [`fig02_q1_moisture_heatmap`](../main/fig02_q1_moisture_heatmap.pdf) | 问题1含水率随时间和半径的分布 | 展示表面先失水、内部存在滞后 |
| 图3 | [`fig03_q2_center_surface`](../main/fig03_q2_center_surface.pdf) | 问题2中心与表面的温度、含水率曲线 | 展示双向耦合后的核心结果 |
| 图4 | [`fig04_q3_threshold`](../main/fig04_q3_threshold.pdf) | 问题3中心和表面含水率与阈值 | 明确全域达标时刻 57.4719 h |
| 图5 | [`fig05_q3_radial_profiles`](../main/fig05_q3_radial_profiles.pdf) | 问题3在多个时刻的径向含水率剖面 | 展示干燥前沿和空间不均匀性 |
| 图6 | [`fig06_q3_moisture_heatmap`](../main/fig06_q3_moisture_heatmap.pdf) | 问题3全过程含水率时空分布 | 展示全程演化规律 |
| 图7 | [`fig07_q4_shrinkage`](../main/fig07_q4_shrinkage.pdf) | 问题4半径及中心/动态表面含水率 | 展示移动边界与收缩效果 |

## 创新分析图表

| 编号 | 文件 | 表达内容 |
|---|---|---|
| 图8 | [`fig08_factorial_times`](../analysis/fig08_factorial_times.pdf) | 固定/收缩几何与两组物性的四组合达标时间 |
| 图9 | [`fig09_factorial_effects`](../analysis/fig09_factorial_effects.pdf) | 几何效应、物性效应及交互效应的定量分解 |
| 图10 | [`fig10_bottleneck_diagnostics`](../analysis/fig10_bottleneck_diagnostics.pdf) | 完整、等温、常物性及表面对流强化模型的瓶颈诊断 |
| 图11 | [`fig11_environment_sensitivity`](../analysis/fig11_environment_sensitivity.pdf) | 长时间环境延拓假设对达标时间的敏感性 |

主图同时提供 PNG、PDF、SVG 和 TIFF；分析图提供 PNG 和 PDF。PNG 适合直接预览或插入普通文档，PDF/SVG 适合排版和无损缩放，TIFF 用于需要栅格输入的投稿系统。

## 校验结果

- `result1.xlsx`：2 个工作表，每个 1801 行 × 22 列。
- `result2.xlsx`：2 个工作表，每个 10801 行 × 22 列。
- `result3.xlsx`：3450 行 × 22 列，末行中心含水率为 0.1500。
- `result4.xlsx`：3067 行 × 23 列，末行中心含水率为 0.1500，动态表面值为 0.0526。
- 已检查四份文件的首尾数据、工作表名称、冻结窗格和数值格式；未发现 `#REF!`、`#DIV/0!`、`#VALUE!`、`#NAME?` 或 `#N/A` 错误。

进一步的逐项校验见 [`复核报告.md`](复核报告.md)，正文与附录的选图建议见 [`核心图表使用建议.md`](核心图表使用建议.md)。
