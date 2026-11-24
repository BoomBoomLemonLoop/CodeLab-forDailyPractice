# 固定壶嘴非稳态运行与诊断（2026-11-24）

旧 `*_smoke_ready` 不覆盖。新计算为 `case1_transient_v1`、`case2_transient_v1`，同一实体、固定25/55°姿态、相同水气物性/60°接触角/R0.6出口。两组入口均更新为48细分积分，仍按假设10mL/s归一化，从原先水相种子重新开始，避免混用两种入口积分下的时间历史。

## 已实施的数值设置

maxCo=0.10，maxAlphaCo=0.05，maxDeltaT=5e-6 s；Euler时间格式、vanLeer alpha输运、界面压缩cAlpha=1；MULESCorr=yes，nAlphaSubCycles=2，nAlphaCorr=2，nLimiterIter=10，压力非正交修正1次。监测每一步alpha/U极值及位置、全部开放边界phi/rhoPhi、域内水量。8个MPI进程/算例，Scotch分区。每1ms写出完整场。

分区时发现旧snappy诊断场 cellLevel/pointLevel 未跟随保守单元合并和createPatch更新。新案例中将它们移至mesh_generation_metadata，保留失败日志后重新分区。静态interFoam不需要这两个网格生成诊断场；没有删除真实U/alpha/p_rgh。

已检查本机 `/usr/lib/openfoam/openfoam2606/applications/solvers/multiphase/VoF/alphaEqn.H` 的预测、MULES修正和日志输出顺序。日志中的所有Min/Max不能混同为最终保存场：旧案例所有已存时刻内部alpha在1e-8容差内，但未存储的中间预测/修正步骤无法事后恢复空间位置。新计算的fieldMinMax记录最终步极值位置；完整场用于超界单元数统计。

## 物理时间依据

启动后在约3ms附近将时间步上限从5e-6提高到1e-5 s，仍保持maxCo=0.10、maxAlphaCo=0.05。各案例 adaptive_cap_change.log 记录修改时已观察到的时间，原控制字典保存在system/controlDict.initial_cap。依据：已保存1ms界面单元的最小体积尺度约91µm，对应量纲毛细时间约0.102ms；1e-5仍显著更小，并继续由实际Co自动约束。这是自适应时间步上限调整，**不是时间步独立性验证**，不能由该量纲估算宣称绝对稳定。

入口到圆角接缝9.5776mm。Q/A平均速度约0.283/0.0515m/s，名义轴向对流时间约0.034/0.186s；R=0.6mm毛细时间sqrt(rho*R³/sigma)=1.73ms。

首个窗口10/25ms覆盖至少5个毛细时间和2R/Umean，研究已有初始水相在圆角附近的最初演化。它们短于完整通道对流时间，不能作为充分发展的证据。完整发展参考时长3tau约0.10/0.56s；是否继续应结合实际流量、储水变化、界面、湿区稳定性及网格可信度，不能仅达到预设时长就认定准稳态。

Case 1 的10ms检查点尚无外壁湿润、供水仍主要积累，因此已从该检查点接续至40ms目标（约1.18个入口对流时间），每2ms保存场。第一段日志log.interFoam保留，第二段为log.interFoam.window2。并行重启直接使用已存processor时间场，不重新初始化水相。完整水量核验读取postProcessing下0和0.01两个运行段。40ms是目标，是否完成必须查日志和实际场。

## 命令

PowerShell，位于v3目录：

```powershell
$py='D:\CodeLab-forDailyPractice\.venv\Scripts\python.exe'
& $py g3_fixed/audit_transient.py g3_fixed/cases/case1_smoke_ready
& $py g3_fixed/concavity_depth.py g3_fixed/cases/case1_smoke_ready
& $py -m unittest discover -s g3_fixed -p 'test*.py'
```

`prepare_transient.py` 拒绝覆盖现有目录。新建测试时使用新的版本名（修改脚本里的目标后缀），然后执行map_inlet --map，再调用并行脚本。已有运行不要重复执行这个创建步骤。

WSL OpenFOAM-Ubuntu，位于v3目录：

```bash
bash g3_fixed/run_parallel_transient.sh "$PWD/g3_fixed/cases/case1_transient_v1"
```

该脚本拒绝覆盖已有log.interFoam；运行结束后自动重构场并导出OpenFOAM体积。进行中只重构已经完整写出、并且当前求解时刻已超过的检查点，例如：

```bash
bash g3_fixed/reconstruct_and_export.sh "$PWD/g3_fixed/cases/case1_transient_v1" "$PWD/g3_fixed" 0.001
```

PowerShell后处理：

```powershell
& $py g3_fixed/postprocess_transient.py g3_fixed/cases/case1_transient_v1
& $py g3_fixed/audit_transient.py g3_fixed/cases/case1_transient_v1
& $py g3_fixed/plot_transient.py g3_fixed/cases/case1_transient_v1
```

## 指标定义与限制

