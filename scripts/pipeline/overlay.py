"""Ink overlay on dimmed CT, fixed absolute scale (same for every patch): ensemble = mean of the three villa models'
_reverse maps (Erwin's direction convention) at d=+1 (layers 26-42); alpha = clip((p-0.40)/(0.70-0.40), 0, 1); CT = layer 34
(d=+1), percentile-stretched for display only and dimmed to 55 %. Optional tiles.json: tiles failing the CT layer-profile
test (peak not in 30-36) are darkened and outlined in red."""
import sys, json, numpy as np, tifffile, zarr
from PIL import Image, ImageDraw
render, inkdir, out = sys.argv[1], sys.argv[2], sys.argv[3]; tiles = sys.argv[4] if len(sys.argv) > 4 else None
r = zarr.open(render, mode='r')['0']; ct = np.asarray(r[34]).astype(np.float32); valid = (np.asarray(r[33]) > 0)
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import bi_common as C  # noqa: E401,E402
ms = C.MODELS
P = np.mean([tifffile.imread(f'{inkdir}/{m}__s26_reverse.tif').astype(np.float32) / 255. for m in ms], 0)
v = ct[valid]; lo, hi = np.percentile(v, 1), np.percentile(v, 99.5); base = np.clip((ct - lo) / (hi - lo), 0, 1) * 0.55
a = np.clip((P - 0.40) / 0.30, 0, 1); col = np.array([1.0, 0.62, 0.12])
rgb = base[..., None] * (1 - a[..., None]) + col * a[..., None]; rgb[~valid] = 0
img = Image.fromarray((rgb * 255).astype(np.uint8)); dr = ImageDraw.Draw(img)
if tiles:
    T = json.load(open(tiles)); H, W = valid.shape
    for k, t in T.items():
        b, c = int(k[1]), int(k[3]); r0, r1 = [(0, 247), (247, 494), (494, 740)][b]; c0, c1 = c * 1200, (c + 1) * 1200
        if not (30 <= t['peak_layer'] <= 36):
            arr = np.asarray(img).copy(); arr[r0:r1, c0:c1] = (arr[r0:r1, c0:c1] * 0.35).astype(np.uint8); img = Image.fromarray(arr); dr = ImageDraw.Draw(img)
            dr.rectangle([c0 + 2, r0 + 2, c1 - 3, r1 - 3], outline=(220, 30, 30), width=4)
img.save(out)
ok = valid & (a > 0); print('ink-overlay pixels (p>0.40):', round(float(ok.sum() / valid.sum()), 4), '| p>0.55:', round(float((valid & (P > 0.55)).sum() / valid.sum()), 4),
      '| ensemble p50/p99:', round(float(np.median(P[valid])), 3), round(float(np.percentile(P[valid], 99)), 3))
