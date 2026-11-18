# 开源求解器阅读

候选 [FVM2D](https://github.com/RetrO598/FVM2D) 与
[Code_CartesianCraft](https://github.com/chenyongxin/Code_CartesianCraft)。
先查许可证与构建依赖，再在独立 clone 中跟踪网格读入 → 控制体 → 数值通量 →
线性系统/时间推进 → 边界 → 输出的调用链。一次只解释一个函数和一个小型基准。
Code4CFD 是资源索引；CrouzeixConjecture 是数学研究记录，两者不归为 CFD 求解器。
状态 Planned，尚未编译或验证这些上游程序。
