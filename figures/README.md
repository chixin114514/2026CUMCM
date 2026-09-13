# 图件目录

`figures/` 按图件用途组织，正式图与实验性输出分开。

```text
figures/
├── flowcharts/
│   ├── problem_flows/       # 问题一至四流程图
│   ├── algorithm_flows/     # 算法步骤 1–7
│   └── overview/            # A题问题一至四可编辑总览图
├── publication/
│   ├── main/                # 正式主图 fig01–fig07
│   ├── analysis/            # 分析图 fig08–fig11
│   ├── tables/              # 正式结果 Excel
│   └── docs/                # 图表索引、复核报告、选图建议
├── exploratory/
│   └── independent/         # 独立可视化脚本、哈希和输出
└── archive/                 # 重复流程图和旧版独立可视化输出
```

## 常用入口

- 正式图表索引：[`publication/docs/README.md`](publication/docs/README.md)
- 正式主图：[`publication/main/`](publication/main/)
- 正式分析图：[`publication/analysis/`](publication/analysis/)
- 流程图：[`flowcharts/`](flowcharts/)
- 独立可视化脚本：[`exploratory/independent/plot_independent_figures.py`](exploratory/independent/plot_independent_figures.py)

重新生成独立可视化：

```bash
python figures/exploratory/independent/plot_independent_figures.py
```

该脚本只读取 `solution/task1/answer/` 至 `solution/task4/answer/` 的已验证结果，并将四张图写入同目录的 `outputs/`。

灵敏度专用图仍由 `solution/sensitivity/figures/plot_sensitivity.py` 管理，不与本目录的正式投稿图混用。`archive/` 中的文件仅作历史或重复副本保存，不作为正文引用入口。
