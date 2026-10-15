# Provenance: Project HERCULES | [id removed]
"""Resample the 8.64 um organizer surface volume to Hecate's 9.6 um sampling (factor 0.9 on all three axes).
scipy.ndimage.zoom order=1 (trilinear), grid_mode=True so output voxel pitch = 8.64/0.9 = 9.6 um exactly;
physical extent preserved. usage: resample.py <in.zarr (group with array 0)> <out.npy> <out.json>"""
import sys, json, numpy as np, zarr, time
from scipy.ndimage import zoom
src = zarr.open(sys.argv[1], mode='r')['0']; v = np.asarray(src[:]); t = time.time()
f = 8.64 / 9.6
out = zoom(v, f, order=1, grid_mode=True, mode='grid-constant', prefilter=False)
np.save(sys.argv[2], out.astype(np.uint8))
m = {'in_shape': list(v.shape), 'in_um': 8.64, 'out_shape': list(out.shape), 'out_um': 9.6, 'zoom': f, 'method': 'scipy.ndimage.zoom order=1 grid_mode=True prefilter=False',
     'in_mean': float(v.mean()), 'out_mean': float(out.mean()), 'in_nonzero_frac': float((v[v.shape[0]//2] > 0).mean()), 'out_nonzero_frac': float((out[out.shape[0]//2] > 0).mean()), 'seconds': round(time.time()-t, 1)}
json.dump(m, open(sys.argv[3], 'w'), indent=1); print(m)
