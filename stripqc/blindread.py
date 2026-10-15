"""Blind reads of ink images with hidden controls.

A read counts only if readers, blind to which image is which, detect HIDDEN POSITIVES (known letters in the SAME
format as the unknowns) and reject HIDDEN NEGATIVES (the same surface moved 8 vox outward, so the same pipeline and
format; without the fill it shows no letter-located signal). Report per-reader AUC on the controls before reading
anything into the unknowns, and compare it with a colour-only baseline (scripts/blindread_colour_baseline.py): if the
amount of colour alone separates the controls as well, the read shows no letter recognition. Negatives should carry a
comparable amount of colour; nearly empty negatives let colour alone separate the classes.
"""
import hashlib

import numpy as np

from .score import auc


def coded_order(names, salt='stripqc'):
    """Fixed pseudo-random order -> {code '01'...: name}. Deterministic, independent of input order."""
    ordered = sorted(names, key=lambda n: hashlib.sha256((salt + n).encode()).hexdigest())
    return {f'{i + 1:02d}': n for i, n in enumerate(ordered)}


def reader_auc(confidence, key, is_pos, is_neg):
    """confidence: {code: 0..1} of one reader; key: {code: name}; is_pos/is_neg: predicates on name -> AUC or None."""
    pos = [confidence[c] for c, n in key.items() if c in confidence and is_pos(n)]
    neg = [confidence[c] for c, n in key.items() if c in confidence and is_neg(n)]
    if not pos or not neg:
        return None
    return auc(np.array(pos + neg), np.array([True] * len(pos) + [False] * len(neg)))


def roc_points(pos, neg):
    """ROC curve points (fpr, tpr) for scores of positives and negatives (thresholds at every distinct score)."""
    s = np.unique(np.concatenate([pos, neg]))[::-1]
    pts = [(0.0, 0.0)]
    for t in s:
        pts.append((float((np.asarray(neg) >= t).mean()), float((np.asarray(pos) >= t).mean())))
    pts.append((1.0, 1.0))
    return pts
