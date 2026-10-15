"""Score strip ink maps against a full-context reference and labelled letter boxes (positive control).

Frames: a render pixel (i, j) of a surface cropped from a source tifxyz at node (src_row0, src_col0) sits at raw
source-frame pixel (i + 20 src_row0, j + 20 src_col0) (tifxyz scale 0.05 = 20 px per node; the renderer's half-pixel
node offset is common to all arms and the boxes; scripts/control_strips/box_shift_check.py moves the boxes by +-20 px). Letter boxes
are [x0, y0, x1, y1] in that raw frame.

Metrics over S = pixels valid in the arm AND in REF, inside the scored rows (strong = p > T, T = 0.55):
  f_in / f_out   strong fraction inside / outside the letter boxes;  E = f_in / max(f_out, 1e-4)
  recall         |arm strong & REF strong & box| / |REF strong & box|
  r              Pearson r of arm vs REF p over S
  coverage       letter-box px in the scored rows that the arm scores / all letter-box px there (REF frame)
  band           strong fraction outside the boxes in rows 20-80 px from the column's valid edge, arm and REF
  recall CI      letter-cluster bootstrap (letters resampled with replacement)
"""
import json
import os

import numpy as np
from scipy.stats import rankdata

T = 0.55


def load_arm(work_dir, depth, row_offset=0):
    """A batch_ink work dir -> dict(E, valid, r0, c0) or None when incomplete. row_offset: node rows to add when the
    arm's tifxyz itself starts below source row 0 (e.g. an extrapolation-padded copy starting at row a - 2)."""
    e = os.path.join(work_dir, f'ens_d{depth}.tif')
    pj = os.path.join(work_dir, 'prep.json')
    cj = os.path.join(work_dir, 'ctlayers_31-35.tif')
    if not (os.path.exists(e) and os.path.exists(pj) and os.path.exists(cj)):
        return None
    import tifffile
    crop = json.load(open(pj))['crop']
    E = tifffile.imread(e).astype(np.float32) / 255.0
    valid = (tifffile.imread(cj) > 0).any(0)   # CT validity; ink maps are non-zero over the blank margin too
    return dict(E=E, valid=valid, r0=20 * (crop['src_row0'] + row_offset), c0=20 * crop['src_col0'])


def letter_ids(boxes, r0, c0, H, W):
    """(H, W) int map: index of the (first) letter box covering each pixel, -1 elsewhere."""
    L = np.full((H, W), -1, np.int32)
    for k, (x0, y0, x1, y1) in enumerate(boxes):
        a, b = max(int(round(y0 - r0)), 0), min(int(round(y1 - r0)), H)
        c, e = max(int(round(x0 - c0)), 0), min(int(round(x1 - c0)), W)
        if a < b and c < e:
            sub = L[a:b, c:e]
            sub[sub < 0] = k
    return L


def _edge_dist(valid):
    H = valid.shape[0]
    has = valid.any(0)
    first = np.where(has, valid.argmax(0), 0)
    last = np.where(has, H - 1 - valid[::-1].argmax(0), -1)
    rows = np.arange(H)[:, None]
    d = np.minimum(rows - first[None, :], last[None, :] - rows)
    d[~valid] = -1
    return d


def match(arm, ref, t0, t1, boxes):
    """Pixels of `arm` in source node rows [t0, t1) valid in arm and REF -> arrays for metrics()."""
    H, W = arm['E'].shape
    yy = np.arange(H) + arm['r0']
    xx = np.arange(W) + arm['c0']
    ry, rx = yy - ref['r0'], xx - ref['c0']
    rows_ok = (yy >= 20 * t0) & (yy < 20 * t1) & (ry >= 0) & (ry < ref['E'].shape[0])
    cols_ok = (rx >= 0) & (rx < ref['E'].shape[1])
    m = arm['valid'] & rows_ok[:, None] & cols_ok[None, :]
    ii, jj = np.nonzero(m)
    keep = ref['valid'][ry[ii], rx[jj]]
    ii, jj = ii[keep], jj[keep]
    lid = letter_ids(boxes, arm['r0'], arm['c0'], H, W)[ii, jj]
    ed = _edge_dist(arm['valid'])[ii, jj]
    # coverage denominator: letter-box px of REF inside the target rows and the arm's column span
    RH, RW = ref['E'].shape
    rl = letter_ids(boxes, ref['r0'], ref['c0'], RH, RW) >= 0
    tr = ((np.arange(RH) + ref['r0']) >= 20 * t0) & ((np.arange(RH) + ref['r0']) < 20 * t1)
    tc = ((np.arange(RW) + ref['c0']) >= arm['c0']) & ((np.arange(RW) + ref['c0']) < arm['c0'] + W)
    nbt = int((rl & ref['valid'] & tr[:, None] & tc[None, :]).sum())
    return dict(pa=arm['E'][ii, jj], pr=ref['E'][ry[ii], rx[jj]], lid=lid, ed=ed, n_box_target=nbt)


