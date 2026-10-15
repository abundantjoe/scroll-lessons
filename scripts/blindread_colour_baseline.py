"""Colour baseline for blind read #2: how well does the strong-ink pixel fraction of each hidden control
image (no reading at all) separate positives from negatives, and how closely does each reader's confidence follow it?
The fractions come from the control rerun's batch log (`ens_d1_p055` per strip); the read used the original run's maps,
whose stored per-strip metrics (`per_strip_d1` in results/control_strips/original_results.json) the rerun's
`per_strip` equals at that precision; the whole-strip strong fraction itself was not stored by the original.

  python blindread_colour_baseline.py --out results/blind_read/colour_baseline.json
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from stripqc.blindread import reader_auc  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--batch-log', default=os.path.join(REPO, 'results/control_strips_rerun/batch.log'))
ap.add_argument('--read', default=os.path.join(REPO, 'results/blind_read/read2_calibrated_controls.json'))
ap.add_argument('--out', required=True)
a = ap.parse_args()
frac = {}
for line in open(a.batch_log):
    if line.startswith('{"name"'):
        d = json.loads(line)
        frac[d['name']] = d['ens_d1_p055']
R = json.load(open(a.read))
images = {x['image']: x['cls'] for x in R['per_image'][0]}
f = {im: frac[f'ctrlS_{im}'] for im in images}
pos = lambda c: c.startswith('pos')  # noqa: E731
neg = lambda c: c == 'neg_displaced'  # noqa: E731
out = dict(strong_fraction_by_image=f,
           colour_auc_all_pos_vs_neg=reader_auc(f, images, pos, neg),
           readers=[])
for rows, summ in zip(R['per_image'], R['readers']):
    conf = {x['image']: x['confidence'] for x in rows}
    ims = sorted(conf)
    rho = spearmanr([conf[i] for i in ims], [f[i] for i in ims]).correlation
    out['readers'].append(dict(reader=summ['reader'], auc_all_pos_vs_neg=summ['auc_all_pos_vs_neg'],
                               spearman_confidence_vs_strong_fraction=float(rho)))
json.dump(out, open(a.out, 'w'), indent=1, allow_nan=False)
print(json.dumps({k: v for k, v in out.items() if k != 'strong_fraction_by_image'}, indent=1))
