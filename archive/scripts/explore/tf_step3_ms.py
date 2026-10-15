"""twoface step 3: the same two-face question at multi-scale, with a CLEAN symmetric /
antisymmetric split.  TRAINING crops only, leave-one-crop-out.

Per crop a matrix (n_labelled_px, 22 channels, 5 spatial scales) is built from the
hole-filled channels; every family below is a column subset or a fixed linear combination
of that matrix, so all families see exactly the same pixels and the same spatial support.

  CH1        best single (channel, scale)                         <- baseline
  LVL        profile level (mean over the 22 channels), all scales
  BOT        11 bottom-face channels, all scales                  <- one-sided (writing face)
  TOP        11 top-face channels, all scales                     <- the NON-writing face alone
  ALL        both faces, all scales                               <- the two-face model
  TOPOUT     T-4..T-1 only: strictly OUTSIDE the non-writing face
  BOTOUT     B+1..B+6 only: strictly OUTSIDE the writing face (where an ink layer sits)
  ININ       T+1..T+6 and B-4..B-1: the sheet interior near either face
  SYM10      the 10 depth-symmetric sums  T(+d)+B(-d), T(-d)+B(+d) (through-thickness)
  ASYM10     the 10 depth-antisymmetric differences                (one-sided)
  ASYM10+L   ASYM10 plus the level
"""
import os, sys, json, time
import numpy as np
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tf_lib import load_crop, fill, smooth, NAMES, TRAIN

OUT = "/home/user/megara/stats/explore/tf_step3_ms.json"
SC = [0.0, 4.0, 8.0, 16.0, 32.0]
NS = len(SC)
IT = {d: i for i, d in enumerate(range(-4, 7))}
IB = {d: 11 + i for i, d in enumerate(range(-4, 7))}


def crop_matrix(seg, crop):
    x, m, t, b = load_crop(seg, crop)
    q = np.stack([fill(x[k], m, 2.0) for k in range(22)])
    sel = t | b
    M = np.empty((int(sel.sum()), 22, NS), np.float32)
    for j, s in enumerate(SC):
        qs = np.stack([smooth(q[k], s) for k in range(22)]) if s > 0 else q
        mu = qs[:, m].mean(1); sd = qs[:, m].std(1) + 1e-6
        M[:, :, j] = ((qs[:, sel].T - mu) / sd).astype(np.float32)
    return M, t[sel]


def fam(M, name):
    """-> (n, F) design matrix"""
    if name == "LVL":
        return M.mean(1)
    if name == "BOT":
        return M[:, 11:, :].reshape(len(M), -1)
    if name == "TOP":
        return M[:, :11, :].reshape(len(M), -1)
    if name == "ALL":
        return M.reshape(len(M), -1)
    if name == "TOPOUT":
        return M[:, [IT[d] for d in (-4, -3, -2, -1)], :].reshape(len(M), -1)
    if name == "BOTOUT":
        return M[:, [IB[d] for d in (1, 2, 3, 4, 5, 6)], :].reshape(len(M), -1)
    if name == "ININ":
        idx = [IT[d] for d in (1, 2, 3, 4, 5, 6)] + [IB[d] for d in (-4, -3, -2, -1)]
        return M[:, idx, :].reshape(len(M), -1)
    if name == "BOT+TOPOUT":
        idx = list(range(11, 22)) + [IT[d] for d in (-4, -3, -2, -1)]
        return M[:, idx, :].reshape(len(M), -1)
    if name == "TOPFAR":
        return M[:, [IT[-4], IT[-3]], :].reshape(len(M), -1)
    # depth-mirrored pairs that both exist: inside T(+d)<->B(-d) and outside T(-d)<->B(+d), d=1..4
    pairs = [(IT[d], IB[-d]) for d in (1, 2, 3, 4)] + [(IT[-d], IB[d]) for d in (1, 2, 3, 4)]
    if name == "SYM10":
        return np.stack([M[:, a, :] + M[:, c, :] for a, c in pairs], 1).reshape(len(M), -1)
    if name == "ASYM10":
        return np.stack([M[:, a, :] - M[:, c, :] for a, c in pairs], 1).reshape(len(M), -1)
    if name == "ASYM10+L":
        A = np.stack([M[:, a, :] - M[:, c, :] for a, c in pairs], 1).reshape(len(M), -1)
        return np.concatenate([A, M.mean(1)], 1)
    raise KeyError(name)


FAMS = ["LVL", "BOT", "TOP", "ALL", "TOPOUT", "TOPFAR", "BOTOUT", "ININ", "BOT+TOPOUT",
        "SYM10", "ASYM10", "ASYM10+L"]


def auc_vec(s, y):
    a = s[y]; z = s[~y]
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size))


t0 = time.time()
D = {}
for seg, crop in TRAIN:
    D[f"{seg}/{crop}"] = crop_matrix(seg, crop)
    print("built", seg, crop, D[f"{seg}/{crop}"][0].shape, f"{time.time()-t0:.0f}s", flush=True)
keys = list(D)

res = {}
for name in FAMS:
    per = []
    for k in keys:
        Xtr = np.concatenate([fam(D[o][0], name) for o in keys if o != k])
        ytr = np.concatenate([D[o][1] for o in keys if o != k])
        w = np.where(ytr, 1.0 / ytr.sum(), 1.0 / (~ytr).sum())
        mdl = LogisticRegression(C=1.0, max_iter=500, solver="lbfgs")
        mdl.fit(Xtr, ytr.astype(np.int8), sample_weight=w)
        Xte = fam(D[k][0], name)
        per.append(round(auc_vec(Xte @ mdl.coef_[0] + mdl.intercept_[0], D[k][1]), 4))
        del Xtr, ytr
    res[name] = {"loco": per, "mean": round(float(np.mean(per)), 4), "nfeat": fam(D[keys[0]][0], name).shape[1]}
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"{name:9s} nf={res[name]['nfeat']:3d} loco mean {res[name]['mean']}  {per}", flush=True)

# single (channel, scale) baseline
ch = {}
for c in range(22):
    for j, s in enumerate(SC):
        per = [round(auc_vec(D[k][0][:, c, j], D[k][1]), 4) for k in keys]
        ch[f"{NAMES[c]}@{int(s)}"] = {"per_crop": per, "mean": round(float(np.mean(per)), 4)}
best = max(ch, key=lambda n: ch[n]["mean"])
res["CH1"] = {"feature": best, "loco": ch[best]["per_crop"], "mean": ch[best]["mean"]}
res["_CH_all"] = ch
print("CH1 =", best, ch[best]["mean"], ch[best]["per_crop"], flush=True)
top5 = sorted(ch, key=lambda n: -ch[n]["mean"])[:8]
print("top single feats:", [(n, ch[n]["mean"]) for n in top5], flush=True)

json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
