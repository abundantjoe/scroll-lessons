"""Score the control-strip arms: pre-registered decisions (docs/prereg/DECL-FL-STRIP.md), letter-bootstrap CIs and
exploratory metrics. Optionally compare with an earlier results.json (reproduction check).

  python score_arms.py --bi <BI_ROOT> --erwin <pherc343-first-letters> --out results.json [--expect original.json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stripqc import score  # noqa: E402

BOXES = 'inputs/concat_w047-w048_R5B2_z9500-11000_letter_boxes.json'
Z13 = [(42, 55), (55, 68), (68, 81), (81, 94), (94, 107)]
Z20 = [(42, 62), (62, 82), (82, 102)]
GROUPS = {'Z13': Z13, 'Z20': Z20, 'P13': Z13, 'D8': Z13, 'F13': Z13, 'FD8': Z13}

ap = argparse.ArgumentParser()
ap.add_argument('--bi', required=True)
ap.add_argument('--erwin', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--expect')
ap.add_argument('--depth', type=int, default=1)
ap.add_argument('--boot', type=int, default=2000)
a = ap.parse_args()
B = json.load(open(os.path.join(a.erwin, BOXES)))
assert B['frame'] == 'raw'
boxes = [l['box'] for l in B['letters']]
ref = score.load_arm(os.path.join(a.bi, 'ctrlS_REF_r40-110'), a.depth)
if ref is None:
    sys.exit('REF arm missing')
res = dict(depth=a.depth, threshold=score.T, arms={}, per_strip={})
for g, rows in GROUPS.items():
    parts = []
    for t0, t1 in rows:
        name = f'ctrlS_{g}_r{t0}-{t1}'
        arm = score.load_arm(os.path.join(a.bi, name), a.depth)
        if arm is None:
            res['per_strip'][name] = None
            continue
        p = score.match(arm, ref, t0, t1, boxes)
        parts.append(p)
        res['per_strip'][name] = score.metrics([p])
    m = score.metrics(parts)
    if m:
        lo, hi, nl = score.bootstrap_recall(parts, n=a.boot)
        m.update(recall_ci95=[lo, hi], n_letters=nl, n_strips=len(parts))
        res['arms'][g] = m
res['arms']['REF'] = score.metrics([score.match(ref, ref, 42, 107, boxes)])
A = res['arms']


def g(k, f):
    return (A.get(k) or {}).get(f)


def sees(k):
    R, E, r = g(k, 'recall'), g(k, 'E'), g(k, 'r')
    return None if None in (R, E, r) else bool(R >= 0.5 and E >= 5 and r >= 0.6)


def band_rule(k):
    """Pre-registered rule 3 for arm k: band f055 outside the boxes >= 0.01 and >= 3 x REF at the same pixels."""
    band, bref = g(k, 'band_f055_out'), g(k, 'band_ref_f055_out')
    return None if None in (band, bref) else bool(band >= 0.01 and band >= 3 * max(bref, 1e-4))


p13_band = band_rule('P13')
res['decisions_preregistered'] = {
    'Z13_sees_ink': sees('Z13'), 'Z20_sees_ink': sees('Z20'),
    'Z13_margin_artifact': band_rule('Z13'),
    'P13_padding_fixes': None if g('P13', 'recall') is None or p13_band is None else bool(
        g('P13', 'recall') >= 0.7 and (g('P13', 'r') or 0) >= 0.8 and not p13_band),
    'D8_no_ink_arm_works': None if None in (g('Z13', 'f_in'), g('D8', 'f_in')) else bool(g('D8', 'f_in') <= 0.2 * g('Z13', 'f_in')),
}
res['exploratory'] = {
    'F13_sees_ink': sees('F13'),
    'F13_fixes_bar_R0.7_r0.8': None if g('F13', 'recall') is None else bool(g('F13', 'recall') >= 0.7 and (g('F13', 'r') or 0) >= 0.8),
    'fill_no_ink_floor_f055': g('FD8', 'f_in') if g('FD8', 'f_in') is not None else None,
    'fill_no_ink_floor_f055_all': None if not A.get('FD8') else (A['FD8']['f_in'] * A['FD8']['n_box_px'] + A['FD8']['f_out'] * (A['FD8']['n_px'] - A['FD8']['n_box_px'])) / A['FD8']['n_px'],
}
if a.expect and os.path.exists(a.expect):
    E0 = json.load(open(a.expect))
    cmp = {}
    for k in ('Z13', 'Z20', 'P13', 'D8', 'F13'):
        o = (E0.get('arms') or {}).get(f'{k}_d{a.depth}')
        if o and A.get(k):
            cmp[k] = {f: dict(original=o.get(f), rerun=A[k].get(f), abs_diff=None if o.get(f) is None or A[k].get(f) is None else abs(o[f] - A[k][f]))
                      for f in ('f_in', 'f_out', 'recall', 'r')}
    res['reproduction_vs_original'] = cmp
missing = sorted(k for k, v in res['per_strip'].items() if v is None)
if missing:
    res['missing_strips'] = missing
json.dump(res, open(a.out, 'w'), indent=1, allow_nan=False)
print(json.dumps(dict(decisions=res['decisions_preregistered'], exploratory=res['exploratory'],
                      recall={k: (round(v['recall'], 3) if v.get('recall') is not None else None, v.get('recall_ci95')) for k, v in A.items()}), indent=1))
if missing:
    sys.exit(f'INCOMPLETE: {len(missing)} strip(s) missing, decisions use fewer strips: {missing}')
