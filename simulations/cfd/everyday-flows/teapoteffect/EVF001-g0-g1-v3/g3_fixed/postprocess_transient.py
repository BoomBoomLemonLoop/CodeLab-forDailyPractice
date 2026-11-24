"""Actual wall coverage proxies, saved-field bounds and all-open-patch water balance.

Wetted face: wall alpha >= threshold. Attachment length: axial extent of wet
outer faces connected by shared edges to the exit. This is a contact-front
proxy, not proof of hydrodynamic separation or a physical contact line.
"""
import json
import csv
import re
import sys
from pathlib import Path
import numpy as np
from foam_io import read_mesh,field_values

def connected_wet(wet,adj,seeds):
    seen=set(int(i) for i in seeds if wet[i]);stack=list(seen)
    while stack:
        for j in adj[stack.pop()]:
            if wet[j] and j not in seen:seen.add(j);stack.append(j)
    return np.array(sorted(seen),dtype=int)

def patch_scalar(path,name,count):
    s=Path(path).read_text();body=re.search(r'\b'+name+r'\s*\{(.*?)\n\s*\}',s,re.S)[1]
    a=re.search(r'value\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\)\s*;',body,re.S)
    if a:return np.fromstring(a[1],sep=' ')
    return np.full(count,float(re.search(r'value\s+uniform\s+([^;]+)',body)[1]))

def classify_wall(wc,sf,L):
    norm=sf/np.linalg.norm(sf,axis=1)[:,None]
    y,z=wc[:,1],wc[:,2];angle=np.arctan2(abs(y),.005-z)
    radius=np.maximum(np.hypot(y,z-.005),1e-20)
    distance=np.where(angle<=np.pi/3,.005-radius,(z-np.sqrt(3)*abs(y)+.005)/2)
    nn=np.column_stack((np.zeros(len(y)),np.where(angle<=np.pi/3,-y/radius,-np.sign(y)*np.sqrt(3)/2),
        np.where(angle<=np.pi/3,(.005-z)/radius,.5)))
    outer=(distance<-.0008)&(wc[:,0]<L)&(np.einsum('ij,ij->i',norm,nn)>.5)
    return outer,wc[:,0]>=L-3e-5,distance

