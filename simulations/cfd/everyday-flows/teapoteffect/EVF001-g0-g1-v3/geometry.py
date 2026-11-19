"""EVF-001 analytic shell and plane clipping. All coordinates/lengths are SI.

Original case-local implementation; no copied upstream geometry.
Spout coordinates (s,y,w); w=0 is the rounded valley, not the virtual sharp edge.
"""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent


def load_config(path=ROOT / "parameters.json"):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    g = cfg["geometry"]
    g["length_m"] = g["upright_valley_rise_m"] / np.sin(np.deg2rad(g["upright_beta_deg"]))
    a = np.deg2rad(g["included_angle_deg"] / 2)
    if not 0 < a < np.pi / 2:
        raise ValueError("included_angle_deg must be between 0 and 180")
    if min(g[k] for k in ("length_m", "inner_radius_m", "thickness_m")) <= 0:
        raise ValueError("positive geometry dimensions required")
    if not np.isclose(2 * g["lip_radius_m"], g["thickness_m"], atol=1e-12):
        raise ValueError("semicircular lip requires radius=thickness/2, independent of R5")
    tangent_height = g["inner_radius_m"] * (1 - np.sin(a))
    if g["outlet_depth_m"] <= tangent_height:
        raise ValueError("rim must be above the valley fillet tangency")
    for key in ("case1", "case2"):
        c = cfg[key]
        if c["H_mode"] != "linear_between_endpoint_events":
            raise ValueError("unimplemented H_mode; do not silently infer liquid level")
        end = c["beta_start_deg"] - c["rate_deg_s"] * c["duration_s"]
        if not 0 < end <= c["beta_start_deg"] < 90:
            raise ValueError("this event template assumes uphill valley: 0 < beta < 90")
    return cfg


def rotation_y(degrees):
    c, s = np.cos(np.deg2rad(degrees)), np.sin(np.deg2rad(degrees))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def world(points, beta, cfg):
    """rW=Q (B rS-pB)+pW; Q rotates the kettle about its body y axis."""
    b = rotation_y(-cfg["geometry"]["upright_beta_deg"])
    q = rotation_y(cfg["geometry"]["upright_beta_deg"] - beta)
    return (np.asarray(points) @ b.T - cfg["rotation"]["pivot_body_m"]) @ q.T + cfg["rotation"][
        "pivot_world_m"
    ]


def profile(s, g, n_arc=80, n_side=40):
    """Inner profile and exact fluid-facing normals, ordered left to right.

    Side planes w=|y| cot(a)+R-R/sin(a); rim depth varies linearly in s.
    Therefore the two trimmed faces widen towards the outlet (pyramid-face
    approximation), rather than a shallow horizontal shelf.
    """
    a = np.deg2rad(g["included_angle_deg"] / 2)
    r = g["inner_radius_m"]
    phi = np.pi / 2 - a
    h = max(0.0, s / g["length_m"] * g["outlet_depth_m"])
    yt, wt = r * np.cos(a), r * (1 - np.sin(a))
    if h <= wt:
        if h == 0:
            return np.array([[s, 0.0, 0.0]]), np.array([[0.0, 0.0, 1.0]])
        phis = np.linspace(-np.arccos(1 - h / r), np.arccos(1 - h / r), n_arc + 1)
        p = np.column_stack((np.full(len(phis), s), r * np.sin(phis), r * (1 - np.cos(phis))))
        n = np.column_stack((np.zeros(len(phis)), -np.sin(phis), np.cos(phis)))
        return p, n
    ymax = yt + (h - wt) * np.tan(a)
    left_y = np.linspace(-ymax, -yt, n_side + 1)[:-1]
    right_y = np.linspace(yt, ymax, n_side + 1)[1:]
    phis = np.linspace(-phi, phi, n_arc + 1)
    y = np.r_[left_y, r * np.sin(phis), right_y]
    w = np.r_[
        -left_y / np.tan(a) + r - r / np.sin(a),
        r * (1 - np.cos(phis)),
        right_y / np.tan(a) + r - r / np.sin(a),
    ]
    ny = np.r_[np.full(n_side, np.cos(a)), -np.sin(phis), np.full(n_side, -np.cos(a))]
    nw = np.r_[np.full(n_side, np.sin(a)), np.cos(phis), np.full(n_side, np.sin(a))]
    return np.column_stack((np.full(len(y), s), y, w)), np.column_stack((np.zeros(len(y)), ny, nw))


