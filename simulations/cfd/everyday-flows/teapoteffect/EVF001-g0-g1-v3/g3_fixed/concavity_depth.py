"""Measure convex-hull-plane violation of flagged cells, not a solver quality substitute."""
import json
import sys
from pathlib import Path
import numpy as np
from foam_io import read_mesh,list_body

case=Path(sys.argv[1]);p,f,o,n,patch=read_mesh(case);m=dict(np.load(case/'mesh_metrics.npz'))
ids=np.fromstring(list_body(case/'constant/polyMesh/sets/concaveCells')[1],sep=' ',dtype=int)
lookup={int(c):[] for c in ids}
for i,c in enumerate(o):
    if int(c) in lookup:lookup[int(c)].append((i,1))
for i,c in enumerate(n):
    if int(c) in lookup:lookup[int(c)].append((i,-1))
depth=[];ratio=[]
for c in ids:
    faces=lookup[int(c)];vi=np.unique(np.concatenate([f[i] for i,s in faces]));vertices=p[vi]
    fi=np.array([i for i,s in faces]);sign=np.array([s for i,s in faces]); normals=m['face_vectors'][fi]*sign[:,None]
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    distances=np.einsum('fvi,fi->fv',vertices[None,:,:]-m['face_centres'][fi,None,:],normals)
    d=max(0,float(distances.max()));depth.append(d);ratio.append(d/np.cbrt(m['volumes'][c]))
depth=np.array(depth);ratio=np.array(ratio);c=m['centres'][ids];L=.045/np.sin(np.deg2rad(70))
out={}
for name,mask in {'all':np.ones(len(ids),bool),'lower_outlet':(abs(c[:,0]-L)<.001)&(c[:,2]<.003)}.items():
    out[name]=dict(count=int(mask.sum()),depth_m_quantile_50_95_99_max=np.quantile(depth[mask],[.5,.95,.99,1]).tolist(),
        depth_over_cube_root_volume_quantile_50_95_99_max=np.quantile(ratio[mask],[.5,.95,.99,1]).tolist())
np.savez_compressed(case/'concavity_depth.npz',ids=ids,depth=depth,relative_depth=ratio)
(case/'concavity_depth.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
