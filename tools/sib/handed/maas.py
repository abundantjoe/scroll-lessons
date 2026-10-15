# Provenance: Project HERCULES | owner the owner | [id removed]
"""Column-slant statistic of a binary ink-label layout (supplementary,
reader-free handedness check).

Prior (papyrological, stated as an assumption, not a law of physics): Maas's
law - in bookrolls each line tends to begin slightly to the LEFT of the line
above, so column edges lean like '/' (top to the right of the bottom) in an
unmirrored image. The slant of a parallelogram is unchanged by a 180 degree
rotation and reversed by a mirror, so its sign tests handedness independently
of up/down.

Statistic: in an image whose rows are (approximately) along the text lines,
split the ink into column blocks at wide ink-free x gaps, estimate the local
line direction per block (projection-profile maximisation over small
angles), rotate the block so lines are horizontal, find text lines as peaks
of the row profile, and regress each line's left end x_L (and right end x_R)
on its row y (Theil-Sen). slope < 0 (x decreases going down, y down) is the
Maas direction for an unmirrored image. Only numbers are returned.
"""

from __future__ import annotations

import math

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d, label as cc_label
from scipy.signal import find_peaks


def theil_sen(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    i, j = np.triu_indices(x.size, 1)
    dx = x[j] - x[i]
    ok = np.abs(dx) > 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else math.nan


def rotate(img: np.ndarray, deg: float) -> np.ndarray:
    h, w = img.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0)
    return cv2.warpAffine(img.astype(np.float32), M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0.0)


def line_angle(block: np.ndarray, max_deg: float = 12.0, step: float = 0.25) -> tuple[float, float]:
    """Angle (deg, cv2 rotation sense) that makes lines horizontal: maximises
    the variance of the row profile. Returns (angle, contrast ratio)."""
    best, best_v, vals = 0.0, -1.0, []
    for a in np.arange(-max_deg, max_deg + 1e-9, step):
        prof = rotate(block, a).sum(1)
        v = float(np.var(prof))
        vals.append(v)
        if v > best_v:
            best, best_v = float(a), v
    return best, best_v / (float(np.median(vals)) + 1e-12)


def column_blocks(ink: np.ndarray, min_gap: int, min_width: int) -> list[tuple[int, int]]:
    prof = gaussian_filter1d(ink.sum(0).astype(float), 2)
    occ = prof > 0.02 * prof.max() if prof.max() > 0 else prof > 0
    blocks, x = [], 0
    W = ink.shape[1]
    while x < W:
        if not occ[x]:
            x += 1
            continue
        x0 = x
        gap = 0
        while x < W and gap < min_gap:
            gap = gap + 1 if not occ[x] else 0
            x += 1
        x1 = x - gap
        if x1 - x0 >= min_width:
            blocks.append((x0, x1))
    return blocks


def block_slant(block: np.ndarray, line_px: float, *, min_lines: int = 6) -> dict:
    """Slant of one column block. ``line_px`` = expected line pitch (px)."""
    ang, contrast = line_angle(block)
    b = rotate(block, ang) > 0.5
    prof = gaussian_filter1d(b.sum(1).astype(float), max(1.0, line_px / 6))
    pk, _ = find_peaks(prof, distance=max(2, int(0.6 * line_px)), height=0.15 * prof.max() if prof.max() else 0)
    xs_l, xs_r, ys = [], [], []
    half = max(1, int(0.3 * line_px))
    for p in pk:
        band = b[max(0, p - half):p + half + 1].any(0)
        cols = np.nonzero(band)[0]
        if cols.size == 0:
            continue
        # ignore isolated specks: keep runs from the first/last substantial ink cluster
        lab, n = cc_label(band)
        sizes = np.bincount(lab)[1:]
        big = np.nonzero(sizes >= max(2, int(0.15 * line_px)))[0] + 1
        if big.size == 0:
            continue
        keep = np.isin(lab, big)
        cols = np.nonzero(keep)[0]
        xs_l.append(cols.min())
        xs_r.append(cols.max())
        ys.append(p)
    out = dict(line_angle_deg=ang, profile_contrast=contrast, n_lines=len(ys))
    if len(ys) < min_lines:
        out.update(slope_left=math.nan, slope_right=math.nan)
        return out
    ys = np.array(ys, float)
    out.update(slope_left=theil_sen(ys, np.array(xs_l, float)), slope_right=theil_sen(ys, np.array(xs_r, float)),
               slant_left_deg=math.degrees(math.atan(theil_sen(ys, np.array(xs_l, float)))),
               slant_right_deg=math.degrees(math.atan(theil_sen(ys, np.array(xs_r, float)))))
    return out


def layout_slant(ink: np.ndarray, line_px: float, *, min_gap_px: int | None = None, min_width_px: int | None = None) -> dict:
    """Column slants over a whole label image (rows ~ text lines)."""
    ink = (np.asarray(ink) > 0).astype(np.float32)
    min_gap = min_gap_px or int(1.5 * line_px)
    min_w = min_width_px or int(6 * line_px)
    blocks = column_blocks(ink, min_gap, min_w)
    res = []
    for x0, x1 in blocks:
        rows = np.nonzero(ink[:, x0:x1].any(1))[0]
        if rows.size == 0:
            continue
        pad = int(line_px)
        sub = ink[max(0, rows.min() - pad):rows.max() + pad + 1, max(0, x0 - pad):x1 + pad]
        r = block_slant(sub, line_px)
        r.update(x0=int(x0), x1=int(x1))
        res.append(r)
    good = [r for r in res if r["n_lines"] >= 6 and np.isfinite(r["slope_left"])]
    sl = np.array([r["slope_left"] for r in good])
    sr = np.array([r["slope_right"] for r in good])
    return dict(blocks=res, n_blocks=len(res), n_measured=len(good),
                n_left_neg=int((sl < 0).sum()), n_left_pos=int((sl > 0).sum()),
                n_right_neg=int((sr < 0).sum()), n_right_pos=int((sr > 0).sum()),
                median_slant_left_deg=float(np.degrees(np.arctan(np.median(sl)))) if sl.size else math.nan,
                median_slant_right_deg=float(np.degrees(np.arctan(np.median(sr)))) if sr.size else math.nan)


def synthetic_layout(n_cols=3, n_lines=24, line_px=12, col_w=150, gap=60, slant_deg=3.0, seed=0, jitter=1.5):
    """Binary layout of word-like ink runs with Maas slant (unmirrored:
    each line starts further LEFT going down when slant_deg > 0)."""
    rng = np.random.default_rng(seed)
    H = n_lines * line_px + 4 * line_px
    W = n_cols * (col_w + gap) + 2 * gap
    img = np.zeros((H, W), np.uint8)
    t = math.tan(math.radians(slant_deg))
    for c in range(n_cols):
        xc = gap + c * (col_w + gap) + n_lines * line_px * t
        for i in range(n_lines):
            y = 2 * line_px + i * line_px
            x0 = int(round(xc - i * line_px * t + rng.normal(0, jitter)))
            length = col_w - int(abs(rng.normal(0, 4)))
            x = x0
            while x < x0 + length:
                wl = int(rng.integers(10, 40))
                img[y - line_px // 4:y + line_px // 4, x:min(x + wl, x0 + length)] = 1
                x += wl + int(rng.integers(3, 7))
    return img
