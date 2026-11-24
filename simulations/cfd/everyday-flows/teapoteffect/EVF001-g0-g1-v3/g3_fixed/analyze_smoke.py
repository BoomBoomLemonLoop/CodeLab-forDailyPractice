"""Assess startup only: alpha bounds, CFL and actual transported water balance."""
import json
import re
import sys
from pathlib import Path
import numpy as np
from foam_io import field_values

case=Path(sys.argv[1]); log=(case/'log.interFoam').read_text()
assert '\nEnd\n' in log and 'FOAM FATAL' not in log, 'solver has not finished successfully'
metrics=np.load(case/'mesh_metrics.npz'); mapping=json.loads((case/'mapping_report.json').read_text())
times=sorted((float(p.name),p) for p in case.iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name))
t,folder=times[-1]; alpha=field_values(folder/'alpha.water'); u=field_values(folder/'U')
vpath=case/'0/V'
volumes=field_values(vpath) if vpath.exists() else metrics['volumes']
initial=float(field_values(case/'0/alpha.water')@volumes); final=float(alpha@volumes)
flux={}; cumulative=0.
for name in ('waterInlet','inlet','atmosphere'):
    data=np.loadtxt(case/'postProcessing'/f'{name}Flux'/'0/surfaceFieldValue.dat')
    q=(data[:,2]-1.2*data[:,1])/(998-1.2)
    dt=np.diff(np.r_[0,data[:,0]])
    # rhoPhi is the alpha-subcycle averaged mixture mass flux used by interFoam.
    integrated=float(q@dt); cumulative+=integrated
    flux[name]=dict(mean_outward_water_Q_m3_s=float(integrated/t),integrated_outward_m3=integrated)
residual=final-initial+cumulative
mins=[float(v) for v in re.findall(r'Min\(alpha.water\) = ([\deE+.-]+)',log)]
maxs=[float(v) for v in re.findall(r'Max\(alpha.water\) = ([\deE+.-]+)',log)]
co=[float(v) for v in re.findall(r'^Courant Number mean: .*?max: ([\deE+.-]+)',log,re.M)]
report=dict(status='TESTED_STARTUP_ONLY_NOT_PHYSICALLY_VALIDATED',end_time_s=t,cells=len(alpha),
    volume_source='OpenFOAM writeCellVolumes' if vpath.exists() else 'independent polygon tetrahedra',
    alpha_min_all_logged=min(mins),alpha_max_all_logged=max(maxs),max_Co_logged=max(co),
    final_max_speed_m_s=float(np.linalg.norm(u,axis=1).max()),initial_water_m3=initial,final_water_m3=final,
    final_max_speed_alpha_gt_half_m_s=float(np.linalg.norm(u[alpha>.5],axis=1).max()),
    patch_water_flux=flux,water_balance_residual_m3=residual,
    balance_relative_to_supplied_water=residual/(1e-5*t),
    balance_relative_to_initial_volume=residual/initial,
    limitations='Short startup, not quasi-steady. Detailed mesh concavity diagnostics remain; no grid/time independence or Teapot Effect conclusion.')
(case/'startup_results.json').write_text(json.dumps(report,indent=2))
status=json.loads((case/'CASE_STATUS.json').read_text())
status['status']=report['status'];status['end_time_s']=t
(case/'CASE_STATUS.json').write_text(json.dumps(status,indent=2))
print(json.dumps(report,indent=2))
