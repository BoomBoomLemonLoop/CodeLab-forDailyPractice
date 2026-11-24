# 实际实施记录 2026-11-22

本轮保持既有几何、两组固定姿态和 10 mL/s 探索性流量。

## G2

新增 `g2_momentum.py`：在真实圆角截面液相区域的阶梯离散上求解
`-laplacian(psi)=1`，固壁无滑移、顶部零剪切；通过积分将速度归一化至 Q。
驱动力 `G=mu*C`，压力梯度 `dp/ds=rho*g_s-G`，单位 Pa/m。
物性 rho=998 kg/m³、mu=0.000998 Pa s 为显式代码参数，Q 默认 1e-5 m³/s。
未模拟空气切向剪切或沿程变截面发展，不能称为整个壶嘴的充分发展解。

实际运行：
```
.venv/Scripts/python.exe simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/g2_momentum.py
```

输出 `artifacts/g2_momentum/` 两组 CSV、NPZ 和 verification.json。
CSV/NPZ 提供三分量局部速度及液相掩码。0.4/0.2/0.1 mm 三级计算均收敛，
相对线性残差小于 1e-9。最细网格 Case1/2 面积约 35.3203/194.0881 mm²，
峰值速度 0.570207/0.105905 m/s，驱动力 102.7445/3.75536 Pa/m，
dp/ds=-4240.338/-8023.565 Pa/m。Q=10mL/s 是归一化约束，不是独立物理验证。
相邻两细级峰值速度变化约 0.25%/0.14%。曲边阶梯误差尚存。
尚缺解析基准自动测试、真实 patch 面积分及入口模型对 VOF 结果的敏感性。

## G3

修复 `g3_fixed/make_cases.py` 的 Python 多行返回语法错误，并实际运行生成
`g3_fixed/cases/case1_fixed` 与 `case2_fixed`。
包含真实 STL、背景网格、snappy 配置、重力、物性和数值字典。
**这些案例仍未完成入口映射：入口零值尚未替换，不能运行后声称获得供水解。**
当前背景盒入口 x=-0.012m 与 G2 s=0.0383104m 不一致，需要先重构局部域截断和入口/空气分区。
不可直接把 G2 数据写到这个错误位置的入口。实体仍是原始完整 STL，需检查上游切面与流体域连通性。
未完成网格贴体检查、液相种子初始化、壁面诊断或 interFoam 运行。

## WSL

`wsl --list --quiet` 实际返回 `OpenFOAM-Ubuntu`。
`Ubuntu-24.04` 不是本机发行版名称，该调用的错误为 WSL_E_DISTRO_NOT_FOUND。
未改变任何 Windows 安全设置或 WSL 配置。
当前正确加载命令：
```
wsl -d OpenFOAM-Ubuntu bash -lc 'source /usr/lib/openfoam/openfoam2606/etc/bashrc; foamVersion; command -v interFoam'
```
本轮已提交 blockMesh/checkMesh 背景网格调用；实际日志保存在 case1_fixed/log.*。
该背景网格即使通过，也不代表真实贴体网格或 VOF 已通过。

所有新增内容未提交、推送或合并。下一步必须修正域入口位置、贴体网格及实际面映射，之后才能执行有意义的非零进料测试。

## 2026-11-22 实际衔接与启动测试更新

以上为上一轮历史记录，保留不删除。当前已完成 G2 三级离散及独立 Fourier 解析基准核验；真实 STL 贴体网格、s=0.8L 入口、非零非均匀速度与液相覆盖映射均已实际实现。

Case 1/2 新案例为 `g3_fixed/cases/case1_smoke_ready` / `case2_smoke_ready`，均229150单元，标准 checkMesh 为 Mesh OK，interFoam v2606 实际正常运行到0.0002 s。扩展网格检查仍有凹单元，未完成物理验证，未宣称 Teapot Effect。

本轮以 [G2/G3实际验证报告](g3_fixed/G2_G3_ACTUAL_RUN_REPORT.md) 和 [可复制运行说明](g3_fixed/RUN_VERIFIED_WORKFLOW.md) 为状态与证据入口。完整日志、初始场、时间场、通量及质量守恒数据保存在各新案例内。旧 fixed 案例与其背景网格未覆盖。

## 2026-11-24 非稳态计算与角速度对照

正式阶段分析记录为 `case1_transient_v1` 至0.040 s、`case2_transient_v1` 至0.025 s。保留原启动测试案例。当前证据入口为 [非稳态结果报告](g3_fixed/G3_TRANSIENT_RESULTS.md) 和 [运行与后处理说明](g3_fixed/TRANSIENT_RUNBOOK.md)。

Case 1末时圆角下半部连通湿区面积7.20758 mm²，连通湿润角167.965°、弧长1.75892 mm（alpha≥0.5）；直段外壁在alpha≥0.5下未检出润湿，但alpha≥0.1阈值有0.215314 mm²含水区域，尚不能确认可分辨液膜。圆角后s=L+0.7mm截面插值水相通量8.51063 mL/s，属于非守恒截面诊断；完整边界水量平衡残差约−0.004548%累计供水。湿区仍在发展，未确认稳定脱离点或准稳态。Case 2仍未形成可分辨的越过圆角出流，不能据此断言没有Teapot Effect。

8项轻量数值测试实际通过。9420凹单元（低洼出口附近832个）影响尚未排除，未完成网格、时间步独立性及实验验证。场图、VTP界面、GIF动画与逐时湿润指标已输出至各案例。

用户指定的壶体角速度10→5°/s已作为独立几何时间重参数化输出到 `artifacts/angular_rate_5deg_s`：Case 1事件历时6 s、Case 2为3 s；121个进度点对照通过。入口水速及假设流量10mL/s没有减半。固定姿态G3尚无角速度到水头/流量的动力学耦合，不能用本次VOF结果宣称验证了真实减速倾倒的效应。本段记录形成时未提交、推送或合并Git。

### 2026-11-24 Case 2 后续窗口记录核对

Case 2 的正式阶段观察仍以0.025 s为准。后续窗口的 `log.interFoam.window2` 在0.05 s后记录 `End`，`log.reconstructPar.window2` 重构到0.05 s并记录 `End`，`execution_status.log` 记录求解和重构退出码均为0。因此日志支持后续窗口运行与重构成功至0.05 s；这不等于流场充分发展。

汇总文件不同步：`log_statistics.json` 在后续窗口前生成，latest time为0.025 s；`CASE_STATUS.json` 与 `transient_metrics.csv/json` 更新于11:04:59并记录至0.03 s，`numerical_audit.json` 更新于11:05:09；后续求解日志时间为11:24、重构日志为11:26。0.035–0.05 s重构目录仅含`alpha.water`、`p_rgh`、`U`，没有相应通量字段或更新后处理指标/审计结论。本次保留全部本地场、日志与状态文件；本报告不将0.025 s之后的数据用于物理解释。
