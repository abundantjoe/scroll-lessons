# Provenance: Project HERCULES | owner the owner | [id removed]
"""Seeded rule for 16 NEW held-out patches (reg0841-NA), run before any non-affine analysis.
Candidates: the same grid and admissibility tests (a, b, d) as tools/sib/reg0841/plan_patches.py
(9 um L3 mask/structure inside the CT-verified band, rescan footprint inside the volume), plus:
 - the block must not come within 32 vox (per axis gap) of any of the 40 earlier patch blocks;
 - fail-closed point-to-surface J clearance of the block grown by 6 vox >= 144 + 12 vox (jsurf.py).
Stratification: 4 z bins (quartiles of admissible candidate z) x 4 radius bins (quartiles of the distance
from the reconstruction axis x = y = 3851.25), one site per cell, drawn uniformly at random with
numpy default_rng(20260926) in cell order (z bin, radius bin); a draw that overlaps an earlier new site
(or fails J clearance) is redrawn in the same cell."""
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from jsurf import JSurf

REPO = "/home/user/dominion"
HZ, HY, HX = 24, 128, 128; PAD = 6; GAP = 32; AX = 3851.25
v3 = np.load("/work/reg/cache/v9_L3.npy", mmap_mode="r"); Z0L3 = 1408
zb = json.load(open(f"{REPO}/logs/sib/reg0841/coarse_step3.json"))["step3_zband"]
Z_LO, Z_HI = zb["z9_at_rescan_z0"] + 60, zb["z9_at_rescan_zmax"] - 60
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]; A = np.array(mf["A"]); c = np.array(mf["c"])
S2 = np.array([30469, 30469, 15121])
old = np.array([p["centre_xyz"] for p in json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))["patches"]])


def overl(a, b, gap):
    return abs(a[0] - b[0]) < 2 * HX + gap and abs(a[1] - b[1]) < 2 * HY + gap and abs(a[2] - b[2]) < 2 * HZ + gap


cands = []
for z in np.arange(np.ceil(Z_LO / 48) * 48, Z_HI, 48):
    for y in np.arange(256, 7703 - 256, 128):
        for x in np.arange(256, 7703 - 256, 128):
            zi, yi, xi = int(round((z - 3.5) / 8)) - Z0L3, int(round((y - 3.5) / 8)), int(round((x - 3.5) / 8))
            b = v3[zi - 3:zi + 3, yi - 16:yi + 16, xi - 16:xi + 16]
            if b.size and b.min() > 0:
                cands.append((x, y, z, float(b.std())))
cands = np.array(cands)
thr = np.percentile(cands[:, 3], 50)  # same rule as plan_patches.py
cands = cands[cands[:, 3] >= thr]
keep = []
for x, y, z, s in cands:
    lo = np.array([x - HX - PAD, y - HY - PAD, z - HZ - PAD]); hi = np.array([x + HX + PAD, y + HY + PAD, z + HZ + PAD])
    q = np.array([[a, b, d] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for d in (lo[2], hi[2])]) @ A.T + c
    if q.min() < 0 or np.any(q.max(0) > S2 - 1):
        continue
    if any(overl((x, y, z), o, GAP) for o in old):
        continue
    keep.append((x, y, z, s))
keep = np.array(keep)
rad = np.hypot(keep[:, 0] - AX, keep[:, 1] - AX)
zq = np.percentile(keep[:, 2], [25, 50, 75]); rq = np.percentile(rad, [25, 50, 75])
zbin = np.searchsorted(zq, keep[:, 2], side="right"); rbin = np.searchsorted(rq, rad, side="right")
J = JSurf()
rng = np.random.default_rng(20260926)
sel = []; log = []
for zi in range(4):
    for ri in range(4):
        idx = np.nonzero((zbin == zi) & (rbin == ri))[0]
        tries = 0
        while True:
            tries += 1
            i = int(rng.choice(idx)); x, y, z, s = keep[i]
            if any(overl((x, y, z), keep[j][:3], GAP) for j in sel):
                continue
            cl = J.box_clearance([x - HX - PAD, y - HY - PAD, z - HZ - PAD], [x + HX + PAD, y + HY + PAD, z + HZ + PAD])
            if cl < 144 + 12:
                log.append(dict(cell=[zi, ri], rejected=[float(x), float(y), float(z)], clearance=cl)); continue
            sel.append(i); log.append(dict(cell=[zi, ri], n_cell=int(len(idx)), tries=tries, clearance=cl)); break
patches = [dict(id=f"N{k:02d}", role="heldout_new", cell=[int(zbin[i]), int(rbin[i])], centre_xyz=keep[i][:3].tolist(),
                radius9=float(rad[i]), l3_std=float(keep[i][3]), j_clearance_vox=log_i["clearance"])
           for k, (i, log_i) in enumerate(zip(sel, [l for l in log if "tries" in l]))]
plan = dict(block_zyx=[48, 256, 256], seed=20260926, z_quartiles=zq.tolist(), radius_quartiles=rq.tolist(), axis_xy=AX,
            gap_to_old_blocks_vox=GAP, n_admissible=int(len(keep)), j_rule="fail-closed point-to-surface >= 156 (144 + 12) on block grown by 6",
            n_triangles=int(len(J.T)), sampling_gap_vox=J.gap, draw_log=log, patches=patches)
s = json.dumps(plan, indent=1, sort_keys=True)
open(f"{REPO}/logs/sib/reg0841na/new_heldout_plan.json", "w").write(s)
print(hashlib.sha256(s.encode()).hexdigest(), len(keep))
for p in patches:
    print(p["id"], p["cell"], p["centre_xyz"], round(p["radius9"]), round(p["j_clearance_vox"], 1))
