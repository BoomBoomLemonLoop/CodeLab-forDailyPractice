# 一维稳态扩散：解析解与离散收敛

研究问题：均匀网格、单元中心有限体积法能否保持通量守恒并达到二阶精度？
状态 Tested（解析解 numerical verification）；实际测试结果见 `docs/initialization-report.md`。

无量纲模型：`-d²u/dx² = π² sin(πx)`，`x ∈ [0,1]`，`u(0)=u(1)=0`，常系数为 1。
解析解 `u(x)=sin(πx)` 可直接代入方程验证。这里采用已知解构造源项，
并非实验数据，也不是实际燃烧室模型。

将方程对每个控制体积分，内部面采用中心梯度，源项采用中点求积。
均匀宽度 h，内部行 `2u_i-u_(i-1)-u_(i+1)=h² f_i`；
边界面距第一个中心 h/2，因此首行 `3u_0-u_1=h² f_0`，末行对称。
Thomas 三对角消元只使用 O(N) 内存与时间。限制 2–2000 单元以保持学习案例轻量。

从仓库根目录运行：

```text
python fundamentals/finite-volume-method/01-diffusion/diffusion.py --cells 40
python -m pytest tests/test_diffusion.py
```

输出单元中心值对解析解的 RMS L2 与 Linf 绝对误差。
测试在 20/40/80 单元计算 `p=log2(E_h/E_(h/2))`，要求 1.95–2.05，
80 单元 RMS 小于 1e-4，并核对边界总外流通量与离散源项积分。
这些容差只适用于本问题，不能复制为所有论文的统一验收阈值。

结果解释：误差随网格加密下降且守恒成立，支持该实现对本模型的 numerical verification；
不构成湍流、多维或真实流动的 validation。下一步先手推两单元矩阵，再改变边界条件。
代码为本仓库独立实现，未复制上游求解器。
