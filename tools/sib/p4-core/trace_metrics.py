# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-7 item 3: validation metrics for a traced core window (tifxyz).

Geometry and numbers only. Nothing here opens, renders or describes an image,
tile or CT voxel; ``fibre_coherence`` takes a 2-D array handed to it by the
caller (the tests use synthetic arrays only).

Conventions
-----------
* A mesh is a tifxyz grid ``points[r, c] = (x, y, z)`` (float, voxels of
  VOXEL_UM = 2.4 um); invalid vertices are (-1, -1, -1) or NaN.
* Triangulation: two triangles per quad with four valid corners, diagonal
  p10-p01, exactly as FLAT-1/FLAT-2 ``flatlib.grid_to_mesh`` (imported from
  the verbatim copy ``flatlib_flat2.py``).
* The roll axis is a callable ``umb(z) -> (ux, uy)`` (``umb_from_polyline``
  builds one from an (n, 3) polyline of (x, y, z)).
* Every public function returns a JSON-ready dict (python floats / ints /
  lists / None only) with a ``pass`` field (True / False, or None for
  report-only metrics).

Metrics (RULES.md DECL-P4-7 item 3)
-----------------------------------
(a) ``self_intersection``          no mesh self-intersection.
(b) ``winding_continuity``         winding-number continuity with w010.
(c) ``neighbour_distance_ratio``   point-to-surface distance to the neighbour
                                   winding >= 60 % of the local spacing.
(d) ``flattening_distortion``      area / angle error with FLAT-2 flatteners.
(e) ``fibre_coherence``            H/V fibre-orientation coherence >= the
                                   w010 strip's median.
``run_all`` bundles them.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
from scipy import ndimage, sparse
from scipy.sparse import csgraph
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flatlib_flat2 as fl  # noqa: E402  (verbatim FLAT-2 flatlib)

VOXEL_UM = 2.4
VOX2_PER_CM2 = 1.0 / (VOXEL_UM * 1e-4) ** 2
TWO_PI = 2.0 * math.pi


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _j(x):
    """Convert numpy scalars / arrays / nested containers to JSON-ready."""
    if isinstance(x, dict):
        return {str(k): _j(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_j(v) for v in x]
    if isinstance(x, np.ndarray):
        return _j(x.tolist())
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    return x


def _pct(a, qs):
    a = np.asarray(a, dtype=np.float64)
    a = a[np.isfinite(a)]
    return {f"p{q:g}": (float(np.percentile(a, q)) if a.size else None) for q in qs}


def valid_mask(points: np.ndarray) -> np.ndarray:
    return fl.valid_mask(points)


def umb_from_polyline(poly: np.ndarray) -> Callable:
    """Callable umb(z) -> (ux, uy) by linear interpolation of an (n, 3)
    polyline of (x, y, z) (sorted by z; constant extrapolation)."""
    p = np.asarray(poly, dtype=np.float64)
    p = p[np.argsort(p[:, 2])]

    def umb(z):
        z = np.asarray(z, dtype=np.float64)
        return np.interp(z, p[:, 2], p[:, 0]), np.interp(z, p[:, 2], p[:, 1])
    return umb


def _wrap(a):
    return (a + math.pi) % TWO_PI - math.pi


def _mesh(points):
    return fl.grid_to_mesh(np.asarray(points, dtype=np.float64))


def _dot(a, b):
    return np.einsum("ij,ij->i", a, b)


# ---------------------------------------------------------------------------
# (a) self-intersection
# ---------------------------------------------------------------------------

def _interval(p, d):
    """Moller (1997) interval of one triangle on the intersection line.
    p: (n, 3) projections of the vertices on the line direction axis,
    d: (n, 3) signed distances of the vertices to the other plane.
    Returns (lo, hi) (n,) and coplanar flag (n,)."""
    d0, d1, d2 = d[:, 0], d[:, 1], d[:, 2]
    k = np.select([d0 * d1 > 0, d0 * d2 > 0, (d1 * d2 > 0) | (d0 != 0), d1 != 0, d2 != 0],
                  [2, 1, 0, 1, 2], default=-1)
    cop = k < 0
    k = np.where(cop, 0, k)
    j1 = (k + 1) % 3
    j2 = (k + 2) % 3
    ar = np.arange(p.shape[0])
    pk, pj1, pj2 = p[ar, k], p[ar, j1], p[ar, j2]
    dk, dj1, dj2 = d[ar, k], d[ar, j1], d[ar, j2]
    with np.errstate(invalid="ignore", divide="ignore"):
        t1 = pk + (pj1 - pk) * dk / (dk - dj1)
        t2 = pk + (pj2 - pk) * dk / (dk - dj2)
    return np.minimum(t1, t2), np.maximum(t1, t2), cop


def _seg_seg_2d(p1, p2, q1, q2):
    """Closed 2-D segment intersection, vectorised (n, 2) each."""
    def orient(a, b, c):
        return (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])

    def onseg(a, b, c):
        return ((np.minimum(a[:, 0], b[:, 0]) <= c[:, 0]) & (c[:, 0] <= np.maximum(a[:, 0], b[:, 0]))
                & (np.minimum(a[:, 1], b[:, 1]) <= c[:, 1]) & (c[:, 1] <= np.maximum(a[:, 1], b[:, 1])))
    o1, o2, o3, o4 = orient(p1, p2, q1), orient(p1, p2, q2), orient(q1, q2, p1), orient(q1, q2, p2)
    gen = (o1 * o2 < 0) & (o3 * o4 < 0)
    col = ((o1 == 0) & onseg(p1, p2, q1)) | ((o2 == 0) & onseg(p1, p2, q2)) | \
          ((o3 == 0) & onseg(q1, q2, p1)) | ((o4 == 0) & onseg(q1, q2, p2))
    return gen | col


def _pt_in_tri_2d(p, a, b, c):
    def cr(u, v, w):
        return (v[:, 0] - u[:, 0]) * (w[:, 1] - u[:, 1]) - (v[:, 1] - u[:, 1]) * (w[:, 0] - u[:, 0])
    d1, d2, d3 = cr(a, b, p), cr(b, c, p), cr(c, a, p)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    return ~(neg & pos)


