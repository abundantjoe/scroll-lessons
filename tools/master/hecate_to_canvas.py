#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Map Hecate's 9.6 um 2-D probability PNG (uint8 = round(255 p)) back onto the 8.64 um surface-volume canvas (H, W) by bilinear
resize (an upsample by 1/0.9), writing a float32 tif in [0,1] for baseline_eval.py, plus a quarter-size PNG.
usage: hecate_to_canvas.py <in.png> <H> <W> <out.tif> <out_q4.png>; with 'mean' as in.png: average two tifs: hecate_to_canvas.py mean a.tif b.tif out.tif out_q4.png"""
import sys, numpy as np, cv2, tifffile
if sys.argv[1] == 'mean':
    m = (tifffile.imread(sys.argv[2]).astype(np.float32) + tifffile.imread(sys.argv[3]).astype(np.float32)) / 2
else:
    p = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED); assert p.ndim == 2 and p.dtype == np.uint8, p.shape
    H, W = int(sys.argv[2]), int(sys.argv[3]); m = cv2.resize(p.astype(np.float32) / 255.0, (W, H), interpolation=cv2.INTER_LINEAR)
tifffile.imwrite(sys.argv[4], m.astype(np.float32))
cv2.imwrite(sys.argv[5], cv2.resize(np.clip(m * 255, 0, 255).astype(np.uint8), None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA))
print(sys.argv[4], m.shape, 'mean', round(float(m.mean()), 4), 'p99', round(float(np.percentile(m, 99)), 4))
