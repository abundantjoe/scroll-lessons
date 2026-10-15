"""ca step 2: controls for step 1 + where the per-crop variation actually is.

(1) sample-size control: GLOBAL fitted on the other 7 crops subsampled to the SAME number of
    samples as the SELF fits, so SELF's deficit cannot be blamed on having less data.
(2) regularisation sweep for the SELF fits (C in 1e-3..1e2) - maybe per-crop fits just overfit.
(3) per-crop single-best-feature: which of the 88 features reads each crop best, and how much
    would an oracle per-crop CHOICE of feature gain over the globally best feature.
(4) per-crop weight vectors: pairwise cosine similarity, within- vs between-segment.
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import TRAIN, fit_logistic, auc_vec, NAMES88

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"


def load(s, c):
    z = np.load(os.path.join(CACHE, f"caB88_{s}_{c}.npz"))
    return z["X"], z["y"], z["rc"]


def main():
    D = {k: load(*k) for k in TRAIN}
    rng = np.random.default_rng(0)
    res = {}

    # ---------- (3)+(4) prep: per-crop single-feature AUCs and per-crop weights ----------
    sf = {}
    Wc = {}
    for (s, c) in TRAIN:
        X, y, _ = D[(s, c)]
        a = np.array([auc_vec(X[:, j], y) for j in range(X.shape[1])])
        sf[f"{s}/{c}"] = a
        w, _ = fit_logistic(X, y)
        Wc[f"{s}/{c}"] = w
    A = np.stack([sf[f"{s}/{c}"] for (s, c) in TRAIN])          # (8,88)
    # signed AUC excess so that direction matters
    best_global_j = int(np.argmax(np.abs(A - 0.5).mean(0)))
    gl = A[:, best_global_j]
    per_best = np.max(np.abs(A - 0.5), axis=1) + 0.5
    res["single_feature"] = dict(
        best_global_feature=NAMES88[best_global_j],
        best_global_per_crop=[round(float(v), 4) for v in gl],
        best_global_mean=round(float(np.mean(np.abs(gl - 0.5) + 0.5)), 4),
        oracle_percrop_feature=[NAMES88[int(np.argmax(np.abs(A[i] - 0.5)))] for i in range(len(TRAIN))],
        oracle_percrop_auc=[round(float(v), 4) for v in per_best],
        oracle_percrop_mean=round(float(per_best.mean()), 4),
        gain_from_percrop_feature_choice=round(float(per_best.mean() - np.mean(np.abs(gl - 0.5) + 0.5)), 4),
        crops=[f"{s}/{c}" for (s, c) in TRAIN])

    names = [f"{s}/{c}" for (s, c) in TRAIN]
    Wm = np.stack([Wc[n] / (np.linalg.norm(Wc[n]) + 1e-12) for n in names])
    Cs = Wm @ Wm.T
    within, between = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            (within if names[i].split("/")[0] == names[j].split("/")[0] else between).append(Cs[i, j])
    res["weight_similarity"] = dict(
        crops=names,
        cosine=[[round(float(v), 3) for v in row] for row in Cs],
        mean_within_segment=round(float(np.mean(within)), 3) if within else None,
        mean_between_segment=round(float(np.mean(between)), 3),
        mean_all_offdiag=round(float((Cs.sum() - len(names)) / (len(names) ** 2 - len(names))), 3))

    # ---------- (1) sample-size control + (2) C sweep ----------
    Cs_list = [0.001, 0.01, 0.1, 1.0, 10.0]
    ss = {f"{c:g}": [] for c in Cs_list}
    gh_sub = []
    gh_full = []
    for (s, c) in TRAIN:
        Xi, yi, rci = D[(s, c)]
        others = [k for k in TRAIN if k != (s, c)]
        Xo = np.concatenate([D[k][0] for k in others])
        yo = np.concatenate([D[k][1] for k in others])
        wg, bg = fit_logistic(Xo, yo)
        sg_full = Xi @ wg + bg
        for ax in (0, 1):
            med = np.median(rci[:, ax])
            P = rci[:, ax] < med
            for part in (P, ~P):
                trm, tem = part, ~part
                ntr = int(trm.sum())
                if min((yi[tem] == 1).sum(), (yi[tem] == 0).sum()) < 200:
                    continue
                gh_full.append(auc_vec(sg_full[tem], yi[tem]))
                # subsample the pooled training set to ntr samples
                sel = rng.choice(Xo.shape[0], min(ntr, Xo.shape[0]), replace=False)
                ws, bs = fit_logistic(Xo[sel], yo[sel])
                gh_sub.append(auc_vec(Xi[tem] @ ws + bs, yi[tem]))
                for Cv in Cs_list:
                    wh, bh = fit_logistic(Xi[trm], yi[trm], C=Cv)
                    ss[f"{Cv:g}"].append(auc_vec(Xi[tem] @ wh + bh, yi[tem]))
        del Xo, yo
        print("done", s, c, flush=True)
    res["controls"] = dict(
        GLOBAL_h_full=round(float(np.mean(gh_full)), 4),
        GLOBAL_h_samplesize_matched=round(float(np.mean(gh_sub)), 4),
        SELF_by_C={k: round(float(np.mean(v)), 4) for k, v in ss.items()},
        SELF_best_C=max(ss, key=lambda k: np.mean(ss[k])),
        n_folds=len(gh_full))
    print(json.dumps(res["controls"], indent=1))
    print(json.dumps(res["single_feature"], indent=1))
    print("weights:", json.dumps({k: v for k, v in res["weight_similarity"].items() if k != "cosine"}))
    json.dump(res, open(os.path.join(OUT, "ca_step2_control.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
