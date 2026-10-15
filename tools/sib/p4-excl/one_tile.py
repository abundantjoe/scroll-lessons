"""All-vertex min distance for ONE tile (same method/meshes/rule as process.py). Coordinates only.
usage: one_tile.py <strip a|b> <r> <c> <npz> <commit> <blob> <struct_dir> <strip_mesh_dir> <grid_json> <out>"""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from process import SEGS, VOX_MM, FLAG_MM, PROV, STRIPNAME, sha

strip, r, c, npz, commit, blob, sdir, mdir, gjson, out = sys.argv[1:11]
r, c = int(r), int(c); key = f'r{r}_c{c}'; t0 = time.time()
g = json.load(open(gjson))
T = int(g['T_px'] if 'T_px' in g else g['T_canvas_px'])
sc = g['canvas_per_grid_scale_rows_cols'] if 'canvas_per_grid_scale_rows_cols' in g else \
    [g['scale_canvas_per_grid']['rows'], g['scale_canvas_per_grid']['cols']]
assert sc[0] == sc[1] and float(sc[0]).is_integer(); s = int(sc[0])
X = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
i0, i1 = -(-r * T // s), -(-(r + 1) * T // s); j0, j1 = -(-c * T // s), -(-(c + 1) * T // s)
sub = X[i0:i1, j0:j1]; valid = (sub >= 0).all(-1) & np.isfinite(sub).all(-1)
V = sub[valid].astype(np.float64); del X
zz = np.load(npz)[key]
subset = bool(np.isin(np.ascontiguousarray(zz.astype(np.float32)).view('V12').ravel(),
                      np.ascontiguousarray(V.astype(np.float32)).view('V12').ravel()).all())
per, npz_per, info = {}, {}, {}
for sg in SEGS:
    S = Surface(np.load(f'{sdir}/{sg}.npz')['grid'])
    d, arg, inf = S.min_dist(V)                       # exact, no early stop
    dn = S.min_dist(zz.astype(np.float64))[0]
    per[sg], npz_per[sg], info[sg] = d, dn, dict(inf, argmin_vertex_xyz=V[arg].round(3).tolist())
    print(sg, round(d * VOX_MM, 6), flush=True); del S
best = min(per, key=per.get); m = per[best] * VOX_MM
res = {'provenance': PROV, 'strip': STRIPNAME[strip], 'tile': key,
       'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
       'what': 'all-vertex minimum 3-D point-to-triangulated-surface distance (exact, CORR-RETRACE-RULE form b, '
               'no early stop) from every valid mesh vertex of the tile to the 8 labelled segment meshes',
       'n_vertices': int(len(V)), 'min_vox': round(per[best], 4), 'min_mm': round(m, 6), 'segment': best,
       'labelled_adjacent': bool(m < FLAG_MM), 'flag_rule': 'min_mm < 1.2',
       'per_segment_mm': {k: round(v * VOX_MM, 6) for k, v in per.items()},
       'npz_subset': {'n_points': int(len(zz)), 'is_subset_of_tile_vertices': subset,
                      'min_mm': round(min(npz_per.values()) * VOX_MM, 6),
                      'per_segment_mm': {k: round(v * VOX_MM, 6) for k, v in npz_per.items()}},
       'nearest_detail': info[best],
       'vertex_rule': f'grid rows [{i0},{i1}) cols [{j0},{j1}): gi*{s} in [r*T,(r+1)*T), T={T}; valid = x,y,z >= 0',
       'voxel_mm': VOX_MM, 'voxel_source_sha256': '881bf77fc0f02a91040755da25d54ad958e290a528ec61489e411937112fba4d',
       'inputs': {'tile_points_npz': {'branch': f'claude/gifted-bell-gavnl5-sib-p4-tiles-{strip}', 'commit': commit,
                                      'git_blob': blob, 'sha256': sha(npz)},
                  'grid_json_sha256': sha(gjson),
                  'strip_mesh_sha256': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif', 'meta.json')},
                  'labelled_meshes_compact_sha256': {sg: sha(f'{sdir}/{sg}.npz') for sg in SEGS},
                  'labelled_meshes_source': 'logs/sib/p4-excl/downloads.jsonl (sha256 of every official file)'},
       'seconds': round(time.time() - t0, 1)}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('n_vertices', 'min_mm', 'segment', 'labelled_adjacent')}), res['npz_subset']['min_mm'])
