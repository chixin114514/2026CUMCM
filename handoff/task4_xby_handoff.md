# A 题问题四技术交接文档

> 版本：2026-09-11。本文说明当前已提交的 `solution/task4/script/solve_task4.py` 及其三个答案文件所对应的模型、假设、离散方法和验收结果。本文不是代码副本；如果并发或旧交接文档与当前脚本冲突，以当前已提交脚本和本文为准。

## 1. 任务定义与最终结论

问题四在问题三的热湿耦合烘干模型上加入药材半径收缩。药材内部仍采用轴对称长圆柱的一维径向模型，烘干结束条件为整个当前药材区域满足

$$
\max_{0\le r\le R(t)} C(r,t)<0.15\ \mathrm{kg/kg}.
$$

当前加密计算结果为：

| 量 | 数值 |
|---|---:|
| 烘干结束时刻 | $188535.109375\ \mathrm{s}=52.3708637153\ \mathrm{h}$ |
| 结束时药材半径 | $R=1.2000\ \mathrm{cm}$ |
| 结束时 $C_{\max}$ | $0.149999999779\ \mathrm{kg/kg}$ |
| $C_{\max}$ 位置 | $\xi=0$，即中心 $r=0\ \mathrm{cm}$ |
| 结束前括号下端 | $188535.1083984375\ \mathrm{s}$ |
| 结束前 $C_{\max}$ | $0.150000000284\ \mathrm{kg/kg}$ |

因此阈值是在中心处首次严格跨过的；表格按四位小数显示为 `0.1500`，但未舍入值为 `0.149999999779<0.15`，严格满足题目要求。结束前的未舍入值仍大于阈值，事件定位不是把某个 60 s 输出点机械当作结束时刻。

问题三当前结果为 `57.0875 h`，问题四缩短 `4.7166363 h`，相对变化约 `8.2621%`。这个差异来自附录 4 物性、给定半径收缩以及移动坐标项的共同作用，不预设问题四必须快或慢。

## 2. 模型思路与继承关系

### 2.1 继承的基线

问题四保持问题二/问题三已经确定的环境、初值和边界传递参数，只做题目明确要求的三类改变：半径变为 $R(t)$、物性改为附录 4、计算域改为移动边界并按问题四格式输出。

- 几何：长为 25 cm 的圆柱，仅求轴对称径向场；长度方向按单位长度处理，不求轴向梯度。
- 初值：$R(0)=2\ \mathrm{cm}$，$T(r,0)=28\ ^\circ\mathrm{C}$，$C(r,0)=2.55\ \mathrm{kg/kg}$。
- 表面对流换热系数：$h=25\ \mathrm{W/(m^2\,K)}$。
- 表面对流传质系数：$h_m=8\times10^{-7}\ \mathrm{m/s}$。
- 烘房边界：附件 1 在 $0\le t\le14400\ \mathrm{s}$ 内按时间分段线性插值；$14400\ \mathrm{s}$ 以后保持附件 1 最后一个观测值，即 $T_\infty=50.165\ ^\circ\mathrm{C}$、$C_\infty=0.04986\ \mathrm{kg/kg}$。
- 时间积分：后向欧拉；非线性物性通过每个时间步内的 Picard 迭代更新。
- 空间离散：守恒型径向有限体积法，界面物性采用算术平均。

### 2.2 问题四的新增内容

附件 2 给出的半径是可靠输入，程序读取其 145 个时间点，先将 cm 转为 m，再使用分段线性插值构造 $R(t)$。问题四不引入轴向收缩，也不把固定半径网格上的 `R=2 cm` 简单替换为时间函数；所有未知量先映射到固定的无量纲坐标 $0\le\xi\le1$，再求解变换后的方程。

## 3. 模型假设与边界条件

本模型的适用假设如下。

