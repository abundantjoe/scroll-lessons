"""Step 7: two controls for the 0.68 -> 0.93 gap.
(a) TEXTURE: ds8_x is 8x MEAN-pooled from 2.4 um. Does the DISCARDED sub-cell texture
    (8x8 block std / IQR of the full-resolution v1a projection) carry ink signal that the
    block mean does not? Only crops that still have proj_bot_v1a.npy on disk.
(b) NON-LINEAR POOLING at stroke scale: if ink is sparse inside a stroke, a percentile
    or top-k mean over the stroke support should beat the plain mean (= Gaussian).
TRAINING crops only."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
from scipy.ndimage import gaussian_filter, percentile_filter, uniform_filter

W = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)

def blockstats(a, m, F=8):
    H8 = a.shape[0] // F
    A = a[:H8 * F, :H8 * F].reshape(H8, F, H8, F).astype(np.float32)
    M = m[:H8 * F, :H8 * F].reshape(H8, F, H8, F).astype(np.float32)
    n = M.sum(axis=(1, 3))
    s1 = (A * M).sum(axis=(1, 3))
    s2 = (A * A * M).sum(axis=(1, 3))
    mu = s1 / np.maximum(n, 1)
    var = np.maximum(s2 / np.maximum(n, 1) - mu * mu, 0)
    return mu, np.sqrt(var), n

def std_over(name):
    v = np.asarray(name, np.float32)
    med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6
    return med, mad

if __name__ == "__main__":
    out = {}
    # ---- (a) texture ----
    tex = {}
    for s, c in TRAIN + EVAL:
        d = cropdir(s, c)
        p = d + "/proj_bot_v1a.npy"
        if not os.path.exists(p):
            continue
        if (s, c) in EVAL:
            continue      # EVAL crops are never touched
        a = np.load(p, mmap_mode="r")
        m = (np.load(d + "/mask_top.npy") > 0) & (np.load(d + "/mask_bot.npy") > 0)
        mu, sd, n = blockstats(np.asarray(a, np.float32), m.astype(np.float32))
        t, b = ds8_labels(s, c)
        ok = (n > 20)
        sel = (t | b) & ok
        # standardise
        res = {}
        for nm, arr in (("block_mean", mu), ("block_std", sd),
                        ("std_over_mean", sd / np.maximum(mu, 1e-3)),
                        ("smooth16_block_std", gaussian_filter(np.where(ok, sd, 0), 16)),
                        ("smooth16_block_mean", gaussian_filter(np.where(ok, mu, 0), 16))):
            res[nm] = round(auc(arr[sel], t[sel], b[sel]), 4)
        tex[f"{s}/{c}"] = res
        print("TEXTURE", s, c, res, flush=True)
    out["texture"] = tex

    # ---- (b) non-linear pooling ----
    import mf_step4 as S4
    pool = {}
    for s, c in TRAIN:
        q, v, t, b, sel = S4.prep(s, c)
        r = {}
        for rad in [8, 16]:
            k = 2 * rad + 1
            yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1]
            fp = (yy * yy + xx * xx) <= rad * rad
            r[f"mean{rad}"] = round(auc(uniform_filter(q, k, mode="nearest")[sel], t[sel], b[sel]), 4)
            for pc in (75, 90):
                pf = percentile_filter(q, pc, footprint=fp, mode="nearest")
                r[f"p{pc}_{rad}"] = round(auc(pf[sel], t[sel], b[sel]), 4)
        pool[f"{s}/{c}"] = r
        print("POOL", s, c, r, flush=True)
    keys = list(next(iter(pool.values())).keys())
    out["pool_mean"] = {k: round(float(np.mean([pool[x][k] for x in pool])), 4) for k in keys}
    print("POOL TRAIN-mean", out["pool_mean"], flush=True)
    json.dump(out, open("/home/user/megara/stats/explore/step7_texture_pool.json", "w"), indent=1)
