"""ca step 3: local (within-crop) calibration mechanisms, selected by LOCO on TRAINING only.

Per-crop global calibration is dead (step 1/2). The surviving form of the hypothesis is that the
feature-to-ink mapping is mis-calibrated BELOW the crop scale: local sheet state (brightness level,
gain, coverage, face-crest geometry) changes what a given channel value means.

Variants, all unsupervised and identical on training and evaluation crops:
  B88   : the 22 channels at sigma in {0,4,8,16}, per-crop standardised           (baseline)
  R<s>  : regional removal   f - G_s(f)                                            (88)
  N<s>  : local gain normal. (f - G_s(f)) / local_sd_s(f)                          (88)
  GEO   : local geometry     (10 maps, 1 mm)
  B88+GEO, R<s>+GEO, N<s>+GEO, and +INT = geometry x top-8 depth-feature interactions
All sigma in ds8 px (19.192 um): 26 = 0.5 mm, 52 = 1 mm, 104 = 2 mm.
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import (TRAIN, VAL, load_crop, build_B88, standardise_cols, sample_idx,
                    fit_logistic, auc_vec, nconv, fast_smooth, NAMES88, NDEP)

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"
SIGL = [26, 52, 104]


def loc_mu_sd(f, mf, sig, den=None):
    mu = nconv(f, mf, sig, den)
    d = f - mu
    var = nconv(d * d, mf, sig, den)
    return mu, np.sqrt(np.maximum(var, 0)) + 1e-6


def build_geo(x, m):
    """local, unsupervised sheet-geometry maps at 1 mm (sigma 52 ds8 px)."""
    mf = m.astype(np.float32)
    sig = 52.0
    dn = fast_smooth(mf, sig)
    T = x[:NDEP]; B = x[NDEP:22]
    Lt = nconv(T.mean(0), mf, sig, dn); Lb = nconv(B.mean(0), mf, sig, dn)
    _, St = loc_mu_sd(T.mean(0), mf, sig, dn)
    _, Sb = loc_mu_sd(B.mean(0), mf, sig, dn)
    cov = nconv(x[22] if x.shape[0] > 22 else mf, mf, sig, dn)
    # crest geometry per face: sub-slice argmax depth and crest curvature of the depth profile
    geo = [Lt, Lb, St, Sb, cov]
    names = ["Ltop", "Lbot", "Stop", "Sbot", "cov"]
    for face, V in (("T", T), ("B", B)):
        k = np.argmax(V, axis=0)
        kc = np.clip(k, 1, V.shape[0] - 2)
        ii = np.arange(V.shape[1] * V.shape[2])
        fl = V.reshape(V.shape[0], -1)
        y0 = fl[kc.ravel() - 1, ii]; y1 = fl[kc.ravel(), ii]; y2 = fl[kc.ravel() + 1, ii]
        den = y0 - 2 * y1 + y2
        off = np.where(np.abs(den) > 1e-6, 0.5 * (y0 - y2) / np.where(np.abs(den) > 1e-6, den, 1.0), 0.0)
        dstar = (kc.ravel() + np.clip(off, -1, 1)).reshape(k.shape).astype(np.float32)
        curv = (-den).reshape(k.shape).astype(np.float32)
        amp = (V.max(0) - V.min(0)).astype(np.float32)
        geo += [nconv(dstar, mf, sig, dn), nconv(curv, mf, sig, dn), nconv(amp, mf, sig, dn)]
        names += [f"{face}dstar", f"{face}curv", f"{face}amp"]
    return np.stack(geo).astype(np.float32), names


def build_all(s, c):
    """returns dict variant -> (n,88 or k) sampled matrix, plus y."""
    p = os.path.join(CACHE, f"caV_{s}_{c}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return {k: z[k] for k in z.files}
    x, m, t, b = load_crop(s, c)
    mf = m.astype(np.float32)
    idx, y = sample_idx(t, b, nmax=20000, seed=0)
    out = {"y": y}
    F = build_B88(x, m)                                   # (88,H,W) unstandardised
    H, W = m.shape

    def take(A):
        return standardise_cols(A, m).reshape(A.shape[0], -1)[:, idx].T.astype(np.float32)

    out["B88"] = take(F)
    for sg in SIGL:
        R = np.empty_like(F); N = np.empty_like(F)
        dn = fast_smooth(mf, float(sg))
        for i in range(F.shape[0]):
            mu, sd = loc_mu_sd(F[i], mf, float(sg), dn)
            R[i] = np.where(m, F[i] - mu, 0.0)
            N[i] = np.where(m, (F[i] - mu) / sd, 0.0)
        out[f"R{sg}"] = take(R); out[f"N{sg}"] = take(N)
        del R, N
    del F
    G, gn = build_geo(np.concatenate([x, m[None].astype(np.float32)]), m)
    out["GEO"] = take(G)
    out["geo_names"] = np.array(gn)
    np.savez_compressed(p, **out)
    return out


def gram(X, y):
    """weighted (class-balanced) Gram and cross-product with an intercept column."""
    n, p = X.shape
    A = np.empty((n, p + 1), np.float64)
    A[:, :p] = X; A[:, p] = 1.0
    npos = max(int((y == 1).sum()), 1); nneg = max(int((y == 0).sum()), 1)
    w = np.where(y == 1, 1.0 / npos, 1.0 / nneg)
    t = np.where(y == 1, 1.0, -1.0)
    Aw = A * w[:, None]
    return A.T @ Aw, Aw.T @ t


def loco(mats, crops, key_build, lam=1e-3):
    """LOCO mean AUC for a feature assembly function, via class-balanced ridge."""
    Xs, Gs, Cs, ys = {}, {}, {}, {}
    for k in crops:
        Xs[k] = key_build(mats[k]); ys[k] = mats[k]["y"]
        Gs[k], Cs[k] = gram(Xs[k], ys[k])
    p = Xs[crops[0]].shape[1]
    aucs = []
    for k in crops:
        G = sum(Gs[j] for j in crops if j != k)
        c = sum(Cs[j] for j in crops if j != k)
        sc = float(np.trace(G)) / (p + 1)
        w = np.linalg.solve(G + lam * sc * np.eye(p + 1), c)
        aucs.append(auc_vec(Xs[k] @ w[:p] + w[p], ys[k]))
    return float(np.mean(aucs)), [round(a, 4) for a in aucs]


def main():
    crops = [f"{s}/{c}" for (s, c) in TRAIN]
    mats = {}
    for (s, c) in TRAIN:
        t0 = time.time()
        mats[f"{s}/{c}"] = build_all(s, c)
        print(f"built {s}/{c} ({time.time()-t0:.0f}s)", flush=True)

    # top-8 depth features by pooled single-feature |AUC-0.5| on TRAIN (used for interactions)
    A = np.zeros(88)
    for k in crops:
        X, y = mats[k]["B88"], mats[k]["y"]
        A += np.array([abs(auc_vec(X[:, j], y) - 0.5) for j in range(88)])
    top8 = np.argsort(-A)[:8]
    print("top8 depth features:", [NAMES88[j] for j in top8], flush=True)

    def std(M):
        return (M - M.mean(0)) / (M.std(0) + 1e-6)

    specs = {}
    specs["B88"] = lambda d: std(d["B88"])
    specs["GEO"] = lambda d: std(d["GEO"])
    specs["B88+GEO"] = lambda d: np.hstack([std(d["B88"]), std(d["GEO"])])
    for sg in SIGL:
        specs[f"R{sg}"] = (lambda sg: (lambda d: std(d[f"R{sg}"])))(sg)
        specs[f"N{sg}"] = (lambda sg: (lambda d: std(d[f"N{sg}"])))(sg)
        specs[f"B88+R{sg}"] = (lambda sg: (lambda d: np.hstack([std(d["B88"]), std(d[f"R{sg}"])])))(sg)
        specs[f"B88+N{sg}"] = (lambda sg: (lambda d: np.hstack([std(d["B88"]), std(d[f"N{sg}"])])))(sg)

    def inter(d, base):
        Bm = std(d[base]); G = std(d["GEO"])
        I = np.hstack([Bm[:, top8] * G[:, [g]] for g in range(G.shape[1])])
        return np.hstack([Bm, G, std(I)])
    specs["B88+GEO+INT"] = lambda d: inter(d, "B88")
    for sg in SIGL:
        specs[f"N{sg}+GEO+INT"] = (lambda sg: (lambda d: inter(d, f"N{sg}")))(sg)

    res = {}
    for name, fn in specs.items():
        t0 = time.time()
        m, per = loco(mats, crops, fn)
        res[name] = dict(loco=round(m, 4), per_crop=per)
        print(f"{name:16s} LOCO {m:.4f}  ({time.time()-t0:.0f}s)  {per}", flush=True)
    res["_crops"] = crops
    res["_top8"] = [NAMES88[j] for j in top8]
    best = max((k for k in res if not k.startswith("_")), key=lambda k: res[k]["loco"])
    res["_best"] = best
    print("BEST", best, res[best]["loco"])
    json.dump(res, open(os.path.join(OUT, "ca_step3_local.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
