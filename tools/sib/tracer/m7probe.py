# Provenance: Project HERCULES | owner the owner | [id removed]
"""Probe the official m7 surface prediction (PHerc1203, streamed anonymously from S3, chunk-cached
on local disk) at mesh points: Euclidean distance (vox) from each point to the nearest voxel with
value >= 170 (the tracer's threshold), searched in a (2r+1)^3 window; capped at r + 1.
Numbers only; no image is written or viewed."""

from __future__ import annotations

import numpy as np

M7_KEY = ("vesuvius-challenge-open-data/PHerc1203/representations/predictions/surfaces/"
          "20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr/0")
TH = 170


def open_m7(cache_dir: str = "/work/m7cache"):
    import fsspec
    import zarr
    fs = fsspec.filesystem("simplecache", target_protocol="s3", target_options={"anon": True},
                           cache_storage=cache_dir)
    return zarr.open_array(fs.get_mapper(M7_KEY), mode="r")


def dist_to_prediction(arr, pts_xyz: np.ndarray, r: int = 6) -> np.ndarray:
    """pts_xyz (N, 3) in voxels (x, y, z). Groups points by 192^3 chunk to read each window once."""
    pts = np.asarray(pts_xyz, dtype=np.float64)
    out = np.full(len(pts), float(r + 1))
    cz, cy, cx = arr.chunks
    zyx = np.round(pts[:, ::-1]).astype(np.int64)
    key = (zyx[:, 0] // cz) * 10 ** 8 + (zyx[:, 1] // cy) * 10 ** 4 + (zyx[:, 2] // cx)
    off = np.stack(np.meshgrid(*[np.arange(-r, r + 1)] * 3, indexing="ij"), -1).reshape(-1, 3)
    offd = np.linalg.norm(off, axis=1)
    for k in np.unique(key):
        idx = np.nonzero(key == k)[0]
        lo = np.maximum(zyx[idx].min(0) - r, 0)
        hi = np.minimum(zyx[idx].max(0) + r + 1, np.array(arr.shape))
        block = arr[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] >= TH
        for i in idx:
            q = zyx[i] - lo + off
            ok = np.all((q >= 0) & (q < np.array(block.shape)), axis=1)
            hit = np.zeros(len(off), bool)
            hit[ok] = block[q[ok, 0], q[ok, 1], q[ok, 2]]
            if hit.any():
                # sub-voxel: distance from the exact point to the voxel centre of each hit
                c = zyx[i] + off[hit]
                out[i] = float(np.min(np.linalg.norm(c - pts[i, ::-1], axis=1)))
    return out
