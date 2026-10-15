"""E3e: AUC as a function of the CONSTANT background-window angle, on the full-resolution TRAIN
window. Does the unsupervised structure-tensor global direction (83.3 deg) coincide with the
AUC-optimal angle? If it does, the angle can be set per crop without labels."""
import os, sys, json, numpy as np, gc
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT
import fb_e3_fullres as E3

MM = E3.MM
S, mf, m, txt, blk, Spre = E3.S, E3.mf, E3.m, E3.txt, E3.blk, E3.Spre
res = {}
for st in (12, 25, 50, 100):
    th, _ = E3.orientation(S, mf, 1.0, st)
    t = np.mod(th[m], np.pi)
    res[f"theta_st{st}_deg"] = round(float(np.rad2deg(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))), 1)
    del th; gc.collect()
# the same estimate restricted to BLANK pixels (no ink can steer it)
th, _ = E3.orientation(S, mf, 1.0, 25)
t = np.mod(th[blk], np.pi)
res["theta_st25_blankonly_deg"] = round(float(np.rad2deg(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))), 1)
del th; gc.collect()
print(res, flush=True)

sweep = {}
for ang in range(0, 180, 15):
    F = np.full(S.shape, np.deg2rad(ang), np.float32)
    bg = E3.oriented(Spre, mf, F, 3.0 * MM, 100.0, n_orient=180)  # n_orient=180 -> 1 deg bins, one used
    r = Spre - bg; del bg
    sweep[ang] = {lab: round(auc(E3.nconv(r, mf, si), txt, blk), 4)
                  for lab, si in (("0.25", 0.25 * MM), ("0.40", 0.40 * MM), ("0.60", 0.60 * MM))}
    print(ang, sweep[ang], flush=True)
    del r, F; gc.collect()
res["angle_sweep"] = sweep
json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e3e_angle.json"), "w"), indent=1)
best = max(sweep, key=lambda a: sweep[a]["0.40"])
print("best angle", best, sweep[best], " unsupervised st25 estimate", res["theta_st25_deg"])
