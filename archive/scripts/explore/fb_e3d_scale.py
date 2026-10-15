"""E3d: the existing best method (v2) band-passes at 3 mm. Compare the ANISOTROPIC background at
the same 3-4 mm scale against its isotropic twin, on the full-resolution TRAIN window."""
import os, sys, json, numpy as np, gc
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT
import fb_e3_fullres as E3

MM = E3.MM
S, mf, m, txt, blk, Spre = E3.S, E3.mf, E3.m, E3.txt, E3.blk, E3.Spre
th, _ = E3.orientation(S, mf, 1.0, 25)
t = np.mod(th[m], np.pi)
th_g = float(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))
print("global angle deg", round(np.rad2deg(th_g), 1), flush=True)
res = {"theta_global_deg": round(float(np.rad2deg(th_g)), 1)}

def add(name, r):
    for lab, si in (("0.25", 0.25 * MM), ("0.40", 0.40 * MM)):
        res[f"{name}|int{lab}"] = round(auc(E3.nconv(r, mf, si), txt, blk), 4)
    print(name, {k: v for k, v in res.items() if k.startswith(name + "|")}, flush=True)

add("plain", Spre)
for sb in (3.0, 4.0, 6.0):
    add(f"iso|bg{sb}", Spre - E3.nconv(Spre, mf, sb * MM))
const = np.full_like(th, th_g)
for sa_px, sl_mm in [(50.0, 3.0), (100.0, 3.0), (100.0, 4.0), (200.0, 4.0)]:
    bg = E3.oriented(Spre, mf, const, sl_mm * MM, sa_px)
    add(f"const|a{sa_px}px|l{sl_mm}mm", Spre - bg); del bg; gc.collect()
bg = E3.oriented(Spre, mf, const + np.pi / 2, 3.0 * MM, 100.0)
add("constperp|a100.0px|l3.0mm", Spre - bg); del bg; gc.collect()
bg = E3.oriented(Spre, mf, th, 3.0 * MM, 100.0)
add("est|a100.0px|l3.0mm", Spre - bg); del bg; gc.collect()
json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e3d_scale.json"), "w"), indent=1)
print("\ntop:")
for k, v in sorted(res.items(), key=lambda t: -t[1] if isinstance(t[1], float) else 0)[:12]:
    print(f"  {v} {k}")
