"""S1-v1: score_face = sum_δ w_face(δ) I(k_face+δ), G 0.25 mm in the mask, z-scored. --dump writes the per-δ samples (float16) for template measurement."""
import sys, os, json, argparse, numpy as np, zarr, time
from scipy.ndimage import gaussian_filter
ap = argparse.ArgumentParser(); ap.add_argument("store"); ap.add_argument("level"); ap.add_argument("y0", type=int); ap.add_argument("y1", type=int)
ap.add_argument("x0", type=int); ap.add_argument("x1", type=int); ap.add_argument("k0", type=int); ap.add_argument("k1", type=int); ap.add_argument("d"); ap.add_argument("pitch", type=float)
ap.add_argument("--template", default=None); ap.add_argument("--tag", default="v1a"); ap.add_argument("--dump", action="store_true"); a = ap.parse_args()
DELTAS = list(range(-4, 7)); arr = zarr.open(a.store, mode="r")[a.level]; H, W, K = a.y1 - a.y0, a.x1 - a.x0, a.k1 - a.k0
kt = np.load(os.path.join(a.d, "k_top.npy")).astype(np.float32); kb = np.load(os.path.join(a.d, "k_bot.npy")).astype(np.float32)
m = (np.load(os.path.join(a.d, "mask_top.npy")) > 0) & (np.load(os.path.join(a.d, "mask_bot.npy")) > 0)
def sample(p, k):
    k = np.clip(np.nan_to_num(k, nan=0.0, posinf=K - 1.0, neginf=0.0), 0, K - 1.001); kk = np.floor(k).astype(np.int32); f = k - kk
    ii, jj = np.indices(k.shape); return p[kk, ii, jj] * (1 - f) + p[kk + 1, ii, jj] * f
T = json.load(open(a.template)) if a.template else None
score = {f: np.zeros((H, W), np.float32) for f in ("top", "bot")}
dump = {f: np.lib.format.open_memmap(os.path.join(a.d, f"I_stack_{f}.npy"), mode="w+", dtype=np.float16, shape=(len(DELTAS), H, W)) for f in ("top", "bot")} if a.dump else None
Tt = 256; t0 = time.time()
for r in range(0, H, Tt):
    r1 = min(r + Tt, H); p = arr[a.k0:a.k1, a.y0 + r:a.y0 + r1, a.x0:a.x1].astype(np.float32)
    for f, km in (("top", kt), ("bot", kb)):
        for i, dl in enumerate(DELTAS):
            v = sample(p, km[r:r1] + dl)
            if dump is not None: dump[f][i, r:r1] = v.astype(np.float16)
            if T is not None: score[f][r:r1] += T["w"][f][i] * v
    if r % 2048 == 0: print(f"rows {r1}/{H} {time.time()-t0:.0f}s", flush=True)
if dump is not None:
    for f in dump: dump[f].flush()
if T is not None:
    s = 0.25 * 1000 / a.pitch; mf = m.astype(np.float32)
    for f in ("top", "bot"):
        np.save(os.path.join(a.d, f"proj_{f}_{a.tag}.npy"), score[f].astype(np.float16))
        G = gaussian_filter(np.where(m, score[f], 0), s) / np.maximum(gaussian_filter(mf, s), 1e-3)
        v = G[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; z = np.where(m, (G - med) / mad, 0).astype(np.float16)
        np.save(os.path.join(a.d, f"s_{f}_{a.tag}.npy"), z); np.save(os.path.join(a.d, f"s_{f}_{a.tag}_u8.npy"), (255 * np.clip(0.5 + z.astype(np.float32) / 8, 0, 1)).astype(np.uint8))
    print(a.d, a.tag, "written")
