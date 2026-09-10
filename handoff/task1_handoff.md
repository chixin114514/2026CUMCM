# A题问题一：融合版数学模型交接文档

## 1. 任务一总结

问题一研究中药材在前 30 min 预热平衡阶段内的温度与水分迁移规律。

药材近似为圆柱体：

- 长度：\(L=25\ \mathrm{cm}=0.25\ \mathrm m\)；
- 半径：\(R=2\ \mathrm{cm}=0.02\ \mathrm m\)；
- 初始温度：\(28^\circ\mathrm C\)；
- 初始水分浓度（干基含水率）：\(2.55\ \mathrm{kg/kg}\)。

附件 1 给出烘房温度和烘房水分浓度随时间的变化，附录 2 给出药材的热物性、换热传质参数以及水分扩散系数经验公式。需要建立

\[
T(r,t),\qquad C(r,t),
\]

即药材内部温度和水分浓度关于时间 \(t\) 与距中心径向位置 \(r\) 的分布模型。

题目要求输出：

- 关键时刻：\(100,300,600,900,1200,1500,1800\ \mathrm s\)；
- 关键半径：\(0,0.5,1,1.5,2\ \mathrm{cm}\)；
- 完整结果：\(0\sim1800\ \mathrm s\) 每隔 1 s，\(0\sim2\ \mathrm{cm}\) 每隔 0.1 cm；
- 温度和水分浓度结果均保留四位小数。

---

## 2. 总体建模结构

问题一采用一维轴对称圆柱径向传热—传质模型：

\[
\boxed{
\text{附件1动态烘房条件}
\rightarrow
\begin{cases}
\text{圆柱径向非稳态导热}\cr
\text{圆柱径向非线性水分扩散}
\end{cases}
\rightarrow
\text{FVM空间离散}
\rightarrow
\text{Crank--Nicolson时间推进}
}
\]

其中水分扩散系数依赖局部水分浓度 \(C\)，因此水分方程是非线性的；每个时间步采用 Picard 迭代更新 \(D(C)\)，控制体界面的扩散系数采用调和平均。

第一问中温度场和水分场分别求解。两者共享同一几何区域与烘房环境，但温度方程不含 \(C\)，题目给出的第一问扩散系数 \(D\) 也不含 \(T\)，因此不额外引入蒸发潜热等题目未提供参数的热湿耦合项。

---

## 3. 基本假设

1. 药材为均匀、各向同性的规则圆柱体。
2. 预热阶段内药材尺寸保持不变，不考虑干燥收缩。
3. 初始温度和初始水分浓度在药材内部均匀分布。
4. 温度和水分仅沿径向变化，忽略周向和轴向梯度。
5. 第一问中 \(\rho,c_p,k,h,h_m\) 均取题目给定常数。
6. 水分扩散系数仅由局部水分浓度决定，严格采用附录 2 的 \(D(C)\)。
7. 烘房温度和水分浓度在整个药材外表面上均匀，只随时间变化。
8. 附件 1 的烘房水分浓度按题目给出的变量直接作为对流传质环境边界，不引入额外吸附等温线或湿空气换算。
9. 不额外加入题目未提供参数的蒸发潜热、辐射换热、化学反应等机制。

由于 \(L/R=12.5\)，圆柱明显细长，而题目只要求“到药材中心的距离”方向上的结果，因此采用一维径向模型作为问题一的主模型是合理的。

---

## 4. 烘房动态边界

附件 1 给出离散时刻的烘房温度和烘房水分浓度。设相邻两个数据点为

\[
(t_j,y_j),\qquad (t_{j+1},y_{j+1}),
\]

其中 \(y\) 分别代表温度或水分浓度，则在区间 \([t_j,t_{j+1}]\) 内采用分段线性插值：

\[
\boxed{
y(t)=y_j+\frac{y_{j+1}-y_j}{t_{j+1}-t_j}(t-t_j)
}
\]

由此得到连续边界函数

