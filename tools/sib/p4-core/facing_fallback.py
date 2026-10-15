# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-26-A1 item 4, fallback (4): the facing surface is the official
w010-027 mesh's adjacent inner winding (k-1) itself. Geometry only (no CT).

For each valid tile vertex p (source winding k = floor(s)) with inward
normal n (facing.inward_normals): intersect the ray p + t n, 0 < t <= 250 um,
with the official k-1 surface by iterated local planes: q = nearest k-1
vertex (KD-tree over k-1 vertices in rows g0-60..g1+60) to the current
point, n_q its grid normal; t = ((q - p) . n_q) / (n . n_q); point = p + t n;
3 iterations; accepted iff 0 < t <= 250 um and the final point lies within
10 um of the local plane of its nearest k-1 vertex. The facing mesh vertex =
that point (invalid otherwise). Gate (DECL-P4-26): 0 self-intersections and
>= 80 % coverage; metrics as facing.metrics; recorded as "fallback (4)".
usage: facing_fallback.py <mesh_dir> <out_dir> <control|title|all>
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import trace_metrics as tm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facing as fc  # noqa: E402
from facing2 import load, CTRL, TITLE  # noqa: E402
from mesh_audit import normals  # noqa: E402

T_MAX_VOX = 250 / 2.4


def tile(P, V, S, U, r, c):
    g0, g1, h0, h1 = fc.tile_vertices(P, V, r, c)
    Pt = P[g0:g1, h0:h1].astype(np.float64)
    v = V[g0:g1, h0:h1]
    Nin, ok = fc.inward_normals(Pt, v, U)
    K = np.floor(S[g0:g1, h0:h1])
    ra, rb = max(0, g0 - 60), min(V.shape[0], g1 + 60)
    Pr = P[ra:rb].astype(np.float64)
    Vr = V[ra:rb] & np.isfinite(S[ra:rb])
    Kr = np.floor(S[ra:rb])
    t_um = np.full(v.shape, np.nan)
    patch_si = {}
    for k in np.unique(K[ok]):
        sel = ok & (K == k)
        m = Vr & (Kr == k - 1)
        if m.sum() < 100:
            continue
        cols = np.where(m.any(0))[0]
        c0, c1 = cols.min(), cols.max() + 1
        blk = np.where(m[:, c0:c1, None], Pr[:, c0:c1], np.nan)
        Nb = normals(blk)
        mm = m[:, c0:c1] & np.all(np.isfinite(Nb), -1)
        Q = blk[mm]
        NQ = Nb[mm]
        QI = np.argwhere(mm)
        tree = cKDTree(Q)
        p = Pt[sel]
        n = Nin[sel]
        x = p + n * (T_MAX_VOX / 2)
        t = np.full(len(p), np.nan)
        for _ in range(3):
            _, j = tree.query(x)
            q, nq = Q[j], NQ[j]
            den = np.sum(n * nq, 1)
            t = np.where(np.abs(den) > 0.2, np.sum((q - p) * nq, 1) / np.where(den == 0, 1, den), np.nan)
            x = p + n * np.nan_to_num(t)[:, None]
        _, j = tree.query(x)
        resid = np.abs(np.sum((x - Q[j]) * NQ[j], 1)) * 2.4
        good = np.isfinite(t) & (t > 0) & (t <= T_MAX_VOX) & (resid <= 10)
        tt = np.full(len(p), np.nan)
        tt[good] = t[good] * 2.4
        t_um[sel] = tt
        if good.any():
            # the official k-1 patch that the rays hit (bounding box of hit vertices, winding k-1 only)
            hi = QI[j[good]]
            a0, a1 = hi[:, 0].min(), hi[:, 0].max() + 1
            b0, b1 = hi[:, 1].min(), hi[:, 1].max() + 1
            sub = np.where(m[a0:a1, c0 + b0:c0 + b1, None], Pr[a0:a1, c0 + b0:c0 + b1], -1.0)
            si = tm.self_intersection(sub)
            patch_si[int(k)] = {"rows": [int(ra + a0), int(ra + a1)], "cols": [int(c0 + b0), int(c0 + b1)],
                                "self_intersection_pairs": int(si.get("n_intersecting_pairs", -1))}
    idx = np.argwhere(ok)
    sf = t_um[idx[:, 0], idx[:, 1]]
    s_grid = t_um.astype(np.float32)
    s_grid[~ok] = np.nan
    t = {"Pt": Pt, "Nin": Nin, "ok": ok, "idx": idx, "own": np.ones(len(idx)), "s_own": np.zeros(len(idx)),
         "s_face": sf, "s_grid": s_grid, "g": (g0, g1, h0, h1)}
    m, Fm = fc.metrics(t, r, c)
    m["method"] = "fallback (4): official k-1 winding surface along the inward normal, t <= 250 um"
    m["resampled_grid_self_intersection_pairs"] = m.pop("self_intersection_pairs")
    m["official_patch"] = patch_si
    m["self_intersection_pairs"] = int(sum(x["self_intersection_pairs"] for x in patch_si.values()))
    m["coverage"] = m["frac_peak_found"]
    m["gate_pass"] = bool(m["self_intersection_pairs"] == 0 and m["coverage"] >= 0.80)
    m["gate_rule"] = "DECL-P4-26-A1 item 4: 0 self-intersections of the official k-1 patch (as an official mesh region) and >= 80 % coverage; the resampled-grid count is reported separately"
    m["mesh_sha256_float32"] = hashlib.sha256(Fm.tobytes()).hexdigest()
    return m, s_grid


def main(mesh_dir, out_dir, which):
    P, V, S, U = load(mesh_dir)
    out = Path(out_dir) / "fallback"
    out.mkdir(parents=True, exist_ok=True)
    tiles = CTRL + TITLE if which == "all" else (CTRL if which == "control" else TITLE)
    for (r, c) in tiles:
        f = out / f"r{r}_c{c}.json"
        if f.exists():
            continue
        t0 = time.time()
        m, sg = tile(P, V, S, U, r, c)
        m["wall_s"] = time.time() - t0
        json.dump(m, open(f, "w"), indent=1)
        np.savez_compressed(out / f"r{r}_c{c}_sface_um.npz", s_face_um=sg.astype(np.float16))
        print(json.dumps({k: m[k] for k in ("tile", "frac_peak_found", "self_intersection_pairs", "gate_pass", "wall_s")}), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
