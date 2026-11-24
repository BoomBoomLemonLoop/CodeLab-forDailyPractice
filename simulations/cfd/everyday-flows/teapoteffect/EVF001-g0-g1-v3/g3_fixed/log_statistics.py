"""Summarize actual step extrema, retaining pre/post-MULES distinction."""
import json
import re
import sys
from pathlib import Path
import numpy as np

case=Path(sys.argv[1]);logs=sorted(case.glob('log.interFoam*'),key=lambda p:p.stat().st_mtime);last=logs[-1].read_text();s='\n'.join(p.read_text() for p in logs)
co=[float(x) for x in re.findall(r'^Courant Number mean: .*?max: (\S+)',s,re.M)]
aco=[float(x) for x in re.findall(r'^Interface Courant Number mean: .*?max: (\S+)',s,re.M)]
alpha=[(float(a),float(b)) for a,b in re.findall(r'^Phase-1.*?Min\(alpha.water\) = (\S+)\s+Max\(alpha.water\) = (\S+)',s,re.M)]
final_min=[float(x) for x in re.findall(r'^\s+min\(alpha.water\) = (\S+)',s,re.M)]
final_max=[float(x) for x in re.findall(r'^\s+max\(alpha.water\) = (\S+)',s,re.M)]
dt=[float(x) for x in re.findall(r'^deltaT = (\S+)',s,re.M)]
report=dict(solver_finished='\nEnd\n' in last,fatal='FOAM FATAL' in s,
    latest_solver_time_s=float(re.findall(r'^Time = (\S+)',s,re.M)[-1]),steps=len(dt),max_Co=max(co),max_alphaCo=max(aco),
    min_dt_s=min(dt),max_dt_s=max(dt),
    all_substep_logged_alpha_min=min(a for a,b in alpha),all_substep_logged_alpha_max=max(b for a,b in alpha),
    final_step_alpha_min=min(final_min),final_step_alpha_max=max(final_max),
    over_1e6_final_step_count=sum(x>1+1e-6 for x in final_max),
    note='Final fieldMinMax extrema are distinct from predictor/correction substeps. Counts here refer to timesteps, not cells.')
(case/'log_statistics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
