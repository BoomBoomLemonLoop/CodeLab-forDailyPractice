"""Plot computed isosurfaces, velocity arrows and wetting/balance histories."""
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
from foam_io import read_mesh

case=Path(sys.argv[1]);p,f,ow,ne,patch=read_mesh(case)
out=case/'transient_figures';out.mkdir(exist_ok=True)
wall=patch['spout'];wf=f[wall['startFace']:wall['startFace']+wall['nFaces']]
wall_centres=np.array([p[fa].mean(axis=0) for fa in wf])
wall_zoom=[p[fa]*1000 for fa,c in zip(wf,wall_centres) if .042<c[0]<.053 and abs(c[1])<.007 and -.004<c[2]<.008]
files=sorted((case/'interface_exports').glob('*.npz'),key=lambda f:float(f.stem))
frames=[]
for file in files:
    path=out/f'interface_{file.stem}.png'
    if path.exists() and path.stat().st_mtime>max(file.stat().st_mtime,Path(__file__).stat().st_mtime):
        frames.append(Image.open(path).convert('RGB'));continue
    data=np.load(file);pts=data['points']*1000;tri=data['triangles'];u=data['U'];speed=np.linalg.norm(u,axis=1)
    fig=plt.figure(figsize=(12,6));ax=fig.add_subplot(121,projection='3d')
    ax.add_collection3d(Poly3DCollection(wall_zoom,facecolor='lightgray',edgecolor='none',alpha=.15))
    tc=pts[tri].mean(axis=1);tri=tri[(tc[:,0]>42)&(tc[:,0]<53)&(abs(tc[:,1])<7)&(tc[:,2]>-4)&(tc[:,2]<8)]
    color=plt.cm.viridis(np.clip(speed[tri].mean(axis=1)/.8,0,1))
    ax.add_collection3d(Poly3DCollection(pts[tri],facecolors=color,edgecolor='none',alpha=.9))
    sel=np.where((pts[:,0]>46)&(abs(pts[:,1])<4))[0][::max(1,len(pts)//300)]
    if len(sel):ax.quiver(*pts[sel].T,*(u[sel]*1.5).T,length=1,normalize=False,color='black',linewidth=.5)
    ax.set(xlim=(42,53),ylim=(-7,7),zlim=(-4,8),xlabel='s [mm]',ylabel='y [mm]',zlabel='w [mm]')
    ax.view_init(22,-110);ax.set_title('Computed alpha=0.5 surface and U vectors')
    ax=fig.add_subplot(122)
    mask=abs(pts[:,1])<.5
    sc=ax.scatter(pts[mask,0],pts[mask,2],c=speed[mask],s=3,vmin=0,vmax=.8,cmap='viridis')
    centres=wall_centres;maskwall=abs(centres[:,1])<.0005
    ax.scatter(centres[maskwall,0]*1000,centres[maskwall,2]*1000,c='gray',s=2)
    ax.set(xlim=(45,52),ylim=(-4,5),aspect='equal',xlabel='s [mm]',ylabel='w [mm]',title='Interface points in |y|<0.5 mm slab')
    fig.colorbar(sc,ax=ax,label='|U| [m/s]',extend='max')
    fig.suptitle(f'{case.name}: CFD time {float(file.stem):.4f} s (transient, unvalidated mesh)')
    fig.tight_layout();path=out/f'interface_{file.stem}.png';fig.savefig(path,dpi=130);plt.close(fig)
    frames.append(Image.open(path).convert('RGB'))
if frames:frames[0].save(out/'interface_evolution.gif',save_all=True,append_images=frames[1:],duration=350,loop=0)
report=json.loads((case/'transient_metrics.json').read_text());rows=report['series'];t=np.array([r['time_s'] for r in rows])
fig,axes=plt.subplots(2,2,figsize=(11,8))
for threshold in (.1,.5,.9):
    axes[0,0].plot(t,[r[f'outer_area_alpha{threshold}_m2']*1e6 for r in rows],label=f'alpha>={threshold}')
    axes[0,1].plot(t,[r[f'attached_length_alpha{threshold}_m']*1000 for r in rows],label=f'alpha>={threshold}')
axes[0,0].set(ylabel='Outer wet area [mm2]');axes[0,1].set(ylabel='Connected axial wet extent [mm]')
axes[1,0].plot(t,[r['max_wet_lip_angle_deg'] for r in rows]);axes[1,0].set(ylabel='Maximum wet lip angle [deg]')
axes[1,1].plot(t,[r['water_balance_residual_m3']*1e9 for r in rows]);axes[1,1].set(ylabel='Water balance residual [microlitre]')
for ax in axes.flat:ax.set_xlabel('CFD time [s]');ax.grid(alpha=.3)
axes[0,0].legend();axes[0,1].legend();fig.tight_layout();fig.savefig(out/'wetting_and_balance.png',dpi=160)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(14,4))
for threshold in (.1,.5,.9):
    axes[0].plot(t,[r[f'connected_lower_lip_area_alpha{threshold}_m2']*1e6 for r in rows],label=f'alpha>={threshold}')
    axes[1].plot(t,[r[f'connected_lip_angle_alpha{threshold}_deg'] for r in rows],label=f'alpha>={threshold}')
    axes[2].plot(t,[r[f'connected_lip_arc_alpha{threshold}_m']*1000 for r in rows],label=f'alpha>={threshold}')
axes[0].set_ylabel('Connected lower lip wet area [mm2]')
axes[1].set_ylabel('Connected wet lip angle [deg]');axes[1].axhline(90,color='gray',ls='--',lw=1)
axes[2].set_ylabel('Wet lip arc R*theta [mm]')
for ax in axes:ax.set_xlabel('CFD time [s]');ax.grid(alpha=.3);ax.legend()
fig.suptitle('Rounded lip attachment; separate from straight outer-wall wetting')
fig.tight_layout();fig.savefig(out/'lip_attachment.png',dpi=160);plt.close(fig)
