# Provenance: Project HERCULES | owner the owner | [id removed]
"""Round trip 9 -> 2.4 -> 9 um under the frozen map (prereg_na.md): 2000 seeded points in the scroll mask
within the band plus the 56 patch centres. PASS iff max |p_rt - p| < 0.5 vox."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from field import load_final
REPO = "/home/user/dominion"
MAP, FD = load_final()
v4 = np.load("/work/reg/cache/v9_L4.npy", mmap_mode="r")
zb = json.load(open(f"{REPO}/logs/sib/reg0841/coarse_step3.json"))["step3_zband"]
rng = np.random.default_rng(20260927)
pts = []
while len(pts) < 2000:
    p = np.array([rng.uniform(0, 7702), rng.uniform(0, 7702), rng.uniform(zb["z9_at_rescan_z0"], zb["z9_at_rescan_zmax"])])
    if v4[int(p[2] // 16), int(p[1] // 16), int(p[0] // 16)] > 0:
        pts.append(p)
pts = np.array(pts)
cent = [p["centre_xyz"] for p in json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))["patches"]]
cent += [p["centre_xyz"] for p in json.load(open(f"{REPO}/logs/sib/reg0841na/new_heldout_plan.json"))["patches"]]
P = np.r_[pts, np.array(cent)]
Q = MAP.f(P)
Pr, it, step = MAP.finv(Q)
e = np.linalg.norm(Pr - P, axis=1)
u = np.linalg.norm(MAP.u(P), axis=1)
out = dict(n=len(P), max_err=float(e.max()), rms_err=float(np.sqrt((e ** 2).mean())), iterations=it, last_step=step,
           field_norm_median=float(np.median(u)), field_norm_max=float(u.max()),
           bar_roundtrip_lt_0p5="PASS" if e.max() < 0.5 else "FAIL")
json.dump(out, open(f"{REPO}/logs/sib/reg0841na/roundtrip.json", "w"), indent=1)
print(json.dumps(out, indent=1))
