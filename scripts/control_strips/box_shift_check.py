"""Robustness of the pre-registered decisions to the letter-box registration: move every letter box by -20/0/+20 px
(one node) in x and y, rescore every arm without the bootstrap, and report any decision that changes.

  python box_shift_check.py --bi <BI_ROOT> --erwin <pherc343-first-letters> --out box_shift_check.json
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stripqc import score  # noqa: E402

BOXES = 'inputs/concat_w047-w048_R5B2_z9500-11000_letter_boxes.json'
Z13 = [(42, 55), (55, 68), (68, 81), (81, 94), (94, 107)]
GROUPS = {'Z13': Z13, 'Z20': [(42, 62), (62, 82), (82, 102)], 'P13': Z13, 'D8': Z13, 'F13': Z13}


def decisions(A):
    """The pre-registered rules exactly as in score_arms.py (docs/prereg/DECL-FL-STRIP.md)."""
    def g(k, f):
        return (A.get(k) or {}).get(f)

    def sees(k):
        R, E, r = g(k, 'recall'), g(k, 'E'), g(k, 'r')
        return None if None in (R, E, r) else bool(R >= 0.5 and E >= 5 and r >= 0.6)
    def band_rule(k):
        band, bref = g(k, 'band_f055_out'), g(k, 'band_ref_f055_out')
        return None if None in (band, bref) else bool(band >= 0.01 and band >= 3 * max(bref, 1e-4))
    p13_band = band_rule('P13')
    return {'Z13_sees_ink': sees('Z13'), 'Z20_sees_ink': sees('Z20'),
            'Z13_margin_artifact': band_rule('Z13'),
            'P13_padding_fixes': None if g('P13', 'recall') is None or p13_band is None else bool(
                g('P13', 'recall') >= 0.7 and (g('P13', 'r') or 0) >= 0.8 and not p13_band),
            'D8_no_ink_arm_works': None if None in (g('Z13', 'f_in'), g('D8', 'f_in')) else bool(g('D8', 'f_in') <= 0.2 * g('Z13', 'f_in')),
            'F13_sees_ink (exploratory)': sees('F13')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bi', required=True)
    ap.add_argument('--erwin', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--depth', type=int, default=1)
    ap.add_argument('--shift', type=int, default=20)
    a = ap.parse_args()
    boxes0 = [l['box'] for l in json.load(open(os.path.join(a.erwin, BOXES)))['letters']]
    ref = score.load_arm(os.path.join(a.bi, 'ctrlS_REF_r40-110'), a.depth)
    arms = {}
    for g, rows in GROUPS.items():
        for t0, t1 in rows:
            arm = score.load_arm(os.path.join(a.bi, f'ctrlS_{g}_r{t0}-{t1}'), a.depth)
            if arm is not None:
                arms.setdefault(g, []).append((arm, t0, t1))
    want = {f'ctrlS_{g}_r{t0}-{t1}' for g, rows in GROUPS.items() for t0, t1 in rows}
    have = {f'ctrlS_{g}_r{t0}-{t1}' for g, lst in arms.items() for _, t0, t1 in lst}
    if ref is None or want - have:
        sys.exit(f'missing arms: {sorted(want - have) + ([] if ref is not None else ["ctrlS_REF_r40-110"])}')
    out = dict(shift_px=a.shift, depth=a.depth, by_shift={})
    s = a.shift
    for dx, dy in itertools.product((-s, 0, s), (-s, 0, s)):
        boxes = [[x0 + dx, y0 + dy, x1 + dx, y1 + dy] for x0, y0, x1, y1 in boxes0]
        A = {g: score.metrics([score.match(arm, ref, t0, t1, boxes) for arm, t0, t1 in lst]) for g, lst in arms.items()}
        out['by_shift'][f'dx={dx:+d},dy={dy:+d}'] = dict(
            decisions=decisions(A), recall={g: (m or {}).get('recall') for g, m in A.items()})
    base = out['by_shift']['dx=+0,dy=+0']['decisions']
    out['decisions_changed'] = sorted({f'{k} at {sh}' for sh, v in out['by_shift'].items()
                                       for k, d in v['decisions'].items() if d != base[k]})
    json.dump(out, open(a.out, 'w'), indent=1, allow_nan=False)
    print(json.dumps(dict(base=base, decisions_changed=out['decisions_changed']), indent=1))


if __name__ == '__main__':
    main()
