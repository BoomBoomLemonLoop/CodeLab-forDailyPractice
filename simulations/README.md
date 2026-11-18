# 仿真计划（Planned）

只有 [Cantera 0D](cantera/zero-dimensional-ignition/README.md) 已实现；
下面尚无网格、边界配置或已验证可运行的求解案例。

| 主题 | 首个交付与检查 | 后续 |
| --- | --- | --- |
| OpenFOAM cavity | 在 WSL 记录实际 v2606 版本、教程来源；复制至独立工作区；checkMesh、边界和速度剖面检查 | 3 级网格、连续性与残差、中心线基准 |
| OpenFOAM pitzDaily | 核实发行版教程路径和求解器，记录 fvSchemes/fvSolution 与 RANS 模型 | 质量流量平衡、再附长度、网格敏感性 |
| 旋转接口 | 分别解释 sliding mesh、AMI 插值与 mixing plane 周向平均 | 不将三者视为同一模型；先找可信基准 |
| Fluent | 按本机 Student 许可实际限制设计网格，先核实可用单元数 | 网格/边界/RANS 敏感性、总压损失、与 OpenFOAM 比较 |

不把求解器版本目标写成已安装事实。初期每例限个人电脑内存和短试跑，
记录峰值内存与运行时间，再决定完整收敛计算预算。大型 Fluent 二进制与 OpenFOAM
时间序列不入 Git；真实案例建成后补 case-local `.gitignore`，保留初始条件和字典。
