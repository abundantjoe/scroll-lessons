"""Pixel-level metrics: rank/gate only, never evidence of letters (I14).

Provenance: Project HERCULES | owner the owner | [id removed]
"""
import cv2
import numpy as np
from scipy import ndimage
from scipy.stats import rankdata

SIGMA_EQ_GRID_MM = np.round(np.arange(0.0, 0.6001, 0.025), 4)
BLOB_THRESHOLD = 180
BLOB_AREA_UNIT_CM2 = 4.717  # K = round(10 * area_cm2 / 4.717) (section 4.C7)


def auc(scores, labels, valid=None):
    """Mann-Whitney AUC of scores for labels (1 = ink, 0 = blank); other label values
    and invalid pixels are ignored. Ties get average ranks."""
    s = np.asarray(scores, dtype=np.float64).ravel()
    lab = np.asarray(labels).ravel()
    m = (lab == 0) | (lab == 1)
    if valid is not None:
        m &= np.asarray(valid, bool).ravel()
    s, lab = s[m], lab[m]
    n1, n0 = int((lab == 1).sum()), int((lab == 0).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[lab == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def pearson(a, b, valid=None):
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    m = np.isfinite(a) & np.isfinite(b)
    if valid is not None:
        m &= np.asarray(valid, bool).ravel()
    a, b = a[m] - a[m].mean(), b[m] - b[m].mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else float("nan")


def sigma_eq(model_map, reference, px_per_mm, valid=None, grid_mm=SIGMA_EQ_GRID_MM):
    """Gaussian blur sigma (mm) of the reference that maximises Pearson r with the model
    map. Returns (sigma_mm, r_at_best, table)."""
    ref = np.asarray(reference, dtype=np.float64)
    table = []
    for s_mm in grid_mm:
        s_px = s_mm * px_per_mm
        blurred = ref if s_px == 0 else cv2.GaussianBlur(ref, (0, 0), s_px, borderType=cv2.BORDER_REFLECT)
        table.append((float(s_mm), pearson(model_map, blurred, valid)))
    best = max(table, key=lambda t: (-np.inf if np.isnan(t[1]) else t[1]))
    return best[0], best[1], table


def f_threshold(map_u8, thr=150, valid=None):
    m = np.asarray(map_u8)
    v = np.ones(m.shape, bool) if valid is None else np.asarray(valid, bool)
    return float(((m >= thr) & v).sum() / max(v.sum(), 1))


def blob_f180(map_u8, area_cm2, valid=None, thr=BLOB_THRESHOLD):
    """Fraction of valid area covered by the K largest 8-connected components of
    (map >= 180), K = max(1, round(10 * area_cm2 / 4.717)). Re-implemented from the
    section 4.C7 description; archived thresholds may not transfer exactly."""
    m = np.asarray(map_u8)
    v = np.ones(m.shape, bool) if valid is None else np.asarray(valid, bool)
    lab, n = ndimage.label((m >= thr) & v, structure=np.ones((3, 3), int))
    if n == 0:
        return 0.0
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    k = max(1, int(round(10.0 * area_cm2 / BLOB_AREA_UNIT_CM2)))
    return float(sizes[:k].sum() / max(v.sum(), 1))
