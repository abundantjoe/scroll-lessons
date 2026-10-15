# Provenance: Project HERCULES | owner the owner | [id removed]
"""Choose 40 patch sites (24 fit + 16 held-out) BEFORE any level-0 read, and freeze the plan.

Patch = 9 um level-0 block of 48 (z) x 256 (y) x 256 (x) voxels, centre (x, y, z).
Candidates on a grid (xy step 128, z step 48) with a 256-vox z guard. A candidate is
admissible iff
 (a) the 9 um L3 block (6 x 32 x 32 around the centre) is entirely non-zero (inside the mask),
 (b) its L3 standard deviation is >= the 50th percentile of the (a)-admissible candidates,
 (c) the block grown by 12 vox, mapped through the ORGANIZER affine, lies inside the
     2.215 um volume (level 0) and its mapped centre is non-zero at 2.215 um level 5.
40 sites are drawn by seeded farthest-point sampling (seed 20260926, z scaled x4), and split
24 / 16 by a seeded permutation. Blocks never overlap. Uses only 9 um L3 and 2.215 um L5.
"""
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import zio
REPO = "/home/user/dominion"
HZ, HY, HX = 24, 128, 128
G = 12
d = json.load(open("/work/handed/root_metadata.json"))["samples"]["PHerc0500P2"]
T = next(t for vt in d["sample"]["properties"]["volume_transforms"] if vt["from_volume_id"] == "20250820143440"
         for t in vt["transforms"] if t["to_volume_id"] == "20250526151718")
M = np.array(T["matrix"]); A, c = M[:, :3], M[:, 3]
(S9, _), (S2, _) = zio.meta("v9", 0), zio.meta("v2", 0)
sh3, _ = zio.meta("v9", 3)
cache = "/work/k4p/v9_L3.npy"
if not os.path.exists(cache):
    v3, _ = zio.read("v9", 3, 0, sh3[0], 0, sh3[1], 0, sh3[2], tag="plan_L3"); np.save(cache, v3)
v3 = np.load(cache)
sh5, _ = zio.meta("v2", 5)
v5, _ = zio.read("v2", 5, 0, sh5[0], 0, sh5[1], 0, sh5[2], tag="plan_L5")
S2xyz = np.array([S2[2], S2[1], S2[0]])
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
    corners = np.array([[a, b, e] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for e in (lo[2], hi[2])])
    q = corners @ A.T + c
    if q.min() < 0 or np.any(q.max(0) > S2xyz - 1):
        continue
    qc = A @ np.array([x, y, z]) + c
    i5 = np.round((qc - 15.5) / 32).astype(int)
    if not (0 <= i5[2] < sh5[0] and 0 <= i5[1] < sh5[1] and 0 <= i5[0] < sh5[2]) or v5[i5[2], i5[1], i5[0]] == 0:
        continue
    keep.append((x, y, z, s))
keep = np.array(keep)
rng = np.random.default_rng(20260926)
W = np.array([1, 1, 4.0])
sel = [int(rng.integers(len(keep)))]
dmin = np.linalg.norm((keep[:, :3] - keep[sel[0], :3]) * W, axis=1)
while len(sel) < 40:
    C = keep[sel, :3]
    i = int(np.argmax(dmin))
    # skip candidates whose block would overlap an already selected block
    if np.any((np.abs(C[:, 0] - keep[i, 0]) < 2 * HX) & (np.abs(C[:, 1] - keep[i, 1]) < 2 * HY) & (np.abs(C[:, 2] - keep[i, 2]) < 2 * HZ)):
        dmin[i] = -1; continue
    sel.append(i)
    dmin = np.minimum(dmin, np.linalg.norm((keep[:, :3] - keep[i, :3]) * W, axis=1))
perm = rng.permutation(40)
patches = [dict(id=f"P{r:02d}", role="fit" if perm[r] < 24 else "heldout",
                centre_xyz=[float(v) for v in keep[i, :3]], l3_std=float(keep[i, 3])) for r, i in enumerate(sel)]
plan = dict(volumes=zio.VOL, voxel_um=zio.VOXEL_UM, block_zyx=[2 * HZ, 2 * HY, 2 * HX], guard_vox=G,
            organizer_affine=M.tolist(), n_candidates_admissible_a_b=int(len(cands)), l3_std_threshold=thr,
            n_admissible=int(len(keep)), seed=20260926, patches=patches)
s = json.dumps(plan, indent=1, sort_keys=True)
os.makedirs(f"{REPO}/logs/sib/ktlb4p-prep/reg", exist_ok=True)
open(f"{REPO}/logs/sib/ktlb4p-prep/reg/patch_plan.json", "w").write(s)
print(hashlib.sha256(s.encode()).hexdigest(), len(keep))
for p in patches:
    print(p["id"], p["role"], p["centre_xyz"])
