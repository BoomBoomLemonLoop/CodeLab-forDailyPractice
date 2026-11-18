# 参考资料索引

当前教材对应与学习时机见 [GitHub 收藏用途](starred-github.md) 和
[学习映射](../docs/study-map.md)。本页继续维护项目背景与许可核查记录。

核查日期：2026-11-18。以下记录来自上游页面；“值得学习/研究联系”为本仓库的学习判断，
不是对上游数值正确性的背书。统一学习状态：Planned（已浏览项目说明，尚未独立构建/验证）。
未下载或复制任何上游源码。语言未确认的条目明确标注待核查。

| 项目（原始链接） | 语言/形式 | 技术与学习价值、研究联系 | 许可证与待核查事项 |
| --- | --- | --- | --- |
| [CFDPython](https://github.com/barbagroup/CFDPython) | Python / Jupyter | 渐进式 PDE 与 Navier–Stokes 教学；用于理解离散与数值扩散，不当作工业求解器 | 存在 LICENSE；代码与教材的具体授权范围需逐项核查后才复制 |
| [FVM2D](https://github.com/RetrO598/FVM2D) | C++ / CMake | 非结构 FVM、Euler/NS/RANS、Roe/AUSM 类通量、SA；学习网格与通量抽象，服务 CFD C++ 阅读 | 页面未明确授权；继承代码来源与许可证均待核查 |
| [Code4CFD](https://github.com/thw1021/Code4CFD) | Markdown 索引 | 流体开源资源地图；发现基准和后处理工具，本身不是数值求解器 | 页面标注 CC0-1.0；链接项目各自独立授权 |
| [Computational-Fluid-Dynamics-Homework](https://github.com/RPLUG/Computational-Fluid-Dynamics-Homework) | 可见 MATLAB 目录；其余待逐文件确认 | CFD 课程习题，适合先独立推导再对照；不抄作业或将上游结果冒充自主实现 | 页面标注 GPL-2.0；再分发前阅读完整 LICENSE |
| [Code_CartesianCraft](https://github.com/chenyongxin/Code_CartesianCraft) | 编译型源码/CMake；具体语言待核查 | 不可压湍流、HYPRE 并行 Poisson、可选 HDF5；后期学习压力求解和 IO，先评估个人电脑构建成本 | 页面未明确许可证；依赖许可也须检查 |
| [CrouzeixConjecture](https://github.com/jinshanmu/CrouzeixConjecture) | LaTeX / Lean 4 | 候选证明研究工作区；借鉴可追溯论证与审计，不是 CFD 求解器或已证明结论 | 许可证待核查；上游声明同行评审待完成，不能当作已确立定理 |

源码研究采用主仓库之外的独立 clone/fork，记录 commit SHA；本索引不是许可审计结论。
读源码后用自己的推导编写实现，确需引用片段必须保留出处及许可证要求。

主题入口：[CFD 学习](cfd-learning.md)、[开源求解器](open-source-solvers.md)、
[燃烧模型](combustion-modeling.md)、[数值方法](numerical-methods.md)。