def _coplanar_tri_tri(A, B, N):
    """A, B (n, 3, 3) coplanar triangles, N (n, 3) plane normal."""
    ax = np.argmax(np.abs(N), axis=1)
    keep = np.array([[1, 2], [0, 2], [0, 1]])[ax]  # drop dominant axis
    ar = np.arange(A.shape[0])
    A2 = np.stack([A[ar, :, keep[:, 0]], A[ar, :, keep[:, 1]]], -1)
    B2 = np.stack([B[ar, :, keep[:, 0]], B[ar, :, keep[:, 1]]], -1)
    hit = np.zeros(A.shape[0], bool)
    for i in range(3):
        for j in range(3):
            hit |= _seg_seg_2d(A2[:, i], A2[:, (i + 1) % 3], B2[:, j], B2[:, (j + 1) % 3])
    hit |= _pt_in_tri_2d(A2[:, 0], B2[:, 0], B2[:, 1], B2[:, 2])
    hit |= _pt_in_tri_2d(B2[:, 0], A2[:, 0], A2[:, 1], A2[:, 2])
    return hit


def tri_tri_intersect(A: np.ndarray, B: np.ndarray, rel_eps: float = 1e-12) -> np.ndarray:
    """Exact-in-floating-point Moller (1997) triangle-triangle test,
    vectorised. A, B: (n, 3, 3). Touching (closed sets) counts as
    intersecting. Distances below rel_eps * |N| * extent are snapped to 0
    (as Moller's EPSILON), which only matters for (near-)coplanar input."""
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    n = A.shape[0]
    out = np.zeros(n, bool)
    if n == 0:
        return out
    ext = np.maximum(np.abs(A).max(axis=(1, 2)), np.abs(B).max(axis=(1, 2))) + 1.0
    N1 = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0])
    du = np.einsum("nij,nj->ni", B - A[:, None, 0], N1)
    du[np.abs(du) < (rel_eps * np.linalg.norm(N1, axis=1) * ext)[:, None]] = 0.0
    sep1 = ((du > 0).all(1)) | ((du < 0).all(1))
    N2 = np.cross(B[:, 1] - B[:, 0], B[:, 2] - B[:, 0])
    dv = np.einsum("nij,nj->ni", A - B[:, None, 0], N2)
    dv[np.abs(dv) < (rel_eps * np.linalg.norm(N2, axis=1) * ext)[:, None]] = 0.0
    sep2 = ((dv > 0).all(1)) | ((dv < 0).all(1))
    cand = ~(sep1 | sep2)
    idx = np.nonzero(cand)[0]
    if idx.size == 0:
        return out
    A, B, du, dv, N1, N2 = A[idx], B[idx], du[idx], dv[idx], N1[idx], N2[idx]
    coplanar = (du == 0).all(1)
    D = np.cross(N1, N2)
    ax = np.argmax(np.abs(D), axis=1)
    ar = np.arange(idx.size)
    pa = A[ar, :, ax]
    pb = B[ar, :, ax]
    lo1, hi1, c1 = _interval(pa, dv)
    lo2, hi2, c2 = _interval(pb, du)
    res = ~((hi1 < lo2) | (hi2 < lo1))
    cop = coplanar | c1 | c2
    res = np.where(cop, False, res)
    if cop.any():
        ci = np.nonzero(cop)[0]
        res[ci] = _coplanar_tri_tri(A[ci], B[ci], N1[ci])
    out[idx] = res
    return out


def self_intersection(points: np.ndarray, *, chunk: int = 200_000, max_report: int = 50,
                      voxel_um: float = VOXEL_UM) -> dict:
    """(a) Self-intersections of the triangulated tifxyz grid.

    Broadphase: cKDTree over triangle centroids, candidate pairs with
    centroid distance <= R_i + R_j (R = centroid-vertex bounding radius),
    then AABB overlap. Pairs sharing a vertex (grid-adjacent triangles) are
    excluded, as required. Narrowphase: vectorised Moller tri-tri test.
    pass iff 0 intersecting pairs.
    """
    t0 = time.perf_counter()
    m = _mesh(points)
    V, F = m.V, m.F
    nT = F.shape[0]
    T = V[F]  # (m, 3, 3)
    cen = T.mean(1)
    R = np.linalg.norm(T - cen[:, None], axis=2).max(1)
    lo, hi = T.min(1), T.max(1)
    area = float(fl.tri_areas_3d(V, F).sum())
    Rmax = float(R.max()) if nT else 0.0
    tree = cKDTree(cen) if nT else None
    hits_i, hits_j = [], []
    n_cand = 0
    for i0 in range(0, nT, chunk):
        i1 = min(nT, i0 + chunk)
        sub = cKDTree(cen[i0:i1])
        pr = sub.sparse_distance_matrix(tree, 2.0 * Rmax + 1e-9, output_type="ndarray")
        I = pr["i"].astype(np.int64) + i0
        J = pr["j"].astype(np.int64)
        keep = J > I
        I, J = I[keep], J[keep]
        d = np.sqrt(pr["v"][keep])
        keep = d <= R[I] + R[J] + 1e-9
        I, J = I[keep], J[keep]
        keep = np.all((lo[I] <= hi[J]) & (lo[J] <= hi[I]), axis=1)
        I, J = I[keep], J[keep]
        share = np.zeros(I.size, bool)
        FI, FJ = F[I], F[J]
        for a in range(3):
            for b in range(3):
                share |= FI[:, a] == FJ[:, b]
        I, J = I[~share], J[~share]
        n_cand += int(I.size)
        if I.size:
            hit = tri_tri_intersect(T[I], T[J])
            hits_i.append(I[hit])
            hits_j.append(J[hit])
    HI = np.concatenate(hits_i) if hits_i else np.zeros(0, np.int64)
    HJ = np.concatenate(hits_j) if hits_j else np.zeros(0, np.int64)
    area_cm2 = area / (1.0 / (voxel_um * 1e-4) ** 2)
    n = int(HI.size)
    tri_in = np.unique(np.concatenate([HI, HJ])) if n else np.zeros(0, np.int64)
    rep = [[m.tri_quad[i].tolist(), m.tri_quad[j].tolist()] for i, j in zip(HI[:max_report], HJ[:max_report])]
    return _j({
        "metric": "a_self_intersection",
        "n_triangles": nT, "n_candidate_pairs_nonadjacent": n_cand,
        "n_intersecting_pairs": n, "n_triangles_involved": int(tri_in.size),
        "area_cm2": area_cm2,
        "pairs_per_cm2": (n / area_cm2) if area_cm2 > 0 else None,
        "example_pairs_quad_rc": rep,
        "seconds": time.perf_counter() - t0,
        "pass": n == 0,
    })


# ---------------------------------------------------------------------------
# (b) winding angle / continuity
# ---------------------------------------------------------------------------

