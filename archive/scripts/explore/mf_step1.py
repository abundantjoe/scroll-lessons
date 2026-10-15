"""Step 1: the best per-pixel depth projection, fit on TRAINING crops only."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *

def gather(crops):
    Xs, ys, ws = [], [], []
    for s, c in crops:
        x, mp = load_x(s, c)
        t, b = ds8_labels(s, c)
        sel = (t | b) & (mp > 0.5)
        X = x[:, sel].T.astype(np.float32)
        y = t[sel].astype(np.int8)
        w = np.where(y == 1, 1.0 / max(y.sum(), 1), 1.0 / max((y == 0).sum(), 1))
        Xs.append(X); ys.append(y); ws.append(w / len(crops))
    return np.concatenate(Xs), np.concatenate(ys), np.concatenate(ws)

if __name__ == "__main__":
    X, y, w = gather(TRAIN)
    print("train pixels", X.shape, "text", int(y.sum()), "blank", int((y == 0).sum()), flush=True)
    # single-channel AUCs (per-pixel ceiling check)
    per = []
    for i in range(22):
        a = auc(X[:, i], y == 1, y == 0)
        per.append(a)
    print("per-channel pooled train AUC:")
    for i, a in enumerate(per):
        face = "top" if i < 11 else "bot"
        d = (i % 11) - 4
        print("  ch%2d %s delta%+d : %.4f" % (i, face, d, a))
    wts, b0 = fit_logistic(X, y, w, l2=1.0)
    print("logistic weights:", np.round(wts, 3).tolist())
    p = X @ wts
    print("POOLED train projection per-pixel AUC: %.4f" % auc(p, y == 1, y == 0))
    np.save("/home/user/megara/stats/explore/proj_w.npy", wts)
    # per-crop
    out = {}
    for grp, crops in (("train", TRAIN), ("val", VAL)):
        for s, c in crops:
            x, mp = load_x(s, c)
            t, b = ds8_labels(s, c)
            sel = (t | b) & (mp > 0.5)
            pj = np.tensordot(wts.astype(np.float32), x, axes=(0, 0))
            a = auc(pj[sel], t[sel], b[sel])
            out[f"{grp}:{s}/{c}"] = round(a, 4)
            print(grp, s, c, "proj px AUC %.4f" % a, flush=True)
    json.dump({"weights": wts.tolist(), "per_channel_pooled_train": per, "per_crop": out},
              open("/home/user/megara/stats/explore/step1_projection.json", "w"), indent=1)
