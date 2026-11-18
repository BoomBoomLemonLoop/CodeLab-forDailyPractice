# 教材 → 问题 → 代码 → 验证

当前进度：Anderson《Computational Fluid Dynamics: The Basics with Applications》已开始第 7 章，
准一维喷管和 MacCormack。毕业论文计算优先 Turns《An Introduction to Combustion》+ Cantera。
Moukalled、Mangani、Darwish《The Finite Volume Method in Computational Fluid Dynamics》按需支持 FVM/OpenFOAM。

下列章节编号来自用户提供的更新版框架，尚未按用户手头版本逐一核对；尤其 Turns 的版次、
页码和小节号在任务开始时记录。只按已知主题规划，不据此宣称已读完或已有计算成果。

| 教材/资源与阅读锚点 | 唯一归属（链接） | 小任务方向与验证依据 | 状态 |
| --- | --- | --- | --- |
| Anderson 第 7 章，7.2–7.3（小节待核对） | [喷管案例](../fundamentals/cfd/anderson/ch07-quasi-1d-nozzle/README.md) | 控制方程、几何、MacCormack 预测校正、边界；手算一步/等熵关系/质量流量与网格收敛 | 阅读进行中，代码 Planned |
| Anderson 第 7 章，7.5–7.6（后续，待核对） | 同一喷管案例 | 守恒/非守恒形式、激波与耗散；先明确边界及适用基准 | Planned |
| Moukalled 第 5/8 章：FVM/扩散 | [教材笔记](../fundamentals/finite-volume-method/moukalled/README.md) → [已有扩散](../fundamentals/finite-volume-method/01-diffusion/README.md) | 控制体收支、边界面距离；解析解与二阶收敛 | 扩散 Tested；教材笔记 Planned |
| Moukalled 第 6–7/9–13/15 章（按需） | 同一教材笔记 | 网格与 OpenFOAM 表示、梯度、线性求解、对流、时间离散、不可压流；每次只关联一个算子 | Planned |
| CFDPython 1–4，后续 11–12 | [伴随学习](../fundamentals/cfd/cfdpython/README.md) | 数组、差分/PDE、cavity/channel；CFL、守恒与收敛，不替代可压喷管 | Planned |
| Turns 第 2 章：热化学（版次待核对） | [理论笔记](../fundamentals/combustion/turns/README.md) → [热化学](../simulations/cantera/thermochemistry/README.md) | 状态、组成、当量比、TP/HP 平衡约束；单位与元素/能量守恒 | Planned |
| Turns 第 4–6 章：动力学、机理与耦合（待核对） | [0D 导航](../simulations/cantera/zero-d-reactors/README.md) → [已有点火](../simulations/cantera/zero-dimensional-ignition/README.md) | 定容/定压、延迟定义、温压/phi 敏感性；质量/能量、容差/采样与窗口检查 | 已有点火 Tested；扩展 Planned |
| GitHub 收藏与 C++ 阅读 | [收藏学习用途](../references/starred-github.md) | FVM2D 的网格/通量调用链；只读一个小模块并解释输入输出 | Planned |
| OpenFOAM / Fluent | [现有仿真计划](../simulations/README.md) | FVM 问题需要时再开 cavity/pitzDaily；版本、checkMesh、守恒、网格检查 | Planned |
| TVC / 压气机 / 代理优化 | [原创研究](../research/README.md) | 将验证过的学习工具用于明确研究问题；0D 延迟不等于稳焰能力 | Planned |
| emu 论文复现 | [已有案例](../reproductions/papers/emu-2024-surrogate/README.md) | 先确认原文、目标图表和指标，不能从目录名推测内容 | Planned |

本表是唯一当前学习映射；长期技能参考 [learning-roadmap.md](learning-roadmap.md)。
状态沿用根 README：Planned、Implemented、Tested、Validated，阅读进度与代码状态分开记录。
每次任务按 [study-tasks.md](study-tasks.md) 建立一条记录；完成后更新这里的案例链接和证据，
不提前生成未来章节的脚本。没有代码的目录只有说明，不意味着可运行。
