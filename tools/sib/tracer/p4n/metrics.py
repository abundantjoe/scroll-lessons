# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-N validation metrics (RULES.md DECL-P4-13), geometry only. All distances in NATIVE 2.4 um voxels unless
a key says L2 (9.6 um). No image, CT intensity or ink value is read.

metrics(run_dir, mode) -> dict, written to <run_dir>/metrics.json

1. official_unchanged   every resumed official vertex is found in the output at its exact position
                        (max displacement; must be 0 up to float32 round-off of the L2 frame, <= 1e-3 L2 vox).
2. seam                 per official column: the first new vertex above the official top vertex vs the
                        quadratic continuation of the official column (3 top rows): 3-D residual and its
                        component along the official surface normal; kink angle between the official top
                        edge and the seam edge. Declared bar: median seam point distance <= 2 vox (native).
                        Operationalisation (a shared-grid resume has no second seam curve): the normal
                        component is the primary number; the 3-D residual is reported alongside.
3. self_intersection    vc_tifxyz_selfcross on the output: transverse crossings total and those that touch a
                        new quad. Bar: 0 touching a new quad (and 0 total reported).
4. neighbour_winding    for each new vertex: point-to-surface distance (fail-closed CORR-RETRACE form:
                        min of nearest densified vertex and exact point-to-triangle) to every OTHER winding,
                        i.e. all official (full 2.4 um mesh, rows near the top) and output vertices at grid
                        Chebyshev distance >= EXCL (L2 grid units) from it. Local spacing: the same clearance
                        measured for official vertices in the top 2 mm, median per official tile column.
                        Bar: clearance >= 0.6 x local spacing for every new vertex (fraction reported).
5. flattening           FLAT-2 (sib-flat1 flatlib, sha256 in ext/FLATLIB_SOURCE.txt): SLIM from the grid
                        start on the new quads plus a 3-row seam band; flatlib.evaluate (quads within +-5 %,
                        area |log|, angle error, flips).
6. holdout only         recovery vs the held-out official vertices: point-to-surface distance from new
                        vertices to the truth surface and from truth vertices to the new surface (coverage).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "ext"))
sys.path.insert(0, str(HERE.parent))
import prep  # noqa: E402

REPO = Path("/home/user/dominion")
EXCL = 60             # L2 grid units (11.5 mm along the sheet) treated as the same winding
SUB = prep.SUB
VOX_MM = prep.VOX_MM


def read_grid(d: Path) -> np.ndarray:
    return np.stack([tifffile.imread(d / f"{a}.tif") for a in "xyz"], axis=-1).astype(np.float64)


def find_output(run: Path) -> Path:
    segs = [p for p in run.iterdir() if p.is_dir() and (p / "x.tif").exists()]
    if len(segs) > 1:                                  # prefer the tracer's own output over derived surfaces
        segs = [p for p in segs if p.name.startswith("auto_grown")] or segs
    if len(segs) != 1:
        raise SystemExit(f"expected one output surface in {run}, found {len(segs)}")
    return segs[0]