1. 药材保持均匀、各向同性的长圆柱形，温度和水分浓度只随半径和时间变化；端面、轴向传热传质和轴向收缩忽略。
2. 药材长度 25 cm 足够长，端面效应相对径向效应可忽略；方程按单位轴向长度建立。
3. 半径变化完全由附件 2 给定的 $R(t)$ 描述，且仅发生径向收缩；不根据水分场反推半径，也不额外加入轴向变形、孔隙率模型或应力模型。
4. $\rho,c_p,k,D$ 仅按附录 4 的局部经验公式由 $C,T$ 决定；不额外加入潜热、内部热源、化学反应、辐射或相变项。表面蒸发的影响通过题设对流传质边界表示，未把蒸发潜热另加到热方程。
5. 烘房温度和水分浓度是外部已知边界，附件 1 的水分浓度直接作为表面传质边界中的环境浓度；表面对流系数 $h,h_m$ 在整个计算期间保持问题二/三的值。
6. $C$ 是干基水分浓度，单位 kg/kg；几何收缩只通过坐标移动项和半径缩放影响场方程，不另加一个未由题目给出的浓度稀释/源项。
7. 附件 2 的最后时刻为 259200 s，计算不超出该覆盖范围，不对半径作无说明外推。

边界条件为中心轴对称和移动表面对流：

$$
\left.\frac{\partial T}{\partial r}\right|_{r=0}=0,
\qquad
\left.\frac{\partial C}{\partial r}\right|_{r=0}=0,
$$

$$
-k\frac{\partial T}{\partial r}\bigg|_{r=R(t)}
=h\,[T(R(t),t)-T_\infty(t)],
$$

$$
-D\frac{\partial C}{\partial r}\bigg|_{r=R(t)}
=h_m\,[C(R(t),t)-C_\infty(t)].
$$

这里的表面始终是实际的 $r=R(t)$，不是固定的 $r=2\ \mathrm{cm}$。

## 4. 移动边界坐标变换

### 4.1 物理域和固定域

物理计算域为

$$
0\le r\le R(t).
$$

令

$$
\xi=\frac r{R(t)},\qquad 0\le\xi\le1,
$$

并定义固定域上的场

$$
\widetilde T(\xi,t)=T(R(t)\xi,t),\qquad
\widetilde C(\xi,t)=C(R(t)\xi,t).
$$

这样 $\xi=0$ 永远是中心，$\xi=1$ 永远是当前移动表面。

### 4.2 链式求导

固定物理位置 $r$ 时，$\xi=r/R(t)$，所以

$$
\left.\frac{\partial \xi}{\partial t}\right|_r
=-\frac{\dot R}{R}\xi.
$$

因此

$$
\left.\frac{\partial T}{\partial t}\right|_r
=\frac{\partial\widetilde T}{\partial t}
-\frac{\dot R}{R}\xi\frac{\partial\widetilde T}{\partial\xi},
$$

$$
\left.\frac{\partial C}{\partial t}\right|_r
=\frac{\partial\widetilde C}{\partial t}
-\frac{\dot R}{R}\xi\frac{\partial\widetilde C}{\partial\xi}.
$$

定义

$$
b(t)=-\frac{\dot R(t)}{R(t)}.
$$

附件 2 中半径不增，因此 $\dot R\le0$、$b\ge0$。此外

$$
\frac{\partial}{\partial r}=\frac1R\frac{\partial}{\partial\xi},
\qquad
\frac1r\frac{\partial}{\partial r}
\left(rq\frac{\partial u}{\partial r}\right)
=\frac1{R^2\xi}\frac{\partial}{\partial\xi}
\left(\xi q\frac{\partial\widetilde u}{\partial\xi}\right),
$$

其中 $q=k,u=T$ 或 $q=D,u=C$。

### 4.3 变换后的热湿方程

原固定物理域方程为

$$
\rho(C)c_p(C)\frac{\partial T}{\partial t}
=\frac1r\frac{\partial}{\partial r}
\left(rk(C)\frac{\partial T}{\partial r}\right),
$$

$$
\frac{\partial C}{\partial t}
=\frac1r\frac{\partial}{\partial r}
\left(rD(T,C)\frac{\partial C}{\partial r}\right).
$$

代入上面的链式关系，得到固定 $\xi$ 域上的真正移动边界方程：

$$
\rho(\widetilde C)c_p(\widetilde C)
\left(
\frac{\partial\widetilde T}{\partial t}
 + b\xi\frac{\partial\widetilde T}{\partial\xi}
\right)
=\frac1{R(t)^2\xi}\frac{\partial}{\partial\xi}
\left(
\xi k(\widetilde C)\frac{\partial\widetilde T}{\partial\xi}
\right),
$$

$$
\frac{\partial\widetilde C}{\partial t}
 + b\xi\frac{\partial\widetilde C}{\partial\xi}
