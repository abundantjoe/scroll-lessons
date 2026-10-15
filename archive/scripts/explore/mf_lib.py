"""Shared helpers for the stroke-matched-filter investigation (ds8 grid, 19.2 um/px)."""
import os, json, numpy as np
from scipy.ndimage import (distance_transform_edt, gaussian_filter, grey_opening,
                           grey_closing, uniform_filter)
from scipy.signal import fftconvolve
from scipy.stats import rankdata

PITCH8 = 19.192   # um per ds8 pixel (8 * 2.399)
F = 8

EVAL = [("20231005123336", "held1"), ("20231005123336", "held2"), ("20231005123336", "held3"),
        ("20231210121321", "held1"), ("20231210121321", "held2"),
        ("20231210121321", "held3"), ("20231210121321", "held4")]
TRAIN = [("20231005123336", "train"),
         ("20230929220926", "held1"), ("20230929220926", "held2"),
         ("20230929220926", "held3"), ("20230929220926", "held4"),
         ("20231012184424", "held1"), ("20231012184424", "held2"),
         ("20231012184424", "held3")]
VAL = [("20231012184424", "held4")]

ROOT = "/home/user/megara"
CACHE = "/home/user/megara/stats/explore/cache"


def cropdir(s, c):
    return os.path.join(ROOT, "data/s1", s, "derived", c)


def pool(x, h8, w8):
    return x[:h8 * F, :w8 * F].reshape(h8, F, w8, F).mean(axis=(1, 3))


def ds8_labels(s, c):
    """ds8 (text, blank) boolean maps.

    For EVAL crops the official cls_text/cls_blank (pooled >0.5) are used.
    For the TRAINING/VAL crops of segments 20230929220926 and 20231012184424 the
    stored cls_blank.npy is identically zero (a defect of the earlier run), so the
    blank class is rebuilt here with the judge's own rule
    (not label, >=0.3 mm from a label, inside the 5 mm zone, inside the mask).
    Cached under stats/explore/cache. Never applied to EVAL crops."""
    d = cropdir(s, c)
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, f"lab_{s}_{c}.npz")
    if os.path.exists(cp):
        z = np.load(cp)
        return z["t"], z["b"]
    t = np.load(d + "/cls_text.npy")
    b = np.load(d + "/cls_blank.npy")
    rebuilt = False
    if b.sum() == 0:
        assert (s, c) not in EVAL, "refuse to rebuild labels on an EVAL crop"
        L = np.load(d + "/label.npy")
        m = (np.load(d + "/mask_top.npy") > 0) & (np.load(d + "/mask_bot.npy") > 0)
        dist = distance_transform_edt(~L) * 2.399 / 1000.0
        b = (~L) & (dist >= 0.3) & (dist <= 5.0) & m
        rebuilt = True
    h8 = t.shape[0] // F
    tp = pool(t.astype(np.float32), h8, h8) > 0.5
    bp = pool(b.astype(np.float32), h8, h8) > 0.5
    np.savez_compressed(cp, t=tp, b=bp, rebuilt=np.array([rebuilt]))
    return tp, bp


def load_x(s, c):
    x = np.load(cropdir(s, c) + "/ds8_x.npy")
    return x[:22], x[22]


def auc(score, t, b, sub=None):
    a = score[t] if sub is None else score[t & sub]
    z = score[b] if sub is None else score[b & sub]
    if len(a) == 0 or len(z) == 0:
        return None
    rk = rankdata(np.concatenate([a, z]))
    n1, n0 = len(a), len(z)
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# ---------- mask-aware base image ----------
def fill(p, m, s0=2.0):
    """Normalised convolution: hole-filled image on the lacy mask. Both the isotropic
    baseline and every shape filter are built from this same image."""
    num = gaussian_filter(p * m, s0, mode="constant")
    den = gaussian_filter(m, s0, mode="constant")
    q = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0)
    return q.astype(np.float32), den.astype(np.float32)


# ---------- filters ----------
def iso_feats(q, scales):
    return [gaussian_filter(q, s, mode="nearest").astype(np.float32) if s > 0 else q.copy()
            for s in scales]


def hessian_feats(q, s):
    """gamma-normalised Hessian at scale s -> (ridge, det, trace, frangi)."""
    hxx = gaussian_filter(q, s, order=(0, 2), mode="nearest") * s * s
    hyy = gaussian_filter(q, s, order=(2, 0), mode="nearest") * s * s
    hxy = gaussian_filter(q, s, order=(1, 1), mode="nearest") * s * s
    tr = hxx + hyy
    dt = hxx * hyy - hxy * hxy
    disc = np.sqrt(np.maximum((hxx - hyy) ** 2 + 4 * hxy * hxy, 0)) / 2.0
    l1 = tr / 2 + disc          # larger algebraic eigenvalue
    l2 = tr / 2 - disc          # smaller
    # a bright ridge has l2 strongly negative (across) and l1 ~ 0 (along)
    ridge = -l2
    ab1, ab2 = np.abs(l1), np.abs(l2)
    big = np.where(ab1 >= ab2, l1, l2)
    small = np.where(ab1 >= ab2, l2, l1)
    rb = np.abs(small) / (np.abs(big) + 1e-6)
    S = np.sqrt(l1 * l1 + l2 * l2)
    cc = 0.5 * np.percentile(S, 99)
    frangi = np.where(big < 0, np.exp(-rb * rb / 0.5) * (1 - np.exp(-S * S / (2 * cc * cc + 1e-9))), 0.0)
    return [ridge.astype(np.float32), dt.astype(np.float32), tr.astype(np.float32),
            frangi.astype(np.float32)], (l1, l2, hxx, hyy, hxy)


def oriented_bank(q, sig_l, sig_w, n_theta=12, surround=2.5):
    """Max over orientations of an elongated zero-mean matched filter.
    Returns (max response, argmax-coherence = max-mean)."""
    rad = int(np.ceil(3 * max(sig_l, sig_w * surround)))
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    resp = None
    acc = 0.0
    for k in range(n_theta):
        th = np.pi * k / n_theta
        ct, st = np.cos(th), np.sin(th)
        u = xx * ct + yy * st          # along the stroke
        v = -xx * st + yy * ct         # across the stroke
        core = np.exp(-(u * u) / (2 * sig_l ** 2) - (v * v) / (2 * sig_w ** 2))
        sur = np.exp(-(u * u) / (2 * sig_l ** 2) - (v * v) / (2 * (sig_w * surround) ** 2))
        K = core / core.sum() - sur / sur.sum()
        r = fftconvolve(q, K[::-1, ::-1], mode="same").astype(np.float32)
        acc = acc + r
        resp = r if resp is None else np.maximum(resp, r)
    mean = acc / n_theta
    return resp, (resp - mean).astype(np.float32)


def tophat(q, r):
    k = int(round(r))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    se = (yy * yy + xx * xx) <= k * k
    op = grey_opening(q, footprint=se, mode="nearest")
    cl = grey_closing(q, footprint=se, mode="nearest")
    return (q - op).astype(np.float32), (cl - q).astype(np.float32)


# ---------- linear fit ----------
def fit_logistic(X, y, w=None, l2=1.0, iters=200):
    """Plain IRLS-free gradient fit; X already standardised. Returns (w, b)."""
    from sklearn.linear_model import LogisticRegression
    m = LogisticRegression(C=1.0 / l2, max_iter=iters, solver="lbfgs")
    m.fit(X, y, sample_weight=w)
    return m.coef_[0].astype(np.float64), float(m.intercept_[0])