def surface_grid(g, ns=40, n_arc=80, n_side=40):
    # Clip underlying triangular faces/cylinder by w <= D*s/L, not extrusion.
    p, _ = profile(g["length_m"], g, n_arc, n_side)
    start = g["length_m"] * p[:, 2] / g["outlet_depth_m"]
    grid = np.tile(p, (ns + 1, 1, 1))
    for i, fraction in enumerate(np.linspace(0, 1, ns + 1)):
        grid[i, :, 0] = start + fraction * (g["length_m"] - start)
    return grid


def grid_faces(rows, cols):
    f = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j
            f += [(a, a + cols, a + 1), (a + 1, a + cols, a + cols + 1)]
    return np.asarray(f, dtype=int)


def solid_mesh(g, ns=32, n_arc=64, n_side=24, n_lip=24):
    """Closed, oriented triangle shell, with normal-offset walls and rolled lip.

    Side rims and upstream cut are closed but sharp; only outlet is rounded.
    """
    p, n = profile(g["length_m"], g, n_arc, n_side)
    inner = list(surface_grid(g, ns, n_arc, n_side))
    outer = [p - g["thickness_m"] * n for p in inner]
    h = g["lip_radius_m"]
    roll = [
        p - h * n + h * np.cos(a) * n + np.array([h * np.sin(a), 0, 0])
        for a in np.linspace(0, np.pi, n_lip + 1)[1:-1]
    ]
    # Rings traverse inner -> lip -> outer (upstream), then wrap across inlet cut.
    rings = np.array(inner + roll + outer[::-1])
    nr, nq = rings.shape[:2]
    vertices = list(rings.reshape(-1, 3))
    faces = list(map(tuple, grid_faces(nr, nq)))
    for j in range(nq - 1):
        a, b = (nr - 1) * nq + j, j
        faces += [(a, b, a + 1), (a + 1, b, b + 1)]
    # Side-rim faces: strips between matching inner/outer longitudinal stations.
    for j in (0, nq - 1):
        reverse = j == 0
        for i in range(ns):
            a, b = i * nq + j, (i + 1) * nq + j
            d, c = (nr - 1 - i) * nq + j, (nr - 2 - i) * nq + j
            fs = [(a, b, d), (b, c, d)]
            faces += [tuple(reversed(f)) if reverse else f for f in fs]
        for i in range(ns + 1, ns + n_lip):
            f = (i * nq + j, (i + 1) * nq + j, ns * nq + j)
            faces.append(tuple(reversed(f)) if reverse else f)
    v, f = np.asarray(vertices), np.asarray(faces, dtype=int)
    # Triangular tips collapse structured-grid edges. Weld and remove only
    # zero-area faces; closedness/orientation are independently tested.
    _, first, inverse = np.unique(np.round(v, 13), axis=0, return_index=True, return_inverse=True)
    v, f = v[first], inverse[f]
    area2 = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    f = f[area2 > 1e-16]
    if signed_volume(v, f) < 0:
        f = f[:, ::-1]
    return v, f


def signed_volume(v, f):
    t = v[f]
    return np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6


def clip_polygon(poly, height):
    """Sutherland-Hodgman clipping by z <= height, no wetness dynamics."""
    result = []
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        da, db = a[2] - height, b[2] - height
        if da <= 0:
            result.append(a)
        if (da < 0 < db) or (db < 0 < da):
            result.append(a + da / (da - db) * (b - a))
    return np.asarray(result).reshape(-1, 3)


