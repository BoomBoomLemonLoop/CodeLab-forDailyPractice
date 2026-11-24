"""ASCII OpenFOAM polyMesh reader and oriented polyhedral geometry, SI units."""
import re
from pathlib import Path

import numpy as np


def list_body(path):
    text=Path(path).read_text()
    if re.search(r'format\s+binary',text):
        raise ValueError(f'ASCII required: {path}')
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    match=re.search(r'\b(\d+)\s*\(',text[text.index('}')+1:])
    rest=text[text.index('}')+1:]
    start=match.end()
    return int(match[1]),rest[start:rest.rfind(')')]


def read_mesh(case):
    root=Path(case)/'constant/polyMesh'
    count,body=list_body(root/'points')
    points=np.fromstring(body.replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
    assert len(points)==count
    count,body=list_body(root/'faces')
    faces=[np.fromstring(s,sep=' ',dtype=int) for s in re.findall(r'\d+\s*\(([^()]*)\)',body)]
    assert len(faces)==count
    owner=np.fromstring(list_body(root/'owner')[1],sep=' ',dtype=int)
    neighbour=np.fromstring(list_body(root/'neighbour')[1],sep=' ',dtype=int)
    _,body=list_body(root/'boundary')
    patches={}
    for name,values in re.findall(r'(\w+)\s*\{([^{}]+)\}',body):
        patches[name]={key:int(re.search(key+r'\s+(\d+)',values)[1]) for key in ('startFace','nFaces')}
    return points,faces,owner,neighbour,patches


def geometry(points,faces,owner,neighbour):
    """Tetrahedral divergence identities, outward face orientation for owner."""
    nfaces=len(faces); ncells=int(max(owner.max(),neighbour.max(initial=0)))+1
    sf=np.zeros((nfaces,3)); cf=np.zeros((nfaces,3)); area=np.zeros(nfaces)
    facevol=np.zeros(nfaces); facemoment=np.zeros((nfaces,3))
    sizes=np.array([len(f) for f in faces])
    for size in np.unique(sizes):
        ids=np.where(sizes==size)[0]
        poly=points[np.array([faces[i] for i in ids])]
        for j in range(1,size-1):
            a,b,c=poly[:,0],poly[:,j],poly[:,j+1]
            vec=np.cross(b-a,c-a)/2
            weight=np.linalg.norm(vec,axis=1)
            sf[ids]+=vec; area[ids]+=weight; cf[ids]+=weight[:,None]*(a+b+c)/3
            volume=np.einsum('ij,ij->i',a,np.cross(b,c))/6
            facevol[ids]+=volume
            facemoment[ids]+=volume[:,None]*(a+b+c)/4
    cf/=area[:,None]
    volumes=np.bincount(owner,weights=facevol,minlength=ncells)
    volumes-=np.bincount(neighbour,weights=facevol[:len(neighbour)],minlength=ncells)
    centres=np.zeros((ncells,3))
    for k in range(3):
        centres[:,k]=np.bincount(owner,weights=facemoment[:,k],minlength=ncells)
        centres[:,k]-=np.bincount(neighbour,weights=facemoment[:len(neighbour),k],minlength=ncells)
    if volumes.min()<=0: raise ValueError('nonpositive polyhedron volume')
    centres/=volumes[:,None]
    return cf,sf,centres,volumes


def field_values(path):
    text=Path(path).read_text()
    match=re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;',text,re.S)
    if not match:
        uniform=re.search(r'internalField\s+uniform\s+([^;]+);',text)
        return np.fromstring(uniform[1].replace('(','').replace(')',''),sep=' ')
    values=np.fromstring(match[2].replace('(',' ').replace(')',' '),sep=' ')
    return values.reshape(int(match[1]),-1).squeeze()
