# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-26 + DECL-P4-26-A1 facing surfaces, staged so the CT is read once.

Stage "peaks" (CT, per tile): for every valid tile vertex with a finite
inward normal, the L1 profile 0..400 um along -n (facing.py sampler, sigma 1
L1 voxel), and ALL peaks of the mirror-padded smoothed profile (position s
in um, prominence), sorted by s, capped at 24 (overflow counted). Saved to
<out>/peaks/rR_cC.npz. Nothing else is decided in this stage.

Stage "rules" (offline, per tile, from the stored peaks):
 * naive  = DECL-P4-26 as declared (facing.analyse logic): own = the
   largest-prominence peak with s <= 30 um (else s_own = 0); face = the
   first peak with s > s_own + 30 um and prominence >= P_MIN1 (p_min1.json).
 * reg    = DECL-P4-26-A1 item 1: (a) candidates s >= s_own + 0.6 x the
   tile's neighbour-winding spacing (mesh_audit rows.jsonl spacing_mm) with
   prominence >= P_MIN1, first such = step-(a) offset; (b) per vertex the
   candidate nearest the 9 x 9 nan-median of the step-(a) facing offsets
   (s_face - 0 on the grid), accepted within +-20 um; (c) the 9 x 9
   nan-median of the (b) result is recomputed and vertices > 20 um from it
   are dropped, as are vertices with no valid 4-neighbour.
 * metrics per rule: facing.metrics (frac found, gap, self-intersections,
   grid flattening, ARAP on the 2x decimated grid) and check (v)
   (DECL-P4-26-A1 item 2): exact point-to-surface distance
   (trace_metrics.point_to_mesh_distance) from each facing vertex to the
   official w010-027 mesh with the source vertex's own winding (floor(s))
   removed, cropped to the grid columns of windings k-1..k+1 (amended from k-3..k+3 after an OOM kill, disclosed; the nearest other-winding surface is adjacent by construction); pass = median
   <= 40 um and >= 80 % within 80 um.
 * Acceptance of reg (item 3): EVERY control tile (r0-r5 x c3-c8) passes the
   gate (0 self-intersections, >= 80 % found) AND (v). Title tiles get reg
   only if accepted; the naive rule is reported for all tiles regardless.
usage: facing2.py peaks <mesh_dir> <out_dir> <control|title> <k/n>
       facing2.py rules <mesh_dir> <out_dir> <control|title> <audit_rows.jsonl>
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import concurrent.futures as cf
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facing as fc  # noqa: E402
import trace_metrics as tm  # noqa: E402

fc.CHUNK_CACHE_MAX = 400


def si_blocked(points, blk=100, ov=4):
    """Self-intersection count in overlapping blk x blk grid blocks (memory-bounded; the
    unblocked test OOMs on jagged facing meshes). Sum over blocks = upper bound (overlap
    double counts); intersections between parts > blk cells apart are not tested."""
    H, W = points.shape[:2]
    n = 0
    for a in range(0, H, blk):
        for b in range(0, W, blk):
            sub = points[a:min(H, a + blk + ov), b:min(W, b + blk + ov)]
            if (sub[..., 0] != -1).sum() < 4:
                continue
            n += int(tm.self_intersection(sub).get("n_intersecting_pairs", 0))
    return {"n_intersecting_pairs": n, "blocked": f"{blk}x{blk} blocks, overlap {ov}, upper bound"}


import types as _types  # noqa: E402
fc.tm = _types.SimpleNamespace(self_intersection=si_blocked, point_to_mesh_distance=tm.point_to_mesh_distance)
KMAX = 24
CTRL = [(r, c) for r in range(6) for c in range(3, 9)]
TITLE = [(r, c) for r in range(6) for c in range(11, 20)]


def load(mesh_dir):
    d = Path(mesh_dir)
    X, Y, Z = (np.load(d / f"{c}.npy") for c in "xyz")
    V = (X != -1) & np.isfinite(Z) & (Z > 0)
    P = np.stack([X, Y, Z], -1).astype(np.float32)
    del X, Y, Z
    S = np.load(d / "s.npy")
    a = json.load(open(d / "umb.json"))
    U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
    return P, V, S, U


def all_peaks(prof):
    sm = ndimage.gaussian_filter1d(prof, 2.0, axis=1)
    n = len(sm)
    ps = np.full((n, KMAX), np.nan, np.float32)
    pp = np.full((n, KMAX), np.nan, np.float32)
    over = 0
    for i in range(n):
        v = sm[i]
        if not np.any(v > 0):
            continue
        m = len(v) - 1
        pk, pr = signal.find_peaks(np.r_[v[:0:-1], v], prominence=0)
        pk = pk - m
        keep = pk >= 0
        pk, prom = pk[keep], pr["prominences"][keep]
        o = np.argsort(pk, kind="stable")
        pk, prom = pk[o], prom[o]
        if len(pk) > KMAX:
            over += 1
            pk, prom = pk[:KMAX], prom[:KMAX]
        ps[i, :len(pk)] = fc.S[pk]
        pp[i, :len(pk)] = prom
    return ps, pp, over


