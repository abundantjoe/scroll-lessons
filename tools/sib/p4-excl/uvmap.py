"""Exact nearest-surface correspondence: for query points, the closest point on a tifxyz triangulated surface,
its distance and its UV (fractional grid row, col). Coordinates only.

closest_bary: Ericson closest-point-on-triangle with barycentric coordinates (all Voronoi regions).
Candidate triangles: quads incident to the k nearest vertices. The result is certified exact when
d <= d_k - Lc (d_k = distance to the k-th nearest vertex): any triangle holding a closer point has a
vertex within d + Lc < d_k, i.e. among the k nearest. Uncertified points are recomputed with a ball
query of radius d + Lc (exact by the same covering bound).
"""
import numpy as np
from surfdist import Surface  # noqa: F401


def closest_bary(q, a, b, c):
    q, a, b, c = (np.asarray(t, np.float64) for t in (q, a, b, c))
    ab = b - a; ac = c - a; ap = q - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = q - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = q - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    n = len(q); W = np.zeros((n, 3)); done = np.zeros(n, bool)

    def put(m, w):
        m = m & ~done
        W[m] = w[m] if np.ndim(w) == 2 else w
        done[:] = done | m
    with np.errstate(divide='ignore', invalid='ignore'):
        put((d1 <= 0) & (d2 <= 0), np.array([1.0, 0, 0]))
        put((d3 >= 0) & (d4 <= d3), np.array([0, 1.0, 0]))
        put((d6 >= 0) & (d5 <= d6), np.array([0, 0, 1.0]))
        v = d1 / (d1 - d3); put((vc <= 0) & (d1 >= 0) & (d3 <= 0), np.stack([1 - v, v, 0 * v], 1))
        w = d2 / (d2 - d6); put((vb <= 0) & (d2 >= 0) & (d6 <= 0), np.stack([1 - w, 0 * w, w], 1))
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6)); put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), np.stack([0 * w, 1 - w, w], 1))
        den = va + vb + vc; v = vb / den; w = vc / den
        put(np.ones(n, bool), np.stack([1 - v - w, v, w], 1))
    bad = ~np.isfinite(W).all(1)          # fully degenerate triangle: fall back to nearest vertex
    if bad.any():
        dd = np.stack([np.linalg.norm(q - t, axis=1) for t in (a, b, c)], 1)
        W[bad] = np.eye(3)[dd[bad].argmin(1)]
    p = W[:, :1] * a + W[:, 1:2] * b + W[:, 2:] * c
    return np.linalg.norm(q - p, axis=1), W


def _eval_pairs(S, Q, pid, i, j):
    """distance and uv for (point, quad) pairs; returns per point min."""
    g = S.grid
    A = g[i, j]; B = g[i, j + 1]; C = g[i + 1, j]; E = g[i + 1, j + 1]; X = Q[pid]
    d1, w1 = closest_bary(X, A, B, E)
    d2, w2 = closest_bary(X, A, E, C)
    fi = i.astype(np.float64); fj = j.astype(np.float64)
    # uv of a,b,c,e = (i,j), (i,j+1), (i+1,j), (i+1,j+1)
    u1 = np.stack([fi + w1[:, 2], fj + w1[:, 1] + w1[:, 2]], 1)          # (a,b,e)
    u2 = np.stack([fi + w2[:, 1] + w2[:, 2], fj + w2[:, 1]], 1)          # (a,e,c)
    use2 = d2 < d1
    d = np.where(use2, d2, d1); uv = np.where(use2[:, None], u2, u1)
    o = np.lexsort((d, pid)); pid, d, uv = pid[o], d[o], uv[o]
    first = np.r_[True, pid[1:] != pid[:-1]]
    return pid[first], d[first], uv[first]


def _quads_of(S, verts, pid):
    i = (S.ij[verts, 0][:, None] + np.array([-1, -1, 0, 0])).ravel()
    j = (S.ij[verts, 1][:, None] + np.array([-1, 0, -1, 0])).ravel()
    p = np.repeat(pid, 4)
    ok = (i >= 0) & (j >= 0) & (i < S.H - 1) & (j < S.W - 1)
    i, j, p = i[ok], j[ok], p[ok]
    ok = S.quad_valid[i, j]
    return p[ok], i[ok], j[ok]


def nearest_uv(S, Q, tol, k=8):
    """Exact distance (inf if > tol) and UV (fractional grid row, col) of the closest surface point."""
    Q = np.asarray(Q, np.float64); n = len(Q)
    D = np.full(n, np.inf); UV = np.full((n, 2), np.nan)
    dk, vk = S.tree.query(Q, k=k, workers=-1)
    cand = np.nonzero(dk[:, 0] - S.Lc <= tol)[0]
    if cand.size == 0:
        return D, UV, 0
    pid = np.repeat(np.arange(len(cand)), k)
    p, i, j = _quads_of(S, vk[cand].ravel(), pid)
    if p.size:
        pp, d, uv = _eval_pairs(S, Q[cand], p, i, j)
        D[cand[pp]] = d; UV[cand[pp]] = uv
    # certificate; recompute the rest exactly with a ball query
    dmin = np.minimum(D[cand], dk[cand, 0])
    unc = cand[~(dmin <= dk[cand, -1] - S.Lc)]
    unc = unc[np.minimum(D[unc], dk[unc, 0]) - 0 <= tol + S.Lc]
    for s0 in range(0, len(unc), 20000):
        u = unc[s0:s0 + 20000]
        r = np.minimum(D[u], dk[u, 0]) + S.Lc
        lists = S.tree.query_ball_point(Q[u], r, workers=-1)
        cnt = np.fromiter((len(x) for x in lists), np.int64, len(lists))
        if cnt.sum() == 0:
            continue
        verts = np.concatenate([np.asarray(x, np.int64) for x in lists if len(x)])
        p, i, j = _quads_of(S, verts, np.repeat(np.arange(len(u)), cnt))
        if p.size:
            pp, d, uv = _eval_pairs(S, Q[u], p, i, j)
            better = d < D[u[pp]]
            D[u[pp][better]] = d[better]; UV[u[pp][better]] = uv[better]
    # isolated valid vertices (in no valid quad) are point primitives: the nearest vertex beats every
    # triangle only in that case; its uv is its own grid index
    iso = cand[dk[cand, 0] < D[cand]]
    D[iso] = dk[iso, 0]; UV[iso] = S.ij[vk[iso, 0]].astype(np.float64)
    far = D > tol
    D[far] = np.inf; UV[far] = np.nan
    return D, UV, int(len(unc))
