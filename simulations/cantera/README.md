# Cantera：热化学 → 0D 反应器 → 点火

本目录是所有 Cantera 计算的唯一归属。Turns 理论笔记放在
[fundamentals/combustion/turns](../../fundamentals/combustion/turns/README.md)，不复制可执行脚本。

| 入口 | 范围 | 状态 |
| --- | --- | --- |
| [thermochemistry](thermochemistry/README.md) | 状态、组成、当量比与约束平衡 | Planned；尚无脚本 |
| [zero-d-reactors](zero-d-reactors/README.md) | 0D 模型/假设导航，后续定压等独立问题 | Planned 导航；链接现有定容案例 |
| [zero-dimensional-ignition](zero-dimensional-ignition/README.md) | 唯一现有 H2/air 绝热定容点火实现 | Tested：守恒与采样检查；未物理 Validated |

已有入口保持不变，从仓库根目录运行：

```text
python simulations/cantera/zero-dimensional-ignition/ignition.py
python -m pytest -m integration
```

需要 `python -m pip install -e ".[dev,combustion]"`。
现有点火的判据、参数敏感性与输出改进都在原案例扩展，不建立第二个 ignition-delay 脚本。
更新 scaffold 的 CH4/gri30 示例与原案例 H2/h2o2 工况不同，本轮不引入、不混用结果。
