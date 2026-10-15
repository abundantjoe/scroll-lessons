"""Synthetic scenes for tests and for checking that a metric behaves as claimed.

A scene is a set of letter-like strokes (thick line segments) on a background, with a detector score that is a controllable mix of
true ink signal, fibre-like anisotropic texture and a large-scale brightness gradient. It lets the tests verify, for example, that the
local stroke test L cancels a regional gradient while the global stroke AUC does not.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

__all__ = ["scene"]


def _strokes(shape, n, width_px, rng):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    lab = np.zeros(shape, bool)
    for _ in range(n):
        y0, x0 = rng.uniform(0.1, 0.9) * h, rng.uniform(0.1, 0.9) * w
        ang = rng.uniform(0, np.pi); ln = rng.uniform(0.08, 0.2) * min(h, w)
        y1, x1 = y0 + ln * np.sin(ang), x0 + ln * np.cos(ang)
        dy, dx = y1 - y0, x1 - x0
        t = np.clip(((yy - y0) * dy + (xx - x0) * dx) / (dy * dy + dx * dx), 0, 1)
        d2 = (yy - (y0 + t * dy)) ** 2 + (xx - (x0 + t * dx)) ** 2
        lab |= d2 <= (width_px / 2) ** 2
    return lab


def scene(shape=(800, 800), n_strokes=40, width_px=60, signal=1.0, texture=1.0, gradient=0.0, seed=0):
    """Return (score, label, mask). ``signal`` scales the ink response, ``texture`` the fibre noise, ``gradient`` a left-to-right ramp."""
    rng = np.random.default_rng(seed)
    label = _strokes(shape, n_strokes, width_px, rng)
    noise = rng.normal(size=shape)
    fibre = gaussian_filter(noise, (1.5, 12.0))          # anisotropic, papyrus-like
    fibre /= fibre.std() + 1e-9
    ramp = np.linspace(-1, 1, shape[1])[None, :] * np.ones((shape[0], 1))
    score = signal * gaussian_filter(label.astype(float), width_px / 6) + texture * fibre + gradient * ramp
    mask = np.ones(shape, bool)
    holes = rng.random(shape) < 2e-4
    mask &= ~(gaussian_filter(holes.astype(float), 6) > 0.01)   # small damage holes, like the grain mask
    return score.astype(np.float32), label, mask
