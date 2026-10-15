"""Geometry only (no raster read): for strip-a tiles, which labelled segments' surfaces cover each tile
and the tile -> segment UV correspondence (nearest-surface, via nearest segment vertex).
Coverage(t) = fraction of the tile's valid vertices with exact point-to-surface distance <= t vox."""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from process import SEGS, VOX_MM, PROV, sha
mdir, gjson, sdir, out, mapout = sys.argv[1:6]
TOLS = [2.0, 20.0]                       # vox: 4.8 um and one grid step (48 um)
t0 = time.time(); g = json.load(open(gjson)); T = int(g['T_canvas_px']); s = 20
X = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
tiles = [(r, c) for r in range(0, 6) for c in range(9, 20)]
P, tid, nv = [], [], {}
for n, (r, c) in enumerate(tiles):
    i0, i1 = -(-r * T // s), -(-(r + 1) * T // s); j0, j1 = -(-c * T // s), -(-(c + 1) * T // s)
    sub = X[i0:i1, j0:j1]; v = (sub >= 0).all(-1) & np.isfinite(sub).all(-1)
    P.append(sub[v].astype(np.float64)); tid.append(np.full(int(v.sum()), n)); nv[n] = int(v.sum())
del X; P = np.concatenate(P); tid = np.concatenate(tid)
res = {f'r{r}_c{c}': {'r': r, 'c': c, 'n_vertices': nv[n], 'segments': {}} for n, (r, c) in enumerate(tiles)}
maps = {}
for sg in SEGS:
    S = Surface(np.load(f'{sdir}/{sg}.npz')['grid'])
    dv, vi = S.tree.query(P, workers=4)
    cand = np.nonzero(dv - S.Lc <= max(TOLS))[0]
    d = np.full(len(P), np.inf)
    for k in range(0, len(cand), 200000):
        ix = cand[k:k + 200000]
        d[ix] = np.minimum(dv[ix], S._batch_dist(P[ix], np.full(len(ix), max(TOLS) + S.Lc)))
    ij = S.ij[vi]                        # nearest segment vertex grid (row, col)
    for n, (r, c) in enumerate(tiles):
        m = tid == n
        if not m.any():
            continue
        dd = d[m]; cov = {f'{t:g}vox': float((dd <= t).mean()) for t in TOLS}
        if cov[f'{max(TOLS):g}vox'] > 0:
            sel = dd <= max(TOLS)
            gij = ij[m][sel]
            res[f'r{r}_c{c}']['segments'][sg] = {
                'coverage': cov, 'min_dist_mm': round(float(dd.min()) * VOX_MM, 6),
                'segment_grid_rows': [int(gij[:, 0].min()), int(gij[:, 0].max())],
                'segment_grid_cols': [int(gij[:, 1].min()), int(gij[:, 1].max())]}
            maps[f'r{r}_c{c}__{sg}'] = gij.astype(np.int32)
    print(sg, round(time.time() - t0), 's', flush=True); del S
for k, v in res.items():
    for t in TOLS:
        # union coverage over segments needs per-point min: recompute cheaply from stored per-segment is not possible; flag via max
        v[f'coverage_max_over_segments_{t:g}vox'] = max([x['coverage'][f'{t:g}vox'] for x in v['segments'].values()] or [0.0])
np.savez_compressed(mapout, **maps)
o = {'provenance': PROV, 'what': 'DECL-P4-21 geometry part: labelled-segment surface coverage of strip-a tiles w010-027 '
     'r0-r5 c9-c19 and the tile -> segment UV correspondence (nearest segment vertex; UV tolerance +-1 grid cell = 20 label px). '
     'No label raster, image or map pixel was read.',
     'ink_fraction': 'NOT COMPUTED: needs label raster pixel reads, which the builder integrity rule forbids; see ASK.md',
     'mapping': {'tolerances_vox': TOLS, 'tolerances_mm': [t * VOX_MM for t in TOLS],
                 'uv_rule': 'tile vertex -> nearest vertex (row, col) of the segment tifxyz grid; label px = grid index / 0.05 (+-20 px)',
                 'coverage_rule': 'fraction of the tile valid vertices with exact point-to-triangulated-surface distance <= tol'},
     'inputs': {'strip_mesh_sha256': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif')}, 'grid_json_sha256': sha(gjson),
                'labelled_meshes': 'logs/sib/p4-excl/downloads.jsonl'},
     'uv_map_file': 'container scratch (not committed), sha256 ' + sha(mapout), 'seconds': round(time.time() - t0, 1), 'tiles': res}
json.dump(o, open(out, 'w'), indent=1)
print('done', o['seconds'])
