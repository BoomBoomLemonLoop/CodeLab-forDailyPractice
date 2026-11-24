# EVF-001：从模型到数值证据的阅读顺序

这是学习计划，不是已掌握记录。先读原始10°/s，再读5°/s对照；两者共用几何与坐标原理。
当前不存在正在等待完成的5°/s独立VOF算例：固定G3没有角速度输入，尚缺角速度到入口压力/流量的物理关联。
不要求同时读完全部脚本，也不替代Cantera论文主线与Anderson第7章。

|顺序|实际文件（按行内顺序读）|需要弄懂的问题与停止点|
|---|---|---|
|1 研究边界|[最新方案](../EVF001_G2G3_固定入口与固定壶嘴实施方案.md)、[进度](G2_G3_PROGRESS.md)、[实际结果](g3_fixed/G3_TRANSIENT_RESULTS.md)|画出G0/G1→G2→G3数据流；标出测量值、假设、数值解、尚未验证项。旧任务书用于历史追溯，冲突处以新方案及后续明确约束为准。|
|2 参数与坐标|[parameters.json](parameters.json)、[geometry.py](geometry.py)的load_config/rotation_y/world|解释s,y,w与世界坐标、45mm高度如何给出母线长度；推导旋转后重力。先不读网格文件解析器。|
|3 实体构造|geometry.py的profile/surface_grid/solid_mesh、[几何测试](test_geometry.py)|说明三角侧面为何沿s变宽；区分R5内圆角、1.2mm厚度与R0.6出口包边；定位一个对应测试。|
|4 原始10°/s几何运动|geometry.py的history/lip_crest_height/intersections/section_metrics、[生成入口](run_g0.py)、[几何报告](REPORT.md)|Case 1历时3s，Case 2历时1.5s；解释水平液面插值与事件约束，P_geom不是实际流体润湿周长。|
|5 5°/s对照|[angular_rate_comparison.py](angular_rate_comparison.py)、[验证记录](artifacts/angular_rate_5deg_s/README.md)|历时变为6/3s；相同进度的几何相同，截交推进速率减半，不推出液体速度减半。|
|6 G2模型分层|[export_g2_state.py](export_g2_state.py)、[g2_exploratory.py](g2_exploratory.py)、[g2_momentum.py](g2_momentum.py)、[verify_g2.py](verify_g2.py)|先识别探索性10mL/s，再读截面Poisson方程、固壁无滑移/界面零剪切、指定Q归一化和反推驱动力；数值解不等于实测入口。读0.4/0.2/0.1mm收敛报告。|
|7 G2→G3映射|[map_inlet.py](g3_fixed/map_inlet.py)、[test_mapping.py](g3_fixed/test_mapping.py)|s=0.8L入口、外法向、alpha覆盖、三分量U与离散面通量；解释为何映射后还要重新积分Q。|
|8 真实网格与字典|[运行流程](g3_fixed/RUN_VERIFIED_WORKFLOW.md)、[make_cases.py](g3_fixed/make_cases.py)、[merge_corner_cells.py](g3_fixed/merge_corner_cells.py)、[prepare_smoke.py](g3_fixed/prepare_smoke.py)|按blockMesh→snappy→检查→局部修复→入口映射读；识别U/alpha/p_rgh/g和物性。背景网格不等于最终流体网格，Mesh OK不证明网格充分。|
|9 非稳态推进|[运行说明](g3_fixed/TRANSIENT_RUNBOOK.md)、[prepare_transient.py](g3_fixed/prepare_transient.py)、[run_parallel_transient.sh](g3_fixed/run_parallel_transient.sh)、[continue_parallel.sh](g3_fixed/continue_parallel.sh)|解释Co、界面Co、MULES、重启及物理时间尺度；先读命令，不要覆盖已有算例重跑。|
|10 证据与局限|[postprocess_transient.py](g3_fixed/postprocess_transient.py)、[audit_transient.py](g3_fixed/audit_transient.py)、[test_transient.py](g3_fixed/test_transient.py)、[export_interfaces.py](g3_fixed/export_interfaces.py)、[结果报告](g3_fixed/G3_TRANSIENT_RESULTS.md)|推导水量平衡；区分圆角下侧/直段外壁、阈值前沿/真实脱离、瞬态/准稳态。最后再读foam_io.py及绘图工具。|

## 第一次学习：90分钟，只完成坐标与时间核验

来源：本项目parameters.json、geometry.py、angular_rate_comparison.py；没有引用未经核对的教材页码。
关键概念：刚体坐标变换不提供流体动力学闭合。

- 15分钟：读第1项及parameters.json，列出长度m、时间s、角度deg、角速度deg/s的单位。
- 25分钟：推导 L=0.045/sin(70°)，β(t)=β0−ωt，T=(β0−βend)/ω；无平移时R=R_y(−β)，g_local=Rᵀ(0,0,−9.81)。
- 35分钟：自己写一个小函数，输入β和ω，返回旋转矩阵、局部重力、两组事件历时。建议保存在本案例自己的学习笔记旁，不修改生产脚本；先写伪代码，再实现。
- 15分钟：核验并解释，而不是只看运行成功。

输入：β=25°/55°，ω=10/5°/s，端点Case 1为55→25°、Case 2为70→55°。
预期输出：L≈0.047888m；T分别为3/1.5s与6/3s；g_local=(-9.81sinβ,0,-9.81cosβ)m/s²。
验收：max|RᵀR−I|<1e-12；重力模误差<1e-12m/s²；历时误差<1e-12s。
再用自己的话回答：为何角速度减半后，固定姿态G3的入口Q不能直接减半？
完成标准：交出自己的函数、数值检查和解释，之后再进入实体构造；目前状态Planned，未认定用户已完成。
