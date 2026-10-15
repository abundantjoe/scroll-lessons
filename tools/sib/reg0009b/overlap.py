# Provenance: Project HERCULES | owner the owner | [id removed]
"""3-D overlap grouping of PHerc0009B segments (task step 3).
Frame: the 8.640 um meshes (vox = 8.64 um); sensitivity run on the 2.401 um meshes (--frame 2).
Pairs whose meshes come within 128 vox (KD-tree on raw vertices) are tested:
  densify both 5 x 5 (bilinear per valid quad), unit normals of the densified target grid,
  for every source point the nearest target point (Euclidean, <= 12 vox), normal distance
  dn = |(a - b) . n_b|, tangential dt = sqrt(d^2 - dn^2); a point counts only if dt <= 3 vox
  (the densified spacing is ~4 vox, so the foot of the perpendicular lies on the target).
PRIMARY rule (CORR-RETRACE-RULE, fail-closed; rules.failclosed): per direction SAME iff
(a) literal nearest-densified-vertex Euclidean bins OR (b) point-to-triangulated-surface bins give
>= 1000 points within 2 vox and count[0,1) >= 2 * count[2,3). A pair is SAME if either direction is SAME.
Also reported (not deciding): the normal-distance variant above (rules.direction).
Papyrus units = connected components of SAME pairs."""
import itertools, json, os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, densify, vertex_normals, valid_mask
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules

DATA = '/work/reg0009b/data'
frame = sys.argv[1] if len(sys.argv) > 1 else '9'
TAG = '-on-20250521125136-8.64um.tifxyz' if frame == '9' else '-on-20250820154339-2.401um.tifxyz'
OUT = f'/home/user/dominion/logs/sib/reg0009b/overlap_frame{frame}.json'
segs = sorted(d for d in os.listdir(DATA) if os.path.isdir(f'{DATA}/{d}/mesh'))
raw, dense, surfs = {}, {}, {}
for s in segs:
    m = read_tifxyz(f'{DATA}/{s}/mesh/{s.split("-")[0]}{TAG}')
    p = m.points.astype(np.float64); v = valid_mask(p)
    raw[s] = p[v]
    dp = densify(p, 5).astype(np.float64); dv = valid_mask(dp)
    nrm = vertex_normals(dp)
    ok = dv & np.isfinite(nrm).all(-1)
    dense[s] = (dp[ok], nrm[ok])
    surfs[s] = rules.TriSurface(dp, dv)
    print(s[:14], 'raw', v.sum(), 'dense', ok.sum(), flush=True)
trees = {s: cKDTree(raw[s]) for s in segs}
dtrees = {s: cKDTree(dense[s][0]) for s in segs}


def direction(a, b):
    return rules.direction(dense[a][0], dense[b][0], dense[b][1], dtrees[b])


pairs = []
for a, b in itertools.combinations(segs, 2):
    lo = np.maximum(raw[a].min(0), raw[b].min(0)); hi = np.minimum(raw[a].max(0), raw[b].max(0))
    if np.any(lo - hi > 128): continue
    dmin = float(trees[a].query(raw[b], k=1, distance_upper_bound=129, workers=4)[0].min())
    if not dmin <= 128: continue
    ab, ba = direction(a, b), direction(b, a)
    fab = rules.failclosed(surfs[a].P[surfs[a].V], surfs[b]); fba = rules.failclosed(surfs[b].P[surfs[b].V], surfs[a])
    pairs.append(dict(a=a, b=b, min_dist_raw_vox=round(dmin, 3), fc_ab=fab, fc_ba=fba,
                      same=fab['same'] or fba['same'], same_both=fab['same'] and fba['same'],
                      normal_variant=dict(ab=ab, ba=ba, same=ab['same'] or ba['same'])))
    print(a[:14], b[:14], round(dmin, 2), fab['counts_a_vertex'], fab['counts_b_surface'], fba['counts_b_surface'], pairs[-1]['same'],
          pairs[-1]['normal_variant']['same'], flush=True)
# connected components
par = {s: s for s in segs}
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for p in pairs:
    if p['same']: par[f(p['a'])] = f(p['b'])
units = {}
for s in segs: units.setdefault(f(s), []).append(s)
units = sorted((sorted(v) for v in units.values()), key=lambda v: (-len(v), v[0]))
json.dump(dict(frame=frame, n_segments=len(segs), n_pairs_total=len(segs) * (len(segs) - 1) // 2,
               n_pairs_within128=len(pairs), n_same=sum(p['same'] for p in pairs),
               n_same_both_directions=sum(p['same_both'] for p in pairs),
               n_same_normal_variant=sum(p['normal_variant']['same'] for p in pairs),
               rule='CORR-RETRACE-RULE fail-closed: (a) nearest-densified-vertex OR (b) point-to-triangulated-surface',
               units=[dict(unit=f'U{k+1:02d}', segments=u) for k, u in enumerate(units)], pairs=pairs),
          open(OUT, 'w'), indent=1)
print('pairs<=128', len(pairs), 'same', sum(p['same'] for p in pairs), 'units', len(units))