def polygon_area(poly):
    if len(poly) < 3:
        return 0.0
    return sum(
        np.linalg.norm(np.cross(poly[i] - poly[0], poly[i + 1] - poly[0])) / 2
        for i in range(1, len(poly) - 1)
    )


def submerged_surface(v, f, height):
    return sum(polygon_area(clip_polygon(tri, height)) for tri in v[f])


def intersections(v, f, height):
    """Plane-triangle segments (coplanar faces excluded)."""
    segments = []
    for tri in v[f]:
        d = tri[:, 2] - height
        if np.all(d > 0) or np.all(d < 0) or np.all(np.abs(d) < 1e-14):
            continue
        points = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if abs(d[i]) < 1e-14:
                points.append(tri[i])
            if d[i] * d[j] < 0:
                points.append(tri[i] + d[i] / (d[i] - d[j]) * (tri[j] - tri[i]))
        unique = []
        for p in points:
            if not any(np.linalg.norm(p - q) < 1e-12 for q in unique):
                unique.append(p)
        if len(unique) == 2:
            segments.append(unique)
    unique_segments = {}
    for segment in segments:
        key = tuple(sorted(tuple(np.round(p, 12)) for p in segment))
        unique_segments[key] = segment
    return np.asarray(list(unique_segments.values())).reshape(-1, 2, 3)


def section_metrics(points, height):
    """Wetted inner arc, transverse span, liquid section area (up to rim)."""
    wet = []
    length = 0.0
    for a, b in zip(points[:-1], points[1:]):
        da, db = a[2] - height, b[2] - height
        if da <= 0 and db <= 0:
            length += np.linalg.norm(b - a)
            wet += [a, b]
        elif da * db < 0:
            c = a + da / (da - db) * (b - a)
            q = a if da < 0 else b
            length += np.linalg.norm(q - c)
            wet += [q, c]
    width = np.ptp(np.array(wet)[:, 1]) if wet else 0.0
    return length, width, polygon_area(clip_polygon(points, height))


def history(t, case, cfg):
    c = cfg[case]
    beta = c["beta_start_deg"] - c["rate_deg_s"] * t
    start = world([0, 0, 0], c["beta_start_deg"], cfg)[2] + c["initial_depth_world_m"]
    end_beta = c["beta_start_deg"] - c["rate_deg_s"] * c["duration_s"]
    end = lip_crest_height(end_beta, cfg)
    height = start + (end - start) * t / c["duration_s"]
    z0 = world([0, 0, 0], beta, cfg)[2]
    front = (height - z0) / np.sin(np.deg2rad(beta))
    return beta, height, front


def lip_crest_height(beta, cfg):
    """Minimum over transverse lip paths of their maximum world elevation.

    For pure pitch and symmetric section the minimax path is y=0, and its
    crest is at roll angle theta=beta (NOT at the inner/outer seam).
    """
    g = cfg["geometry"]
    return world([g["length_m"], 0, 0], beta, cfg)[2] + g["lip_radius_m"] * (
        1 - np.cos(np.deg2rad(beta))
    )


def inner_seam_contact_time(case, cfg):
    """Bisection for the pre-crest seam-contact event in the current histories."""

    def clearance(t):
        beta, height, _ = history(t, case, cfg)
        return world([cfg["geometry"]["length_m"], 0, 0], beta, cfg)[2] - height

    lo, hi = 0.0, cfg[case]["duration_s"]
    if clearance(lo) <= 0:
        return lo
    if clearance(hi) > 0:
        raise ValueError("history never reaches inner lip seam")
    for _ in range(60):
        mid = (lo + hi) / 2
        if clearance(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def write_stl(path, vertices, faces):
    import struct

    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    with Path(path).open("wb") as stream:
        stream.write(b"EVF001 parametric SI solid; NOT calibrated".ljust(80, b" "))
        stream.write(struct.pack("<I", len(faces)))
        for n, tri in zip(normals, triangles):
            stream.write(struct.pack("<12fH", *n, *tri.ravel(), 0))
