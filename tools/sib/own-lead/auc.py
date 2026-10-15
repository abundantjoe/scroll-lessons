# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN pixel AUC (DECL-P4-23 item 6(a), 6(c)). Numbers only.
AUC = Mann-Whitney probability P(score_ink > score_bg) + 0.5 P(tie), computed exactly from 256-bin histograms of the
u8 map values (u8 = clip(p*255), the display-domain values) at pixels with label coverage (sup) and mesh-valid.
Labels: ink = label > 0. Pooled over all given tiles (pixel AUC), plus per-tile values.
CLI (held-out F arms and NULL on the same pixels):
  auc.py --arrays <maps>/arrays --tiles "seg:r,c;..." --excl <p4-excl p4own dir> --out auc.json
Labels are read through build_patches.load_excl, which refuses any label shard overlapping X."""
import argparse
import json
import os

import numpy as np


def hist_pair(score_u8, ink, mask):
    s = score_u8[mask]
    y = ink[mask] >= 0.5          # ink = label ink fraction (0/1 when n_sub = 1)
    return (np.bincount(s[y], minlength=256).astype(np.float64),
            np.bincount(s[~y], minlength=256).astype(np.float64))


def auc_from_hist(hp, hn):
    npos, nneg = hp.sum(), hn.sum()
    if npos == 0 or nneg == 0:
        return None
    cneg_below = np.concatenate([[0.0], np.cumsum(hn)[:-1]])
    return float((hp * (cneg_below + 0.5 * hn)).sum() / (npos * nneg))


def auc(score_u8, ink, mask):
    return auc_from_hist(*hist_pair(score_u8, ink, mask))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arrays', required=True)
    ap.add_argument('--tiles', required=True)
    ap.add_argument('--excl', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    import own_common as C
    from build_patches import load_excl
    ex = load_excl(a.excl)
    short = {s.split('-', 1)[1]: s for s in C.SEGS}
    HP, HN = np.zeros(256), np.zeros(256)
    per = {}
    for tok in [t for t in a.tiles.split(';') if t]:
        seg, rc = tok.split(':')
        seg = short.get(seg, seg)
        r, c = (int(v) for v in rc.split(','))
        assert not C.in_x_zone(seg, r, c), 'X labels are never read here (DECL-P4-21-A1)'
        name = f'{seg}_r{r}_c{c}'
        z = np.load(os.path.join(a.arrays, f'{name}.npz'))
        T = C.tile_px(seg)
        ink, sup = ex.labels(seg, r * T, (r + 1) * T, c * T, (c + 1) * T)
        m = sup & z['valid'].astype(bool)
        hp, hn = hist_pair(z['u8'], ink, m)
        HP += hp
        HN += hn
        per[name] = dict(auc=auc_from_hist(hp, hn), n_ink=int(hp.sum()), n_bg=int(hn.sum()))
    res = dict(pixel_auc=auc_from_hist(HP, HN), n_ink=int(HP.sum()), n_bg=int(HN.sum()), per_tile=per,
               rule='Mann-Whitney on u8 map values at sup & mesh-valid px; ties 0.5', utc=C.utc())
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps(res))


if __name__ == '__main__':
    main()
