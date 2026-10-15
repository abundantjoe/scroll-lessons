"""edgeshape (es): depth-profile SHAPE descriptors on the ds8 (19.2 um/px) surface-aligned stacks.

Channel contract:  x[0:11] TOP face at delta=-4..+6 slices, x[11:22] BOTTOM face, x[22] coverage.
Every channel was standardised per crop (median/MAD over the mask) by the data pipeline.
"""
import os, sys
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mf_lib import ds8_labels, cropdir, TRAIN, VAL, EVAL   # noqa: E402

PITCH8 = 19.192
NDEP = 11
DELTAS = np.arange(-4, 7)
SIGMAS = [0, 4, 8, 16]          # ds8 px
SIG_BG = 52.0                   # ~1 mm local background


def load_crop(s, c):
    x = np.load(cropdir(s, c) + "/ds8_x.npy")
    m = x[22] > 0.5
    t, b = ds8_labels(s, c)
    return x[:22].astype(np.float32), m, (t & m), (b & m)


def nconv(p, mf, sigma):
    """mask-aware Gaussian smoothing (normalised convolution)."""
    if sigma <= 0:
        return p.astype(np.float32)
    num = gaussian_filter(p * mf, sigma, mode="nearest")
    den = gaussian_filter(mf, sigma, mode="nearest")
    return np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)


def smooth_stack(x, m, sigma):
    mf = m.astype(np.float32)
    return np.stack([nconv(x[i], mf, sigma) for i in range(x.shape[0])])


def auc(score, t, b):
    a = score[t]; z = score[b]
    if a.size < 10 or z.size < 10:
        return float("nan")
    rk = rankdata(np.concatenate([a, z]))
    n1, n0 = a.size, z.size
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# ---------------- descriptors ----------------

def face_resid(Q, m, i0, sig_bg=SIG_BG):
    """R = face channels minus their own local (1 mm) background, inside the mask."""
    mf = m.astype(np.float32)
    V = Q[i0:i0 + NDEP]
    return np.stack([V[d] - nconv(V[d], mf, sig_bg) for d in range(NDEP)]).astype(np.float32)


def _subpix_argmax(R):
    """parabolic sub-sample refinement of the arg-max along axis 0 (depth)."""
    k = np.argmax(R, axis=0)
    kc = np.clip(k, 1, R.shape[0] - 2)
    idx = np.arange(R.shape[1] * R.shape[2]).reshape(R.shape[1], R.shape[2])
    flat = R.reshape(R.shape[0], -1)
    kf = kc.ravel()
    y0 = flat[kf - 1, idx.ravel()]
    y1 = flat[kf, idx.ravel()]
    y2 = flat[kf + 1, idx.ravel()]
    den = (y0 - 2 * y1 + y2)
    off = np.where(np.abs(den) > 1e-6, 0.5 * (y0 - y2) / np.where(np.abs(den) > 1e-6, den, 1.0), 0.0)
    off = np.clip(off, -1, 1)
    curv = -den                                   # positive = sharp crest
    return (kf.astype(np.float32) + off).reshape(k.shape), curv.reshape(k.shape).astype(np.float32), y1.reshape(k.shape)


def edge_feats(R, m):
    """nonlinear, level-invariant descriptors of one face's residual depth profile R (11,H,W)."""
    A = R.max(axis=0)
    dstar, curv, _ = _subpix_argmax(R)
    G = np.diff(R, axis=0)                        # 10 forward differences
    smax = G.max(axis=0)
    dslope, _, _ = _subpix_argmax(G)
    a0 = float(np.median(np.abs(A[m]))) + 1e-6
    pos = np.maximum(R, 0.0).sum(axis=0)
    width = pos / (A + a0)
    sharp = smax / (np.abs(A) + a0)
    nrm = np.sqrt((R * R).sum(axis=0))
    cen = (np.maximum(R, 0.0) * DELTAS[:, None, None].astype(np.float32)).sum(axis=0) / np.maximum(pos, 1e-6)
    names = ["dstar", "curv", "amp", "smax", "dslope", "width", "sharp", "norm", "cen"]
    return np.stack([dstar, curv, A, smax, dslope, width, sharp, nrm, cen]).astype(np.float32), names


def shape_unit(R):
    n = np.sqrt((R * R).sum(axis=0)) + 1e-6
    return (R / n).astype(np.float32)


def build_groups(x, m, sigma):
    """returns dict group -> (stack of feature maps, names)."""
    Q = smooth_stack(x, m, sigma)
    out = {}
    ch_names = [f"T{d:+d}" for d in DELTAS] + [f"B{d:+d}" for d in DELTAS]
    out["CH22"] = (Q, ch_names)
    lvl = np.stack([Q[0:NDEP].mean(0), Q[NDEP:2 * NDEP].mean(0)])
    out["LVL"] = (lvl, ["Tlvl", "Blvl"])
    d1, d2, sh, eg, n1, n2, ns, ne = [], [], [], [], [], [], [], []
    for face, i0 in (("T", 0), ("B", NDEP)):
        V = Q[i0:i0 + NDEP]
        g1 = 0.5 * (V[2:] - V[:-2])               # 9 central first differences
        g2 = V[2:] - 2 * V[1:-1] + V[:-2]         # 9 second differences
        d1.append(g1); d2.append(g2)
        n1 += [f"{face}d1{d:+d}" for d in DELTAS[1:-1]]
        n2 += [f"{face}d2{d:+d}" for d in DELTAS[1:-1]]
        R = face_resid(Q, m, i0)
        sh.append(shape_unit(R)); ns += [f"{face}u{d:+d}" for d in DELTAS]
        e, en = edge_feats(R, m)
        eg.append(e); ne += [f"{face}{v}" for v in en]
    out["D1"] = (np.concatenate(d1), n1)
    out["D2"] = (np.concatenate(d2), n2)
    out["SHAPE"] = (np.concatenate(sh), ns)
    out["EDGE"] = (np.concatenate(eg), ne)
    for k in out:
        out[k] = (np.where(m[None], out[k][0], 0.0).astype(np.float32), out[k][1])
    return out
