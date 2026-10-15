"""Step 6: does it help to smooth BEFORE combining depths? Joint depth x scale linear
model (22 channels x 5 isotropic scales = 110 features) vs project-then-smooth.
Also local-contrast-normalised variants. LOCO over the 8 TRAINING crops."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
from scipy.ndimage import gaussian_filter

SC = [0, 4, 8, 16, 32]
W = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)

def crop_feats(s, c):
    x, mp = load_x(s, c)
    t, b = ds8_labels(s, c)
    m = (mp > 0.5).astype(np.float32)
    den = gaussian_filter(m, 2.0, mode="constant")
    sel = (t | b) & (mp > 0.5)
    F = []
    for i in range(22):
        num = gaussian_filter(x[i] * m, 2.0, mode="constant")
        qi = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)
        for sg in SC:
            F.append((gaussian_filter(qi, sg, mode="nearest") if sg else qi)[sel])
    X = np.stack(F, 1).astype(np.float32)
    # project-then-smooth reference on the same pixels
    pj = np.tensordot(W, x, axes=(0, 0)).astype(np.float32)
    num = gaussian_filter(pj * m, 2.0, mode="constant")
    q = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)
    ref = np.stack([(gaussian_filter(q, sg, mode="nearest") if sg else q)[sel] for sg in SC], 1)
    return X, ref, t[sel].astype(np.int8), b[sel]

if __name__ == "__main__":
    D = {}
    for s, c in TRAIN:
        D[(s, c)] = crop_feats(s, c)
        print("feat", s, c, D[(s, c)][0].shape, flush=True)
    res = {}
    for name, idx in (("depthXscale", 0), ("proj_then_smooth", 1)):
        for lam in [1.0, 10.0, 100.0]:
            aucs = []
            for held in TRAIN:
                Xs, ys, ws = [], [], []
                for k in TRAIN:
                    if k == held: continue
                    X = D[k][idx]; y = D[k][2]
                    X = (X - X.mean(0)) / (X.std(0) + 1e-6)
                    w = np.where(y == 1, 1.0 / max(y.sum(), 1), 1.0 / max((y == 0).sum(), 1))
                    Xs.append(X); ys.append(y); ws.append(w)
                wt, b0 = fit_logistic(np.concatenate(Xs), np.concatenate(ys), np.concatenate(ws), l2=lam)
                Xh = D[held][idx]; Xh = (Xh - Xh.mean(0)) / (Xh.std(0) + 1e-6)
                sc = Xh @ wt
                yh = D[held][2]
                aucs.append(auc(sc, yh == 1, yh == 0))
            res["%s_l2_%g" % (name, lam)] = {"folds": [round(a, 4) for a in aucs],
                                             "mean": round(float(np.mean(aucs)), 4)}
            print("%-18s l2=%-5g LOCO %.4f" % (name, lam, np.mean(aucs)), flush=True)
    json.dump(res, open("/home/user/megara/stats/explore/step6_depthxscale.json", "w"), indent=1)
