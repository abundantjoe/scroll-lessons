# Provenance: Project HERCULES | owner the owner | [id removed]
"""Geometry for the READCAL-2 bank candidate search (numbers only; no image is written or viewed).

Canvas convention (hercules.pipeline.canvas, official renderer at --scale 1): organizer canvas pixel P samples tifxyz
grid coordinate (P + 0.5) * s (s = meta scale, 0.05); xyz is bilinear over the 4 surrounding vertices (NaN if a
corner is invalid); a pixel is mesh-valid when its nearest vertex is valid.

Reference mapping 2.399 -> 9.362 um (as the D1 J builder / B0841-BANK / RCBANK-1): per axis
c9 = (c2 + 10) N9 / N2 - 10, exact separable area average of the 2.4 um pixels covered by each 9 um pixel.

Same papyrus (RULES.md CORR-RETRACE-RULE, fail-closed): trace T is SAME papyrus as window W if EITHER
 (a) nearest densified-vertex distances of W's points to T's 5 x 5 densified vertices, OR
 (b) point-to-triangulated-surface distances of W's points to T's densified surface (2 triangles per quad),
give >= 1000 W points within 2 vox AND count[0,1) >= 2 count[2,3).
W's points are the window's canvas samples at stride 4 px (= 4 vox spacing, the density of a 5 x 5 densified
20-vox mesh, the density the rule was defined on). Distance clearances (>= 128 vox) use point-to-surface distance.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'src'))
from hercules.geometry.tifxyz import densify, read_tifxyz, valid_mask  # noqa: E402

OFFSET_PX = 10.0
SP_MIN_WITHIN_2 = 1000
SP_RATIO = 2.0


# ------------------------------------------------------------------------------------------ canvas <-> grid
def canvas_shape(mesh) -> tuple[int, int]:
    H, W = mesh.points.shape[:2]
    su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
    return int(np.floor(H / sv + 0.5)), int(np.floor(W / su + 0.5))


def bilinear_points(P: np.ndarray, v: np.ndarray, u: np.ndarray) -> np.ndarray:
    """xyz at fractional grid (v, u), clamped to the grid (replicate border); NaN if a corner is invalid."""
    H, W = P.shape[:2]
    v = np.clip(v, 0, H - 1)
    u = np.clip(u, 0, W - 1)
    r0 = np.minimum(np.floor(v).astype(np.int64), max(H - 2, 0))
    c0 = np.minimum(np.floor(u).astype(np.int64), max(W - 2, 0))
    t = (v - r0)[..., None]
    s = (u - c0)[..., None]
    q00, q01, q10, q11 = P[r0, c0], P[r0, c0 + 1], P[r0 + 1, c0], P[r0 + 1, c0 + 1]
    out = (1 - t) * ((1 - s) * q00 + s * q01) + t * ((1 - s) * q10 + s * q11)
    return out


def mesh_points_nan(mesh) -> np.ndarray:
    P = np.asarray(mesh.points, np.float64).copy()
    P[~valid_mask(mesh.points)] = np.nan
    return P


def canvas_samples(mesh, stride: int = 4, rect=None):
    """Canvas samples (row, col) on a stride grid (optionally inside rect = (y0, x0, h, w)), their xyz (NaN where a
    bilinear corner is invalid) and mesh-validity (nearest vertex valid)."""
    P = mesh_points_nan(mesh)
    Hc, Wc = canvas_shape(mesh)
    su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
    if rect is None:
        ys, xs = np.arange(stride // 2, Hc, stride), np.arange(stride // 2, Wc, stride)
    else:
        y0, x0, h, w = rect
        ys = np.arange(y0 + stride // 2, min(Hc, y0 + h), stride)
        xs = np.arange(x0 + stride // 2, min(Wc, x0 + w), stride)
    yy, xx = np.meshgrid(ys, xs, indexing='ij')
    v, u = (yy + 0.5) * sv, (xx + 0.5) * su
    xyz = bilinear_points(P, v, u)
    H, W = P.shape[:2]
    rn = np.clip(np.floor(v + 0.5).astype(np.int64), 0, H - 1)
    cn = np.clip(np.floor(u + 0.5).astype(np.int64), 0, W - 1)
    mv = np.isfinite(P[rn, cn]).all(-1)
    return yy, xx, xyz, mv


def mesh_valid_canvas(mesh) -> np.ndarray:
    """(Hc, Wc) bool: nearest vertex valid (full resolution)."""
    P = mesh.points
    vm = valid_mask(P)
    Hc, Wc = canvas_shape(mesh)
    su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
    H, W = vm.shape
    rn = np.clip(np.floor((np.arange(Hc) + 0.5) * sv + 0.5).astype(np.int64), 0, H - 1)
    cn = np.clip(np.floor((np.arange(Wc) + 0.5) * su + 0.5).astype(np.int64), 0, W - 1)
    return vm[rn][:, cn]


# ------------------------------------------------------------------------------------------ reference mapping
def area_matrix(n9: int, n2: int, offset: float = OFFSET_PX) -> sp.csr_matrix:
    """(n9 x n2) row-normalised matrix: 9 um pixel i averages the 2.4 um pixels of [a, b) with
    a = (i - 0.5 + offset) n2/n9 - offset + 0.5, b = (i + 0.5 + offset) n2/n9 - offset + 0.5 (pixel j spans [j, j+1)
    in edge coordinates = [j - 0.5, j + 0.5) in centre coordinates), weights = overlap lengths."""
    r = n2 / n9
    rows, cols, vals = [], [], []
    for i in range(n9):
        a = (i - 0.5 + offset) * r - offset + 0.5
        b = (i + 0.5 + offset) * r - offset + 0.5
        j0, j1 = max(0, int(math.floor(a))), min(n2, int(math.ceil(b)))
        for j in range(j0, j1):
            w = min(b, j + 1) - max(a, j)
            if w > 0:
                rows.append(i)
                cols.append(j)
                vals.append(w)
    M = sp.csr_matrix((vals, (rows, cols)), shape=(n9, n2), dtype=np.float64)
    s = np.asarray(M.sum(1)).ravel()
    s[s == 0] = 1.0
    return sp.diags(1.0 / s) @ M


def map_ref_to_canvas(ref2: np.ndarray, hw9: tuple[int, int], block: int = 2048) -> np.ndarray:
    """Separable exact area average of a 2.4 um uint8 map onto the (H9, W9) canvas; float32 in 0..255."""
    H2, W2 = ref2.shape
    Ay = area_matrix(hw9[0], H2).astype(np.float32)          # (H9, H2)
    Axt = area_matrix(hw9[1], W2).astype(np.float32).tocsr()  # (W9, W2)
    tmp = np.zeros((hw9[0], W2), np.float32)
    for c in range(0, W2, block):
        tmp[:, c:c + block] = Ay @ ref2[:, c:c + block].astype(np.float32)
    out = np.zeros(hw9, np.float32)
    for r in range(0, hw9[1], block):
        out[:, r:r + block] = (Axt[r:r + block] @ tmp.T).T
    return out


# ------------------------------------------------------------------------------------------ surfaces
class Surface:
    """5 x 5 densified trace (NaN invalid) with its vertices, KD-tree and triangles (2 per valid quad)."""

    def __init__(self, mesh, k: int = 5, name: str = '', rect=None, pad_cells: int = 2):
        P = mesh_points_nan(mesh)
        self.r_off = self.c_off = 0
        if rect is not None:  # restrict to the grid cells under a canvas rect (y0, x0, h, w) (+ pad)
            y0, x0, h, w = rect
            su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
            H, W = P.shape[:2]
            r0 = max(0, int(math.floor((y0 + 0.5) * sv)) - pad_cells)
            r1 = min(H, int(math.ceil((y0 + h + 0.5) * sv)) + pad_cells + 1)
            c0 = max(0, int(math.floor((x0 + 0.5) * su)) - pad_cells)
            c1 = min(W, int(math.ceil((x0 + w + 0.5) * su)) + pad_cells + 1)
            P = P[r0:r1, c0:c1]
            self.r_off, self.c_off = r0, c0
        Pd = densify(np.where(np.isfinite(P), P, -1.0).astype(np.float32), k).astype(np.float64)
        Pd[~valid_mask(Pd)] = np.nan
        self.name, self.k, self.grid = name, k, Pd
        ok = np.isfinite(Pd).all(-1)
        self.vid = -np.ones(ok.shape, np.int64)
        self.vid[ok] = np.arange(int(ok.sum()))
        self.verts = Pd[ok]
        a, b, c, d = self.vid[:-1, :-1], self.vid[:-1, 1:], self.vid[1:, :-1], self.vid[1:, 1:]
        t1 = np.stack([a, b, c], -1).reshape(-1, 3)
        t2 = np.stack([b, d, c], -1).reshape(-1, 3)
        tris = np.concatenate([t1, t2])
        self.tris = tris[(tris >= 0).all(1)]
        # vertex -> incident triangles (CSR)
        n = self.verts.shape[0]
        vt = np.repeat(np.arange(self.tris.shape[0]), 3)
        vv = self.tris.ravel()
        o = np.argsort(vv, kind='stable')
        self.inc_ptr = np.searchsorted(vv[o], np.arange(n + 1))
        self.inc_tri = vt[o]
        self.tree = cKDTree(self.verts) if n else None
        self.bbox = (self.verts.min(0), self.verts.max(0)) if n else None


def closest_point_triangle(p, a, b, c):
    """Vectorised Ericson closest point on triangle abc to p; all (N, 3). Returns distances (N,)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    q = np.empty_like(p)
    done = np.zeros(p.shape[0], bool)

    def put(mask, val):
        m = mask & ~done
        q[m] = val[m] if val.ndim == 2 else val
        done[m] = True
    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide='ignore', invalid='ignore'):
        v = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        v3, w3 = vb * den, vc * den
        put(np.ones(p.shape[0], bool), a + v3[:, None] * ab + w3[:, None] * ac)
    return np.linalg.norm(p - q, axis=1)


