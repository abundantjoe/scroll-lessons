import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter
from scipy.stats import rankdata
d, pitch, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
ref = np.load(os.path.join(d, "ref.npy")).astype(np.float32); ref = ref / 255.0 if ref.max() > 1.5 else ref
mt = np.load(os.path.join(d, "mask_top.npy")) > 0; mb = np.load(os.path.join(d, "mask_bot.npy")) > 0; m = mt & mb
St = np.load(os.path.join(d, "S_top.npy")).astype(np.float32); Sb = np.load(os.path.join(d, "S_bot.npy")).astype(np.float32)
pk = np.load(os.path.join(d, "peak.npy")).astype(np.float32)
s = 0.25 * 1000 / pitch
def G(x, mm=None):
    ss = s if mm is None else mm * 1000 / pitch
    return gaussian_filter(np.where(m, x, 0), ss) / np.maximum(gaussian_filter(m.astype(np.float32), ss), 1e-3)
def z(x):
    v = x[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; return (x - med) / mad
rng = np.random.default_rng(0); sub = rng.random(m.shape) < 0.02
text = m & (ref >= 0.40) & sub; blank = m & (ref <= 0.25) & sub
def auc(x):
    a, b = x[text], x[blank]; rk = rankdata(np.concatenate([a, b])); n1, n0 = len(a), len(b)
    return round(float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), 4)
res = {}
gt, gb = z(G(St)), z(G(Sb)); res["top"] = auc(gt); res["bot"] = auc(gb); res["top+bot"] = auc(gt + gb)
res["peak"] = auc(G(pk))
w = int(round(0.05 * 1000 / pitch))
mu = uniform_filter(np.where(m, St, 0), w) / np.maximum(uniform_filter(m.astype(np.float32), w), 1e-3)
mu2 = uniform_filter(np.where(m, St * St, 0), w) / np.maximum(uniform_filter(m.astype(np.float32), w), 1e-3)
rough = np.sqrt(np.maximum(mu2 - mu * mu, 0)); gr = z(G(rough)); res["rough_top"] = auc(gr)
res["rank(top+bot) - rank(rough)"] = auc(gt + gb - gr); res["rank(top+bot) + rank(rough)"] = auc(gt + gb + gr)
# roughness relative to local intensity (coefficient of variation)
res["cv_top"] = auc(z(G(rough / np.maximum(mu, 1))))
print(res); json.dump(res, open(out, "w"), indent=1)
