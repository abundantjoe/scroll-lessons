"""edgeshape step 2b: leave-one-crop-out logistic regression over the declared feature groups.
TRAINING crops only. Answers: does any level-invariant depth-profile SHAPE group carry ink
information, and does it ADD to the level (brightness) features?
"""
import os, sys, json, time
import numpy as np
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import es_lib as E

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore/es_step2_loco.json"

from es_combos import COMBOS, add_subgroups


def auc_vec(s, y):
    a = s[y]; z = s[~y]
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size))


names = list(np.load(os.path.join(CACHE, f"es_M_{E.TRAIN[0][0]}_{E.TRAIN[0][1]}.npz"),
                     allow_pickle=True)["names"])
data = []
for seg, crop in E.TRAIN:
    z = np.load(os.path.join(CACHE, f"es_M_{seg}_{crop}.npz"), allow_pickle=True)
    data.append((f"{seg}/{crop}", z["M"], z["y"], json.loads(str(z["gidx"]))))
gidx = add_subgroups(data[0][3], names)
print("crops", len(data), "features", data[0][1].shape, flush=True)

res = {}
t0 = time.time()
for cname, gs in COMBOS.items():
    cols = np.array(sorted(set(sum([gidx[g] for g in gs], []))))
    fold = []
    for i in range(len(data)):
        Xtr = np.concatenate([data[j][1][:, cols] for j in range(len(data)) if j != i])
        ytr = np.concatenate([data[j][2] for j in range(len(data)) if j != i])
        w = np.where(ytr, 1.0 / ytr.sum(), 1.0 / (~ytr).sum())
        mdl = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
        mdl.fit(Xtr, ytr.astype(np.int8), sample_weight=w)
        s = data[i][1][:, cols] @ mdl.coef_[0] + mdl.intercept_[0]
        fold.append(round(auc_vec(s, data[i][2]), 4))
        del Xtr, ytr
    res[cname] = {"nfeat": int(cols.size), "loco": fold, "mean": round(float(np.mean(fold)), 4)}
    print(f"{cname:18s} nf {cols.size:3d}  mean {res[cname]['mean']}  {fold}  {time.time()-t0:.0f}s", flush=True)

json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
