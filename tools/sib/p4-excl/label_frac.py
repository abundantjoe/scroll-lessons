"""DECL-P4-21 (with -A1): per-tile organizer ink-label fractions for strip-a tiles, computed in code only.
No label value is displayed, saved as an image or described; outputs are per-tile numbers.
Mapping: each tile mesh vertex -> exact closest point on each labelled segment surface (uvmap.nearest_uv,
<= TOL vox) -> segment UV -> label pixel round(uv * 20) (label level 0 = tifxyz grid x 20, verified by shape).
Sampling: one sample per tile mesh vertex (the strip grid, one per 20 x 20 strip px cell)."""
import sys, os, json, time
import numpy as np, tifffile, zarr
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from uvmap import nearest_uv
from process import SEGS, VOX_MM, PROV, sha
mdir, gjson, sdir, ldir, out = sys.argv[1:6]
rows = range(int(sys.argv[6]), int(sys.argv[7]) + 1); cols = range(int(sys.argv[8]), int(sys.argv[9]) + 1)
TOL = 20.0
t0 = time.time(); g = json.load(open(gjson)); T = int(g['T_canvas_px']); s = 20
X = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
tiles = [(r, c) for r in rows for c in cols]
P, tid = [], []
for n, (r, c) in enumerate(tiles):
    i0, i1 = -(-r * T // s), -(-(r + 1) * T // s); j0, j1 = -(-c * T // s), -(-(c + 1) * T // s)
    sub = X[i0:i1, j0:j1]; v = (sub >= 0).all(-1) & np.isfinite(sub).all(-1)
    P.append(sub[v].astype(np.float64)); tid.append(np.full(int(v.sum()), n))
del X; P = np.concatenate(P); tid = np.concatenate(tid); N = len(P)
Dall = np.full((len(SEGS), N), np.inf); COV = np.zeros((len(SEGS), N), bool); INK = np.zeros((len(SEGS), N), bool)
lab_sha = {}
for si, sg in enumerate(SEGS):
    S = Surface(np.load(f'{sdir}/{sg}.npz')['grid'])
    D = np.full(N, np.inf); UV = np.full((N, 2), np.nan)
    for k in range(0, N, 100_000):
        d, uv, _ = nearest_uv(S, P[k:k + 100_000], TOL); D[k:k + 100_000] = d; UV[k:k + 100_000] = uv
    zi = zarr.open_array(f'{ldir}/{sg}/inklabels.zarr/0', mode='r'); zs = zarr.open_array(f'{ldir}/{sg}/supervision.zarr/0', mode='r')
    assert zi.shape == zs.shape == (S.H * 20, S.W * 20), (zi.shape, S.H, S.W)
    lab_sha[sg] = {a: sha(f'{ldir}/{sg}/{a}.zarr/0/c/0/0') for a in ('inklabels', 'supervision')}
    ok = np.isfinite(D)
    pr = np.clip(np.rint(UV[ok, 0] * 20).astype(np.int64), 0, zi.shape[0] - 1)
    pc = np.clip(np.rint(UV[ok, 1] * 20).astype(np.int64), 0, zi.shape[1] - 1)
    idx = np.nonzero(ok)[0]; cv = np.zeros(len(idx), bool); ik = np.zeros(len(idx), bool)
    for n in range(len(tiles)):              # read one bounding box per tile (code only)
        m = tid[idx] == n
        if not m.any():
            continue
        r0, r1, c0, c1 = pr[m].min(), pr[m].max() + 1, pc[m].min(), pc[m].max() + 1
        bi = zi[r0:r1, c0:c1]; bs = zs[r0:r1, c0:c1]
        cv[m] = bs[pr[m] - r0, pc[m] - c0] == 255; ik[m] = bi[pr[m] - r0, pc[m] - c0] == 255
        del bi, bs
    Dall[si] = D; COV[si, idx] = cv; INK[si, idx] = ik
    print(sg, 'mapped', int(ok.sum()), 'covered', int(cv.sum()), round(time.time() - t0), 's', flush=True)
    del S
# any segment: nearest covering segment decides
Dc = np.where(COV, Dall, np.inf); best = Dc.argmin(0); anyc = np.isfinite(Dc.min(0))
anyink = anyc & INK[best, np.arange(N)]
res = {}
for n, (r, c) in enumerate(tiles):
    m = tid == n; nt = int(m.sum()); e = {'r': r, 'c': c, 'n_samples': nt, 'segments': {}}
    for si, sg in enumerate(SEGS):
        mp = int((np.isfinite(Dall[si]) & m).sum())
        if mp == 0:
            continue
        cvn = int((COV[si] & m).sum()); ikn = int((INK[si] & COV[si] & m).sum())
        e['segments'][sg] = {'mapped_fraction': round(mp / nt, 6), 'coverage_fraction': round(cvn / nt, 6),
                             'ink_fraction_of_covered': round(ikn / cvn, 6) if cvn else None,
                             'ink_fraction_of_tile': round(ikn / nt, 6),
                             'min_dist_mm': round(float(Dall[si][m].min()) * VOX_MM, 6)}
    ca = int((anyc & m).sum()); ia = int((anyink & m).sum())
    e['any_segment'] = {'coverage_fraction': round(ca / nt, 6) if nt else None,
                        'ink_fraction_of_covered': round(ia / ca, 6) if ca else None,
                        'ink_fraction_of_tile': round(ia / nt, 6) if nt else None}
    res[f'r{r}_c{c}'] = e
o = {'provenance': PROV, 'strip': '20260701183124-w010-027',
     'what': 'DECL-P4-21 (with DECL-P4-21-A1): organizer ink-label fractions per strip-a tile, numbers only',
     'labels': 'official 20260918 set, ink-labels/2.4um-volume-20260411134726/20260918/{inklabels,supervision}.zarr level 0 '
               '(values 0/255; shape = segment tifxyz grid x 20); read in code only, never displayed, saved as an image or described',
     'labels_sha256': lab_sha,
     'mapping': {'tolerance_vox': TOL, 'tolerance_mm': TOL * VOX_MM,
                 'rule': 'tile mesh vertex -> exact closest point on the segment triangulated surface (certified k-NN + ball '
                         'fallback, tools/sib/p4-excl/uvmap.py, tests 6/6) -> segment UV -> label px round(uv*20)',
                 'sampling': 'one sample per strip mesh vertex (20 x 20 strip px cell); fractions are over those samples'},
     'definitions': {'coverage_fraction': 'samples mapped (<= tol) whose label supervision = 255, over all tile samples',
                     'ink_fraction_of_covered': 'samples with inklabel = 255 among the covered ones',
                     'any_segment': 'covered if any segment covers; ink decided by the nearest covering segment'},
     'inputs': {'strip_mesh_sha256': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif')}, 'grid_json_sha256': sha(gjson)},
     'seconds': round(time.time() - t0, 1), 'tiles': res}
json.dump(o, open(out, 'w'), indent=1); print('done', o['seconds'])
