# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-22 metrics: the re-traced patch P (official outside holes + re-trace inside) vs the official mesh on P.
Same four measures as P4-N, each computed identically for both surfaces; native 2.4 um voxels.

Adoption rule (fixed before any trace of P exists):
  ADOPT iff  self-intersection pairs touching P == 0 (re-trace)
        and  seam median normal residual (re-trace hole borders) <= official baseline median (same measure on
             official vertices inside P)
        and  neighbour-winding frac >= 0.6 (re-trace, over P) >= official frac over P
        and  flattening (SLIM on P): pct quads within +-5 % >= official and mean angle error <= official.
EXCL = 40 L2 grid steps (7.7 mm along the sheet) for the same-winding exclusion: at the 1.8-2.5 mm radii of
c14-c19 one winding is about 60-80 grid steps, so P4-N's 60 would drop true neighbours.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "ext")); sys.path.insert(0, str(HERE.parent))
import metrics as M  # noqa: E402
import prep  # noqa: E402

EXCL = 40


def clearance_grid(g: np.ndarray) -> np.ndarray:
    """Per-vertex clearance to other windings within the same grid (fail-closed point-to-surface)."""
    v = g[..., 0] != -1
    R, C = np.nonzero(v)
    rc = np.stack([R, C], 1).astype(float)
    ids = np.full(g.shape[:2] + (2,), np.nan); ids[R, C] = rc
    tris, trc = M.tri_mesh(g, ids)
    old = M.EXCL
    M.EXCL = EXCL
    try:
        cl = M.clearance(g[v], rc, g[v], rc, tris, trc)
    finally:
        M.EXCL = old
    out = np.full(g.shape[:2], np.nan); out[R, C] = cl
    return out


def tile_ids(shape, rows_off, cols_off):
    """Strip-a tile (row, col) index per grid vertex from official native row/col arrays."""
    return (rows_off[:, None] / prep.T_GRID).astype(int), (cols_off[None, :] / prep.T_GRID).astype(int)


def spacing_by_tile(cl_off, inP, tr, tc):
    sp = {}
    for a in np.unique(tr):
        for b in np.unique(tc):
            m = inP & (tr == a) & (tc == b) & np.isfinite(cl_off)
            if m.sum() > 50:
                sp[(int(a), int(b))] = float(np.median(cl_off[m]))
    return sp


def ratio_from(cl, sp, tr, tc):
    s = np.vectorize(lambda a, b: sp.get((int(a), int(b)), np.nan))(np.broadcast_to(tr, cl.shape),
                                                                     np.broadcast_to(tc, cl.shape))
    return cl / s


def seam_general(g, newm, fixedm):
    """For each new vertex and each of the 4 grid directions whose next 3 vertices are fixed (official): residual
    of the new vertex vs the quadratic continuation of those 3, normal component."""
    n = M.normals(np.where(fixedm[..., None], g, -1.0))
    res = []
    H, W = g.shape[:2]
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        R, C = np.nonzero(newm)
        r1, c1, r2, c2, r3, c3 = R + dr, C + dc, R + 2 * dr, C + 2 * dc, R + 3 * dr, C + 3 * dc
        ok = (r3 >= 0) & (r3 < H) & (c3 >= 0) & (c3 < W)
        R, C, r1, c1, r2, c2, r3, c3 = (x[ok] for x in (R, C, r1, c1, r2, c2, r3, c3))
        ok = fixedm[r1, c1] & fixedm[r2, c2] & fixedm[r3, c3]
        R, C, r1, c1, r2, c2, r3, c3 = (x[ok] for x in (R, C, r1, c1, r2, c2, r3, c3))
        pred = 3 * g[r1, c1] - 3 * g[r2, c2] + g[r3, c3]
        nn = n[r1, c1]
        bad = ~np.isfinite(nn).all(1)                     # first fixed vertex borders the hole: use the next one
        nn[bad] = n[r2, c2][bad]
        fin = np.isfinite(nn).all(1)
        res.append(np.abs(((g[R, C] - pred) * nn).sum(1))[fin])
    return np.concatenate(res) if res else np.array([])


def flat(g, mask):
    import flatlib as FL
    gg = np.where(mask[..., None], g, -1.0)
    qm = FL.quad_mask(gg)
    mesh = FL.grid_to_mesh(gg, qm)
    e = np.linalg.norm(gg[:, 1:] - gg[:, :-1], axis=-1)[(gg[:, 1:, 0] != -1) & (gg[:, :-1, 0] != -1)]
    UV, info = FL.flatten_slim(mesh.V, mesh.F, FL.grid_init_uv(mesh, float(np.median(e))))
    uv = FL.uv_to_grid(mesh, UV, gg.shape[:2])
    ev = FL.evaluate(gg, uv, qm)
    return {"pct_quads_within_5pct": ev["pct_quads_within_5pct"], "angle_err_mean_deg": ev["angle_abs_err_deg"]["mean"],
            "angle_err_p99_deg": ev["angle_abs_err_deg"]["p99"], "area_abs_log_mean": ev["area_ratio"]["weighted_mean_abs_log"],
            "flipped": ev["flipped_triangles"], "n_quads": ev["n_quads"], "slim": info}, uv


def st(x):
    x = x[np.isfinite(x)]
    return {"n": int(x.size), "median": float(np.median(x)) if x.size else None,
            "p90": float(np.percentile(x, 90)) if x.size else None}
