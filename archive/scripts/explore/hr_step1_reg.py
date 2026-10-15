"""HR step 1: global registration of the 1.129um-scan surface volume (published at 2.258 um/px,
source_group=1) to the 2.4 um surface volume of the SAME segment 20231210121321.
Uses level-5 overviews of both stores (76.8 um/px and 72.256 um/px), mean-over-z renders,
scale search + FFT cross-correlation. Writes stats/explore/hr_reg_global.json."""
import os, json, numpy as np, zarr
from scipy.ndimage import zoom, gaussian_filter
from numpy.fft import rfft2, irfft2

S = "/tmp/claude-0/-home-user-megara/0338ab0f-b99b-560d-a818-e4da621f98e6/scratchpad/reg"
OUT = "/home/user/megara/stats/explore"

def render(store, level):
    a = zarr.open(store, mode="r")[str(level)]
    v = np.asarray(a[:]).astype(np.float32)          # (K,H,W)
    m = (v > 0).any(0)
    r = v.mean(0)
    return r, m

r24, m24 = render(f"{S}/s24.zarr", 5)   # 76.8 um/px
r11, m11 = render(f"{S}/s11.zarr", 5)   # 72.256 um/px
print("r24", r24.shape, "r11", r11.shape, "cov", m24.mean(), m11.mean(), flush=True)

# resample r11 onto the 76.8 um grid of r24: factor 72.256/76.8
def prep(x, m):
    x = np.where(m, x, 0.0).astype(np.float32)
    x = x - (x[m].mean() if m.any() else 0.0)
    return np.where(m, x, 0.0)

best = None
for f in np.arange(0.930, 0.950, 0.0010):     # 72.256/76.8 = 0.94083
    z11 = zoom(r11, f, order=1); zm11 = zoom(m11.astype(np.float32), f, order=1) > 0.5
    A = prep(gaussian_filter(r24, 1.0), m24)
    B = prep(gaussian_filter(z11, 1.0), zm11)
    H = max(A.shape[0], B.shape[0]) * 2; W = max(A.shape[1], B.shape[1]) * 2
    FA = rfft2(A, (H, W)); FB = rfft2(B, (H, W))
    cc = irfft2(FA * np.conj(FB), (H, W))
    # normalise by overlap count
    ma = rfft2(m24.astype(np.float32), (H, W)); mb = rfft2(zm11.astype(np.float32), (H, W))
    n = np.maximum(irfft2(ma * np.conj(mb), (H, W)), 1.0)
    sc = cc / n
    sc[n < 0.2 * min(m24.sum(), zm11.sum())] = -1e9
    iy, ix = np.unravel_index(np.argmax(sc), sc.shape)
    dy = iy if iy < H // 2 else iy - H
    dx = ix if ix < W // 2 else ix - W
    # correlation coefficient at that shift
    val = float(sc[iy, ix])
    if best is None or val > best[0]:
        best = (val, float(f), int(dy), int(dx))
    print(f"f={f:.4f} peak {val:.2f} dy {dy} dx {dx}", flush=True)

val, f, dy, dx = best
# mapping: pixel p24 (level5, 76.8um) corresponds to p11_level5 = (p24 - d)/f
# in LEVEL 0 pixels: p11_0 = 32 * ((p24_0/32) - d)/f   with d=(dy,dx)
scale0 = 1.0 / f                    # level0 px_11 per level0 px_24 ... careful: grids differ
res = dict(level=5, pitch24=76.8, pitch11=72.256, best_zoom=f, peak=val, dy_l5=dy, dx_l5=dx,
           canvas_ratio=[54160 / 51000, 42460 / 39980], pitch_ratio=2.4 / 2.258,
           note="p11_level5 = (p24_level5 - d)/f ; level0: p11_0 = 32*((p24_0/32) - d)/f")
json.dump(res, open(os.path.join(OUT, "hr_reg_global.json"), "w"), indent=1)
print("BEST", res)
