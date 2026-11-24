"""Cell-centred cross-section Poisson solve; SI, stationary laminar approximation.
No slip on staircase solid boundary; zero shear at horizontal liquid interface.
Solves -laplacian(psi)=1, then sets Q by normalization; inferred driving G=mu*C.
"""
import json
import numpy as np
from geometry import ROOT


def solve(height, spacing, target=1e-5, tolerance=1e-9, viscosity=.000998,
          rectangular_width=None):
    if min(height,spacing,target,viscosity) <= 0:
        raise ValueError('positive height, spacing, flow and viscosity required')
    radius=.005
    halfwidth=(height+.005)/np.sqrt(3)
    if rectangular_width is not None:
        halfwidth=rectangular_width/2
    ny=int(np.ceil(2*halfwidth/spacing)); nz=int(np.ceil(height/spacing))
    dy=2*halfwidth/ny; dz=height/nz
    y=(np.arange(ny)+.5)*dy-halfwidth
    z=(np.arange(nz)+.5)*dz
    wall=np.where(abs(y)<=radius*np.sqrt(3)/2,
                  radius-np.sqrt(np.maximum(0,radius**2-y*y)),np.sqrt(3)*abs(y)-radius)
    if rectangular_width is not None:
        wall=np.zeros_like(y)
    mask=z[None,:]>wall[:,None]
    ay,az=1/dy**2,1/dz**2
    diag=np.zeros(mask.shape)
    # Dirichlet boundary distance half a cell; Neumann at top.
    for axis,weight in ((0,ay),(1,az)):
        for direction in (-1,1):
            neighbour=np.roll(mask,direction,axis)
            sl=[slice(None)]*2; sl[axis]=0 if direction==1 else -1
            neighbour[tuple(sl)]=False
            contribution=np.where(neighbour,weight,2*weight)
            if axis==1 and direction==-1: contribution[:,-1]=0
            diag+=contribution
    def mat(v):
        a=diag*v
        for axis,weight in ((0,ay),(1,az)):
            for direction in (-1,1):
                n=np.roll(v,direction,axis)
                sl=[slice(None)]*2; sl[axis]=0 if direction==1 else -1
                n[tuple(sl)]=0
                a-=weight*n
        return np.where(mask,a,0)
    psi=np.zeros(mask.shape); residual=mask.astype(float); direction=residual.copy()
    rr=np.sum(residual**2); initial=rr
    for iteration in range(20000):
        ap=mat(direction); alpha=rr/np.sum(direction*ap)
        psi+=alpha*direction; residual-=alpha*ap
        new=np.sum(residual**2)
        if new/initial<tolerance**2: break
        direction=residual+(new/rr)*direction; rr=new
    else: raise RuntimeError('CG did not converge')
    coefficient=target/(psi.sum()*dy*dz)
    velocity=coefficient*psi
    assert velocity.min()>-1e-12
    return y,z,mask,velocity,dict(area_m2=float(mask.sum()*dy*dz),Q_m3_s=float(velocity.sum()*dy*dz),
        U_max_m_s=float(velocity.max()),G_Pa_m=float(viscosity*coefficient),iterations=iteration+1,
        relative_residual=float(np.sqrt(new/initial)),dy_m=dy,dz_m=dz)


if __name__=='__main__':
    states=json.loads((ROOT/'artifacts/g2_fixed_state.json').read_text())['cases']
    out=ROOT/'artifacts/g2_momentum';out.mkdir(exist_ok=True)
    report={'assumptions':'Q=10mL/s; locally straight laminar section; stress-free top; staircase no-slip wall; inferred pressure gradient','cases':{}}
    for case,state in states.items():
        records=[]
        for h in (.0004,.0002,.0001):
            y,z,mask,u,record=solve(state['baseline_section']['local_water_height_w_m'],h)
            record['dp_ds_Pa_m']=998*state['constant_gravity_spout_m_s2'][0]-record['G_Pa_m']
            records.append(record)
        yy,zz=np.meshgrid(y,z,indexing='ij')
        np.savez_compressed(out/f'{case}.npz',y=y,w=z,alpha=mask.astype(float),U_s=u,U_y=np.zeros_like(u),U_w=np.zeros_like(u))
        np.savetxt(out/f'{case}.csv',np.column_stack([yy.ravel(),zz.ravel(),mask.ravel(),u.ravel(),np.zeros(u.size),np.zeros(u.size)]),delimiter=',',header='y_m,w_m,alpha,U_s_m_s,U_y_m_s,U_w_m_s',comments='')
        report['cases'][case]=records
    (out/'verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
