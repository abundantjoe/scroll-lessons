"""Evaluation metrics for ink detection against hand-labelled text.

Every function here is a line-for-line port of the research script that produced the published numbers, so results reproduce
exactly (see tests/test_published.py):

    judge_classes, pixel_auc   <- scripts/s1_judge.py
    stroke_auc                 <- scripts/stroke_test.py
    local_stroke_auc           <- scripts/local_stroke_test.py

Conventions: all maps are 2-D arrays of the same shape; ``label`` is the registered hand label (True = ink); ``mask`` is the judge mask
(True = pixel is judged); ``pitch_um`` is the pixel size in micrometres. Scores may be any real-valued map: only their ranks matter.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import rankdata

__all__ = ["auc", "judge_classes", "pixel_auc", "stroke_auc", "local_stroke_auc", "judge"]


def auc(pos: np.ndarray, neg: np.ndarray) -> float | None:
    """Mann-Whitney AUC: probability that a positive scores above a negative (ties count one half). None if a class is empty."""
    pos = np.asarray(pos, dtype=np.float64).ravel(); neg = np.asarray(neg, dtype=np.float64).ravel()
    n1, n0 = len(pos), len(neg)
    if n1 == 0 or n0 == 0:
        return None
    rk = rankdata(np.concatenate([pos, neg]))
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def judge_classes(label: np.ndarray, mask: np.ndarray, pitch_um: float = 2.4,
                  blank_min_mm: float = 0.3, zone_mm: float = 5.0) -> tuple[np.ndarray, np.ndarray]:
    """Text and blank classes exactly as the published judge builds them.

    text  = label AND mask
    blank = NOT label AND (distance to nearest label >= blank_min_mm) AND (distance <= zone_mm) AND mask

    The 0.3 mm gap keeps registration slop and stroke edges out of the negatives; the 5 mm zone keeps the negatives on the same
    written surface as the text (far-away papyrus differs in ways that have nothing to do with ink).
    """
    label = np.asarray(label, bool); mask = np.asarray(mask, bool)
    dist = distance_transform_edt(~label) * pitch_um / 1000.0
    text = label & mask
    blank = (~label) & (dist >= blank_min_mm) & (dist <= zone_mm) & mask
    return text, blank


def pixel_auc(score: np.ndarray, text: np.ndarray, blank: np.ndarray,
              subsample: float | None = 0.05, seed: int = 0) -> float | None:
    """Pixel AUC of ``score`` for text vs blank pixels.

    The published judge evaluates a fixed random 5 % of pixels (``np.random.default_rng(0).random(shape) < 0.05``) to keep the
    rank computation small; pass ``subsample=None`` to use every pixel. Neighbouring pixels are strongly correlated, so the number of
    pixels is NOT an effective sample size - put confidence intervals on crops (inkeval.stats), not on pixels.
    """
    score = np.asarray(score, np.float32)
    if subsample is not None and subsample < 1.0:
        sub = np.random.default_rng(seed).random(text.shape) < subsample
        return auc(score[text & sub], score[blank & sub])
    return auc(score[text], score[blank])


def _disk(r: int) -> np.ndarray:
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    return (yy * yy + xx * xx) <= r * r


def stroke_auc(score: np.ndarray, label: np.ndarray, mask: np.ndarray, pitch_um: float = 2.4, r_mm: float = 0.25,
               blank_mm: float = 0.5, max_n: int = 2000, seed: int = 0) -> tuple[float | None, int, int]:
    """Stroke test: AUC of the mean score over disks of radius ``r_mm`` lying inside strokes vs disks in blank papyrus.

    Ink disks: centre >= r_mm inside a stroke. Blank disks: centre >= blank_mm from any label. Both need >= 50 % of the disk in the
    mask. Centres sit on an r-spaced grid; at most ``max_n`` per class (seeded). Returns (auc, n_ink_disks, n_blank_disks); auc is
    None when either class has fewer than 20 disks.

    Why it exists: a 'letter' test built from connected label components is undefined when hand labels merge whole words into one
    component (measured: undefined on 2 of 7 evaluation crops under the final mask, 4 of 7 under the original one). The stroke test asks the same question - is the detector right when
    integrated over a stroke-sized support - and is defined wherever strokes and blank both exist.
    """
    score = np.asarray(score, np.float32); label = np.asarray(label, bool); mask = np.asarray(mask, bool)
    r = int(round(r_mm * 1000 / pitch_um))
    disk = _disk(r)
    din = distance_transform_edt(label) * pitch_um / 1000.0
    dout = distance_transform_edt(~label) * pitch_um / 1000.0
    g = np.zeros(label.shape, bool); g[r:-r:r, r:-r:r] = True
    ink_c = np.argwhere(g & (din >= r_mm)); blk_c = np.argwhere(g & (dout >= blank_mm))
    rng = np.random.default_rng(seed)

    def means(cs):
        if len(cs) > 4 * max_n:
            cs = cs[rng.choice(len(cs), 4 * max_n, replace=False)]
        vals = []
        for y, x in cs:
            m = mask[y - r:y + r + 1, x - r:x + r + 1] & disk
            if m.sum() < 0.5 * disk.sum():
                continue
            vals.append(float(score[y - r:y + r + 1, x - r:x + r + 1][m].mean()))
            if len(vals) >= max_n:
                break
        return np.array(vals)

    a, c = means(ink_c), means(blk_c)
    if len(a) < 20 or len(c) < 20:
        return None, len(a), len(c)
    return auc(a, c), len(a), len(c)


def local_stroke_auc(score: np.ndarray, label: np.ndarray, mask: np.ndarray, pitch_um: float = 2.4, r_mm: float = 0.25,
                     blank_mm: float = 0.5, near_mm: float = 1.5, max_ink: int = 1500,
                     seed: int = 0) -> tuple[float | None, int, int, int]:
    """Local stroke test L: each ink disk is compared only with blank disks whose centres lie within ``near_mm`` of it.

    L is the fraction of (ink, nearby blank) pairs in which the ink disk scores higher, weighted equally per ink disk. Any contrast
    varying on scales above ~2 mm cancels, so L separates letter-level information from regional brightness. Reading rule: a detector
    with stroke AUC well above 0.5 but L near 0.5 carries only regional information. Returns (L, n_ink, n_blank, n_paired).
    """
    score = np.asarray(score, np.float32); label = np.asarray(label, bool); mask = np.asarray(mask, bool)
    r = int(round(r_mm * 1000 / pitch_um)); near_px = near_mm * 1000 / pitch_um
    disk = _disk(r); need = 0.5 * disk.sum()
    din = distance_transform_edt(label) * pitch_um / 1000.0
    dout = distance_transform_edt(~label) * pitch_um / 1000.0
    g = np.zeros(label.shape, bool); g[r:-r:r, r:-r:r] = True
    rng = np.random.default_rng(seed)

    def collect(cs, cap):
        out_c, out_v = [], []
        if len(cs) > cap * 4:
            cs = cs[rng.choice(len(cs), cap * 4, replace=False)]
        for y, x in cs:
            m = mask[y - r:y + r + 1, x - r:x + r + 1] & disk
            if m.sum() < need:
                continue
            out_c.append((y, x)); out_v.append(float(score[y - r:y + r + 1, x - r:x + r + 1][m].mean()))
            if len(out_c) >= cap:
                break
        return np.array(out_c, float).reshape(-1, 2), np.array(out_v)

    ic, iv = collect(np.argwhere(g & (din >= r_mm)), max_ink)
    bc, bv = collect(np.argwhere(g & (dout >= blank_mm)), 6000)
    if len(ic) < 20 or len(bc) < 20:
        return None, 0, 0, 0
    tree = cKDTree(bc); wins = tot = 0.0; used = 0
    for i in range(len(ic)):
        nb = tree.query_ball_point(ic[i], near_px)
        if not nb:
            continue
        used += 1
        v = bv[nb]
        wins += float((iv[i] > v).sum() + 0.5 * (iv[i] == v).sum()) / len(v); tot += 1
    return (wins / tot if tot else None), len(ic), len(bc), used


def judge(score: np.ndarray, label: np.ndarray, mask: np.ndarray, pitch_um: float = 2.4,
          text: np.ndarray | None = None, blank: np.ndarray | None = None) -> dict:
    """All three published metrics for one crop. ``text``/``blank`` default to ``judge_classes(label, mask, pitch_um)``."""
    if text is None or blank is None:
        text, blank = judge_classes(label, mask, pitch_um)
    st, n_ink, n_blank = stroke_auc(score, label, mask, pitch_um)
    lo, li, lb, lp = local_stroke_auc(score, label, mask, pitch_um)
    return {"pixel_auc": pixel_auc(score, text, blank), "stroke_auc": st, "local_L": lo,
            "text_px": int(text.sum()), "blank_px": int(blank.sum()),
            "stroke_disks": {"ink": n_ink, "blank": n_blank}, "local_pairs": {"ink": li, "blank": lb, "paired": lp}}
