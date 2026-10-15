"""Rank-mean ensembling, as used for the release's best detector E (port of scripts/ensemble_e.py).

Each map is rank-normalised inside the mask (so differently calibrated detectors become comparable without any fitted scaling),
the ranks are averaged with equal weight, and the result is smoothed by normalised convolution with a Gaussian.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

__all__ = ["rank_mean"]


def rank_mean(maps: Sequence[np.ndarray], mask: np.ndarray, sigma_mm: float = 0.08, pitch_um: float = 2.4) -> np.ndarray:
    """Equal-weight mean of per-map ranks inside ``mask``, smoothed at ``sigma_mm``; zero outside the mask. Returns float16.

    The release's E uses two maps (v8, GP-R1), sigma 0.08 mm = half the measured median stroke half-width, fixed before any result.
    """
    mask = np.asarray(mask, bool)
    if not mask.any():
        raise ValueError("empty mask")
    acc = np.zeros(mask.shape, np.float32)
    for x in maps:
        x = np.asarray(x, np.float32)
        r = np.zeros(mask.shape, np.float32)
        r[mask] = (rankdata(x[mask]) / mask.sum()).astype(np.float32)
        acc += r
    acc /= len(maps)
    s = sigma_mm * 1000 / pitch_um
    mf = mask.astype(np.float32)
    sm = gaussian_filter(acc * mf, s) / np.maximum(gaussian_filter(mf, s), 1e-3)
    return np.where(mask, sm, 0).astype(np.float16)
