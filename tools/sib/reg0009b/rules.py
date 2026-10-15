# Provenance: Project HERCULES | owner the owner | [id removed]
"""Same-papyrus rule with normal distance (task reg0009b step 3), shared by overlap.py and tests.
For source points A and a densified target (points Bp, unit normals Bn, KD-tree T):
nearest target point (Euclidean <= 12 vox); dn = |(a - b) . n_b|; dt = sqrt(d^2 - dn^2);
only points with dt <= 3 vox count. SAME iff #(dn < 2) >= 1000 and #[0,1) >= 2 * #[2,3)."""
import numpy as np


def direction(A, Bp, Bn, T, *, workers=4, min_within_2=1000, ratio=2.0, dt_max=3.0):
    d, i = T.query(A, k=1, distance_upper_bound=12.0, workers=workers)
    f = np.isfinite(d); d = d[f]; i = i[f]; Af = A[f]
    dn = np.abs(np.einsum('ij,ij->i', Af - Bp[i], Bn[i]))
    dt = np.sqrt(np.maximum(d ** 2 - dn ** 2, 0))
    ok = dt <= dt_max
    dn = dn[ok]
    hist = [int(((dn >= k) & (dn < k + 1)).sum()) for k in range(10)]
    c = hist[:3]
    w2 = c[0] + c[1]
    eu = [int(((d >= k) & (d < k + 1)).sum()) for k in range(3)]
    return dict(n_src=int(len(A)), hist_dn_0_10=hist, counts_dn=c, within2=w2,
                same=bool(w2 >= min_within_2 and c[0] >= ratio * c[2]),
                counts_euclid=eu, frac_src_within2=round(w2 / max(len(A), 1), 5))


# ---------------------------------------------------------------------------
# CORR-RETRACE-RULE (RULES.md 2026-09-25T19:01:33Z): fail-closed rule.
# SAME iff (a) literal nearest-densified-vertex Euclidean bins OR (b) point-to-triangulated-surface
# bins give >= 1000 points within 2 vox and count[0,1) >= 2 * count[2,3).
# ---------------------------------------------------------------------------

def _closest_on_tri(p, a, b, c):
    """Vectorised closest point on triangles (a, b, c) to points p (Ericson, RTCD 5.1.5). All (N, 3)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = p - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = p - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    out = np.empty_like(p)
    done = np.zeros(len(p), bool)
    def put(m, val):
        nonlocal done
        m = m & ~done
        out[m] = val[m] if val.ndim == 2 else val
        done |= m
    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(invalid='ignore', divide='ignore'):
        v = d1 / (d1 - d3); put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6); put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc); v3 = vb * den; w3 = vc * den
        put(np.ones(len(p), bool), a + v3[:, None] * ab + w3[:, None] * ac)
    return out


class TriSurface:
    """Triangulated densified grid: dense (H, W, 3) points + validity. Each valid quad -> 2 triangles."""

    def __init__(self, dp, dv):
        from scipy.spatial import cKDTree
        self.P = dp; self.V = dv
        self.rc = np.argwhere(dv)
        self.T = cKDTree(dp[dv])
        H, W = dv.shape
        self.qv = np.zeros((H + 1, W + 1), bool)  # padded quad validity, quad (r, c) at [r+1, c+1]
        self.qv[1:-1, 1:-1] = dv[:-1, :-1] & dv[:-1, 1:] & dv[1:, :-1] & dv[1:, 1:]

    def distance(self, A, *, k=4, upper=12.0, workers=4, chunk=200000):
        """Point-to-surface distance for points A (N, 3); inf where no vertex within `upper`."""
        out = np.full(len(A), np.inf)
        for s in range(0, len(A), chunk):
            a = A[s:s + chunk]
            d, idx = self.T.query(a, k=k, distance_upper_bound=upper, workers=workers)
            best = np.full(len(a), np.inf)
            H, W = self.V.shape
            for j in range(k):
                ok = np.isfinite(d[:, j])
                if not ok.any(): continue
                r, c = self.rc[idx[ok, j]].T
                pa = a[ok]
                for dr in (-1, 0):
                    for dc in (-1, 0):
                        qr, qc = r + dr, c + dc
                        m = self.qv[qr + 1, qc + 1]
                        if not m.any(): continue
                        q00 = self.P[qr[m], qc[m]]; q01 = self.P[qr[m], qc[m] + 1]
                        q10 = self.P[qr[m] + 1, qc[m]]; q11 = self.P[qr[m] + 1, qc[m] + 1]
                        for t0, t1, t2 in ((q00, q01, q11), (q00, q11, q10)):
                            cp = _closest_on_tri(pa[m], t0, t1, t2)
                            dd = np.linalg.norm(pa[m] - cp, axis=1)
                            sub = np.flatnonzero(ok)[m]
                            best[sub] = np.minimum(best[sub], dd)
            out[s:s + chunk] = best
        return out


def bins_rule(dist, *, min_within_2=1000, ratio=2.0):
    c = [int(((dist >= k) & (dist < k + 1)).sum()) for k in range(3)]
    return c, bool(c[0] + c[1] >= min_within_2 and c[0] >= ratio * c[2])


def failclosed(A, surf, *, workers=4):
    """Form (a) literal nearest-vertex and form (b) point-to-surface; SAME = (a) or (b)."""
    dv, _ = surf.T.query(A, k=1, distance_upper_bound=12.0, workers=workers)
    ca, sa = bins_rule(dv)
    # a point <= 3 vox from the surface has its nearest dense vertex within sqrt(3^2 + 2.83^2) < 5 vox
    ds = surf.distance(A, upper=5.0, workers=workers)
    cb, sb = bins_rule(ds)
    hist_b = [int(((ds >= k) & (ds < k + 1)).sum()) for k in range(4)]
    return dict(counts_a_vertex=ca, same_a=sa, counts_b_surface=cb, same_b=sb, hist_b_0_4=hist_b,
                same=bool(sa or sb), frac_src_within2_b=round((cb[0] + cb[1]) / max(len(A), 1), 5))
