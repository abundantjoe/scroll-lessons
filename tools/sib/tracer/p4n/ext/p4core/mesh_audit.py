# Provenance: Project HERCULES | owner the owner | [id removed]
"""HYPOTHESES L10: sheet-switch audit of the official w010-027 mesh
(20260701183124, 2.4 um), per 2 x 2 cm tile of the strip-a grid
(p4-tiles-a grid.json: T = 8343 canvas px = 417.15 grid cells; tile (r, c) =
grid rows [floor(r*T/20), floor((r+1)*T/20)), cols likewise).
Numbers only; CT is streamed as byte ranges and reduced to 1-D profiles.

Per tile:
 1 neighbour ratio: for sampled vertices on winding k (floor(s) == k),
   distance to the nearest vertex of winding k-1 and k+1 (per-winding
   KD-trees; vertex distance, error <= half the 20-vox grid diagonal,
   ~34 um), split inward/outward. Ratio = min(in, out) / tile median of
   (in + out) / 2 spacing. A sheet switch puts the mesh ON the neighbour
   sheet, so the ratio collapses toward 0 there.
 2 self-intersection of the tile sub-grid (trace_metrics.self_intersection).
 3 normal flips: triangles whose normal opposes the 9 x 9 mean normal
   (FLAT-2 fold rule), and the fraction of vertex normals pointing inward
   (toward the umbilicus) after orienting by the tile majority.
 4 w027 vertices (floor(s) == 17): distance to the w028-037 mesh.
 5 CT agreement: for 40 vertices per tile, the L0 profile along the normal
   over +-60 um (1 vox steps, Gaussian sigma 1 vox): the signed offset (mm,
   + = away from the umbilicus) of the max |dI/dn| (edge) and of the max I
   (sheet centre).
usage: mesh_audit.py <mesh_dir> <mesh028_dir> <out_rows.jsonl>
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402
import trace_metrics as tm  # noqa: E402

T = 8343
NR, NC = 9, 21
VOXMM = 2.4e-3


def load(d: Path, s=True):
    X, Y, Z = (np.load(d / f"{c}.npy") for c in "xyz")
    S = np.load(d / "s.npy") if s else None
    return X, Y, Z, S


def normals(P):
    """Vertex normals of an (h, w, 3) grid (NaN invalid) by central differences."""
    du = np.gradient(P, axis=1)
    dv = np.gradient(P, axis=0)
    n = np.cross(du, dv)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12)


def profile(xyz, n, half=25):
    """L0 intensities along xyz + t*n, t = -half..half vox (byte ranges)."""
    t = np.arange(-half, half + 1, dtype=float)
    Q = xyz[None, :] + t[:, None] * n[None, :]
    zlo, zhi = int(math.floor(Q[:, 2].min())) - 1, int(math.ceil(Q[:, 2].max())) + 2
    ylo, yhi = int(math.floor(Q[:, 1].min())) - 1, int(math.ceil(Q[:, 1].max())) + 2
    xlo, xhi = int(math.floor(Q[:, 0].min())) - 1, int(math.ceil(Q[:, 0].max())) + 2
    blk = np.zeros((zhi - zlo, yhi - ylo, xhi - xlo), np.float32)
    for cz in range(zlo // 128, (zhi - 1) // 128 + 1):
        a, b = max(zlo, cz * 128), min(zhi, (cz + 1) * 128)
        for cy in range(ylo // 128, (yhi - 1) // 128 + 1):
            for cx in range(xlo // 128, (xhi - 1) // 128 + 1):
                raw = cc._fetch(f"{cc.VOL}/{cz}/{cy}/{cx}", (a - cz * 128) * 16384, (b - cz * 128) * 16384 - 1)
                if raw is None:
                    continue
                arr = np.frombuffer(raw, np.uint8).reshape(b - a, 128, 128)
                sy = slice(max(ylo, cy * 128), min(yhi, (cy + 1) * 128))
                sx = slice(max(xlo, cx * 128), min(xhi, (cx + 1) * 128))
                blk[a - zlo:b - zlo, sy.start - ylo:sy.stop - ylo, sx.start - xlo:sx.stop - xlo] = \
                    arr[:, sy.start - cy * 128:sy.stop - cy * 128, sx.start - cx * 128:sx.stop - cx * 128]
    v = ndimage.map_coordinates(blk, [Q[:, 2] - zlo, Q[:, 1] - ylo, Q[:, 0] - xlo], order=1)
    return t, v


def tile_rows(X, Y, Z, S, U, trees, tree028, r, c, rng):
    g0, g1 = (r * T) // 20, ((r + 1) * T) // 20
    h0, h1 = (c * T) // 20, ((c + 1) * T) // 20
    P = np.stack([X[g0:g1, h0:h1], Y[g0:g1, h0:h1], Z[g0:g1, h0:h1]], -1).astype(np.float64)
    s = S[g0:g1, h0:h1].astype(np.float64)
    valid = (P[..., 0] != -1) & np.isfinite(P[..., 2]) & (P[..., 2] > 0) & np.isfinite(s)
    out = {"r": r, "c": c, "n_valid": int(valid.sum())}
    if valid.sum() < 2000:
        out["skip"] = "fewer than 2000 valid vertices"
        return out
    Pn = np.where(valid[..., None], P, np.nan)
    N = normals(Pn)
    ux = np.interp(P[..., 2], U[:, 0], U[:, 1])
    uy = np.interp(P[..., 2], U[:, 0], U[:, 2])
    rad = np.stack([P[..., 0] - ux, P[..., 1] - uy, np.zeros_like(ux)], -1)
    rad /= np.linalg.norm(rad, axis=-1, keepdims=True) + 1e-12
    dot = np.sum(N * rad, -1)
    okn = valid & np.isfinite(dot)
    sign = 1.0 if np.nanmedian(dot[okn]) >= 0 else -1.0
    N *= sign                                   # now + = away from the umbilicus
    dot *= sign
    out["normal_inward_frac"] = float(np.mean(dot[okn] < 0))
    # FLAT-2 fold rule on vertex normals: against the 9x9 mean
    Nm = np.stack([ndimage.uniform_filter(np.nan_to_num(N[..., i]), 9) for i in range(3)], -1)
    fl = np.sum(N * Nm, -1) < 0
    out["normal_flip_frac"] = float(np.mean(fl[okn]))
    # 1 neighbour ratio
    sub = np.zeros_like(valid)
    sub[::4, ::4] = True
    sel = valid & sub & okn
    Pi, si, Ni = P[sel], s[sel], N[sel]
    k = np.floor(si).astype(int)
    din = np.full(len(Pi), np.nan)
    dout = np.full(len(Pi), np.nan)
    for kk in np.unique(k):
        m = k == kk
        for nb, arr in ((kk - 1, din), (kk + 1, dout)):
            if nb in trees:
                d, j = trees[nb][0].query(Pi[m], distance_upper_bound=600)
                d[~np.isfinite(d)] = np.nan
                arr[m] = d
    sp = np.nanmedian(np.r_[din, dout])
    rat = np.fmin(din, dout) / sp
    f = np.isfinite(rat)
    out["spacing_mm"] = float(sp * VOXMM)
    out["ratio"] = {"n": int(f.sum()), "p1": float(np.percentile(rat[f], 1)), "p5": float(np.percentile(rat[f], 5)),
                    "p50": float(np.median(rat[f])), "frac_lt_0p6": float(np.mean(rat[f] < 0.6)),
                    "frac_lt_0p3": float(np.mean(rat[f] < 0.3))}
    # 2 self-intersection
    si_ = tm.self_intersection(np.where(valid[..., None], P, -1.0))
    out["self_intersection_pairs"] = int(si_.get("n_intersecting_pairs", -1))
    # winding coordinate jumps along columns (s should change smoothly)
    ds = np.abs(np.diff(s, axis=1))
    vv = valid[:, 1:] & valid[:, :-1]
    out["s_jumps_gt0p25"] = int(np.sum(ds[vv] > 0.25))
    # 4 w027 -> w028-037
    m27 = sel & (np.floor(s) == 17)
    if m27.any() and tree028 is not None:
        d, _ = tree028.query(P[m27], distance_upper_bound=600)
        d = d[np.isfinite(d)] * VOXMM
        out["w027_to_w028_mm"] = {"n": int(d.size), "p5": float(np.percentile(d, 5)) if d.size else None,
                                  "p50": float(np.median(d)) if d.size else None}
    # 5 CT offsets
    ids = np.argwhere(valid & okn)
    pick = ids[rng.choice(len(ids), min(40, len(ids)), replace=False)]
    oe, oc = [], []
    for (i, j) in pick:
        t, v = profile(P[i, j], N[i, j])
        if not np.any(v > 0):
            continue
        vs = ndimage.gaussian_filter1d(v, 1.0)
        gr = np.abs(np.gradient(vs))
        oe.append(t[np.argmax(gr)] * VOXMM)
        oc.append(t[np.argmax(vs)] * VOXMM)
    for key, a in (("ct_edge_offset_mm", oe), ("ct_centre_offset_mm", oc)):
        a = np.array(a)
        out[key] = {"n": int(a.size), "p10": float(np.percentile(a, 10)) if a.size else None,
                    "p50": float(np.median(a)) if a.size else None, "p90": float(np.percentile(a, 90)) if a.size else None,
                    "frac_at_window_edge": float(np.mean(np.abs(a) >= 0.059)) if a.size else None}
    return out


def main(mesh_dir, m028_dir, out_rows):
    X, Y, Z, S = load(Path(mesh_dir))
    a = json.load(open(Path(mesh_dir) / "umb.json"))
    U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
    valid = (X != -1) & np.isfinite(S)
    kk = np.floor(S[valid]).astype(int)
    V = np.stack([X[valid], Y[valid], Z[valid]], 1).astype(np.float32)
    trees = {int(k): (cKDTree(V[kk == k]),) for k in np.unique(kk)}
    del V, kk
    try:
        X2, Y2, Z2, _ = load(Path(m028_dir), s=False)
        m2 = (X2 != -1) & (Z2 > 0)
        tree028 = cKDTree(np.stack([X2[m2], Y2[m2], Z2[m2]], 1))
        del X2, Y2, Z2
    except Exception:
        tree028 = None
    done = set()
    if Path(out_rows).exists():
        for line in open(out_rows):
            d = json.loads(line)
            done.add((d["r"], d["c"]))
    rng = np.random.default_rng(20260927)
    for r in range(NR):
        for c in range(NC):
            if (r, c) in done:
                continue
            t0 = time.time()
            row = tile_rows(X, Y, Z, S, U, trees, tree028, r, c, np.random.default_rng([20260927, r, c]))
            row["wall_s"] = time.time() - t0
            with open(out_rows, "a") as f:
                f.write(json.dumps(row) + "\n")
            print(r, c, row.get("ratio", {}).get("p5"), row.get("wall_s"), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
