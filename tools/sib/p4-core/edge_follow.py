# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-24-A1 (e2): sheet-following edge test for w010-027 strip-a.
Numbers only (L0 byte-range profiles, as holes.py / mesh_audit.py).

Fixed before any (e2) number exists (this file's first commit):
 * Edge ray (as holes.py (e)): column j, outermost valid vertex of the tile
   (r0: smallest row = top z; r8: largest row); tangent t = unit linear fit
   of xyz vs row over the last 10 valid vertices, pointing out of the mesh;
   normal n = the nearest inward vertex with a finite normal (mesh_audit
   normals, oriented away from the umbilicus by tile majority).
 * Follow: p <- p + 0.1 mm * d (d = +t beyond the edge, -t into the mesh);
   then the L0 profile along n over +-60 um (sigma 1 vox); the largest-
   prominence peak with prominence >= P_MIN (holes_agg p_min_prominence,
   the c0-c8 reference rule of DECL-P4-24 (d)); re-centre p <- p + off * n.
   Stop at the first step with no such peak, or with |off| > 40 um (a
   break). L = 0.1 mm x the number of completed steps (cap 12.5 mm beyond
   the edge, 2.0 mm for validation). n and d are kept fixed along a ray.
 * Validation (into the mesh, r0 and r8 edges, columns every 25 grid cells
   over c0-c19): at 0.5, 1, 1.5, 2 mm the perpendicular offset of the
   followed point from the true mesh = |(p - q) . n_q| with q the nearest
   valid vertex of the tile (KD-tree) and n_q its normal. A column passes if
   it reaches 2 mm and its offset AT 2 mm is <= 30 um (the path-mean offset
   up to 2 mm is reported too). (e2) is VALID iff >= 80 % of columns pass,
   for r0 and r8 pooled (and each reported).
 * Beyond the edge (only if VALID): 40 rays per tile (as holes.py (e)) for
   r0 and r8 tiles c9-c19 (c14-c17 first) and c0-c8 as reference; L per ray
   and per column; HOLE-FLAG(edge) iff L >= 2 mm on >= 25 % of a tile's
   rays; for c14-c17, P = 0.24 x min(1, L / 12.5 mm) per ray (p4-titulus
   Q5 (d)), reported as the tile median.
usage: edge_follow.py <mesh_dir> <p_min> <out.json> validate|beyond [v1|v2]

AMENDMENT v2 (2026-09-27 ~06:50Z, disclosed; before any recorded (e2)
number and before any beyond-edge profile): a 3-column smoke test INTO the
known mesh (r0 cols 1000/3000/5000, P_MIN 15 provisional, output discarded)
showed v1 stopping on "jump" after 0-1 mm because at sigma 1 vox a single
sheet shows two peaks ~30-40 um apart (its two fibre layers). v2 = Gaussian
FWHM 20 um (sigma 3.54 vox, the DECL-P4-7 kernel) and re-centring on the
NEAREST peak with prominence >= P_MIN2, P_MIN2 = 0.25 x the median, over the
validation columns, of the largest v2 prominence at the edge vertex itself
(step 0, on the known mesh). v1 is still run and reported unchanged; the
validation criterion is unchanged; beyond the edge uses v1 if VALID, else v2
if VALID, else nothing.
"""

from __future__ import annotations

import json
import sys
import time
import concurrent.futures as cf
from pathlib import Path

import numpy as np
from scipy import ndimage, signal
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_audit import normals, profile, T  # noqa: E402

VOXMM = 2.4e-3
STEP_MM = 0.1


VARIANT = "v1"
SIG = {"v1": 1.0, "v2": 20.0 / 2.354820045 / 2.4}


def peaks(p, n):
    t, v = profile(p, n)
    if not np.any(v > 0):
        return t, np.zeros(0, int), np.zeros(0)
    vs = ndimage.gaussian_filter1d(v.astype(float), SIG[VARIANT])
    pk, pr = signal.find_peaks(vs, prominence=0)
    return t, pk, pr["prominences"]


def peak_offset(p, n, pmin):
    t, pk, prom = peaks(p, n)
    if pk.size == 0:
        return None
    if VARIANT == "v1":
        i = int(np.argmax(prom))
        if prom[i] < pmin:
            return None
        return float(t[pk[i]])            # vox along n
    ok = prom >= pmin
    if not ok.any():
        return None
    j = np.where(ok)[0][np.argmin(np.abs(t[pk[ok]]))]
    return float(t[pk[j]])


def follow(p0, d, n, pmin, max_mm, record_at=()):
    p = p0.astype(float).copy()
    steps = int(round(max_mm / STEP_MM))
    pts = {}
    L = 0.0
    stop = "cap"
    for k in range(1, steps + 1):
        p = p + d * (STEP_MM / VOXMM)
        off = peak_offset(p, n, pmin)
        if off is None:
            stop = "no_peak"
            break
        if abs(off) * VOXMM * 1000 > 40:
            stop = "jump"
            break
        p = p + off * n
        L = k * STEP_MM
        for r in record_at:
            if abs(L - r) < 1e-9:
                pts[r] = p.copy()
    return L, stop, pts


def edge_rays_for(P, V, N, r, cols):
    g0, g1 = (r * T) // 20, min(V.shape[0], ((r + 1) * T) // 20)
    rays = []
    for j in cols:
        rows = np.where(V[g0:g1, j])[0] + g0
        if len(rows) < 60:
            continue
        seq = rows[:10] if r == 0 else rows[-10:]
        i0 = seq[0] if r == 0 else seq[-1]
        d = np.polyfit(seq.astype(float), P[seq, j], 1)[0]
        t = (-1 if r == 0 else 1) * d / (np.linalg.norm(d) + 1e-12)
        fin = [i for i in (rows[:40] if r == 0 else rows[-40:][::-1]) if np.all(np.isfinite(N[i, j]))]
        if not fin:
            continue
        rays.append({"col": int(j), "tile_c": int(j * 20 // T), "i0": int(i0), "p0": P[i0, j], "t": t, "n": N[fin[0], j]})
    return rays


def oriented_normals(P, V, U, g0, g1):
    Pt = P[g0:g1]
    N = normals(np.where(V[g0:g1, :, None], Pt, np.nan))
    ux = np.interp(Pt[..., 2], U[:, 0], U[:, 1])
    uy = np.interp(Pt[..., 2], U[:, 0], U[:, 2])
    dot = N[..., 0] * (Pt[..., 0] - ux) + N[..., 1] * (Pt[..., 1] - uy)
    s = 1.0 if np.nanmedian(dot[V[g0:g1]]) >= 0 else -1.0
    return s * N


def oriented_normals_full(P, V, U):
    g0, g1 = (8 * T) // 20, V.shape[0]
    N = np.full(P.shape, np.nan, np.float32)
    N[g0:g1] = oriented_normals(P, V, U, g0, g1)
    return N


def main(mesh_dir, pmin, out, mode, variant="v1"):
    global VARIANT
    VARIANT = variant
    pmin = float(pmin)
    d = Path(mesh_dir)
    X, Y, Z = (np.load(d / f"{c}.npy") for c in "xyz")
    V = (X != -1) & np.isfinite(Z) & (Z > 0)
    P = np.stack([X, Y, Z], -1).astype(np.float64)
    del X, Y, Z
    a = json.load(open(d / "umb.json"))
    U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
    ncols = min(V.shape[1], (20 * T) // 20)
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "entry": f"DECL-P4-24-A1 (e2) {mode}", "variant": VARIANT, "sigma_vox": SIG[VARIANT], "p_min": pmin, "rows": {}}
    t0 = time.time()
    with cf.ThreadPoolExecutor(24) as pool:
        for r in (0, 8):
            g0, g1 = (r * T) // 20, min(V.shape[0], ((r + 1) * T) // 20)
            N = np.full(P.shape, np.nan, np.float32)
            N[g0:g1] = oriented_normals(P, V, U, g0, g1)
            if mode == "validate":
                rays = edge_rays_for(P, V, N, r, range(0, ncols, 25))
                if VARIANT == "v2" and r == 0:
                    pr0 = list(pool.map(lambda ry: (lambda q: float(q[2].max()) if q[2].size else 0.0)(peaks(ry["p0"], ry["n"])), rays))
                    rays8 = edge_rays_for(P, V, np.nan_to_num(oriented_normals_full(P, V, U)), 8, range(0, ncols, 25))
                    pr8 = list(pool.map(lambda ry: (lambda q: float(q[2].max()) if q[2].size else 0.0)(peaks(ry["p0"], ry["n"])), rays8))
                    pmin = 0.25 * float(np.median(pr0 + pr8))
                    res["p_min"] = pmin
                    res["p_min_rule"] = "v2: 0.25 x median largest prominence at the edge vertex (step 0) over r0+r8 validation columns"
                vv = V[g0:g1]
                ids = np.argwhere(vv)
                Pv = P[g0:g1][vv]
                tree = cKDTree(Pv)
                Nv = N[g0:g1][vv].astype(np.float64)

                def one(ray):
                    L, stop, pts = follow(ray["p0"], -ray["t"], ray["n"], pmin, 2.0, (0.5, 1.0, 1.5, 2.0))
                    offs = {}
                    for dist, p in pts.items():
                        _, k = tree.query(p)
                        offs[str(dist)] = float(abs((p - Pv[k]) @ Nv[k]) * VOXMM * 1000) if np.all(np.isfinite(Nv[k])) else None
                    ok2 = [v for v in offs.values() if v is not None]
                    return {"col": ray["col"], "tile_c": ray["tile_c"], "L_mm": L, "stop": stop, "offset_um": offs,
                            "path_mean_um": float(np.mean(ok2)) if ok2 else None,
                            "pass": bool(L >= 2.0 - 1e-9 and offs.get("2.0") is not None and offs["2.0"] <= 30)}

                rows = list(pool.map(one, rays))
                res["rows"][f"r{r}"] = {"n_columns": len(rows), "frac_pass": float(np.mean([x["pass"] for x in rows])) if rows else None,
                                        "frac_reach_2mm": float(np.mean([x["L_mm"] >= 2.0 - 1e-9 for x in rows])) if rows else None,
                                        "offset_at_2mm_um_p50": float(np.median([x["offset_um"]["2.0"] for x in rows if x["offset_um"].get("2.0") is not None])) if rows else None,
                                        "columns": rows}
            else:
                order = list(range(14, 18)) + [9, 10, 11, 12, 13, 18, 19] + list(range(0, 9))
                tiles = {}
                for c in order:
                    h0, h1 = (c * T) // 20, min(ncols, ((c + 1) * T) // 20)
                    cols = [h0 + int(k) for k in np.linspace(0, h1 - h0 - 1, 40)]
                    rays = edge_rays_for(P, V, N, r, cols)

                    def one(ray):
                        L, stop, _ = follow(ray["p0"], ray["t"], ray["n"], pmin, 12.5)
                        return {"col": ray["col"], "L_mm": L, "stop": stop}

                    rr = list(pool.map(one, rays))
                    Ls = np.array([x["L_mm"] for x in rr]) if rr else np.zeros(0)
                    rec = {"n_rays": len(rr), "L_mm_p25_p50_p75": [float(np.percentile(Ls, q)) for q in (25, 50, 75)] if rr else None,
                           "frac_L_ge_2mm": float(np.mean(Ls >= 2.0 - 1e-9)) if rr else None,
                           "edge_flag": bool(rr and c >= 9 and np.mean(Ls >= 2.0 - 1e-9) >= 0.25), "rays": rr}
                    if 14 <= c <= 17 and rr:
                        rec["P_titulus_median"] = float(np.median(0.24 * np.minimum(1, Ls / 12.5)))
                    tiles[f"r{r}_c{c}"] = rec
                    res["rows"][f"r{r}"] = tiles
                    json.dump(res, open(out, "w"), indent=1)
                    print(r, c, rec["frac_L_ge_2mm"], rec["L_mm_p25_p50_p75"], flush=True)
            if mode == "validate":
                print(r, json.dumps({k: v for k, v in res["rows"][f"r{r}"].items() if k != "columns"}), flush=True)
    if mode == "validate":
        cols = [x for rr in res["rows"].values() for x in rr["columns"]]
        res["pooled_frac_pass"] = float(np.mean([x["pass"] for x in cols])) if cols else None
        res["VALID"] = bool(res["pooled_frac_pass"] is not None and res["pooled_frac_pass"] >= 0.80)
    res["wall_s"] = time.time() - t0
    json.dump(res, open(out, "w"), indent=1)
    print("VALID" if res.get("VALID") else "", res.get("pooled_frac_pass"), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:6])