def locate_resume(out_loc: np.ndarray, patch_loc: np.ndarray) -> tuple[int, int, dict]:
    """Grid offset (dy, dx) of the resume patch inside the output, from exact coordinate matches."""
    ov = out_loc[..., 0] != -1
    key = lambda p: np.round(p * 1000).astype(np.int64)
    oi = np.argwhere(ov)
    d = {tuple(k): tuple(ix) for k, ix in zip(key(out_loc[ov]), oi)}
    pv = np.argwhere(patch_loc[..., 0] != -1)
    offs = []
    for j, i in pv[:: max(1, len(pv) // 2000)]:
        hit = d.get(tuple(key(patch_loc[j, i])))
        if hit is not None:
            offs.append((hit[0] - j, hit[1] - i))
    if not offs:
        raise SystemExit("no official vertex found unchanged in the output")
    vals, cnt = np.unique(np.array(offs), axis=0, return_counts=True)
    dy, dx = vals[np.argmax(cnt)]
    return int(dy), int(dx), {"n_probe": len(offs), "offset_votes": int(cnt.max())}


def official_unchanged(out_loc, patch_loc, dy, dx) -> dict:
    pv = patch_loc[..., 0] != -1
    H, W = patch_loc.shape[:2]
    o = out_loc[dy:dy + H, dx:dx + W]
    ov = o[..., 0] != -1
    both = pv & ov
    disp = np.linalg.norm(o[both] - patch_loc[both], axis=1)
    return {"n_official": int(pv.sum()), "n_present": int(both.sum()), "n_removed": int((pv & ~ov).sum()),
            "max_disp_L2": float(disp.max()) if disp.size else None,
            "pass": bool((pv & ~ov).sum() == 0 and disp.size and disp.max() <= 1e-3)}


def normals(g: np.ndarray) -> np.ndarray:
    v = g[..., 0] != -1
    gy = np.zeros_like(g); gx = np.zeros_like(g)
    gy[1:-1] = g[2:] - g[:-2]; gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    n = np.cross(gx, gy)
    ok = v.copy()
    ok[1:-1] &= v[2:] & v[:-2]; ok[:, 1:-1] &= v[:, 2:] & v[:, :-2]
    ok[[0, -1]] = False; ok[:, [0, -1]] = False
    ln = np.linalg.norm(n, axis=-1, keepdims=True)
    n = np.where(ok[..., None] & (ln > 0), n / np.maximum(ln, 1e-12), np.nan)
    return n


def seam(out_nat, new_mask, dy, dx, patch_shape) -> dict:
    """Per output column inside the patch: official top vertex t (topmost official row), rows t+1,t+2 below;
    the new vertex at t-1."""
    H, W = patch_shape
    off = np.zeros(out_nat.shape[:2], bool)
    off[dy:dy + H, dx:dx + W] = (out_nat[dy:dy + H, dx:dx + W, 0] != -1) & ~new_mask[dy:dy + H, dx:dx + W]
    n = normals(np.where(off[..., None], out_nat, -1.0))
    res3, resn, kink, ncol = [], [], [], 0
    for c in range(dx, dx + W):
        rows = np.flatnonzero(off[:, c])
        if rows.size < 3:
            continue
        t = rows.min()
        if t < 1 or not (off[t + 1, c] and off[t + 2, c]) or not new_mask[t - 1, c]:
            continue
        ncol += 1
        p0, p1, p2 = out_nat[t, c], out_nat[t + 1, c], out_nat[t + 2, c]
        pred = 3 * p0 - 3 * p1 + p2
        e = out_nat[t - 1, c] - pred
        res3.append(float(np.linalg.norm(e)))
        nn = n[t, c] if np.isfinite(n[t, c]).all() else n[t + 1, c]
        if np.isfinite(nn).all():
            resn.append(float(abs(e @ nn)))
        a, b = p0 - p1, out_nat[t - 1, c] - p0
        kink.append(float(np.degrees(np.arccos(np.clip(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1)))))
    f = lambda x: {"n": len(x), "median": float(np.median(x)) if x else None,
                   "p90": float(np.percentile(x, 90)) if x else None}
    out = {"n_seam_columns": ncol, "normal_residual_vox": f(resn), "residual_3d_vox": f(res3), "kink_deg": f(kink)}
    out["pass_median_normal_le_2vox"] = bool(resn) and float(np.median(resn)) <= 2.0
    return out


def selfcross(out_dir: Path, work: Path, new_mask, label) -> dict:
    import surfmetrics as SM
    rep = SM.selfcross(out_dir, work / "selfcross.json", REPO / "logs/sib/tracer/runs.jsonl", label)
    pairs = SM.crossing_pairs(rep)
    touch = 0
    for qa, qb in pairs:
        for (r, c) in (qa, qb):
            if new_mask[r:r + 2, c:c + 2].any():
                touch += 1
                break
    return {"transverse_pairs": len(pairs), "pairs_touching_new": touch,
            "coplanar": rep.get("coplanar_pairs", rep.get("coplanar")), "pass": touch == 0}


def tri_mesh(g: np.ndarray, ids: np.ndarray):
    """Triangles of a grid (both diagonals' fail-closed union is not needed for distance: one split)."""
    v = g[..., 0] != -1
    q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    r, c = np.nonzero(q)
    A, B, C, D = g[r, c], g[r, c + 1], g[r + 1, c], g[r + 1, c + 1]
    tris = np.concatenate([np.stack([A, B, D], 1), np.stack([A, D, C], 1)])
    tid = np.concatenate([ids[r, c], ids[r, c]])
    return tris, tid


def point_tri_dist(p, tri):
    """Exact point-triangle distance (Ericson), vectorised over pairs."""
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(va + vb + vc == 0, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den
    q = a + ab * v[:, None] + ac * w[:, None]
    # region tests
    m = (d1 <= 0) & (d2 <= 0); q[m] = a[m]
    m2 = (d3 >= 0) & (d4 <= d3); q[m2] = b[m2]
    m3 = (d6 >= 0) & (d5 <= d6); q[m3] = c[m3]
    m4 = (vc <= 0) & (d1 >= 0) & (d3 <= 0) & ~(m | m2)
    t4 = d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3); q[m4] = (a + ab * t4[:, None])[m4]
    m5 = (vb <= 0) & (d2 >= 0) & (d6 <= 0) & ~(m | m3)
    t5 = d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6); q[m5] = (a + ac * t5[:, None])[m5]
    m6 = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0) & ~(m2 | m3)
    t6 = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6))
    q[m6] = (b + (c - b) * t6[:, None])[m6]
    return np.linalg.norm(p - q, axis=1)


