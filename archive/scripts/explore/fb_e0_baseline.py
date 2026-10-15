"""E0: AUC of the existing score maps on the ds8 (19.2 um) pixel grid, exactly the pixel set
used for every fiberbg experiment. Pools the full-res s_bot_<tag>.npy 8x the same way ds8_x was made."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

F = 8
TAGS = ["v0.1b", "v1b", "v2", "v3", "team"]

def pool8(x, H8, W8):
    return x[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))

out = {}
groups = {"TRAIN": TRAIN_CROPS, "VAL": VAL_CROPS, "EVAL": EVAL_CROPS}
for g, crops in groups.items():
    for seg, crop in crops:
        d = cdir(seg, crop)
        x, y, m = load(seg, crop)
        H8, W8 = y.shape
        rec = {"n_text": int(((y == 1) & m).sum()), "n_blank": int(((y == 0) & m).sum()),
               "mask_frac": float(m.mean()), "group": g}
        for t in TAGS:
            p = os.path.join(d, f"s_bot_{t}.npy")
            if not os.path.exists(p):
                continue
            s = np.load(p).astype(np.float32)
            rec[t] = round(auc_on(pool8(s, H8, W8), y, m), 4)
            del s
        out[f"{seg}/{crop}"] = rec
        print(g, seg, crop, rec, flush=True)

json.dump(out, open(os.path.join(ROOT, "stats/explore/fb_e0_baseline.json"), "w"), indent=1)
for g in groups:
    ks = [k for k in out if out[k]["group"] == g]
    print("\n== mean", g)
    for t in TAGS:
        vs = [out[k][t] for k in ks if t in out[k]]
        if vs:
            print(f"  {t}: {np.mean(vs):.4f}  ({len(vs)} crops)")
