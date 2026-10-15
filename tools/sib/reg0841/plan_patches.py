# Provenance: Project HERCULES | owner the owner | [id removed]
"""Choose 40 patch sites (24 fit + 16 held-out) BEFORE any level-0 read, and freeze the plan.

Patch = 9 um level-0 block of 48 (z) x 256 (y) x 256 (x) voxels, centre (x, y, z).
Candidates on a grid (xy step 128, z step 48) inside the CT-verified rescan band
(coarse_step3.json: z9 12790.6 .. 16669.3) with a 60-vox guard. A candidate is admissible iff
 (a) the 9 um L3 block (6 x 32 x 32 around the centre) is entirely non-zero (inside the mask),
 (b) its L3 standard deviation is >= the 50th percentile of the admissible-(a) candidates
     (papyrus structure, not homogeneous core or large gaps),
 (c) the block grown by 6 vox is >= 144 + 12 vox (3-D) from every J point (jexcl.py),
 (d) its rescan footprint under the mesh affine lies inside the rescan volume.
Then 40 sites are drawn by seeded farthest-point sampling (seed 20260925, z scaled x4 so
sites also spread in z), and split 24 / 16 by a seeded permutation. Blocks never overlap.
"""
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from jexcl import JExcl, LIMIT, MARGIN

REPO = "/home/user/dominion"
HZ, HY, HX = 24, 128, 128
PAD = 6
v3 = np.load("/work/reg/cache/v9_L3.npy", mmap_mode="r"); Z0L3 = 1408
zb = json.load(open(f"{REPO}/logs/sib/reg0841/coarse_step3.json"))["step3_zband"]
Z_LO, Z_HI = zb["z9_at_rescan_z0"] + 60, zb["z9_at_rescan_zmax"] - 60
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]
A = np.array(mf["A"]); c = np.array(mf["c"])
S2 = np.array([30469, 30469, 15121])  # x, y, z

cands = []
for z in np.arange(np.ceil(Z_LO / 48) * 48, Z_HI, 48):
    for y in np.arange(256, 7703 - 256, 128):
        for x in np.arange(256, 7703 - 256, 128):
            zi, yi, xi = int(round((z - 3.5) / 8)) - Z0L3, int(round((y - 3.5) / 8)), int(round((x - 3.5) / 8))
            b = v3[zi - 3:zi + 3, yi - 16:yi + 16, xi - 16:xi + 16]
            if b.size and b.min() > 0:
                cands.append((x, y, z, float(b.std())))
cands = np.array(cands)
thr = np.percentile(cands[:, 3], 50)
cands = cands[cands[:, 3] >= thr]
J = JExcl()
keep = []
for x, y, z, s in cands:
    lo = np.array([x - HX - PAD, y - HY - PAD, z - HZ - PAD]); hi = np.array([x + HX + PAD, y + HY + PAD, z + HZ + PAD])
    corners = np.array([[a, b, d] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for d in (lo[2], hi[2])])
    q = corners @ A.T + c
    if q.min() < 0 or np.any(q.max(0) > S2 - 1):
        continue
    d = J.box_dist(lo, hi)
    if d >= LIMIT + MARGIN:
        keep.append((x, y, z, s, d))
keep = np.array(keep)
rng = np.random.default_rng(20260925)
W = np.array([1, 1, 4.0])
sel = [int(rng.integers(len(keep)))]
dmin = np.linalg.norm((keep[:, :3] - keep[sel[0], :3]) * W, axis=1)
while len(sel) < 40:
    i = int(np.argmax(dmin)); sel.append(i)
    dmin = np.minimum(dmin, np.linalg.norm((keep[:, :3] - keep[i, :3]) * W, axis=1))
perm = rng.permutation(40)
patches = []
for rank, i in enumerate(sel):
    x, y, z, s, d = keep[i]
    patches.append(dict(id=f"P{rank:02d}", role="fit" if perm[rank] < 24 else "heldout",
                        centre_xyz=[float(x), float(y), float(z)], l3_std=float(s),
                        j_box_dist_vox=float(d) if np.isfinite(d) else "gt_" + str(int(np.linalg.norm([HX + PAD, HY + PAD, HZ + PAD]) * 0 + LIMIT + MARGIN + 50))))
# no overlap check
C = np.array([p["centre_xyz"] for p in patches])
ov = [(i, j) for i in range(40) for j in range(i + 1, 40)
      if abs(C[i, 0] - C[j, 0]) < 2 * HX and abs(C[i, 1] - C[j, 1]) < 2 * HY and abs(C[i, 2] - C[j, 2]) < 2 * HZ]
assert not ov, ov
plan = dict(block_zyx=[2 * HZ, 2 * HY, 2 * HX], z_band_used=[Z_LO, Z_HI], n_candidates_grid=int(len(cands) * 2),
            l3_std_threshold=float(thr), n_admissible=int(len(keep)), seed=20260925,
            j_limit_vox=LIMIT, j_margin_vox=MARGIN, j_pad_vox=PAD, j_points=int(len(J.p)),
            min_j_box_dist_selected=float(min(p["j_box_dist_vox"] for p in patches if not isinstance(p["j_box_dist_vox"], str))), patches=patches)
s = json.dumps(plan, indent=1, sort_keys=True)
open(f"{REPO}/logs/sib/reg0841/patch_plan.json", "w").write(s)
print(hashlib.sha256(s.encode()).hexdigest(), len(keep), plan["min_j_box_dist_selected"])
for p in patches:
    print(p["id"], p["role"], p["centre_xyz"], p["j_box_dist_vox"])
