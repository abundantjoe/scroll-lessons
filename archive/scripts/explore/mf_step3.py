"""Step 3: does shape-matched integration add anything ON TOP of isotropic smoothing?
Leave-one-crop-out CV over the 8 TRAINING crops. Feature bank cached to disk."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *

W = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)
FDIR = "/home/user/megara/stats/explore/feat"
os.makedirs(FDIR, exist_ok=True)

ISO = [0, 4, 8, 11, 16, 22, 32, 45]
RID = [8, 11, 16, 22, 30]
ORI = [(16, 5), (24, 8), (40, 8), (40, 12), (60, 12)]
TOP = [8, 18, 26]

ISO_KEYS = [f"iso{s}" for s in ISO]
SHAPE_KEYS = ([f"ridge{s}" for s in RID] + [f"frangi{s}" for s in RID]
              + [f"ori{a}x{w}" for a, w in ORI] + [f"ani{a}x{w}" for a, w in ORI]
              + [f"wth{r}" for r in TOP] + [f"bth{r}" for r in TOP])

def build(s, c):
    p = os.path.join(FDIR, f"{s}_{c}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return {k: z[k] for k in z.files if k not in ("t", "b", "sel")}, z["t"], z["b"], z["sel"]
    x, mp = load_x(s, c)
    t, b = ds8_labels(s, c)
    pj = np.tensordot(W, x, axes=(0, 0)).astype(np.float32)
    m = (mp > 0.5).astype(np.float32)
    q, _ = fill(pj, m, 2.0)
    f = {}
    for sg in ISO:
        f[f"iso{sg}"] = (gaussian_filter(q, sg, mode="nearest") if sg > 0 else q).astype(np.float32)
    for sg in RID:
        hs, _ = hessian_feats(q, sg)
        f[f"ridge{sg}"], _d, _t, f[f"frangi{sg}"] = hs
    for a, w_ in ORI:
        r, ani = oriented_bank(q, a, w_)
        f[f"ori{a}x{w_}"] = r; f[f"ani{a}x{w_}"] = ani
    for r_ in TOP:
        th, bh = tophat(q, r_)
        f[f"wth{r_}"] = th; f[f"bth{r_}"] = bh
    sel = (t | b) & (mp > 0.5)
    np.savez(p, t=t, b=b, sel=sel, **f)
    return f, t, b, sel

def mat(f, keys, sel):
    return np.stack([f[k][sel] for k in keys], 1).astype(np.float32)

if __name__ == "__main__":
    data = {}
    for s, c in TRAIN + VAL:
        f, t, b, sel = build(s, c)
        data[(s, c)] = (f, t, b, sel)
        print("built", s, c, flush=True)

    banks = {"ISO": ISO_KEYS, "SHAPE": SHAPE_KEYS, "ISO+SHAPE": ISO_KEYS + SHAPE_KEYS}
    out = {}
    for name, keys in banks.items():
        # standardise per crop with train-fold stats only (features are already per-crop standardised inputs)
        aucs = []
        for held in TRAIN:
            Xs, ys, ws = [], [], []
            for s, c in TRAIN:
                if (s, c) == held: continue
                f, t, b, sel = data[(s, c)]
                X = mat(f, keys, sel); y = t[sel].astype(np.int8)
                mu = X.mean(0); sd = X.std(0) + 1e-6
                X = (X - mu) / sd
                w = np.where(y == 1, 1.0 / max(y.sum(), 1), 1.0 / max((y == 0).sum(), 1))
                Xs.append(X); ys.append(y); ws.append(w)
            Xa = np.concatenate(Xs); ya = np.concatenate(ys); wa = np.concatenate(ws)
            wt, b0 = fit_logistic(Xa, ya, wa, l2=10.0)
            f, t, b, sel = data[held]
            Xh = mat(f, keys, sel); Xh = (Xh - Xh.mean(0)) / (Xh.std(0) + 1e-6)
            a = auc(Xh @ wt, t[sel], b[sel])
            aucs.append(a)
            print("  %-10s hold %s/%s  %.4f" % (name, held[0], held[1], a), flush=True)
        out[name] = {"loco": [round(a, 4) for a in aucs], "mean": round(float(np.mean(aucs)), 4)}
        print("%-10s LOCO mean %.4f" % (name, np.mean(aucs)), flush=True)
    # reference: best single isotropic under the same protocol
    for k in ISO_KEYS + ["ridge22", "ori40x8"]:
        a = [auc(data[(s, c)][0][k][data[(s, c)][3]], data[(s, c)][1][data[(s, c)][3]],
                 data[(s, c)][2][data[(s, c)][3]]) for s, c in TRAIN]
        out[k] = {"per_crop": [round(v, 4) for v in a], "mean": round(float(np.mean(a)), 4)}
        print("single %-10s mean %.4f" % (k, np.mean(a)))
    json.dump(out, open("/home/user/megara/stats/explore/step3_loco.json", "w"), indent=1)
