"""Generate independent G0 artifacts. No OpenFOAM files or velocity fields written."""

import argparse
import copy
import csv
import hashlib
import json
import os
import platform
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplcache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from geometry import (
    ROOT,
    clip_polygon,
    grid_faces,
    history,
    inner_seam_contact_time,
    intersections,
    lip_crest_height,
    load_config,
    polygon_area,
    profile,
    section_metrics,
    signed_volume,
    solid_mesh,
    surface_grid,
    world,
    write_stl,
)
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
from vtk_export import write_pvd, write_vtp


def wet_surface(v, f, height):
    tri = v[f]
    full = np.all(tri[:, :, 2] <= height, axis=1)
    dry = np.all(tri[:, :, 2] > height, axis=1)
    area = (
        np.linalg.norm(
            np.cross(tri[full, 1] - tri[full, 0], tri[full, 2] - tri[full, 0]), axis=1
        ).sum()
        / 2
    )
    partial = [clip_polygon(t, height) for t in tri[~(full | dry)]]
    area += sum(polygon_area(p) for p in partial)
    return float(area), list(tri[full]) + [p for p in partial if len(p) >= 3]


def compute(cfg, case, samples):
    g = cfg["geometry"]
    grid = surface_grid(g, ns=20, n_arc=40, n_side=12)
    f = grid_faces(*grid.shape[:2])
    flat = grid.reshape(-1, 3)
    f = f[
        np.linalg.norm(
            np.cross(flat[f[:, 1]] - flat[f[:, 0]], flat[f[:, 2]] - flat[f[:, 0]]), axis=1
        )
        > 1e-16
    ]
    rows, frames = [], []
    duration = cfg[case]["duration_s"]
    # The R0.6 lip creates a short final wetting interval; resolve it explicitly.
    times = np.unique(
        np.r_[
            np.linspace(0, duration, samples),
            np.linspace(inner_seam_contact_time(case, cfg), duration, 21),
        ]
    )
    for t in times:
        beta, height, front = history(t, case, cfg)
        v = world(grid.reshape(-1, 3), beta, cfg)
        area, wet = wet_surface(v, f, height)
        segments = intersections(v, f, height)
        lip_crest = lip_crest_height(beta, cfg)
        rims = world(grid[0], beta, cfg)
        row = dict(
            time_s=float(t),
            beta_deg=float(beta),
            H_world_m=float(height),
            valley_front_s_m=float(np.clip(front, 0, g["length_m"])),
            extrapolated_plane_valley_s_m=float(front),
            inner_submerged_area_m2=area,
            lip_crest_clearance_m=float(lip_crest - height),
            max_side_rim_submergence_m=float(max(0, height - rims[:, 2].min())),
        )
        for name, s in (
            ("upstream", g["length_m"] * 0.1),
            ("mid", g["length_m"] / 2),
            ("outlet", g["length_m"]),
        ):
            p, _ = profile(s, g, n_arc=160, n_side=40)
            per, width, section = section_metrics(world(p, beta, cfg), height)
            row.update(
                {
                    f"P_{name}_m": float(per),
                    f"b_{name}_m": float(width),
                    f"A_{name}_m2": float(section),
                }
            )
        sv = np.linspace(0, g["length_m"], 101)
        sections = [section_metrics(world(profile(s, g)[0], beta, cfg), height)[2] for s in sv]
        row["V_submerged_trough_m3"] = float(np.trapezoid(sections, sv))
        row["intersection_length_inner_m"] = float(
            np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1).sum()
        )
        rows.append(row)
        frames.append((v, wet, segments))
    # This derivative is a body-coordinate geometric event speed, NOT fluid U.
    speed = np.gradient([r["extrapolated_plane_valley_s_m"] for r in rows], times, edge_order=2)
    for row, value in zip(rows, speed):
        row["geometric_front_ds_dt_m_s_NOT_FLUID_U"] = (
            float(value) if 0 <= row["extrapolated_plane_valley_s_m"] < g["length_m"] else None
        )
    return rows, frames, f


def setup3d(ax, limits, title):
    ax.set(
        xlim=limits[0],
        ylim=limits[1],
        zlim=limits[2],
        xlabel="X world [mm]",
        ylabel="Y world [mm]",
        zlabel="Z world [mm]",
        title=title,
    )
    ax.set_box_aspect([np.ptp(x) for x in limits])
    ax.view_init(elev=24, azim=-65)


