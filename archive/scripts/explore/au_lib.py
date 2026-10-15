"""AUDIT (reference-noise) helpers. Full-resolution 2.4 um work, one crop at a time.

Everything here is descriptive: no fitting, no thresholds learned from data.
"""
import os, json
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = "/home/user/megara"
PITCH = 2.399                     # um / px at full resolution
MM = PITCH / 1000.0               # mm per px

TRAIN = [("20231005123336", "train")]
HELD = [("20231005123336", "held1"), ("20231005123336", "held2"), ("20231005123336", "held3"),
        ("20231210121321", "held1"), ("20231210121321", "held2"),
        ("20231210121321", "held3"), ("20231210121321", "held4")]
TAGS = ["v0.1b", "v1b", "v2", "v3", "team"]


def cdir(seg, crop):
    return os.path.join(ROOT, "data/s1", seg, "derived", crop)


def load_masks(seg, crop):
    d = cdir(seg, crop)
    L = np.load(os.path.join(d, "label.npy"))
    text = np.load(os.path.join(d, "cls_text.npy"))
    blank = np.load(os.path.join(d, "cls_blank.npy"))
    m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
    return L, text, blank, m


def load_score(seg, crop, tag, face="bot"):
    p = os.path.join(cdir(seg, crop), f"s_{face}_{tag}.npy")
    if not os.path.exists(p):
        return None
    return np.load(p).astype(np.float32)


def edt_mm(b):
    """Euclidean distance (mm) from every False pixel of b to the nearest True pixel is
    edt_mm(~b); edt_mm(b) gives, for every True pixel, its distance to the nearest False one."""
    return (distance_transform_edt(b) * MM).astype(np.float32)


def auc_masked(s, pos, neg, rng, cap=400000):
    """Mann-Whitney AUC of score s between boolean masks pos and neg, subsampled to <=cap each."""
    a = s[pos]
    b = s[neg]
    n1, n0 = a.size, b.size
    if n1 < 200 or n0 < 200:
        return None, n1, n0
    if n1 > cap:
        a = a[rng.choice(n1, cap, replace=False)]
    if n0 > cap:
        b = b[rng.choice(n0, cap, replace=False)]
    rk = rankdata(np.concatenate([a, b]))
    k1 = a.size
    v = float((rk[:k1].sum() - k1 * (k1 + 1) / 2) / (k1 * b.size))
    return v, int(n1), int(n0)


def shift(a, dy, dx, fill=0):
    """Integer translation of a 2-D array, zero (or `fill`) padded."""
    out = np.full_like(a, fill)
    ys_s = slice(max(0, dy), a.shape[0] + min(0, dy))
    ys_d = slice(max(0, -dy), a.shape[0] + min(0, -dy))
    xs_s = slice(max(0, dx), a.shape[1] + min(0, dx))
    xs_d = slice(max(0, -dx), a.shape[1] + min(0, -dx))
    out[ys_d, xs_d] = a[ys_s, xs_s]
    return out


def jwrite(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1)
    print("wrote", path, flush=True)
