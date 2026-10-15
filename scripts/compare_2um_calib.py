#!/usr/bin/env python
"""B-2UM calibration comparison: our 2.4 um map of the w028 calibration crop against the team's published map of the
same pixels. Ours: uint8 TIFF written by run_2um.py (prob*255) over the calib.zarr array frame (4224^2, array origin
(28032, 20736) of the level-0 w028 surface volume); team: team_pred_crop.npy (uint8, same 4224^2 frame). A border of
--border px is dropped (tile edge effects), and only the declared 1 cm^2 window (offset (48, 64), 4160 px) is scored.
Reports Pearson, AUC of ours against team > 0.5, means, and the 'unit-rule levels': the mean of our map over text
pixels (team map pooled 4x4 >= 0.40) and over blank pixels (pooled <= 0.25), the same thresholds as the J-w028 judge.
Usage: compare_2um_calib.py <ours.tif> <team_pred_crop.npy> <out.json> [--y0 48 --x0 64 --size 4160 --border 64]"""
import argparse, json, numpy as np, tifffile

def auc(pos, neg, bins=512):
    lo, hi = min(pos.min(), neg.min()), max(pos.max(), neg.max())
    if hi <= lo: return 0.5
    hp, e = np.histogram(pos, bins=bins, range=(lo, hi)); hn, _ = np.histogram(neg, bins=bins, range=(lo, hi))
    cn = np.cumsum(hn); auc_ = (hp * (cn - hn / 2.0)).sum() / (len(pos) * len(neg))
    return float(auc_)

def pool4(a):
    h, w = a.shape[0] // 4 * 4, a.shape[1] // 4 * 4
    return a[:h, :w].reshape(h // 4, 4, w // 4, 4).mean((1, 3))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ours'); ap.add_argument('team'); ap.add_argument('out')
    ap.add_argument('--y0', type=int, default=48); ap.add_argument('--x0', type=int, default=64); ap.add_argument('--size', type=int, default=4160)
    ap.add_argument('--border', type=int, default=64); ap.add_argument('--label', default='')
    ap.add_argument('--expect-weak', action='store_true',
                    help='the map under test is the REVERSE depth order: the team map is a forward map, so agreement is not the bar. '
                         'Pass = our mean and our level over the team\'s text pixels are both far below the team\'s (the depth asymmetry that ink produces).')
    ap.add_argument('--ours-origin', type=int, nargs=2, default=(0, 0), metavar=('Y', 'X'), help='origin of the ours frame inside the team frame (0 0 for a full-frame map; 48 64 for the smoke sub-window TIFF)')
    a = ap.parse_args()
    ours = tifffile.imread(a.ours).astype(np.float32) / 255.0; team = np.load(a.team).astype(np.float32) / 255.0
    ys, xs = slice(a.y0 + a.border, a.y0 + a.size - a.border), slice(a.x0 + a.border, a.x0 + a.size - a.border)
    oy, ox = a.ours_origin
    o = ours[ys.start - oy: ys.stop - oy, xs.start - ox: xs.stop - ox]; t = team[ys, xs]
    if o.shape != t.shape: raise SystemExit(f'shape mismatch ours {o.shape} team {t.shape}')
    pearson = float(np.corrcoef(o.ravel(), t.ravel())[0, 1])
    pos, neg = o[t > 0.5], o[t <= 0.5]
    r = dict(label=a.label, ours=a.ours, team=a.team, window=dict(y0=a.y0, x0=a.x0, size=a.size, border=a.border), n_px=int(o.size),
             pearson=round(pearson, 4), auc_vs_team=round(auc(pos, neg), 4) if pos.size and neg.size else None,
             ours_mean=round(float(o.mean()), 4), team_mean=round(float(t.mean()), 4), team_frac_gt_0p5=round(float((t > 0.5).mean()), 4))
    po, pt = pool4(o), pool4(t); text, blank = pt >= 0.40, pt <= 0.25
    r['unit_rule_levels'] = dict(pooled_4x4=True, text_thr=0.40, blank_thr=0.25, text_frac=round(float(text.mean()), 4), blank_frac=round(float(blank.mean()), 4),
                                 ours_text_mean=round(float(po[text].mean()), 4) if text.any() else None, ours_blank_mean=round(float(po[blank].mean()), 4) if blank.any() else None,
                                 team_text_mean=round(float(pt[text].mean()), 4) if text.any() else None, team_blank_mean=round(float(pt[blank].mean()), 4) if blank.any() else None)
    if a.expect_weak:
        u = r['unit_rule_levels']
        r['bar'] = dict(kind='reverse-order asymmetry', ours_mean_max=0.5 * r['team_mean'], ours_text_mean_max=0.5 * (u['team_text_mean'] or 1))
        r['passed'] = bool(r['ours_mean'] <= r['bar']['ours_mean_max'] and (u['ours_text_mean'] or 1) <= r['bar']['ours_text_mean_max'])
    else:
        r['bar'] = dict(pearson_min=0.9, auc_min=0.95); r['passed'] = bool(pearson >= 0.9 and (r['auc_vs_team'] or 0) >= 0.95)
    json.dump(r, open(a.out, 'w'), indent=1)
    print(f"B-2UM calibration {'PASS' if r['passed'] else 'FAIL'} [{a.label}]: Pearson {r['pearson']}, AUC vs team {r['auc_vs_team']}, means ours {r['ours_mean']} team {r['team_mean']}; "
          f"text/blank levels ours {r['unit_rule_levels']['ours_text_mean']}/{r['unit_rule_levels']['ours_blank_mean']} team {r['unit_rule_levels']['team_text_mean']}/{r['unit_rule_levels']['team_blank_mean']}")

if __name__ == '__main__':
    main()