\[
\boxed{T_\infty(t)},\qquad \boxed{C_\infty(t)}.
\]

这种处理直接保留附件 1 中真实的动态升温与水分环境变化，不额外假设烘房条件为常数，也不引入不必要的高阶拟合。

---

## 5. 温度模型

### 5.1 控制方程

根据能量守恒和 Fourier 导热定律，在轴对称、仅考虑径向变化条件下，圆柱内部温度满足

\[
\boxed{
\rho c_p\frac{\partial T}{\partial t}
=
\frac{1}{r}\frac{\partial}{\partial r}
\left(kr\frac{\partial T}{\partial r}\right)
},
\qquad 0<r<R.
\]

第一问中 \(\rho,c_p,k\) 为常数，因此也可写为

\[
\boxed{
\frac{\partial T}{\partial t}
=
\alpha\left(
\frac{\partial^2T}{\partial r^2}
+\frac1r\frac{\partial T}{\partial r}
\right)
},
\qquad
\alpha=\frac{k}{\rho c_p}.
\]

### 5.2 参数

\[
\rho=820\ \mathrm{kg/m^3},
\]

\[
c_p=2600\ \mathrm{J/(kg\cdot K)},
\]

\[
k=0.36\ \mathrm{W/(m\cdot K)},
\]

\[
h=25\ \mathrm{W/(m^2\cdot K)}.
\]

热扩散率为

\[
\boxed{
\alpha=\frac{k}{\rho c_p}
\approx1.6886\times10^{-7}\ \mathrm{m^2/s}
}.
\]

### 5.3 初始条件

\[
\boxed{T(r,0)=28^\circ\mathrm C}.
\]

### 5.4 圆柱中心边界

由于 \(r=0\) 是对称轴，中心不存在净径向热流：

\[
\boxed{
\left.\frac{\partial T}{\partial r}\right|_{r=0}=0
}.
\]

### 5.5 药材表面边界

药材表面与烘房热风之间采用 Newton 对流换热条件：

\[
\boxed{
-k\left.\frac{\partial T}{\partial r}\right|_{r=R}
=h[T(R,t)-T_\infty(t)]
}.
\]

等价地可写为

\[
k\left.\frac{\partial T}{\partial r}\right|_{r=R}
=h[T_\infty(t)-T(R,t)].
\]

当 \(T_\infty>T(R,t)\) 时，热量由烘房进入药材，随后由表面向中心传导。

### 5.6 为什么必须求空间温度分布

温度 Biot 数为

\[
Bi_h=\frac{hR}{k}
=\frac{25\times0.02}{0.36}
\approx1.3889.
\]

由于 \(Bi_h\) 明显大于 0.1，药材内部温度梯度不能忽略，因此不能把整根药材视作一个均匀温度的集总系统。

热扩散特征时间约为

\[
\tau_T\sim\frac{R^2}{\alpha}
\approx2.37\times10^3\ \mathrm s
\approx39.5\ \mathrm{min}.
\]

30 min 与该特征时间处于同一数量级，因此预热阶段表面与中心存在明显温差具有合理的物理尺度。

---

## 6. 水分模型

### 6.1 控制方程

根据水分质量守恒和 Fick 第一定律

\[
J_r=-D(C)\frac{\partial C}{\partial r},
\]

圆柱内部水分浓度满足

\[
\boxed{
\frac{\partial C}{\partial t}
=
\frac1r\frac{\partial}{\partial r}
\left[rD(C)\frac{\partial C}{\partial r}\right]
},
\qquad 0<r<R.
\]

### 6.2 水分扩散系数

附录 2 给出

\[
\boxed{
D(C)=7\times10^{-9}
\exp\left(-\frac{0.89}{C}\right)
\ \mathrm{m^2/s}
}.
\]

由于 \(D\) 随局部 \(C\) 变化，水分方程是非线性扩散方程，不能在整个计算过程中把 \(D\) 固定为初始值。

初始状态 \(C=2.55\) 时

