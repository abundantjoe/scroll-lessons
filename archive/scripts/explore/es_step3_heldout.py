"""edgeshape step 3: the single held-out run declared in stats/explore/es_DECLARATION.md.

Fits the chosen group combinations on the 8 TRAINING crops (cached sampled rows) and reports
pixel AUC on the 19.2 um ds8 grid for the 7 EVALUATION crops, next to the existing methods
re-measured on exactly the same pixels (their 2.4 um score maps mean-pooled 8x).

usage: es_step3_heldout.py COMBO[,COMBO...]
"""
import os, sys, json, time
import numpy as np
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import es_lib as E
from es_combos import COMBOS, add_subgroups
from es_step2_build import SIGS, GROUPS
from mf_lib import cropdir, pool

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore/es_step3_heldout.json"
COMPARATORS = ["v1b", "v2", "v3", "team"]


def auc_vec(s, y):
    a = s[y]; z = s[~y]
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size))


def eval_matrix(seg, crop):
    """full (not subsampled) feature matrix at the labelled pixels of a crop, same column order
    and same per-crop standardisation as es_step2_build."""
    x, m, t, b = E.load_crop(seg, crop)
    sel = t | b
    y = t[sel]
    idx = np.flatnonzero(sel.ravel())
    cols, names = [], []
    for sg in SIGS:
        g = E.build_groups(x, m, sg)
        for gn in GROUPS:
            F, nm = g[gn]
            for i, n in enumerate(nm):
                f = F[i].ravel()
                mu = float(f[m.ravel()].mean()); sd = float(f[m.ravel()].std()) + 1e-9
                cols.append(((f[idx] - mu) / sd).astype(np.float32))
                names.append(f"{gn}:{n}@{sg}")
        del g
    return np.stack(cols, axis=1), y, sel, m, t.shape


combos = sys.argv[1].split(",")
data = []
for seg, crop in E.TRAIN:
    z = np.load(os.path.join(CACHE, f"es_M_{seg}_{crop}.npz"), allow_pickle=True)
    data.append((z["M"], z["y"]))
gidx = json.loads(str(np.load(os.path.join(CACHE, f"es_M_{E.TRAIN[0][0]}_{E.TRAIN[0][1]}.npz"),
                              allow_pickle=True)["gidx"]))
_names = list(np.load(os.path.join(CACHE, f"es_M_{E.TRAIN[0][0]}_{E.TRAIN[0][1]}.npz"),
                      allow_pickle=True)["names"])
gidx = add_subgroups(gidx, _names)
ytr = np.concatenate([d[1] for d in data])
w = np.where(ytr, 1.0 / ytr.sum(), 1.0 / (~ytr).sum())

fitted = {}
for cname in combos:
    cols = np.array(sorted(set(sum([gidx[g] for g in COMBOS[cname]], []))))
    X = np.concatenate([d[0][:, cols] for d in data])
    mdl = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
    mdl.fit(X, ytr.astype(np.int8), sample_weight=w)
    fitted[cname] = (cols, mdl.coef_[0].astype(np.float64), float(mdl.intercept_[0]))
    print(f"fitted {cname} nf={cols.size} in-sample TRAIN auc "
          f"{auc_vec(X @ mdl.coef_[0] + mdl.intercept_[0], ytr):.4f}", flush=True)
    del X
del data

res = {}
t0 = time.time()
for seg, crop in E.EVAL:
    M, y, sel, m, shp = eval_matrix(seg, crop)
    ent = {}
    for cname, (cols, cw, cb) in fitted.items():
        ent[cname] = round(auc_vec(M[:, cols] @ cw + cb, y), 4)
    h8 = shp[0]
    for tag in COMPARATORS:
        p = cropdir(seg, crop) + f"/s_bot_{tag}.npy"
        if not os.path.exists(p):
            continue
        S = pool(np.load(p).astype(np.float32), h8, h8)
        ent[tag] = round(auc_vec(np.where(m, S, 0.0)[sel], y), 4)
    ent["n_text"] = int(y.sum()); ent["n_blank"] = int((~y).sum())
    res[f"{seg}/{crop}"] = ent
    print(f"{seg}/{crop}: " + "  ".join(f"{k} {v}" for k, v in ent.items()) +
          f"   {time.time()-t0:.0f}s", flush=True)
    del M

keys = combos + COMPARATORS
res["_heldout_mean"] = {k: round(float(np.mean([res[c][k] for c in res if k in res[c]])), 4) for k in keys}
json.dump(res, open(OUT, "w"), indent=1)
print("\nHELD-OUT MEANS (7 eval crops, ds8 pixel AUC):")
for k in keys:
    print(f"  {k:18s} {res['_heldout_mean'][k]}")
print("wrote", OUT)
