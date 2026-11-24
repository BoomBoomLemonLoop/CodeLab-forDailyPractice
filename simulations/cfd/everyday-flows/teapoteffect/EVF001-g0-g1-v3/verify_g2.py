"""Independent rectangular-channel Fourier benchmark and three-level G2 comparison."""
import json
import os
import sys

import numpy as np

from geometry import ROOT, rotation_y
from g2_momentum import solve

sys.path.insert(0,str(ROOT/'g3_fixed'))
from map_inlet import interpolate

os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def rectangle_exact(y,z,width,height):
    """Unit -Laplacian forcing, Dirichlet sides/bottom, Neumann top."""
    a=width/2; psi=np.zeros((len(y),len(z))); integral=0.
    for m in range(300):
        k=(2*m+1)*np.pi/(2*a)
        ratio=np.exp(-k*z)*(1+np.exp(-2*k*(height-z)))/(1+np.exp(-2*k*height))
        psi+=4*(-1.)**m/((2*m+1)*np.pi*k*k)*np.cos(k*y)[:,None]*(1-ratio)[None,:]
        integral+=8/((2*m+1)*np.pi*k**3)*(height-np.tanh(k*height)/k)
    return psi*1e-5/integral,.000998*1e-5/integral


def main():
    out=ROOT/'artifacts/g2_momentum'
    report={'rectangular_analytic_benchmark':[],'cases':{},'flow_is_assumed_not_validated':True}
    for spacing in (.0004,.0002,.0001):
        y,z,mask,u,rec=solve(.003,spacing,rectangular_width=.01)
        exact,drive=rectangle_exact(y,z,.01,.003)
        error=np.linalg.norm(u-exact)/np.linalg.norm(exact)
        report['rectangular_analytic_benchmark'].append(dict(spacing_m=spacing,
            velocity_L2_relative=float(error),G_relative=float(abs(rec['G_Pa_m']-drive)/drive)))
    errors=[r['velocity_L2_relative'] for r in report['rectangular_analytic_benchmark']]
    assert errors[1]<errors[0]/2 and errors[2]<errors[1]/2,errors
    assert errors[-1]<.002,errors
    states=json.loads((ROOT/'artifacts/g2_fixed_state.json').read_text())['cases']
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for col,(case,state) in enumerate(states.items()):
        solutions=[]; rows=[]
        for spacing in (.0004,.0002,.0001):
            y,z,mask,u,rec=solve(state['baseline_section']['local_water_height_w_m'],spacing)
            rec['nominal_spacing_m']=spacing
            rec['dp_ds_Pa_m']=998*state['constant_gravity_spout_m_s2'][0]-rec['G_Pa_m']
            rec['area_relative_error']=float(abs(rec['area_m2']/state['baseline_section']['liquid_area_m2']-1))
            assert abs(rec['Q_m3_s']/1e-5-1)<1e-12
            solutions.append((y,z,mask,u)); rows.append(rec)
            axes[0,col].plot(z*1000,u[len(y)//2],label=f'{spacing*1000:g} mm')
        y,z,mask,fine=solutions[-1]
        yy,zz=np.meshgrid(y,z,indexing='ij')
        for i in (0,1):
            cy,cz,cm,cu=solutions[i]
            mapped=interpolate(yy,zz,cy,cz,cu)*mask
            rows[i]['profile_relative_L2_vs_finest']=float(np.linalg.norm(mapped-fine)/np.linalg.norm(fine))
        axes[0,col].set(title=f'{case}: centreline profile',xlabel='w [mm]',ylabel='U_s [m/s]')
        axes[0,col].legend(); axes[0,col].grid(alpha=.2)
        mesh=axes[1,col].pcolormesh(y*1000,z*1000,np.where(mask,fine,np.nan).T,shading='nearest')
        axes[1,col].set(xlabel='y [mm]',ylabel='w [mm]',title='Finest section solution [m/s]')
        axes[1,col].set_aspect('equal');fig.colorbar(mesh,ax=axes[1,col])
        local=np.column_stack((fine[mask],np.zeros((mask.sum(),2))))
        r=rotation_y(-state['fixed_beta_deg'])
        world=local@r.T
        np.testing.assert_allclose(world@r,local,atol=1e-14)
        assert np.all(world[:,2]>=-1e-14)
        report['cases'][case]={'levels':rows,'coordinate_roundtrip_max_error':float(np.max(abs(world@r-local))),
            'fine_vs_medium_Umax_relative':float(abs(rows[-1]['U_max_m_s']/rows[-2]['U_max_m_s']-1)),
            'fine_vs_medium_G_relative':float(abs(rows[-1]['G_Pa_m']/rows[-2]['G_Pa_m']-1))}
    fig.suptitle('G2 local laminar momentum solutions; assumed Q=10 mL/s')
    fig.tight_layout();fig.savefig(out/'convergence_profiles.png',dpi=150);plt.close(fig)
    (out/'convergence_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
