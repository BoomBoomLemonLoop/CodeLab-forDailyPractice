# Anderson 第 7 章：准一维喷管

阅读进行中；代码 **Planned**。本轮没有生成 MacCormack 完整解答。
来源为 Anderson《Computational Fluid Dynamics: The Basics with Applications》，版次/页码待记录。

本目录是该喷管案例唯一位置：先明确控制方程、几何、无量纲化和边界，再由学习者逐步实现
一个函数或预测—校正步骤。可用等熵关系、手算一步、质量流量、时间/网格收敛作检查，
使用哪项取决于工况与模型假设；激波问题不能直接套光滑等熵解作全域基准。
后续再比较守恒/非守恒形式及耗散，不把 CFDPython 不可压流课程当本章替代。

开始任务见 [学习映射](../../../../docs/study-map.md) 与
[小任务记录](../../../../docs/study-tasks.md)。实际代码和 notes 只在开始时创建。
