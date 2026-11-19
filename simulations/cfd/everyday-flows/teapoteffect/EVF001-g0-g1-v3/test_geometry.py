"""Numerical verification only; these tests do not validate a real kettle."""

import copy
import unittest
from collections import Counter

import numpy as np
from geometry import (
    clip_polygon,
    history,
    inner_seam_contact_time,
    intersections,
    lip_crest_height,
    load_config,
    polygon_area,
    profile,
    rotation_y,
    section_metrics,
    signed_volume,
    solid_mesh,
    world,
)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.g = self.cfg["geometry"]

    def test_seam_contact_precedes_crest(self):
        for case in ("case1", "case2"):
            t = inner_seam_contact_time(case, self.cfg)
            self.assertLess(t, self.cfg[case]["duration_s"])
            beta, height, _ = history(t, case, self.cfg)
            self.assertAlmostEqual(world([self.g["length_m"], 0, 0], beta, self.cfg)[2], height)

    def test_rotation_and_gravity_sign(self):
        for beta in (25, 40, 55, 70):
            r = rotation_y(-beta)
            np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-14)
            self.assertAlmostEqual(np.linalg.det(r), 1)
            delta = world([1, 0, 0], beta, self.cfg) - world([0, 0, 0], beta, self.cfg)
            self.assertAlmostEqual(delta[2], np.sin(np.deg2rad(beta)))
            self.assertLess(np.dot([0, 0, -9.81], delta), 0)

    def test_pivot_maps_to_fixed_world_point(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["rotation"]["pivot_body_m"] = [0.01, -0.02, 0.03]
        cfg["rotation"]["pivot_world_m"] = [0.1, 0.2, 0.3]
        p = rotation_y(70) @ cfg["rotation"]["pivot_body_m"]
        for beta in (25, 55):
            np.testing.assert_allclose(world(p, beta, cfg), [0.1, 0.2, 0.3], atol=1e-14)

    def test_radius_thickness_and_tangency(self):
        length = self.g["length_m"]
        p, n = profile(length, self.g, 80, 40)
        arc = p[40:121]
        center = [length, 0, 0.005]
        np.testing.assert_allclose(np.linalg.norm(arc - center, axis=1), 0.005, atol=1e-14)
        outer = p - 0.0012 * n
        np.testing.assert_allclose(np.linalg.norm(outer - p, axis=1), 0.0012, atol=1e-14)
        np.testing.assert_allclose(n[39], n[40], atol=1e-14)
        np.testing.assert_allclose(n[120], n[121], atol=1e-14)
        self.assertAlmostEqual(p[:, 2].max(), 0.025)
        self.assertAlmostEqual(p[:, 2].min(), 0)
        # Plane normals have zero s component: exact longitudinal tangency to lip.
        self.assertTrue(np.all(n[:, 0] == 0))

    def test_watertight_oriented_mesh_and_lip_extent(self):
        v, f = solid_mesh(self.g)
        directed = Counter((int(a), int(b)) for tri in f for a, b in zip(tri, np.roll(tri, -1)))
        self.assertTrue(
            all(count == 1 and directed[b, a] == 1 for (a, b), count in directed.items())
        )
        self.assertEqual(len(v) - len(directed) // 2 + len(f), 2)
        self.assertGreater(signed_volume(v, f), 0)
        areas = (
            np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2
        )
        self.assertGreater(areas.min(), 1e-14)
        self.assertAlmostEqual(v[:, 0].max(), self.g["length_m"] + 0.0006)

    def test_exact_partial_circle_and_refinement(self):
        height, r = 0.001, 0.005
        theta = np.arccos(1 - height / r)
        exact_p = 2 * r * theta
        exact_a = r * r * (theta - np.sin(theta) * np.cos(theta))
        errors = []
        for n in (40, 80, 160):
            p, _ = profile(0.04, self.g, n, 20)
            wet_p, width, area = section_metrics(p, height)
            errors.append(abs(wet_p - exact_p))
            self.assertLess(abs(area - exact_a), 2e-8)
            self.assertLess(abs(width - 2 * r * np.sin(theta)), 1e-5)
        self.assertLess(errors[-1], errors[0] / 3)
        self.assertLess(errors[-1], 1e-6)

    def test_triangle_clip_and_plane_intersection(self):
        tri = np.array([[0.0, 0, 0], [1, 0, 0], [0, 0, 1]])
        self.assertAlmostEqual(polygon_area(clip_polygon(tri, 0.5)), 0.375)
        seg = intersections(tri, np.array([[0, 1, 2]]), 0.5)
        np.testing.assert_allclose(seg[:, :, 2], 0.5)
        self.assertAlmostEqual(np.linalg.norm(seg[0, 1] - seg[0, 0]), 0.5)

    def test_case_events_and_lip_crest(self):
        for case in ("case1", "case2"):
            c = self.cfg[case]
            for t in np.linspace(0, c["duration_s"], 31):
                beta, height, front = history(t, case, self.cfg)
                self.assertGreaterEqual(front, -1e-14)
                clearance = lip_crest_height(beta, self.cfg) - height
                self.assertGreaterEqual(clearance, -1e-14)
                if t < c["duration_s"]:
                    self.assertGreater(clearance, 0)
            beta, height, _ = history(c["duration_s"], case, self.cfg)
            self.assertAlmostEqual(height, lip_crest_height(beta, self.cfg))
        self.assertEqual(history(0, "case1", self.cfg)[2], 0)
        self.assertGreater(history(0, "case2", self.cfg)[2], 0)
        self.assertEqual(history(3, "case1", self.cfg)[0], 25)
        self.assertEqual(history(0, "case2", self.cfg)[0], 70)
        self.assertEqual(history(1.5, "case2", self.cfg)[0], 55)

    def test_triangular_trim_and_height_definition(self):
        length = self.g["length_m"]
        self.assertAlmostEqual(length * np.sin(np.deg2rad(70)), 0.045)
        p0, _ = profile(0, self.g)
        self.assertEqual(len(p0), 1)
        half, _ = profile(length / 2, self.g)
        end, _ = profile(length, self.g)
        self.assertLess(np.ptp(half[:, 1]), np.ptp(end[:, 1]))
        self.assertAlmostEqual(half[:, 2].max(), self.g["outlet_depth_m"] / 2)

    def test_lip_minimax_and_tangent_continuity(self):
        h = self.g["lip_radius_m"]
        p, n = profile(self.g["length_m"], self.g)
        for beta in (25, 55):
            angle = np.deg2rad(beta)
            center = p - h * n
            # Each transverse point has a maximum along its semicircular path.
            nz = n[:, 2] * np.cos(angle)
            maxima = world(center, beta, self.cfg)[:, 2] + h * np.hypot(np.sin(angle), nz)
            self.assertAlmostEqual(maxima.min(), lip_crest_height(beta, self.cfg))
            self.assertGreater(
                lip_crest_height(beta, self.cfg), world(p[len(p) // 2], beta, self.cfg)[2]
            )
        # Roll tangent at theta=0 / pi is +/- s, tangent to both wall surfaces.
        np.testing.assert_allclose(n[:, 0], 0)

    def test_pure_pitch_has_horizontal_transverse_intersection(self):
        p, _ = profile(0.04, self.g)
        wp = world(p, 40, self.cfg)
        np.testing.assert_allclose(
            wp[:, 2], 0.04 * np.sin(np.deg2rad(40)) + p[:, 2] * np.cos(np.deg2rad(40)), atol=1e-14
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
