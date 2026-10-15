"""ca step 3b: the strongest form of the per-crop calibration hypothesis, done unsupervised.

If each crop needs its own normalisation, then aligning the crops' feature distributions BEFORE
pooling must help. Two alignments, both estimated from a random sample of MASK pixels only (no
labels used, so they can be applied unchanged to an evaluation crop):
  Q   per-crop quantile (rank -> normal score) transform of every feature.
      NOTE: for a single feature evaluated within one crop this is a no-op for AUC, but for a
      POOLED multi-feature linear model it is not: it removes crop-to-crop differences in the
      marginal shape of each feature.
  W   per-crop whitening X -> (X - mu_k) Sigma_k^{-1/2} with shrinkage, i.e. every crop gets its own
      linear recalibration of the whole feature space; the pooled model is then fitted in the
      common whitened coordinates.
  QW  quantile transform then whitening.
Selected by LOCO on the 8 TRAINING crops only.
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import (TRAIN, load_crop, build_B88, standardise_cols, sample_idx, auc_vec, nconv,
                    fast_smooth)
from ca_step3_local import loc_mu_sd, build_geo, loco, SIGL

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"
NU = 20000


def build_pair(s, c):
    """labelled sample + random-mask (unsupervised) sample of the same feature variants."""
    p = os.path.join(CACHE, f"caU_{s}_{c}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return {k: z[k] for k in z.files}
    x, m, t, b = load_crop(s, c)
    mf = m.astype(np.float32)
    idx, y = sample_idx(t, b, nmax=20000, seed=0)
    rng = np.random.default_rng(1)
    im = np.flatnonzero(m.ravel())
    uidx = rng.choice(im, min(NU, im.size), replace=False)
    out = {"y": y}
    F = build_B88(x, m)

    def take(A, ii):
        return standardise_cols(A, m).reshape(A.shape[0], -1)[:, ii].T.astype(np.float32)

    out["B88"] = take(F, idx); out["B88u"] = take(F, uidx)
    for sg in SIGL:
        N = np.empty_like(F)
        dn = fast_smooth(mf, float(sg))
        for i in range(F.shape[0]):
            mu, sd = loc_mu_sd(F[i], mf, float(sg), dn)
            N[i] = np.where(m, (F[i] - mu) / sd, 0.0)
        out[f"N{sg}"] = take(N, idx); out[f"N{sg}u"] = take(N, uidx)
        del N
    del F
    G, gn = build_geo(np.concatenate([x, m[None].astype(np.float32)]), m)
    out["GEO"] = take(G, idx); out["GEOu"] = take(G, uidx)
    np.savez_compressed(p, **out)
    return out


def qtrans(Xu, X):
    """per-crop quantile -> normal-score map, fitted on the unsupervised sample."""
    from scipy.special import ndtri
    Z = np.empty_like(X)
    n = Xu.shape[0]
    q = (np.arange(n) + 0.5) / n
    g = ndtri(q).astype(np.float32)
    for j in range(X.shape[1]):
        srt = np.sort(Xu[:, j])
        Z[:, j] = np.interp(X[:, j], srt, g).astype(np.float32)
    return Z


def whiten(Xu, X, shrink=0.1):
    mu = Xu.mean(0)
    A = Xu - mu
    S = (A.T @ A) / max(A.shape[0] - 1, 1)
    S = (1 - shrink) * S + shrink * np.eye(S.shape[0]) * np.trace(S) / S.shape[0]
    ev, V = np.linalg.eigh(S)
    ev = np.maximum(ev, 1e-8)
    Wm = V @ np.diag(ev ** -0.5) @ V.T
    return ((X - mu) @ Wm).astype(np.float32)


def main():
    crops = [f"{s}/{c}" for (s, c) in TRAIN]
    mats = {}
    for (s, c) in TRAIN:
        t0 = time.time()
        mats[f"{s}/{c}"] = build_pair(s, c)
        print(f"built {s}/{c} ({time.time()-t0:.0f}s)", flush=True)

    def std(M):
        return (M - M.mean(0)) / (M.std(0) + 1e-6)

    bases = ["B88"] + [f"N{sg}" for sg in SIGL]
    specs = {}
    for bkey in bases:
        specs[f"{bkey}"] = (lambda bkey: (lambda d: std(d[bkey])))(bkey)
        specs[f"{bkey}|Q"] = (lambda bkey: (lambda d: qtrans(d[bkey + "u"], d[bkey])))(bkey)
        specs[f"{bkey}|W"] = (lambda bkey: (lambda d: whiten(d[bkey + "u"], d[bkey])))(bkey)
        specs[f"{bkey}|QW"] = (lambda bkey: (lambda d: whiten(
            qtrans(d[bkey + "u"], d[bkey + "u"]), qtrans(d[bkey + "u"], d[bkey]))))(bkey)
    specs["B88+GEO|W"] = lambda d: whiten(np.hstack([d["B88u"], d["GEOu"]]),
                                          np.hstack([d["B88"], d["GEO"]]))

    res = {}
    for name, fn in specs.items():
        t0 = time.time()
        m, per = loco(mats, crops, fn)
        res[name] = dict(loco=round(m, 4), per_crop=per)
        print(f"{name:14s} LOCO {m:.4f}  ({time.time()-t0:.0f}s)  {per}", flush=True)
    res["_crops"] = crops
    best = max((k for k in res if not k.startswith("_")), key=lambda k: res[k]["loco"])
    res["_best"] = best
    print("BEST", best, res[best]["loco"])
    json.dump(res, open(os.path.join(OUT, "ca_step3b_norm.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
