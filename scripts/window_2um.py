#!/usr/bin/env python
"""Choose the 1 cm^2 render window of a level-2 traced rescan patch (B-2UM scale-down): the k x k block of tifxyz grid
cells with the most valid cells (ties: most on-sheet area), k = 52 cells = 4160 output px at --scale-segmentation 4
(one grid cell = 20 L2 voxels = 80 level-0 voxels = 80 px at scale 1). Writes <patch>/window_2um.json with the
renderer crop (--crop-x/--crop-y in output px) and the window's area in cm^2 from the cell geometry. The maps are
never consulted (they do not exist yet); only the trace geometry decides."""
import argparse, json, os
import numpy as np, tifffile

def choose(patch_dir, k=52, px_per_cell=80, um_l2=9.612):
    x, y, z = [tifffile.imread(os.path.join(patch_dir, f'{c}.tif')).astype(np.float64) for c in 'xyz']
    valid = (x > -1) & (y > -1) & (z > -1); pts = np.stack([x, y, z], -1)
    du = pts[1:, :-1] - pts[:-1, :-1]; dv = pts[:-1, 1:] - pts[:-1, :-1]
    cv = valid[1:, :-1] & valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, 1:]
    cm2 = np.linalg.norm(np.cross(du, dv), axis=-1) * cv * (um_l2 * 1e-4) ** 2
    H, W = cv.shape
    if H < k or W < k: raise SystemExit(f'patch grid {H}x{W} cells smaller than the {k}x{k} window')
    P = lambda a: np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    A, N = P(cm2), P(cv.astype(np.int64))
    # R-COVER: when the level-2 check render's per-cell papyrus coverage exists, the window maximises coverage first
    covf = os.path.join(patch_dir, 'render_l2_cover.json'); C = None
    if os.path.exists(covf):
        cc = np.array(json.load(open(covf))['cell_coverage'], dtype=np.float64)
        g = np.zeros((H, W)); hh, ww = min(H, cc.shape[0]), min(W, cc.shape[1]); g[:hh, :ww] = cc[:hh, :ww]; C = P(g)
    best = None
    for i in range(H - k + 1):
        for j in range(W - k + 1):
            n = N[i + k, j + k] - N[i, j + k] - N[i + k, j] + N[i, j]; a = A[i + k, j + k] - A[i, j + k] - A[i + k, j] + A[i, j]
            c = (C[i + k, j + k] - C[i, j + k] - C[i + k, j] + C[i, j]) / (k * k) if C is not None else 0.0
            key = (round(c, 3), n, a)
            if best is None or key > best[0]: best = (key, int(n), float(a), i, j, float(c))
    _, n, a, i, j, c = best
    return dict(patch_dir=patch_dir, k_cells=k, px_per_cell=px_per_cell, cell_i0=i, cell_j0=j, crop_y=i * px_per_cell, crop_x=j * px_per_cell,
                crop_px=k * px_per_cell, valid_cells=n, total_cells=k * k, window_area_cm2=round(a, 4), patch_area_cm2=round(float(cm2.sum()), 4),
                window_coverage_l2=(round(c, 4) if C is not None else None), coverage_source=(covf if C is not None else None),
                grid_cells=[H, W], um_l2=um_l2, note='crop in output px of vc_render_tifxyz at --scale 1 --scale-segmentation 4; 4160 px = 0.9994 cm2 nominal at 2.403 um; window chosen by L2-render papyrus coverage, then valid cells')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('patch_dir'); ap.add_argument('--k', type=int, default=52)
    a = ap.parse_args(); r = choose(a.patch_dir, a.k)
    json.dump(r, open(os.path.join(a.patch_dir, 'window_2um.json'), 'w'), indent=1)
    print(json.dumps(r))
