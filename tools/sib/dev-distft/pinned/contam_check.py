# Provenance: Project HERCULES | owner the owner | [id removed]
"""Contamination checks on a D2 training-patch registry (patch_registry*.npz), per RULES.md CORR-RETRACE-RULE.

Surfaces: every source's mesh points in the registry are triangulated.
  grid       mesh_xyz (N, G, H, 3): each grid cell (quad) -> 2 triangles; cells with a NaN vertex are dropped
  tilequads  mesh_xyz (N, Q, 2, 2, 3): per tile the 2 x 2 lattice of its corner pixel centres -> 2 triangles
Clearance (>= 128 vox exclusions, FL-09 halo): exact point-to-triangulated-surface distance (no sampling bound).
Same papyrus (fail-closed): a training segment is SAME as a window if EITHER
  (a) nearest-vertex distances to the segment's surface densified 5 x 5 (literal form), OR
  (b) point-to-triangulated-surface distances
give >= 1000 window points within 2 vox and count[0,1) >= 2 x count[2,3).
Limits (reported, not hidden): the triangulated surface is only as fine as the registry lattice (stagec: every 24 px;
tilegrid: tile corners only, 127 px apart); a sheet curving between lattice points is approximated by planes. For a
certificate that must hold at that scale, the checker is re-run on the segment mesh (registry keeps segment and
canvas box). Numbers only."""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

MIN_NEAR = 1000
DENSIFY = 5


def _quads_to_tris(a, b, c, d):
    """Quad (a b / c d, row-major lattice) -> triangles (a, b, d) and (a, d, c); (M, 3) arrays each."""
    return np.concatenate([np.stack([a, b, d], 1), np.stack([a, d, c], 1)])


def grid_triangles(grid: np.ndarray) -> np.ndarray:
    """(G, H, 3) lattice -> (T, 3, 3) triangles, dropping any quad with a non-finite vertex."""
    g = np.asarray(grid, np.float64)
    a, b, c, d = g[:-1, :-1], g[:-1, 1:], g[1:, :-1], g[1:, 1:]
    ok = np.isfinite(a).all(-1) & np.isfinite(b).all(-1) & np.isfinite(c).all(-1) & np.isfinite(d).all(-1)
    return _quads_to_tris(a[ok], b[ok], c[ok], d[ok])


def registry_surfaces(npz_path: str) -> dict[str, np.ndarray]:
    """{segment: (T, 3, 3) triangles} over every source in the registry."""
    out: dict[str, list] = {}
    with np.load(npz_path, allow_pickle=False) as z:
        for k in z.files:
            if not k.endswith("_mesh_xyz"):
                continue
            p = k[: -len("mesh_xyz")]
            mx = z[k]
            segs = z[p + "segment"] if (p + "segment") in z.files else np.array([""] * len(mx))
            for m, s in zip(mx, segs):
                if m.ndim == 3:                               # grid (G, H, 3)
                    tris = grid_triangles(m)
                elif m.ndim == 4 and m.shape[1:3] == (2, 2):  # tilequads (Q, 2, 2, 3)
                    tris = np.concatenate([grid_triangles(q) for q in m]) if len(m) else np.zeros((0, 3, 3))
                else:
                    raise ValueError(f"{k}: unsupported mesh layout {m.shape}")
                out.setdefault(str(s), []).append(tris)
    return {s: np.concatenate(v) if v else np.zeros((0, 3, 3)) for s, v in out.items()}


def point_triangle_distance(p: np.ndarray, tri: np.ndarray) -> np.ndarray:
    """Exact Euclidean distance from points p (M, 3) to triangles tri (M, 3, 3), pairwise by row
    (closest-point regions after Ericson, Real-Time Collision Detection 5.1.5)."""
    p = np.asarray(p, np.float64); a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    q = np.empty_like(p)
    done = np.zeros(len(p), bool)

    def put(mask, val):
        m = mask & ~done
        q[m] = val[m]
        done[m] = True

    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    put((d6 >= 0) & (d5 <= d6), c)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        w = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        put(np.ones(len(p), bool), a + vv[:, None] * ab + ww[:, None] * ac)
    return np.linalg.norm(p - q, axis=1)


