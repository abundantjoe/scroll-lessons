"""E7 -- DECLARED BEFORE RUNNING ON THE EVALUATION CROPS (fiberbg investigation).

Measures, on the ds8 19.2 um grid, over the mask, classes from ds8_y (1 = verified text, 0 = blank):
  A  FIB-theta : papyrus-frame background subtraction. base S = mean of ds8 channels 11..14
                 (bottom face, delta = -4..-1), Spre = G_0.04mm(S); theta_crop = circular mean of
                 the structure-tensor direction (sigma_grad 1 px, sigma_tensor 16 px) over the MASK
                 (no labels used); bg = anisotropic local mean, sigma_along 3.0 mm along theta_crop,
                 sigma_across 0.12 mm; score = G_0.40mm(Spre - bg).      <-- THE HYPOTHESIS
  B  ANI-90    : identical but with the window direction fixed at 90 deg (the direction that came
                 out best on the TRAINING crops; it is the perpendicular to the text lines, i.e.
                 page layout, not fibre physics).
  C  ISO-3.0   : identical but with an isotropic 3.0 mm background.
  D  PLAIN     : G_0.40mm(Spre), no background removal at all.
Baselines on the same pixels are already measured in stats/explore/fb_e0_baseline.json
(v2 0.6378, v3 0.6294, v1b 0.6159, v0.1b 0.5552, team 0.9158 over the 7 evaluation crops).
TRAIN numbers are printed first; the EVALUATION crops are judged once and nothing is changed after.
"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

MM = 1000.0 / PITCH
CH_BOT = [11, 12, 13, 14]

def measures(seg, crop, y):
    x, _, m = load(seg, crop)
    S = x[CH_BOT].mean(axis=0)
    Spre = nconv(S, m, 0.04 * MM)
    pos = (y == 1) & m; neg = (y == 0) & m
    th, _ = structure_tensor(S, m, 1.0, 16)
    t = np.mod(th[m], np.pi)
    a = float(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))
    out = {"theta_crop_deg": round(float(np.rad2deg(a)), 1)}
    bgA = oriented_filter(Spre, m, np.full_like(Spre, a), 3.0 * MM, 0.12 * MM, n_orient=360)
    out["A_FIB_theta"] = round(auc(nconv(Spre - bgA, m, 0.40 * MM), pos, neg), 4)
    bgB = oriented_filter(Spre, m, np.full_like(Spre, np.pi / 2), 3.0 * MM, 0.12 * MM, n_orient=180)
    out["B_ANI_90"] = round(auc(nconv(Spre - bgB, m, 0.40 * MM), pos, neg), 4)
    out["C_ISO_3.0"] = round(auc(nconv(Spre - nconv(Spre, m, 3.0 * MM), m, 0.40 * MM), pos, neg), 4)
    out["D_PLAIN"] = round(auc(nconv(Spre, m, 0.40 * MM), pos, neg), 4)
    return out

res = {}
for grp, crops in (("TRAIN", TRAIN_CROPS), ("EVAL", EVAL_CROPS)):
    print(f"\n===== {grp} =====", flush=True)
    for seg, crop in crops:
        y = fit_classes(seg, crop) if grp == "TRAIN" else np.load(os.path.join(cdir(seg, crop), "ds8_y.npy"))
        r = measures(seg, crop, y); r["group"] = grp
        res[f"{seg}/{crop}"] = r
        print(f"{seg}/{crop} {json.dumps(r)}", flush=True)
    ks = [k for k in res if res[k]["group"] == grp]
    print(f"-- {grp} means: " + "  ".join(
        f"{t}={np.mean([res[k][t] for k in ks]):.4f}" for t in ("A_FIB_theta", "B_ANI_90", "C_ISO_3.0", "D_PLAIN")), flush=True)
json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e7_heldout.json"), "w"), indent=1)