def main(case):
    p,f,owner,ne,patches=read_mesh(case);m=np.load(case/'mesh_metrics.npz')
    v=field_values(case/'0/V');c=m['centres'];L=.045/np.sin(np.deg2rad(70))
    patch=patches['spout'];ids=np.arange(patch['startFace'],patch['startFace']+patch['nFaces'])
    wc=m['face_centres'][ids];sf=m['face_vectors'][ids];area=np.linalg.norm(sf,axis=1);norm=sf/area[:,None]
    outer,lip,distance=classify_wall(wc,sf,L)
    theta=np.arctan2(np.maximum(0,wc[:,0]-L),distance+.0006)
    adj=[set() for i in ids];edge={}
    for j,i in enumerate(ids):
        poly=f[i]
        for a,b in zip(poly,np.roll(poly,-1)):
            key=tuple(sorted((int(a),int(b))))
            if key in edge:
                k=edge[key];adj[j].add(k);adj[k].add(j)
            else:edge[key]=j
    seeds=np.where(lip&(theta<np.deg2rad(20)))[0];out=[]
    times=[]
    for t in case.iterdir():
        try:value=float(t.name)
        except ValueError:continue
        if (t/'alpha.water').exists():times.append((value,t))
    times.sort()
    flux={}
    for name in ('waterInlet','inlet','atmosphere'):
        chunks=[]
        for file in (case/'postProcessing'/f'{name}Flux').glob('*/surfaceFieldValue.dat'):
            data=np.atleast_2d(np.loadtxt(file));chunks.extend(data.tolist())
        data=np.array(sorted({row[0]:row for row in chunks}.values()))
        q=(data[:,2]-1.2*data[:,1])/996.8
        flux[name]=(data[:,0],np.cumsum(q*np.diff(np.r_[0,data[:,0]])))
    initial=float(field_values(case/'0/alpha.water')@v)
    cy=c[:,1]
    wall_z=np.where(abs(cy)<=.005*np.sqrt(3)/2,.005-np.sqrt(np.maximum(0,.005**2-cy**2)),np.sqrt(3)*abs(cy)-.005)
    interior=(c[:,0]<=L)&(c[:,2]>=wall_z)&(c[:,2]<=.025*c[:,0]/L)
    for t,path in times:
        a=field_values(path/'alpha.water');u=field_values(path/'U');wall=patch_scalar(path/'alpha.water','spout',len(ids))
        assert np.isfinite(a).all() and np.isfinite(u).all()
        speed=np.linalg.norm(u,axis=1)
        row=dict(time_s=t,water_volume_m3=float(a@v),alpha_min=float(a.min()),alpha_max=float(a.max()),
            geometric_spout_interior_water_m3=float((a*v)[interior].sum()),
            alpha_outside_1e8_count=int(((a < -1e-8)|(a>1+1e-8)).sum()),
            alpha_outside_1e6_count=int(((a < -1e-6)|(a>1+1e-6)).sum()),
            worst_max_alpha_xyz_m=c[a.argmax()].tolist(),worst_min_alpha_xyz_m=c[a.argmin()].tolist(),
            wall_alpha_min=float(wall.min()),wall_alpha_max=float(wall.max()),
            max_speed_all_m_s=float(speed.max()),max_speed_air_alpha_lt_001_m_s=float(speed[a<.01].max()),
            max_speed_all_xyz_m=c[speed.argmax()].tolist(),
            beyond_lip_water_m3=float((a*v)[c[:,0]>L+.0006].sum()),
            maximum_liquid_s_m=float(c[a>.5,0].max()),max_liquid_speed_m_s=float(np.linalg.norm(u[a>.5],axis=1).max()),
            outer_alpha_area_m2=float(np.sum(np.clip(wall[outer],0,1)*area[outer])))
        for threshold in (.1,.5,.9):
            wet=wall>=threshold;connected=connected_wet(wet&(outer|lip),adj,seeds);attached=connected[outer[connected]]
            row[f'outer_area_alpha{threshold}_m2']=float(area[outer&wet].sum())
            row[f'attached_length_alpha{threshold}_m']=float(max(0,L-wc[attached,0].min())) if len(attached) else 0.
            row[f'contact_front_alpha{threshold}_xyz_m']=wc[attached[np.argmin(wc[attached,0])]].tolist() if len(attached) else None
            connected_lip=connected[lip[connected]]
            lower=connected_lip[theta[connected_lip]>np.pi/2]
            row[f'connected_lower_lip_area_alpha{threshold}_m2']=float(area[lower].sum())
            angle=float(theta[connected_lip].max()) if len(connected_lip) else 0.
            row[f'connected_lip_angle_alpha{threshold}_deg']=float(np.rad2deg(angle))
            row[f'connected_lip_arc_alpha{threshold}_m']=.0006*angle
            front=connected_lip[np.argmax(theta[connected_lip])] if len(connected_lip) else None
            row[f'lip_front_candidate_alpha{threshold}_xyz_m']=wc[front].tolist() if front is not None else None
            row[f'lip_front_adjacent_U_alpha{threshold}_m_s']=u[owner[ids[front]]].tolist() if front is not None else None
        lipwet=lip&(wall>.5)
        row['max_wet_lip_angle_deg']=float(np.rad2deg(theta[lipwet]).max()) if lipwet.any() else 0.
        row['max_wet_lip_xyz_m']=wc[np.where(lipwet)[0][np.argmax(theta[lipwet])]].tolist() if lipwet.any() else None
        liquid=np.where(a>.5)[0]
        row['maximum_liquid_s_xyz_m']=c[liquid[np.argmax(c[liquid,0])]].tolist()
        total=0.
        for name,(ft,fv) in flux.items():
            q=float(np.interp(t,np.r_[0,ft],np.r_[0,fv]));row[name+'_integrated_outward_m3']=q;total+=q
        row['water_balance_residual_m3']=row['water_volume_m3']-initial+total
        out.append(row)
    (case/'transient_metrics.json').write_text(json.dumps(dict(definition=__doc__,series=out),indent=2))
    state=json.loads((case/'CASE_STATUS.json').read_text())
    state.update(status='TRANSIENT_FIELDS_ANALYZED_NOT_PHYSICALLY_VALIDATED',analyzed_until_s=out[-1]['time_s'])
    (case/'CASE_STATUS.json').write_text(json.dumps(state,indent=2))
    with (case/'transient_metrics.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
    np.savez_compressed(case/'wall_classification.npz',face_ids=ids,outer=outer,lip=lip,centres=wc,area=area)
    print(json.dumps(out[-1],indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
