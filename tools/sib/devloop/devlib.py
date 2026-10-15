# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV-LOOP evaluator library (task devloop; RULES.md DECL-DEVLOOP). Numbers only: no image is ever
written for viewing, opened or displayed by this code.

Frames
------
* 9 um canvas: pixel (row, col) of the official vc_render_tifxyz render of the ORGANIZER 9 um mesh at
  --scale 1 (the organizer SV frame). Pixel P samples grid coordinate (P + 0.5) s (hercules.pipeline.canvas).
* 2.4 um canvas: the same for the organizer 2.4 um mesh; the official reference ink map
  (model 20260417190342) and the 2.4 um organizer SV live on it.
* Mapping (hercules.pipeline.canvas docstring, code-consistent offset 10.5 = 10 grid-px + the renderer's half
  pixel): per axis, c2 = (c9 + 10.5) * r - 10.5 with r = N2 / N9 (canvas extents of the SAME mesh on the two
  canvases), plus a per-window residual shift (dy2, dx2) measured on CT (``ct_residual_shift``), never on a model
  map, so registration is identical for every candidate checkpoint.

Metric (DECL-DEVLOOP): sigma_eq = hercules.metrics.pixel.sigma_eq of the text-order model map against the
registered 2.4 um reference resampled to the 9 um canvas (area average), valid pixels only, grid 0-0.60 mm in
0.025 mm, px_per_mm from the volume's metadata.json. Constraint: hercules.metrics.pixel.blob_f180 of the
NON-text-order map on DEV blank windows <= 0.0272.
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if os.path.join(_REPO, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(_REPO, 'src'))

from hercules.metrics import pixel as PX  # noqa: E402

OFFSET = 10.5
BLOB_BAR = 0.0272
SIGMA_MARGIN_MM = 0.05


# ---------------------------------------------------------------------------------------------------------------
# coordinate maps
# ---------------------------------------------------------------------------------------------------------------

def c9_to_c2(c9, r, offset=OFFSET):
    return (np.asarray(c9, dtype=np.float64) + offset) * r - offset


def c2_to_c9(c2, r, offset=OFFSET):
    return (np.asarray(c2, dtype=np.float64) + offset) / r - offset


def level_coord(c0, level):
    """Level-0 pixel coordinate -> pixel coordinate on a 2^level mean pyramid (pixel-centre convention)."""
    f = 2.0 ** level
    return (np.asarray(c0, dtype=np.float64) + 0.5) / f - 0.5


def _bilinear_operator(coords, n_src):
    """Sparse (len(coords) x n_src) matrix of exact 1-D linear-interpolation weights (float64); a coordinate
    outside [0, n_src - 1] gets zero weight and is reported as outside."""
    from scipy import sparse
    c = np.asarray(coords, np.float64)
    inside = (c >= 0) & (c <= n_src - 1)
    c0 = np.clip(np.floor(c), 0, max(n_src - 2, 0)).astype(np.int64)
    f = np.clip(c - c0, 0.0, 1.0)
    rows = np.repeat(np.arange(c.size), 2)
    cols = np.stack([c0, np.minimum(c0 + 1, n_src - 1)], 1).ravel()
    vals = np.stack([1 - f, f], 1).ravel() * np.repeat(inside, 2)
    return sparse.csr_matrix((vals, (rows, cols)), shape=(c.size, n_src)), inside


def ref_on_9(ref2, window, r_yx, shift2_yx=(0.0, 0.0), ref_origin_yx=(0, 0), sub=4, offset=OFFSET):
    """Area-average of the 2.4 um map ``ref2`` over the footprint of every 9 um pixel of ``window``: the mean of
    sub x sub exact bilinear samples evenly spaced over the pixel footprint. The canvas map is separable per axis,
    so this is out = Wy @ ref2 @ Wx^T with sparse averaged interpolation operators (float64, no quantisation).

    window        : (y0, x0, h, w) on the 9 um canvas.
    r_yx          : (r_rows, r_cols) = N2 / N9 per axis.
    shift2_yx     : residual (dy, dx) in 2.4 um pixels added to the mapped 2.4 um coordinate (CT registration).
    ref_origin_yx : 2.4 um canvas (row, col) of ref2[0, 0] (ref2 may be a crop of the canvas).
    Returns float32 (h, w) and a bool mask of pixels whose samples all fell inside ref2.
    """
    y0, x0, h, w = (int(v) for v in window)
    src = np.asarray(ref2, dtype=np.float64)
    H2, W2 = src.shape
    offs = (np.arange(sub) + 0.5) / sub - 0.5
    ops = []
    for axis, (n0, n, r, sh, org, nsrc) in enumerate(((y0, h, r_yx[0], shift2_yx[0], ref_origin_yx[0], H2),
                                                      (x0, w, r_yx[1], shift2_yx[1], ref_origin_yx[1], W2))):
        c9 = np.arange(n, dtype=np.float64) + n0
        M, ins = None, np.ones(n, bool)
        for o in offs:
            Mo, io = _bilinear_operator(c9_to_c2(c9 + o, float(r), offset) + sh - org, nsrc)
            M = Mo if M is None else M + Mo
            ins &= io
        ops.append((M / sub, ins))
    (Wy, iy), (Wx, ix) = ops
    out = (Wy @ (Wx @ src.T).T)
    return np.asarray(out, np.float32), iy[:, None] & ix[None, :]