def stage_peaks(mesh_dir, out_dir, which, shard):
    k_sh, n_sh = map(int, shard.split("/"))
    P, V, S, U = load(mesh_dir)
    out = Path(out_dir) / "peaks"
    out.mkdir(parents=True, exist_ok=True)
    cache = fc.ChunkCache()
    with cf.ThreadPoolExecutor(32) as pool:
        for (r, c) in (CTRL if which == "control" else TITLE)[k_sh::n_sh]:
            f = out / f"r{r}_c{c}.npz"
            if f.exists():
                continue
            t0 = time.time()
            g0, g1, h0, h1 = fc.tile_vertices(P, V, r, c)
            Pt = P[g0:g1, h0:h1].astype(np.float64)
            v = V[g0:g1, h0:h1]
            Nin, ok = fc.inward_normals(Pt, v, U)
            idx = np.argwhere(ok)
            ps = np.full((len(idx), KMAX), np.nan, np.float32)
            pp = np.full((len(idx), KMAX), np.nan, np.float32)
            over = 0
            for b0 in range(0, len(idx), 4096):
                ii = idx[b0:b0 + 4096]
                pts = Pt[ii[:, 0], ii[:, 1]][:, None, :] + Nin[ii[:, 0], ii[:, 1]][:, None, :] * (fc.S[None, :, None] / 2.4)
                prof = fc.sample_l1(pts.reshape(-1, 3), cache, pool).reshape(len(ii), len(fc.S))
                a, b, o = all_peaks(prof)
                ps[b0:b0 + len(ii)], pp[b0:b0 + len(ii)] = a, b
                over += o
            np.savez_compressed(f, idx=idx.astype(np.int32), ps=ps, pp=pp, grid=np.array([g0, g1, h0, h1]), overflow=over)
            print(json.dumps({"tile": f"r{r}_c{c}", "n": len(idx), "overflow": over, "wall_s": time.time() - t0}), flush=True)


def nanmedian9(G):
    pad = np.pad(G, 4, constant_values=np.nan)
    W = np.lib.stride_tricks.sliding_window_view(pad, (9, 9))
    return np.nanmedian(W.reshape(G.shape[0], G.shape[1], 81), axis=2)


def rule_naive(ps, pp, pmin):
    n = len(ps)
    s_own = np.zeros(n)
    s_face = np.full(n, np.nan)
    for i in range(n):
        s, p = ps[i], pp[i]
        f = np.isfinite(s)
        s, p = s[f], p[f]
        near = s <= 30.0
        if near.any():
            s_own[i] = s[near][np.argmax(p[near])]
        cand = (s > s_own[i] + 30.0) & (p >= pmin)
        if cand.any():
            s_face[i] = s[np.argmax(cand)]
    return s_own, s_face


def rule_reg(ps, pp, pmin, idx, shape, spacing_um):
    n = len(ps)
    s_own = np.zeros(n)
    first = np.full(n, np.nan)
    cands = []
    for i in range(n):
        s, p = ps[i], pp[i]
        f = np.isfinite(s)
        s, p = s[f], p[f]
        near = s <= 30.0
        if near.any():
            s_own[i] = s[near][np.argmax(p[near])]
        c = s[(s >= s_own[i] + 0.6 * spacing_um) & (p >= pmin)]
        cands.append(c)
        if c.size:
            first[i] = c[0]
    G = np.full(shape, np.nan)
    G[idx[:, 0], idx[:, 1]] = first
    M = nanmedian9(G)
    chosen = np.full(n, np.nan)
    for i in range(n):
        c = cands[i]
        m = M[idx[i, 0], idx[i, 1]]
        if c.size and np.isfinite(m):
            j = np.argmin(np.abs(c - m))
            if abs(c[j] - m) <= 20.0:
                chosen[i] = c[j]
    G2 = np.full(shape, np.nan)
    G2[idx[:, 0], idx[:, 1]] = chosen
    M2 = nanmedian9(G2)
    bad = np.abs(G2 - M2) > 20.0
    G2[bad] = np.nan
    fin = np.isfinite(G2)
    nb = np.zeros(shape, int)
    nb[1:] += fin[:-1]
    nb[:-1] += fin[1:]
    nb[:, 1:] += fin[:, :-1]
    nb[:, :-1] += fin[:, 1:]
    G2[fin & (nb == 0)] = np.nan
    return s_own, G2[idx[:, 0], idx[:, 1]]


KC = None