def winding_angle(points: np.ndarray, umb: Callable) -> tuple[np.ndarray, np.ndarray]:
    """Wrapped angle theta in (-pi, pi] and radius around the umbilicus in
    the vertex's own z plane. (H, W) arrays, NaN at invalid vertices."""
    p = np.asarray(points, dtype=np.float64)
    ok = valid_mask(p)
    th = np.full(p.shape[:2], np.nan)
    rr = np.full(p.shape[:2], np.nan)
    ux, uy = umb(p[..., 2][ok])
    dx, dy = p[..., 0][ok] - ux, p[..., 1][ok] - uy
    th[ok] = np.arctan2(dy, dx)
    rr[ok] = np.hypot(dx, dy)
    return th, rr


def winding_coordinate(points: np.ndarray, umb: Callable, seed: tuple[int, int] | None = None) -> dict:
    """Continuous winding coordinate w = theta / 2 pi, unwrapped by a
    breadth-first flood fill over 4-connected valid grid vertices: each
    vertex gets its BFS parent's value plus the wrapped angle difference.
    Each connected component is unwrapped from its own seed (``seed`` for
    the component that contains it, else the first valid vertex in raster
    order); the seed keeps its principal value theta / 2 pi in (-1/2, 1/2].
    Returns dict(w (H, W) NaN invalid, theta, radius, n_components,
    labels (H, W) component id or -1)."""
    th, rr = winding_angle(points, umb)
    ok = np.isfinite(th)
    H, W = ok.shape
    idx = np.full((H, W), -1, np.int64)
    idx[ok] = np.arange(int(ok.sum()))
    n = int(ok.sum())
    rows, cols = [], []
    for a, b in ((idx[:, :-1], idx[:, 1:]), (idx[:-1, :], idx[1:, :])):
        e = (a >= 0) & (b >= 0)
        rows.append(a[e])
        cols.append(b[e])
    r_ = np.concatenate(rows)
    c_ = np.concatenate(cols)
    G = sparse.coo_matrix((np.ones(r_.size), (r_, c_)), shape=(n, n)).tocsr()
    ncomp, lab = csgraph.connected_components(G, directed=False)
    thv = th[ok]
    wv = np.full(n, np.nan)
    seeds = {}
    if seed is not None and idx[seed] >= 0:
        seeds[lab[idx[seed]]] = int(idx[seed])
    for comp in range(ncomp):
        s = seeds.get(comp, int(np.argmax(lab == comp)))
        order, pred = csgraph.breadth_first_order(G, s, directed=False, return_predecessors=True)
        wv[s] = thv[s] / TWO_PI
        o = order[1:]
        pr = pred[o]
        dth = _wrap(thv[o] - thv[pr]) / TWO_PI
        wl = wv.tolist()
        ol, pl, dl = o.tolist(), pr.tolist(), dth.tolist()
        for v, p_, d in zip(ol, pl, dl):
            wl[v] = wl[p_] + d
        wv = np.asarray(wl)
    w = np.full((H, W), np.nan)
    w[ok] = wv
    labels = np.full((H, W), -1, np.int64)
    labels[ok] = lab
    return {"w": w, "theta": th, "radius": rr, "n_components": int(ncomp), "labels": labels}


class _RayCaster:
    """Horizontal rays from the umbilicus against a triangulated tifxyz mesh.

    Candidate triangles come from a cKDTree over triangle centroids mapped
    to (Rs cos theta, Rs sin theta, z) (Rs = median vertex radius), queried
    with the largest mapped (theta, z) bounding-box diagonal of any triangle,
    so every triangle whose angular / z extent contains the ray is a
    candidate. Exact test: vectorised Moller-Trumbore (closed triangles,
    u, v >= -eps), t > 0.
    """

    def __init__(self, points: np.ndarray, umb: Callable, wcoord: np.ndarray | None = None):
        self.m = _mesh(points)
        self.umb = umb
        V, F = self.m.V, self.m.F
        ux, uy = umb(V[:, 2])
        self.theta = np.arctan2(V[:, 1] - uy, V[:, 0] - ux)
        rad = np.hypot(V[:, 0] - ux, V[:, 1] - uy)
        self.Rs = float(np.median(rad)) if rad.size else 1.0
        th0 = self.theta[F[:, 0]]
        rel = _wrap(self.theta[F] - th0[:, None])  # (m, 3)
        thc = th0 + rel.mean(1)
        zc = V[F][:, :, 2].mean(1)
        span = np.hypot(self.Rs * (rel.max(1) - rel.min(1)), np.ptp(V[F][:, :, 2], axis=1))
        self.rq = float(span.max()) * 1.001 + 1e-6 if span.size else 0.0
        self.tree = cKDTree(np.stack([self.Rs * np.cos(thc), self.Rs * np.sin(thc), zc], 1)) if F.shape[0] else None
        self.w_vertex = None
        if wcoord is not None:
            wv = np.full(V.shape[0], np.nan)
            ok = self.m.index >= 0
            wv[self.m.index[ok]] = wcoord[ok]
            self.w_vertex = wv

    def cast(self, theta: np.ndarray, z: np.ndarray, *, eps: float = 1e-9, chunk: int = 100_000):
        """Returns (ray, tri, t, w_hit) arrays of all hits (t > 0)."""
        out = ([], [], [], [])
        if self.tree is None or theta.size == 0:
            e = np.zeros(0)
            return e.astype(np.int64), e.astype(np.int64), e, e
        V, F = self.m.V, self.m.F
        for i0 in range(0, theta.size, chunk):
            th = theta[i0:i0 + chunk]
            zz = z[i0:i0 + chunk]
            q = np.stack([self.Rs * np.cos(th), self.Rs * np.sin(th), zz], 1)
            pr = cKDTree(q).sparse_distance_matrix(self.tree, self.rq, output_type="ndarray")
            I = pr["i"].astype(np.int64)
            J = pr["j"].astype(np.int64)
            ux, uy = self.umb(zz[I])
            O = np.stack([ux, uy, zz[I]], 1)
            D = np.stack([np.cos(th[I]), np.sin(th[I]), np.zeros(I.size)], 1)
            a, b, c = V[F[J, 0]], V[F[J, 1]], V[F[J, 2]]
            e1, e2 = b - a, c - a
            pv = np.cross(D, e2)
            det = _dot(e1, pv)
            good = np.abs(det) > 1e-12 * np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1)
            with np.errstate(invalid="ignore", divide="ignore"):
                inv = 1.0 / det
                tv = O - a
                u = _dot(tv, pv) * inv
                qv = np.cross(tv, e1)
                v = _dot(D, qv) * inv
                t = _dot(e2, qv) * inv
            hit = good & (u >= -eps) & (v >= -eps) & (u + v <= 1 + eps) & (t > 0)
            I, J, t = I[hit], J[hit], t[hit]
            if self.w_vertex is not None:
                v0 = F[J, 0]
                wh = self.w_vertex[v0] + _wrap(th[I] - self.theta[v0]) / TWO_PI
            else:
                wh = np.full(I.size, np.nan)
            out[0].append(I + i0)
            out[1].append(J)
            out[2].append(t)
            out[3].append(wh)
        return tuple(np.concatenate(x) for x in out)


