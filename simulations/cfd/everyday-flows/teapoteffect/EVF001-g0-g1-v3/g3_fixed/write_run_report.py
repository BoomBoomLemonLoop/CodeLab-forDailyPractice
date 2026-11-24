"""Compile this run's evidence; requires both successful startup reports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
g2=json.loads((ROOT.parent/'artifacts/g2_momentum/convergence_report.json').read_text())
lines=['# EVF-001 G2→G3 实际验证报告（2026-11-22）','',
'已完成两个真实三维实体网格、非零非均匀入口、水相初始场的 OpenFOAM v2606 最小 VOF 启动测试。两组终止时刻均为 0.0002 s，interFoam 退出码 0。状态为 Tested startup；物理 Validated 尚未达到。旧 G0/G1 与旧 OpenFOAM 成果保留，无提交、推送或合并。','',
'## G2 数值验证','',
'Q=10 mL/s 是探索性假设；精确满足流量是归一化约束，不是实验验证。G 是净轴向驱动力，dp/ds 已计入局部重力。','',
'|工况|名义步长 mm|面积 mm²|Umax m/s|G Pa/m|dp/ds Pa/m|Q mL/s|',
'|---|---:|---:|---:|---:|---:|---:|']
for name,case in g2['cases'].items():
    for row in case['levels']:
        lines.append(f'|{name}|{row["nominal_spacing_m"]*1000:.1f}|{row["area_m2"]*1e6:.6f}|{row["U_max_m_s"]:.8f}|{row["G_Pa_m"]:.6f}|{row["dp_ds_Pa_m"]:.6f}|{row["Q_m3_s"]*1e6:.8f}|')
lines+=['','Case 1/2 由0.2到0.1 mm的 Umax 变化分别为0.2452%/0.1361%，净驱动力变化0.2938%/0.2495%。相对最细网格的速度剖面 L2 差：Case 1 为1.6708%→0.5098%，Case 2 为0.4728%→0.2213%。阶梯边界使压力梯度和面积不严格单调，不能据此宣称圆角截面二阶收敛。',
'独立矩形开口通道 Fourier 解析解基准的速度 L2 误差为0.6858%、0.1887%、0.04745%，支持离散实现的约二阶精度；仅是 numerical verification。坐标变换往返误差约1e-16。',
'证据：[完整验证 JSON](../artifacts/g2_momentum/convergence_report.json)、[剖面图](../artifacts/g2_momentum/convergence_profiles.png)。','',
'## 真实几何、网格与坐标','',
'使用原 geometry.py 的 solid_mesh：中央 R5 mm、壁厚1.2 mm、出口独立 R0.6 mm，包含内壁、出口包边、外壁及侧缘封口。STL 由 surfaceCheck 检查；没有用背景盒子冒充壶嘴。流体域为该实体之外、s从0.8L到70 mm、y为±30 mm、w为−20到45 mm的连通空气/水域。',
'入口 s=38.3103998091 mm，外法向(-1,0,0)；G2水面高度 w=4.528134956/14.124298359 mm。入流区 waterInlet 与其余开放空气 inlet 共面；外部其余边界 atmosphere 开放。实体统一 wall patch spout 包含内壁、出口和外壁，尚未拆分为独立诊断 patch。',
'局部 U=(Us,0,0)，世界 U=R_y(-beta)U，beta=25/55°；g_local=(-9.81 sin beta,0,-9.81 cos beta)。几何固定，边界时间不变；没有动态网格。',
'背景网格124800单元，经实际 snappyHexMesh 生成229160单元；干燥入口上缘10个退化单元通过只删除内部公共面的保守合并修复，最终两组均229150单元，物理边界点、面不移动。修复前后网格和日志均保留。',
'标准 checkMesh：Mesh OK。主要指标：最大非正交63.087465°，最大 skewness 2.7134566，最小体积6.0553645e-13 m³，最小 determinant 0.060570031，最小面插值权重0.19048882。',
'扩展 checkMesh -allTopology -allGeometry：仍 Failed 1 mesh checks，9420凹单元；另有670凹面诊断。不能称为完整质量验证通过。当前无边界层，最小边长约30.7 μm不代表全圆角或液膜均达到该分辨率。',
'已查看两组 mesh_and_inlet.png：可辨认中央弧形内壁、出口包边与外壁；入口液相覆盖随工况变化，初始水只在内部。中心平面图显示出口R0.6附近局部网格。该检查不等于CAD误差或界面网格独立性认证。','',
'## 入口映射和实际求解','',
'|指标|Case 1（25°）|Case 2（55°）|','|---|---:|---:|']
data=[]
for name in ('case1','case2'):
    case=ROOT/'cases'/f'{name}_smoke_ready'
    data.append((json.loads((case/'mapping_report.json').read_text()),json.loads((case/'startup_results.json').read_text())))
for title,fun in [
    ('含水入口面数',lambda m,r:f'{m["wet_faces"]}'),
    ('实际入口覆盖 mm²',lambda m,r:f'{m["wet_area_m2"]*1e6:.6f}'),
    ('映射前 Q 偏差 %',lambda m,r:f'{(m["raw_mapped_Q_m3_s"]/1e-5-1)*100:.6f}'),
    ('归一化系数',lambda m,r:f'{m["normalization_factor"]:.9f}'),
    ('映射后 Q 相对误差',lambda m,r:f'{m["relative_Q_error"]:.3g}'),
    ('求解器实际平均入口水量 mL/s',lambda m,r:f'{-r["patch_water_flux"]["waterInlet"]["mean_outward_water_Q_m3_s"]*1e6:.9f}'),
    ('最大记录 Co',lambda m,r:f'{r["max_Co_logged"]:.6f}'),
    ('alpha 最小/最大',lambda m,r:f'{r["alpha_min_all_logged"]:.5g} / {r["alpha_max_all_logged"]:.8g}'),
    ('初始水量 mL',lambda m,r:f'{r["initial_water_m3"]*1e6:.9f}'),
    ('末时水量 mL',lambda m,r:f'{r["final_water_m3"]*1e6:.9f}'),
    ('水量残差/累计供水 %',lambda m,r:f'{r["balance_relative_to_supplied_water"]*100:.7f}'),
    ('末时全域最大速度 m/s',lambda m,r:f'{r["final_max_speed_m_s"]:.6f}'),
    ('末时 alpha>0.5 区最大速度 m/s',lambda m,r:f'{r["final_max_speed_alpha_gt_half_m_s"]:.6f}')]:
    lines.append('|'+title+'|'+'|'.join(fun(*item) for item in data)+'|')
lines+=['','Case 1 首轮使用面内6细分，保留已运行数据；额外3/6/12/24/48细分审计显示24→48通量变化0.0088%，但6与48结果仍有约0.73%差异。Case 2实际使用48细分，24→48变化0.0142%。当前默认映射已升至48细分；两组仅作启动测试，不以此直接进行物理差异归因。',
'归一化保持每面非均匀速度形状，未用峰值代替整片入口。部分含水面允许混合物速度携带少量空气；实际水相通量由 alpha 和面通量共同决定。',
'水量核验使用 OpenFOAM writeCellVolumes 得到的 V，并以求解器 rhoPhi/phi 重建子循环平均水相通量。残差包含ASCII写出精度和时间记录精度。Co目标0.25具有自适应滞后，启动时峰值达到0.285/0.399，未严格保持目标，需要更保守时间步复核；alpha存在轻微数值超界，未人为裁剪原结果。',
'第一次 Case 1 启动因 volFieldValue 缺 writeFields 失败，已修正并保存 log.interFoam.attempt1；随后两组均实际执行至 End。WSL 的重复user.default/网络回退警告未阻止运行，没有修改Windows安全设置或WSL配置。','',
'## 文件、测试和局限','',
'- 修改 g2_momentum.py：加入可检验的矩形解析基准入口与黏度参数；新增 verify_g2.py 和 convergence_report.json / convergence_profiles.png。',
'- 完善 make_cases.py：真实STL、准确入口位置、局部网格、固定重力、短时控制。',
'- 新增 foam_io.py / test_mapping.py：ASCII网格、几何积分和3项已通过的独立数值测试。',
'- 新增 mesh_case.sh / merge_corner_cells.py / patch_case.sh：实际网格执行、保守修复、入口分区与质量检查。',
'- 新增 map_inlet.py / set_fixed_state.py：真实面映射、非零U/alpha及内部水相初始化。',
'- 新增 prepare_smoke.py / run_solver.sh / cell_volumes.sh / analyze_smoke.py：v2606兼容配置、实际求解及守恒核验。',
'- 新增 inspect_case.py：实际网格/入口图、求积精度审计、ParaView入口 view.foam。',
'- 每个 *_smoke_ready 内保留实际网格、0场、时间目录、监测数据、完整日志、mapping_report.json、startup_results.json、quadrature_audit.json、mesh_repair.json、mesh_and_inlet.png。生成的大型中间文件本地保留并由.gitignore排除。',
'- [准确运行命令与模型方程](RUN_VERIFIED_WORKFLOW.md)。本轮 verify_g2.py、3项单元测试、blockMesh、surfaceCheck、surfaceFeatureExtract、snappyHexMesh、createPatch、两类checkMesh、interFoam、writeCellVolumes、两案例后处理均实际运行。','',
'仍未完成：扩展网格凹单元问题、层网格与自由界面分辨率、局部网格/时间步/入口模型独立性、压力与入口发展的物理合理性、接触角校准。截面G2已数值求解，但10mL/s及60°接触角并非实测；绝对姿态也保留研究约定。',
'0.2 ms 属启动瞬态，液体尚未经历足够的出口发展时间。尚未验证外壁湿润面积、附壁长度、脱离位置或准稳态。不能用此结果宣布存在/不存在 Teapot Effect。下一步先统一48细分入口并解决扩展网格质量，再研究足够时长及敏感性。']
(ROOT/'G2_G3_ACTUAL_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(ROOT/'G2_G3_ACTUAL_RUN_REPORT.md')
