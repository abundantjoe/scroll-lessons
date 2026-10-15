# Provenance: Project HERCULES | owner the owner | [id removed]
"""Seeded rule for 16 NEW held-out patches (attempt 2), run before any non-affine analysis.
Candidates: the grid and admissibility tests (a), (b), (c) of plan_patches.py, plus: the block must not
come within 32 vox (per-axis gap) of any of the 40 earlier patch blocks. Stratification: 4 z bins
(quartiles of admissible z) x 4 radius bins (quartiles of the distance from the xy centroid of the
admissible candidates), one site per cell, drawn with numpy default_rng(20260927) in cell order; a draw
overlapping an earlier new site is redrawn in the same cell."""
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import zio
REPO = "/home/user/dominion"; OUT = f"{REPO}/logs/sib/ktlb4p-prep/reg"
HZ, HY, HX = 24, 128, 128; G = 12; GAP = 32
plan = json.load(open(f"{OUT}/patch_plan.json"))
M = np.array(plan["organizer_affine"]); A, c = M[:, :3], M[:, 3]
(S9, _), (S2, _) = zio.meta("v9", 0), zio.meta("v2", 0)
v3 = np.load("/work/k4p/v9_L3.npy")
sh5, _ = zio.meta("v2", 5)
v5, _ = zio.read("v2", 5, 0, sh5[0], 0, sh5[1], 0, sh5[2], tag="plan2_L5")
S2xyz = np.array([S2[2], S2[1], S2[0]])
old = np.array([p["centre_xyz"] for p in plan["patches"]])


def overl(a, b, gap):
    return abs(a[0] - b[0]) < 2 * HX + gap and abs(a[1] - b[1]) < 2 * HY + gap and abs(a[2] - b[2]) < 2 * HZ + gap


cands = []
for z in np.arange(256, S9[0] - 256, 48):
    for y in np.arange(256, S9[1] - 256, 128):
        for x in np.arange(256, S9[2] - 256, 128):
            zi, yi, xi = int(round((z - 3.5) / 8)), int(round((y - 3.5) / 8)), int(round((x - 3.5) / 8))
            b = v3[zi - 3:zi + 3, yi - 16:yi + 16, xi - 16:xi + 16]
            if b.size == 6 * 32 * 32 and b.min() > 0:
                cands.append((x, y, z, float(b.std())))
cands = np.array(cands)
thr = float(np.percentile(cands[:, 3], 50))
cands = cands[cands[:, 3] >= thr]
keep = []
for x, y, z, s in cands:
    lo = np.array([x - HX - G, y - HY - G, z - HZ - G]); hi = np.array([x + HX + G, y + HY + G, z + HZ + G])
    q = np.array([[a, b, e] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for e in (lo[2], hi[2])]) @ A.T + c
    if q.min() < 0 or np.any(q.max(0) > S2xyz - 1):
        continue
    qc = A @ np.array([x, y, z]) + c
    i5 = np.round((qc - 15.5) / 32).astype(int)
    if not (0 <= i5[2] < sh5[0] and 0 <= i5[1] < sh5[1] and 0 <= i5[0] < sh5[2]) or v5[i5[2], i5[1], i5[0]] == 0:
        continue
    if any(overl((x, y, z), o, GAP) for o in old):
        continue
    keep.append((x, y, z, s))
keep = np.array(keep)
cxy = keep[:, :2].mean(0)
rad = np.hypot(keep[:, 0] - cxy[0], keep[:, 1] - cxy[1])
zq = np.percentile(keep[:, 2], [25, 50, 75]); rq = np.percentile(rad, [25, 50, 75])
zbin = np.searchsorted(zq, keep[:, 2], side="right"); rbin = np.searchsorted(rq, rad, side="right")
rng = np.random.default_rng(20260927)
sel = []
for zi in range(4):
    for ri in range(4):
        idx = np.nonzero((zbin == zi) & (rbin == ri))[0]
        for _ in range(1000):
            i = int(idx[rng.integers(len(idx))])
            if not any(overl(keep[i], keep[j], 0) for j in sel):
                sel.append(i); break
patches = [dict(id=f"N{k:02d}", role="heldout2", centre_xyz=[float(v) for v in keep[i, :3]], l3_std=float(keep[i, 3]),
                zbin=int(zbin[i]), rbin=int(rbin[i])) for k, i in enumerate(sel)]
out = dict(rule=__doc__, seed=20260927, n_admissible=int(len(keep)), xy_centroid=cxy.tolist(), z_quartiles=zq.tolist(),
           r_quartiles=rq.tolist(), block_zyx=plan["block_zyx"], organizer_affine=plan["organizer_affine"], patches=patches)
s = json.dumps(out, indent=1, sort_keys=True)
open(f"{OUT}/new_heldout_plan.json", "w").write(s)
print(hashlib.sha256(s.encode()).hexdigest(), len(keep), len(patches))
