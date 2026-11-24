"""Compare saved CFD development, not equal clock times or one-variable causality.

python g3_fixed/compare_development.py
Outputs development_comparison.json/png from actual reconstructed metrics.
Tau=(L-s_in)/mean(Uin); threshold events are brackets between saved times.
Wet front positions are not claimed to be hydrodynamic separation points.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent

def event_bracket(rows,key,threshold):
    for i,row in enumerate(rows):
        if row[key]>threshold:return [rows[max(0,i-1)]['time_s'],row['time_s']]
    return None

def main():
    scales=json.loads((ROOT/'physical_scales.json').read_text());L=.045/np.sin(np.deg2rad(70))
    fig,axs=plt.subplots(2,3,figsize=(15,8));summary={}
    for name in ('case1','case2'):
        case=ROOT/'cases'/f'{name}_transient_v1'
        rows=json.loads((case/'transient_metrics.json').read_text())['series']
        tau=.2*L/scales[name]['mean_inlet_m_s'];t=np.array([r['time_s'] for r in rows])
        event=event_bracket(rows,'maximum_liquid_s_m',L+.0006)
        last,prev=rows[-1],rows[-2]
        summary[name]={'last_analyzed_s':float(t[-1]),'advection_time_s':tau,'last_t_over_tau':float(t[-1]/tau),
            'bulk_beyond_lip_event_bracket_s':event,
            'lower_lip_wetting_bracket_s':event_bracket(rows,'connected_lower_lip_area_alpha0.5_m2',1e-12),
            'last_inner_storage_rate_over_Q':(last['geometric_spout_interior_water_m3']-prev['geometric_spout_interior_water_m3'])/(t[-1]-t[-2])/1e-5,
            'detachment_position_status':'UNRESOLVED; reported wet front is a proxy, not a validated separation point'}
        recent=rows[-3:]
        summary[name]['recent_saved_window_s']=[recent[0]['time_s'],recent[-1]['time_s']]
        summary[name]['bulk_beyond_lip_in_all_recent_frames']=all(r['maximum_liquid_s_m']>L+.0006 for r in recent)
        summary[name]['lower_lip_wet_in_all_recent_frames']=all(r['connected_lower_lip_area_alpha0.5_m2']>1e-12 for r in recent)
        summary[name]['warning']='Persistence at saved frames is not quasi-steady convergence or physical validation.'
        for j,x in enumerate((t*1000,t/tau)):
            axs[j,0].plot(x,[r['connected_lower_lip_area_alpha0.5_m2']*1e6 for r in rows],label=name)
            axs[j,1].plot(x,[r['connected_lip_angle_alpha0.5_deg'] for r in rows],label=name)
            axs[j,2].plot(x,[r['attached_length_alpha0.5_m']*1000 for r in rows],label=name)
            for ax in axs[j]:ax.set_xlabel('CFD time [ms]' if j==0 else 't / inlet-to-lip advection time');ax.legend();ax.grid(alpha=.3)
    for j in (0,1):
        axs[j,0].set_ylabel('Connected lower lip wet area [mm2]')
        axs[j,1].set_ylabel('Connected wet angle [deg]')
        axs[j,2].set_ylabel('Straight outer-wall attached extent [mm]')
    fig.suptitle('Combined conditions; alpha >= 0.5. Equal time is not equal flow development.')
    fig.tight_layout();fig.savefig(ROOT/'development_comparison.png',dpi=140);plt.close(fig)
    (ROOT/'development_comparison.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
