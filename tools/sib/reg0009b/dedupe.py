# Provenance: Project HERCULES | owner the owner | [id removed]
"""Global 3-D de-duplication of dense candidate windows (from windows.json) across ALL segments,
independent of the unit grouping. Greedy by ink150 descending; a window is rejected if >= 10 % of its
mesh points (2.401 um mesh vertices, every 4th row/column) lie within TOL 2.4-um vox of an accepted
window's points. TOL = 10 and 20 (2.4-um vox; 24 / 48 um). Counts are then tallied per unit for
the primary (task-rule) grouping and for the offset-sensitivity grouping.
Each accepted window also gets its 8.64 um canvas box through the corrected label map
c9 = (c2 + 10) * N9 / N2 - 10 + d (d = depth-corrected global shift of the segment); coordinates only."""
import json, os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, valid_mask

DATA = '/work/reg0009b/data'
LOG = '/home/user/dominion/logs/sib/reg0009b'
W = json.load(open(f'{LOG}/windows.json'))
WIN = W['params']['win_cells']
prim = {s: u['unit'] for u in json.load(open(f'{LOG}/overlap_frame9.json'))['units'] for s in u['segments']}
sens_units = json.load(open(f'{LOG}/sensitivity_units.json'))
sens = {s: u['unit'] for u in sens_units for s in u['segments']}


def dense(w, t=W['params']['primary']):
    return w['valid'] >= t['valid'] and w['ink150'] >= t['ink150'] and w['spread'] >= t['spread']


mesh = {}
def pts(s):
    if s not in mesh:
        P = read_tifxyz(f'{DATA}/{s}/mesh/{s.split("-")[0]}-on-20250820154339-2.401um.tifxyz').points.astype(np.float64)
        mesh[s] = (P, valid_mask(P))
    return mesh[s]


def box9(s, box2):
    r = json.load(open(f'{LOG}/reg/{s}.dc.json'))
    N9, N2, d = r['N9'], r['N2'], r['global_shift_median']
    x0, y0, x1, y1 = box2
    f = lambda c, ax: (c + 10) * N9[ax] / N2[ax] - 10 + d[ax]
    return [round(f(x0, 0), 1), round(f(y0, 1), 1), round(f(x1, 0), 1), round(f(y1, 1), 1)]


cand = sorted(((w['ink150'], s, k) for s, v in W['segments'].items() for k, w in enumerate(v['windows']) if dense(w)), reverse=True)
out = dict(n_dense_windows_all_segments=len(cand), tol={})
for tol in (10.0, 20.0):
    acc, clouds = [], []
    for ink, s, k in cand:
        w = W['segments'][s]['windows'][k]; P, V = pts(s)
        sl = (slice(w['r0'], w['r0'] + WIN, 4), slice(w['c0'], w['c0'] + WIN, 4))
        c = P[sl][V[sl]]
        if any(np.isfinite(t.query(c, k=1, distance_upper_bound=tol)[0]).mean() >= 0.10 for t in clouds):
            continue
        clouds.append(cKDTree(c))
        acc.append(dict(segment=s, window_index=k, unit_primary=prim[s], unit_sensitivity=sens[s], ink150=w['ink150'],
                        ink128=w['ink128'], spread=w['spread'], valid=w['valid'], canvas2_px_x0y0x1y1=w['canvas2_px'],
                        canvas9_px_x0y0x1y1=box9(s, w['canvas2_px']), centroid_2p4_vox=np.round(c.mean(0), 1).tolist()))
    per_p, per_s = {}, {}
    for a in acc:
        per_p[a['unit_primary']] = per_p.get(a['unit_primary'], 0) + 1
        per_s[a['unit_sensitivity']] = per_s.get(a['unit_sensitivity'], 0) + 1
    out['tol'][str(int(tol))] = dict(n_accepted=len(acc), per_unit_primary=per_p, per_unit_sensitivity=per_s, accepted=acc)
    print('tol', tol, len(acc), per_p, per_s, flush=True)
json.dump(out, open(f'{LOG}/windows_dedupe.json', 'w'), indent=1)
