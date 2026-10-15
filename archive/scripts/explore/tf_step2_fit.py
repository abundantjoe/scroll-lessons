"""twoface step 2: leave-one-crop-out model comparison on the TRAINING crops ONLY.

Geometry established from scripts/topo_faces.py: k_top and k_bot are the two 50%-of-peak
crossings of the smoothed depth profile, k increasing from the top face to the bottom face.
Therefore
  T-4..T-1 = OUTSIDE the top face (9.6..2.4 um above the sheet)
  T+0      = the top crossing  == 0.5*peak
  T+1..T+6 = INSIDE the sheet from the top     (2.4..14.4 um)
  B-4..B-1 = INSIDE the sheet from the bottom  (9.6..2.4 um)
  B+0      = the bottom crossing == 0.5*peak  (algebraically the same number as T+0)
  B+1..B+6 = OUTSIDE the bottom (writing) face
Median sheet thickness is 21-25 slices (50-60 um), so the two faces are genuinely 50-60 um
apart and the interior between T+6 and B-4 is NOT sampled.

Feature families compared (all linear-logistic, identical pixels, identical smoothing):
  BEST1     the single best channel (chosen by the same LOCO protocol)  <- baseline
  BOT11     the 11 bottom-face channels                                 <- one-sided
  TOP11     the 11 top-face channels                                    <- the NON-writing face
  ALL22     both faces
  LVL       the profile level only (mean of the 22 channels)
  SHAPE21   the 22 channels minus their own level (pure profile SHAPE)
  SHAPE_DT  level + slope removed per face, i.e. shape after a per-face affine normalisation
  SYM       level + the depth-symmetric combinations  T(+d)+B(-d), T(-d)+B(+d)  (through-thickness)
  ASYM      the depth-antisymmetric combinations      T(+d)-B(-d), T(-d)-B(+d)  (one-sided)
  SUMDIFF   SYM + ASYM (a full reparametrisation of ALL22; sanity check == ALL22)
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tf_lib import load_crop, fill, smooth, auc, NAMES, TRAIN, VAL, EVAL

from sklearn.linear_model import LogisticRegression

OUT = "/home/user/megara/stats/explore/tf_step2_loco.json"
SIGMAS = [0.0, 8.0, 16.0]

TOP = list(range(11))            # T-4..T+6
BOT = list(range(11, 22))        # B-4..B+6
IT = {f"T{d:+d}": i for i, d in enumerate(range(-4, 7))}
IB = {f"B{d:+d}": 11 + i for i, d in enumerate(range(-4, 7))}


def build_feats(q):
    """q: (22,H,W) hole-filled, smoothed channels -> dict of (F,H,W) feature stacks."""
    lvl = q.mean(0)
    shape = q - lvl[None]
    # per-face affine (mean + linear-in-delta slope) removed
    d = np.arange(-4, 7, dtype=np.float32)
    d = (d - d.mean()) / np.sqrt((d ** 2).sum() - 11 * d.mean() ** 2)
    sh_aff = []
    for face in (TOP, BOT):
        blk = q[face]
        mu = blk.mean(0)
        sl = np.tensordot(d, blk - mu[None], axes=(0, 0))
        sh_aff.append(blk - mu[None] - d[:, None, None] * sl[None])
    sh_aff = np.concatenate(sh_aff, 0)                  # 22, rank 18
    # symmetric / antisymmetric pairs about the sheet mid-plane
    sym, asym = [], []
    for k in range(1, 7):                               # inside pairs T+k <-> B-k
        if f"B{-k:+d}" in IB:
            a, b = q[IT[f"T{+k:+d}"]], q[IB[f"B{-k:+d}"]]
            sym.append(a + b); asym.append(a - b)
    for k in range(1, 5):                               # outside pairs T-k <-> B+k
        a, b = q[IT[f"T{-k:+d}"]], q[IB[f"B{+k:+d}"]]
        sym.append(a + b); asym.append(a - b)
    sym = np.stack(sym); asym = np.stack(asym)
    unp = np.stack([q[IT["T+0"]], q[IB["B+5"]], q[IB["B+6"]]])   # unpaired channels
    return {
        "BOT11": q[BOT], "TOP11": q[TOP], "ALL22": q,
        "LVL": lvl[None], "SHAPE21": shape, "SHAPE_DT": sh_aff,
        "SYM": np.concatenate([lvl[None], sym, unp]),
        "ASYM": np.concatenate([asym, unp]),
        "SUMDIFF": np.concatenate([sym, asym, unp]),
    }


def rows(seg, crop, sigma):
    x, m, t, b = load_crop(seg, crop)
    q = np.stack([fill(x[k], m, 2.0) for k in range(22)])
    if sigma > 0:
        q = np.stack([smooth(q[k], sigma) for k in range(22)])
    F = build_feats(q)
    sel = t | b
    out = {}
    for name, st in F.items():
        v = st[:, sel].T.astype(np.float32)
        mu = st[:, m].mean(1); sd = st[:, m].std(1) + 1e-6      # per-crop, unsupervised
        out[name] = ((v - mu) / sd).astype(np.float32)
    # single channels (per-crop standardised too)
    v = q[:, sel].T.astype(np.float32)
    mu = q[:, m].mean(1); sd = q[:, m].std(1) + 1e-6
    out["_CHAN"] = ((v - mu) / sd).astype(np.float32)
    return out, t[sel].astype(np.int8) if False else (t[sel] if t[sel].dtype == bool else t[sel])


def fit_eval(Xtr, ytr, Xte, yte, C=1.0):
    w = np.where(ytr == 1, 1.0 / max(ytr.sum(), 1), 1.0 / max((~ytr).sum(), 1))
    mdl = LogisticRegression(C=C, max_iter=400, solver="lbfgs")
    mdl.fit(Xtr, ytr.astype(np.int8), sample_weight=w)
    s = Xte @ mdl.coef_[0] + mdl.intercept_[0]
    a = s[yte]; z = s[~yte]
    from scipy.stats import rankdata
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size)), mdl


def auc_vec(s, y):
    from scipy.stats import rankdata
    a = s[y]; z = s[~y]
    rk = rankdata(np.concatenate([a, z]))
    return float((rk[:a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * z.size))


res = {}
t0 = time.time()
for sigma in SIGMAS:
    data = {}
    for seg, crop in TRAIN:
        data[f"{seg}/{crop}"] = rows(seg, crop, sigma)
        print(f"sigma {sigma} built {seg}/{crop} {time.time()-t0:.0f}s", flush=True)
    keys = list(data.keys())
    ent = {}
    fams = [k for k in data[keys[0]][0] if not k.startswith("_")]
    for fam in fams:
        per = []
        for i, k in enumerate(keys):
            Xtr = np.concatenate([data[o][0][fam] for o in keys if o != k])
            ytr = np.concatenate([data[o][1] for o in keys if o != k])
            a, _ = fit_eval(Xtr, ytr, data[k][0][fam], data[k][1])
            per.append(round(a, 4))
        ent[fam] = {"loco": per, "mean": round(float(np.mean(per)), 4)}
        print(f"  sigma {sigma} {fam:9s} loco mean {ent[fam]['mean']}  {per}", flush=True)
    # single channels
    ch = {}
    for c in range(22):
        per = [round(auc_vec(data[k][0]["_CHAN"][:, c], data[k][1]), 4) for k in keys]
        ch[NAMES[c]] = {"per_crop": per, "mean": round(float(np.mean(per)), 4),
                        "mean_abs": round(float(np.mean([abs(p - .5) for p in per])) + .5, 4)}
    ent["_CHAN"] = ch
    best = max(ch, key=lambda n: ch[n]["mean"])
    ent["BEST1"] = {"channel": best, "loco": ch[best]["per_crop"], "mean": ch[best]["mean"]}
    print(f"  sigma {sigma} BEST1 = {best} mean {ch[best]['mean']}", flush=True)
    res[f"sigma{int(sigma)}"] = ent
    del data

json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
