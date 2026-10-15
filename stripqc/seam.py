"""Where two independently fit surfaces share a sheet, and whether their maps agree there.

Lessons encoded here: winding indices of different fits are NOT comparable (the same index can be 3-15 sheets apart);
match surfaces by 3-D geometry only. Agreement of two maps at the same 3-D points validates the pixel -> 3-D mapping
and shows a reproducible CT response; it does not certify ink (both maps read the same CT).
"""
import numpy as np
from scipy.spatial import cKDTree


def surface_points(P, ok, up=3):
    """Bilinear samples (up x up per valid quad) of a node grid -> (n, 3)."""
    cell = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    t = (np.arange(up) + 0.5) / up
    u, v = np.meshgrid(t, t, indexing='ij')
    u, v = u[..., None], v[..., None]
    out = []
    for i, j in zip(*np.nonzero(cell)):
        a, b, c, d = P[i, j], P[i + 1, j], P[i, j + 1], P[i + 1, j + 1]
        out.append(((1 - u) * (1 - v) * a + u * (1 - v) * b + (1 - u) * v * c + u * v * d).reshape(-1, 3))
    return np.concatenate(out) if out else np.zeros((0, 3))


def coincident_fraction(PA, PB, tol=4.0):
    """Share of A's points (inside B's z range) within tol vox of B's surface, and their median distance."""
    z0, z1 = max(PA[:, 2].min(), PB[:, 2].min()), min(PA[:, 2].max(), PB[:, 2].max())
    a = PA[(PA[:, 2] >= z0) & (PA[:, 2] <= z1)]
    if not len(a):
        return dict(n=0, frac=0.0, med=None)
    d, _ = cKDTree(PB).query(a, distance_upper_bound=2 * tol)
    close = d <= tol
    return dict(n=int(len(a)), frac=float(close.mean()), med=float(np.median(d[close])) if close.any() else None)


def circular_null_r(a, B, rows, cols, shifts):
    """Pearson r of a (values of map A at matched points) vs B at the matched (rows, cols), and the null distribution
    with B's columns circularly shifted by each k in `shifts` (equal n for every shift; report the effective n:
    neighbouring shifts are correlated). -> (r0, null array, empirical p)."""
    W = B.shape[1]
    def r(b):
        return float(np.corrcoef(a, b)[0, 1]) if a.std() > 1e-9 and b.std() > 1e-9 else np.nan
    r0 = r(B[rows, cols])
    nul = np.array([r(B[rows, (cols + k) % W]) for k in shifts])
    nul = nul[np.isfinite(nul)]
    p = float((np.sum(nul >= r0) + 1) / (nul.size + 1)) if nul.size and np.isfinite(r0) else None
    return r0, nul, p
