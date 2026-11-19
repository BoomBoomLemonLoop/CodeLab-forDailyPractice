"""Check generated XML, numeric geometry consistency and actual image decoding."""

import csv
import json
from xml.etree import ElementTree as ET

import numpy as np
from geometry import ROOT, load_config
from PIL import Image


def reference_submerged_area(g, beta, height):
    """Independent 1-D quadrature of exact curved/planar surface strip widths."""
    a = np.deg2rad(g["included_angle_deg"] / 2)
    r, length, depth = g["inner_radius_m"], g["length_m"], g["outlet_depth_m"]
    b = np.deg2rad(beta)

    def axial_wet_length(w):
        start = length * w / depth
        end = np.minimum(length, (height - w * np.cos(b)) / np.sin(b))
        return np.maximum(0, end - start)

    phi = np.linspace(0, np.pi / 2 - a, 20001)
    w = r * (1 - np.cos(phi))
    curved = 2 * r * np.trapezoid(axial_wet_length(w), phi)
    wside = np.linspace(r * (1 - np.sin(a)), depth, 20001)
    planar = 2 / np.cos(a) * np.trapezoid(axial_wet_length(wside), wside)
    return curved + planar


def main():
    out, cfg = ROOT / "artifacts", load_config()
    evidence = {"XML_files": 0, "PVD_time_samples": {}, "images": {}, "area_checks": []}
    for pvd in sorted((out / "paraview").glob("*.pvd")):
        entries = ET.parse(pvd).findall(".//DataSet")
        evidence["PVD_time_samples"][pvd.name] = len(set(e.attrib["timestep"] for e in entries))
        assert len(entries) == 84
        for entry in entries:
            root = ET.parse(pvd.parent / entry.attrib["file"])
            piece = root.find(".//Piece")
            points = np.fromstring(root.find(".//Points/DataArray").text or "", sep=" ").reshape(
                -1, 3
            )
            assert len(points) == int(piece.attrib["NumberOfPoints"])
            conn = np.fromstring(
                root.find(".//DataArray[@Name='connectivity']").text or "", sep=" ", dtype=int
            )
            if len(conn):
                assert conn.min() >= 0 and conn.max() < len(points)
            if entry.attrib["part"] == "2":
                assert np.ptp(points[:, 2]) < 1e-12
            evidence["XML_files"] += 1
    for path in list(out.glob("*.png")) + [out / "immersion_3d.gif"]:
        with Image.open(path) as im:
            frames = getattr(im, "n_frames", 1)
            for i in range(frames):
                im.seek(i)
                im.load()
            evidence["images"][path.name] = {"size": im.size, "frames": frames}
    assert evidence["images"]["immersion_3d.gif"]["frames"] == 41
    for case in ("case1", "case2"):
        with (out / f"{case}_history.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        middle = int(
            np.argmin([abs(float(r["time_s"]) - cfg[case]["duration_s"] / 2) for r in rows])
        )
        for i in (middle, len(rows) - 1):
            row = {k: float(v) if v else float("nan") for k, v in rows[i].items()}
            ref = reference_submerged_area(cfg["geometry"], row["beta_deg"], row["H_world_m"])
            error = abs(row["inner_submerged_area_m2"] - ref) / ref
            assert error < 0.002, (case, i, error)
            evidence["area_checks"].append(
                {
                    "case": case,
                    "time_s": row["time_s"],
                    "reference_m2": ref,
                    "relative_error": error,
                }
            )
    (out / "artifact_verification.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
