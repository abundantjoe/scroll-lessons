"""S1-v3: ridge on multi-depth multi-scale face intensities (RULES.md). fit <d> <pitch> <out.json> | apply <d> <pitch> <w.json>."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter
mode, d, pitch, wp = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
SIG = (0.05, 0.15, 0.40); ND = 11
m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0); mf = m.astype(np.float32)
den = {s * 1000 / pitch: np.maximum(gaussian_filter(mf, s * 1000 / pitch), 1e-3) for s in SIG if s * 1000 / pitch <= 40}
from scipy.ndimage import zoom
def Gn(x, sig_px):
    """Normalised-convolution Gaussian. For σ > 40 px computed on a pooled grid (factor 4, or 8 above 120 px) and bilinearly upsampled;
    the pooling box is ≤ σ/10 so the difference from the exact filter is negligible. Same code path for fit and apply."""
    if sig_px <= 40: return gaussian_filter(np.where(m, x, 0), sig_px) / den[sig_px]
    F = 8 if sig_px > 120 else 4; H, W = m.shape; H8, W8 = H // F, W // F
    pool = lambda a: a[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    num = gaussian_filter(pool(np.where(m, x, 0)), sig_px / F); dn = np.maximum(gaussian_filter(pool(mf), sig_px / F), 1e-3)
    up = zoom(num / dn, F, order=1); out = np.zeros((H, W), np.float32); h, w = min(up.shape[0], H), min(up.shape[1], W); out[:h, :w] = up[:h, :w]
    if h < H: out[h:] = out[h - 1]
    if w < W: out[:, w:] = out[:, w - 1:w]
    return out
def feat_iter():
    for f in ("top", "bot"):
        P = np.load(os.path.join(d, f"I_stack_{f}.npy"), mmap_mode="r")
        for i in range(ND):
            x = np.asarray(P[i]).astype(np.float32)
            for s in SIG:
                yield (f, i, s), Gn(x, s * 1000 / pitch)
if mode == "fit":
    text = np.load(os.path.join(d, "cls_text.npy")); blank = np.load(os.path.join(d, "cls_blank.npy"))
    rng = np.random.default_rng(0); sel = (text | blank) & (rng.random(m.shape) < 0.02); idx = np.where(sel)
    y = np.where(text[idx], 1.0, -1.0); H = m.shape[0]; upper = idx[0] < H // 2
    X = []; keys = []
    for k, F in feat_iter(): X.append(F[idx]); keys.append(k); print("feat", k, flush=True)
    X = np.stack(X, 1).astype(np.float64); mu = X.mean(0); sd = X.std(0) + 1e-6; Xs = (X - mu) / sd
    def ridge(A, b, lam):
        A1 = np.hstack([A, np.ones((len(A), 1))]); R = lam * np.eye(A1.shape[1]); R[-1, -1] = 0
        return np.linalg.solve(A1.T @ A1 + R, A1.T @ b)
    def auc(s, yy):
        from scipy.stats import rankdata
        rk = rankdata(s); n1 = (yy > 0).sum(); n0 = len(yy) - n1; return float((rk[yy > 0].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    best = None
    for lam in (1e-2, 1e-1, 1, 10, 100):
        a = 0
        for tr, te in ((upper, ~upper), (~upper, upper)):
            w = ridge(Xs[tr], y[tr], lam * tr.sum()); a += auc(Xs[te] @ w[:-1] + w[-1], y[te]) / 2
        print("lambda", lam, "cv auc %.4f" % a, flush=True)
        if best is None or a > best[0]: best = (a, lam)
    w = ridge(Xs, y, best[1] * len(y))
    json.dump({"keys": [list(k) for k in keys], "mu": mu.tolist(), "sd": sd.tolist(), "w": w[:-1].tolist(), "b": float(w[-1]), "lambda": best[1], "cv_auc": best[0], "n": int(len(y))}, open(wp, "w"), indent=1)
    order = np.argsort(-np.abs(w[:-1])); print("top weights:", [(keys[i], round(w[i], 3)) for i in order[:10]])
else:
    W = json.load(open(wp)); score = np.full(m.shape, W["b"], np.float32); keys = [tuple(k) for k in W["keys"]]
    for (k, F) in feat_iter():
        j = keys.index((k[0], k[1], k[2])); score += (W["w"][j] / W["sd"][j]) * (F - W["mu"][j])
    s = 0.10 * 1000 / pitch; G = gaussian_filter(np.where(m, score, 0), s) / np.maximum(gaussian_filter(mf, s), 1e-3)
    v = G[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; z = np.where(m, (G - med) / mad, 0).astype(np.float16)
    np.save(os.path.join(d, "s_bot_v3.npy"), z); np.save(os.path.join(d, "s_top_v3.npy"), z); np.save(os.path.join(d, "s_bot_v3_u8.npy"), (255 * np.clip(0.5 + z.astype(np.float32) / 8, 0, 1)).astype(np.uint8))
    print(d, "v3 written")
