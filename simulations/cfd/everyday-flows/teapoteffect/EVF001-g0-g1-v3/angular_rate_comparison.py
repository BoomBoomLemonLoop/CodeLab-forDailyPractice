"""User-requested 10 -> 5 deg/s kinematic comparison, WITHOUT rescaling fluid U.

Reuses the existing event-constrained horizontal-plane model. No new geometry,
no dynamic CFD mesh, and no assumed relation between angular speed and Q.
"""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from geometry import ROOT,load_config,history,profile,world,section_metrics

def main():
    original=ROOT/'parameters.json';before=hashlib.sha256(original.read_bytes()).hexdigest()
    fast=load_config();slow=copy.deepcopy(fast)
    out=ROOT/'artifacts/angular_rate_5deg_s';out.mkdir(exist_ok=True)
    for name in ('case1','case2'):
        slow[name]['rate_deg_s']=fast[name]['rate_deg_s']/2
        slow[name]['duration_s']=fast[name]['duration_s']*2
    (out/'parameters_5deg_s.json').write_text(json.dumps(slow,indent=2),encoding='utf-8')
    slow=load_config(out/'parameters_5deg_s.json')
    report=dict(status='TESTED_KINEMATIC_TIME_REPARAMETRIZATION_NOT_FLUID_PREDICTION',
        original_parameters_sha256=before,liquid_flow_rescaled=False,
        free_surface_assumption='Same event endpoints; H interpolated against normalized tilt progress, not mass conservation',cases={})
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for i,name in enumerate(('case1','case2')):
        tau=np.linspace(0,1,121);tfast=tau*fast[name]['duration_s'];tslow=tau*slow[name]['duration_s']
        hf=np.array([history(t,name,fast) for t in tfast]);hs=np.array([history(t,name,slow) for t in tslow])
        np.testing.assert_allclose(hf,hs,atol=1e-14,rtol=1e-13)
        section,_=profile(.8*fast['geometry']['length_m'],fast['geometry'],n_arc=320,n_side=160)
        mf=np.array([section_metrics(world(section,b,fast),h) for b,h,_ in hf])
        ms=np.array([section_metrics(world(section,b,slow),h) for b,h,_ in hs])
        np.testing.assert_allclose(mf,ms,atol=1e-14,rtol=1e-13)
        vf=np.gradient(hf[:,2],tfast);vs=np.gradient(hs[:,2],tslow)
        np.testing.assert_allclose(vs,.5*vf,atol=1e-13,rtol=1e-12)
        table=np.column_stack((tau,tfast,tslow,hf,hs,mf,ms,vf,vs))
        np.savetxt(out/f'{name}_comparison.csv',table,delimiter=',',comments='',header='progress,t_10deg_s,t_5deg_s,beta_fast_deg,H_fast_m,front_fast_m,beta_slow_deg,H_slow_m,front_slow_m,P_fast_m,b_fast_m,A_fast_m2,P_slow_m,b_slow_m,A_slow_m2,geometric_front_speed_fast_m_s,geometric_front_speed_slow_m_s')
        report['cases'][name]=dict(original_rate_deg_s=fast[name]['rate_deg_s'],new_rate_deg_s=slow[name]['rate_deg_s'],
            original_event_time_s=float(tfast[-1]),new_event_time_s=float(tslow[-1]),
            fixed_exit_beta_deg=float(hs[-1,0]),endpoint_H_world_m=float(hs[-1,1]),
            inlet_area_m2=float(ms[-1,2]),inlet_wetted_perimeter_m=float(ms[-1,0]),
            max_same_progress_geometry_difference=float(np.max(abs(mf-ms))),
            max_front_speed_halving_error_m_s=float(np.max(abs(vs-.5*vf))),
            fixed_G3_inlet_changed=False,reason='Angular rate absent from fixed G2/G3 equations; event geometry and assumed Q unchanged.')
        axes[i,0].plot(tfast,hf[:,0],label='10 deg/s');axes[i,0].plot(tslow,hs[:,0],label='5 deg/s')
        axes[i,1].plot(tfast,mf[:,2]*1e6,label='10 deg/s');axes[i,1].plot(tslow,ms[:,2]*1e6,label='5 deg/s')
        axes[i,0].set(ylabel=f'{name}: beta [deg]');axes[i,1].set(ylabel='s=0.8L liquid area [mm2]')
    for ax in axes.flat:ax.set_xlabel('Kinematic tilt time [s], NOT CFD time');ax.grid(alpha=.3);ax.legend()
    fig.tight_layout();fig.savefig(out/'angular_rate_comparison.png',dpi=160)
    assert hashlib.sha256(original.read_bytes()).hexdigest()==before
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (out/'README.md').write_text('''# 壶体角速度减半：已实际计算的对照

命令：在 v3 目录执行 `python angular_rate_comparison.py`。

按用户明确选择，10°/s改为5°/s，**没有把水流速度或10mL/s流量减半**。原parameters.json与G0/G1成果不修改。

Case 1：beta=55−5t，0≤t≤6s；Case 2：beta=70−5t，0≤t≤3s。终态分别仍为25°和55°。

本次沿用原有“以起终事件约束的水平液面插值”假设，故H_5(t)=H_10(t/2)，所有相同倾倒进度的几何覆盖完全相同。程序实际比较121个进度点、截面积、湿周和交线推进速度；几何交线速度减半，但它不是流体质点速度。

结果：仅此角速度调整不改变现有固定G2/G3的任何输入，不能生成另一套相同边界的VOF并称为“减慢倾倒的流动结果”。原固定姿态非稳态基准继续计算，尚未建立真实倾倒角速度→水头/压力/流量的动力学关联。这是当前模型无法分辨角速度效应，不证明真实流体对倾倒角速度不敏感。

“倾倒更慢导致附壁变化”目前仍是待检验假设。验证它需要一个能保留倾倒历史影响的上游流动模型或数据，再把所得不同入口条件交给固定G3；不是从6s/3s几何事件时间直接计算出口流速。当前研究边界保持固定壶嘴、无动态网格。
''',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