\[
D(2.55)\approx4.94\times10^{-9}\ \mathrm{m^2/s}.
\]

对应扩散特征时间约为

\[
\tau_C\sim\frac{R^2}{D(2.55)}
\approx8.1\times10^4\ \mathrm s
\approx22.5\ \mathrm h.
\]

这一尺度远大于 30 min，因此预热阶段应表现为表层首先明显失水，而中心含水率变化相对很小。

### 6.3 初始条件

\[
\boxed{C(r,0)=2.55\ \mathrm{kg/kg}}.
\]

### 6.4 圆柱中心边界

中心处不存在跨越对称轴的净水分通量：

\[
\boxed{
\left.\frac{\partial C}{\partial r}\right|_{r=0}=0
}.
\]

### 6.5 药材表面边界

采用对流传质 Robin 边界：

\[
\boxed{
-D(C_s)
\left.\frac{\partial C}{\partial r}\right|_{r=R}
=
h_m[C_s-C_\infty(t)]
},
\qquad C_s=C(R,t),
\]

其中

\[
\boxed{h_m=8\times10^{-7}\ \mathrm{m/s}}.
\]

当 \(C_s>C_\infty(t)\) 时，药材表面向烘房排出水分，内部水分再向表面扩散。

---

## 7. 有限体积空间离散

空间上采用守恒型有限体积法（FVM）。这样可直接对每个径向控制体写热量或水分守恒，同时自然处理圆柱坐标中心 \(r=0\) 和外表面 Robin 边界。

### 7.1 径向网格

取

\[
0=r_0<r_1<\cdots<r_N=R,
\]

主计算可采用

\[
\boxed{\Delta r=0.005\ \mathrm{cm}=5\times10^{-5}\ \mathrm m}.
\]

对应 \(R/\Delta r=400\)，包含首尾节点共 401 个径向节点。最终输出所需的 0.1 cm 间隔位置均可直接落在计算网格上。

### 7.2 控制体几何

节点 \(r_i\) 左右界面为 \(r_{i-1/2}\) 与 \(r_{i+1/2}\)。约去所有方程共有的 \(2\pi L\) 后，第 \(i\) 个控制体的径向体积测度为

\[
\boxed{
V_i^{(r)}
=
\frac{r_{i+1/2}^2-r_{i-1/2}^2}{2}
}.
\]

中心和表面节点采用半控制体。

---

## 8. 温度方程的有限体积形式

内部界面导热通量写为

\[
\boxed{
F^T_{i+1/2}
=
k r_{i+1/2}
\frac{T_{i+1}-T_i}{\Delta r}
}.
\]

对内部控制体：

\[
\boxed{
\rho c_pV_i^{(r)}\frac{dT_i}{dt}
=
F^T_{i+1/2}-F^T_{i-1/2}
}.
\]

中心控制体左侧面积为零，因此

\[
\boxed{
\rho c_pV_0^{(r)}\frac{dT_0}{dt}=F^T_{1/2}
}.
\]

这样无需在 \(r=0\) 直接计算 \(1/r\)，也无需人为加入数值 \(\varepsilon\)。

表面对流热通量按“进入药材为正”写为

\[
\boxed{
F^T_R=Rh[T_\infty(t)-T_N]
}.
\]

于是表面控制体满足

\[
\boxed{
\rho c_pV_N^{(r)}\frac{dT_N}{dt}
=
F^T_R-F^T_{N-1/2}
}.
\]

---

## 9. 水分方程的有限体积形式

内部界面扩散通量写为

\[
\boxed{
F^C_{i+1/2}
=
D_{i+1/2}r_{i+1/2}
\frac{C_{i+1}-C_i}{\Delta r}
}.
\]

内部控制体满足

\[
\boxed{
V_i^{(r)}\frac{dC_i}{dt}
=
F^C_{i+1/2}-F^C_{i-1/2}
}.
\]

中心控制体为

\[
\boxed{
V_0^{(r)}\frac{dC_0}{dt}=F^C_{1/2}
}.
\]