def _clusters(ray, t, tol):
    """Sort hits by (ray, t) and merge hits of one ray closer than tol (a
    ray through an edge / vertex hits several triangles at the same t).
    Returns sorted (ray, t, order, first-of-cluster mask)."""
    o = np.lexsort((t, ray))
    r, tt = ray[o], t[o]
    new = np.ones(r.size, bool)
    if r.size > 1:
        new[1:] = (r[1:] != r[:-1]) | (tt[1:] - tt[:-1] > tol)
    return r, tt, o, new


def winding_continuity(trace: np.ndarray, w010: np.ndarray, umb: Callable, expected_offset: int | None = None, *,
                       spacing: float | np.ndarray | None = None, hit_tol: float = 2.0,
                       max_report: int = 50) -> dict:
    """(b) Winding-number continuity of a trace with the w010 mesh.

    For every valid trace vertex v (angle theta_v, radius r_v, plane z_v):
      1. cast the horizontal ray from umb(z_v) at theta_v against the w010
         mesh (exact ray-triangle intersection, not nearest vertices);
         R_w = innermost w010 hit, W_w = w010's unwrapped winding coordinate
         at that hit; the next distinct w010 hit (if any) gives the local
         spacing s_v = R_w2 - R_w;
      2. cast the same ray against the trace itself and count the distinct
         trace sheets n_between with r_v + hit_tol < t < R_w - hit_tol;
      3. steps inward k_v = max(1 + n_between, round((R_w - r_v) / s_v)),
         i.e. the count of sheets between the vertex and w010, where the
         radial term also counts windings the trace does not contain
         (a trace placed two windings in, or hopping to the next winding);
         offset_v = -k_v (w010 = 0, w009 = -1, ...).
    ``spacing``: scalar or per-vertex (H, W) array overriding s_v;
    default: local w010 turn gap where the ray hits w010 twice, else the
    median of those gaps; if w010 never covers a ray twice, the median of
    (R_w - r_v) / (1 + n_between) over the trace (reported as
    ``spacing_source``).

    Continuity: with A_v = W_w - k_v (w010-anchored winding coordinate of
    v) and W_t(v) the trace's own flood-fill-unwrapped winding coordinate,
    for every 4-neighbour grid pair (u, v) with both rays hitting w010,
    jump iff |(A_v - A_u) - (W_t(v) - W_t(u))| >= 0.5 turn, i.e. the
    w010-anchored winding coordinate changes by a turn more than the
    geometric (angular) expectation. Equivalently the per-vertex phase
    O_v = A_v - W_t(v) (an integer on a consistent trace) changes.

    pass iff n_jumps == 0, every trace vertex whose ray hits w010 lies
    inward of it (frac_inside_w010 == 1), at least one ray hits w010, and
    (if expected_offset is given) offset_mode == expected_offset.
    """
    t0 = time.perf_counter()
    tp = np.asarray(trace, dtype=np.float64)
    wt = winding_coordinate(tp, umb)
    ww = winding_coordinate(w010, umb)
    ok = np.isfinite(wt["w"])
    rr, cc = np.nonzero(ok)
    th = wt["theta"][ok]
    rt = wt["radius"][ok]
    zt = tp[..., 2][ok]
    N = th.size
    # 1. w010 hits
    rc_w = _RayCaster(w010, umb, ww["w"])
    ray, tri, t, wh = rc_w.cast(th, zt)
    r_s, t_s, o_s, new = _clusters(ray, t, hit_tol)
    wh_s = wh[o_s]
    # rank of each distinct-hit cluster along its ray (0 = innermost)
    cs = np.nonzero(new)[0]
    cr = r_s[cs]
    ray_first = np.ones(cs.size, bool)
    ray_first[1:] = cr[1:] != cr[:-1]
    rank = np.arange(cs.size) - np.maximum.accumulate(np.where(ray_first, np.arange(cs.size), 0))
    Rw = np.full(N, np.nan)
    Ww = np.full(N, np.nan)
    Rw2 = np.full(N, np.nan)
    Rw[cr[rank == 0]] = t_s[cs[rank == 0]]
    Ww[cr[rank == 0]] = wh_s[cs[rank == 0]]
    Rw2[cr[rank == 1]] = t_s[cs[rank == 1]]
    has = np.isfinite(Rw)
    gap_w = Rw2 - Rw
    # 2. trace self hits between the vertex and w010
    rc_t = _RayCaster(tp, umb)
    ray2, _, t2, _ = rc_t.cast(th, zt)
    lim_lo = rt[ray2] + hit_tol
    lim_hi = np.where(has[ray2], Rw[ray2] - hit_tol, -np.inf)
    sel = (t2 > lim_lo) & (t2 < lim_hi)
    rb, tb, _, newb = _clusters(ray2[sel], t2[sel], hit_tol)
    n_between = np.bincount(rb[newb], minlength=N) if rb.size else np.zeros(N, np.int64)
    k_count = 1 + n_between
    gap = Rw - rt
    # spacing
    if spacing is not None:
        s_arr = np.asarray(spacing, dtype=np.float64)
        s_v = np.full(N, float(s_arr)) if s_arr.ndim == 0 else s_arr[ok]
        source = "given"
    elif np.isfinite(gap_w).any():
        med = float(np.nanmedian(gap_w))
        s_v = np.where(np.isfinite(gap_w), gap_w, med)
        source = "w010_turn_gap_local_else_median"
    else:
        med = float(np.nanmedian(gap[has] / k_count[has])) if has.any() else math.nan
        s_v = np.full(N, med)
        source = "trace_gap_over_count_median (w010 covers no ray twice)"
    with np.errstate(invalid="ignore"):
        k_rad = np.rint(gap / s_v)
    k = np.where(has, np.maximum(k_count, np.nan_to_num(k_rad, nan=1.0)), np.nan)
    offset = -k
    A = Ww - k
    Wt = wt["w"][ok]
    phase = A - Wt
    # grid adjacency
    vid = np.full(ok.shape, -1, np.int64)
    vid[ok] = np.arange(N)
    pa, pb = [], []
    for a, b in ((vid[:, :-1], vid[:, 1:]), (vid[:-1, :], vid[1:, :])):
        e = (a >= 0) & (b >= 0)
        pa.append(a[e])
        pb.append(b[e])
    pa = np.concatenate(pa)
    pb = np.concatenate(pb)
    both = has[pa] & has[pb]
    pa, pb = pa[both], pb[both]
    dev = (A[pb] - A[pa]) - (Wt[pb] - Wt[pa])
    jump = np.abs(dev) >= 0.5
    inside = rt[has] < Rw[has]
    offs = offset[has].astype(np.int64)
    if offs.size:
        vals, cnt = np.unique(offs, return_counts=True)
        mode = int(vals[np.argmax(cnt)])
        mode_frac = float(cnt.max() / offs.size)
        hist = {str(int(v)): int(c) for v, c in zip(vals, cnt)}
        vc, cc_ = np.unique(-k_count[has], return_counts=True)
        mode_count_only = int(vc[np.argmax(cc_)])
        ph = np.rint(phase[has]).astype(np.int64)
        pv, pc = np.unique(ph, return_counts=True)
        ph_mode, ph_frac = int(pv[np.argmax(pc)]), float(pc.max() / ph.size)
        ph_resid = float(np.max(np.abs(phase[has] - np.rint(phase[has]))))
    else:
        mode = mode_frac = mode_count_only = ph_mode = ph_frac = ph_resid = None
        hist = {}
    jl = [[int(rr[a]), int(cc[a]), int(rr[b]), int(cc[b])] for a, b in zip(pa[jump][:max_report], pb[jump][:max_report])]
    n_jumps = int(jump.sum())
    frac_inside = float(inside.mean()) if inside.size else None
    passed = bool(has.any() and n_jumps == 0 and frac_inside == 1.0
                  and (expected_offset is None or mode == expected_offset))
    return _j({
        "metric": "b_winding_continuity",
        "n_trace_vertices": N, "n_rays_hit_w010": int(has.sum()),
        "frac_rays_hit_w010": float(has.mean()) if N else None,
        "frac_inside_w010": frac_inside, "n_outside_w010": int((~inside).sum()),
        "spacing_source": source, "spacing_median_vox": float(np.nanmedian(s_v)) if N else None,
        "gap_over_spacing_pct": _pct((gap / s_v)[has], (1, 50, 99)),
        "offset_mode": mode, "offset_mode_frac": mode_frac, "offset_hist": hist,
        "offset_count_only_mode": mode_count_only,
        "expected_offset": expected_offset,
        "frac_equal_expected": (float(np.mean(offs == expected_offset)) if (expected_offset is not None and offs.size) else None),
        "phase_mode": ph_mode, "phase_mode_frac": ph_frac, "phase_max_abs_residual": ph_resid,
        "n_neighbour_pairs": int(pa.size), "n_jumps": n_jumps,
        "frac_continuous_pairs": float(1.0 - jump.mean()) if pa.size else None,
        "jump_pairs_rc": jl,
        "w010_components": ww["n_components"], "trace_components": wt["n_components"],
        "seconds": time.perf_counter() - t0,
        "pass": passed,
    })


