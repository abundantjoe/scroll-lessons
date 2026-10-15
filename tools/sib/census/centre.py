# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 2b: centre curve per volume and its reliability.

Centre = official umbilicus of the same volume where one exists, else the
level-4 CT-mask centroid per slice, Gaussian-smoothed in z (sigma 256 level-0
vox, as hercules.pipeline.centre.mask_centroid_curve). Shape metrics from
mask_shape.py decide the reliability flag; where an umbilicus exists the
centroid and the deepest-interior-point estimators are scored against it.
"""
from __future__ import annotations

import json
import os

import numpy as np

SIGMA = 256.0


def gauss_smooth(z, v, sigma=SIGMA):
    out = np.empty_like(v)
    for i, zi in enumerate(z):
        w = np.exp(-0.5 * ((z - zi) / sigma) ** 2)
        out[i] = np.sum(w * v) / np.sum(w)
    return out


def load_shape(mask_dir, scroll):
    d = dict(np.load(os.path.join(mask_dir, f"{scroll}_shape_L4.npz")))
    return d


def scroll_z_extent(sh, frac=0.25):
    """Level-0 z extent of slices whose filled-mask area is >= frac x the median
    non-empty area (drops caps and empty end slices)."""
    a = sh["area"]
    ne = a[a > 0]
    thr = frac * np.median(ne)
    ok = np.nonzero(a >= thr)[0]
    return float(sh["z"][ok[0]]), float(sh["z"][ok[-1]]), float(thr)


MEDWIN = 65  # level-4 slices (1040 level-0 vox) running median before the Gaussian


def robust_smooth(z, v, win=MEDWIN, sigma=SIGMA):
    """Running median (removes single-slice mask flicker) then Gaussian in z."""
    from scipy.ndimage import median_filter

    return gauss_smooth(z, median_filter(v, size=win, mode="nearest"), sigma)


def centroid_curve(sh, robust=True):
    ok = np.isfinite(sh["cx"]) & (sh["area"] >= 0.25 * np.median(sh["area"][sh["area"] > 0]))
    z = sh["z"][ok]
    f = robust_smooth if robust else gauss_smooth
    return z, f(z, sh["cx"][ok]), f(z, sh["cy"][ok]), ok


def dt_curve(sh, ok):
    z = sh["z"][ok]
    return z, gauss_smooth(z, sh["dtx"][ok]), gauss_smooth(z, sh["dty"][ok])


def umbilicus_curve(path):
    d = json.load(open(path))
    cp = sorted(d["control_points"], key=lambda p: p["z"])
    return (np.array([p["z"] for p in cp], float), np.array([p["x"] for p in cp], float),
            np.array([p["y"] for p in cp], float), d["metadata"]["volume"])


def interp_curve(zc, xc, yc, z):
    return np.interp(z, zc, xc), np.interp(z, zc, yc)


def reliability(sh, ok):
    """Per-volume shape metrics over the scroll z extent."""
    a = sh["axis_ratio"][ok]
    s = sh["solidity"][ok]
    zr, xr, yr = sh["z"][ok], sh["cx"][ok], sh["cy"][ok]
    xs, ys = gauss_smooth(zr, xr), gauss_smooth(zr, yr)
    jitter = np.hypot(xr - xs, yr - ys)
    # offset of the smoothed centroid from the deepest interior point, relative to r_eq
    dz, dx, dy = dt_curve(sh, ok)
    off = np.hypot(xs - dx, ys - dy) / sh["r_eq"][ok]
    q = lambda v, p: float(np.nanpercentile(v, p))
    return dict(axis_ratio_median=q(a, 50), axis_ratio_p10=q(a, 10), solidity_median=q(s, 50),
                solidity_p10=q(s, 10), centroid_jitter_rms_vox=float(np.sqrt(np.nanmean(jitter ** 2))),
                centroid_minus_dtmax_over_req_median=q(off, 50), centroid_minus_dtmax_over_req_p90=q(off, 90),
                r_eq_median_vox=q(sh["r_eq"][ok], 50), n_slices=int(ok.sum()))
