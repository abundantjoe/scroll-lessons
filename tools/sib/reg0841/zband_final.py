# Provenance: Project HERCULES | owner the owner | [id removed]
"""Rescan z-band in the 9 um frame under the final affine (and the mesh affine, and M1 for
information), over the scroll cross-section (9 um L4 mask > 0 in the band), plus the
displacement between final and mesh affines at the 40 patch centres and over the band."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import model_loo
REPO = "/home/user/dominion"
aff = json.load(open(f"{REPO}/logs/sib/reg0841/affine_final.json")); A = np.array(aff["A"]); c = np.array(aff["c"])
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]; A0 = np.array(mf["A"]); c0 = np.array(mf["c"])
v4 = np.load("/work/reg/cache/v9_L4.npy", mmap_mode="r")
zl = np.arange(int(12790 / 16), int(16670 / 16))
m = (np.asarray(v4[zl]) > 0).any(0)
yy, xx = np.nonzero(m); xy = np.c_[xx * 16 + 7.5, yy * 16 + 7.5]
out = {"n_xy_cols": int(len(xy)), "xy_extent_9um": [xy.min(0).tolist(), xy.max(0).tolist()]}


def zfor(A, c, z2):
    # solve (A p + c)_z = z2 for p_z at each (x, y)
    return (z2 - c[2] - A[2, 0] * xy[:, 0] - A[2, 1] * xy[:, 1]) / A[2, 2]


for name, (AA, cc) in {"final_affine": (A, c), "mesh_affine": (A0, c0)}.items():
    lo = zfor(AA, cc, 0.0); hi = zfor(AA, cc, 15120.0)
    out[name] = dict(z9_at_rescan_z0=[float(lo.min()), float(np.median(lo)), float(lo.max())],
                     z9_at_rescan_z15120=[float(hi.min()), float(np.median(hi)), float(hi.max())])
f1 = model_loo.model_fn("M1")
P = np.c_[xy, np.full(len(xy), 12790.0)]
out["M1_z_offset_vs_affine_at_z12790_9umvox"] = [float(v) for v in np.percentile(
    np.linalg.solve(A, (f1(P) - (P @ A.T + c)).T)[2], [0, 50, 100])]
plan = json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))
C = np.array([p["centre_xyz"] for p in plan["patches"]])
dd = np.linalg.solve(A, ((C @ A.T + c) - (C @ A0.T + c0)).T).T
out["final_minus_mesh_at_patch_centres_9umvox"] = dict(rms=float(np.sqrt((dd ** 2).sum(1).mean())),
                                                     max=float(np.linalg.norm(dd, axis=1).max()),
                                                     mean_xyz=dd.mean(0).tolist())
print(json.dumps(out, indent=1))
json.dump(out, open(f"{REPO}/logs/sib/reg0841/zband_final.json", "w"), indent=1)