def distances(points: np.ndarray, S: Surface, radius: float = 6.0, knn: int = 8):
    """(d_vertex, d_surface) for each point: nearest densified vertex distance and point-to-triangulated-surface
    distance, both inf beyond `radius` (the surface distance is evaluated on the triangles incident to the knn
    nearest vertices within radius + the vertex spacing bound, then capped). NaN points give inf."""
    n = points.shape[0]
    dv, ds = np.full(n, np.inf), np.full(n, np.inf)
    if S.tree is None or n == 0:
        return dv, ds
    ok = np.isfinite(points).all(1)
    lo, hi = S.bbox
    ok &= (points >= lo - radius - 8).all(1) & (points <= hi + radius + 8).all(1)
    idx_ok = np.nonzero(ok)[0]
    if idx_ok.size == 0:
        return dv, ds
    pts = points[idx_ok]
    # vertex spacing <= ~4-6 vox; search a bit wider so the closest triangle's vertices are found
    d, ii = S.tree.query(pts, k=knn, distance_upper_bound=radius + 8.0)
    dv[idx_ok] = np.where(d[:, 0] <= radius, d[:, 0], np.inf)
    best = np.full(pts.shape[0], np.inf)
    for j in range(knn):
        m = np.isfinite(d[:, j])
        if not m.any():
            continue
        vj = ii[m, j]
        starts, ends = S.inc_ptr[vj], S.inc_ptr[vj + 1]
        cnt = ends - starts
        rep = np.repeat(np.nonzero(m)[0], cnt)
        tot = int(cnt.sum())
        if tot == 0:
            continue
        first = np.repeat(np.cumsum(cnt) - cnt, cnt)
        tri_idx = S.inc_tri[np.repeat(starts, cnt) + (np.arange(tot) - first)]
        T = S.tris[tri_idx]
        dd = closest_point_triangle(pts[rep], S.verts[T[:, 0]], S.verts[T[:, 1]], S.verts[T[:, 2]])
        np.minimum.at(best, rep, dd)
    ds[idx_ok] = np.where(best <= radius, best, np.inf)
    return dv, ds


def bins(d: np.ndarray) -> tuple[int, int, int]:
    return int((d < 1).sum()), int(((d >= 1) & (d < 2)).sum()), int(((d >= 2) & (d < 3)).sum())


def same_rule(c: tuple[int, int, int]) -> bool:
    return (c[0] + c[1]) >= SP_MIN_WITHIN_2 and c[0] >= SP_RATIO * c[2]


def same_papyrus(dv: np.ndarray, ds: np.ndarray) -> dict:
    ca, cb = bins(dv), bins(ds)
    return {'counts_vertex': list(ca), 'counts_surface': list(cb), 'same_a': same_rule(ca), 'same_b': same_rule(cb),
            'same': same_rule(ca) or same_rule(cb)}


def min_surface_distance(points: np.ndarray, S: Surface, cap: float) -> np.ndarray:
    """Point-to-surface distance up to `cap` (inf beyond): KD-tree vertex distance minus the sampling bound gives
    candidates, the exact triangle distance decides (used for the >= 128 vox clearances)."""
    return distances(points, S, radius=cap, knn=8)[1]