表面对流传质通量按“进入药材为正”写为

\[
\boxed{
F^C_R=Rh_m[C_\infty(t)-C_N]
}.
\]

因此表面控制体满足

\[
\boxed{
V_N^{(r)}\frac{dC_N}{dt}
=
F^C_R-F^C_{N-1/2}
}.
\]

通常 \(C_\infty<C_N\)，因此 \(F^C_R<0\)，对应药材向外失水。

---

## 10. 界面扩散系数：调和平均

先在节点处计算

\[
D_i=D(C_i).
\]

对于相邻节点间的控制体界面，采用调和平均：

\[
\boxed{
D_{i+1/2}
=
\frac{2D_iD_{i+1}}{D_i+D_{i+1}}
}.
\]

这样处理的主要理由是有限体积法真正关心的是跨界面的扩散通量。调和平均可解释为两侧扩散阻力串联；当相邻区域的扩散系数差异较大时，它不会使较大的扩散系数过度主导界面通量，因此比简单算术平均更适合当前扩散模型。

---

## 11. 时间离散：Crank--Nicolson

时间方向采用 Crank--Nicolson 格式。对一般半离散系统

\[
\frac{d\mathbf u}{dt}=\mathbf F(t,\mathbf u),
\]

从 \(t_n\) 到 \(t_{n+1}=t_n+\Delta t\) 写为

\[
\boxed{
\frac{\mathbf u^{n+1}-\mathbf u^n}{\Delta t}
=
\frac12
\left[
\mathbf F(t_n,\mathbf u^n)
+
\mathbf F(t_{n+1},\mathbf u^{n+1})
\right]
}.
\]

主计算可采用

\[
\boxed{\Delta t=0.25\ \mathrm s}.
\]

温度模型在线性物性条件下，每一时间步形成一个三对角线性方程组，可直接求解。

选择 CN 的原因是时间离散公式清晰可见，数值过程容易解释；对于扩散型问题又具有良好的稳定性，并且相比一阶隐式格式具有更高时间精度。

---

## 12. 水分非线性处理：Picard 迭代

由于

\[
D=D(C),
\]

未知的 \(C^{n+1}\) 同时决定下一时间层的扩散系数，因此水分 CN 方程是非线性的。

在每个时间步内采用 Picard 迭代。

已知 \(C^n\)，先取

\[
\boxed{C^{n+1,(0)}=C^n}.
\]

第 \(m\) 次迭代执行：

\[
D_i^{(m)}=D\!\left(C_i^{n+1,(m)}\right),
\]

再计算界面调和平均

\[
D_{i+1/2}^{(m)}
=
\frac{2D_i^{(m)}D_{i+1}^{(m)}}{D_i^{(m)}+D_{i+1}^{(m)}}.
\]

固定这一轮 \(D^{(m)}\) 后，水分方程变为线性 CN 方程组，求得

\[
C^{n+1,(m+1)}.
\]

当

\[
\boxed{
\max_i
\left|
C_i^{n+1,(m+1)}-C_i^{n+1,(m)}
\right|
<\varepsilon
}
\]

时接受该时间步的解。

这种方法的计算逻辑是显式可解释的：根据当前含水率估计局部扩散能力，再利用新的含水率修正扩散系数，反复迭代直到两者相互一致。

---

## 13. 完整数学模型

问题一最终模型可集中写为

\[
\boxed{
\begin{cases}
\displaystyle
\rho c_p\frac{\partial T}{\partial t}
=
\frac1r\frac{\partial}{\partial r}
\left(kr\frac{\partial T}{\partial r}\right),\\[8pt]
\displaystyle
\frac{\partial C}{\partial t}
=
\frac1r\frac{\partial}{\partial r}
\left[rD(C)\frac{\partial C}{\partial r}\right],\\[8pt]
\displaystyle
D(C)=7\times10^{-9}\exp\left(-\frac{0.89}{C}\right),\\[8pt]
T(r,0)=28,\qquad C(r,0)=2.55,\\[6pt]
\displaystyle
\left.\frac{\partial T}{\partial r}\right|_{r=0}=0,
\qquad
\left.\frac{\partial C}{\partial r}\right|_{r=0}=0,\\[8pt]
\displaystyle
-k\left.\frac{\partial T}{\partial r}\right|_{r=R}
=h[T(R,t)-T_\infty(t)],\\[8pt]
\displaystyle
-D(C_s)\left.\frac{\partial C}{\partial r}\right|_{r=R}
=h_m[C_s-C_\infty(t)].
\end{cases}
}
\]

