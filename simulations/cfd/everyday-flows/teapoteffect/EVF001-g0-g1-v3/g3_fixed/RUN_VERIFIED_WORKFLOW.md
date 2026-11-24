# 实际执行工作流（2026-11-22）

本目录属于原 v3 工程。G0/G1、历史算例不修改。以下命令在 v3 根目录执行；已有案例目录禁止重新生成或覆盖。`case1_smoke_ready` / `case2_smoke_ready` 是本轮数据，短时结果不构成物理验证。

## Python 验证与查看

PowerShell：

```powershell
Set-Location D:\CodeLab-forDailyPractice\simulations\cfd\everyday-flows\teapoteffect\EVF001-g0-g1-v3
$py = 'D:\CodeLab-forDailyPractice\.venv\Scripts\python.exe'
& $py verify_g2.py
& $py -m unittest discover -s g3_fixed -p test_mapping.py
& $py g3_fixed/inspect_case.py g3_fixed/cases/case1_smoke_ready
& $py g3_fixed/analyze_smoke.py g3_fixed/cases/case1_smoke_ready
```

使用 ParaView 打开案例内 `view.foam`；勾选内部网格、spout 和 waterInlet，选择 `alpha.water` 或 `U`，使用时间控件。`mesh_and_inlet.png` 是实际边界网格和初始场检查图，不是几何示意图。

## 新的可复现测试（避免覆盖已有结果）

```powershell
& $py g3_fixed/make_cases.py --case case1 --label reproduce
```

WSL Ubuntu 终端（实际发行版名 `OpenFOAM-Ubuntu`，非 Ubuntu-24.04）：

```bash
cd /mnt/d/CodeLab-forDailyPractice/simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3
bash g3_fixed/mesh_case.sh "$PWD/g3_fixed/cases/case1_reproduce"
```

这依次运行 `blockMesh`、`surfaceCheck`、`surfaceFeatureExtract`、`snappyHexMesh -overwrite`、完整 `checkMesh`。不能仅依据 checkMesh 的进程返回码判断成功，必须阅读日志末尾与失败集合。本轮原始网格在干燥入口上缘发现 10 个行列式退化单元；保留原网格，将它们与内部邻单元保守合并，保持全部实体边界顶点和面：

```powershell
& $py g3_fixed/merge_corner_cells.py g3_fixed/cases/case1_reproduce g3_fixed/cases/case1_reproduce_ready
& $py g3_fixed/map_inlet.py g3_fixed/cases/case1_reproduce_ready --split --quadrature 48
```

合并程序只适用于通过位置断言的干燥上缘退化单元，不是任意坏网格的通用修复器。若新网格不满足断言，应诊断真实日志。

```bash
bash g3_fixed/patch_case.sh "$PWD/g3_fixed/cases/case1_reproduce_ready"
```

```powershell
& $py g3_fixed/map_inlet.py g3_fixed/cases/case1_reproduce_ready --map --quadrature 48
& $py g3_fixed/prepare_smoke.py g3_fixed/cases/case1_reproduce_ready
```

```bash
bash g3_fixed/run_solver.sh "$PWD/g3_fixed/cases/case1_reproduce_ready"
bash g3_fixed/cell_volumes.sh "$PWD/g3_fixed/cases/case1_reproduce_ready"
```

```powershell
& $py g3_fixed/analyze_smoke.py g3_fixed/cases/case1_reproduce_ready
& $py g3_fixed/inspect_case.py g3_fixed/cases/case1_reproduce_ready
```

在 PowerShell 直接调用任一 bash 脚本的等效形式：

```powershell
wsl -d OpenFOAM-Ubuntu bash /mnt/d/CodeLab-forDailyPractice/simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/g3_fixed/run_solver.sh /mnt/d/CodeLab-forDailyPractice/simulations/cfd/everyday-flows/teapoteffect/EVF001-g0-g1-v3/g3_fixed/cases/case1_reproduce_ready
```

Case 2 在 Case 1 跑通后复用同一个局部坐标实体网格：将未分割入口的原始 snappy 案例通过 `merge_corner_cells.py` 写入新的 Case 2 目录，执行 `set_fixed_state.py <新目录> case2`，然后依次 split、patch_case、map、prepare_smoke、run_solver、cell_volumes、analyze_smoke。`set_fixed_state.py` 拒绝修改已有求解日志的案例。

## 模型、单位和限制

- 几何与速度全部 SI。局部 x=s，y 为横向，z=w；入口平面 s=0.8L=0.0383103998091 m，流体域入口外法向 (-1,0,0)。实体在此坐标中固定，旋转重力而非网格。
- 世界坐标 X=R_y(-beta)x，U_world=R_y(-beta)U_local；g_local=(-g sin beta,0,-g cos beta)。Case 1/2 分别 beta=25/55°。
- G2 求解局部直通、稳态、层流、单向截面动量方程：`-mu laplacian(U_s)=G=-dp/ds+rho*g_s`，固壁无滑移、平自由液面零切向应力。以假设 Q=10 mL/s 反推 G 和 dp/ds；这不是测量水头或全壶动力学求出的压力梯度。
- G2 的已发展截面近似没有包含真实三角侧面沿程变化、入口发展长度、气相剪切及曲率诱导横流。G3 随后自行求解三个速度分量；不能把 G2 称为真实壶嘴三维流场。
- 入口逐多边形求积，插值 G2 细网格速度，分别计算水相面积分数和水相平均速度，再以实际面向量重新积分并归一化 Q。部分含水面使用一套混合物速度，因此也带入一部分空气；不等同于精确解析的面内两相速度。
- 初始水相仅布置在内部、自由液面下的单元中心，外壁邻近空气保持干燥。初始压力为零 p_rgh，经投影调整；初始场不是稳态解，启动扰动不可用于附壁结论。
- 水/空气 rho=998/1.2 kg/m³，nu=1e-6/1.5e-5 m²/s，sigma=0.072 N/m，静态接触角60°为探索参数；R0.6 mm 出口来自原实体，两组相同。
- `rhoPhi` 是求解器实际混合物质量通量，水相通量按 `(rhoPhi-rho_air*phi)/(rho_water-rho_air)` 提取。以子循环平均通量在时间步上积分，与实际 OpenFOAM 单元体积求得的水量变化核对。
- 当前网格无棱柱边界层；完整诊断仍存在凹单元。0.0002 s 只测试启动；未完成准稳态、接触线网格独立性、时间步独立性、外壁湿润/脱离指标验证。

状态：Implemented / Tested（见每案例日志与 JSON）；物理 Validated：否。不得将该短时测试称为 Teapot Effect 复现。
