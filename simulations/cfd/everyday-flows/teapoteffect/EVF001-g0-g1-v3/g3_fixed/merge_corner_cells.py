"""Conservatively merge under-determined dry inlet-rim cells with a neighbour.

Preserves every boundary polygon and point, removes only shared INTERNAL faces.
Writes a separate case; no deletion or displacement of the physical boundary.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

from foam_io import geometry, list_body, read_mesh
from make_cases import foam


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path); parser.add_argument('destination',type=Path)
    args=parser.parse_args(); src=args.source.resolve(); dst=args.destination.resolve()
    if src.parent!=dst.parent or dst.exists():raise ValueError('new sibling case required')
    pts,faces,owner,neighbour,patches=read_mesh(src)
    cf,sf,centres,volumes=geometry(pts,faces,owner,neighbour)
    bad=np.fromstring(list_body(src/'constant/polyMesh/sets/cellDeterminant')[1],sep=' ',dtype=int)
    assert len(bad)<100
    assert np.all(centres[bad,0]<pts[:,0].min()+.0003)
    assert np.all(centres[bad,2]>.018), 'only dry upper rim cells may be merged by this repair'
    root=np.arange(len(centres)); merges=[]
    def find(c):
        while root[c]!=c:
            root[c]=root[root[c]];c=root[c]
        return c
    ni=len(neighbour)
    for cell in bad:
        ids=np.where((owner[:ni]==cell)|(neighbour==cell))[0]
        other=np.where(owner[ids]==cell,neighbour[ids],owner[ids])
        allowed=np.array([find(int(c))!=find(int(cell)) for c in other])
        if not allowed.any():continue
        ids,other=ids[allowed],other[allowed]
        scores=np.linalg.norm(sf[ids],axis=1)
        inward=centres[other,0]>centres[cell,0]
        if inward.any():scores=np.where(inward,scores,-1)
        target=int(other[np.argmax(scores)])
        root[find(int(cell))]=find(target); merges.append((int(cell),target))
    labels=np.array([find(i) for i in range(len(root))])
    _,labels=np.unique(labels,return_inverse=True)
    ow=labels[owner]; ne=labels[neighbour]
    keep=np.where(ow[:ni]!=ne)[0]
    newfaces=[]; newow=[];newne=[]
    order=keep[np.lexsort((np.maximum(ow[keep],ne[keep]),np.minimum(ow[keep],ne[keep])))]
    for i in order:
        reverse=ow[i]>ne[i]
        newfaces.append(faces[i][::-1] if reverse else faces[i])
        newow.append(min(ow[i],ne[i]));newne.append(max(ow[i],ne[i]))
    newfaces.extend(faces[ni:]);newow.extend(ow[ni:])
    newow=np.asarray(newow);newne=np.asarray(newne)
    _,_,newc,newv=geometry(pts,newfaces,newow,newne)
    np.testing.assert_allclose(newv.sum(),volumes.sum(),rtol=1e-12)
    for folder in ('0','system'):shutil.copytree(src/folder,dst/folder)
    (dst/'constant').mkdir(exist_ok=True)
    for path in (src/'constant').iterdir():
        if path.name=='polyMesh':continue
        if path.is_dir():shutil.copytree(path,dst/'constant'/path.name)
        else:shutil.copy2(path,dst/'constant'/path.name)
    shutil.copy2(src/'CASE_STATUS.json',dst/'CASE_STATUS.json')
    mesh=dst/'constant/polyMesh';mesh.mkdir()
    def write(name,cls,data,count):
        (mesh/name).write_text(foam(name,cls,'constant/polyMesh')+f'{count}\n(\n'+data+'\n)\n')
    write('points','vectorField','\n'.join('('+' '.join(f'{x:.17g}' for x in p)+')' for p in pts),len(pts))
    write('faces','faceList','\n'.join(f'{len(f)}('+ ' '.join(map(str,f))+')' for f in newfaces),len(newfaces))
    write('owner','labelList','\n'.join(map(str,newow)),len(newow))
    write('neighbour','labelList','\n'.join(map(str,newne)),len(newne))
    body=[]
    for name,p in patches.items():
        start=p['startFace']-ni+len(newne)
        typ='wall' if name.startswith('spout') else 'patch'
        body.append(f'{name}\n{{ type {typ}; nFaces {p["nFaces"]}; startFace {start}; }}')
    write('boundary','polyBoundaryMesh','\n'.join(body),len(body))
    report=dict(source=str(src),cells_before=len(volumes),cells_after=len(newv),merges=merges,
                removed_internal_faces=ni-len(newne),boundary_faces_preserved=len(faces)-ni,
                relative_volume_change=float((newv.sum()-volumes.sum())/volumes.sum()),
                boundary_point_displacement_m=0.)
    (dst/'mesh_repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()