参数为

\[
R=0.02\ \mathrm m,
\quad
\rho=820\ \mathrm{kg/m^3},
\quad
c_p=2600\ \mathrm{J/(kg\cdot K)},
\]

\[
k=0.36\ \mathrm{W/(m\cdot K)},
\quad
h=25\ \mathrm{W/(m^2\cdot K)},
\quad
h_m=8\times10^{-7}\ \mathrm{m/s}.
\]

其中 \(T_\infty(t)\) 和 \(C_\infty(t)\) 由附件 1 分段线性插值得到。

数值求解采用

\[
\boxed{
\text{径向 FVM}
+
\text{Crank--Nicolson}
+
\text{Picard 非线性迭代}
+
\text{界面 }D\text{ 调和平均}
}.
\]

---

## 14. 模型的完整计算流程

```text
附件1
│
├── 烘房温度数据 ──线性插值──> T∞(t)
│
└── 烘房水分数据 ──线性插值──> C∞(t)

药材圆柱模型：0 ≤ r ≤ R
│
├── 温度场 T(r,t)
│   ├── 能量守恒 + Fourier 定律
│   ├── 圆柱径向非稳态导热 PDE
│   ├── 中心对称条件
│   ├── 表面 Newton 对流边界
│   ├── FVM 空间离散
│   └── Crank--Nicolson 时间推进
│
└── 水分场 C(r,t)
    ├── 质量守恒 + Fick 定律
    ├── 非线性扩散 PDE
    ├── D = D(C)
    ├── 中心对称条件
    ├── 表面对流传质边界
    ├── FVM 空间离散
    ├── 界面 D 调和平均
    └── CN + Picard 迭代

                ↓
         得到 T(r,t), C(r,t)
                ↓
      抽取题目指定时间与半径
                ↓
       形成表1、表2和完整结果
```

---

## 15. 结果应呈现的物理规律

由上述模型的尺度分析可预期：

- 预热阶段烘房温度高于药材温度，热量首先由表面对流进入药材，再向内部传导，因此表面升温快于中心；
- 水分由药材表面向烘房迁移，内部水分再向表面扩散，因此表面失水快于内部；
- 热扩散特征时间约 39.5 min，而初始水分扩散特征时间约 22.5 h，因此在前 30 min 内，温度变化能够较明显地传播到内部，而中心水分浓度变化应明显滞后于表层。

这三个规律是模型本身所表达的核心实际过程：

\[
\boxed{
\text{表面先受热、先失水}
\quad\Longrightarrow\quad
\text{热量和水分梯度驱动内部传递}
}
\]

---

## 16. 问题一输出

模型求解后需要形成两类结果。

第一类为题目正文表格：

- 时间：100、300、600、900、1200、1500、1800 s；
- 半径：0、0.5、1、1.5、2 cm；
- 分别给出温度 \(T(r,t)\) 和水分浓度 \(C(r,t)\)。

第二类为完整时空结果：

- 时间：0–1800 s，每隔 1 s；
- 半径：0–2 cm，每隔 0.1 cm；
- 对每个 \((t,r)\) 同时保存温度和水分浓度。

因此问题一的完整计算目标可以概括为

\[
\boxed{
(T_\infty(t),C_\infty(t))
\xrightarrow{\text{传热传质模型}}
(T(r,t),C(r,t))
\xrightarrow{\text{指定采样}}
\text{问题一结果}
}.
\]
