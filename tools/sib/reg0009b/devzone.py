# Provenance: Project HERCULES | owner the owner | [id removed]
"""0009B area eligible for DEV windows under DECL-DEVLOOP-A1 item 7 (numbers only; no map produced):
outside every KTLB-M candidate window + 144 vox. Declares nothing; the registry extension is the
orchestrator's.
- Frame: 2.401 um meshes (finer sampling). 144 vox is read as 8.64 um vox (stricter; 1.244 mm), plus a
  vertex-sampling margin: both the exclusion set and the tested set are mesh vertices on a 20-vox grid
  (half-diagonal h = 14.2 2.4-um vox, measured edge median <= 20.05), so the true point-to-surface
  distance is >= vertex distance - 2h. Threshold T = 144 x 3.61 + 2 x 14.2 = 548.3 -> 550 2.4-um vox
  (3.61 >= every per-axis scale of the official 8.64 -> 2.401 affine). Also: 144 2.4-um vox (+ 2h margin = 173):
  the native unit of the 2.401 um volume on which the KTLB-M windows are defined (orchestrator ruling 2026-09-26 05:59Z).
- Exclusion sets: POOL23 = the 23 deduplicated candidate windows; ALL76 = every dense window of every
  segment before dedupe (stricter).
- Counts per segment: allowed valid area; 2 x 2 cm windows (417 cells, stride 208) with every valid cell
  allowed, valid >= 0.90, and ink150 fraction; 1 x 1 cm blanks (208 cells, stride 104) fully allowed with
  coverage >= 0.90 and ink150 fraction < 0.01 (the DECL-DEVLOOP-A1 blank bars except blob-f180, which
  needs a model map and is not computed here)."""
import json, os, sys, glob
import numpy as np, tifffile
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, valid_mask

DATA = '/work/reg0009b/data'; LOG = '/home/user/dominion/logs/sib/reg0009b'
W = json.load(open(f'{LOG}/windows.json')); D = json.load(open(f'{LOG}/windows_dedupe.json'))
WIN = W['params']['win_cells']; PR = W['params']['primary']
units = {s: u['unit'] for u in json.load(open(f'{LOG}/overlap_frame9.json'))['units'] for s in u['segments']}
TH = {'strict_9umvox': 550.0, 'native_2p4vox': 173.0}
segs = sorted(W['segments'])
mesh, ink = {}, {}
for s in segs:
    P = read_tifxyz(f'{DATA}/{s}/mesh/{s.split("-")[0]}-on-20250820154339-2.401um.tifxyz').points.astype(np.float64)
    V = valid_mask(P); H, Wd = V.shape
    a = tifffile.imread(glob.glob(f'{DATA}/{s}/ink-detection/*.tif')[0])
    c = (a >= 150).reshape(H, 20, Wd, 20).sum((1, 3)).astype(np.float32) / 400.0
    del a
    c[~V] = 0; mesh[s] = (P, V); ink[s] = c
    print('loaded', s[:14], flush=True)

def wpts(s, r0, c0, n=WIN):
    P, V = mesh[s]; return P[r0:r0 + n, c0:c0 + n][V[r0:r0 + n, c0:c0 + n]]

sets = {'POOL23': [(a['segment'], W['segments'][a['segment']]['windows'][a['window_index']]) for a in D['tol']['10']['accepted']],
        'ALL76': [(s, w) for s in segs for w in W['segments'][s]['windows']
                  if w['valid'] >= PR['valid'] and w['ink150'] >= PR['ink150'] and w['spread'] >= PR['spread']]}
out = dict(thresholds_2p4vox=TH, n_windows={k: len(v) for k, v in sets.items()}, results={})
for sname, lst in sets.items():
    T = cKDTree(np.concatenate([wpts(s, w['r0'], w['c0']) for s, w in lst]))
    for tname, thr in TH.items():
        key = f'{sname}/{tname}'; res = {}
        for s in segs:
            P, V = mesh[s]
            d = np.full(V.shape, np.inf); d[V] = T.query(P[V], k=1, distance_upper_bound=2000.0, workers=4)[0]
            ok = V & (d >= thr)
            H, Wd = V.shape
            w2 = []; bl = 0; wl = []
            for r0 in range(0, H - WIN + 1, 208):
                for c0 in range(0, Wd - WIN + 1, 208):
                    v = V[r0:r0 + WIN, c0:c0 + WIN]
                    if v.mean() < 0.90 or not ok[r0:r0 + WIN, c0:c0 + WIN][v].all(): continue
                    w2.append(round(float(ink[s][r0:r0 + WIN, c0:c0 + WIN][v].mean()), 4))
                    wl.append(dict(kind='2cm', canvas2_px_x0y0x1y1=[c0 * 20, r0 * 20, (c0 + WIN) * 20, (r0 + WIN) * 20],
                                   valid=round(float(v.mean()), 4), ink150=w2[-1],
                                   min_vertex_dist_2p4vox=round(float(d[r0:r0 + WIN, c0:c0 + WIN][v].min()), 1)))
            for r0 in range(0, H - 208 + 1, 104):
                for c0 in range(0, Wd - 208 + 1, 104):
                    v = V[r0:r0 + 208, c0:c0 + 208]
                    if v.mean() < 0.90 or not ok[r0:r0 + 208, c0:c0 + 208][v].all(): continue
                    ik = float(ink[s][r0:r0 + 208, c0:c0 + 208][v].mean())
                    if ik < 0.01:
                        bl += 1
                        wl.append(dict(kind='blank1cm', canvas2_px_x0y0x1y1=[c0 * 20, r0 * 20, (c0 + 208) * 20, (r0 + 208) * 20],
                                       valid=round(float(v.mean()), 4), ink150=round(ik, 5),
                                       min_vertex_dist_2p4vox=round(float(d[r0:r0 + 208, c0:c0 + 208][v].min()), 1)))
            res[s] = dict(unit=units[s], valid_cm2=round(float(V.sum() * 400 * 2.401e-4 ** 2), 3),
                          allowed_cm2=round(float(ok.sum() * 400 * 2.401e-4 ** 2), 3),
                          n_2cm_windows_allowed=len(w2), n_2cm_ink150_ge_0p05=sum(x >= 0.05 for x in w2),
                          ink150_of_allowed_windows=sorted(w2, reverse=True), n_1cm_blanks_allowed=bl, windows=wl)
        tot = dict(allowed_cm2=round(sum(r['allowed_cm2'] for r in res.values()), 3),
                   n_2cm=sum(r['n_2cm_windows_allowed'] for r in res.values()),
                   n_2cm_ink=sum(r['n_2cm_ink150_ge_0p05'] for r in res.values()),
                   n_blanks=sum(r['n_1cm_blanks_allowed'] for r in res.values()))
        out['results'][key] = dict(per_segment=res, totals=tot)
        print(key, tot, flush=True)
json.dump(out, open(f'{LOG}/devzone.json', 'w'), indent=1)
