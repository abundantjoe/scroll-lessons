"""D1: depth profile of the reference contrast (declared diagnostic, see RULES.md). Not a scorer."""
import sys, os, json, numpy as np, zarr, time
store, level, y0, y1, x0, x1, k0, k1, d, out = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:9]), sys.argv[9], sys.argv[10]
arr = zarr.open(store, mode="r")[level]
H, W, K = y1 - y0, x1 - x0, k1 - k0
B = 32; W = (W // B) * B; H = (H // B) * B
kt = np.load(os.path.join(d, "k_top.npy")).astype(np.float32)[:H, :W]; kb = np.load(os.path.join(d, "k_bot.npy")).astype(np.float32)[:H, :W]
ref = np.load(os.path.join(d, "ref.npy")).astype(np.float32)[:H, :W]; ref = ref / 255.0 if ref.max() > 1.5 else ref
mask = ((np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0))[:H, :W]
pk = np.load(os.path.join(d, "peak.npy")).astype(np.float32)[:H, :W]
text = mask & (ref >= 0.40); blank = mask & (ref <= 0.25)
deltas = np.arange(-8, 9); anchors = {"top": kt, "mid": 0.5 * (kt + kb), "bot": kb}
hist = {a: {c: np.zeros((len(deltas), 256), np.int64) for c in ("text", "blank")} for a in anchors}
nb = H // B
blocks = {a: np.zeros((len(deltas), nb, W // B), np.float64) for a in anchors}
bcount = np.zeros((nb, W // B), np.int64)
def sample(p, k):
    k = np.clip(np.nan_to_num(k, nan=0.0, posinf=K - 1.0, neginf=0.0), 0, K - 1.001); kk = np.floor(k).astype(np.int32); f = k - kk
    ii, jj = np.indices(k.shape)
    return p[kk, ii, jj] * (1 - f) + p[kk + 1, ii, jj] * f
T = 256; t0 = time.time()
for r in range(0, H - H % B, T):
    r1 = min(r + T, H - H % B)
    p = arr[k0:k1, y0 + r:y0 + r1, x0:x0 + W].astype(np.float32)
    m = mask[r:r1]; tx = text[r:r1]; bl = blank[r:r1]
    bcount[r // B:r1 // B] += m.reshape(-1, B, W // B, B).sum(axis=(1, 3))
    for a, kmap in anchors.items():
        km = kmap[r:r1]
        for i, dl in enumerate(deltas):
            v = sample(p, km + dl)
            vi = np.clip(np.rint(v), 0, 255).astype(np.int64)
            hist[a]["text"][i] += np.bincount(vi[tx], minlength=256); hist[a]["blank"][i] += np.bincount(vi[bl], minlength=256)
            blocks[a][i, r // B:r1 // B] += np.where(m, v, 0).reshape(-1, B, W // B, B).sum(axis=(1, 3))
    print(f"rows {r1}/{H} {time.time()-t0:.0f}s", flush=True)
def auc_hist(ht, hb):
    # P(text > blank) + 0.5 P(equal) from histograms
    cb = np.cumsum(hb); tot_b = cb[-1]; tot_t = ht.sum()
    if tot_b == 0 or tot_t == 0: return None
    less = np.concatenate([[0], cb[:-1]])
    return float((ht * (less + 0.5 * hb)).sum() / (tot_t * tot_b))
def auc_rank(x, y):
    from scipy.stats import rankdata
    z = np.concatenate([x, y]); rk = rankdata(z); n1, n0 = len(x), len(y)
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
refb = np.where(mask, ref, 0)[:nb * B].reshape(nb, B, W // B, B).sum(axis=(1, 3)) / np.maximum(bcount, 1)
okb = bcount >= 0.5 * B * B; tb = okb & (refb >= 0.40); bb = okb & (refb <= 0.25)
res = {"deltas": deltas.tolist(), "n_text_px": int(text.sum()), "n_blank_px": int(blank.sum()), "n_text_blocks": int(tb.sum()), "n_blank_blocks": int(bb.sum())}
for a in anchors:
    res[a] = {"mean_text": [], "mean_blank": [], "auc_px": [], "auc_block": []}
    for i in range(len(deltas)):
        ht, hb = hist[a]["text"][i], hist[a]["blank"][i]; v = np.arange(256)
        res[a]["mean_text"].append(float((ht * v).sum() / max(ht.sum(), 1))); res[a]["mean_blank"].append(float((hb * v).sum() / max(hb.sum(), 1)))
        res[a]["auc_px"].append(auc_hist(ht, hb))
        bm = blocks[a][i] / np.maximum(bcount, 1)
        res[a]["auc_block"].append(auc_rank(bm[tb], bm[bb]))
t = (kb - kt) * float(json.load(open(os.path.join(d, "residual_v0.1b.json"))).get("pitch_um", 2.399)) if False else (kb - kt)
sub = np.random.default_rng(0).random(text.shape) < 0.05
res["auc_thickness_px"] = auc_rank(t[text & sub], t[blank & sub]); res["auc_peak_px"] = auc_rank(pk[text & sub], pk[blank & sub])
json.dump(res, open(out, "w"), indent=1)
for a in anchors: print(a, "auc_px", [round(x, 3) for x in res[a]["auc_px"]]); print(a, "auc_block", [round(x, 3) for x in res[a]["auc_block"]])
print("thickness", res["auc_thickness_px"], "peak", res["auc_peak_px"])