def clearance(query, qrc, pts, prc, tris, trc, k=24) -> np.ndarray:
    """Min distance from each query to surfaces of OTHER windings: candidates with grid Chebyshev distance
    >= EXCL (rc in common L2-grid units). Fail-closed: min over nearest-vertex and point-triangle forms."""
    out = np.full(len(query), np.inf)
    vt = cKDTree(pts)
    cent = tris.mean(1)
    tt = cKDTree(cent)
    far = lambda a, b: np.max(np.abs(a - b), axis=-1) >= EXCL
    for kk in (k, 4 * k, 16 * k):
        todo = ~np.isfinite(out)
        if not todo.any():
            break
        dv, iv = vt.query(query[todo], k=min(kk, len(pts)))
        ok = far(prc[iv], qrc[todo][:, None, :])
        dvv = np.where(ok, dv, np.inf).min(1)
        dt, it = tt.query(query[todo], k=min(kk, len(cent)))
        okt = far(trc[it], qrc[todo][:, None, :])
        best = np.full(todo.sum(), np.inf)
        for j in range(it.shape[1]):
            sel = okt[:, j]
            if sel.any():
                dd = point_tri_dist(query[todo][sel], tris[it[sel, j]])
                best[sel] = np.minimum(best[sel], dd)
        res = np.minimum(dvv, best)
        # accept only if the nearest far candidate is closer than the k-th neighbour radius (else widen k)
        found = res <= dv[:, -1]
        cur = out[todo]; cur[found] = res[found]; out[todo] = cur
    return out


