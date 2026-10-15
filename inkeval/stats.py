"""Uncertainty and controls at the right unit of replication.

Pixels in a crop are spatially correlated, so a pixel count is not a sample size. The unit here is the crop (and, honestly, the
segment). With 7 crops a percentile bootstrap is wide; that width is the truthful statement of what the data support.
"""
from __future__ import annotations

import itertools
import math
from typing import Callable, Sequence

import numpy as np

from .metrics import auc

__all__ = ["bootstrap_ci", "paired_bootstrap", "label_swap_null", "trunc"]


def bootstrap_ci(values: Sequence[float], resamples: int = 10000, seed: int = 0, level: float = 0.95) -> dict:
    """Percentile bootstrap of the mean over units (crops). Returns {'mean', 'ci': [lo, hi], 'n'}."""
    x = np.asarray(values, float)
    if x.size == 0:
        raise ValueError("no values")
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, x.size, size=(resamples, x.size))].mean(axis=1)
    a = (1 - level) / 2 * 100
    return {"mean": float(x.mean()), "ci": [float(np.percentile(m, a)), float(np.percentile(m, 100 - a))], "n": int(x.size)}


def paired_bootstrap(a: Sequence[float], b: Sequence[float], resamples: int = 10000, seed: int = 0, level: float = 0.95) -> dict:
    """Bootstrap of the mean paired difference a - b over the same units, plus how many units favour a."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    if a.shape != b.shape:
        raise ValueError("paired inputs must have the same length")
    d = a - b
    out = bootstrap_ci(d, resamples, seed, level)
    out["positive_units"] = int((d > 0).sum())
    return out


def label_swap_null(scores: Sequence[np.ndarray], texts: Sequence[np.ndarray], blanks: Sequence[np.ndarray],
                    masks: Sequence[np.ndarray] | None = None, subsample: float | None = 0.05, seed: int = 0,
                    metric: Callable | None = None) -> dict:
    """Negative control: judge each crop's score against every OTHER crop's text/blank classes (all ordered pairs).

    Both spatial structures - the detector's texture response and the label's letter layout - are preserved; only their
    correspondence is broken. A detector that reads letters should sit near 0.5 here; a large deviation means the AUC can be produced
    by spatial statistics alone. Requires crops of identical shape.
    """
    n = len(scores)
    if n < 2:
        raise ValueError("need at least two crops")
    if len(texts) != n or len(blanks) != n or (masks is not None and len(masks) != n):
        raise ValueError("give one score, text, blank (and mask) per crop")
    shapes = sorted({np.shape(x) for x in (*scores, *texts, *blanks, *(masks if masks is not None else ()))})
    if len(shapes) != 1:
        raise ValueError(f"all crops must have the same shape; got {shapes}")
    sub = None
    if subsample is not None and subsample < 1.0:
        sub = np.random.default_rng(seed).random(texts[0].shape) < subsample
    vals = []
    for i, j in itertools.permutations(range(n), 2):
        s = np.asarray(scores[i], np.float32)
        mi = np.ones(s.shape, bool) if masks is None else np.asarray(masks[i], bool)
        t = texts[j] & mi; b = blanks[j] & mi
        if sub is not None:
            t = t & sub; b = b & sub
        v = metric(s, t, b) if metric else auc(s[t], s[b])
        if v is not None:
            vals.append(v)
    if not vals:
        raise ValueError("no ordered pair has both text and blank pixels (after mask and subsample); check the masks, labels and pitch_um")
    v = np.array(vals)
    return {"pairs": int(v.size), "mean": float(v.mean()), "min": float(v.min()), "max": float(v.max()),
            "mean_abs_dev_from_half": float(np.abs(v - 0.5).mean())}


def trunc(x: float, digits: int = 3) -> float:
    """Truncate toward zero - never rounds a number up in magnitude (the release's reporting rule).

    The scaled value is first rounded at 6 decimals so that floating-point noise does not cut a digit off an exact value
    (-0.00599999999999999 is -0.006, not -0.005); a true value within 1e-6 of a step of the last digit is treated as on it."""
    f = 10 ** digits
    return math.copysign(math.trunc(round(x * f, 6)) / f, x)        # keeps the sign of a value that truncates to zero (-0.000)
