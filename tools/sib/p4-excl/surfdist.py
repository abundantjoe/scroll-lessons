"""Exact point-to-triangulated-surface distance for tifxyz meshes (CORR-RETRACE-RULE form (b)).

Geometry only: x/y/z coordinate grids, never pixels.

Triangulation: every grid quad whose 4 corners are valid (x, y, z >= 0 and finite) is split into
triangles (a, b, e) and (a, e, c), a=(i,j) b=(i,j+1) c=(i+1,j) e=(i+1,j+1). Valid vertices that are
in no valid quad are kept as point primitives (distance = vertex distance).

Exactness argument (no densification needed):
  L = max edge length over all triangles, Lc = L / sqrt(3). Every point p of a triangle T lies
  within Lc of some vertex of T (the vertex covering radius of a triangle is its circumradius
  R = l / (2 sin t) <= l / sqrt(3) when acute, t >= 60 deg being the angle opposite the longest
  edge l, and l / 2 when right or obtuse). For a query q, d_v = distance to the nearest vertex
  (KD-tree, exact). The closest surface point p lies in some triangle T with |q-p| = d_s <= d_v,
  and some vertex of T is within d_s + Lc of q. So the exact distance is the min over triangles
  incident to the vertices inside B(q, r) for any r >= d_s + Lc, and d_s >= d_v - Lc. For the
  minimum over a SET of points (a tile) with upper bound ub, only points with d_v - Lc <= ub can
  attain it, and r = ub + Lc suffices for them.
"""
import numpy as np
from scipy.spatial import cKDTree


def closest_point_dist(q, a, b, c):
    """Exact Euclidean distance from points q (n,3) to triangles (a,b,c) (n,3 each), float64.
    Ericson, Real-Time Collision Detection 5.1.5, vectorised; degenerate triangles handled by
    also taking the minimum with the three edge-segment distances."""
    q, a, b, c = (np.asarray(t, np.float64) for t in (q, a, b, c))
    ab = b - a; ac = c - a; ap = q - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = q - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = q - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc
    with np.errstate(divide='ignore', invalid='ignore'):
        v = vb / den; w = vc / den
    res = a + ab * v[:, None] + ac * w[:, None]          # interior (face region)
    out = np.full(len(q), np.inf)
    face = (va >= 0) & (vb >= 0) & (vc >= 0) & (den > 0)
    out[face] = np.linalg.norm(q[face] - res[face], axis=1)
    # boundary: exact distance to the 3 edge segments (covers vertex and edge regions exactly)
    for s, e in ((a, b), (b, c), (c, a)):
        out = np.minimum(out, seg_dist(q, s, e))
    return out


def seg_dist(q, s, e):
    d = e - s
    dd = (d * d).sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.where(dd > 0, ((q - s) * d).sum(1) / dd, 0.0)
    t = np.clip(t, 0.0, 1.0)
    return np.linalg.norm(q - (s + d * t[:, None]), axis=1)


