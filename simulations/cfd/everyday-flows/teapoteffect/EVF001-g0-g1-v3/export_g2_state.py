"""Freeze G0/G1 endpoint geometry for a planned STATIC G2/G3 setup.

No inlet velocity or VOF solution is generated. SI units throughout.
Run from repository root with .venv/Scripts/python.exe <this file>.
"""

import csv
import hashlib
import json

import numpy as np
from geometry import ROOT, load_config, profile, rotation_y, section_metrics, world


def main():
    cfg = load_config()
    length = cfg["geometry"]["length_m"]
    result = {
        "status": "TESTED_GEOMETRIC_HANDOFF_ONLY; VELOCITY_AND_VOF_NOT_IMPLEMENTED",
        "mesh_frame": "spout local (s,y,w); geometry static",
        "time_dependence": "none; G3 solver time independent of G0 event time",
        "inlet_s_over_L": 0.8,
        "inlet_s_m": 0.8 * length,
        "velocity_model_found": False,
        "U_in_m_s": None,
        "Q_in_m3_s": None,
        "sources_sha256": {},
        "cases": {},
    }
    for path in (ROOT / "geometry.py", ROOT / "parameters.json"):
        result["sources_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("case1", "case2"):
        source = ROOT / "artifacts" / f"{name}_history.csv"
        result["sources_sha256"][source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        with source.open(encoding="utf-8") as stream:
            row = list(csv.DictReader(stream))[-1]
        beta, height = float(row["beta_deg"]), float(row["H_world_m"])
        rotation = rotation_y(-beta)
        gravity = rotation.T @ np.array([0.0, 0.0, -9.81])
        np.testing.assert_allclose(np.linalg.norm(gravity), 9.81, atol=1e-12)
        np.testing.assert_allclose(rotation @ gravity, [0, 0, -9.81], atol=1e-12)
        assert gravity[0] < 0  # Uphill spout, gravity opposes outlet direction.
        c = cfg[name]
        assert abs(beta - (c["beta_start_deg"] - c["rate_deg_s"] * c["duration_s"])) < 1e-12
        assert abs(float(row["lip_crest_clearance_m"])) < 1e-12
        candidates = []
        for fraction in (0.75, 0.8, 0.85):
            s = fraction * length
            p, _ = profile(s, cfg["geometry"], n_arc=320, n_side=80)
            pw = world(p, beta, cfg)
            per, width, area = section_metrics(pw, height)
            cut_w = (height - world([s, 0, 0], beta, cfg)[2]) / np.cos(np.deg2rad(beta))
            assert 0 < cut_w < p[:, 2].max(), "candidate inlet overtops side rims"
            assert area > 0 and per > 0
            # Repeat at finer circular resolution: bounds scientific discretization error.
            fine = world(profile(s, cfg["geometry"], n_arc=640, n_side=160)[0], beta, cfg)
            refined = section_metrics(fine, height)
            assert abs(refined[2] - area) / refined[2] < 1e-4
            candidates.append(
                dict(
                    s_over_L=fraction,
                    s_m=s,
                    local_water_height_w_m=cut_w,
                    wetted_perimeter_m=per,
                    transverse_width_m=width,
                    liquid_area_m2=area,
                )
            )
        result["cases"][name] = {
            "source_event_time_s": float(row["time_s"]),
            "fixed_beta_deg": beta,
            "source_H_world_m": height,
            "constant_gravity_spout_m_s2": gravity.tolist(),
            "candidate_inlet_sections": candidates,
            "baseline_section": candidates[1],
        }
    dest = ROOT / "artifacts" / "g2_fixed_state.json"
    dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
