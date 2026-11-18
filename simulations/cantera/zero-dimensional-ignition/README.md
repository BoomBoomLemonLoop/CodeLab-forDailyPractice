# 绝热定容均匀反应器

研究问题：H2/air 理想均匀混合物在给定初态下的温升及点火延迟是什么？
状态和实测证据见 `docs/initialization-report.md`；没有实验验证数据。

模型：封闭、刚性、绝热、理想气体反应器；质量和总内能守恒，
物种满足 `dY_k/dt = W_k omega_k/rho`，温度由内能方程与状态方程耦合求解。
无流入流出、无湍流或热损失。Cantera 自带 `h2o2.yaml`，默认 H2/O2/N2，
1000 K、101325 Pa、当量比 1、体积 1 m³（均匀绝热状态演化与此体积选择无关）。
这不是涡喷燃油模型；不得推断实际 TVC 稳焰能力。

```text
python -m pip install -e ".[dev,combustion]"
python simulations/cantera/zero-dimensional-ignition/ignition.py --temperature 1000 --pressure 101325 --phi 1 --end-time 0.002 --samples 2001
python -m pytest -m integration
```

输出 JSON 包括版本、机理、参数、容差、最终温压、质量/能量漂移与点火延迟。
点火定义为采样 `dT/dt` 的内部最大值，且总温升超过 100 K。
若峰值位于时间窗口端点或温升不足，返回 `ignition_resolved=false` 和 null，
含义是该窗口/判据未分辨点火，不代表物理上永不点火。
积分器采用自适应时间步，均匀输出采样不是内部积分步长。

测试比较 2001/4001 采样的延迟，允许 1% 差异；检查内能相对漂移 <1e-6、
质量漂移 <1e-12，短时间窗不得给出伪点火。仍需进一步收紧积分容差、延长窗口，
比较 OH 峰值、温升阈值等定义及温度/压力/当量比敏感性。
程序成功与守恒检查不等于机理对目标燃料/工况正确。

方法背景：[Cantera 官方点火延迟示例](https://cantera.org/stable/examples/python/reactors/non_ideal_shock_tube.html)。
该页面中的真实气体和 OH 定义与本案例不同，未复制其数据或将其数值当本案例基准。