=\frac1{R(t)^2\xi}\frac{\partial}{\partial\xi}
\left(
\xi D(\widetilde T,\widetilde C)
\frac{\partial\widetilde C}{\partial\xi}
\right).
$$

变换后的边界条件为

$$
\widetilde T_\xi(0,t)=0,\qquad \widetilde C_\xi(0,t)=0,
$$

$$
-\frac{k}{R(t)}\widetilde T_\xi(1,t)
=h[\widetilde T(1,t)-T_\infty(t)],
$$

$$
-\frac{D}{R(t)}\widetilde C_\xi(1,t)
=h_m[\widetilde C(1,t)-C_\infty(t)].
$$

如果只在固定的 $r$ 网格中把 `R=2 cm` 换成随时间变化的数字，网格节点将不能代表同一物质位置，且会遗漏 $b\xi u_\xi$ 移动坐标项、$R^{-2}$ 扩散缩放和真实表面 Robin 条件；收缩后表面外的点还可能被错误外推。因此该做法不等价于问题四的移动边界模型。

### 4.4 半径插值和 $\dot R$

附件 2 的半径先由 cm 转成 m，再使用分段线性函数 $R(t)$。内部时间步 $[t_n,t_{n+1}]$ 使用

$$
R_n=R(t_n),\qquad R_{n+1}=R(t_{n+1}),qquad
\dot R_n^{\mathrm{step}}=\frac{R_{n+1}-R_n}{\Delta t},
$$

并令组装该步方程时的半径为 $R_{n+1}$，移动系数为

$$
b_n=-\frac{\dot R_n^{\mathrm{step}}}{R_{n+1}}.
$$

这与分段线性半径和当前时间步完全匹配，不引入高阶拟合或额外经验参数。

## 5. 附录 4 物性与热湿耦合

问题四使用

$$
\rho=760+90C,
$$

$$
c_p=1850+2150\frac{C}{C+1},
$$

$$
k=0.12+0.20\frac{C}{C+1},
$$

$$
D=4.2\times10^{-4}
\exp\left(-\frac{0.30}{C}\right)
\exp\left(-\frac{3850}{T_K}\right).
$$

其中 $\rho$ 的单位为 kg/m³，$c_p$ 为 J/(kg·K)，$k$ 为 W/(m·K)，$D$ 为 m²/s，$C$ 为 kg/kg。程序中输出温度以摄氏度表示，但进入扩散系数指数前明确转换为

$$
T_K=T_{^\circ\mathrm C}+273.15.
$$

实际 `_picard_step` 的第 $m$ 轮使用同一个猜测状态 $(T^{(m)},C^{(m)})$ 计算并冻结 $\rho(C^{(m)}),c_p(C^{(m)}),k(C^{(m)}),D(T^{(m)},C^{(m)})$。在这组相同的冻结物性下，分别组装并求解温度和水分两个线性三对角系统，得到 $(T^{(m+1)},C^{(m+1)})$；温度新解不会在同一轮立即进入 $D$ 的计算。然后同时用新旧两场的最大差检查收敛，未收敛才将两者一起更新为下一轮猜测，直到

$$
\|\Delta T\|_\infty\le10^{-8}\ ^\circ\mathrm C,
\qquad
\|\Delta C\|_\infty\le10^{-10}\ \mathrm{kg/kg},
$$

或达到程序允许的最大迭代次数。最终运行中最大 Picard 迭代次数为 4。

## 6. 数值离散和终止事件

### 6.1 固定域有限体积离散

固定域取 $N=320$ 个区间、321 个节点，

$$
\Delta\xi=\frac1{320}.
$$

时间步为 $\Delta t=0.5\ \mathrm{s}$，答案采样间隔为 60 s。方程乘以 $\xi$ 后在控制体上积分，径向测度取

$$
m_0=\frac12\xi_{1/2}^2,
\quad
m_j=\frac12(\xi_{j+1/2}^2-\xi_{j-1/2}^2),
\quad
m_N=\frac12(1-\xi_{N-1/2}^2).
$$

因此控制体完整覆盖 $[0,1]$ 的径向积分测度。任一扩散物性 $q$ 在面上的导通系数取

