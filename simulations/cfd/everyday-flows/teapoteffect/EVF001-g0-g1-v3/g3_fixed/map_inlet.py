"""Map G2 to actual polygonal inlet faces; split air patch, initialize inner water.

Two invocations: --split then OpenFOAM createPatch -overwrite, then --map.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from geometry import ROOT, load_config, rotation_y
from foam_io import geometry, read_mesh
from make_cases import foam


def wall_height(y):
    y=np.asarray(y)
    return np.where(abs(y)<=.005*np.sqrt(3)/2,
        .005-np.sqrt(np.maximum(0,.005**2-y*y)),np.sqrt(3)*abs(y)-.005)


def interpolate(y,z,grid_y,grid_z,values):
    """Bilinear velocity; zero padding at sides/bottom, stress-free at top."""
    gy=np.r_[grid_y[0]-(grid_y[1]-grid_y[0]),grid_y,grid_y[-1]+grid_y[1]-grid_y[0]]
    gz=np.r_[0.,grid_z,grid_z[-1]+(grid_z[1]-grid_z[0])/2]
    val=np.zeros((len(gy),len(gz)))
    val[1:-1,1:-1]=values
    val[1:-1,-1]=values[:,-1]
    iy=np.clip(np.searchsorted(gy,y)-1,0,len(gy)-2)
    iz=np.clip(np.searchsorted(gz,z)-1,0,len(gz)-2)
    fy=np.clip((y-gy[iy])/(gy[iy+1]-gy[iy]),0,1)
    fz=np.clip((z-gz[iz])/(gz[iz+1]-gz[iz]),0,1)
    ans=((1-fy)*(1-fz)*val[iy,iz]+fy*(1-fz)*val[iy+1,iz]
         +(1-fy)*fz*val[iy,iz+1]+fy*fz*val[iy+1,iz+1])
    return np.where((y>=gy[0])&(y<=gy[-1])&(z>=0)&(z<=gz[-1]),ans,0)


def integrate_faces(points,faces,ids,source,free,n=6):
    bary=[]
    for i in range(n):
        for j in range(n-i):
            bary.append(((i+1/3)/n,(j+1/3)/n))
            if j<n-i-1: bary.append(((i+2/3)/n,(j+2/3)/n))
    bary=np.asarray(bary)
    fractions=[]; means=[]; areas=[]
    for face_id in ids:
        poly=points[faces[face_id]]
        total=wet=transport=0.
        for j in range(1,len(poly)-1):
            a,b,c=poly[0],poly[j],poly[j+1]
            area=np.linalg.norm(np.cross(b-a,c-a))/2
            samples=a+bary[:,0,None]*(b-a)+bary[:,1,None]*(c-a)
            liquid=(samples[:,2]>=wall_height(samples[:,1]))&(samples[:,2]<=free)
            u=interpolate(samples[:,1],samples[:,2],source['y'],source['w'],source['U_s'])
            total+=area; wet+=area*liquid.mean(); transport+=area*np.mean(u*liquid)
        fractions.append(wet/total)
        means.append(transport/wet if wet>0 else 0.)
        areas.append(total)
    return np.array(fractions),np.array(means),np.array(areas)


def nonuniform(values):
    values=np.asarray(values)
    vector=values.ndim==2
    if vector:
        body='\n'.join('('+' '.join(f'{v:.12g}' for v in row)+')' for row in values)
    else: body='\n'.join(f'{v:.12g}' for v in values)
    return f'nonuniform List<{"vector" if vector else "scalar"}>\n{len(values)}\n(\n{body}\n)'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',type=Path)
    parser.add_argument('--split',action='store_true')
    parser.add_argument('--map',action='store_true')
    parser.add_argument('--quadrature',type=int,default=48)
    args=parser.parse_args(); case=args.case.resolve()
    state_name=json.loads((case/'CASE_STATUS.json').read_text())['source_case']
    state=json.loads((ROOT/'artifacts/g2_fixed_state.json').read_text())['cases'][state_name]
    source_file=ROOT/'artifacts/g2_momentum'/f'{state_name}.npz'
    source=np.load(source_file)
    points,faces,owner,neighbour,patches=read_mesh(case)
    name='inlet' if args.split else 'waterInlet'
    patch=patches[name]; ids=np.arange(patch['startFace'],patch['startFace']+patch['nFaces'])
    free=state['baseline_section']['local_water_height_w_m']
    fractions,mean,areas=integrate_faces(points,faces,ids,source,free,n=args.quadrature)
    if args.split:
        selected=ids[fractions>0]
        folder=case/'constant/polyMesh/sets'; folder.mkdir(exist_ok=True)
        text=foam('waterFaces','faceSet','constant/polyMesh/sets')
        text+=f'{len(selected)}\n(\n'+'\n'.join(map(str,selected))+'\n)\n'
        (folder/'waterFaces').write_text(text)
        (case/'system/createPatchDict').write_text(foam('createPatchDict','dictionary','system')+
            'pointSync false; patches ({ name waterInlet; patchInfo { type patch; } constructFrom set; set waterFaces; });\n')
        print(f'Selected {len(selected)} wet faces out of {len(ids)} upstream faces')
        return
    if not args.map: parser.error('choose --split or --map')
    cf,sf,centres,volumes=geometry(points,faces,owner,neighbour)
    length=load_config()['geometry']['length_m']; s_in=.8*length
    assert np.max(abs(cf[ids,0]-s_in))<1e-8
    assert np.max(abs(sf[ids,1:]))<1e-12
    assert np.all(sf[ids,0]<0)
    target=1e-5
    q_raw=float(np.sum(fractions*mean*(-sf[ids,0])))
    factor=target/q_raw
    if abs(factor-1)>.05: raise ValueError(f'large mapping correction {factor}; refine/review mesh')
    velocities=np.column_stack((mean*factor,np.zeros((len(ids),2))))
    q=float(np.sum(fractions*(-np.einsum('ij,ij->i',velocities,sf[ids]))))
    coarse_a,coarse_u,_=integrate_faces(points,faces,ids,source,free,n=max(1,args.quadrature//2))
    beta=np.deg2rad(state['fixed_beta_deg'])
    height=state['source_H_world_m']
    seed=(centres[:,0]<=length)&(centres[:,2]>=wall_height(centres[:,1]))
    seed&=(centres[:,0]*np.sin(beta)+centres[:,2]*np.cos(beta)<=height)
    seed&=(centres[:,2]<=.025*centres[:,0]/length)
    u0=np.zeros_like(centres)
    u0[:,0]=interpolate(centres[:,1],centres[:,2],source['y'],source['w'],source['U_s'])*seed*factor
    # Static inner liquid seed; all external air stays dry. Pressure adjusts by projection.
    internals={'alpha.water':seed.astype(float),'U':u0,'p_rgh':np.zeros(len(centres))}
    dims={'alpha.water':'[0 0 0 0 0 0 0]','U':'[0 1 -1 0 0 0 0]','p_rgh':'[1 -1 -2 0 0 0 0]'}
    for field,internal in internals.items():
        cls='volVectorField' if field=='U' else 'volScalarField'
        text=foam(field,cls,'0')+f'dimensions {dims[field]};\ninternalField '+nonuniform(internal)+';\nboundaryField\n{\n'
        for pname in patches:
            if pname=='waterInlet':
                bc=('type fixedValue; value '+nonuniform(velocities if field=='U' else fractions)+';'
                    if field!='p_rgh' else 'type fixedFluxPressure; value uniform 0;')
            elif pname.startswith('spout'):
                bc={'U':'type noSlip;', 'alpha.water':'type constantAlphaContactAngle; theta0 60; limit gradient; value uniform 0;',
                    'p_rgh':'type fixedFluxPressure; value uniform 0;'}[field]
            else:
                bc={'U':'type pressureInletOutletVelocity; value uniform (0 0 0);',
                    'alpha.water':'type inletOutlet; inletValue uniform 0; value uniform 0;',
                    'p_rgh':'type prghTotalPressure; p0 uniform 0; value uniform 0;'}[field]
            text+=f'{pname}\n{{\n{bc}\n}}\n'
        (case/'0'/field).write_text(text+'}\n')
    world_u=velocities@rotation_y(-state['fixed_beta_deg']).T
    np.testing.assert_allclose(world_u@rotation_y(-state['fixed_beta_deg']),velocities,atol=1e-14)
    np.savez_compressed(case/'mesh_metrics.npz',centres=centres,volumes=volumes,face_centres=cf,
        face_vectors=sf,owner=owner,neighbour=neighbour,seed=seed)
    table=np.column_stack((cf[ids],sf[ids],fractions,velocities,world_u))
    np.savetxt(case/'inlet_mapping.csv',table,delimiter=',',header='s,y,w,Ss,Sy,Sw,alpha,Us,Uy,Uw,UXworld,UYworld,UZworld',comments='')
    report=dict(source_case=state_name,source_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
        mesh_cells=len(centres),s_in_m=s_in,normal_outward=[-1,0,0],wet_faces=len(ids),
        target_Q_m3_s=target,raw_mapped_Q_m3_s=q_raw,normalization_factor=factor,mapped_Q_m3_s=q,
        relative_Q_error=abs(q-target)/target,wet_area_m2=float(np.sum(fractions*areas)),
        quadrature_subdivision=args.quadrature,
        quadrature_half_vs_full_Q_relative_difference=float(abs(np.sum(coarse_a*coarse_u*(-sf[ids,0]))-q_raw)/q_raw),
        initial_water_volume_m3=float(volumes[seed].sum()),initialization='inner connected seed; external air dry; binary cell centre alpha',
        status='MAPPED_AND_INITIALIZED_NOT_YET_SOLVED')
    (case/'mapping_report.json').write_text(json.dumps(report,indent=2))
    (case/'CASE_STATUS.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
