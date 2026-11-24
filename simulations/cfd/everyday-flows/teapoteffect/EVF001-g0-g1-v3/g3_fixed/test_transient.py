import tempfile
import unittest
from pathlib import Path
import numpy as np
from postprocess_transient import connected_wet,patch_scalar,classify_wall
from section_flux_math import linear_product_integral
from compare_development import event_bracket

class TransientTests(unittest.TestCase):
    def test_event_is_bracketed_not_exact(self):
        rows=[{'time_s':t,'x':x} for t,x in [(0,0),(.005,.2),(.01,.8)]]
        self.assertEqual(event_bracket(rows,'x',.5),[.005,.01])
        self.assertIsNone(event_bracket(rows,'x',1))
        self.assertEqual(event_bracket(rows,'x',-.1),[0,0])
    def test_triangle_flux_quadrature(self):
        p=np.array([[0,0,0],[0,2,0],[0,0,1.]])
        f=np.array([[0,1,2]])
        self.assertAlmostEqual(linear_product_integral(p,f,np.ones(3),np.full(3,.2)),.2)
        self.assertAlmostEqual(linear_product_integral(p,f,np.array([1.,0,0]),np.array([1.,0,0])),1/6)
    def test_analytic_inner_outer_lip_classification(self):
        L=.048;ny=-np.sqrt(3)/2
        p=np.array([[.04,0,0],[.04,0,-.0012],[L+.0006,0,-.0006],
                    [.04,.01-.0012*ny,np.sqrt(3)*.01-.005-.0006]])
        normals=np.array([[0,0,-1],[0,0,1],[-1,0,0],[0,ny,.5]])
        outer,lip,distance=classify_wall(p,normals,L)
        np.testing.assert_array_equal(outer,[False,True,False,True])
        np.testing.assert_array_equal(lip,[False,False,True,False])
        np.testing.assert_allclose(distance[[1,3]],-.0012,atol=1e-15)
    def test_isolated_droplet_not_attachment(self):
        adj=[{1},{0,2},{1},set()]
        np.testing.assert_array_equal(connected_wet(np.array([1,1,0,1],bool),adj,[0]),[0,1])
    def test_dry_lip_does_not_seed_attachment(self):
        self.assertEqual(len(connected_wet(np.array([0,1],bool),[{1},{0}],[0])),0)
    def test_wall_patch_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'alpha.water'
            p.write_text('spout\n{\ntype constantAlphaContactAngle;\nvalue nonuniform List<scalar> 3\n(0.1 0.5 0.9);\n}\n')
            np.testing.assert_allclose(patch_scalar(p,'spout',3),[.1,.5,.9])

if __name__=='__main__':unittest.main()
