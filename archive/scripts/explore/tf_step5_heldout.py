"""twoface step 5: the single held-out run declared in stats/explore/tf_DECLARATION.md.

Fits the declared models on the 8 TRAINING crops and reports pixel AUC on the 19.2 um ds8
grid for the 7 EVALUATION crops, next to the existing methods re-measured on exactly the
same pixels (their 2.4 um score maps mean-pooled 8x).
"""
import os, sys, json, time
import numpy as np
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tf_lib import load_crop, fill, smooth, NAMES, TRAIN, EVAL
from mf_lib import cropdir, pool
from tf_step3_ms import crop_matrix, fam, SC

OUT = "/home/user/megara/stats/explore/tf_step5_heldout.json"
MODELS = ["CH1", "ALL", "BOT", "TOP", "SYM10", "ASYM10", "BOT+TOPOUT"]
CH1_C, CH1_S = 11, 3          # channel B-4 (index 11), scale index 3 (sigma 16)
COMPARATORS = ["v1b", "v2", "v3", "team"]


def auc_vec(s, y):
    a = s[y]; z = s[~y]
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size))


t0 = time.time()
Xtr, ytr = {}, []
mats = []
for seg, crop in TRAIN:
    M, y = crop_matrix(seg, crop)
    mats.append(M); ytr.append(y)
    print("train matrix", seg, crop, M.shape, f"{time.time()-t0:.0f}s", flush=True)
ytr = np.concatenate(ytr)
w = np.where(ytr, 1.0 / ytr.sum(), 1.0 / (~ytr).sum())

fitted = {}
for name in MODELS:
    if name == "CH1":
        continue
    X = np.concatenate([fam(M, name) for M in mats])
    mdl = LogisticRegression(C=1.0, max_iter=500, solver="lbfgs")
    mdl.fit(X, ytr.astype(np.int8), sample_weight=w)
    fitted[name] = (mdl.coef_[0].astype(np.float64), float(mdl.intercept_[0]))
    tr = auc_vec(X @ mdl.coef_[0] + mdl.intercept_[0], ytr)
    print(f"fitted {name:11s} nf={X.shape[1]:3d} in-sample TRAIN auc {tr:.4f}", flush=True)
    del X
del mats

json.dump({k: {"w": list(v[0]), "b": v[1]} for k, v in fitted.items()},
          open("/home/user/megara/stats/explore/tf_weights.json", "w"))

res = {}
for seg, crop in EVAL:
    M, y = crop_matrix(seg, crop)
    ent = {}
    ent["CH1"] = round(auc_vec(M[:, CH1_C, CH1_S], y), 4)
    for name in MODELS:
        if name == "CH1":
            continue
        cw, b = fitted[name]
        ent[name] = round(auc_vec(fam(M, name) @ cw + b, y), 4)
    # comparators on exactly the same pixels
    x, m, t, bl = load_crop(seg, crop)
    sel = t | bl
    h8 = t.shape[0]
    for tag in COMPARATORS:
        p = cropdir(seg, crop) + f"/s_bot_{tag}.npy"
        if not os.path.exists(p):
            continue
        S = pool(np.load(p).astype(np.float32), h8, h8)
        S = np.where(m, S, 0.0)
        ent[tag] = round(auc_vec(S[sel], y), 4)
    ent["n_text"] = int(y.sum()); ent["n_blank"] = int((~y).sum())
    res[f"{seg}/{crop}"] = ent
    print(f"{seg}/{crop}: " + "  ".join(f"{k} {v}" for k, v in ent.items()), flush=True)
    del M

names = MODELS + COMPARATORS
means = {n: round(float(np.mean([res[k][n] for k in res if n in res[k]])), 4) for n in names}
res["_heldout_mean"] = means
print("\nHELD-OUT MEANS (7 eval crops, ds8 pixel AUC):")
for n in names:
    print(f"  {n:11s} {means[n]}")
json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
