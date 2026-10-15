"""twoface step 1 (TRAINING crops only): per-face, per-depth detectability, profile level
vs shape, and whether the NON-writing (top) face carries anything not explained by the
writing (bottom) face.  Nothing is fitted here that is carried to EVAL; pure diagnosis."""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tf_lib import load_crop, fill, smooth, auc, NAMES, DELTAS, TRAIN, VAL

OUT = "/home/user/megara/stats/explore/tf_step1_diag.json"
SIGMAS = [0.0, 4.0, 8.0, 16.0]

res = {}
for s, c in TRAIN + VAL:
    key = f"{s}/{c}"
    x, m, t, b = load_crop(s, c)
    n = m.sum()
    q = np.stack([fill(x[k], m, 2.0) for k in range(22)])       # hole-filled channels
    ent = {"n_text": int(t.sum()), "n_blank": int(b.sum()), "mask_frac": float(m.mean())}

    # ---- per-channel AUC at several isotropic smoothings
    for sg in SIGMAS:
        qs = np.stack([smooth(q[k], sg) for k in range(22)]) if sg > 0 else q
        a = [round(auc(qs[k], t, b), 4) for k in range(22)]
        ent[f"auc_s{int(sg)}"] = dict(zip(NAMES, a))
        ent[f"best_top_s{int(sg)}"] = [NAMES[int(np.argmax(np.abs(np.array(a[:11]) - .5)))],
                                       max(a[:11], key=lambda v: abs(v - .5))]
        ent[f"best_bot_s{int(sg)}"] = [NAMES[11 + int(np.argmax(np.abs(np.array(a[11:]) - .5)))],
                                       max(a[11:], key=lambda v: abs(v - .5))]

    # ---- profile level: mean channel value on text vs blank (raw, standardised units)
    mt = np.array([x[k][t].mean() for k in range(22)])
    mb = np.array([x[k][b].mean() for k in range(22)])
    sd = np.array([x[k][m].std() for k in range(22)])
    ent["mean_text"] = [round(float(v), 4) for v in mt]
    ent["mean_blank"] = [round(float(v), 4) for v in mb]
    ent["cohens_d"] = [round(float(v), 4) for v in (mt - mb) / np.maximum(sd, 1e-6)]

    # ---- does the TOP face carry anything the BOTTOM face does not?
    # regress each top channel on all 11 bottom channels over the mask, AUC of residual
    B = np.stack([q[11 + j][m] for j in range(11)], 1).astype(np.float64)
    B = np.concatenate([B, np.ones((B.shape[0], 1))], 1)
    G = B.T @ B + 1e-3 * np.eye(B.shape[1])
    part = {}
    for k in range(11):
        yv = q[k][m].astype(np.float64)
        w = np.linalg.solve(G, B.T @ yv)
        r = np.zeros_like(q[k]); r[m] = (yv - B @ w).astype(np.float32)
        part[NAMES[k]] = [round(auc(r, t, b), 4),
                          round(float(1.0 - ((yv - B @ w) ** 2).sum() / max(((yv - yv.mean()) ** 2).sum(), 1e-9)), 4)]
    ent["top_resid_after_bottom_auc_and_R2"] = part
    # and the reverse: bottom channels after removing the top face
    T = np.stack([q[j][m] for j in range(11)], 1).astype(np.float64)
    T = np.concatenate([T, np.ones((T.shape[0], 1))], 1)
    GT = T.T @ T + 1e-3 * np.eye(T.shape[1])
    part2 = {}
    for k in range(11, 22):
        yv = q[k][m].astype(np.float64)
        w = np.linalg.solve(GT, T.T @ yv)
        r = np.zeros_like(q[k]); r[m] = (yv - T @ w).astype(np.float32)
        part2[NAMES[k]] = [round(auc(r, t, b), 4),
                           round(float(1.0 - ((yv - T @ w) ** 2).sum() / max(((yv - yv.mean()) ** 2).sum(), 1e-9)), 4)]
    ent["bot_resid_after_top_auc_and_R2"] = part2

    # ---- cross-face correlation of the channel maps (over the mask)
    cc = np.corrcoef(np.stack([q[k][m] for k in range(22)]))
    ent["corr_topmean_botmean"] = round(float(np.mean(cc[:11, 11:])), 4)
    ent["corr_max_cross"] = round(float(np.max(np.abs(cc[:11, 11:]))), 4)

    res[key] = ent
    print(key, "n_t", ent["n_text"], "n_b", ent["n_blank"],
          "bestBOT s8", ent["best_bot_s8"], "bestTOP s8", ent["best_top_s8"],
          "xcorr", ent["corr_topmean_botmean"], flush=True)

json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
