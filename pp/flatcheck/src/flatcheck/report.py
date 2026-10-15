"""Quality report of a tifxyz AS A FLATTENING: a tifxyz grid is itself a
flat parameterisation (every grid edge has flat length 1/scale). A quad is
isometric within tol if its four 3-D edges lie within +-tol of the nominal
step ("raw") or of step x s, s = sqrt(A3 / A2) one global area factor
("norm"). Fold-overs: triangles whose normal points against the
area-weighted mean normal of their 9 x 9 quad neighbourhood (the grid cannot
flip in (u, v); a fold is its flip equivalent). Optional square tiles of
side `tile` grid cells give per-tile scores. Memory: about 60 bytes per
vertex; process very large meshes by rows with `row_block`."""

from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

from .tifxyz import valid_mask

FOLD_WIN = 9


def grid_report(points: np.ndarray, step: float, *, tol: float = 0.05, tile: int | None = None,
                bar: float = 93.1) -> dict:
    p = np.asarray(points, dtype=np.float32)
    H, W = p.shape[:2]
    v = valid_mask(p)
    qv = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    nq = int(qv.sum())
    if nq == 0:
        raise ValueError("no valid quad")
    Lh = np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)
    Lv = np.linalg.norm(p[1:] - p[:-1], axis=-1)
    p00, p01, p10, p11 = p[:-1, :-1], p[:-1, 1:], p[1:, :-1], p[1:, 1:]
    n1 = np.cross(p00 - p10, p01 - p10)
    n2 = np.cross(p01 - p10, p11 - p10)
    a1 = 0.5 * np.linalg.norm(n1, axis=-1)
    a2 = 0.5 * np.linalg.norm(n2, axis=-1)
    A3 = float(np.where(qv, a1 + a2, 0).sum(dtype=np.float64))
    s = math.sqrt(A3 / (nq * step * step))
    ns = np.where(qv[..., None], n1 + n2, 0).astype(np.float32)
    mean_n = np.stack([ndimage.uniform_filter(ns[..., k], FOLD_WIN, mode="constant") for k in range(3)], -1)
    fold = qv & (((n1 * mean_n).sum(-1) < 0) | ((n2 * mean_n).sum(-1) < 0))
    nfold = int((qv & ((n1 * mean_n).sum(-1) < 0)).sum() + (qv & ((n2 * mean_n).sum(-1) < 0)).sum())
    del n1, n2, mean_n, ns, p00, p01, p10, p11

    def ok(ref, t):
        oh = np.abs(Lh / ref - 1) <= t
        ov = np.abs(Lv / ref - 1) <= t
        return oh[:-1] & oh[1:] & ov[:, :-1] & ov[:, 1:] & qv

    ok_raw, ok_norm = ok(step, tol), ok(step * s, tol)
    worst = np.maximum.reduce([np.abs(Lh[:-1] / step - 1), np.abs(Lh[1:] / step - 1),
                               np.abs(Lv[:, :-1] / step - 1), np.abs(Lv[:, 1:] / step - 1)])[qv]
    out = {"grid_shape": [H, W], "nominal_step": step, "n_valid_quads": nq, "area_3d_vox2": A3,
           "area_scale_factor": s, "tol": tol,
           "pct_quads_within_tol_raw": 100.0 * ok_raw.sum() / nq,
           "pct_quads_within_tol_norm": 100.0 * ok_norm.sum() / nq,
           "pct_quads_within_1pct_raw": 100.0 * ok(step, 0.01).sum() / nq,
           "quad_worst_edge_dev_pctl": {str(k): float(np.percentile(worst, k)) for k in (50, 90, 95, 99, 99.9)},
           "fold_triangles": nfold, "quads_with_fold": int(fold.sum()),
           "passes_bar_norm": 100.0 * ok_norm.sum() / nq >= bar, "bar": bar}
    if tile:
        ti = (np.arange(H - 1) // tile)[:, None]
        tj = (np.arange(W - 1) // tile)[None, :]
        nc = (W - 1 + tile - 1) // tile
        tid = ti * nc + tj
        nt = int(tid.max()) + 1
        cq = np.bincount(tid[qv], minlength=nt)
        cn = np.bincount(tid[ok_norm], minlength=nt)
        cf = np.bincount(tid[fold], minlength=nt)
        tiles = [{"row": int(k // nc), "col": int(k % nc), "n_quads": int(cq[k]),
                  "pct_within_tol_norm": float(100.0 * cn[k] / cq[k]), "quads_with_fold": int(cf[k])}
                 for k in range(nt) if cq[k]]
        out["tiles"] = tiles
        out["tiles_summary"] = {"tile_cells": tile, "n_tiles": len(tiles),
                                "n_tiles_ge_bar": int(sum(t["pct_within_tol_norm"] >= bar for t in tiles))}
    return out
