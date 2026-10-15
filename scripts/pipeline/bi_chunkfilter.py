#!/usr/bin/env python3
"""bi_chunkfilter.py: drop the spurious chunks crop_and_chunks.py lists on ragged meshes.

  python -I bi_chunkfilter.py MESH_DIR CHUNKS.json [--margin 64]   (rewrites CHUNKS.json, keeps CHUNKS.json.orig)

crop_and_chunks.py interpolates node coordinates bilinearly with order-1 map_coordinates over the whole grid, so samples
next to invalid (-1) nodes get coordinates pulled toward (-1, -1, -1) and list chunks far from the surface. Every sample
the renderer can take from valid nodes lies inside the bounding box of the valid nodes (bilinear interpolation stays in
the convex hull), moved by at most 33.5 voxels along a unit normal, plus one voxel for the trilinear corners; so a chunk
whose 128^3 box does not intersect bbox +- margin is never read. Default margin 64: the render is grid x 20 px, so edge pixels can lie up to
19 vox beyond the last node row/column (33.5 + 1 + 19 = 53.5 < 64); verified by byte-identical renders from a filtered mirror. Prints counts as JSON.
"""
import argparse, json, os, shutil
import numpy as np, tifffile

ap = argparse.ArgumentParser(); ap.add_argument('mesh'); ap.add_argument('chunks'); ap.add_argument('--margin', type=float, default=64)
ap.add_argument('--chunk', type=int, default=128)
a = ap.parse_args()
X, Y, Z = (tifffile.imread(f'{a.mesh}/{c}.tif').astype(np.float64) for c in 'xyz')
ok = (X > -0.5) & (Y > -0.5) & (Z > -0.5)
lo = np.array([Z[ok].min(), Y[ok].min(), X[ok].min()]) - a.margin; hi = np.array([Z[ok].max(), Y[ok].max(), X[ok].max()]) + a.margin
K = json.load(open(a.chunks)); cs = a.chunk
keep = [k for k in K if all(k[i] * cs < hi[i] and (k[i] + 1) * cs > lo[i] for i in range(3))]
if not os.path.exists(a.chunks + '.orig'): shutil.copy(a.chunks, a.chunks + '.orig')
json.dump(keep, open(a.chunks, 'w'))
print(json.dumps(dict(listed=len(K), kept=len(keep), dropped=len(K) - len(keep), bbox_zyx=[lo.round(1).tolist(), hi.round(1).tolist()])))
