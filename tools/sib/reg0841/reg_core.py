# Provenance: Project HERCULES | owner the owner | [id removed]
"""Core of the 9.366 <-> 2.403 um block registration (CT only).

Frames: 9 um level-0 voxel p = (x, y, z); rescan level-0 voxel q = A p + c.
Blocks: B9 = 9 um block (origin o9 [z, y, x]); rescan region b2 (origin o2 [z, y, x]).
R9(p; A, c, d) = G_s * b2 sampled (trilinear) at A (p + d) + c, with G_s a Gaussian prefilter,
sigma = F/2 rescan vox (frozen before any held-out number exists).
Phase correlation (3-D Hann window, parabolic sub-voxel peak) returns s with B9(p) ~ R9(p + s);
iterated (resample at d += s) until |s| < 0.02 vox. Correspondence: p_c <-> A (p_c + d) + c.
"""
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

F = 9.366 / 2.403
SIGMA2 = F / 2


def prefilter(b2):
    return gaussian_filter(b2.astype(np.float32), SIGMA2, mode="nearest", truncate=3.0)


def block_points(o9, shape9):
    z, y, x = np.meshgrid(*[np.arange(o, o + n, dtype=np.float64) for o, n in zip(o9, shape9)], indexing="ij")
    return np.stack([x.ravel(), y.ravel(), z.ravel()], 1)


def sample(f2, o2, A, c, P, shape9, d=(0, 0, 0)):
    q = (P + np.asarray(d, float)) @ np.asarray(A).T + np.asarray(c)
    coords = np.stack([q[:, 2] - o2[0], q[:, 1] - o2[1], q[:, 0] - o2[2]])
    inside = np.all((coords >= 0) & (coords <= (np.array(f2.shape)[:, None] - 1)), axis=0)
    v = map_coordinates(f2, coords, order=1, mode="nearest")
    return v.reshape(shape9).astype(np.float32), float(inside.mean())


def ncc(a, b):
    a = a.astype(np.float64).ravel(); b = b.astype(np.float64).ravel()
    a = a - a.mean(); b = b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))


def _win(shape):
    w = np.ones(shape)
    for ax, n in enumerate(shape):
        s = [1] * len(shape); s[ax] = n
        w = w * np.hanning(n).reshape(s)
    return w


def phase_corr(B, R):
    """Return (s_xyz, peak): R(x) ~ B(x - s), i.e. B(p) ~ R(p + s)."""
    w = _win(B.shape)
    FB = np.fft.fftn((B - B.mean()) * w); FR = np.fft.fftn((R - R.mean()) * w)
    X = FR * np.conj(FB); X /= np.abs(X) + 1e-12
    r = np.fft.ifftn(X).real
    i = np.array(np.unravel_index(np.argmax(r), r.shape))
    sub = []
    for ax in range(3):
        n = r.shape[ax]
        im = i.copy(); im[ax] = (i[ax] - 1) % n
        ip = i.copy(); ip[ax] = (i[ax] + 1) % n
        y0, y1, y2 = r[tuple(im)], r[tuple(i)], r[tuple(ip)]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
        v = i[ax] + off
        sub.append(v if v <= n / 2 else v - n)
    sz, sy, sx = sub
    return np.array([sx, sy, sz]), float(r.max())


def refine(B, f2, o2, A, c, P, d0=(0, 0, 0), it=8, tol=0.02):
    d = np.asarray(d0, float).copy(); hist = []
    for _ in range(it):
        R, ins = sample(f2, o2, A, c, P, B.shape, d)
        s, pk = phase_corr(B, R)
        hist.append(dict(step=s.tolist(), peak=pk))
        d += s
        if np.linalg.norm(s) < tol:
            break
    R, ins = sample(f2, o2, A, c, P, B.shape, d)
    return d, dict(ncc_after_shift=ncc(B, R), pc_peak=hist[-1]["peak"], n_iter=len(hist), inside_frac=ins, hist=hist)


def fit_affine(P, Q):
    Xh = np.c_[P, np.ones(len(P))]
    sol, *_ = np.linalg.lstsq(Xh, Q, rcond=None)
    return sol[:3].T, sol[3]


def sheet_normal_pitch(B, max_lag=40.0, step=0.5):
    """Structure-tensor normal of the block and the autocorrelation period along it (9 um vox)."""
    g = gaussian_filter(B.astype(np.float32), 1.0)
    gz, gy, gx = np.gradient(g)
    Gm = np.stack([gx.ravel(), gy.ravel(), gz.ravel()])
    T = Gm @ Gm.T / Gm.shape[1]
    ev, V = np.linalg.eigh(T)
    n = V[:, -1]; aniso = float((ev[-1] - ev[-2]) / ev[-1])
    Z, Y, X = B.shape
    m = 20
    zz, yy, xx = np.meshgrid(np.arange(m // 2, Z - m // 2), np.arange(m * 2, Y - m * 2), np.arange(m * 2, X - m * 2), indexing="ij")
    base = B[zz, yy, xx].astype(np.float64)
    lags = np.arange(0, max_lag + 1e-9, step); ac = []
    for t in lags:
        cz = np.clip(zz + t * n[2], 0, Z - 1); cy = np.clip(yy + t * n[1], 0, Y - 1); cx = np.clip(xx + t * n[0], 0, X - 1)
        v = map_coordinates(B.astype(np.float32), np.stack([cz.ravel(), cy.ravel(), cx.ravel()]), order=1)
        ac.append(ncc(base, v))
    ac = np.array(ac)
    mins = [k for k in range(1, len(ac) - 1) if ac[k] < ac[k - 1] and ac[k] <= ac[k + 1]]
    pitch = None; flag = "ok"
    if mins:
        k0 = mins[0]
        maxs = [k for k in range(k0 + 1, len(ac) - 1) if ac[k] > ac[k - 1] and ac[k] >= ac[k + 1]]
        if maxs:
            pitch = float(lags[maxs[0]])
        else:
            pitch = float(2 * lags[k0]); flag = "no_second_max:2x_first_min"
    else:
        flag = "no_min"
    return n, pitch, aniso, flag, ac