def median_radial_gap(inner: np.ndarray, outer: np.ndarray, umb: Callable, hit_tol: float = 2.0) -> dict:
    """Median radial gap between two labelled windings (e.g. w010 and w011):
    rays from the umbilicus through every inner vertex against the outer
    mesh (innermost hit beyond the vertex). Used as the independent local
    spacing of metric (c)."""
    wi = winding_angle(inner, umb)
    ok = np.isfinite(wi[0])
    th, r = wi[0][ok], wi[1][ok]
    z = np.asarray(inner, dtype=np.float64)[..., 2][ok]
    ray, _, t, _ = _RayCaster(outer, umb).cast(th, z)
    sel = t > r[ray] + hit_tol
    g = np.full(th.size, np.inf)
    np.minimum.at(g, ray[sel], t[sel] - r[ray[sel]])
    g = g[np.isfinite(g)]
    return _j({"median_gap_vox": float(np.median(g)) if g.size else None, "n_rays": int(g.size),
               **{k: v for k, v in _pct(g, (25, 75)).items()}})


# ---------------------------------------------------------------------------
# (c) point-to-surface distance to the neighbour winding
# ---------------------------------------------------------------------------

def point_triangle_distance(P: np.ndarray, A: np.ndarray, B: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Exact Euclidean distance point -> closed triangle (Ericson, Real-Time
    Collision Detection 5.1.5), vectorised over rows."""
    ab, ac, ap = B - A, C - A, P - A
    d1, d2 = _dot(ab, ap), _dot(ac, ap)
    bp = P - B
    d3, d4 = _dot(ab, bp), _dot(ac, bp)
    cp = P - C
    d5, d6 = _dot(ab, cp), _dot(ac, cp)
    vc = d1 * d4 - d3 * d2
    vb = d5 * d2 - d1 * d6
    va = d3 * d6 - d5 * d4
    with np.errstate(invalid="ignore", divide="ignore"):
        v_ab = d1 / (d1 - d3)
        w_ac = d2 / (d2 - d6)
        w_bc = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        den = 1.0 / (va + vb + vc)
        vi, wi = vb * den, vc * den
    conds = [
        (d1 <= 0) & (d2 <= 0),
        (d3 >= 0) & (d4 <= d3),
        (vc <= 0) & (d1 >= 0) & (d3 <= 0),
        (d6 >= 0) & (d5 <= d6),
        (vb <= 0) & (d2 >= 0) & (d6 <= 0),
        (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0),
    ]
    choices = [A, B, A + v_ab[:, None] * ab, C, A + w_ac[:, None] * ac, B + w_bc[:, None] * (C - B)]
    Q = A + vi[:, None] * ab + wi[:, None] * ac
    done = np.zeros(P.shape[0], bool)
    for cnd, ch in zip(conds, choices):
        use = cnd & ~done
        Q = np.where(use[:, None], ch, Q)
        done |= use
    return np.linalg.norm(P - Q, axis=1)


def point_to_mesh_distance(P: np.ndarray, points: np.ndarray, *, k: int = 16, chunk: int = 20_000) -> np.ndarray:
    """Distance from points P (n, 3) to the triangulated tifxyz surface.
    Candidates: all triangles incident to the k nearest mesh vertices
    (cKDTree); exact point-triangle distance, minimum over candidates. On a
    regular grid mesh the closest triangle is incident to one of the few
    nearest vertices; k = 16 is a wide margin (documented approximation of
    the candidate set, the distance itself is exact)."""
    m = _mesh(points)
    V, F = m.V, m.F
    nV = V.shape[0]
    fr = F.ravel()
    o = np.argsort(fr, kind="stable")
    cnt = np.bincount(fr, minlength=nV)
    maxdeg = int(cnt.max())
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    vt = np.full((nV, maxdeg), -1, np.int64)
    pos = np.arange(fr.size) - np.repeat(start, cnt)
    vt[fr[o], pos] = o // 3
    tree = cKDTree(V)
    kk = min(k, nV)
    out = np.empty(P.shape[0])
    for i0 in range(0, P.shape[0], chunk):
        p = P[i0:i0 + chunk]
        _, nn = tree.query(p, kk)
        nn = nn.reshape(p.shape[0], kk)
        cand = vt[nn].reshape(p.shape[0], -1)
        rows = np.repeat(np.arange(p.shape[0]), cand.shape[1])
        tri = cand.ravel()
        good = tri >= 0
        rows, tri = rows[good], tri[good]
        d = point_triangle_distance(p[rows], V[F[tri, 0]], V[F[tri, 1]], V[F[tri, 2]])
        best = np.full(p.shape[0], np.inf)
        np.minimum.at(best, rows, d)
        out[i0:i0 + chunk] = best
    return out


def neighbour_distance_ratio(trace: np.ndarray, neighbour: np.ndarray, local_spacing=None, *,
                             umb: Callable | None = None, spacing_pair: tuple | None = None,
                             threshold: float = 0.6, k: int = 16) -> dict:
    """(c) Point-to-surface distance d from each valid trace vertex to the
    neighbour winding's triangulated surface, divided by the local spacing.

    local_spacing: scalar, or (H, W) array per trace vertex, or None. If
    None, it is computed as the median radial gap between TWO labelled
    reference windings ``spacing_pair = (inner, outer)`` (e.g. w010, w011)
    with ``umb`` (``median_radial_gap``). It is deliberately NOT computed
    from the trace-neighbour gap itself: that would make d / spacing ~ 1
    by construction and hide a trace that sits too close.

    RULES.md DECL-P4-7: "point-to-surface distance to the neighbour winding
    >= 60 % of the local spacing". Read as: for every vertex. Declared
    pass criterion: p5 of d / spacing >= threshold (0.6). Also reported:
    fraction of vertices with ratio >= 0.6, the minimum and p1, and
    ``pass_all_vertices`` (min >= 0.6) so the orchestrator can apply the
    strict reading. No lower bar is introduced.
    """
    t0 = time.perf_counter()
    tp = np.asarray(trace, dtype=np.float64)
    ok = valid_mask(tp)
    P = tp[ok]
    src = "given"
    if local_spacing is None:
        if spacing_pair is None or umb is None:
            raise ValueError("local_spacing=None needs spacing_pair=(inner, outer) and umb")
        g = median_radial_gap(spacing_pair[0], spacing_pair[1], umb)
        s = np.full(P.shape[0], g["median_gap_vox"])
        src = "median_radial_gap(spacing_pair)"
    else:
        a = np.asarray(local_spacing, dtype=np.float64)
        s = np.full(P.shape[0], float(a)) if a.ndim == 0 else a[ok]
    d = point_to_mesh_distance(P, neighbour, k=k)
    ratio = d / s
    fin = np.isfinite(ratio)
    pc = _pct(ratio, (1, 5, 50))
    p5 = pc["p5"]
    return _j({
        "metric": "c_neighbour_distance_ratio",
        "n_vertices": int(P.shape[0]), "spacing_source": src,
        "spacing_median_vox": float(np.median(s)) if s.size else None,
        "distance_vox_pct": _pct(d, (1, 5, 50)),
        "ratio_p1": pc["p1"], "ratio_p5": p5, "ratio_p50": pc["p50"],
        "ratio_min": float(ratio[fin].min()) if fin.any() else None,
        "threshold": threshold,
        "frac_ratio_ge_threshold": float(np.mean(ratio[fin] >= threshold)) if fin.any() else None,
        "pct_ratio_ge_threshold": float(100 * np.mean(ratio[fin] >= threshold)) if fin.any() else None,
        "pass_all_vertices": bool(fin.any() and ratio[fin].min() >= threshold),
        "pass_rule": "p5(d/spacing) >= 0.6",
        "seconds": time.perf_counter() - t0,
        "pass": bool(p5 is not None and p5 >= threshold),
    })


# ---------------------------------------------------------------------------
# (d) flattening distortion (FLAT-2 flatlib, verbatim copy)
# ---------------------------------------------------------------------------

def _have_igl() -> bool:
    try:
        import igl  # noqa: F401
        return True
    except Exception:
        return False


def _arap_scipy(V, F, UV0, iters=100):
    """Fallback only if libigl is absent: local-global ARAP (Liu et al.
    2008), cotangent weights, one vertex pinned. NOT FLAT-2 tooling; the
    result is labelled as such."""
    from scipy.sparse.linalg import factorized
    n = V.shape[0]
    T = V[F]
    e1 = T[:, 1] - T[:, 0]
    e2 = T[:, 2] - T[:, 0]
    l1 = np.linalg.norm(e1, axis=1)
    x = e1 / l1[:, None]
    nrm = np.cross(e1, e2)
    y = np.cross(nrm / np.linalg.norm(nrm, axis=1)[:, None], x)
    X = np.zeros((F.shape[0], 3, 2))
    X[:, 1] = np.stack([l1, np.zeros_like(l1)], 1)
    X[:, 2] = np.stack([_dot(e2, x), _dot(e2, y)], 1)
    cot = np.zeros((F.shape[0], 3))
    for i in range(3):
        a, b = X[:, (i + 1) % 3] - X[:, i], X[:, (i + 2) % 3] - X[:, i]
        cot[:, i] = (a * b).sum(1) / np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
    rows, cols, vals = [], [], []
    for i in range(3):
        j, kx = (i + 1) % 3, (i + 2) % 3
        w = 0.5 * cot[:, i]  # edge (j, k)
        for a_, b_ in ((j, kx), (kx, j)):
            rows += [F[:, a_], F[:, a_]]
            cols += [F[:, a_], F[:, b_]]
            vals += [w, -w]
    L = sparse.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    L = L.tolil()
    L[0, :] = 0
    L[0, 0] = 1.0
    solve = factorized(L.tocsc())
    U = UV0[:, :2].copy()
    for _ in range(iters):
        Ut = U[F]
        S = np.zeros((F.shape[0], 2, 2))
        for i in range(3):
            j, kx = (i + 1) % 3, (i + 2) % 3
            S += cot[:, i, None, None] * np.einsum("ni,nj->nij", Ut[:, j] - Ut[:, kx], X[:, j] - X[:, kx])
        Uu, _, Vt = np.linalg.svd(S)
        R = Uu @ Vt
        neg = np.linalg.det(R) < 0
        Uu[neg, :, 1] *= -1
        R = Uu @ Vt
        b = np.zeros((n, 2))
        for i in range(3):
            j, kx = (i + 1) % 3, (i + 2) % 3
            r = 0.5 * cot[:, i, None] * np.einsum("nij,nj->ni", R, X[:, j] - X[:, kx])
            np.add.at(b, F[:, j], r)
            np.add.at(b, F[:, kx], -r)
        b[0] = UV0[0, :2]
        U = np.stack([solve(b[:, 0]), solve(b[:, 1])], 1)
    return U


def flattening_distortion(points: np.ndarray, *, method: str = "slim", max_iter: int = 200, quads=None,
                          thresholds: dict | None = None) -> dict:
    """(d) Flatten with FLAT-2 flatlib (``flatten_slim`` symmetric
    Dirichlet, or ``flatten_arap``) from the flip-free grid initialisation
    ``grid_init_uv`` (step = median 3-D edge length) and evaluate with
    flatlib ``evaluate`` (global area normalisation, FLAT-1 convention).

    Reported: area error = area-weighted mean |log(area ratio)| and % of
    triangles with area ratio within +-5 %; angle error = mean / p99 of
    |flat angle - 3-D angle| (deg); FLAT-1 main metric % quads with all
    edges within +-5 %; flipped triangles.

    DECL-P4-7 names the metric but gives no threshold, so ``pass`` is None
    (report only) unless ``thresholds`` is given, e.g.
    {"area_abs_log_max": 0.02, "angle_mean_deg_max": 1.0}.
    If libigl is not installed, a scipy ARAP fallback is used and
    ``flattener`` says so (it is NOT the FLAT-2 flattener).
    """
    t0 = time.perf_counter()
    p = np.asarray(points, dtype=np.float64)
    m = fl.grid_to_mesh(p, quads)
    ok = valid_mask(p)
    eh = np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    ev = np.linalg.norm(p[1:] - p[:-1], axis=-1)[ok[1:] & ok[:-1]]
    step = float(np.median(np.concatenate([eh, ev])))
    UV0 = fl.grid_init_uv(m, step)
    info = {}
    if _have_igl():
        if method == "slim":
            UV, info = fl.flatten_slim(m.V, m.F, UV0, max_iter=max_iter)
            flattener = "flatlib_flat2.flatten_slim (libigl SLIM, symmetric Dirichlet)"
        elif method == "arap":
            UV, info = fl.flatten_arap(m.V, m.F, UV0, max_iter=max_iter)
            flattener = "flatlib_flat2.flatten_arap (libigl ARAP)"
        else:
            raise ValueError(method)
    else:
        UV = _arap_scipy(m.V, m.F, UV0, iters=min(max_iter, 100))
        flattener = "FALLBACK scipy ARAP (libigl missing; not FLAT-2)"
    uv = fl.uv_to_grid(m, UV, p.shape[:2])
    ev_ = fl.evaluate(p, uv, m.quads)
    out = {
        "metric": "d_flattening_distortion", "flattener": flattener, "method": method,
        "n_triangles": ev_["n_triangles"],
        "area_error_weighted_mean_abs_log": ev_["area_ratio"]["weighted_mean_abs_log"],
        "area_pct_tri_within_5pct": ev_["area_ratio"]["pct_tri_within_5pct"],
        "area_ratio_p1": ev_["area_ratio"]["p1"], "area_ratio_p99": ev_["area_ratio"]["p99"],
        "angle_error_mean_deg": ev_["angle_abs_err_deg"]["mean"],
        "angle_error_p99_deg": ev_["angle_abs_err_deg"]["p99"],
        "pct_quads_within_5pct": ev_["pct_quads_within_5pct"],
        "flipped_triangles": ev_["flipped_triangles"],
        "iterations": info.get("iterations"),
        "seconds": time.perf_counter() - t0,
        "pass": None,
    }
    if thresholds:
        conds = []
        if "area_abs_log_max" in thresholds:
            conds.append(out["area_error_weighted_mean_abs_log"] <= thresholds["area_abs_log_max"])
        if "angle_mean_deg_max" in thresholds:
            conds.append(out["angle_error_mean_deg"] <= thresholds["angle_mean_deg_max"])
        out["thresholds"] = thresholds
        out["pass"] = bool(all(conds)) and out["flipped_triangles"] == 0
    return _j(out)


# ---------------------------------------------------------------------------
# (e) fibre-orientation coherence
# ---------------------------------------------------------------------------

def orientation_windows(texture: np.ndarray, *, window: int = 64, grad_sigma: float = 1.0,
                        band: tuple[float, float] = (0.03, 0.25), mask: np.ndarray | None = None,
                        min_valid_frac: float = 0.9) -> dict:
    """Per-window orientation statistics of a 2-D array (numbers only).

    Windows: non-overlapping ``window`` x ``window`` px blocks (the
    remainder at the right / bottom edge is dropped); a window is used if
    >= min_valid_frac of its pixels are finite and inside ``mask``
    (invalid pixels are set to the window mean).

    1. Structure tensor (spec): Gaussian-derivative gradients (sigma
       ``grad_sigma`` px), J = sum [gx^2, gx gy; gx gy, gy^2] per window,
       coherence c = (l1 - l2) / (l1 + l2), dominant gradient angle
       phi = 0.5 atan2(2 Jxy, Jxx - Jyy) (fibres run perpendicular to it),
       hv2 = c |cos 2 phi| (coherence-weighted H/V alignment).
       Limitation: for CROSSED vertical + horizontal fibres the two
       orientations cancel in this 2nd-order tensor (c -> 0, like
       isotropic noise), and a per-pixel gradient angle is mixed by the
       additive superposition, so neither separates a papyrus recto with
       both fibre layers from isotropic texture.
    2. Primary H/V score hv4 (fourfold spectral moment): mean-removed,
       Hann-tapered window, power spectrum P(k) over the radial band
       ``band`` (cycles / px), hv4 = sum P cos(4 psi_k) / sum P, psi_k the
       wave-vector angle. Power is additive over uncorrelated fibre
       layers, so hv4 -> +1 for horizontal and/or vertical fibres, ~0 for
       isotropic texture, -1 for fibres on the diagonals.
    """
    I = np.asarray(texture, dtype=np.float64)
    fin = np.isfinite(I)
    if mask is not None:
        fin &= np.asarray(mask, bool)
    fill = float(np.mean(I[fin])) if fin.any() else 0.0
    I0 = np.where(fin, I, fill)
    gy = ndimage.gaussian_filter(I0, grad_sigma, order=(1, 0))
    gx = ndimage.gaussian_filter(I0, grad_sigma, order=(0, 1))
    H, W = I.shape
    nh, nw = H // window, W // window

    def blocks(a):
        return a[:nh * window, :nw * window].reshape(nh, window, nw, window).transpose(0, 2, 1, 3).reshape(nh * nw, window, window)
    fb = blocks(fin.astype(np.float64))
    vf = fb.mean((1, 2))
    Jxx = (blocks(gx * gx) * fb).sum((1, 2))
    Jyy = (blocks(gy * gy) * fb).sum((1, 2))
    Jxy = (blocks(gx * gy) * fb).sum((1, 2))
    tr = Jxx + Jyy
    disc = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        c = disc / tr
    phi = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    hv2 = c * np.abs(np.cos(2 * phi))
    # spectral fourfold moment
    Ib = blocks(I0)
    cnt = np.maximum(fb.sum((1, 2)), 1.0)
    mu = (Ib * fb).sum((1, 2)) / cnt
    Ib = np.where(fb > 0, Ib - mu[:, None, None], 0.0)
    hann = np.hanning(window)
    P = np.abs(np.fft.fft2(Ib * np.outer(hann, hann)[None])) ** 2
    ky = np.fft.fftfreq(window)[:, None]
    kx = np.fft.fftfreq(window)[None, :]
    kr = np.hypot(kx, ky)
    psi = np.arctan2(ky, kx)
    inb = (kr >= band[0]) & (kr <= band[1])
    w4 = np.where(inb, np.cos(4 * psi), 0.0)
    Pb = (P * inb[None]).sum((1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        hv4 = (P * w4[None]).sum((1, 2)) / Pb
    use = (vf >= min_valid_frac) & (tr > 0) & (Pb > 0)
    return {"coherence": c[use], "phi_grad_rad": phi[use], "hv2": hv2[use], "hv4": hv4[use],
            "n_windows": int(use.sum()), "window": window, "grad_sigma": grad_sigma, "band": band}


def fibre_coherence(texture: np.ndarray, reference: np.ndarray | None = None, *,
                    reference_median: float | None = None, window: int = 64, grad_sigma: float = 1.0,
                    band: tuple[float, float] = (0.03, 0.25), mask: np.ndarray | None = None, reference_mask: np.ndarray | None = None) -> dict:
    """(e) H/V fibre-orientation coherence of a (recto) texture array,
    median over windows of hv4 (see ``orientation_windows``), compared with
    the reference (w010 strip) median computed with the SAME parameters
    from ``reference`` (or given as ``reference_median``).
    pass iff median_hv4(trace) >= median_hv4(reference) (rule text:
    ">= the w010 strip's median"). Window 64 px default; at the FLAT tile
    scale of 2.4 um/px that is ~154 um, i.e. several fibre widths; band
    (0.03, 0.25) cycles/px = periods of 4-33 px (~10-80 um).
    """
    st = orientation_windows(texture, window=window, grad_sigma=grad_sigma, band=band, mask=mask)
    med = float(np.median(st["hv4"])) if st["n_windows"] else math.nan
    out = {
        "metric": "e_fibre_coherence", "window_px": window, "grad_sigma_px": grad_sigma,
        "band_cycles_per_px": list(band), "primary_score": "hv4 (fourfold spectral moment)",
        "n_windows": st["n_windows"],
        "hv4_median": med, "hv4_pct": _pct(st["hv4"], (5, 25, 75, 95)),
        "hv2_median": float(np.median(st["hv2"])) if st["n_windows"] else None,
        "coherence_median": float(np.median(st["coherence"])) if st["n_windows"] else None,
    }
    ref = reference_median
    if reference is not None:
        rs = orientation_windows(reference, window=window, grad_sigma=grad_sigma, band=band, mask=reference_mask)
        ref = float(np.median(rs["hv4"])) if rs["n_windows"] else math.nan
        out["reference_n_windows"] = rs["n_windows"]
        out["reference_hv2_median"] = float(np.median(rs["hv2"])) if rs["n_windows"] else None
    out["reference_hv4_median"] = ref
    out["pass"] = (None if ref is None else bool(np.isfinite(med) and np.isfinite(ref) and med >= ref))
    return _j(out)


# ---------------------------------------------------------------------------
# bundle
# ---------------------------------------------------------------------------

def run_all(trace: np.ndarray, w010: np.ndarray, umb: Callable, *, neighbour: np.ndarray | None = None,
            local_spacing=None, spacing_pair=None, expected_offset: int | None = None,
            trace_texture: np.ndarray | None = None, reference_texture: np.ndarray | None = None,
            reference_median: float | None = None, flatten_method: str = "slim",
            flatten_thresholds: dict | None = None, fibre_window: int = 64) -> dict:
    """All five DECL-P4-7 item 3 metrics. ``neighbour`` defaults to w010.
    Returns {"a": ..., "b": ..., "c": ..., "d": ..., "e": ...,
    "passed": [...], "failed": [...], "report_only": [...], "all_pass"}."""
    nb = w010 if neighbour is None else neighbour
    res = {
        "a": self_intersection(trace),
        "b": winding_continuity(trace, w010, umb, expected_offset),
        "c": neighbour_distance_ratio(trace, nb, local_spacing, umb=umb, spacing_pair=spacing_pair),
        "d": flattening_distortion(trace, method=flatten_method, thresholds=flatten_thresholds),
    }
    if trace_texture is not None:
        res["e"] = fibre_coherence(trace_texture, reference_texture, reference_median=reference_median,
                                   window=fibre_window)
    else:
        res["e"] = {"metric": "e_fibre_coherence", "pass": None, "note": "no texture given"}
    passed = [k for k, v in res.items() if v.get("pass") is True]
    failed = [k for k, v in res.items() if v.get("pass") is False]
    report_only = [k for k, v in res.items() if v.get("pass") is None]
    res.update({"passed": passed, "failed": failed, "report_only": report_only,
                "all_pass": (len(failed) == 0 and len(report_only) == 0)})
    return _j(res)
