# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-26 item 1: facing-surface tifxyz meshes of 20260701183124-w010-027
strip-a tiles (title windows r0-r5 x c11-c19; control r0-r5 x c3-c8).
Numbers only; CT chunks are streamed into memory and reduced to 1-D profiles.

Fixed before any facing number exists (this file's first commit):
 * Ink side = inward (toward the umbilicus): p4-depth sign.json measured
   du x dv outward, and recto = inward (papyrological convention). Vertex
   normal n = normalised central-difference du x dv (mesh_audit.normals),
   oriented per tile so that the majority points away from the umbilicus;
   the profile direction is -n (inward).
 * Volume: 2.4 um volume 20260411134726 at pyramid level 1 (4.8 um voxels;
   L0 is ~20 GB of chunks per tile). Profile s = 0 .. 400 um in 2.4 um steps
   along -n from every valid tile vertex; trilinear; Gaussian sigma 1 L1
   voxel (4.8 um) along s.
 * Own sheet: the largest-prominence peak with s <= 30 um (s_own; if none,
   s_own = 0). Facing peak: the first peak with s > s_own + 30 um and
   prominence >= P_MIN1 (the gap on both sides is implied by prominence),
   s <= 400 um. P_MIN1 = 0.25 x the median own-sheet prominence over all
   control-tile vertices (computed from the controls before the title
   windows are processed; controls run first).
 * Facing mesh vertex = vertex - s_face * n * (1/2.4 um) with s_face the
   facing-peak distance; vertices with no peak are invalid (-1,-1,-1).
 * Per tile: frac_peak_found, the median / IQR gap (s_face - s_own) in um,
   self-intersection count (trace_metrics.self_intersection), and flattening
   (a) as-grid (FLAT-2 official rule: % quads with all 4 edges within +-5 %
   of the 20-vox step, and area-ratio fractions > 2 or < 0.5) and (b) ARAP
   via flatlib_flat2 (FLAT-2 evaluate: area and angle error). SLIM is not
   run (5-6 min per tile at 2.4 um; FLAT-2 found ARAP equivalent).
 * Gate: 0 self-intersections AND frac_peak_found >= 0.80.
 * L1 validation: at 40 vertices per tile the facing distance is recomputed
   from an L0 profile (mesh_audit.profile, 0..400 um) with the same rule;
   median |L1 - L0| reported.
 * Storage: per tile, s_face as float16 um on the tile grid (NaN = no
   peak), npz-compressed, with the sha256 of the float32 facing mesh; the
   mesh is rebuilt deterministically by rebuild() from the official mesh.
usage: facing.py <mesh_dir> <out_dir> <pmin|control|title> [k/n shard]
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import concurrent.futures as cf
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402
import trace_metrics as tm  # noqa: E402
from mesh_audit import normals, profile, T  # noqa: E402

LEVEL = 1
F = 2 ** LEVEL
S_MAX_UM, STEP_UM = 400.0, 2.4
S = np.arange(0.0, S_MAX_UM + 1e-9, STEP_UM)
VOL1 = cc.VOL[:-2] + f"/{LEVEL}"
CHUNK_CACHE_MAX = 900                     # x 2 MB


class ChunkCache:
    def __init__(self):
        self.d = OrderedDict()

    def get_many(self, keys, pool):
        need = [k for k in keys if k not in self.d]

        def fetch(k):
            url = f"{VOL1}/{k[0]}/{k[1]}/{k[2]}"
            for a in range(5):
                try:
                    import urllib.request
                    with urllib.request.urlopen(url, timeout=120) as r:
                        return k, np.frombuffer(r.read(), np.uint8).reshape(128, 128, 128)
                except urllib.error.HTTPError as e:
                    if e.code in (403, 404):
                        return k, None
                except Exception:
                    pass
                time.sleep(2 ** a)
            raise RuntimeError(url)

        for k, a in pool.map(fetch, need):
            self.d[k] = a
        for k in keys:
            self.d.move_to_end(k)
        got = {k: self.d[k] for k in keys}          # before eviction (a request may exceed the cache)
        while len(self.d) > CHUNK_CACHE_MAX:
            self.d.popitem(last=False)
        return got


def sample_l1(pts_l0, cache, pool):
    """Trilinear samples of level 1 at L0-frame points (n, 3) x, y, z.
    Points are grouped by chunk with one sort per corner (O(n log n))."""
    q = pts_l0 / F - 0.5 * (1 - 1 / F)    # L1 voxel centres (downsampled by 2)
    lo = np.floor(q).astype(np.int64)
    fr = (q - lo).astype(np.float32)
    corners = [(dx, dy, dz) for dz in (0, 1) for dy in (0, 1) for dx in (0, 1)]
    keys = set()
    for dx, dy, dz in corners:
        c = (lo + [dx, dy, dz]) // 128
        keys.update(map(tuple, np.unique(c[:, ::-1], axis=0).tolist()))
    ch = cache.get_many(sorted(keys), pool)
    out = np.zeros(len(q), np.float32)
    for dx, dy, dz in corners:
        v = lo + [dx, dy, dz]
        w = (fr[:, 0] if dx else 1 - fr[:, 0]) * (fr[:, 1] if dy else 1 - fr[:, 1]) * (fr[:, 2] if dz else 1 - fr[:, 2])
        c = v // 128
        o = v % 128
        key = (c[:, 2] << 40) | (c[:, 1] << 20) | c[:, 0]
        order = np.argsort(key, kind="stable")
        ks = key[order]
        cut = np.r_[0, np.nonzero(np.diff(ks))[0] + 1, len(ks)]
        vals = np.zeros(len(v), np.float32)
        for a0, a1 in zip(cut[:-1], cut[1:]):
            idx = order[a0:a1]
            k = (int(c[idx[0], 2]), int(c[idx[0], 1]), int(c[idx[0], 0]))
            arr = ch[k]
            if arr is None:
                continue
            vals[idx] = arr[o[idx, 2], o[idx, 1], o[idx, 0]]
        out += w * vals
    return out


def analyse(prof, pmin=None):
    """prof (n, len(S)) -> own prominence, s_own, s_face (NaN if none)."""
    sm = ndimage.gaussian_filter1d(prof, 2.0, axis=1)   # sigma 1 L1 voxel = 2 steps of 2.4 um
    n = len(sm)
    own_p = np.zeros(n)
    s_own = np.zeros(n)
    s_face = np.full(n, np.nan)
    for i in range(n):
        v = sm[i]
        if not np.any(v > 0):
            continue
        m = len(v) - 1                                       # mirror-pad so a peak at s = 0 has a true prominence
        pk, pr = signal.find_peaks(np.r_[v[:0:-1], v], prominence=0)
        pk = pk - m
        prom = pr["prominences"]
        keep = pk >= 0
        pk, prom = pk[keep], prom[keep]
        near = S[pk] <= 30.0
        if near.any():
            j = np.argmax(np.where(near, prom, -1))
            own_p[i], s_own[i] = prom[j], S[pk[j]]
        if pmin is None:
            continue
        cand = (S[pk] > s_own[i] + 30.0) & (prom >= pmin)
        if cand.any():
            s_face[i] = S[pk[np.argmax(cand)]]
    return own_p, s_own, s_face


def tile_vertices(P, V, r, c):
    H, W = V.shape
    g0, g1 = (r * T) // 20, min(H, ((r + 1) * T) // 20)
    h0, h1 = (c * T) // 20, min(W, ((c + 1) * T) // 20)
    return g0, g1, h0, h1


def inward_normals(Pt, v, U):
    N = normals(np.where(v[..., None], Pt, np.nan))
    ux = np.interp(Pt[..., 2], U[:, 0], U[:, 1])
    uy = np.interp(Pt[..., 2], U[:, 0], U[:, 2])
    rad = np.stack([Pt[..., 0] - ux, Pt[..., 1] - uy, np.zeros_like(ux)], -1)
    dot = np.sum(N * rad, -1)
    ok = v & np.isfinite(dot)
    sign = 1.0 if np.nanmedian(dot[ok]) >= 0 else -1.0
    return -sign * N, ok                       # inward


def rebuild(Pt, Nin, s_face_um):
    """Facing mesh (h, w, 3) float32 from the official tile grid, inward
    normals and s_face (um); -1 where no peak."""
    F_ = Pt + Nin * (s_face_um[..., None] / 2.4)
    bad = ~np.isfinite(F_).all(-1)
    F_[bad] = -1
    return F_.astype(np.float32)


def run_tile(P, V, U, r, c, cache, pool, pmin, block=64, subsample=None):
    g0, g1, h0, h1 = tile_vertices(P, V, r, c)
    Pt = P[g0:g1, h0:h1]
    v = V[g0:g1, h0:h1]
    Nin, ok = inward_normals(Pt, v, U)
    idx = np.argwhere(ok)
    if subsample is not None and len(idx) > subsample:
        idx = idx[np.sort(np.random.default_rng([20260930, r, c]).choice(len(idx), subsample, replace=False))]
    own = np.zeros(len(idx))
    sown = np.zeros(len(idx))
    sface = np.full(len(idx), np.nan)
    for b0 in range(0, len(idx), block * block):
        ii = idx[b0:b0 + block * block]
        p0 = Pt[ii[:, 0], ii[:, 1]]
        nn = Nin[ii[:, 0], ii[:, 1]]
        pts = p0[:, None, :] + nn[:, None, :] * (S[None, :, None] / 2.4)
        prof = sample_l1(pts.reshape(-1, 3), cache, pool).reshape(len(ii), len(S))
        o, so, sf = analyse(prof, pmin)
        own[b0:b0 + len(ii)], sown[b0:b0 + len(ii)], sface[b0:b0 + len(ii)] = o, so, sf
    s_grid = np.full(v.shape, np.nan, np.float32)
    s_grid[idx[:, 0], idx[:, 1]] = sface
    return {"g": (g0, g1, h0, h1), "Pt": Pt, "Nin": Nin, "ok": ok, "idx": idx, "own": own, "s_own": sown,
            "s_face": sface, "s_grid": s_grid}


def metrics(t, r, c):
    Fm = rebuild(t["Pt"], t["Nin"], t["s_grid"].astype(np.float64))
    okf = (Fm[..., 0] != -1)
    n_ok = int(t["ok"].sum())
    found = np.isfinite(t["s_face"])
    gap = (t["s_face"] - t["s_own"])[found]
    out = {"tile": f"r{r}_c{c}", "n_vertices": n_ok, "frac_peak_found": float(found.mean()) if n_ok else 0.0,
           "gap_um": {"p25": float(np.percentile(gap, 25)), "p50": float(np.median(gap)), "p75": float(np.percentile(gap, 75))} if gap.size else None,
           "own_prom_median": float(np.median(t["own"])) if n_ok else None}
    si = tm.self_intersection(np.where(okf[..., None], Fm.astype(np.float64), -1.0))
    out["self_intersection_pairs"] = int(si.get("n_intersecting_pairs", -1))
    # as-grid flattening
    Pm = np.where(okf[..., None], Fm.astype(np.float64), np.nan)
    eh = np.linalg.norm(np.diff(Pm, axis=1), axis=-1)
    ev = np.linalg.norm(np.diff(Pm, axis=0), axis=-1)
    q = okf[:-1, :-1] & okf[1:, :-1] & okf[:-1, 1:] & okf[1:, 1:]
    okq = (np.abs(eh[:-1] / 20 - 1) <= 0.05) & (np.abs(eh[1:] / 20 - 1) <= 0.05) & \
          (np.abs(ev[:, :-1] / 20 - 1) <= 0.05) & (np.abs(ev[:, 1:] / 20 - 1) <= 0.05)
    p00, p01, p10, p11 = Pm[:-1, :-1][q], Pm[:-1, 1:][q], Pm[1:, :-1][q], Pm[1:, 1:][q]
    a = 0.5 * np.linalg.norm(np.cross(p00 - p10, p01 - p10), axis=1) + 0.5 * np.linalg.norm(np.cross(p01 - p10, p11 - p10), axis=1)
    ratio = 400.0 / np.maximum(a, 1e-9)
    out["flat_grid"] = {"n_quads": int(q.sum()), "pct_quads_within_5pct": float(100 * np.mean(okq[q])) if q.any() else None,
                        "area_ratio_bad_frac": float(np.mean((ratio > 2) | (ratio < 0.5))) if q.any() else None}
    try:
        import flatlib_flat2 as fl
        # ARAP on a 2x-decimated grid (208 x 208) to bound runtime; decimation disclosed
        sub = np.where(okf[::2, ::2, None], Fm[::2, ::2].astype(np.float64), -1.0)
        mesh = fl.grid_to_mesh(sub)
        uv0 = fl.grid_init_uv(mesh, 40.0)
        UV, info = fl.flatten_arap(mesh.V, mesh.F, uv0, max_iter=100)
        uvg = fl.uv_to_grid(mesh, UV, sub.shape[:2])
        ev_ = fl.evaluate(sub, uvg, fl.quad_mask(sub))
        out["flat_arap_decim2"] = {k: ev_.get(k) for k in ("pct_quads_within_5pct_norm", "flipped_triangles", "area_ratio", "angle_abs_err_deg")}
    except Exception as e:  # reported, never hidden
        out["flat_arap_decim2"] = {"error": repr(e)[:300]}
    out["gate_pass"] = bool(out["self_intersection_pairs"] == 0 and out["frac_peak_found"] >= 0.80)
    return out, Fm


def l0_check(t, pmin_l0_scale, rng):
    """Facing distance from L0 profiles at 40 vertices, same rule (P_MIN scaled per tile)."""
    idx = t["idx"]
    pick = rng.choice(len(idx), min(40, len(idx)), replace=False)
    diffs = []
    for k in pick:
        i, j = idx[k]
        if not np.isfinite(t["s_face"][k]):
            continue
        p0 = t["Pt"][i, j] + t["Nin"][i, j] * (200 / 2.4)      # centre of 0..400 um
        tt, v = profile(p0, t["Nin"][i, j], half=int(round(200 / 2.4)))
        v = v[None, :]
        s_l0 = (tt + 200 / 2.4) * 2.4
        sm = ndimage.gaussian_filter1d(v, 2.0, axis=1)[0]
        pk, pr = signal.find_peaks(sm, prominence=0)
        own = [(pr["prominences"][m], s_l0[p]) for m, p in enumerate(pk) if s_l0[p] <= 30]
        so = max(own)[1] if own else 0.0
        cand = [s_l0[p] for m, p in enumerate(pk) if s_l0[p] > so + 30 and pr["prominences"][m] >= pmin_l0_scale]
        if cand:
            diffs.append(abs(cand[0] - t["s_face"][k]))
    a = np.array(diffs)
    return {"n": int(a.size), "median_abs_um": float(np.median(a)) if a.size else None,
            "frac_within_10um": float(np.mean(a <= 10)) if a.size else None}


def main(mesh_dir, out_dir, which, shard="0/1"):
    k_sh, n_sh = map(int, shard.split("/"))
    d = Path(mesh_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    X, Y, Z = (np.load(d / f"{c}.npy") for c in "xyz")
    V = (X != -1) & np.isfinite(Z) & (Z > 0)
    P = np.stack([X, Y, Z], -1).astype(np.float64)
    del X, Y, Z
    a = json.load(open(d / "umb.json"))
    U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
    cache = ChunkCache()
    ctrl = [(r, c) for r in range(6) for c in range(3, 9)]
    title = [(r, c) for r in range(6) for c in range(11, 20)]
    pfile = out / "p_min1.json"
    with cf.ThreadPoolExecutor(32) as pool:
        if not pfile.exists():
            # own-sheet prominences over the controls define P_MIN1 (no facing peaks yet)
            owns = []
            for (r, c) in ctrl:
                t = run_tile(P, V, U, r, c, cache, pool, None, subsample=3000)
                owns.append(np.median(t["own"]))
                print("pmin pass", r, c, float(np.median(t["own"])), flush=True)
            json.dump({"p_min1": 0.25 * float(np.median(owns)), "per_tile_own_median": owns,
                       "rule": "0.25 x median over control tiles of the per-tile median own-sheet prominence; per-tile median from 3000 random valid vertices (rng [20260930, r, c]) - amendment disclosed 2026-09-27 ~08:10Z for runtime, before any facing number"},
                      open(pfile, "w"), indent=1)
        if which == "pmin":
            return
        pmin = json.load(open(pfile))["p_min1"]
        todo = (ctrl if which == "control" else title)
        for (r, c) in todo[k_sh::n_sh]:
            f = out / f"r{r}_c{c}.json"
            if f.exists():
                continue
            t0 = time.time()
            t = run_tile(P, V, U, r, c, cache, pool, pmin)
            m, Fm = metrics(t, r, c)
            m["l1_vs_l0"] = l0_check(t, pmin, np.random.default_rng([20260929, r, c]))
            m["mesh_sha256_float32"] = hashlib.sha256(Fm.tobytes()).hexdigest()
            m["grid_rows_cols"] = list(t["g"])
            m["wall_s"] = time.time() - t0
            np.savez_compressed(out / f"r{r}_c{c}_sface_um.npz", s_face_um=t["s_grid"].astype(np.float16))
            json.dump(m, open(f, "w"), indent=1)
            print(json.dumps({k: m[k] for k in ("tile", "frac_peak_found", "self_intersection_pairs", "gate_pass", "wall_s")}), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:5])
