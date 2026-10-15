# Provenance: Project HERCULES | owner the owner | [id removed]
"""Sensitivity test for the overlap rule (not the primary grouping).
For every pair from overlap_frame<f>.json with >= 1000 points within 2 vox (point-to-surface, form b) in either direction:
signed normal distance s = (a - b) . n_b for source points with |s| < 6 and dt <= 3 vox;
points binned in 64-vox 3-D cells; per cell (>= 50 points) the median s is the local offset;
residual r = s - cell median. Reported: offset distribution (p10/p50/p90 of cell medians),
residual histogram |r| in [0,1), [1,2), [2,3), within-cell MAD, and the task rule applied to |r|
("SAME after local offset"). A pair that is SAME only after local offset removal means: two traces
nearly coincide up to a smooth offset field (e.g. a cross-frame affine error), i.e. likely the same
papyrus traced twice. Frame 9: vox = 8.64 um."""
import json, os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, densify, vertex_normals, valid_mask

DATA = '/work/reg0009b/data'
frame = sys.argv[1] if len(sys.argv) > 1 else '9'
TAG = '-on-20250521125136-8.64um.tifxyz' if frame == '9' else '-on-20250820154339-2.401um.tifxyz'
O = json.load(open(f'/home/user/dominion/logs/sib/reg0009b/overlap_frame{frame}.json'))
cache = {}


def load(s):
    if s not in cache:
        p = read_tifxyz(f'{DATA}/{s}/mesh/{s.split("-")[0]}{TAG}').points.astype(np.float64)
        dp = densify(p, 5).astype(np.float64); n = vertex_normals(dp)
        ok = valid_mask(dp) & np.isfinite(n).all(-1)
        cache[s] = (dp[ok], n[ok], cKDTree(dp[ok]))
    return cache[s]


def one(a, b):
    A = load(a)[0]; Bp, Bn, T = load(b)
    d, i = T.query(A, k=1, distance_upper_bound=8.0, workers=4)
    f = np.isfinite(d); A, d, i = A[f], d[f], i[f]
    s = np.einsum('ij,ij->i', A - Bp[i], Bn[i]); dt = np.sqrt(np.maximum(d ** 2 - s ** 2, 0))
    ok = (dt <= 3) & (np.abs(s) < 6); A, s = A[ok], s[ok]
    if len(s) < 1000: return None
    cell = np.floor(A / 64).astype(np.int64)
    key = (cell[:, 0] * 100003 + cell[:, 1]) * 100003 + cell[:, 2]
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    med = np.array([np.median(s[inv == k]) for k in range(len(u))])
    good = cnt[inv] >= 50
    r = np.abs(s - med[inv])[good]
    mad = np.array([np.median(np.abs(s[inv == k] - med[k])) for k in range(len(u)) if cnt[k] >= 50])
    c = [int(((r >= k) & (r < k + 1)).sum()) for k in range(3)]
    return dict(n_pts=int(good.sum()), n_cells=int((cnt >= 50).sum()),
                cell_offset_p10_p50_p90=np.percentile(med[cnt >= 50], [10, 50, 90]).round(3).tolist() if (cnt >= 50).any() else None,
                cell_mad_median=float(np.median(mad)) if len(mad) else None,
                resid_counts=c, same_after_offset=bool(c[0] + c[1] >= 1000 and c[0] >= 2 * c[2]))


out = []
for p in O['pairs']:
    b = lambda x: x['counts_b_surface'][0] + x['counts_b_surface'][1]
    if max(b(p['fc_ab']), b(p['fc_ba'])) < 1000: continue
    ab, ba = one(p['a'], p['b']), one(p['b'], p['a'])
    rec = dict(a=p['a'], b=p['b'], same_rule=p['same'], ab=ab, ba=ba,
               same_after_offset=bool((ab or {}).get('same_after_offset') or (ba or {}).get('same_after_offset')))
    out.append(rec)
    print(p['a'][:14], p['b'][:14], p['same'], rec['same_after_offset'], ab and ab['cell_offset_p10_p50_p90'], ab and ab['cell_mad_median'], ab and ab['resid_counts'], flush=True)
segs = sorted({s for u in O['units'] for s in u['segments']})
par = {s: s for s in segs}
def f(x):
    while par[x] != x: x = par[x]
    return x
for r in out:
    if r['same_rule'] or r['same_after_offset']: par[f(r['a'])] = f(r['b'])
units = {}
for s in segs: units.setdefault(f(s), []).append(s)
units = sorted((sorted(v) for v in units.values()), key=lambda v: (-len(v), v[0]))
json.dump(dict(frame=frame, n_pairs_tested=len(out), n_same_rule=sum(r['same_rule'] for r in out),
               n_same_rule_or_offset=sum(r['same_rule'] or r['same_after_offset'] for r in out),
               units_sensitivity=units, pairs=out),
          open(f'/home/user/dominion/logs/sib/reg0009b/overlap_offset_frame{frame}.json', 'w'), indent=1)
print('tested', len(out), 'units', len(units))
