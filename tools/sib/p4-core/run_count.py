# Provenance: Project HERCULES | owner the owner | [id removed]
"""Run the DECL-P4-7 crossing count on the 2.4 um volume, one z-level per
call, writing one numbers-only JSON per level (resumable).

usage: run_count.py <mesh_dir> <out_dir> <z_mm> [<z_mm> ...]
mesh_dir holds x.npy, y.npy, z.npy (the 20260701183124 w010-027 2.4 um
tifxyz, streamed from S3 and cached as float32) and s.npy (winding coordinate
per vertex: unwrapped angle around the umbilicus along each grid row, in
turns, 0 at the inner end), and umb.json (official umbilicus).
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402


def load(mesh_dir: Path):
    X, Y, Z, S = (np.load(mesh_dir / f"{c}.npy") for c in "xyzs")
    a = json.load(open(mesh_dir / "umb.json"))
    U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
    return X, Y, Z, S, U


def snap_z(zmm: float) -> int:
    z = int(round(zmm / (cc.VOX_UM * 1e-3)))
    h = cc.PARAMS["slab_half"]
    lz = z % cc.CH
    if lz < h:
        z += h - lz
    elif lz > cc.CH - 1 - h:
        z -= lz - (cc.CH - 1 - h)
    return z


def level(X, Y, Z, S, U, zmm: float) -> dict:
    t0 = time.time()
    z0 = snap_z(zmm)
    cx, cy = float(np.interp(z0, U[:, 0], U[:, 1])), float(np.interp(z0, U[:, 0], U[:, 2]))
    P0, P1, s0, s1 = cc.plane_segments(X, Y, Z, S, float(z0))
    angles = np.linspace(0, 2 * math.pi, cc.PARAMS["n_rays"], endpoint=False)
    cr = cc.ray_crossings(P0, P1, s0, s1, (cx, cy), angles)
    wr, ordered = zip(*[cc.winding_radii(r, s, kmax=11) for r, s in cr])
    wr = np.array(wr)
    # window: all ray points out to w021 (+ margin for smoothing)
    rmax = np.nanmax(np.where(np.isfinite(wr[:, 11]), wr[:, 11], wr[:, 10])) + 60
    if not np.isfinite(rmax):
        return {"z_mm": zmm, "z_vox": z0, "error": "no w020 crossings"}
    rmax = min(rmax, 3000)
    x0, x1 = int(max(0, cx - rmax)), int(min(cc.SHAPE[2], cx + rmax + 1))
    y0, y1 = int(max(0, cy - rmax)), int(min(cc.SHAPE[1], cy + rmax + 1))
    img, absent = cc.read_slab_mean(z0, y0, y1, x0, x1, cc.PARAMS["slab_half"])
    t_fetch = time.time() - t0
    origin = (y0, x0)

    res = {"z_mm": zmm, "z_vox": z0, "umb_xy": [cx, cy], "window_yx": [y0, y1, x0, x1],
           "absent_chunk_frac": absent, "window_zero_frac": float(np.mean(img == 0)),
           "n_segments": int(len(P0)), "rays_mesh_ordered_frac": float(np.mean(ordered)),
           "angles": angles.tolist(),
           "w_radii_mm": np.round(wr * cc.VOX_UM * 1e-3, 5).tolist()}

    # alignment sanity: intensity at mesh crossings vs midway between them
    sm_p = ndimage.gaussian_filter(img, cc.sigma_vox(cc.PARAMS["smooth_primary"]))
    on, mid = [], []
    for th, w in zip(angles, wr):
        f = np.isfinite(w[:11])
        if f.sum() < 3:
            continue
        rr = w[:11][f]
        for rad, lst in ((rr, on), ((rr[:-1] + rr[1:]) / 2, mid)):
            xs = cx + rad * math.cos(th) - x0
            ys = cy + rad * math.sin(th) - y0
            lst.extend(ndimage.map_coordinates(sm_p, [ys, xs], order=1).tolist())
    res["mesh_alignment"] = {"mean_at_crossings": float(np.mean(on)) if on else None,
                             "mean_midway": float(np.mean(mid)) if mid else None,
                             "frac_on_gt_mid_pairs": None}

    runs = {}
    for key, spec in (("primary", cc.PARAMS["smooth_primary"]), ("secondary", cc.PARAMS["smooth_secondary"])):
        sig = cc.sigma_vox(spec)
        fr = [cc.PARAMS["prom_frac"]] if key == "secondary" else cc.PARAMS["prom_frac_sweep"]
        for pf in fr:
            out = cc.run_level(img, origin, (cx, cy), angles, wr, pf, sig)
            runs[f"{key}_pf{pf:.2f}"] = [None if o is None else
                                         {"n_inner": o["n_inner"], "n_cal": o["n_cal"],
                                          "r_inner_lim_mm": o["r_inner_lim"] * cc.VOX_UM * 1e-3,
                                          "inner_peaks_mm": [round(v * cc.VOX_UM * 1e-3, 4) for v in o["inner_peaks_r"]],
                                          "zero_frac_inner": o["zero_frac_inner"]} for o in out]
    res["runs"] = runs
    res["wall_s"] = time.time() - t0
    res["fetch_s"] = t_fetch
    return res


if __name__ == "__main__":
    mesh_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    X, Y, Z, S, U = load(mesh_dir)
    for zmm in map(float, sys.argv[3:]):
        f = out_dir / f"z{zmm:06.2f}.json"
        if f.exists():
            continue
        r = level(X, Y, Z, S, U, zmm)
        json.dump(r, open(f, "w"))
        p = r.get("runs", {}).get("primary_pf0.25", [])
        n = [o["n_inner"] for o in p if o]
        c = [o["n_cal"] for o in p if o]
        print(f"z={zmm} valid_rays={len(n)} inner median={np.median(n) if n else None} cal median={np.median(c) if c else None} "
              f"wall={r.get('wall_s', 0):.0f}s", flush=True)
