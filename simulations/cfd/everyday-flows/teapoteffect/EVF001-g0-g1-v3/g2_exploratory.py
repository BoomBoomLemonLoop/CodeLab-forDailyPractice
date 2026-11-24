"""Exploratory constant inlet: exact cross-section quadrature and flux checks."""
import csv
import json
from pathlib import Path

import numpy as np

from geometry import ROOT, load_config, profile, world


def section(case, n=801):
    cfg = load_config()
    state = json.loads((ROOT/'artifacts'/'g2_fixed_state.json').read_text())['cases'][case]
    s = .8*cfg['geometry']['length_m']
    beta, height = state['fixed_beta_deg'], state['source_H_world_m']
    p, _ = profile(s, cfg['geometry'], n_arc=n, n_side=n//2)
    y, w = p[:,1], p[:,2]
    wf = (height-world([s,0,0],beta,cfg)[2])/np.cos(np.deg2rad(beta))
    mask = w < wf
    y = y[mask]; w = w[mask]
    # Exact piecewise-linear wall quadrature: integral of depth over y.
    depth = wf-w
    area = np.trapezoid(depth,y)
    if area <= 0: raise ValueError('empty inlet')
    return y,w,depth,area,state


def generate():
    out = ROOT/'artifacts'/'g2_exploratory'
    out.mkdir(exist_ok=True)
    summary={"status":"exploratory fixed-Q kinematic inlet; not measured or momentum-solved",
             "assumed_Q_m3_s":1e-5,"profile":"local plane-film Poiseuille shape 2xi-xi^2; approximate, not fully developed in triangular spout", "cases":{}}
    for case in ('case1','case2'):
        y,w,depth,area,state=section(case)
        # n=0 at wall, n=depth at interface; no-slip and zero interface shear.
        # Width-integrated shape = 2*depth/3, hence Q=Umax*integral(2*depth/3 dy).
        shape_integral=np.trapezoid(2*depth/3,y)
        umax=1e-5/shape_integral
        flux=umax*shape_integral
        rows=[]
        for yi,wi,di in zip(y,w,depth):
            for xi in (0.,.25,.5,.75,1.):
                rows.append((yi,wi+xi*di,xi,umax*(2*xi-xi*xi),1))
        with (out/f'{case}_profile.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream); writer.writerow(('y_m','w_m','relative_depth','U_s_m_s','alpha.water'))
            writer.writerows(rows)
        summary['cases'][case]={"beta_deg":state['fixed_beta_deg'],"g_local_m_s2":state['constant_gravity_spout_m_s2'],
             "s_in_m":.8*load_config()['geometry']['length_m'],"w_free_m":state['baseline_section']['local_water_height_w_m'],
             "area_m2":float(area),"U_mean_m_s":float(flux/area),"U_max_m_s":float(umax),
             "integrated_Q_m3_s":float(flux),"relative_flux_error":float(abs(flux-1e-5)/1e-5)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': generate()
