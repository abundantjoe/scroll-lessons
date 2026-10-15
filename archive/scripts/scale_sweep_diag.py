"""D1b (exploration chart only): AUC of face intensity vs reference as a function of smoothing scale (normalised convolution over the mask)."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter
d, pitch, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
ref = np.load(os.path.join(d, "ref.npy")).astype(np.float32); ref = ref / 255.0 if ref.max() > 1.5 else ref
res = {}
rng = np.random.default_rng(0)
for f in ("top", "bot"):
    S = np.load(os.path.join(d, f"S_{f}.npy")).astype(np.float32); m = np.load(os.path.join(d, f"mask_{f}.npy")) > 0
    text = m & (ref >= 0.40); blank = m & (ref <= 0.25); sub = rng.random(m.shape) < 0.02
    res[f] = {}
    for sig_mm in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8):
        if sig_mm == 0: G = S
        else:
            s = sig_mm * 1000 / pitch
            G = gaussian_filter(np.where(m, S, 0), s) / np.maximum(gaussian_filter(m.astype(np.float32), s), 1e-3)
        from scipy.stats import rankdata
        x, y = G[text & sub], G[blank & sub]; z = np.concatenate([x, y]); rk = rankdata(z); n1, n0 = len(x), len(y)
        a = float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)); res[f][str(sig_mm)] = round(a, 4); print(f, sig_mm, round(a, 4), flush=True)
json.dump(res, open(out, "w"), indent=1)
