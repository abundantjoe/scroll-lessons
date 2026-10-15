"""ca step 1: is there per-crop calibration headroom?

GLOBAL(i)   : logistic fitted on the other 7 TRAINING crops, evaluated on crop i.
SELF(i)     : fitted on one spatial half of crop i, evaluated on the other half (both split
              directions, both halves, averaged).
GLOBAL_h(i) : the LOCO model evaluated on exactly the same held-out halves.
INSAMPLE(i) : fitted and evaluated on all of crop i (optimistic, reported, not evidence).
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import (TRAIN, VAL, load_crop, build_B88, standardise_cols, sample_idx,
                    fit_logistic, auc_vec, NAMES88)

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"


def cache_crop(s, c, nmax=20000):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"caB88_{s}_{c}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return z["X"], z["y"], z["rc"]
    x, m, t, b = load_crop(s, c)
    F = build_B88(x, m)
    F = standardise_cols(F, m)
    idx, y = sample_idx(t, b, nmax=nmax, seed=0)
    H, W = m.shape
    X = F.reshape(F.shape[0], -1)[:, idx].T.astype(np.float32)
    rc = np.stack([idx // W, idx % W]).T.astype(np.int32)
    np.savez_compressed(p, X=X, y=y, rc=rc)
    del F
    return X, y, rc


def main():
    crops = TRAIN + VAL
    data = {}
    for s, c in crops:
        t0 = time.time()
        X, y, rc = cache_crop(s, c)
        data[(s, c)] = (X, y, rc)
        print(f"{s}/{c}: X {X.shape} text {(y==1).sum()} blank {(y==0).sum()} "
              f"({time.time()-t0:.0f}s)", flush=True)

    res = {}
    W_self = {}
    tr = TRAIN
    for i, (s, c) in enumerate(tr):
        Xi, yi, rci = data[(s, c)]
        # ---- GLOBAL: fit on other 7 training crops
        Xo = np.concatenate([data[k][0] for k in tr if k != (s, c)])
        yo = np.concatenate([data[k][1] for k in tr if k != (s, c)])
        wg, bg = fit_logistic(Xo, yo)
        del Xo, yo
        sg = Xi @ wg + bg
        a_global = auc_vec(sg, yi)
        # ---- INSAMPLE
        wi, bi = fit_logistic(Xi, yi)
        a_ins = auc_vec(Xi @ wi + bi, yi)
        W_self[f"{s}/{c}"] = wi.tolist()
        # ---- SELF via spatial halves
        selfs, globs = [], []
        for ax in (0, 1):
            med = np.median(rci[:, ax])
            A = rci[:, ax] < med
            for part in (A, ~A):
                tr_m = part; te_m = ~part
                if (yi[te_m] == 1).sum() < 200 or (yi[te_m] == 0).sum() < 200:
                    continue
                if (yi[tr_m] == 1).sum() < 200 or (yi[tr_m] == 0).sum() < 200:
                    continue
                wh, bh = fit_logistic(Xi[tr_m], yi[tr_m])
                selfs.append(auc_vec(Xi[te_m] @ wh + bh, yi[te_m]))
                globs.append(auc_vec(sg[te_m], yi[te_m]))
        res[f"{s}/{c}"] = dict(GLOBAL=round(a_global, 4),
                               SELF=round(float(np.mean(selfs)), 4),
                               GLOBAL_h=round(float(np.mean(globs)), 4),
                               SELF_folds=[round(v, 4) for v in selfs],
                               GLOBAL_h_folds=[round(v, 4) for v in globs],
                               INSAMPLE_optimistic=round(a_ins, 4),
                               n_text=int((yi == 1).sum()), n_blank=int((yi == 0).sum()))
        print(f"{s}/{c}: GLOBAL {a_global:.4f}  SELF {np.mean(selfs):.4f}  "
              f"GLOBAL_h {np.mean(globs):.4f}  insample {a_ins:.4f}", flush=True)

    mg = float(np.mean([v["GLOBAL"] for v in res.values()]))
    ms = float(np.mean([v["SELF"] for v in res.values()]))
    mgh = float(np.mean([v["GLOBAL_h"] for v in res.values()]))
    mi = float(np.mean([v["INSAMPLE_optimistic"] for v in res.values()]))
    res["_mean"] = dict(GLOBAL=round(mg, 4), SELF=round(ms, 4), GLOBAL_h=round(mgh, 4),
                        INSAMPLE_optimistic=round(mi, 4),
                        SELF_minus_GLOBAL_h=round(ms - mgh, 4))
    print("MEAN", json.dumps(res["_mean"]))
    json.dump(res, open(os.path.join(OUT, "ca_step1_percrop.json"), "w"), indent=1)
    json.dump({"names": NAMES88, "w": W_self},
              open(os.path.join(OUT, "ca_step1_weights.json"), "w"))


if __name__ == "__main__":
    main()