$$
g_{j+1/2}
=\frac{q_{j+1/2}\xi_{j+1/2}}
{R_{n+1}^2\Delta\xi},
\qquad
q_{j+1/2}=\frac{q_j+q_{j+1}}2.
$$

这里显式保留了移动域带来的 $1/R^2$ 缩放，$q=k$ 时用于热方程，$q=D$ 时用于水分方程；界面算术平均与问题二/三基线一致。

### 6.2 移动项和边界离散

后向欧拉中，$b\xi u_\xi$ 与扩散项一起隐式求解。因为收缩时 $b\ge0$，采用一阶后向迎风

$$
u_\xi(\xi_j)\approx\frac{u_j-u_{j-1}}{\Delta\xi}.
$$

中心 $\xi=0$ 的移动项因 $\xi=0$ 自然为零，左侧扩散通量按轴对称条件取零。表面 Robin 条件在归一化控制体中分别产生

$$
\frac{h}{R_{n+1}}(T_s-T_\infty),
\qquad
\frac{h_m}{R_{n+1}}(C_s-C_\infty),
$$

所以矩阵边界导通项是 $h/R$ 和 $h_m/R$，而不是未变换的 `h` 或 `hm`；这是物理表面条件经过 $\partial_r=R^{-1}\partial_\xi$ 和径向控制体归一化后的量纲形式。

### 6.3 全域阈值和事件二分

每个内部时间步都计算

$$
C_{\max}(t_n)=\max_{0\le j\le N}C_j(t_n),
$$

不把中心或表面预先硬编码为最后干燥位置。第一次出现

$$
C_{\max}(t_n)\ge0.15,
\qquad
C_{\max}(t_{n+1})<0.15
$$

时，固定跨阈值前的 $t_n$ 状态作为同一个 base state，对候选中点时间重新从该 base state 积分到候选时刻；不把前一次候选状态错误地作为下一次候选的起点。按二分更新上下端，直到时间括号宽度不超过 $10^{-3}\ \mathrm{s}$，取严格低于阈值的上端作为结束时刻。

## 7. 输出文件语义

### 7.1 `result4.xlsx`

文件使用官方模板的 `Sheet1`，A1 为 `时间\\到药材中心的距离`；B:V 是固定绝对距离 `0.0, 0.1, ..., 2.0 cm`，W 列是额外的 `药材表面` 动态列。数据时间为 `60, 120, ..., 188520 s`，共 3142 个 60 s 状态；不写入 0 s 行，保持当前模板/生成器语义。

固定绝对位置在某一时刻只有满足 $r\le R(t)$ 才有效；收缩后已经位于表面之外的单元格保持空白，绝不外推。`药材表面` 列始终取该时刻固定域 $\xi=1$ 的真实值，对应真实 $r=R(t)$。所有水分数值按四位小数保存。

### 7.2 `task4_all_answers.csv`

字段为：

```text
record_type,time_s,time_h,radius_cm,r_cm,is_surface,temperature_C,moisture_kgkg
```

包含四类记录：

- `sample_fixed`：每 60 s、每个当时仍位于药材内部的固定绝对位置；
- `sample_surface`：每 60 s 的真实移动表面；
- `drying_end_fixed`：精确终止时刻的有效固定位置；
- `drying_end_surface`：精确终止时刻的真实表面。

因此 CSV 同时保留温度、水分、当时半径、绝对位置、表面标志和精确终止状态，可独立重建 `result4.xlsx` 与表 6，而不是只有少量论文数据。

### 7.3 `task4_paper_table.xlsx` 与表 6

工作表名为 `表6`，含 6 h 间隔行直到 48 h，再加精确结束行和最终时长摘要。空间列采用 `0 cm`、`0.5 cm`、`1.0 cm` 和该时刻真实的 `药材表面`；表面列不把 `r=2 cm` 当作表面。

当前终止半径只有 `1.2000 cm`，所以 `1.5 cm` 在终止时已位于药材外部，不能为表 6 的最终行凭空外推；当前生成器据此保留终止时仍有明确物理意义的 `0/0.5/1.0 cm` 固定列，并单独给出真实表面列。

表 6 完整数值如下（均按四位小数书写）：

