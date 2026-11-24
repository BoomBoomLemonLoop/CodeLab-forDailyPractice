"""New fixed-spout transient cases, preserving all startup evidence."""
import json
import shutil
from pathlib import Path
import numpy as np
from make_cases import foam

ROOT=Path(__file__).resolve().parent
for name in ('case1','case2'):
    src=ROOT/'cases'/f'{name}_smoke_ready'; dst=ROOT/'cases'/f'{name}_transient_v1'
    if dst.exists():raise FileExistsError(dst)
    for folder in ('constant','system','0'):shutil.copytree(src/folder,dst/folder)
    if (dst/'0/cellLevel').exists():
        (dst/'mesh_generation_metadata').mkdir()
        shutil.move(dst/'0/cellLevel',dst/'mesh_generation_metadata/cellLevel_premerge')
    if (dst/'0/pointLevel').exists():
        shutil.move(dst/'0/pointLevel',dst/'mesh_generation_metadata/pointLevel_prepatch')
    for file in ('CASE_STATUS.json','mesh_repair.json','mesh_metrics.npz'):shutil.copy2(src/file,dst/file)
    m=json.loads((src/'mapping_report.json').read_text()); L=.045/np.sin(np.deg2rad(70))
    mean=1e-5/m['wet_area_m2']; tau=(L-.8*L)/mean
    capillary=np.sqrt(998*.0006**3/.072)
    target=np.ceil(max(5*capillary,2*.0006/mean)/.005)*.005
    (dst/'time_scales.json').write_text(json.dumps(dict(mean_inlet_m_s=mean,inlet_to_lip_advection_s=tau,
        lip_capillary_s=capillary,two_radii_advection_s=.0012/mean,
        first_window_s=target,full_development_assessment_s=3*tau,
        rationale='First window resolves >=5 lip capillary times and >=2 radius advection times; not full-domain residence or quasi-steady.'),indent=2))
    p=dst/'system/controlDict'; s=p.read_text().replace('endTime 0.0002;',f'endTime {target:.6g};')
    s=s.replace('writeInterval 0.00005;', 'writeInterval 0.001;').replace('writePrecision 8;','writePrecision 12;')
    s=s.replace('maxCo 0.25;','maxCo 0.1;').replace('maxAlphaCo 0.2;','maxAlphaCo 0.05;').replace('maxDeltaT 1e-5;','maxDeltaT 5e-6;')
    s=s.replace('functions {','functions {\nbounds { type fieldMinMax; libs (fieldFunctionObjects); fields (alpha.water U); mode magnitude; location true; writeControl timeStep; writeInterval 1; }')
    p.write_text(s)
    p=dst/'system/fvSolution';s=p.read_text().replace('nLimiterIter 5;','nLimiterIter 10;').replace('nNonOrthogonalCorrectors 0;','nNonOrthogonalCorrectors 1;');p.write_text(s)
    (dst/'system/decomposeParDict').write_text(foam('decomposeParDict','dictionary','system')+'numberOfSubdomains 8; method scotch;\n')
    (dst/'view.foam').touch()
    print(dst,target,tau)
