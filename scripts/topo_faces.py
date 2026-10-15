#!/usr/bin/env python3
"""5.3/5.4 sampling: from a thick render I(u,v,k) (zarr level, uint8, axes k,v,u) compute per pixel
  peak, kstar (crest), k_top, k_bot (sub-slice, band containing the crest, 50 % of peak), t = k_bot-k_top,
  S_top = I(k_top-1) [just outside the top face], D_top = I(k_top+2) [inside], S_bot = I(k_bot+1), D_bot = I(k_bot-2),
  ct_mid = I at the mesh slice, valid = band not clipped by the stack ends and peak >= PEAK_MIN.
Smoothing before the search: Gaussian sigma = 1 slice along k, 1 px along (u,v). Tiled, idempotent.
Sign convention: k increases from the "top" face towards the "bottom" face; outside the top face is smaller k.
usage: topo_faces.py <store> <level> <y0> <y1> <x0> <x1> <k0> <k1> <outdir> [--tile 1024]"""
import sys, os, json, argparse, numpy as np, zarr, time
from scipy.ndimage import gaussian_filter
PEAK_MIN = 24.0   # uint8 units; below this the profile is masked (zero) volume, not papyrus

def band(p, thr, kstar):
    """p: (K,H,W) float32 smoothed profiles; returns k_top, k_bot (float, sub-slice) and clipped flags."""
    K = p.shape[0]
    idx = np.arange(K, dtype=np.int32)[:, None, None]
    above = p >= thr[None]
    below = (~above) & (idx < kstar[None])
    has_b = below.any(0)
    kt0 = np.where(has_b, K - 1 - np.argmax(below[::-1], axis=0), -1)       # last not-above index below the crest
    abv = (~above) & (idx > kstar[None])
    has_a = abv.any(0)
    kb1 = np.where(has_a, np.argmax(abv, axis=0), K)                           # first not-above index above the crest
    H, W = kstar.shape; ii, jj = np.indices((H, W))
    kt0c = np.clip(kt0, 0, K - 1); kb1c = np.clip(kb1, 0, K - 1)
    p0 = p[kt0c, ii, jj]; p1 = p[np.clip(kt0c + 1, 0, K - 1), ii, jj]
    k_top = kt0 + (thr - p0) / np.maximum(p1 - p0, 1e-3)
    q1 = p[kb1c, ii, jj]; q0 = p[np.clip(kb1c - 1, 0, K - 1), ii, jj]
    k_bot = kb1 - (thr - q1) / np.maximum(q0 - q1, 1e-3)
    return k_top.astype(np.float32), k_bot.astype(np.float32), (~has_b) | (~has_a)

def sample(p, k):
    """linear interpolation of p (K,H,W) at fractional slice k (H,W), clamped."""
    K = p.shape[0]; k = np.clip(k, 0, K - 1); k0 = np.floor(k).astype(np.int32); k1 = np.minimum(k0 + 1, K - 1)
    f = (k - k0).astype(np.float32); ii, jj = np.indices(k.shape)
    return (p[k0, ii, jj] * (1 - f) + p[k1, ii, jj] * f).astype(np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("store"); ap.add_argument("level"); ap.add_argument("y0", type=int); ap.add_argument("y1", type=int)
    ap.add_argument("x0", type=int); ap.add_argument("x1", type=int); ap.add_argument("k0", type=int); ap.add_argument("k1", type=int)
    ap.add_argument("outdir"); ap.add_argument("--tile", type=int, default=1024); ap.add_argument("--halo", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    if os.path.exists(os.path.join(a.outdir, "topo.done")): print("done already"); return
    arr = zarr.open(a.store, mode="r")[a.level]
    H, W = a.y1 - a.y0, a.x1 - a.x0; K = a.k1 - a.k0
    names = ["peak", "kstar", "k_top", "k_bot", "S_top", "D_top", "S_bot", "D_bot", "ct_mid"]
    out = {n: np.lib.format.open_memmap(os.path.join(a.outdir, n + ".npy"), mode="w+", dtype=np.float16, shape=(H, W)) for n in names}
    out["valid"] = np.lib.format.open_memmap(os.path.join(a.outdir, "valid.npy"), mode="w+", dtype=np.uint8, shape=(H, W))
    kmid = K // 2; t0 = time.time(); n = 0
    for ty in range(0, H, a.tile):
        for tx in range(0, W, a.tile):
            y0, y1 = max(ty - a.halo, 0), min(ty + a.tile + a.halo, H); x0, x1 = max(tx - a.halo, 0), min(tx + a.tile + a.halo, W)
            raw = arr[a.k0:a.k1, a.y0 + y0:a.y0 + y1, a.x0 + x0:a.x0 + x1]
            ct_mid = raw[kmid].astype(np.float32)
            p = gaussian_filter(raw.astype(np.float32), sigma=(1, 1, 1), mode="nearest")
            peak = p.max(0); kstar = p.argmax(0).astype(np.int32); thr = 0.5 * peak
            k_top, k_bot, clipped = band(p, thr, kstar); k_top = np.clip(k_top, -2, K + 1); k_bot = np.clip(k_bot, -2, K + 1)
            valid = (~clipped) & (peak >= PEAK_MIN) & (raw[kmid] > 0)
            res = dict(peak=peak, kstar=kstar.astype(np.float32), k_top=k_top, k_bot=k_bot, ct_mid=ct_mid,
                       S_top=sample(p, k_top - 1), D_top=sample(p, k_top + 2), S_bot=sample(p, k_bot + 1), D_bot=sample(p, k_bot - 2))
            sy, sx = slice(ty - y0, ty - y0 + min(a.tile, H - ty)), slice(tx - x0, tx - x0 + min(a.tile, W - tx))
            for nme, v in res.items(): out[nme][ty:ty + a.tile, tx:tx + a.tile] = v[sy, sx]
            out["valid"][ty:ty + a.tile, tx:tx + a.tile] = valid[sy, sx]
            n += 1
            if n % 8 == 0: print(f"tile {n} ({ty},{tx}) {time.time()-t0:.0f}s", flush=True)
    for v in out.values(): v.flush()
    t = out["k_bot"][:].astype(np.float32) - out["k_top"][:].astype(np.float32); vm = out["valid"][:] > 0
    stats = dict(shape=[H, W], K=K, k0=a.k0, valid_fraction=float(vm.mean()),
                 t_median=float(np.median(t[vm])) if vm.any() else None, t_p5_p95=[float(x) for x in np.percentile(t[vm], [5, 95])] if vm.any() else None,
                 ktop_median=float(np.median(out["k_top"][:][vm])) if vm.any() else None, kbot_median=float(np.median(out["k_bot"][:][vm])) if vm.any() else None,
                 peak_median=float(np.median(out["peak"][:][vm])) if vm.any() else None, seconds=time.time() - t0)
    json.dump(stats, open(os.path.join(a.outdir, "topo_stats.json"), "w"), indent=1); print(stats)
    open(os.path.join(a.outdir, "topo.done"), "w").close()

if __name__ == "__main__":
    main()