# ---------------------------------------------------------------------------------------------------------------
# CT registration (candidate-independent)
# ---------------------------------------------------------------------------------------------------------------

def _ncc(a, b, m):
    x = a[m].astype(np.float64)
    y = b[m].astype(np.float64)
    if x.size < 200:
        return float('nan')
    x -= x.mean()
    y -= y.mean()
    d = math.sqrt(float(x @ x) * float(y @ y))
    return float(x @ y) / d if d > 0 else float('nan')


def _parabola(vm, v0, vp):
    den = vm - 2 * v0 + vp
    if not np.isfinite(den) or den >= 0:
        return 0.0
    return float(np.clip(0.5 * (vm - vp) / den, -0.5, 0.5))


def shift_search(ours, ref, valid_ours, valid_ref, max_shift=4):
    """Integer shift (dy, dx) maximising NCC of ours(y, x) vs ref(y + dy, x + dx), refined by a per-axis
    parabola. ``ref`` must carry a border of max_shift pixels around ``ours`` (shape + 2 * max_shift).
    Returns dict(shift=(dy, dx), ncc=best, ncc0=at zero, on_border=bool, grid)."""
    S = int(max_shift)
    h, w = ours.shape
    grid = np.full((2 * S + 1, 2 * S + 1), np.nan)
    for dy in range(-S, S + 1):
        for dx in range(-S, S + 1):
            rr = ref[S + dy:S + dy + h, S + dx:S + dx + w]
            vr = valid_ref[S + dy:S + dy + h, S + dx:S + dx + w]
            grid[dy + S, dx + S] = _ncc(ours, rr, valid_ours & vr)
    if not np.isfinite(grid).any():
        return dict(shift=(float('nan'), float('nan')), ncc=float('nan'), ncc0=float('nan'), on_border=True,
                    grid=grid)
    iy, ix = np.unravel_index(np.nanargmax(grid), grid.shape)
    on_border = iy in (0, 2 * S) or ix in (0, 2 * S)
    fy = fx = 0.0
    if not on_border:
        fy = _parabola(grid[iy - 1, ix], grid[iy, ix], grid[iy + 1, ix])
        fx = _parabola(grid[iy, ix - 1], grid[iy, ix], grid[iy, ix + 1])
    return dict(shift=(iy - S + fy, ix - S + fx), ncc=float(grid[iy, ix]), ncc0=float(grid[S, S]),
                on_border=bool(on_border), grid=grid)


def ct_residual_shift(ours9, valid9, ct2_on9_fn, sub_windows=3, max_shift=4, min_ncc=0.35):
    """Residual registration on CT, per window.

    ours9       : our render's surface slice (h, w) on the 9 um window (float; the model input frame).
    valid9      : its validity mask.
    ct2_on9_fn  : function (dy9, dx9, pad) -> (img, valid) giving the 2.4 um organizer SV surface slab resampled
                  onto the same 9 um window, grown by ``pad`` pixels on every side, after adding (dy9, dx9) 9 um px
                  to the mapped coordinate (used with 0, 0 here).
    The window is split into sub_windows^2 tiles; each tile's shift is found by :func:`shift_search`. The window
    shift is the median over tiles with NCC >= min_ncc and not on the search border.
    Returns dict with per-tile shifts, the median (dy, dx) in 9 um px, the MAD spread and the tile count."""
    h, w = ours9.shape
    S = int(max_shift)
    ct, vct = ct2_on9_fn(0.0, 0.0, S)
    tiles = []
    for i in range(sub_windows):
        for j in range(sub_windows):
            ys, ye = i * h // sub_windows, (i + 1) * h // sub_windows
            xs, xe = j * w // sub_windows, (j + 1) * w // sub_windows
            res = shift_search(ours9[ys:ye, xs:xe], ct[ys:ye + 2 * S, xs:xe + 2 * S], valid9[ys:ye, xs:xe],
                               vct[ys:ye + 2 * S, xs:xe + 2 * S], S)
            tiles.append(dict(tile=(ys, xs, ye - ys, xe - xs), shift=[float(v) for v in res['shift']],
                              ncc=res['ncc'], ncc0=res['ncc0'], on_border=res['on_border']))
    good = [t for t in tiles if np.isfinite(t['ncc']) and t['ncc'] >= min_ncc and not t['on_border']]
    if not good:
        return dict(tiles=tiles, n_good=0, shift9=None, mad9=None)
    sy = np.array([t['shift'][0] for t in good])
    sx = np.array([t['shift'][1] for t in good])
    med = (float(np.median(sy)), float(np.median(sx)))
    mad = (float(np.median(np.abs(sy - med[0]))), float(np.median(np.abs(sx - med[1]))))
    return dict(tiles=tiles, n_good=len(good), shift9=med, mad9=mad,
                ncc_median=float(np.median([t['ncc'] for t in good])))


