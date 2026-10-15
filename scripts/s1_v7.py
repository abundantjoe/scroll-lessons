"""Method v7 (RULES.md, declared before fitting): per-channel multi-scale smoothing, regional removal, ridge.
fit  <out.json>   - LOCO over the 8 TRAINING crops, picks sigma_R and lambda, writes weights.
apply <crop_dir> <weights.json> - writes s_bot_v7.npy at 2.4 um (8x bilinear upsample)."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter, zoom
from scipy.stats import rankdata

PITCH_DS8 = 19.2
SIGMAS = (0.05, 0.10, 0.25, 0.60)
SIGMA_R = (1.0, 1.5, 2.5, 4.0, None)
LAMBDAS = (0.1, 1.0, 10.0, 100.0, 1000.0)
TRAIN = ["20231005123336/derived/train"] + [f"20230929220926/derived/held{i}" for i in (1, 2, 3, 4)] + [f"20231012184424/derived/held{i}" for i in (1, 2, 3)]

def features(d, sigma_r):
    X = np.load(os.path.join(d, "ds8_x.npy"))
    m = X[22] > 0.5; mf = m.astype(np.float32)
    def G(x, mm):
        s = mm * 1000 / PITCH_DS8
        return gaussian_filter(np.where(m, x, 0), s) / np.maximum(gaussian_filter(mf, s), 1e-3)
    out = []
    for c in range(22):
        x = X[c]
        for s in SIGMAS:
            f = G(x, s)
            if sigma_r is not None: f = f - G(f, sigma_r)
            out.append(np.where(m, f, 0).astype(np.float32))
    return np.stack(out), m

def standardise(F, m):
    F = F.copy()
    for i in range(len(F)):
        v = F[i][m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6
        F[i] = np.where(m, (F[i] - med) / mad, 0)
    return F

def xy(d, sigma_r, sub=1.0, seed=0):
    F, m = features(d, sigma_r); F = standardise(F, m)
    Y = np.load(os.path.join(d, "ds8_y.npy")); sel = (Y >= 0) & m
    if sub < 1.0: sel &= np.random.default_rng(seed).random(Y.shape) < sub
    X = F[:, sel].T.astype(np.float32); y = np.where(Y[sel] == 1, 1.0, -1.0).astype(np.float32)
    del F
    return X, y

def gram(X, y):
    """Per-crop sufficient statistics [X 1]'[X 1] and [X 1]'y: constant memory in the pixel count."""
    A = np.hstack([X.astype(np.float64), np.ones((len(X), 1))])
    return A.T @ A, A.T @ y.astype(np.float64), len(X)

def solve(G, c, lam):
    R = lam * np.eye(G.shape[0]); R[-1, -1] = 0
    return np.linalg.solve(G + R, c)

def ridge(A, b, lam):
    A1 = np.hstack([A.astype(np.float64), np.ones((len(A), 1))]); R = lam * np.eye(A1.shape[1]); R[-1, -1] = 0
    return np.linalg.solve(A1.T @ A1 + R, A1.T @ b.astype(np.float64))

def auc(s, y):
    rk = rankdata(s); n1 = int((y > 0).sum()); n0 = len(y) - n1
    return float((rk[y > 0].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else None

if __name__ == "__main__":
    if sys.argv[1] == "fit":
        out = sys.argv[2]; best = None; table = {}
        for sr in SIGMA_R:
            Gs, cs, ns, rows = [], [], [], []
            for c in TRAIN:                                            # one crop in memory at a time
                X, y = xy(f"data/s1/{c}", sr)
                G, cc, n = gram(X, y); Gs.append(G); cs.append(cc); ns.append(n); rows.append((X, y))
            print("built sigma_R", sr, "rows", sum(ns), flush=True)
            Gt = sum(Gs); ct = sum(cs); nt = sum(ns)
            for lam in LAMBDAS:
                aucs = []
                for i in range(len(TRAIN)):
                    w = solve(Gt - Gs[i], ct - cs[i], lam * (nt - ns[i]))
                    X, y = rows[i]; aucs.append(auc(X @ w[:-1] + w[-1], y))
                mean = float(np.mean(aucs)); table[f"{sr}_{lam}"] = round(mean, 4)
                print(f"sigma_R {sr} lambda {lam} LOCO {mean:.4f}", flush=True)
                if best is None or mean > best[0]: best = (mean, sr, lam, aucs, Gt, ct, nt)
            del rows, Gs, cs
        mean, sr, lam, aucs, Gt, ct, nt = best
        w = solve(Gt, ct, lam * nt)
        json.dump({"sigma_r": sr, "lambda": lam, "loco_mean": mean, "loco_per_crop": [round(a, 4) for a in aucs],
                   "loco_table": table, "sigmas": SIGMAS, "w": w[:-1].tolist(), "b": float(w[-1]), "train_crops": TRAIN}, open(out, "w"), indent=1)
        print("CHOSEN sigma_R", sr, "lambda", lam, "LOCO", round(mean, 4))
    else:
        d, wp = sys.argv[2], sys.argv[3]; W = json.load(open(wp))
        F, m = features(d, W["sigma_r"]); F = standardise(F, m)
        sc = np.tensordot(np.array(W["w"]), F, axes=(0, 0)) + W["b"]
        s = 0.10 * 1000 / PITCH_DS8
        sc = gaussian_filter(np.where(m, sc, 0), s) / np.maximum(gaussian_filter(m.astype(np.float32), s), 1e-3)
        v = sc[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826 + 1e-6; z = np.where(m, (sc - med) / mad, 0)
        up = zoom(z.astype(np.float32), 8, order=1)
        mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
        full = np.zeros(mask.shape, np.float32); h, w2 = min(up.shape[0], mask.shape[0]), min(up.shape[1], mask.shape[1])
        full[:h, :w2] = up[:h, :w2]; full = np.where(mask, full, 0).astype(np.float16)
        np.save(os.path.join(d, "s_bot_v7.npy"), full); np.save(os.path.join(d, "s_top_v7.npy"), full)
        print(d, "v7 written")
