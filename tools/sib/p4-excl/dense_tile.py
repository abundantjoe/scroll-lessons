"""Certify a near-threshold unflagged tile: sample every triangle of the tile's strip-mesh quads at barycentric
step 1/N (max gap to any tile surface point <= Lmax/N) and take exact point-to-surface distances.
Lower bound on the true tile-surface minimum = dense min - (max over triangles of the covering radius of the samples)."""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from process import SEGS, VOX_MM, PROV, sha
mdir, gjson, key, N, sdir, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
t0 = time.time(); g = json.load(open(gjson)); T = int(g['T_px']); s = 20
r, c = (int(t[1:]) for t in key.split('_'))
X = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
i0, i1 = -(-r * T // s), -(-(r + 1) * T // s); j0, j1 = -(-c * T // s), -(-(c + 1) * T // s)
sub = X[i0:i1 + 1, j0:j1 + 1].astype(np.float64); del X          # include quads straddling the far edge
v = (sub >= 0).all(-1)
q = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & v[1:, 1:]
qi, qj = np.nonzero(q)
A, B, C, E = sub[qi, qj], sub[qi, qj + 1], sub[qi + 1, qj], sub[qi + 1, qj + 1]
bc = np.array([(a / N, b / N) for a in range(N + 1) for b in range(N + 1 - a)])   # weights on 2nd, 3rd vertex
L = max(np.linalg.norm(u - w, axis=1).max() for u, w in ((A, B), (A, C), (B, E), (C, E), (A, E)))
gap = L / N / np.sqrt(3) * 1.0000001        # each sub-triangle has edges <= L/N -> covering radius <= L/(N sqrt 3)
res = {}
for sg in SEGS:
    S = Surface(np.load(f'{sdir}/{sg}.npz')['grid']); best = np.inf
    for (P0, P1, P2) in ((A, B, E), (A, E, C)):
        for w in np.array_split(bc, 6):
            pts = (P0[:, None] * (1 - w[:, 0] - w[:, 1])[None, :, None] + P1[:, None] * w[None, :, 0, None]
                   + P2[:, None] * w[None, :, 1, None]).reshape(-1, 3)
            best = min(best, S.min_dist(pts)[0])
    res[sg] = best; print(sg, round(best * VOX_MM, 6), flush=True); del S
m = min(res.values()); sgm = min(res, key=res.get)
o = {'provenance': PROV, 'tile': key, 'strip_mesh_dir_sha256': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif')},
     'n_quads': int(len(qi)), 'barycentric_N': N, 'strip_Lmax_vox': round(float(L), 3), 'sample_gap_bound_vox': round(float(gap), 3),
     'dense_min_mm': round(m * VOX_MM, 6), 'segment': sgm, 'lower_bound_mm': round((m - gap) * VOX_MM, 6),
     'certified_not_adjacent': bool((m - gap) * VOX_MM >= 1.2),
     'per_segment_dense_mm': {k: round(x * VOX_MM, 6) for k, x in res.items()},
     'note': 'distance to a surface is 1-Lipschitz, so the true tile-surface minimum >= dense min - gap',
     'seconds': round(time.time() - t0, 1)}
json.dump(o, open(out, 'w'), indent=1); print(json.dumps({k: o[k] for k in ('dense_min_mm', 'lower_bound_mm', 'certified_not_adjacent', 'seconds')}))