def render_cases(out, cfg, data, frames, faces, animate):
    g = cfg["geometry"]
    solid, sf = solid_mesh(g, ns=12, n_arc=24, n_side=8, n_lip=12)
    allv = (
        np.concatenate([world(solid, r["beta_deg"], cfg) for rows in data.values() for r in rows])
        * 1000
    )
    limits = [(allv[:, i].min() - 7, allv[:, i].max() + 7) for i in range(3)]
    fig = plt.figure(figsize=(12, 5.6))
    axes = [fig.add_subplot(121 + i, projection="3d") for i in range(2)]

    def draw(indices):
        for ax, case, index in zip(axes, ("case1", "case2"), indices):
            ax.clear()
            row = data[case][index]
            v, wet, segments = frames[case][index]
            vsolid = world(solid, row["beta_deg"], cfg) * 1000
            ax.add_collection3d(
                Poly3DCollection(vsolid[sf], facecolor="#aeb9c2", edgecolor="none", alpha=0.25)
            )
            if wet:
                ax.add_collection3d(
                    Poly3DCollection(
                        [p * 1000 for p in wet], facecolor="#0087b8", edgecolor="none", alpha=0.8
                    )
                )
            if len(segments):
                ax.add_collection3d(
                    Line3DCollection(segments * 1000, colors="#d14c00", linewidths=2.0)
                )
            h = row["H_world_m"] * 1000
            xx, yy = limits[0], limits[1]
            plane = np.array(
                [[xx[0], yy[0], h], [xx[1], yy[0], h], [xx[1], yy[1], h], [xx[0], yy[1], h]]
            )
            ax.add_collection3d(
                Poly3DCollection(
                    [plane], facecolor="#36adca", alpha=0.10, edgecolor="#36adca", linewidth=0.5
                )
            )
            bottom = world([[0, 0, 0], [g["length_m"], 0, 0]], row["beta_deg"], cfg) * 1000
            ax.plot(*bottom.T, color="#142a42", linewidth=1)
            setup3d(
                ax,
                limits,
                f"{case}: t={row['time_s']:.2f} s, beta={row['beta_deg']:.1f} deg\n"
                f"H={h:.1f} mm; P_out={row['P_outlet_m'] * 1000:.3f} mm",
            )
        fig.suptitle(
            "PARAMETRIC EXAMPLE, NOT CALIBRATED | "
            "blue: submerged inner surface; orange: plane intersection",
            fontsize=10,
        )
        fig.subplots_adjust(left=0.01, right=0.92, bottom=0.08, top=0.84, wspace=0.08)

    for fraction, label in ((0, "initial"), (0.5, "middle"), (1, "arrival")):
        draw(
            [
                int(
                    np.argmin(
                        abs(
                            np.array([r["time_s"] for r in data[k]])
                            - fraction * cfg[k]["duration_s"]
                        )
                    )
                )
                for k in ("case1", "case2")
            ]
        )
        fig.savefig(out / f"intersection_{label}.png", dpi=150)
    if animate:
        # Shared REAL clock. Case 2 holds its last frame after 1.5 s.
        clock = np.linspace(0, max(cfg[k]["duration_s"] for k in data), 41)

        def update(t):
            draw(
                [
                    int(
                        np.argmin(
                            abs(
                                np.array([r["time_s"] for r in data[k]])
                                - min(t, cfg[k]["duration_s"])
                            )
                        )
                    )
                    for k in ("case1", "case2")
                ]
            )

        anim = FuncAnimation(fig, update, frames=clock, interval=100)
        anim.save(out / "immersion_3d.gif", writer=PillowWriter(fps=10))
    plt.close(fig)


def geometry_views(out, cfg, v, f):
    fig, axs = plt.subplots(2, 2, figsize=(11, 8))
    g = cfg["geometry"]
    for ax, (i, j), title in zip(
        axs.ravel()[:3], ((0, 1), (0, 2), (1, 2)), ("Top (s-y)", "Side (s-w)", "Outlet (y-w)")
    ):
        # Structured wire edges plus bounding shell scatter, not a misleading filled projection.
        ax.scatter(v[:, i] * 1000, v[:, j] * 1000, s=0.12, color="#476479", alpha=0.3)
        for s in (0, g["length_m"]):
            p, n = profile(s, g)
            ax.plot(p[:, i] * 1000, p[:, j] * 1000, color="#004a78")
            outer = p - g["thickness_m"] * n
            ax.plot(outer[:, i] * 1000, outer[:, j] * 1000, color="#bd4c00", linewidth=0.8)
        ax.set(title=title, xlabel=f"{'syw'[i]} [mm]", ylabel=f"{'syw'[j]} [mm]")
        ax.axis("equal")
        ax.grid(alpha=0.2)
    ax = axs[1, 1]
    th = np.linspace(0, np.pi, 121)
    h, length = g["lip_radius_m"], g["length_m"]
    ax.plot([length - 0.003, length], [0, 0], color="#004a78")
    ax.plot([length - 0.003, length], [-2 * h, -2 * h], color="#bd4c00")
    ax.plot(length + h * np.sin(th), -h + h * np.cos(th), color="#444444")
    ax.set(title="Lip at valley: independent R0.6 mm", xlabel="s [m]", ylabel="w [m]")
    ax.axis("equal")
    ax.grid(alpha=0.2)
    fig.suptitle(
        "Two trimmed pyramid faces + R5 valley + 1.2 mm shell | dimensions awaiting calibration"
    )
    fig.tight_layout()
    fig.savefig(out / "geometry_views.png", dpi=160)
    plt.close(fig)


