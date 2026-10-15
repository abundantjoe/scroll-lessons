"""The patch grid of villa flat ink inference and which output rows inherit a blank-containing patch.

villa (vesuvius.ink_detection.inference.infer, commit 41701aa) slides square patches of `tile` px with `stride`
(overlap 0.5 -> stride 64 for 128 px): positions range(0, L - tile + 1, stride), plus L - tile appended when it is
not already on the grid. Outputs are blended with a 2-D Hann window (max 1, floor 1e-3).
"""
import numpy as np


def positions(L, tile=128, stride=64):
    """Patch start offsets along one axis of length L (villa's _sliding_positions_1d rule)."""
    if L <= tile:
        return [0]
    xs = list(range(0, L - tile + 1, stride))
    if xs[-1] != L - tile:
        xs.append(L - tile)
    return xs


def hann1d(tile=128, floor=1e-3):
    w = np.hanning(tile).astype(np.float64)
    w /= w.max()
    return np.maximum(w, floor)


def blank_share(valid_rows, tile=128, stride=64):
    """valid_rows: (H,) bool for one column. For every row, the Hann-weighted share of the patches covering it that
    contain at least one blank row. Rows near the centre of an edge patch inherit that patch's output."""
    v = np.asarray(valid_rows, bool)
    H = v.size
    w = hann1d(tile)
    num, den = np.zeros(H), np.zeros(H)
    for p in positions(H, tile, stride):
        seg = slice(p, min(p + tile, H))
        n = seg.stop - seg.start
        has_blank = not v[seg].all()
        den[seg] += w[:n]
        if has_blank:
            num[seg] += w[:n]
    return num / np.maximum(den, 1e-12)
