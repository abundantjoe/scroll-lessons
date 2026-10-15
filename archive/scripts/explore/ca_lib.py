"""calib (ca): per-crop calibration / geometry conditioning on the ds8 (19.2 um/px) stacks.

Channel contract: x[0:11] TOP face at delta=-4..+6 slices, x[11:22] BOTTOM face, x[22] coverage.
Every channel was standardised per crop (median/MAD over the mask) by the data pipeline.
"""
import os, sys, json
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mf_lib import ds8_labels, cropdir, TRAIN, VAL, EVAL, pool  # noqa: E402

PITCH8 = 19.192
NDEP = 11
DELTAS = np.arange(-4, 7)
SIGMAS = [0, 4, 8, 16]
NAMES88 = [f"{f}{d:+d}@{s}" for s in SIGMAS for f in ("T", "B") for d in DELTAS]
# NOTE: build order below is (sigma, channel index 0..21) with channels T-4..T+6,B-4..B+6
NAMES88 = [f"{('T' if i < NDEP else 'B')}{DELTAS[i % NDEP]:+d}@{s}"
           for s in SIGMAS for i in range(22)]


def auc(score, t, b):
    a = np.asarray(score)[t]; z = np.asarray(score)[b]
    if a.size < 10 or z.size < 10:
        return float("nan")
    rk = rankdata(np.concatenate([a, z]))
    n1, n0 = a.size, z.size
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def auc_vec(s, y):
    """AUC of score vector s against binary y (1=text)."""
    t = y == 1; b = y == 0
    return auc(s, t, b)


def fast_smooth(p, sigma):
    """Gaussian smoothing; for large sigma done on a coarse pyramid level (exact to O(f/sigma))."""
    from scipy.ndimage import zoom
    if sigma <= 0:
        return p.astype(np.float32)
    if sigma <= 20:
        return gaussian_filter(p, sigma, mode="nearest").astype(np.float32)
    f = max(2, int(sigma // 6))
    H, W = p.shape
    Hp = -(-H // f) * f; Wp = -(-W // f) * f
    q = np.pad(p, ((0, Hp - H), (0, Wp - W)), mode="edge")
    s = q.reshape(Hp // f, f, Wp // f, f).mean(axis=(1, 3))
    s = gaussian_filter(s, sigma / f, mode="nearest")
    u = zoom(s, f, order=1)
    return u[:H, :W].astype(np.float32)


def nconv(p, mf, sigma, den=None):
    if sigma <= 0:
        return p.astype(np.float32)
    num = fast_smooth(p * mf, sigma)
    if den is None:
        den = fast_smooth(mf, sigma)
    return np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)


def load_crop(s, c):
    x = np.load(cropdir(s, c) + "/ds8_x.npy")
    m = x[22] > 0.5
    t, b = ds8_labels(s, c)
    return x[:22].astype(np.float32), m, (t & m), (b & m)


def build_B88(x, m):
    """22 channels at 4 mask-aware Gaussian scales -> (88,H,W)."""
    mf = m.astype(np.float32)
    d2 = fast_smooth(mf, 2.0)
    # hole-fill once at sigma 2 so smoothing is well defined inside the lacy mask
    base = np.stack([nconv(x[i], mf, 2.0, d2) for i in range(22)])
    base = np.where(m[None], x, base).astype(np.float32)
    out = []
    for s in SIGMAS:
        dn = fast_smooth(mf, float(s)) if s > 0 else None
        for i in range(22):
            out.append(nconv(base[i], mf, s, dn) if s > 0 else base[i])
    return np.stack(out).astype(np.float32)


def standardise_cols(F, m):
    """per-crop standardisation of each feature map over the mask (unsupervised)."""
    G = np.empty_like(F)
    for i in range(F.shape[0]):
        v = F[i][m]
        mu = float(v.mean()); sd = float(v.std()) + 1e-6
        G[i] = np.where(m, (F[i] - mu) / sd, 0.0)
    return G


def sample_idx(t, b, nmax=20000, seed=0):
    rng = np.random.default_rng(seed)
    it = np.flatnonzero(t.ravel()); ib = np.flatnonzero(b.ravel())
    if it.size > nmax:
        it = rng.choice(it, nmax, replace=False)
    if ib.size > nmax:
        ib = rng.choice(ib, nmax, replace=False)
    idx = np.concatenate([it, ib])
    y = np.concatenate([np.ones(it.size, np.int8), np.zeros(ib.size, np.int8)])
    return idx, y


def fit_logistic(X, y, C=1.0, iters=300):
    from sklearn.linear_model import LogisticRegression
    w = np.where(y == 1, 1.0 / max((y == 1).sum(), 1), 1.0 / max((y == 0).sum(), 1))
    mdl = LogisticRegression(C=C, max_iter=iters, solver="lbfgs")
    mdl.fit(X, y, sample_weight=w)
    return mdl.coef_[0].astype(np.float64), float(mdl.intercept_[0])


def pooled_map(s, c, tag, h8):
    p = cropdir(s, c) + f"/s_bot_{tag}.npy"
    if not os.path.exists(p):
        return None
    a = np.load(p).astype(np.float32)
    return pool(a, h8, h8)
