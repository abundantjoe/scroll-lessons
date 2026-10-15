"""E9 (TRAINING crops only): confirm the mechanism behind B_ANI_90 -- measure the text-line
direction directly. For each angle phi, rotate the label map by -phi and take the mean over image
rows; if the text lines run at phi, that profile is strongly modulated (line bodies vs interline
gaps), so var(profile) peaks at the line direction."""
import os, sys, json, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

res = {}
for seg, crop in TRAIN_CROPS:
    y = fit_classes(seg, crop)
    x, _, m = load(seg, crop)
    lab = ((y == 1) & m).astype(np.float32)
    val = ((y != -1) & m).astype(np.float32)
    H, W = lab.shape
    D = int(np.ceil(np.hypot(H, W)))
    cx, cy = W / 2.0, H / 2.0
    v = {}
    for ang in range(0, 180, 5):
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
        M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
        rl = cv2.warpAffine(lab, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        rv = cv2.warpAffine(val, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        num = rl.sum(axis=1); den = rv.sum(axis=1)
        ok = den > 0.2 * den.max()
        if ok.sum() < 20:
            v[ang] = 0.0; continue
        p = num[ok] / den[ok]
        v[ang] = float(p.std())
    best = max(v, key=lambda a: v[a])
    res[f"{seg}/{crop}"] = {"line_dir_deg": best, "profile_std": round(v[best], 4),
                            "std_at_0": round(v[0], 4), "std_at_90": round(v[90], 4)}
    print(f"{seg}/{crop} line_dir={best} deg  std {v[best]:.4f} (0deg {v[0]:.4f}, 90deg {v[90]:.4f})", flush=True)
json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e9_linedir.json"), "w"), indent=1)
