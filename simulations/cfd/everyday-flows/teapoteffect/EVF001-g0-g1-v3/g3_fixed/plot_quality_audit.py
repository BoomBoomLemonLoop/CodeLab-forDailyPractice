import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

case=Path(sys.argv[1]);m=dict(np.load(case/'mesh_metrics.npz'));q=np.load(case/'concavity_depth.npz')
c=m['centres'][q['ids']]*1000;dep=q['depth']*1e6
fig=plt.figure(figsize=(12,5));ax=fig.add_subplot(121,projection='3d')
sc=ax.scatter(*c.T,c=dep,s=1,cmap='magma',vmin=0,vmax=125)
ax.set(xlabel='s [mm]',ylabel='y [mm]',zlabel='w [mm]',title='9420 cells flagged by detailed checkMesh');ax.view_init(25,-110)
ax=fig.add_subplot(122);mask=(abs(c[:,1])<3)&(c[:,2]<3)&(c[:,0]>46)
sc=ax.scatter(c[mask,0],c[mask,2],c=dep[mask],s=10,cmap='magma',vmin=0,vmax=125)
ax.set(xlabel='s [mm]',ylabel='w [mm]',title='Lower outlet, |y|<3 mm',aspect='equal')
fig.colorbar(sc,ax=ax,label='Maximum face-plane violation [micrometre]')
fig.tight_layout();fig.savefig(case/'concavity_locations.png',dpi=170)
