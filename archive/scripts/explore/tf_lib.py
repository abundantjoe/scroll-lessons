"""twoface investigation: shared helpers on the ds8 (19.2 um/px) surface-aligned stacks.

Channel contract (data contract given in the task):
  x[0:11]  TOP face    at delta = -4..+6 slices (1 slice = 2.4 um)
  x[11:22] BOTTOM face at the same offsets  (bottom = writing face)
  x[22]    mask coverage fraction
"""
import os, sys, json
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mf_lib import ds8_labels, cropdir, TRAIN, VAL, EVAL   # noqa: E402

PITCH8 = 19.192
DELTAS = np.arange(-4, 7)          # 11 offsets per face
NAMES = ([f"T{d:+d}" for d in DELTAS] + [f"B{d:+d}" for d in DELTAS])


def load_crop(s, c):
    x = np.load(cropdir(s, c) + "/ds8_x.npy")
    m = x[22] > 0.5
    t, b = ds8_labels(s, c)
    t = t & m
    b = b & m
    return x[:22].astype(np.float32), m, t, b


def fill(p, m, s0=2.0):
    """mask-aware normalised convolution (same recipe as mf_lib.fill)."""
    num = gaussian_filter(p * m, s0, mode="constant")
    den = gaussian_filter(m.astype(np.float32), s0, mode="constant")
    return np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)


def smooth(q, sigma):
    if sigma <= 0:
        return q
    return gaussian_filter(q, sigma, mode="nearest").astype(np.float32)


def auc(score, t, b):
    a = score[t]; z = score[b]
    if a.size < 10 or z.size < 10:
        return float("nan")
    rk = rankdata(np.concatenate([a, z]))
    n1, n0 = a.size, z.size
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
