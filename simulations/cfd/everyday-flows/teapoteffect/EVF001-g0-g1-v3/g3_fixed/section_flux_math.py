"""Integral of two linear nodal fields over a triangular planar surface."""
import numpy as np

def linear_product_integral(points,triangles,a,u):
    tri=points[triangles]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    av=a[triangles];uv=u[triangles]
    return float(np.sum(area*(av.sum(axis=1)*uv.sum(axis=1)+(av*uv).sum(axis=1))/12))