| 时间/h | 0 cm | 0.5 cm | 1.0 cm | 药材表面 |
|---:|---:|---:|---:|---:|
| 6 | 1.9493 | 1.7800 | 1.2555 | 0.5682 |
| 12 | 0.8691 | 0.7727 | 0.4841 | 0.2141 |
| 18 | 0.4567 | 0.4108 | 0.2640 | 0.1017 |
| 24 | 0.3056 | 0.2791 | 0.1894 | 0.0711 |
| 30 | 0.2369 | 0.2188 | 0.1549 | 0.0608 |
| 36 | 0.1991 | 0.1853 | 0.1351 | 0.0565 |
| 42 | 0.1754 | 0.1641 | 0.1222 | 0.0543 |
| 48 | 0.1590 | 0.1494 | 0.1132 | 0.0531 |
| 烘干结束时间（52.3709 h） | 0.1500 | 0.1413 | 0.1081 | 0.0525 |

最终烘干时长摘要为 `52.3709 h`。

## 8. 验证、敏感性和可信度证据

当前脚本的只读基线命令输出了以下数值证据：

- 附件 2 共读取 145 个已知时间点，分段线性插值回读误差为 `0.0 m`；初始半径为 `2.0 cm`，终止半径为 `1.2 cm`。
- 固定域中心离散满足零通量，且中心移动项系数因 $\xi=0$ 为零。
- 温度范围为 `28.0000–50.1650 °C`；内部水分范围为 `0.05249609–2.55000000 kg/kg`；未出现 NaN、Inf 或明显负水分。
- 附录 4 的 $D$ 计算在指数前使用 Kelvin；独立参考点检查通过。
- 全部时间步的最大 Picard 迭代次数为 `4`。
- `result4.xlsx`、`task4_paper_table.xlsx`、`task4_all_answers.csv` 回读后与求解器四位小数结果的最大差均为 `0`；越过移动表面的固定位置均保持空白，越界非空值为 `0`。
- 终止二分括号宽度为 `0.0009765625 s`，满足不超过 `0.001 s`；上端严格低于阈值，下端仍高于阈值。

低成本敏感性检查采用 `N=160, \Delta t=1 s`，得到 `52.3510623 h`；与基线 `N=320, \Delta t=0.5 s` 的差为 `0.0198014 h`，即约 `71.285 s`、相对差 `0.0378%`。该差异相对于约 52 h 的烘干时长较小，当前加密结果可作为最终提交数值。

## 9. 文件、运行命令和 Git 记录

### 9.1 当前文件

- 求解器：[solution/task4/script/solve_task4.py](../solution/task4/script/solve_task4.py)
- 官方格式结果：[solution/task4/answer/result4.xlsx](../solution/task4/answer/result4.xlsx)
- 论文表 6：[solution/task4/answer/task4_paper_table.xlsx](../solution/task4/answer/task4_paper_table.xlsx)
- 完整长表：[solution/task4/answer/task4_all_answers.csv](../solution/task4/answer/task4_all_answers.csv)

### 9.2 运行命令

在仓库根目录执行完整求解、粗网格敏感性和三个文件生成/回读验收：

```bash
/Users/jiaqiaosu/miniconda3/bin/python solution/task4/script/solve_task4.py
```

只做数值检查而不写入答案文件：

```bash
/Users/jiaqiaosu/miniconda3/bin/python solution/task4/script/solve_task4.py --no-write
```

跳过 `N=160, dt=1 s` 粗解以缩短检查时间：

```bash
/Users/jiaqiaosu/miniconda3/bin/python solution/task4/script/solve_task4.py --no-write --skip-sensitivity
```

### 9.3 问题四已有提交

按时间顺序，问题四实现的四个提交为：

1. `bbc9c4f7c59587add316b27e43894b77bb01316`：建立问题四移动边界求解器；
2. `07cf8855c430771b5ed66ac8bf8aa62ef2767178`：修正问题四界面离散与终止事件定位；
3. `c4bc983dd74e2930399afdfc40c0bb93992f97b1`：实现问题四结果文件生成与验收；
4. `2b0d204d040e49e39e39ab4e4efbc39cdedb6573`：生成问题四最终数值结果。

本文档应作为后续建模或论文整理的直接入口。仓库中并发产生的 `handoff/task4_gjs_handoff.md`、`context/context-task4-1_xby.md` 以及 `.DS_Store`、`__pycache__` 等非 task4 当前提交文件未被本任务处理；若其内容与当前已提交脚本或本文不一致，优先采用当前脚本和本文。