class Surface:
    """Triangulated surface with exact nearest-distance queries."""

    def __init__(self, tris: np.ndarray):
        self.tris = np.asarray(tris, np.float64)
        if len(self.tris) == 0:
            raise ValueError("empty surface")
        self.cen = self.tris.mean(1)
        self.rmax = float(np.linalg.norm(self.tris - self.cen[:, None], axis=2).max())
        self.tree = cKDTree(self.cen)

    def distance(self, q: np.ndarray, chunk: int = 4096) -> np.ndarray:
        q = np.asarray(q, np.float64).reshape(-1, 3)
        out = np.empty(len(q))
        for s in range(0, len(q), chunk):
            qq = q[s:s + chunk]
            _, j = self.tree.query(qq, k=1)
            ub = point_triangle_distance(qq, self.tris[j])            # distance to one triangle: an upper bound
            cands = self.tree.query_ball_point(qq, ub + self.rmax)     # every triangle that can be nearer
            best = ub.copy()
            for i, cs in enumerate(cands):
                if len(cs) > 1:
                    cs = np.asarray(cs)
                    best[i] = point_triangle_distance(np.repeat(qq[i:i + 1], len(cs), 0), self.tris[cs]).min()
            out[s:s + chunk] = best
        return out


def densify_vertices(tris: np.ndarray, k: int = DENSIFY) -> np.ndarray:
    """Barycentric k-subdivision vertices of every triangle (the 5 x 5 densification of the literal form)."""
    pts = []
    for i in range(k + 1):
        for j in range(k + 1 - i):
            u, v = i / k, j / k
            pts.append(tris[:, 0] * (1 - u - v) + tris[:, 1] * u + tris[:, 2] * v)
    return np.unique(np.round(np.concatenate(pts), 6), axis=0)


def bins(d: np.ndarray) -> dict:
    return dict(n_within_2=int(np.sum(d < 2)), c01=int(np.sum(d < 1)), c12=int(np.sum((d >= 1) & (d < 2))),
                c23=int(np.sum((d >= 2) & (d < 3))))


def same_rule(b: dict) -> bool:
    return b["n_within_2"] >= MIN_NEAR and b["c01"] >= 2 * b["c23"]


def same_papyrus(tris: np.ndarray, window_pts: np.ndarray) -> dict:
    """CORR-RETRACE-RULE fail-closed: SAME if form (a) vertex OR form (b) surface says SAME."""
    w = np.asarray(window_pts, np.float64).reshape(-1, 3)
    w = w[np.isfinite(w).all(1)]
    dv, _ = cKDTree(densify_vertices(tris)).query(w, k=1)
    ds = Surface(tris).distance(w)
    ba, bb = bins(dv), bins(ds)
    return dict(vertex=ba, surface=bb, same_vertex=same_rule(ba), same_surface=same_rule(bb),
                same=bool(same_rule(ba) or same_rule(bb)))


def clearance(npz_path: str, query_pts: np.ndarray, threshold: float = 128.0) -> dict:
    """Minimum point-to-surface distance (vox) from query points to every training surface in the registry."""
    q = np.asarray(query_pts, np.float64).reshape(-1, 3)
    q = q[np.isfinite(q).all(1)]
    per = {}
    for seg, tris in registry_surfaces(npz_path).items():
        if len(tris):
            per[seg] = float(Surface(tris).distance(q).min())
    mn = min(per.values()) if per else None
    return dict(method="point-to-triangulated-surface (CORR-RETRACE-RULE)", n_query=int(len(q)),
                min_distance_vox=mn, per_segment_min=per, threshold_vox=threshold,
                pass_=bool(mn is not None and mn >= threshold))
