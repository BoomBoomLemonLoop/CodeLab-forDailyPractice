"""Independent analytic solid-volume and refinement evidence, plus legacy hashes."""

import hashlib
import json

import numpy as np
from geometry import ROOT, load_config, profile, section_metrics, signed_volume, solid_mesh


def analytic_volume(g):
    a = np.deg2rad(g["included_angle_deg"] / 2)
    phi = np.pi / 2 - a
    r, thickness = g["inner_radius_m"], g["thickness_m"]

    def perimeter(depth):
        return 2 * r * phi + 2 * (depth - r * (1 - np.sin(a))) / np.cos(a)

    depth, length = g["outlet_depth_m"], g["length_m"]
    tangent_w = r * (1 - np.sin(a))
    outlet = perimeter(depth)
    # Integral over transverse arclength q and normal offset u, weighted by
    # available axial extent L*(1-w(q)/D). The curved strip Jacobian is 1+u/R.
    curved = (
        (thickness * r + thickness**2 / 2)
        * length
        * (2 * phi * (1 - r / depth) + 2 * r / depth * np.sin(phi))
    )
    planar = (
        2
        * thickness
        * length
        / np.cos(a)
        * (depth - tangent_w - (depth**2 - tangent_w**2) / (2 * depth))
    )
    shell = curved + planar
    h = g["lip_radius_m"]
    lip = np.pi * h**2 / 2 * (outlet + 2 * phi * h)
    return shell + lip


def main():
    g = load_config()["geometry"]
    exact = analytic_volume(g)
    evidence = {"analytic_solid_volume_m3": float(exact), "refinement": []}
    for n in (16, 32, 64, 128):
        v, f = solid_mesh(g, ns=8, n_arc=n, n_side=12, n_lip=n // 2)
        volume = signed_volume(v, f)
        p, _ = profile(0.04, g, n_arc=n, n_side=12)
        measured, _, area = section_metrics(p, 0.001)
        theta = np.arccos(0.8)
        evidence["refinement"].append(
            {
                "arc_intervals": n,
                "lip_intervals": n // 2,
                "solid_volume_m3": float(volume),
                "solid_relative_error": float(abs(volume - exact) / exact),
                "partial_arc_error_m": float(abs(measured - 2 * 0.005 * theta)),
                "partial_area_error_m2": float(
                    abs(area - 0.005**2 * (theta - np.sin(theta) * np.cos(theta)))
                ),
            }
        )
    errors = [row["solid_relative_error"] for row in evidence["refinement"]]
    assert all(b < a / 3 for a, b in zip(errors, errors[1:])), errors
    assert errors[-1] < 1e-4, errors
    manifest = json.loads((ROOT / "legacy_manifest.json").read_text(encoding="utf-8-sig"))
    changed, missing = [], []
    for item in manifest:
        path = ROOT.parent / item["Path"]
        if not path.is_file():
            missing.append(item["Path"])
        elif hashlib.sha256(path.read_bytes()).hexdigest().upper() != item["Hash"]:
            changed.append(item["Path"])
    evidence["legacy_integrity"] = {
        "files_checked": len(manifest),
        "changed": changed,
        "missing": missing,
    }
    assert not changed and not missing, evidence["legacy_integrity"]
    (ROOT / "artifacts" / "numerical_verification.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
