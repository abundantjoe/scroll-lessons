# Provenance: Project HERCULES | owner the owner | [id removed]
"""Coarse check of the organizer affine 20250820143440 -> 20250526151718 on
low-resolution CT only (9 um level 3 vs 2.215 um level 5, both ~75 um/px and
~71 um/px): for 8 slabs spread in z, NCC of the 9 um slab with the 2.215 um
volume resampled through the affine, compared with 7 control transforms
(affine composed with 90/180/270 deg rotations about the slab centre and
with a z flip). Numbers only. Writes logs/sib/ktlb4p-prep/reg/coarse_check.json"""
import json, os, sys
import numpy as np
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.dirname(__file__)); import zio
REPO = "/home/user/dominion"
d = json.load(open("/work/handed/root_metadata.json"))["samples"]["PHerc0500P2"]
T = next(t for vt in d["sample"]["properties"]["volume_transforms"] if vt["from_volume_id"] == "20250820143440"
         for t in vt["transforms"] if t["to_volume_id"] == "20250526151718")
M = np.array(T["matrix"]); A, c = M[:, :3], M[:, 3]
(S9, _), (S2, _) = zio.meta("v9", 0), zio.meta("v2", 0)
L9, L2 = 3, 5
f9, f2 = 2 ** L9, 2 ** L2
Z9 = S9[0]
v9_all = {}
# low-res 2.215 volume (level 5: 878 x 569 x 569) in memory
sh2, _ = zio.meta("v2", L2)
v2, i2 = zio.read("v2", L2, 0, sh2[0], 0, sh2[1], 0, sh2[2], tag="coarse_L5")
out = dict(affine=M.tolist(), det=float(np.linalg.det(A)), level9=L9, level2=L2, v2_read=i2, slabs=[])
sh9, _ = zio.meta("v9", L9)
zs = np.linspace(0.15, 0.85, 8) * sh9[0]


def ctl(kind, pc):
    """Control: pre-compose the affine with a rotation about the z axis through pc (9 um), or a z flip."""
    if kind == "identity":
        R = np.eye(3)
    elif kind.startswith("rz"):
        a = np.radians(int(kind[2:])); R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    elif kind == "flipz":
        R = np.diag([1, 1, -1.0])
    elif kind == "flipx":
        R = np.diag([-1, 1, 1.0])
    elif kind == "flipy":
        R = np.diag([1, -1, 1.0])
    Ar = A @ R
    cr = c + A @ pc - Ar @ pc
    return Ar, cr


kinds = ["identity", "rz90", "rz180", "rz270", "flipz", "flipx", "flipy"]
for zl in zs.astype(int):
    b9, _ = zio.read("v9", L9, zl - 2, zl + 3, 0, sh9[1], 0, sh9[2], tag="coarse_L3")
    s9 = b9.mean(0)
    yy, xx = np.mgrid[0:sh9[1], 0:sh9[2]]
    P = np.stack([xx.ravel() * f9 + (f9 - 1) / 2, yy.ravel() * f9 + (f9 - 1) / 2, np.full(xx.size, zl * f9 + (f9 - 1) / 2)], 1)
    m = s9.ravel() > 0
    pc = P[m].mean(0)
    row = dict(z9=float(pc[2]), n_mask=int(m.sum()))
    for k in kinds:
        Ak, ck = ctl(k, pc)
        Q = P[m] @ Ak.T + ck
        q = (Q - (f2 - 1) / 2) / f2
        v = map_coordinates(v2.astype(np.float32), np.stack([q[:, 2], q[:, 1], q[:, 0]]), order=1, cval=0)
        a_, b_ = s9.ravel()[m].astype(float), v
        a_ = a_ - a_.mean(); b_ = b_ - b_.mean()
        row[k] = float(a_ @ b_ / np.sqrt((a_ @ a_) * (b_ @ b_) + 1e-12))
        if k == "identity":
            row["frac_mapped_nonzero"] = float((v > 0).mean())
    out["slabs"].append(row)
    print(json.dumps(row), flush=True)
out["median"] = {k: float(np.median([r[k] for r in out["slabs"]])) for k in kinds}
os.makedirs(f"{REPO}/logs/sib/ktlb4p-prep/reg", exist_ok=True)
json.dump(out, open(f"{REPO}/logs/sib/ktlb4p-prep/reg/coarse_check.json", "w"), indent=1)
print(json.dumps(out["median"]))