# ---------------------------------------------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------------------------------------------

def px_per_mm(voxel_um):
    return 1000.0 / float(voxel_um)


def sigma_eq_window(model_u8, ref9, valid, voxel_um):
    """DECL-DEVLOOP metric on one window: hercules.metrics.pixel.sigma_eq, unchanged."""
    s, r, table = PX.sigma_eq(np.asarray(model_u8, np.float64), np.asarray(ref9, np.float64), px_per_mm(voxel_um),
                              valid=valid)
    return dict(sigma_eq_mm=float(s), r_best=float(r), table=[[float(a), float(b)] for a, b in table])


def sigma_eq_pooled(items, voxel_um, grid_mm=PX.SIGMA_EQ_GRID_MM):
    """Pooled sigma_eq over several windows of one scroll: for each grid sigma every window's reference is blurred
    on its own (Gaussian, BORDER_REFLECT exactly as hercules.metrics.pixel.sigma_eq), then ONE Pearson r is taken
    over the concatenated valid pixels of all windows. items: list of (model_u8, ref9, valid)."""
    ppm = px_per_mm(voxel_um)
    table = []
    ms = [np.asarray(m, np.float64)[np.asarray(v, bool)] for m, _, v in items]
    mcat = np.concatenate(ms) if ms else np.zeros(0)
    for s_mm in grid_mm:
        s_px = s_mm * ppm
        parts = []
        for _, ref, v in items:
            ref = np.asarray(ref, np.float64)
            b = ref if s_px == 0 else cv2.GaussianBlur(ref, (0, 0), s_px, borderType=cv2.BORDER_REFLECT)
            parts.append(b[np.asarray(v, bool)])
        table.append((float(s_mm), PX.pearson(mcat, np.concatenate(parts))))
    best = max(table, key=lambda t: (-np.inf if np.isnan(t[1]) else t[1]))
    return dict(sigma_eq_mm=best[0], r_best=best[1], table=[[a, b] for a, b in table])


def blob_f180_window(model_u8, valid, voxel_um):
    """hercules.metrics.pixel.blob_f180 with area_cm2 = n_valid x (voxel mm)^2 / 100 (DECL-D3-A3 item 5)."""
    v = np.asarray(valid, bool)
    area_cm2 = float(v.sum()) * (float(voxel_um) / 1000.0) ** 2 / 100.0
    return dict(blob_f180=PX.blob_f180(np.asarray(model_u8), area_cm2, valid=v), area_cm2=area_cm2)


def text_order_choice(auc_fwd, auc_rev):
    """Text order = the order whose base-map AUC against the reference labels is higher (chosen once per scroll
    with the base checkpoint, before any candidate; never revisited)."""
    if not (np.isfinite(auc_fwd) and np.isfinite(auc_rev)) or auc_fwd == auc_rev:
        return None
    return 'forward' if auc_fwd > auc_rev else 'reverse'


def finalist(per_scroll_sigma, sigma_crit_mm, blob_ok, margin_mm=SIGMA_MARGIN_MM, min_scrolls=3):
    """DECL-DEVLOOP FINALIST rule: sigma_eq <= sigma_crit + 0.05 mm on >= 3 DEV scrolls, with the blank
    constraint met. per_scroll_sigma: {scroll: sigma_eq_mm}. Returns dict(finalist, n_pass, passing)."""
    bar = float(sigma_crit_mm) + float(margin_mm)
    passing = sorted(s for s, v in per_scroll_sigma.items() if v is not None and np.isfinite(v) and v <= bar + 1e-9)
    ok = bool(blob_ok) and len(passing) >= int(min_scrolls)
    return dict(finalist=ok, n_pass=len(passing), passing=passing, bar_mm=bar, blob_ok=bool(blob_ok),
                n_scrolls=len(per_scroll_sigma))


def ref_labels(ref9, valid, ink=150.0, blank=100.0):
    """Reference-derived labels for the text-order AUC (as fold-A in D3): 1 ink (>= 150), 0 blank (<= 100),
    255 ignored."""
    lab = np.full(ref9.shape, 255, np.uint8)
    lab[(ref9 >= ink) & valid] = 1
    lab[(ref9 <= blank) & valid] = 0
    return lab
