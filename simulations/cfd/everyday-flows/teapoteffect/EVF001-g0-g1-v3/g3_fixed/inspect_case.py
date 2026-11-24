"""Actual mesh/initial field visualization and inlet quadrature audit."""
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from foam_io import read_mesh
from map_inlet import integrate_faces, ROOT

case=Path(sys.argv[1])
p,f,o,ne,patches=read_mesh(case)
m=np.load(case/'mesh_metrics.npz')
report=json.loads((case/'mapping_report.json').read_text())
state=json.loads((ROOT/'artifacts/g2_fixed_state.json').read_text())['cases'][report['source_case']]
source=np.load(ROOT/'artifacts/g2_momentum'/f'{report["source_case"]}.npz')
patch=patches['waterInlet']; ids=np.arange(patch['startFace'],patch['startFace']+patch['nFaces'])
audit=[]
for n in (3,6,12,24,48):
    a,u,area=integrate_faces(p,f,ids,source,state['baseline_section']['local_water_height_w_m'],n)
    audit.append(dict(subdivision=n,Q_m3_s=float(np.sum(a*u*(-m['face_vectors'][ids,0]))),area_m2=float(np.sum(a*area))))
(case/'quadrature_audit.json').write_text(json.dumps(audit,indent=2))
fig=plt.figure(figsize=(14,9))
ax=fig.add_subplot(221,projection='3d')
wall=patches['spout']; wi=np.arange(wall['startFace'],wall['startFace']+wall['nFaces'])
ax.add_collection3d(Poly3DCollection([p[f[i]]*1000 for i in wi],facecolor='lightgray',edgecolor='gray',linewidth=.08,alpha=.5))
c=m['centres']*1000; seed=m['seed']
ax.scatter(*c[seed][::3].T,s=1,color='royalblue')
ax.set(xlim=(38,52),ylim=(-18,18),zlim=(-2,27),xlabel='s [mm]',ylabel='y [mm]',zlabel='w [mm]',title='Actual solid boundary + inner water seed')
ax.view_init(25,-125)
table=np.loadtxt(case/'inlet_mapping.csv',delimiter=',',skiprows=1)
ax=fig.add_subplot(222)
sc=ax.scatter(table[:,1]*1000,table[:,2]*1000,c=table[:,7],s=12)
fig.colorbar(sc,ax=ax,label='U_s [m/s]')
ax.set(xlabel='y [mm]',ylabel='w [mm]',title='Actual inlet face mean liquid velocity',aspect='equal')
ax=fig.add_subplot(223)
sc=ax.scatter(table[:,1]*1000,table[:,2]*1000,c=table[:,6],s=12,vmin=0,vmax=1)
fig.colorbar(sc,ax=ax,label='alpha.water')
ax.set(xlabel='y [mm]',ylabel='w [mm]',title='Fractional inlet liquid coverage',aspect='equal')
ax=fig.add_subplot(224)
cf=m['face_centres']*1000
cut=np.abs(cf[:,1])<.08
ax.scatter(cf[cut,0],cf[cut,2],s=.2,c='gray')
sel=seed&(np.abs(c[:,1])<.55)
ax.scatter(c[sel,0],c[sel,2],s=2,c='royalblue')
ax.set(xlim=(38,52),ylim=(-2,max(8,state['baseline_section']['local_water_height_w_m']*1000+1)),xlabel='s [mm]',ylabel='w [mm]',title='Centre-plane faces / liquid cells in 1.1 mm slab',aspect='equal')
fig.tight_layout();fig.savefig(case/'mesh_and_inlet.png',dpi=170);plt.close(fig)
(case/'view.foam').touch()
print(json.dumps(audit,indent=2))
