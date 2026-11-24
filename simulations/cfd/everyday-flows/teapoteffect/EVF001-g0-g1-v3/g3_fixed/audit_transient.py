"""Locate detailed mesh defects and saved-field alpha excursions (SI)."""
import json
import sys
from pathlib import Path
import numpy as np
from foam_io import list_body, field_values

case=Path(sys.argv[1]); m=np.load(case/'mesh_metrics.npz'); c=m['centres']
L=.045/np.sin(np.deg2rad(70))
bad=np.fromstring(list_body(case/'constant/polyMesh/sets/concaveCells')[1],sep=' ',dtype=int)
regions={'outlet_1mm':abs(c[:,0]-L)<.001,'lower_outlet_1mm':(abs(c[:,0]-L)<.001)&(c[:,2]<.003),'upper_rim':c[:,2]>.018}
report={'concave_count':len(bad),'regions':{k:{'total':int(v.sum()),'concave':int(v[bad].sum())} for k,v in regions.items()},'alpha':[]}
def time_key(p):
    try:return float(p.name)
    except ValueError:return -1
for p in sorted(case.iterdir(),key=time_key):
    if not (p/'alpha.water').is_file():continue
    a=field_values(p/'alpha.water')
    if a.size!=len(c):continue
    violation=(a < -1e-8)|(a>1+1e-8)
    ids=np.where(violation)[0]
    report['alpha'].append(dict(time=p.name,min=float(a.min()),max=float(a.max()),count_gt_1e8=int(violation.sum()),
        on_concave=int(violation[bad].sum()),near_lower_outlet=int((violation&regions['lower_outlet_1mm']).sum()),
        concave_liquid_cells=int((a[bad]>.5).sum()),
        concave_interface_cells=int(((a[bad]>.01)&(a[bad]<.99)).sum()),
        lower_outlet_concave_liquid_cells=int(((a[bad]>.5)&regions['lower_outlet_1mm'][bad]).sum()),
        lower_outlet_concave_interface_cells=int(((a[bad]>.01)&(a[bad]<.99)&regions['lower_outlet_1mm'][bad]).sum()),
        worst_min_xyz_m=c[a.argmin()].tolist(),worst_max_xyz_m=c[a.argmax()].tolist(),
        violation_extent_m=[c[ids].min(axis=0).tolist(),c[ids].max(axis=0).tolist()] if len(ids) else None))
np.savez_compressed(case/'concavity_locations.npz',centres=c[bad],ids=bad)
(case/'numerical_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
