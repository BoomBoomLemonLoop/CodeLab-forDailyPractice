"""Compile only computed evidence; never promote a target time to a result."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
lines=['# EVF-001 固定壶嘴非稳态结果记录（2026-11-24）','',
'本报告区分已计算场、解释与未验证假设。旧G0/G1和最小运行案例保留；未提交、推送或合并Git。25°/55°固定姿态、物性、60°接触角、R0.6mm出口保持一致。10mL/s仍是探索性输入。','',
'## 已计算时间场与指标','',
'下表时间来自实际重构并后处理的场，不是controlDict目标时间。附壁长度是出口连通外壁湿区的轴向长度，不是自动识别的真实脱离位置。','',
'|指标|Case 1|Case 2|','|---|---:|---:|']
data=[]
for name in ('case1','case2'):
    case=ROOT/'cases'/f'{name}_transient_v1'
    subprocess.run([sys.executable,str(ROOT/'log_statistics.py'),str(case)],check=True,capture_output=True)
    records=json.loads((case/'transient_metrics.json').read_text())['series']
    stats=json.loads((case/'log_statistics.json').read_text())
    data.append((records,stats))
for title,fn in [
    ('最后分析时刻 s',lambda r,s:f'{r[-1]["time_s"]:.6g}'),
    ('日志已推进时刻 s（可能晚于重构场）',lambda r,s:f'{s["latest_solver_time_s"]:.6g}'),
    ('初始水量 mL',lambda r,s:f'{r[0]["water_volume_m3"]*1e6:.7f}'),
    ('末时水量 mL',lambda r,s:f'{r[-1]["water_volume_m3"]*1e6:.7f}'),
    ('累计水量残差/累计供水 %',lambda r,s:f'{r[-1]["water_balance_residual_m3"]/(1e-5*r[-1]["time_s"])*100:.6g}'),
    ('直段外壁面积 alpha≥0.1/0.5/0.9，mm²',lambda r,s:' / '.join(f'{r[-1][f"outer_area_alpha{x}_m2"]*1e6:.6g}' for x in (.1,.5,.9))),
    ('出口连通外壁湿区长度 alpha≥0.5，mm',lambda r,s:f'{r[-1]["attached_length_alpha0.5_m"]*1000:.6g}'),
    ('连通下半圆角湿润面积 alpha≥0.5，mm²',lambda r,s:f'{r[-1]["connected_lower_lip_area_alpha0.5_m2"]*1e6:.6g}'),
    ('连通圆角湿润角 alpha≥0.1/0.5/0.9，deg',lambda r,s:' / '.join(f'{r[-1][f"connected_lip_angle_alpha{x}_deg"]:.5g}' for x in (.1,.5,.9))),
    ('末时圆角最大湿润角，deg',lambda r,s:f'{r[-1]["max_wet_lip_angle_deg"]:.6g}'),
    ('最下游 alpha>0.5 单元 s，mm',lambda r,s:f'{r[-1]["maximum_liquid_s_m"]*1000:.6g}'),
    ('末时内部 alpha 最小/最大',lambda r,s:f'{r[-1]["alpha_min"]:.4g} / {r[-1]["alpha_max"]:.12g}'),
    ('末时超出[0,1]容差1e-8 / 1e-6单元数',lambda r,s:f'{r[-1]["alpha_outside_1e8_count"]} / {r[-1]["alpha_outside_1e6_count"]}'),
    ('日志最大Co / 界面Co',lambda r,s:f'{s["max_Co"]:.5g} / {s["max_alphaCo"]:.5g}'),
    ('所有输运子步骤最大alpha',lambda r,s:f'{s["all_substep_logged_alpha_max"]:.12g}'),
    ('最终时间步最大alpha',lambda r,s:f'{s["final_step_alpha_max"]:.12g}')]:
    lines.append('|'+title+'|'+'|'.join(fn(*d) for d in data)+'|')
lines+=['','## 出口流动事实与解释边界','']
crest=.045/np.sin(np.deg2rad(70))+.0006
for name,(rows,stats) in zip(('case1','case2'),data):
    passed=[r['time_s'] for r in rows if r['maximum_liquid_s_m']>crest]
    wet=[r['time_s'] for r in rows if r['outer_area_alpha0.5_m2']>1e-12]
    last=rows[-1];previous=rows[-2]
    storage=(last['water_volume_m3']-previous['water_volume_m3'])/(last['time_s']-previous['time_s'])/1e-5
    lines.append(f'- {name}：已存场中，α>0.5单元越过最下游圆角坐标的首次时刻：{passed[0] if passed else "尚未观察到"}；外壁α≥0.5面积首次非零时刻：{wet[0] if wet else "尚未观察到"}。最后两个保存时刻的储水增长率/Q约{storage:.4g}。')
    lower=[r['time_s'] for r in rows if r['connected_lower_lip_area_alpha0.5_m2']>1e-12]
    lines.append(f'  下半圆角连通湿区首次非零保存时刻：{lower[0] if lower else "尚未观察到"} s；末时湿润弧长（α≥0.5）为{last["connected_lip_arc_alpha0.5_m"]*1000:.5g} mm。这属于圆角下侧附壁，须与直段外壁面积分别报告。首次事件仅由离散保存时刻定位。')
    lines.append(f'  末时湿润前沿候选局部坐标（m）：{last.get("lip_front_candidate_alpha0.5_xyz_m")}；邻接流体单元速度（m/s）：{last.get("lip_front_adjacent_U_alpha0.5_m_s")}。该速度不是无滑移壁面速度，候选前沿不是已确认的稳定脱离点。')
    flux_path=ROOT/'cases'/f'{name}_transient_v1'/'section_flux_diagnostic.json'
    if flux_path.exists():
        flux=json.loads(flux_path.read_text())['series'][-1]
        lines.append(f'  截面诊断时刻{flux["time_s"]:.6g} s：圆角下游s=L+0.7mm的插值水相通量为{flux["beyond_lip_Q_m3_s"]*1e6:.6g} mL/s。这是线性插值截面诊断，不是求解器守恒面通量；全域质量平衡仍使用rhoPhi。')
lines+=['','尚不自动认定准稳态或Teapot Effect。只有界面确实绕过出口并持续沿外壁发展，才能讨论附壁；湿区边缘也不必等于自由液流的脱离点。需要联合检查VTP界面、速度和连续时间帧。全域包含下游空气，因此整体水量增长可能是射流在空气区延伸，不能单凭全域储水增长判定壶嘴没有持续出流。应联合内部出口截面通量、壶嘴内部储量和湿区变化判断局部发展状态。',
'物理解释候选：几何自由液面到达出口crest仅是G0/G1事件，不保证含表面张力/接触角的VOF立即出流。初始压力投影、毛细调整、重力及入口储水共同影响短时行为；本计算尚未通过独立对照分离这些机制。不能将两组差异单独归因于速度、姿态或倾倒角速度。','',
'## 网格与数值检查','',
'两组229150单元。标准checkMesh通过，但完整检查仍有9420凹单元；出口±1mm区域4058个，低洼出口(w<3mm)832个。后者面平面侵入深度中位数约10µm，95%分位59µm，最大125µm。相对R0.6mm不应忽略，尚未修复或证明其影响可接受。不能据此做网格无关的定量脱离预测。',
'旧0.2ms日志的输运中间步骤超界与保存场不同：全部旧保存场内部alpha在1e-8容差内。新计算保存更高精度，并每一步记录最终极值位置；内部超界位置、数量及与凹单元重叠见numerical_audit.json。日志子步骤并未保存全部空间场，不能伪造其位置。',
'采用maxCo=0.1、maxAlphaCo=0.05、MULES限制迭代10、压力非正交修正1；时间步上限由启动5µs调整为10µs，记录保留。实际Co可能因步内加速超目标，见上表。该调整不是时间步独立性验证。',
'水量平衡使用OpenFOAM单元体积，积分所有开放patch的(rhoPhi−1.2phi)/996.8，壁面不可穿透。重启段按真实时间拼接通量；未只用指定Q代替实际边界通量。','',
'## 5°/s 的独立请求','',
'已生成angular_rate_5deg_s对照，121个相同倾倒进度点验证通过。Case 1事件时间3→6s，Case 2为1.5→3s；终态25/55°和截面相同。没有把入口水速或10mL/s减半。当前G2/G3不含角速度历史，因此这只能证明当前几何模型的时间重参数化，不证明真实流动对角速度不敏感。要研究真实减速效应仍需上游角速度→水头/压力/流量关联。','',
'## 文件与复现','',
'- [运行说明与指标定义](TRANSIENT_RUNBOOK.md)：命令、单位、边界与限制。',
'- audit_transient.py、concavity_depth.py、plot_quality_audit.py：凹单元与超界空间审计；结果保留在案例内。',
'- prepare_transient.py、run_parallel_transient.sh、continue_parallel.sh：新案例和接续求解；原始失败分区日志保留。',
'- postprocess_transient.py、test_transient.py：全部边界水量、真实壁面含水面积、连通湿区前沿；含原映射及三角面通量测试共8项测试实际通过。',
'- export_interfaces.py、plot_transient.py：已安装ParaView提取真实alpha=0.5界面及U，生成VTP/NPZ/PNG/GIF。不是倾倒几何动画。',
'- log_statistics.py、monitor_transient.py：只读日志，区分目标时刻与实际完成时刻。',
'- 每案例transient_metrics.json/csv、log_statistics.json、numerical_audit.json、interface_exports/与transient_figures/为数据入口。',
'- [5°/s验证说明](../artifacts/angular_rate_5deg_s/README.md)。','',
'仍未完成：出口区域凹单元修复/对照、局部网格与时间步独立性、入口模型敏感性、壁面接触角校准、充分发展流动与可靠脱离点确认。当前结果为探索性非稳态计算事实，不是实验验证。']
(ROOT/'G3_TRANSIENT_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(ROOT/'G3_TRANSIENT_RESULTS.md')
