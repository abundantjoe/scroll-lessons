"""Build compact per-segment structures from fetched tifxyz (coords only) and log sha256."""
import sys, json, time, hashlib, os, glob
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface, save_compact
SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
out = {}
for d in sorted(glob.glob(SRC + '/2*')):
    sid = os.path.basename(d); t = time.time()
    g = np.stack([tifffile.imread(f'{d}/{c}.tif') for c in 'xyz'], -1)
    p = f'{DST}/{sid}.npz'
    meta = json.load(open(d + '/meta.json'))
    save_compact(p, g, meta)
    S = Surface(np.load(p)['grid'])
    out[sid] = {'grid_shape': list(g.shape[:2]), 'valid_vertices': int(len(S.V)), 'valid_quads': S.n_quads,
                'triangles': 2 * S.n_quads, 'max_edge_vox': round(S.L, 4),
                'bbox_vox': [S.V.min(0).round(2).tolist(), S.V.max(0).round(2).tolist()],
                'meta_bbox': meta['bbox'], 'compact_file': os.path.basename(p), 'compact_bytes': os.path.getsize(p),
                'compact_sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'build_s': round(time.time() - t, 1)}
    print(sid, out[sid]); del S
json.dump(out, open(DST + '/structures.json', 'w'), indent=1)
