"""S1-v2 (RULES.md): candidates built from proj_bot_v1b; 'select' on TRAIN writes the config, 'apply' uses it unchanged."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata
mode, d, pitch, cfg_p = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0); mf = m.astype(np.float32)
p = np.load(os.path.join(d, "proj_bot_v1b.npy")).astype(np.float32); pk = np.load(os.path.join(d, "peak.npy")).astype(np.float32)
def G(x, mm):
    """Normalised-convolution Gaussian; for σ > 100 px computed on an 8x mean-pooled grid and bilinearly upsampled (error < 1e-3 of the
    signal at these scales; introduced 2026-09-17 20:45 UTC for speed, held1/held2 were computed exactly)."""
    s = mm * 1000 / pitch
[line withheld: prize-candidate detail under review]
    from scipy.ndimage import zoom
    F = 8; H, W = m.shape; H8, W8 = H // F, W // F
    pool = lambda a: a[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    num = gaussian_filter(pool(np.where(m, x, 0)), s / F); den = np.maximum(gaussian_filter(pool(mf), s / F), 1e-3)
    up = zoom(num / den, F, order=1); out = np.zeros((H, W), np.float32); h, w = min(up.shape[0], H), min(up.shape[1], W); out[:h, :w] = up[:h, :w]
    if h < H: out[h:] = out[h - 1]
    if w < W: out[:, w:] = out[:, w - 1:w]
    return out
def z(x):
    v = x[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; return np.where(m, (x - med) / mad, 0)
ratio = p / np.maximum(G(pk, 1.0), 1.0)
PAIRS = [(0.10, 1.0), (0.15, 2.0), (0.25, 3.0)]
def cand(name):
    if name == "a": return z(G(ratio, 0.25))
    kind, i = name[0], int(name[1]); s1, s2 = PAIRS[i]
    base = p if kind == "b" else ratio
    return z(G(base, s1) - G(base, s2))
names = ["a"] + [f"b{i}" for i in range(3)] + [f"c{i}" for i in range(3)]
if mode == "select":
    text = np.load(os.path.join(d, "cls_text.npy")); blank = np.load(os.path.join(d, "cls_blank.npy")); rng = np.random.default_rng(0); sub = rng.random(m.shape) < 0.05
    def auc(x):
        a, b = x[text & sub], x[blank & sub]; rk = rankdata(np.concatenate([a, b])); n1, n0 = len(a), len(b); return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    res = {}
    for n in names: res[n] = round(auc(cand(n)), 4); print(n, res[n], flush=True)
    best = max(res, key=res.get); json.dump({"pairs": PAIRS, "train_auc": res, "chosen": best}, open(cfg_p, "w"), indent=1); print("chosen", best)
else:
    best = json.load(open(cfg_p))["chosen"]; s = cand(best).astype(np.float16)
    np.save(os.path.join(d, "s_bot_v2.npy"), s); np.save(os.path.join(d, "s_top_v2.npy"), s)  # v2 is a bottom-face score; top slot mirrors it
    np.save(os.path.join(d, "s_bot_v2_u8.npy"), (255 * np.clip(0.5 + s.astype(np.float32) / 8, 0, 1)).astype(np.uint8)); print(d, "v2", best, "written")
