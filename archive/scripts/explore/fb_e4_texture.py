"""E4 (ds8 grid, TRAINING crops): fibre-frame features that are INVARIANT to fibre brightness
rather than subtractive -- local contrast / coefficient of variation measured in the fibre frame,
and the across-fibre vs along-fibre roughness ratio (physical prediction: ink fills the inter-fibre
grooves, so inked papyrus should be smoother ACROSS the fibres)."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

MM = 1000.0 / PITCH
CH_BOT = [11, 12, 13, 14]
SIG_PRE = 0.04 * MM
ST = 16                       # structure-tensor sigma: 307 um (the scale at which the field is physical)
INT = 0.25 * MM
EPS = 0.3

rows = {}
for seg, crop in TRAIN_CROPS:
    x, _, m = load(seg, crop)
    y = fit_classes(seg, crop)
    S = x[CH_BOT].mean(axis=0)
    Spre = nconv(S, m, SIG_PRE)
    pos = (y == 1) & m; neg = (y == 0) & m
    th, coh = structure_tensor(S, m, 1.0, ST)
    rec = {}
    def add(n, f):
        rec[n] = round(auc(nconv(f, m, INT), pos, neg), 4)

    # local std in the fibre frame
    combos = {"acr": (0.05, 0.30), "alo": (0.30, 0.05), "iso": (0.15, 0.15),
              "acr2": (0.05, 0.60), "alo2": (0.60, 0.05), "iso2": (0.25, 0.25)}
    sd = {}
    for k, (sl, sa) in combos.items():
        sd[k] = oriented_filter(Spre, m, th, sl * MM, sa * MM, mode="std")
        add(f"std_{k}", sd[k])
    add("std_ratio_acr_over_alo", sd["acr"] / np.maximum(sd["alo"], 1e-3))
    add("std_ratio_acr_over_alo2", sd["acr2"] / np.maximum(sd["alo2"], 1e-3))
    add("coherence", coh)
    # coefficient of variation: local std / local mean level (mean taken on a 1 mm oriented window,
    # shifted to a positive scale because the channels are MAD-standardised around 0)
    lvl = oriented_filter(Spre, m, th, 1.0 * MM, 0.05 * MM) + 6.0
    add("cv_acr", sd["acr"] / np.maximum(lvl, 0.5))
    add("cv_iso", sd["iso"] / np.maximum(lvl, 0.5))
    # multiplicative fibre-brightness normalisation: S / (along-fibre level)
    for sl in (0.3, 0.6, 1.2, 2.4):
        bg = oriented_filter(Spre, m, th, sl * MM, 0.05 * MM) + 6.0
        add(f"ratio_l{sl}", (Spre + 6.0) / np.maximum(bg, 0.5))
        bgi = nconv(Spre, m, sl * MM) + 6.0
        add(f"ratio_iso{sl}", (Spre + 6.0) / np.maximum(bgi, 0.5))
    # reference on the same pixels
    add("plain", Spre)
    rows[f"{seg}/{crop}"] = rec
    print(seg, crop, json.dumps(rec), flush=True)

json.dump(rows, open(os.path.join(ROOT, "stats/explore/fb_e4_texture.json"), "w"), indent=1)
keys = list(next(iter(rows.values())).keys())
mean = {k: float(np.mean([rows[c][k] for c in rows])) for k in keys}
print("\n== TRAIN mean over %d crops (AUC; <0.5 means the feature is anti-correlated with ink)" % len(rows))
for k, v in sorted(mean.items(), key=lambda t: -abs(t[1] - 0.5)):
    print(f"  {v:.4f}  {k}")
