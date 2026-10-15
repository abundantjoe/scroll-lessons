# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-14-A2 item 2 equivalence check on r0 c5: full-resolution u8 predictions (b's WORK/it4/full/*.npy) of the fp32
and bf16 runs, compared over mesh-valid px. PASS iff the fraction of px with |diff| > 2 (i.e. > 2/255) is <= 1 %.
Numbers only. Usage: p4o_bf16check.py FP32_WORK BF16_WORK OUT.json"""
import hashlib
import json
import sys
import time

import numpy as np

fn = '20260701183124-w010-027_r0_c5.png.npy'
a = np.load(f'{sys.argv[1]}/it4/full/{fn}').astype(np.int16)
b = np.load(f'{sys.argv[2]}/it4/full/{fn}').astype(np.int16)
valid = np.load(f'{sys.argv[1]}/mesh_valid.npy')
T = 8343
ys, xs = np.arange(0, T), np.arange(5 * T, 6 * T)
gy, gx = (ys * valid.shape[0]) // 69760, (xs * valid.shape[1]) // 170000
m = valid[np.ix_(gy, gx)]
d = np.abs(a - b)[m]
frac = float((d > 2).mean())
rec = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
           rule='DECL-P4-14-A2 item 2: <= 1 % of mesh-valid px differ by more than 2/255', tile='r0 c5',
           valid_px=int(m.sum()), frac_diff_gt2=frac, frac_diff_gt0=float((d > 0).mean()), mean_abs=float(d.mean()),
           max_abs=int(d.max()), pass_=None, fp32_sha256=hashlib.sha256(np.load(f'{sys.argv[1]}/it4/full/{fn}').tobytes()).hexdigest(),
           bf16_sha256=hashlib.sha256(np.load(f'{sys.argv[2]}/it4/full/{fn}').tobytes()).hexdigest(),
           utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
rec['pass'] = frac <= 0.01
del rec['pass_']
json.dump(rec, open(sys.argv[3], 'w'), indent=1)
print(json.dumps(rec))