def auc(p, y):
    """Tie-aware ROC AUC of scores p for binary labels y (Mann-Whitney)."""
    p, y = np.asarray(p, float), np.asarray(y, bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return None
    r = rankdata(p)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _pearson(a, b):
    if a.size < 3 or a.std() < 1e-6 or b.std() < 1e-6:   # guard: constant maps give NaN, which is invalid JSON
        return None
    return float(np.corrcoef(a, b)[0, 1])


def metrics(parts, thresh=T):
    """Pooled metrics over a list of match() results (one per strip). None-safe, NaN-free."""
    if not parts:
        return None
    cat = {k: np.concatenate([p[k] for p in parts]) for k in ('pa', 'pr', 'lid', 'ed')}
    pa, pr, lid, ed = cat['pa'], cat['pr'], cat['lid'], cat['ed']
    if pa.size == 0:   # no pixel valid in both the arm and REF inside the scored rows
        return None
    box = lid >= 0
    sa, sr = pa > thresh, pr > thresh
    f_in = float(sa[box].mean()) if box.any() else None
    f_out = float(sa[~box].mean()) if (~box).any() else None
    den = int((sr & box).sum())
    band = (~box) & (ed >= 20) & (ed <= 80)
    k = float(sr.mean())
    tq = float(np.quantile(pa, 1 - k)) if k > 0 else 1.0
    out = dict(n_px=int(pa.size), n_box_px=int(box.sum()),
               coverage=round(int(box.sum()) / max(sum(p['n_box_target'] for p in parts), 1), 4),
               f_in=f_in, f_out=f_out, E=(f_in / max(f_out, 1e-4)) if f_in is not None and f_out is not None else None,
               ref_f_in=float(sr[box].mean()) if box.any() else None, ref_f_out=float(sr[~box].mean()) if (~box).any() else None,
               recall=float((sa & sr & box).sum()) / den if den else None, ref_strong_box_px=den,
               r=_pearson(pa, pr),
               band_f055_out=float(sa[band].mean()) if band.any() else None,
               band_ref_f055_out=float(sr[band].mean()) if band.any() else None,
               auc_box=auc(pa, box), ref_auc_box=auc(pr, box),
               recall_matched_rate=float(((pa >= tq) & sr & box).sum()) / den if den else None,
               p99=float(np.quantile(pa, 0.99)), ref_p99=float(np.quantile(pr, 0.99)))
    return out


def bootstrap_recall(parts, n=2000, seed=0, thresh=T):
    """95 % CI of pooled recall by resampling letters (clusters) with replacement. -> (lo, hi, n_letters)."""
    pa = np.concatenate([p['pa'] for p in parts])
    pr = np.concatenate([p['pr'] for p in parts])
    lid = np.concatenate([p['lid'] for p in parts])
    m = lid >= 0
    letters = np.unique(lid[m])
    if letters.size < 2:
        return None, None, int(letters.size)
    hit = np.array([((pa > thresh) & (pr > thresh) & (lid == L)).sum() for L in letters], float)
    den = np.array([((pr > thresh) & (lid == L)).sum() for L in letters], float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, letters.size, size=(n, letters.size))
    d = den[idx].sum(1)
    rec = np.where(d > 0, hit[idx].sum(1) / np.maximum(d, 1), np.nan)
    rec = rec[np.isfinite(rec)]
    if rec.size == 0:   # no letter has REF-strong pixels
        return None, None, int(letters.size)
    return float(np.quantile(rec, 0.025)), float(np.quantile(rec, 0.975)), int(letters.size)
