"""Full original STL plus computed interface; upstream solid is context, not CFD.

Usage: python g3_fixed/plot_full_spout.py CASE [TIME ...]
SI input, mm display. Local (s,y,w); fixed pose/gravity recorded in case.
No reconstructed water is drawn upstream of s=0.8L.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

def read_binary_stl(path):
    raw=Path(path).read_bytes()
    count=int.from_bytes(raw[80:84],'little')
    if len(raw)!=84+50*count:raise ValueError('Expected exact binary STL')
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    return np.frombuffer(raw,offset=84,count=count,dtype=dtype)['vertices'].astype(float)

def main(case,times):
    solid=read_binary_stl(case/'constant/triSurface/spout.stl')*1000
    out=case/'full_spout_figures';out.mkdir(exist_ok=True)
    files=sorted((case/'interface_exports').glob('*.npz'),key=lambda p:float(p.stem))
    if times:files=[p for p in files if any(abs(float(p.stem)-t)<1e-9 for t in times)]
    L=45/np.sin(np.deg2rad(70));sin=.8*L
    frames=[]
    for file in files:
        dest=out/f'full_spout_{file.stem}.png'
        if not dest.exists() or dest.stat().st_mtime<max(file.stat().st_mtime,Path(__file__).stat().st_mtime):
            d=np.load(file);p=d['points']*1000;tri=d['triangles'];u=d['U']
            speeds=np.linalg.norm(u,axis=1);colors=plt.cm.viridis(np.clip(speeds[tri].mean(axis=1)/.8,0,1))
            fig=plt.figure(figsize=(15,7))
            for j,(elev,azim) in enumerate(((26,-115),(-20,-105))):
                ax=fig.add_subplot(1,2,j+1,projection='3d')
                ax.add_collection3d(Poly3DCollection(solid,facecolor='#999999',edgecolor='none',alpha=.22))
                ax.add_collection3d(Poly3DCollection(p[tri],facecolors=colors,edgecolor='none',alpha=.95))
                ax.plot([sin,sin],[-18,18],[0,0],color='red',lw=2,label='CFD inlet s=0.8L')
                ax.set(xlim=(0,70),ylim=(-20,20),zlim=(-20,30),xlabel='s [mm]',ylabel='y [mm]',zlabel='w [mm]')
                ax.set_box_aspect((70,40,50));ax.view_init(elev,azim);ax.legend(loc='upper left')
                ax.set_title('Full solid + computed interface' if j==0 else 'Underside view: same fixed solid and time')
            fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0,.8),cmap='viridis'),ax=fig.axes,shrink=.6,label='Interface |U| [m/s]',extend='max')
            fig.suptitle(f'{case.name}, t={float(file.stem):.4f} s\nGrey: original STL; upstream of red inlet is geometry context only. Static local coordinates.')
            fig.savefig(dest,dpi=130);plt.close(fig)
        frames.append(Image.open(dest).convert('RGB'))
    if frames:frames[0].save(out/'full_spout_evolution.gif',save_all=True,append_images=frames[1:],duration=400,loop=0)
    print(f'{case.name}: {len(frames)} full-solid frames')

if __name__=='__main__':main(Path(sys.argv[1]),[float(s) for s in sys.argv[2:]])