def neighbour_winding(out_nat, new_mask, dy, dx, official_cols0) -> dict:
    """Common grid units = L2 grid (official native cols / SUB). Output grid (r, c) -> official col
    official_cols0 + (c - dx) * SUB."""
    P = prep.load_official()
    a, b = official_cols0
    rows_top = 400
    Ps = P[:rows_top:SUB, ::SUB]
    ov = Ps[..., 0] != -1
    rr, cc = np.nonzero(ov)
    orc = np.stack([rr - 0.0, cc.astype(float)], 1)            # official L2-grid rc (rows from official row 0)
    # output rc in the same units: output row r -> official sub row (r - dy); col c -> (a/SUB) + (c - dx)
    vv = out_nat[..., 0] != -1
    R, C = np.nonzero(vv)
    newv = new_mask[R, C]
    urc = np.stack([(R - dy).astype(float), a / SUB + (C - dx)], 1)
    pts = np.concatenate([Ps[ov], out_nat[R[newv], C[newv]]])
    prc = np.concatenate([orc, urc[newv]])
    ids = np.full(Ps.shape[:2] + (2,), np.nan); ids[rr, cc] = orc
    t1, r1 = tri_mesh(Ps, ids)
    g2 = np.where(new_mask[..., None], out_nat, -1.0)
    ids2 = np.full(out_nat.shape[:2] + (2,), np.nan); ids2[R, C] = urc
    t2, r2 = tri_mesh(g2, ids2)
    tris = np.concatenate([t1, t2]); trc = np.concatenate([r1, r2])
    # local spacing: official vertices in the top 2 mm of each column, clearance to other windings
    top = np.argmax(ov, axis=0)
    band = ov & (np.arange(ov.shape[0])[:, None] - top[None, :] < math.ceil(2.0 / (20 * SUB * VOX_MM)))
    br, bc = np.nonzero(band)
    sp = clearance(Ps[br, bc], np.stack([br.astype(float), bc.astype(float)], 1), pts, prc, tris, trc)
    T = prep.T_GRID / SUB
    tile = (bc / T).astype(int)
    spacing = {int(t): float(np.median(sp[(tile == t) & np.isfinite(sp)])) for t in np.unique(tile)
               if np.isfinite(sp[tile == t]).any()}
    q = out_nat[R[newv], C[newv]]
    cl = clearance(q, urc[newv], pts, prc, tris, trc)
    qt = (urc[newv][:, 1] / T).astype(int)
    loc = np.array([spacing.get(int(t), np.nan) for t in qt])
    ratio = cl / loc
    fin = np.isfinite(ratio)
    return {"excl_grid_L2": EXCL, "n_new": int(newv.sum()), "n_measured": int(fin.sum()),
            "local_spacing_vox_by_tile": spacing,
            "clearance_vox": {"min": float(np.min(cl[np.isfinite(cl)])) if np.isfinite(cl).any() else None,
                              "median": float(np.median(cl[np.isfinite(cl)])) if np.isfinite(cl).any() else None},
            "ratio": {"min": float(ratio[fin].min()) if fin.any() else None,
                      "p1": float(np.percentile(ratio[fin], 1)) if fin.any() else None,
                      "median": float(np.median(ratio[fin])) if fin.any() else None},
            "frac_ge_0p6": float(np.mean(ratio[fin] >= 0.6)) if fin.any() else None,
            "n_no_other_winding_within_search": int((~np.isfinite(cl)).sum()),
            # control: the same ratio for the official top-2-mm vertices against their own tile medians
            "official_band_baseline": (lambda r: {"n": int(r.size), "frac_ge_0p6": float(np.mean(r >= 0.6)),
                                                  "min": float(r.min()), "p1": float(np.percentile(r, 1))})(
                (sp / np.array([spacing.get(int(t), np.nan) for t in tile]))[np.isfinite(sp)]),
            "pass": bool(fin.any() and np.all(ratio[fin] >= 0.6))}


