import unittest

import numpy as np

from foam_io import geometry
from map_inlet import integrate_faces, interpolate


class MappingTests(unittest.TestCase):
    def test_translated_cube_volume_and_centroid(self):
        points=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],
                         [0,0,1],[1,0,1],[1,1,1],[0,1,1]],dtype=float)*.002+[.04,-.01,.02]
        faces=[np.array(f) for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),
                                     (1,2,6,5),(2,3,7,6),(3,0,4,7))]
        cf,sf,c,v=geometry(points,faces,np.zeros(6,dtype=int),np.array([],dtype=int))
        np.testing.assert_allclose(v,[8e-9],rtol=1e-12)
        np.testing.assert_allclose(c,[[.041,-.009,.021]],atol=1e-14)
        np.testing.assert_allclose(sf.sum(axis=0),0,atol=1e-16)

    def test_bilinear_linear_interior(self):
        y=np.linspace(-.003,.003,7); z=np.linspace(.0001,.0031,7)
        yy,zz=np.meshgrid(y,z,indexing='ij'); field=2+20*yy+100*zz
        sy=np.array([-.00125,.00065]); sz=np.array([.0009,.0017])
        np.testing.assert_allclose(interpolate(sy,sz,y,z,field),2+20*sy+100*sz)

    def test_partial_face_phase_flux(self):
        points=np.array([[.04,-.001,.001],[.04,-.001,.003],
                         [.04,.001,.003],[.04,.001,.001]])
        source={'y':np.linspace(-.004,.004,9),'w':np.linspace(.0001,.0041,9),
                'U_s':np.full((9,9),.2)}
        alpha,u,area=integrate_faces(points,[np.arange(4)],[0],source,.002,n=6)
        np.testing.assert_allclose(alpha,[.5],atol=1e-12)
        np.testing.assert_allclose(alpha*u*area,[4e-7],rtol=1e-12)


if __name__=='__main__':unittest.main(verbosity=2)
