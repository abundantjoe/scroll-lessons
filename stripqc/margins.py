"""Blank render margins and the edge bands they cause: measurement helpers.

A pixel of a vc_render_tifxyz render is valid when any CT layer is non-zero (ctlayers/render > 0). Do NOT use ink p > 0
as validity: villa ink maps are non-zero over the blank margin too (about p = 0.31 there).
"""
import numpy as np


def valid_from_render(A):
    """(D, H, W) render or (k, H, W) CT layers -> (H, W) bool."""
    return (np.asarray(A) > 0).any(0)


def valid_from_overlay(rgb, thresh=30):
    """RGB overlay where invalid pixels are black -> (H, W) bool."""
    return np.asarray(rgb, np.float32).sum(-1) > thresh


def column_edges(valid):
    """First and last valid row per column (-1 / -1 for empty columns)."""
    H = valid.shape[0]
    has = valid.any(0)
    first = np.where(has, valid.argmax(0), -1)
    last = np.where(has, H - 1 - valid[::-1].argmax(0), -1)
    return first, last


def edge_distance(valid):
    """Per valid pixel: distance (rows) to its column's nearest valid edge; -1 elsewhere."""
    first, last = column_edges(valid)
    rows = np.arange(valid.shape[0])[:, None]
    d = np.minimum(rows - first[None, :], last[None, :] - rows)
    d[~valid] = -1
    return d


def band_mid(ink, valid, band=(20, 80), mid=80):
    """Mean ink in the edge band (band[0] <= distance <= band[1]) and in the strip middle (distance > mid)."""
    d = edge_distance(valid)
    b, m = (d >= band[0]) & (d <= band[1]), d > mid
    vb = float(ink[b].mean()) if b.any() else float('nan')
    vm = float(ink[m].mean()) if m.any() else float('nan')
    return dict(band=vb, mid=vm, ratio=(vb / vm) if (np.isfinite(vm) and vm > 0) else None, n_band=int(b.sum()), n_mid=int(m.sum()))


def top_margin_experiment(ink, valid, rows=(50, 90), window=129, classes=(30, 10), tol=2, min_cols=129):
    """Natural experiment inside one strip. Columns whose blank TOP margin is constant (within tol) over a centred
    window of `window` columns are split into margin classes (e.g. 30 vs 10 blank rows). The mean ink at the same
    fixed render rows is compared between classes: a physical feature sits at fixed node rows and would not depend on
    the margin; a margin artifact does. -> {class: (mean ink, n columns)}."""
    first, _ = column_edges(valid)
    W = valid.shape[1]
    h = window // 2
    out = {}
    for c in classes:
        isc = (np.abs(first - c) <= tol) & (first >= 0)
        cs = np.cumsum(np.concatenate([[0], isc.astype(int)]))
        lo, hi = np.clip(np.arange(W) - h, 0, W), np.clip(np.arange(W) + h + 1, 0, W)
        homo = isc & ((cs[hi] - cs[lo]) == (hi - lo))
        cols = np.flatnonzero(homo)
        if cols.size < min_cols:
            out[c] = (float('nan'), int(cols.size))
            continue
        sub = ink[rows[0]:rows[1]][:, cols]
        v = valid[rows[0]:rows[1]][:, cols]
        out[c] = (float(sub[v].mean()) if v.any() else float('nan'), int(cols.size))
    return out