def plots(out, data):
    fig, axes = plt.subplots(3, 2, figsize=(11, 10))
    for color, (case, rows) in zip(("#0072b2", "#d55e00"), data.items()):
        t = [r["time_s"] for r in rows]
        for station, style in (("upstream", "-"), ("mid", "--"), ("outlet", ":")):
            axes[0, 0].plot(
                t,
                [r[f"P_{station}_m"] * 1000 for r in rows],
                style,
                label=f"{case} {station}",
                color=color,
            )
        axes[0, 1].plot(t, [r["inner_submerged_area_m2"] * 1e6 for r in rows], label=case)
        axes[1, 0].plot(t, [r["valley_front_s_m"] * 1000 for r in rows], label=case)
        axes[1, 1].plot(
            t,
            np.array([r["geometric_front_ds_dt_m_s_NOT_FLUID_U"] for r in rows], dtype=float)
            * 1000,
            label=case,
        )
    for ax, title, unit in zip(
        axes.ravel(),
        (
            "Wet perimeter: outlet = inner lip seam",
            "Submerged inner area (geometry only)",
            "Valley plane-intersection position",
            "Geometric speed, NOT fluid velocity",
            "Transverse geometric coverage",
            "Explicit interpolated plane elevation",
        ),
        ("P [mm]", "A [mm^2]", "s_front [mm]", "ds_front/dt [mm/s]", "b [mm]", "H [mm]"),
    ):
        ax.set(xlabel="time [s]", ylabel=unit, title=title)
        ax.grid(alpha=0.2)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=8)
    for case, rows in data.items():
        t = [r["time_s"] for r in rows]
        axes[2, 0].plot(t, [r["b_mid_m"] * 1000 for r in rows], label=f"{case} mid")
        axes[2, 0].plot(t, [r["b_outlet_m"] * 1000 for r in rows], ":", label=f"{case} outlet")
        axes[2, 1].plot(t, [r["H_world_m"] * 1000 for r in rows], label=case)
    axes[2, 0].legend(fontsize=8)
    axes[2, 1].legend(fontsize=8)
    fig.suptitle("Kinematic geometry ONLY | Case 2: provisional 70 to 55 deg", fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "immersion_curves.png", dpi=160)
    fig.savefig(out / "immersion_curves.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for case, rows in data.items():
        end = rows[-1]["time_s"]
        selected = [r for r in rows if r["time_s"] > end - 0.02]
        t = [(r["time_s"] - end) * 1000 for r in selected]
        axes[0].plot(t, [r["P_outlet_m"] * 1000 for r in selected], ".-", label=case)
        axes[1].plot(t, [r["b_outlet_m"] * 1000 for r in selected], ".-", label=case)
    for ax, ylabel in zip(axes, ("P at inner lip seam [mm]", "b at inner lip seam [mm]")):
        ax.set(xlabel="time relative to event B [ms]", ylabel=ylabel)
        ax.legend()
        ax.grid(alpha=0.2)
    fig.suptitle("Resolved final seam immersion; event B is the downstream lip crest")
    fig.tight_layout()
    fig.savefig(out / "outlet_detail.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "parameters.json")
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--samples", type=int, default=61)
    parser.add_argument("--no-animation", action="store_true")
    args = parser.parse_args()
    if args.samples < 3:
        parser.error("at least 3 samples required")
    cfg = load_config(args.config)
    out = args.out.resolve()
    # Restrict generated writes to this new project; never accept a legacy-case path.
    if not out.is_relative_to(ROOT):
        parser.error("output must be inside this independent project directory")
    out.mkdir(parents=True, exist_ok=True)
    v, f = solid_mesh(cfg["geometry"])
    write_stl(out / "spout_solid_spout_frame_m.stl", v, f)
    write_stl(
        out / "spout_solid_body_frame_m.stl",
        world(v, 70, {**cfg, "rotation": {"pivot_body_m": [0, 0, 0], "pivot_world_m": [0, 0, 0]}}),
        f,
    )
    np.savez_compressed(out / "solid_mesh.npz", vertices=v, faces=f)
    geometry_views(out, cfg, v, f)
    data, frames = {}, {}
    for case in ("case1", "case2"):
        data[case], frames[case], faces = compute(cfg, case, args.samples)
        with (out / f"{case}_history.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(data[case][0]))
            writer.writeheader()
            writer.writerows(data[case])
        print(case, json.dumps({"initial": data[case][0], "arrival": data[case][-1]}), flush=True)
    plots(out, data)
    sensitivity(out, cfg)
    export_dynamic(out, cfg, data, frames, faces)
    render_cases(out, cfg, data, frames, faces, not args.no_animation)
    edges = Counter(
        tuple(sorted((int(a), int(b)))) for tri in f for a, b in zip(tri, np.roll(tri, -1))
    )
    audit = {
        "status": "Implemented/Tested geometric example, NOT physically Validated",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "parameters": cfg,
        "vertices": len(v),
        "triangles": len(f),
        "edges_not_two_incident_faces": sum(n != 2 for n in edges.values()),
        "signed_solid_volume_m3": float(signed_volume(v, f)),
        "bounds_spout_m": [v.min(axis=0).tolist(), v.max(axis=0).tolist()],
        "case_events": {k: {"initial": rows[0], "arrival": rows[-1]} for k, rows in data.items()},
        "fluid_velocity": None,
        "flow_rate": None,
        "inner_seam_contact_time_s": {case: inner_seam_contact_time(case, cfg) for case in data},
        "film_thickness": None,
        "total_kettle_water_volume_conservation": (
            "NOT TESTABLE: reservoir and fill missing; H is explicit illustrative input"
        ),
    }
    audit["source_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "geometry.py", ROOT / "run_g0.py", args.config)
    }
    (out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"Artifacts: {out}", flush=True)


def sensitivity(out, cfg):
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for depth in cfg["case2"]["initial_depth_sensitivity_m"]:
        variant = copy.deepcopy(cfg)
        variant["case2"]["initial_depth_world_m"] = depth
        series = []
        for t in np.linspace(0, cfg["case2"]["duration_s"], 61):
            beta, height, front = history(t, "case2", variant)
            p, _ = profile(cfg["geometry"]["length_m"] / 2, cfg["geometry"], n_arc=160)
            per, width, area = section_metrics(world(p, beta, variant), height)
            row = dict(
                initial_depth_m=depth,
                time_s=float(t),
                H_m=float(height),
                beta_deg=float(beta),
                P_mid_m=float(per),
                b_mid_m=float(width),
                A_mid_m2=float(area),
                extrapolated_front_m=float(front),
            )
            rows.append(row)
            series.append(row)
        axes[0].plot(
            [r["time_s"] for r in series],
            [r["P_mid_m"] * 1000 for r in series],
            label=f"h0={depth * 1000:g} mm",
        )
        axes[1].plot(
            [r["time_s"] for r in series],
            [r["b_mid_m"] * 1000 for r in series],
            label=f"h0={depth * 1000:g} mm",
        )
    for ax, ylabel in zip(axes, ("P_mid [mm]", "b_mid [mm]")):
        ax.set(xlabel="time [s]", ylabel=ylabel)
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Case 2 initial-depth sensitivity (illustrative, 70 to 55 deg)")
    fig.tight_layout()
    fig.savefig(out / "case2_depth_sensitivity.png", dpi=150)
    plt.close(fig)
    with (out / "case2_depth_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_dynamic(out, cfg, data, frames, faces):
    folder = out / "paraview"
    folder.mkdir(exist_ok=True)
    solid, sf = solid_mesh(cfg["geometry"], ns=8, n_arc=24, n_side=8, n_lip=12)
    for case, rows in data.items():
        entries = []
        for i in sorted(set(np.linspace(0, len(rows) - 1, 21).astype(int))):
            row = rows[i]
            v, _, segments = frames[case][i]
            h, t = row["H_world_m"], row["time_s"]
            shell = world(solid, row["beta_deg"], cfg)
            xmin, ymin = shell[:, :2].min(axis=0) - 0.005
            xmax, ymax = shell[:, :2].max(axis=0) + 0.005
            plane = [[xmin, ymin, h], [xmax, ymin, h], [xmax, ymax, h], [xmin, ymax, h]]
            items = [
                (v, faces, False),
                (segments.reshape(-1, 3), np.arange(segments.size // 3).reshape(-1, 2), True),
                (plane, [[0, 1, 2], [0, 2, 3]], False),
                (shell, sf, False),
            ]
            for part, (points, cells, lines) in enumerate(items):
                filename = f"{case}_{i:03d}_{part}.vtp"
                write_vtp(folder / filename, points, cells, h, lines=lines)
                entries.append((t, part, filename))
        write_pvd(folder / f"{case}.pvd", entries)


if __name__ == "__main__":
    main()
