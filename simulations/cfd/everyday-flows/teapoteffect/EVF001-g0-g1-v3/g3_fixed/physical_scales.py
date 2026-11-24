"""Dimensionless scale estimates, NOT solved stresses or a spill criterion."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
result={}
for name in ('case1','case2'):
    case=ROOT/'cases'/f'{name}_transient_v1';m=json.loads((case/'mapping_report.json').read_text())
    u=1e-5/m['wet_area_m2'];rho=998.;mu=.000998;sigma=.072;R=.0006
    result[name]=dict(mean_inlet_m_s=u,Ca_mean=mu*u/sigma,We_mean_R=rho*u*u*R/sigma,
        Re_mean_R=rho*u*R/mu,Bo_R=(rho-1.2)*9.81*R*R/sigma,
        dynamic_head_mean_m=u*u/(2*9.81),sigma_over_R_pressure_scale_Pa=sigma/R,
        warning='R-based mean-inlet scales only. Actual interface has two evolving curvatures; sigma/R is not a prescribed Laplace jump or proven spill threshold.')
(ROOT/'physical_scales.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
