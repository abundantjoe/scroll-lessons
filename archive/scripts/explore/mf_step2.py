"""Step 2: single-feature sweep. Isotropic smoothing vs shape-matched integration,
per TRAINING crop, on the depth projection fitted in step 1."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *

W = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)

def base(s, c, s0=2.0):
    x, mp = load_x(s, c)
    t, b = ds8_labels(s, c)
    p = np.tensordot(W, x, axes=(0, 0)).astype(np.float32)
    m = (mp > 0.5).astype(np.float32)
    q, den = fill(p, m, s0)
    sel = (t | b) & (mp > 0.5)
    return q, m, t, b, sel, p

ISO = [0, 2, 4, 6, 8, 11, 16, 22, 32, 45]
RID = [3, 5, 8, 11, 16, 22]
ORI = [(8, 3), (16, 3), (16, 5), (24, 5), (32, 5), (24, 8), (40, 8), (16, 8)]
TOP = [4, 8, 12, 18, 26]

def feats(q):
    f = {}
    for s in ISO:
        f[f"iso{s}"] = gaussian_filter(q, s, mode="nearest") if s > 0 else q
    for s in RID:
        hs, _ = hessian_feats(q, s)
        f[f"ridge{s}"], f[f"det{s}"], f[f"trace{s}"], f[f"frangi{s}"] = hs
    for (a, w_) in ORI:
        r, ani = oriented_bank(q, a, w_)
        f[f"ori{a}x{w_}"] = r
        f[f"ani{a}x{w_}"] = ani
    for r in TOP:
        th, bh = tophat(q, r)
        f[f"wth{r}"] = th
        f[f"bth{r}"] = bh
    return f

if __name__ == "__main__":
    res = {}
    for s, c in TRAIN + VAL:
        q, m, t, b, sel, p = base(s, c)
        f = feats(q)
        r = {k: round(auc(v[sel], t[sel], b[sel]), 4) for k, v in f.items()}
        r["proj_raw"] = round(auc(p[sel], t[sel], b[sel]), 4)
        r["q_filled"] = round(auc(q[sel], t[sel], b[sel]), 4)
        res[f"{s}/{c}"] = r
        print(f"{s}/{c}", flush=True)
        for k in sorted(r, key=lambda z: -r[z])[:8]:
            print("   %-12s %.4f" % (k, r[k]))
    json.dump(res, open("/home/user/megara/stats/explore/step2_single_feats.json", "w"), indent=1)
    # summary: mean over the 8 TRAIN crops
    keys = list(res[f"{TRAIN[0][0]}/{TRAIN[0][1]}"].keys())
    print("\n== mean over 8 TRAIN crops ==")
    mt = {k: float(np.mean([res[f"{s}/{c}"][k] for s, c in TRAIN])) for k in keys}
    for k in sorted(mt, key=lambda z: -mt[z]):
        print("  %-12s %.4f   (val %.4f)" % (k, mt[k], res[f"{VAL[0][0]}/{VAL[0][1]}"][k]))