- 凹单元审计：定位checkMesh输出集合，并计算各单元顶点超过外向面心平面的最大距离。此量用于严重程度比较，不替代OpenFOAM质量判据。底部出口附近最大约0.125mm，不能认为无影响；扩展checkMesh未通过这一点保持记录。
- 实际界面：已安装ParaView的pvpython读取真实OpenFOAM时间场，cell-to-point插值后提取alpha=0.5等值面，输出VTP/NPZ、三维图和动画。不是几何水平液面的动画。亚网格薄膜可能不出现在0.5等值面中。
- 壁面分类：用原实体内表面的解析有符号距离与真实网格面法向区分内/外壁，出口s≈L单独标识；侧面封边不纳入外壁主体。局部网格偏离和非平面面会影响分类。
- 湿润面积：对真实外壁边界面的alpha分别以0.1/0.5/0.9阈值计面积，同时记录积分alpha*dA。仅为VOF壁面含水指标，不是实验接触线。
- 附壁长度：与含水出口面经共享边连通的含水外壁区域，取L−min(s_face)。排除孤立液滴。该长度是轴向投影，未加上πR，也不是沿任意三维流线的弧长。
- 圆角与平直外壁分别统计：从内侧接缝附近(theta<20°)的含水面出发，沿圆角/外壁共享边追踪连通湿区，另报theta>90°的圆角下半部湿润面积、最大连通角度及R*theta弧长。平直外壁面积为零并不意味着圆角上完全没有附着。raw最大湿润角另行保留；细膜若低于阈值可能被离散连通性判据漏掉。
- 输出的contact_front为该连通湿区最上游面心，表示湿区边缘候选；不能自动等同于水流脱离位置。真正的脱离必须结合自由界面离壁、局部速度方向、连续时间证据，若未辨认则保持未确定。
- 水量：V来自OpenFOAM，所有开放边界水相通量由(rhoPhi−1.2phi)/(998−1.2)求得，按子循环平均通量逐步累计；固壁通量为零。报告域内水量变化加累计净流出，不能只比较指定入口与单个出口。
- 局部出流诊断：`pvpython g3_fixed/export_section_flux.py <case>`在中央母线势能crest对应s平面和s=L+R+0.1mm平面上，用VTK切割真实流体网格，积分线性节点alpha与U_s的乘积。这是插值诊断，不能代替求解器的守恒面通量；极小非零值可能来自弥散界面，必须结合alpha=0.5等值面判断。
- 初始p_rgh=0且水相为单元中心判定种子，存在启动调整；小时间窗中的差异同时包含初始水量、覆盖和重力差异，不能单因子归因。

已实现/数值测试不等于物理验证。详细实际运行状态和数据必须以本轮结果报告及日志为准。

## Case 2 分阶段接续与完整几何视图

Case 2第二段使用已有processor检查点0.025 s，`startFrom latestTime`，首个目标0.050 s，保存间隔0.005 s；原controlDict保存在`system/controlDict.window1`。固定55°、网格、重力、入口覆盖/U/10mL/s及物性不变。目标时刻不是完成证据，以log.interFoam.window2的End、execution_status.log和已重建场为准。

```bash
bash g3_fixed/continue_parallel.sh "$PWD/g3_fixed/cases/case2_transient_v1" window2
# 上述标签已有日志时会拒绝重复执行。先检查运行状态，不要重复启动求解器。
pvpython g3_fixed/export_interfaces.py g3_fixed/cases/case2_transient_v1
pvpython g3_fixed/export_section_flux.py g3_fixed/cases/case2_transient_v1
```

```powershell
& $py g3_fixed/postprocess_transient.py g3_fixed/cases/case2_transient_v1
& $py g3_fixed/audit_transient.py g3_fixed/cases/case2_transient_v1
& $py g3_fixed/plot_transient.py g3_fixed/cases/case2_transient_v1
& $py g3_fixed/plot_full_spout.py g3_fixed/cases/case2_transient_v1
& $py g3_fixed/compare_development.py
```

`plot_full_spout.py`直接读取案例中的完整原始STL，并叠加实际VOF界面；红线标记局部CFD入口。上游s<0.8L只有几何背景，没有求解或补造水相。上下两个视角用于观察内壁和圆角下侧，与出口近景共同检查；坐标是局部坐标，固定55°通过重力体现。

`compare_development.py`用tau=(L−s_in)/U_mean计算平流时间（Case 1约33.785ms、Case 2约185.802ms），同时输出物理时间与t/tau曲线。首次出流/下侧润湿仅按相邻保存帧给出事件区间。内部储水采用几何单元中心掩膜，是发展诊断而非精确局部控制体守恒。

凹单元审计新增液相及界面与低洼出口凹单元的重叠计数。重叠能说明缺陷处于活跃流动区域，不能定量证明其误差大小；即使alpha有界，也不能排除曲率、接触角和速度的网格偏差。脱离位置保持未确定，除非连续界面和速度证据足以识别，不能把湿润前沿直接改名为脱离点。