class Surface:
    """Grid mesh (H, W, 3) float32 with invalid cells NaN (or any coordinate < 0)."""

    def __init__(self, grid):
        g = np.asarray(grid, np.float32)
        valid = np.isfinite(g).all(-1) & (g >= 0).all(-1)
        self.H, self.W = valid.shape
        self.valid = valid
        qv = valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, :-1] & valid[1:, 1:]
        self.quad_valid = qv
        ii, jj = np.nonzero(valid)
        self.vid = np.full(valid.shape, -1, np.int64)
        self.vid[ii, jj] = np.arange(len(ii))
        self.V = g[ii, jj].astype(np.float64)
        self.ij = np.stack([ii, jj], 1).astype(np.int32)
        self.grid = g
        # max edge over triangles (4 sides + the a-e diagonal)
        L = 0.0
        a = g[:-1, :-1]; b = g[:-1, 1:]; c = g[1:, :-1]; e = g[1:, 1:]
        for u, w in ((a, b), (a, c), (b, e), (c, e), (a, e)):
            dl = np.linalg.norm((u - w)[qv].astype(np.float64), axis=1)
            if dl.size:
                L = max(L, float(dl.max()))
        self.L = L
        self.Lc = L / np.sqrt(3.0)
        self.tree = cKDTree(self.V)
        self.n_quads = int(qv.sum())

    def _tri_dist_for_vertices(self, q, verts):
        """exact min distance from q (3,) to all triangles incident to vertex ids `verts`."""
        i = self.ij[verts, 0][:, None] + np.array([-1, -1, 0, 0])[None]
        j = self.ij[verts, 1][:, None] + np.array([-1, 0, -1, 0])[None]
        i = i.ravel(); j = j.ravel()
        ok = (i >= 0) & (j >= 0) & (i < self.H - 1) & (j < self.W - 1)
        i, j = i[ok], j[ok]
        ok = self.quad_valid[i, j]
        i, j = i[ok], j[ok]
        if i.size == 0:
            return np.inf
        k = np.unique(i.astype(np.int64) * self.W + j)
        i, j = k // self.W, k % self.W
        g = self.grid
        A = g[i, j]; B = g[i, j + 1]; C = g[i + 1, j]; E = g[i + 1, j + 1]
        Q = np.broadcast_to(q, A.shape)
        d = np.minimum(closest_point_dist(Q, A, B, E), closest_point_dist(Q, A, E, C))
        return float(d.min())

    def _batch_dist(self, Q, r):
        """For points Q (m,3) and radii r (m,): min over the vertex distance and all triangles
        incident to vertices within r. Exact where the true distance d satisfies d + Lc <= r."""
        lists = self.tree.query_ball_point(Q, r, workers=4)
        cnt = np.fromiter((len(x) for x in lists), np.int64, len(lists))
        out = np.full(len(Q), np.inf)
        if cnt.sum() == 0:
            return out
        verts = np.concatenate([np.asarray(x, np.int64) for x in lists if len(x)])
        pid = np.repeat(np.arange(len(Q)), cnt)
        dvv = np.linalg.norm(self.V[verts] - Q[pid], axis=1)
        np.minimum.at(out, pid, dvv)
        i = (self.ij[verts, 0][:, None] + np.array([-1, -1, 0, 0])).ravel()
        j = (self.ij[verts, 1][:, None] + np.array([-1, 0, -1, 0])).ravel()
        pq = np.repeat(pid, 4)
        ok = (i >= 0) & (j >= 0) & (i < self.H - 1) & (j < self.W - 1)
        i, j, pq = i[ok], j[ok], pq[ok]
        ok = self.quad_valid[i, j]
        i, j, pq = i[ok], j[ok], pq[ok]
        if i.size == 0:
            return out
        nq = np.int64((self.H - 1) * (self.W - 1))
        key = np.unique(pq * nq + i.astype(np.int64) * (self.W - 1) + j)
        pq = key // nq; lin = key % nq; i = lin // (self.W - 1); j = lin % (self.W - 1)
        g = self.grid
        for s0 in range(0, len(key), 2_000_000):
            sl = slice(s0, s0 + 2_000_000)
            ii, jj, pp = i[sl], j[sl], pq[sl]
            A = g[ii, jj]; B = g[ii, jj + 1]; C = g[ii + 1, jj]; E = g[ii + 1, jj + 1]; X = Q[pp]
            d = np.minimum(closest_point_dist(X, A, B, E), closest_point_dist(X, A, E, C))
            np.minimum.at(out, pp, d)
        return out

    def min_dist(self, P, dv=None, stop_vox=0.0, chunk=256):
        """Exact min over points P (n,3) of point-to-surface distance.
        Returns (dist, argmin index, info). If stop_vox > 0, refinement stops once the attained
        distance is <= stop_vox (the returned value is then an attained exact distance of one
        point, i.e. an upper bound on the set minimum, with lower bound max(0, min dv - Lc))."""
        P = np.asarray(P, np.float64)
        if dv is None:
            dv, _ = self.tree.query(P, workers=4)
        ub = float(dv.min()); arg = int(dv.argmin())
        order = np.argsort(dv, kind='stable')
        pos = 0; nref = 0; stopped = False
        while pos < len(order):
            if dv[order[pos]] - self.Lc > ub:
                break
            if stop_vox > 0 and ub <= stop_vox:
                stopped = True
                break
            sel = order[pos:pos + chunk]
            sel = sel[dv[sel] - self.Lc <= ub]
            pos += chunk
            d = self._batch_dist(P[sel], np.full(len(sel), ub + self.Lc))
            nref += len(sel)
            k = int(np.argmin(d))
            if d[k] < ub:
                ub, arg = float(d[k]), int(sel[k])
        lb = max(0.0, float(dv.min()) - self.Lc)
        return ub, arg, {'refined_points': nref, 'early_stop': stopped, 'lower_bound_vox': lb}

    def point_dist(self, P):
        """Exact per-point distances (for tests / small sets)."""
        P = np.asarray(P, np.float64)
        dv, _ = self.tree.query(P)
        out = dv.copy()
        return np.minimum(dv, self._batch_dist(P, dv + self.Lc))

    def point_dist_loop(self, P):
        """Per-point reference with the looser radius d_v + L (tests only)."""
        P = np.asarray(P, np.float64)
        dv, _ = self.tree.query(P)
        out = dv.copy()
        for k in range(len(P)):
            verts = self.tree.query_ball_point(P[k], dv[k] + self.L)
            out[k] = min(dv[k], self._tri_dist_for_vertices(P[k], np.asarray(verts)))
        return out

    def brute(self, P):
        """O(n * triangles) reference, tests only."""
        P = np.asarray(P, np.float64)
        i, j = np.nonzero(self.quad_valid)
        g = self.grid
        A = g[i, j]; B = g[i, j + 1]; C = g[i + 1, j]; E = g[i + 1, j + 1]
        out = []
        for p in P:
            Q = np.broadcast_to(p, A.shape)
            d = np.minimum(closest_point_dist(Q, A, B, E), closest_point_dist(Q, A, E, C))
            dv = np.linalg.norm(self.V - p, axis=1).min()
            out.append(min(float(d.min()) if d.size else np.inf, dv))
        return np.array(out)


def save_compact(path, grid, meta):
    """Compact structure: float32 grid with NaN at invalid cells (triangulation is derived)."""
    g = np.asarray(grid, np.float32).copy()
    g[~(np.isfinite(g).all(-1) & (g >= 0).all(-1))] = np.nan
    np.savez_compressed(path, grid=g, meta=np.array(repr(meta)))


def load_compact(path):
    z = np.load(path)
    return Surface(z['grid'])
