"""v0.3f: face intensities at the D1 depths, smoothed 0.25 mm, standardised. Needs the raw stack."""
import sys, os, numpy as np, zarr, time
from scipy.ndimage import gaussian_filter
store, level, y0, y1, x0, x1, k0, k1, d, pitch = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:9]), sys.argv[9], float(sys.argv[10])
arr = zarr.open(store, mode="r")[level]; H, W, K = y1 - y0, x1 - x0, k1 - k0
kt = np.load(os.path.join(d, "k_top.npy")).astype(np.float32); kb = np.load(os.path.join(d, "k_bot.npy")).astype(np.float32)
m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
I = {"top": np.zeros((H, W), np.float32), "bot": np.zeros((H, W), np.float32)}
def sample(p, k):
    k = np.clip(np.nan_to_num(k, nan=0.0, posinf=K - 1.0, neginf=0.0), 0, K - 1.001); kk = np.floor(k).astype(np.int32); f = k - kk
    ii, jj = np.indices(k.shape); return p[kk, ii, jj] * (1 - f) + p[kk + 1, ii, jj] * f
T = 256; t0 = time.time()
for r in range(0, H, T):
    r1 = min(r + T, H); p = arr[k0:k1, y0 + r:y0 + r1, x0:x1].astype(np.float32)
    I["top"][r:r1] = sample(p, kt[r:r1] + 0.0); I["bot"][r:r1] = sample(p, kb[r:r1] - 2.5)
    if r % 2048 == 0: print(f"rows {r1}/{H} {time.time()-t0:.0f}s", flush=True)
s = 0.25 * 1000 / pitch
for f in ("top", "bot"):
    G = gaussian_filter(np.where(m, I[f], 0), s) / np.maximum(gaussian_filter(m.astype(np.float32), s), 1e-3)
    v = G[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; z = np.where(m, (G - med) / mad, 0).astype(np.float16)
    np.save(os.path.join(d, f"s_{f}_v0.3f.npy"), z); np.save(os.path.join(d, f"s_{f}_v0.3f_u8.npy"), (255 * np.clip(0.5 + z.astype(np.float32) / 8, 0, 1)).astype(np.uint8))
    np.save(os.path.join(d, f"I_{f}_d1.npy"), I[f].astype(np.float16))
print(d, "v0.3f written")
