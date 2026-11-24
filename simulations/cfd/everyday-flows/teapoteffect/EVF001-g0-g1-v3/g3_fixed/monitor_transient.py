"""Read-only compact live solver status; success requires End, never elapsed time."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for name in ('case1','case2'):
    case=ROOT/'cases'/f'{name}_transient_v1';p=max(case.glob('log.interFoam*'),key=lambda p:p.stat().st_mtime)
    with p.open('rb') as f:
        f.seek(max(0,p.stat().st_size-50000));s=f.read().decode(errors='replace')
    def last(pattern):
        values=re.findall(pattern,s,re.M);return values[-1] if values else None
    print(json.dumps(dict(case=name,time=last(r'^Time = (\S+)'),dt=last(r'^deltaT = (\S+)'),
        Co=last(r'^Courant Number mean: .*?max: (\S+)'),alphaCo=last(r'^Interface Courant Number mean: .*?max: (\S+)'),
        alpha_minmax=last(r'^Phase-1.*?Min\(alpha.water\) = (\S+)\s+Max\(alpha.water\) = (\S+)'),
        clock_s=last(r'ClockTime = (\S+) s'),finished='\nEnd\n' in s,fatal='FOAM FATAL' in s)))
