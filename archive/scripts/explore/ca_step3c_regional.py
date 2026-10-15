"""ca step 3c: the local-offset (regional) recalibration that step 3 found, taken to its optimum,
plus the strongest UNSUPERVISED per-crop calibrations applied on top of it.

Bases (all built the same way on training and evaluation crops, no labels anywhere):
  B88        22 depth channels at sigma_s in {0,4,8,16} ds8 px, per-crop standardised
  R<s>       B88 minus its own mask-aware local mean at sigma = s ds8 px (s = 104,156,208,312
             = 2.0, 3.0, 4.0, 6.0 mm)  -> a LOCAL re-zeroing = calibration below the crop scale
  RMS        R104 and R312 stacked (two removal scales at once)
  GEO        11 local sheet-geometry maps at 1 mm
Per-crop calibrations, each estimated from a random sample of MASK pixels only:
  |Q  per-crop quantile -> normal-score transform of every feature
  |W  per-crop whitening (each crop gets its own linear recalibration of the whole feature space)
  |QW both
Everything selected by LOCO over the 8 TRAINING crops.
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import (TRAIN, load_crop, build_B88, standardise_cols, sample_idx, auc_vec,
                    nconv, fast_smooth)
from ca_step3_local import loc_mu_sd, build_geo, loco
from ca_step3b_norm import qtrans, whiten

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"
RSIG = [104, 156, 208, 312]
NU = 20000


def build_c(s, c):
    p = os.path.join(CACHE, f"caW_{s}_{c}.npz")
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
    F = standardise_cols(build_B88(x, m), m)

    def take(A, ii):
        return A.reshape(A.shape[0], -1)[:, ii].T.astype(np.float32)

    out["B88"] = take(F, idx); out["B88u"] = take(F, uidx)
    for sg in RSIG:
        dn = fast_smooth(mf, float(sg))
        R = np.empty_like(F)
        for i in range(F.shape[0]):
            R[i] = np.where(m, F[i] - nconv(F[i], mf, float(sg), dn), 0.0)
        out[f"R{sg}"] = take(R, idx); out[f"R{sg}u"] = take(R, uidx)
        del R
    del F
    G, gn = build_geo(np.concatenate([x, m[None].astype(np.float32)]), m)
    G = standardise_cols(G, m)
    out["GEO"] = take(G, idx); out["GEOu"] = take(G, uidx)
    np.savez_compressed(p, **out)
    return out


def main():
    crops = [f"{s}/{c}" for (s, c) in TRAIN]
    mats = {}
    for (s, c) in TRAIN:
        t0 = time.time()
        mats[f"{s}/{c}"] = build_c(s, c)
        print(f"built {s}/{c} ({time.time()-t0:.0f}s)", flush=True)

    def std(M):
        return (M - M.mean(0)) / (M.std(0) + 1e-6)

    def get(d, key, u=False):
        sfx = "u" if u else ""
        if key == "RMS":
            return np.hstack([d["R104" + sfx], d["R312" + sfx]])
        if key == "R104+GEO":
            return np.hstack([d["R104" + sfx], d["GEO" + sfx]])
        return d[key + sfx]

    bases = ["B88"] + [f"R{s}" for s in RSIG] + ["RMS", "R104+GEO"]
    specs = {}
    for bk in bases:
        specs[bk] = (lambda bk: (lambda d: std(get(d, bk))))(bk)
    for bk in ["B88", "R104", "R208", "RMS"]:
        specs[bk + "|Q"] = (lambda bk: (lambda d: qtrans(get(d, bk, True), get(d, bk))))(bk)
        specs[bk + "|W"] = (lambda bk: (lambda d: whiten(get(d, bk, True), get(d, bk))))(bk)
        specs[bk + "|QW"] = (lambda bk: (lambda d: whiten(
            qtrans(get(d, bk, True), get(d, bk, True)),
            qtrans(get(d, bk, True), get(d, bk)))))(bk)

    # geometry interactions on the best regional base
    A = np.zeros(88)
    for k in crops:
        X, y = mats[k]["R104"], mats[k]["y"]
        A += np.array([abs(auc_vec(X[:, j], y) - 0.5) for j in range(88)])
    top8 = np.argsort(-A)[:8]

    def inter(d, bk):
        Bm = std(get(d, bk)); G = std(d["GEO"])
        I = np.hstack([Bm[:, top8] * G[:, [g]] for g in range(G.shape[1])])
        return np.hstack([Bm, G, std(I)])
    specs["R104+GEO+INT"] = lambda d: inter(d, "R104")
    specs["RMS+GEO+INT"] = lambda d: inter(d, "RMS")

    res = {}
    for name, fn in specs.items():
        t0 = time.time()
        mn, per = loco(mats, crops, fn)
        res[name] = dict(loco=round(mn, 4), per_crop=per)
        print(f"{name:16s} LOCO {mn:.4f}  ({time.time()-t0:.0f}s)  {per}", flush=True)
    res["_crops"] = crops
    res["_top8_R104"] = [int(j) for j in top8]
    best = max((k for k in res if not k.startswith("_")), key=lambda k: res[k]["loco"])
    res["_best"] = best
    print("BEST", best, res[best]["loco"])
    json.dump(res, open(os.path.join(OUT, "ca_step3c_regional.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
