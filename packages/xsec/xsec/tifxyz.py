import json, os, numpy as np, tifffile

def read(d):
    """Read a tifxyz directory -> (X, Y, Z) float32 arrays (rows, cols) in volume voxel coordinates; invalid = -1."""
    return [tifffile.imread(os.path.join(d, c + ".tif")).astype(np.float32) for c in "xyz"]

def valid_mask(X):
    return (X > 0) & (X != -1)

def write(d, X, Y, Z, meta=None):
    os.makedirs(d, exist_ok=True)
    for c, a in zip("xyz", (X, Y, Z)):
        tifffile.imwrite(os.path.join(d, c + ".tif"), a.astype(np.float32))
    json.dump(meta or {"format": "tifxyz", "type": "seg"}, open(os.path.join(d, "meta.json"), "w"))
