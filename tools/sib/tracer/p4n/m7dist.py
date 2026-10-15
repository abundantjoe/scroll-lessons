# Provenance: Project HERCULES | owner the owner | [id removed]
"""Distance (L2 voxels, capped at CAP) from points in the local m7-L2 frame to the nearest prediction voxel
>= TH (170, the tracer's thresholdedDistance level), exact EDT per 192^3 block with a CAP-voxel halo."""

from __future__ import annotations

import numpy as np
import zarr
from scipy.ndimage import distance_transform_edt

ZP = "/work/p4n/m7l2_local.zarr/0"
TH = 170
CAP = 12


def m7_distance(pts_xyz: np.ndarray, zp: str = ZP, cap: int = CAP) -> np.ndarray:
    a = zarr.open(zp, mode="r")
    Z, Y, X = a.shape
    p = np.asarray(pts_xyz, dtype=np.float64).reshape(-1, 3)
    out = np.full(len(p), np.nan)
    ok = np.isfinite(p).all(1) & (p[:, 0] != -1)
    idx = np.round(p[:, ::-1]).astype(int)                       # zyx
    inside = ok & (idx >= 0).all(1) & (idx < np.array([Z, Y, X])).all(1)
    out[ok & ~inside] = np.inf                                     # outside the local volume: no evidence
    B = 192
    blk = idx[inside] // B
    order = np.flatnonzero(inside)
    keys, inv = np.unique(blk, axis=0, return_inverse=True)
    for k, key in enumerate(keys):
        sel = order[inv.ravel() == k]
        lo = np.maximum(key * B - cap, 0)
        hi = np.minimum(key * B + B + cap, [Z, Y, X])
        sub = np.asarray(a[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]) >= TH
        if not sub.any():
            out[sel] = cap
            continue
        d = distance_transform_edt(~sub)
        q = idx[sel] - lo
        out[sel] = np.minimum(d[q[:, 0], q[:, 1], q[:, 2]], cap)
    return out