def flattening(out_nat, new_mask) -> dict:
    import flatlib as FL
    band = new_mask.copy()
    for _ in range(3):                                   # 3-row seam band of official vertices
        band[1:] |= band[:-1] & (out_nat[1:, :, 0] != -1)
    g = np.where(band[..., None], out_nat, -1.0)
    rows = np.flatnonzero(band.any(1)); cols = np.flatnonzero(band.any(0))
    g = g[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    qm = FL.quad_mask(g)
    mesh = FL.grid_to_mesh(g, qm)
    step = float(np.median(np.linalg.norm(g[:, 1:] - g[:, :-1], axis=-1)[qm[:, :] if False else
                 (g[:, 1:, 0] != -1) & (g[:, :-1, 0] != -1)]))
    UV0 = FL.grid_init_uv(mesh, step)
    UV, info = FL.flatten_slim(mesh.V, mesh.F, UV0)
    uv = FL.uv_to_grid(mesh, UV, g.shape[:2])
    ev = FL.evaluate(g, uv, qm)
    return {"method": "SLIM (flatlib.flatten_slim, grid start)", "slim_info": info, "evaluate": ev}


def recovery(out_nat, new_mask, run: Path) -> dict:
    truth = np.load(Path("/work/p4n/patches/holdout.tifxyz_truth_native.npy")).astype(np.float64)
    tv = truth[..., 0] != -1
    T = truth[tv]
    ids = np.zeros(truth.shape[:2] + (2,))
    tris, _ = tri_mesh(truth, ids)
    tt = cKDTree(tris.mean(1))
    q = out_nat[new_mask]
    dt, it = tt.query(q, k=8)
    d = np.min(np.stack([point_tri_dist(q, tris[it[:, j]]) for j in range(8)], 1), 1)
    # only new vertices lying within the held-out z band are scored against truth
    zlo, zhi = T[:, 2].min(), T[:, 2].max()
    inband = (q[:, 2] >= zlo) & (q[:, 2] <= zhi)
    dn = d[inband]
    g = np.where(new_mask[..., None], out_nat, -1.0)
    ntr, _ = tri_mesh(g, np.zeros(g.shape[:2] + (2,)))
    cov = {}
    if len(ntr):
        nt = cKDTree(ntr.mean(1))
        _, jt = nt.query(T, k=8)
        dc = np.min(np.stack([point_tri_dist(T, ntr[jt[:, j]]) for j in range(8)], 1), 1)
        cov = {"truth_n": int(len(T)), "truth_frac_within_4vox": float(np.mean(dc <= 4)),
               "truth_frac_within_8vox": float(np.mean(dc <= 8)), "truth_median_vox": float(np.median(dc))}
    return {"n_new_in_truth_band": int(inband.sum()),
            "new_to_truth_vox": {"median": float(np.median(dn)) if dn.size else None,
                                 "p90": float(np.percentile(dn, 90)) if dn.size else None,
                                 "frac_le_2": float(np.mean(dn <= 2)) if dn.size else None,
                                 "frac_le_4": float(np.mean(dn <= 4)) if dn.size else None},
            "coverage": cov}


def metrics(run: Path, mode: str) -> dict:
    out_dir = find_output(run)
    out_loc = read_grid(out_dir)
    patch_loc = read_grid(Path(f"/work/p4n/patches/{mode}.tifxyz"))
    dy, dx, loc_info = locate_resume(out_loc, patch_loc)
    H, W = patch_loc.shape[:2]
    offc = np.zeros(out_loc.shape[:2], bool)
    offc[dy:dy + H, dx:dx + W] = patch_loc[..., 0] != -1
    new_mask = (out_loc[..., 0] != -1) & ~offc
    out_nat = prep.to_native(out_loc.copy())
    info = json.loads(Path(f"/work/p4n/patches/{mode}.tifxyz_prep.json").read_text())
    m = {"mode": mode, "run": str(run), "output": out_dir.name, "offset": [dy, dx], "locate": loc_info,
         "n_new_vertices": int(new_mask.sum()),
         "new_area_cm2": None}
    tris, _ = tri_mesh(np.where(new_mask[..., None], out_nat, -1.0), np.zeros(out_nat.shape[:2] + (2,)))
    if len(tris):
        m["new_area_cm2"] = float(0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]),
                                                        axis=1).sum() * (VOX_MM ** 2) / 100)
        z = out_nat[new_mask][:, 2]
        m["new_z_mm"] = [float(z.min() * VOX_MM), float(z.max() * VOX_MM)]
    m["official_unchanged"] = official_unchanged(out_loc, patch_loc, dy, dx)
    m["seam"] = seam(out_nat, new_mask, dy, dx, (H, W))
    m["self_intersection"] = selfcross(out_dir, run, new_mask, f"p4n_selfcross_{mode}")
    m["neighbour_winding"] = neighbour_winding(out_nat, new_mask, dy, dx, info["official_cols"])
    m["flattening"] = flattening(out_nat, new_mask) if new_mask.sum() > 50 else None
    if mode == "holdout":
        m["recovery"] = recovery(out_nat, new_mask, run)
    (run / "metrics.json").write_text(json.dumps(m, indent=1, default=float) + "\n")
    return m


if __name__ == "__main__":
    print(json.dumps(metrics(Path(sys.argv[1]), sys.argv[2]), indent=1, default=float))
