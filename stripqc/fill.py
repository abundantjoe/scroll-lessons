"""Reflect-fill the blank margin of a rendered surface volume, for ink inference only.

Why: villa's flat ink inference slides 128 px patches (stride 64, Hann blending) over the render, normalises each patch
with a robust median/MAD transform computed over ALL its voxels (no mask), and the models use InstanceNorm. Thin strips
rendered with vc_render_tifxyz carry blank (all-zero) rows at their edges, so every patch that touches an edge sees
shifted statistics. Measured effects: false ink bands on one scroll, real ink roughly halved on another
(docs/RESULTS.md). The partial fix fills the blank pixels with CT reflected from just inside the valid region, so no patch sees the
blank-margin zeros; validity, scoring and display must keep using the ORIGINAL render (filled pixels are never scored).

  python -m stripqc.fill SRC_render.zarr DST_render_fill.zarr
"""
import argparse
import json
import os
import shutil

import numpy as np
from scipy.ndimage import distance_transform_edt


def reflect_fill(A):
    """A: (D, H, W) render (layers, rows, cols); a pixel is blank when it is 0 in every layer.
    Per column, rows above the first / below the last valid row take the layer vector reflected about that row
    (row t0 - k <- row t0 + k, clamped to the valid run); pixels still blank (empty columns, holes) take their nearest
    valid pixel. Valid pixels are returned unchanged. -> (filled copy, stats dict)."""
    A = np.asarray(A)
    if A.ndim != 3:
        raise ValueError(f'expected (D, H, W), got {A.shape}')
    valid = (A > 0).any(0)
    D, H, W = A.shape
    out = A.copy()
    rows = np.arange(H)
    n_reflect = 0
    for j in range(W):
        rv = np.flatnonzero(valid[:, j])
        if rv.size < 2:
            continue
        t0, t1 = rv[0], rv[-1]
        up, dn = rows < t0, rows > t1
        if up.any():
            out[:, rows[up], j] = A[:, np.minimum(2 * t0 - rows[up], t1), j]
        if dn.any():
            out[:, rows[dn], j] = A[:, np.maximum(2 * t1 - rows[dn], t0), j]
        n_reflect += int(up.sum() + dn.sum())
    v2 = (out > 0).any(0)
    n_nn = int((~v2).sum())
    if n_nn and v2.any():
        _, (iy, ix) = distance_transform_edt(~v2, return_indices=True)
        m = ~v2
        out[:, m] = out[:, iy[m], ix[m]]
    stats = dict(shape=list(A.shape), valid_px=int(valid.sum()), reflected_px=n_reflect, nearest_px=n_nn,
                 still_blank_px=int((~(out > 0).any(0)).sum()))
    return out, stats


def fill_zarr(src, dst):
    """Read SRC/0 (zarr v2 array written by vc_render_tifxyz), write the filled copy to DST/0 (same chunks/codec)."""
    import zarr
    if os.path.realpath(src) == os.path.realpath(dst):
        raise ValueError('dst must differ from src: the original render is needed for validity and scoring')
    S = zarr.open(os.path.join(src, '0'), mode='r')
    out, stats = reflect_fill(S[:])
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(dst, f))
    Z = zarr.open(os.path.join(dst, '0'), mode='w', shape=out.shape, chunks=S.chunks, dtype=out.dtype,
                  compressor=S.compressor, fill_value=0, dimension_separator='/')
    Z[:] = out
    stats.update(src=src, dst=dst, mode='reflect')
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--mode', default='reflect', choices=['reflect'])
    a = ap.parse_args(argv)
    print(json.dumps(fill_zarr(a.src, a.dst)))


if __name__ == '__main__':
    main()
