"""Mean-pool the face-aligned depth stacks 8x and standardise (RULES S1-v5). Writes ds8_x.npy (23,H8,W8) float32 and ds8_y.npy/ds8_m.npy."""
import sys, os, numpy as np
d = sys.argv[1]; F = 8
m = ((np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)).astype(np.float32)
H, W = m.shape; H8, W8 = H // F, W // F
def pool(x): return x[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
mp = pool(m); chans = []
for f in ("top", "bot"):
    P = np.load(os.path.join(d, f"I_stack_{f}.npy"), mmap_mode="r")
    for i in range(P.shape[0]):
        x = np.asarray(P[i]).astype(np.float32); xm = pool(x * m) / np.maximum(mp, 1e-3)
        v = xm[mp > 0.5]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6
        chans.append(np.where(mp > 0.5, (xm - med) / mad, 0).astype(np.float32))
chans.append(mp)
np.save(os.path.join(d, "ds8_x.npy"), np.stack(chans)); np.save(os.path.join(d, "ds8_m.npy"), mp)
if os.path.exists(os.path.join(d, "cls_text.npy")):
    t = pool(np.load(os.path.join(d, "cls_text.npy")).astype(np.float32)); b = pool(np.load(os.path.join(d, "cls_blank.npy")).astype(np.float32))
    y = np.full((H8, W8), -1, np.int8); y[b > 0.5] = 0; y[t > 0.5] = 1; np.save(os.path.join(d, "ds8_y.npy"), y)
print(d, "ds8 written", len(chans), H8, W8)