def check_v(Fm, okf, src_k, P, V, S, g):
    """Exact point-to-surface distance (um) of facing vertices to the official
    mesh with the source winding removed (columns of windings k-3..k+3)."""
    out = np.full(Fm.shape[:2], np.nan)
    Kc = KC if KC is not None else np.floor(S)
    for k in np.unique(src_k[okf]):
        sel = okf & (src_k == k)
        cols = np.where(np.any((Kc >= k - 1) & (Kc <= k + 1), axis=0))[0]
        if cols.size == 0:
            continue
        c0, c1 = cols.min(), cols.max() + 1
        rows = slice(max(0, g[0] - 60), min(V.shape[0], g[1] + 60))
        grid = P[rows, c0:c1].astype(np.float64).copy()
        inv = ~V[rows, c0:c1] | (Kc[rows, c0:c1] == k) | ~np.isfinite(S[rows, c0:c1])
        grid[inv] = -1.0
        d = tm.point_to_mesh_distance(Fm[sel].astype(np.float64), grid)
        out[sel] = d * 2.4
    a = out[okf]
    a = a[np.isfinite(a)]
    return {"n": int(a.size), "median_um": float(np.median(a)) if a.size else None,
            "frac_within_80um": float(np.mean(a <= 80)) if a.size else None,
            "pass": bool(a.size and np.median(a) <= 40 and np.mean(a <= 80) >= 0.8)}


def stage_rules(mesh_dir, out_dir, which, audit_rows):
    global KC
    P, V, S, U = load(mesh_dir)
    KC = np.floor(S)
    out = Path(out_dir)
    pmin = json.load(open(out / "p_min1.json"))["p_min1"]
    sp = {(j["r"], j["c"]): j.get("spacing_mm") for j in map(json.loads, open(audit_rows))}
    accepted = None
    accf = out / "reg_acceptance.json"
    if which == "title":
        accepted = json.load(open(accf))["accepted"]
    res = []
    for (r, c) in (CTRL if which == "control" else TITLE):
        pf = out / "peaks" / f"r{r}_c{c}.npz"
        rf = out / "rules" / f"r{r}_c{c}.json"
        if not pf.exists() or rf.exists():
            if rf.exists():
                res.append(json.load(open(rf)))
            continue
        rf.parent.mkdir(exist_ok=True)
        z = np.load(pf)
        idx, ps, pp = z["idx"], z["ps"], z["pp"]
        g0, g1, h0, h1 = [int(x) for x in z["grid"]]
        Pt = P[g0:g1, h0:h1].astype(np.float64)
        v = V[g0:g1, h0:h1]
        Nin, ok = fc.inward_normals(Pt, v, U)
        src_k = np.floor(S[g0:g1, h0:h1])
        rec = {"tile": f"r{r}_c{c}", "overflow": int(z["overflow"]), "spacing_um": None if sp.get((r, c)) is None else sp[(r, c)] * 1000}
        rules = [("naive", None)]
        if which == "control" or accepted:
            rules.append(("reg", rec["spacing_um"]))
        for name, spc in rules:
            if name == "naive":
                so, sf = rule_naive(ps, pp, pmin)
            else:
                if spc is None:
                    rec["reg"] = {"error": "no mesh_audit spacing for tile"}
                    continue
                so, sf = rule_reg(ps, pp, pmin, idx, v.shape, spc)
            s_grid = np.full(v.shape, np.nan, np.float32)
            s_grid[idx[:, 0], idx[:, 1]] = sf
            t = {"Pt": Pt, "Nin": Nin, "ok": ok, "idx": idx, "own": np.ones(len(idx)), "s_own": so, "s_face": sf, "s_grid": s_grid, "g": (g0, g1, h0, h1)}
            m, Fm = fc.metrics(t, r, c)
            okf = Fm[..., 0] != -1
            m["check_v"] = check_v(Fm, okf, src_k, P, V, S, (g0, g1, h0, h1))
            m["mesh_sha256_float32"] = hashlib.sha256(Fm.tobytes()).hexdigest()
            m["gate_and_v_pass"] = bool(m["gate_pass"] and m["check_v"]["pass"])
            np.savez_compressed(out / "rules" / f"r{r}_c{c}_{name}_sface_um.npz", s_face_um=s_grid.astype(np.float16))
            rec[name] = m
        json.dump(rec, open(rf, "w"), indent=1)
        res.append(rec)
        print(json.dumps({"tile": rec["tile"], **{k: {kk: rec[k][kk] for kk in ("frac_peak_found", "self_intersection_pairs", "gate_pass")} | {"v": rec[k]["check_v"]} for k in ("naive", "reg") if k in rec and "gate_pass" in rec[k]}}), flush=True)
    if which == "control":
        done = [x for x in res if "reg" in x and "gate_pass" in x["reg"]]
        acc = len(done) == len(CTRL) and all(x["reg"]["gate_and_v_pass"] for x in done)
        json.dump({"accepted": bool(acc), "n_control_tiles": len(done),
                   "n_pass_gate_and_v": sum(x["reg"]["gate_and_v_pass"] for x in done),
                   "rule": "DECL-P4-26-A1 item 3: every control tile passes the gate AND check (v)"}, open(accf, "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "peaks":
        stage_peaks(*sys.argv[2:6])
    else:
        stage_rules(*sys.argv[2:6])
