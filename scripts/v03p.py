import sys, os, numpy as np
from scipy.ndimage import gaussian_filter
d, pitch = sys.argv[1], float(sys.argv[2])
m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
pk = np.load(os.path.join(d, "peak.npy")).astype(np.float32); s = 0.25 * 1000 / pitch
G = gaussian_filter(np.where(m, pk, 0), s) / np.maximum(gaussian_filter(m.astype(np.float32), s), 1e-3)
v = G[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; z = np.where(m, (G - med) / mad, 0).astype(np.float16)
for f in ("top", "bot"):
    np.save(os.path.join(d, f"s_{f}_v0.3p.npy"), z); np.save(os.path.join(d, f"s_{f}_v0.3p_u8.npy"), (255 * np.clip(0.5 + z.astype(np.float32) / 8, 0, 1)).astype(np.uint8))
print(d, "v0.3p written")
