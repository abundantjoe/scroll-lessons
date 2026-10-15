"""Crop a tifxyz to rows whose z lies in [zlo, zhi] and list the exact level-0 chunks a 66-layer trilinear render touches.
Surface is upsampled bilinearly to `sub` vx; normals from finite differences; offsets -32.5..+33.5 (floor..floor+1 corners)."""
import sys, json, os, numpy as np, tifffile
from scipy.ndimage import map_coordinates
src, dst, zlo, zhi = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
sub = 2.0
X, Y, Z = (tifffile.imread(f'{src}/{c}.tif').astype(np.float64) for c in 'xyz')
meta = json.load(open(f'{src}/meta.json')); step = 1 / meta['scale'][0]
valid = (X != -1) & np.isfinite(X)
zr = np.where(valid, Z, np.nan); rowz = np.nanmedian(zr, 1)
rows = np.where((rowz >= zlo) & (rowz <= zhi))[0]; r0, r1 = rows.min(), rows.max() + 1
X, Y, Z, valid = X[r0:r1], Y[r0:r1], Z[r0:r1], valid[r0:r1]
os.makedirs(dst, exist_ok=True)
for c, a in (('x', X), ('y', Y), ('z', Z)): tifffile.imwrite(f'{dst}/{c}.tif', np.where(valid, a, -1).astype(np.float32))
vq = valid[:-1, :-1] & valid[1:, :-1] & valid[:-1, 1:] & valid[1:, 1:]
area = int(vq.sum()) * step * step
m = dict(meta); m.update({'uuid': os.path.basename(dst), 'area_vx2': area, 'area_cm2': area * 8.64**2 / 1e8,
          'bbox': [[float(X[valid].min()), float(Y[valid].min()), float(Z[valid].min())], [float(X[valid].max()), float(Y[valid].max()), float(Z[valid].max())]],
          'source': f'crop rows {r0}..{r1-1} (z {zlo}..{zhi}) of {meta.get("uuid")}'})
json.dump(m, open(f'{dst}/meta.json', 'w'), indent=2)
nr, nc = X.shape; f = step / sub
gr = np.arange(0, nr - 1 + 1e-9, 1 / f); gc = np.arange(0, nc - 1 + 1e-9, 1 / f)
keys = set(); offs = np.concatenate([np.arange(-32.5, 33.6, 2.0), [33.5]])
for i0 in range(0, len(gr), 64):
    R_, C_ = np.meshgrid(gr[i0:i0 + 64], gc, indexing='ij')
    P = np.stack([map_coordinates(A, [R_, C_], order=1) for A in (X, Y, Z)], -1)
    V = map_coordinates(vq.astype(float), [np.minimum(R_, nr - 2), np.minimum(C_, nc - 2)], order=0) > 0.5
    du = np.stack([map_coordinates(A, [R_, np.minimum(C_ + 0.5, nc - 1)], order=1) - map_coordinates(A, [R_, np.maximum(C_ - 0.5, 0)], order=1) for A in (X, Y, Z)], -1)
    dv = np.stack([map_coordinates(A, [np.minimum(R_ + 0.5, nr - 1), C_], order=1) - map_coordinates(A, [np.maximum(R_ - 0.5, 0), C_], order=1) for A in (X, Y, Z)], -1)
    N = np.cross(du, dv); N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-12
    P, N = P[V], N[V]
    for o in offs:
        Q = np.floor(P + o * N)
        for d in ((0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,1,1)):
            q = Q + d; k = np.stack([q[:, 2] // 128, q[:, 1] // 128, q[:, 0] // 128], 1).astype(int)
            keys.update(map(tuple, np.unique(k, axis=0).tolist()))
keys = sorted(keys); json.dump(keys, open(dst + '.chunks.json', 'w'))
zrows = sorted(set(k[0] for k in keys))
print(json.dumps({'rows': [int(r0), int(r1 - 1)], 'grid': [nr, nc], 'area_vx2': area, 'area_mm2': area * 0.00864**2, 'chunks': len(keys),
                  'chunk_rows': {int(z): sum(1 for k in keys if k[0] == z) for z in zrows}}))
