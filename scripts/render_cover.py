#!/usr/bin/env python
"""R-COVER: papyrus coverage of a render = fraction of pixels whose maximum over the rendered layers exceeds the
papyrus threshold (60 on the 8-bit scans used here: air is 30-40 under the export windows, papyrus 80-130; the w040
control segment scores 0.997, an air/void window 0.28). Bar: >= 0.80 before any inference. Also returns the per-cell
coverage grid when --cell-px is given (render without auto-crop, cell = grid cell of the tifxyz trace).
Usage: render_cover.py <render.zarr> <out.json> [--thr 60] [--bar 0.8] [--cell-px 20] [--step 2]"""
import argparse, json, sys, zarr, numpy as np

def coverage(render, thr=60, step=2, cell_px=None):
    a = zarr.open_group(render, mode='r')['0']; n = a.shape[0]
    mx = np.asarray(a[n // 2]).copy()
    for i in range(0, n, step): mx = np.maximum(mx, np.asarray(a[i]))
    cov = (mx > thr)
    r = dict(render=render, thr=thr, n_layers=n, layer_step=step, coverage=round(float(cov.mean()), 4),
             nonzero_mid=round(float((np.asarray(a[n // 2]) > 0).mean()), 4), shape=list(a.shape))
    if cell_px:
        H, W = cov.shape; h, w = H // cell_px, W // cell_px
        r['cell_px'] = cell_px; r['cell_coverage'] = cov[:h * cell_px, :w * cell_px].reshape(h, cell_px, w, cell_px).mean((1, 3)).round(3).tolist()
    return r

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('render'); ap.add_argument('out'); ap.add_argument('--thr', type=int, default=60); ap.add_argument('--bar', type=float, default=0.80)
    ap.add_argument('--cell-px', type=int, default=None); ap.add_argument('--step', type=int, default=2)
    a = ap.parse_args(); r = coverage(a.render, a.thr, a.step, a.cell_px); r['bar'] = a.bar; r['passed'] = bool(r['coverage'] >= a.bar)
    json.dump(r, open(a.out, 'w')); print(f"R-COVER {'PASS' if r['passed'] else 'VOID-COVER'}: coverage {r['coverage']:.3f} (bar >= {a.bar}, thr {a.thr}), non-zero mid {r['nonzero_mid']:.3f}")
    sys.exit(0 if r['passed'] else 1)
