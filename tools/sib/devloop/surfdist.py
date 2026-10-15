# Provenance: Project HERCULES | owner the owner | [id removed]
"""Vendored verbatim from branch claude/gifted-bell-gavnl5-sib-tribunal commit 95de3ba320a4718cedaea47085b39dbc52329713,
src/hercules/tribunal/preread.py (team code; CORR-RETRACE-RULE reference implementation): _closest_on_triangles,
surface_distances, same_papyrus_surface. Only the imports are adapted."""
import math
import numpy as np
from scipy.spatial import cKDTree
from hercules.geometry.tifxyz import valid_mask
RETRACE_DENSIFY = 5
RETRACE_MIN_WITHIN_2 = 1000
RETRACE_RATIO = 2.0

def _closest_on_triangles(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Distance from points p (N, 3) to triangles (a, b, c) (N, 3) each (Ericson 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3 = np.einsum("ij,ij->i", ab, bp)
    d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5 = np.einsum("ij,ij->i", ab, cp)
    d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    res = np.empty_like(p)
    done = np.zeros(len(p), dtype=bool)

    def put(mask, val):
        m = mask & ~done
        res[m] = val[m]
        done[m] = True

    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        inner = a + ab * vv[:, None] + ac * ww[:, None]
    put(np.ones(len(p), dtype=bool), inner)
    return np.linalg.norm(p - res, axis=1)


def surface_distances(A_dense: np.ndarray, B_dense_grid: np.ndarray, max_dist: float = 3.0, k_nn: int = 4,
                      workers: int = 1) -> np.ndarray:
    """Distance from each valid point of A (N, 3 or grid) to the triangulated surface of
    the densified grid B; inf beyond ``max_dist`` (plus a circumradius bound)."""
    from hercules.geometry.contamination import cloud

    a = cloud(A_dense)
    g = np.asarray(B_dense_grid, dtype=np.float64)
    vb = valid_mask(g)
    Hb, Wb = vb.shape
    idx_grid = np.full((Hb, Wb), -1, dtype=np.int64)
    idx_grid[vb] = np.arange(int(vb.sum()))
    bpts = g[vb]
    rc, cc = np.nonzero(vb)
    out = np.full(len(a), np.inf)
    if len(bpts) == 0 or len(a) == 0:
        return out
    # circumradius bound: any surface point is within half the longest quad diagonal of a vertex
    du = np.linalg.norm(g[:, 1:] - g[:, :-1], axis=-1)[vb[:, 1:] & vb[:, :-1]]
    dv = np.linalg.norm(g[1:] - g[:-1], axis=-1)[vb[1:] & vb[:-1]]
    hmax = float(max(du.max() if du.size else 0.0, dv.max() if dv.size else 0.0))
    reach = max_dist + hmax * math.sqrt(2.0) / 2.0 + 1e-6
    tree = cKDTree(bpts)
    d, nn = tree.query(a, k=k_nn, distance_upper_bound=reach, workers=workers)
    d = np.atleast_2d(d.reshape(len(a), -1))
    nn = np.atleast_2d(nn.reshape(len(a), -1))
    cand = np.isfinite(d[:, 0])
    qi = np.flatnonzero(cand)
    if qi.size == 0:
        return out
    best = np.full(qi.size, np.inf)
    for kk in range(nn.shape[1]):
        vid = nn[qi, kk]
        okv = vid < len(bpts)
        r0 = np.where(okv, rc[np.minimum(vid, len(rc) - 1)], 0)
        c0 = np.where(okv, cc[np.minimum(vid, len(cc) - 1)], 0)
        for dr in (-1, 0):
            for dc in (-1, 0):
                r, c = r0 + dr, c0 + dc
                inq = okv & (r >= 0) & (c >= 0) & (r + 1 < Hb) & (c + 1 < Wb)
                rr, cc2 = np.where(inq, r, 0), np.where(inq, c, 0)
                qv = inq & vb[rr, cc2] & vb[rr + 1, cc2] & vb[rr, cc2 + 1] & vb[rr + 1, cc2 + 1]
                if not qv.any():
                    continue
                sel = np.flatnonzero(qv)
                p = a[qi[sel]]
                p00, p01 = g[rr[sel], cc2[sel]], g[rr[sel], cc2[sel] + 1]
                p10, p11 = g[rr[sel] + 1, cc2[sel]], g[rr[sel] + 1, cc2[sel] + 1]
                for tri in ((p00, p01, p10), (p11, p10, p01)):
                    dd = _closest_on_triangles(p, *tri)
                    best[sel] = np.minimum(best[sel], dd)
    out[qi] = best
    out[out > max_dist] = np.inf
    return out


def same_papyrus_surface(A_dense, B_dense_grid, *, min_within_2: int = RETRACE_MIN_WITHIN_2,
                         ratio: float = RETRACE_RATIO, workers: int = 1) -> dict:
    """The declared rule with point-to-SURFACE distance (density-independent form)."""
    d = surface_distances(A_dense, B_dense_grid, 3.0, workers=workers)
    c0 = int(np.sum(d < 1.0))
    c1 = int(np.sum((d >= 1.0) & (d < 2.0)))
    c2 = int(np.sum((d >= 2.0) & (d < 3.0)))
    w2 = c0 + c1
    return {"counts": [c0, c1, c2], "n_within_2": w2, "same": bool(w2 >= min_within_2 and c0 >= ratio * c2),
            "n_a": int(np.isfinite(d).size)}


