# Provenance: Project HERCULES | owner the owner | [id removed]
"""Aggregate per-level count JSONs into count.json (DECL-P4-7 items 1-2).

usage: aggregate_count.py <levels_dir> <synthetic_tests.json> <out count.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402

KEY = "primary_pf0.25"


def arr(runs, f):
    return np.array([f(o) if o else np.nan for o in runs], float)


def spacing(peaks):
    p = np.asarray(peaks, float)
    return np.diff(p) if p.size > 1 else np.zeros(0)


def main(levels_dir: Path, synth: Path | None, out: Path):
    L = sorted([json.load(open(f)) for f in levels_dir.glob("z*.json")], key=lambda d: d["z_mm"])
    L = [d for d in L if "runs" in d]
    per = []
    Nmat, Cmat = [], []
    all_inner_sp, all_mesh_sp = [], []
    for d in L:
        R = d["runs"][KEY]
        n = arr(R, lambda o: o["n_inner"])
        c = arr(R, lambda o: o["n_cal"])
        Nmat.append(n)
        Cmat.append(c)
        w = np.array(d["w_radii_mm"], float)
        mesh_sp = np.diff(w[:, :11], axis=1).ravel()
        mesh_sp = mesh_sp[np.isfinite(mesh_sp)]
        in_sp = np.concatenate([spacing(o["inner_peaks_mm"]) for o in R if o] or [np.zeros(0)])
        # gap between the outermost inner peak and w010
        gap = np.array([w[i, 0] - o["inner_peaks_mm"][-1] for i, o in enumerate(R) if o and o["inner_peaks_mm"]])
        all_inner_sp.append(in_sp)
        all_mesh_sp.append(mesh_sp)
        h = len(n) // 2
        diam = (n[:h] + n[h:]) / 2
        f = np.isfinite(n)
        sweeps = {k: float(np.nanmedian(arr(v, lambda o: o["n_inner"]))) for k, v in d["runs"].items()}
        sweeps_cal = {k: float(np.nanmedian(arr(v, lambda o: o["n_cal"]))) for k, v in d["runs"].items()}
        per.append({
            "z_mm": d["z_mm"], "z_vox": d["z_vox"], "in_1129_footprint": 67.4 <= d["z_mm"] <= 135.3,
            "n_rays_valid": int(f.sum()), "absent_chunk_frac": d["absent_chunk_frac"],
            "window_zero_frac": d["window_zero_frac"], "mesh_rays_ordered_frac": d["rays_mesh_ordered_frac"],
            "inner_count": cc.describe(n[f]),
            "inner_count_hist": np.bincount(n[f].astype(int)).tolist() if f.any() else [],
            "frac_rays_ge1": float(np.mean(n[f] >= 1)), "frac_rays_gt10": float(np.mean(n[f] > 10)),
            "diameter_count_median": float(np.nanmedian(diam)),
            "calibration_count": cc.describe(c[f]),
            "calibration_frac_eq10": float(np.mean(c[f] == 10)),
            "calibration_frac_within1": float(np.mean(np.abs(c[f] - 10) <= 1)),
            "calibration_scaled_inner_median": float(np.nanmedian(n * 10 / np.where(c > 0, c, np.nan))),
            "sweep_inner_median": sweeps, "sweep_calibration_median": sweeps_cal,
            "w010_along_ray_r_mm": cc.describe(w[:, 0]),
            "mesh_spacing_w010_020_along_ray_mm": cc.describe(mesh_sp),
            "inner_peak_spacing_along_ray_mm": cc.describe(in_sp),
            "gap_outermost_inner_peak_to_w010_mm": cc.describe(gap),
            "step_rate_adjacent_rays": cc.step_rate(n, 0, True),
            "mesh_alignment": d["mesh_alignment"],
        })
    N = np.array(Nmat)
    C = np.array(Cmat)
    fin = np.isfinite(N)
    allN = N[fin]
    inner_sp = np.concatenate(all_inner_sp)
    mesh_sp = np.concatenate(all_mesh_sp)
    summary = {
        "n_levels": len(L), "n_ray_samples": int(fin.sum()),
        "z_range_mm": [L[0]["z_mm"], L[-1]["z_mm"]] if L else None,
        "inner_count_all": cc.describe(allN),
        "inner_count_hist_all": np.bincount(allN.astype(int)).tolist(),
        "per_level_median": cc.describe([p["inner_count"].get("median") for p in per]),
        "frac_ray_samples_ge1": float(np.mean(allN >= 1)),
        "frac_ray_samples_gt10": float(np.mean(allN > 10)),
        "decl_p4_7_gt10_stable_80pct_of_rays": bool(np.mean(allN > 10) >= 0.8),
        "calibration_all": cc.describe(C[fin]),
        "calibration_frac_within1_all": float(np.mean(np.abs(C[fin] - 10) <= 1)),
        "step_rate_adjacent_rays": cc.step_rate(N, 1, True),
        "step_rate_adjacent_z": cc.step_rate(N, 0, False),
        "mesh_spacing_w010_020_along_ray_mm": cc.describe(mesh_sp),
        "mesh_spacing_iqr_mm": [float(np.percentile(mesh_sp, 25)), float(np.percentile(mesh_sp, 75))],
        "inner_peak_spacing_along_ray_mm": cc.describe(inner_sp),
        "inner_peak_spacing_iqr_mm": [float(np.percentile(inner_sp, 25)), float(np.percentile(inner_sp, 75))] if inner_sp.size else None,
        "in_1129_footprint": cc.describe([p["inner_count"].get("median") for p in per if p["in_1129_footprint"]]),
    }
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "entry": "DECL-P4-7 items 1-2, 2.4 um volume (independent of p4-inner's 1.129 um count)",
           "viewing": "No image, tile or CT pixel was viewed or described; CT values were streamed as numbers, reduced to ray profiles and peak positions, and discarded.",
           "volume": cc.VOL, "mesh": "PHercParis4/segments/20260701183124-w010-027 (-on-20260411134726-2.4um.tifxyz)",
           "umbilicus": "PHercParis4/representations/umbilicus/20260411134726-umbilicus-20260524235033.json",
           "params": cc.PARAMS, "primary_run": KEY, "summary": summary, "levels": per}
    if synth and synth.exists():
        res["synthetic_tests_file"] = synth.name
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 3 else None, Path(sys.argv[-1]))
