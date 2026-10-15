# Provenance: Project HERCULES | owner the owner | [id removed]
"""Model selection on the 24 FIT patches only (prereg_heldout.md + prereg_clarification.md).
Affine: 2 passes from the organizer affine. If the affine leave-one-out RMS (9 um vox) > 1.5,
the reg0841na Q field is fitted to the fit residuals and chosen only if its LOO RMS is lower.
Writes logs/sib/ktlb4p-prep/reg/fit_result.json and model_final.json (frozen before any
held-out block is read)."""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc
REPO = "/home/user/dominion"; BL = "/work/k4p/blocks"; OUT = f"{REPO}/logs/sib/ktlb4p-prep/reg"
plan = json.load(open(f"{OUT}/patch_plan.json"))
FIT = [p for p in plan["patches"] if p["role"] == "fit"]
S = 1000.0


def to_l1(A0, c0):
    return np.asarray(A0) / 2.0, (np.asarray(c0) - 0.5) / 2.0


def to_l0(A1, c1):
    return np.asarray(A1) * 2.0, np.asarray(c1) * 2.0 + 0.5


def quad_feats(X):
    x, y, z = (np.atleast_2d(X) / S).T
    return np.c_[x, y, z, np.ones(len(x)), x * x, x * y, y * y]


def one(args):
    pid, A0, c0 = args
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape)
    A1, c1 = to_l1(A0, c0)
    o2 = m["origin2_zyx_level1"]
    R0, ins0 = rc.sample(f2, o2, A1, c1, P, B.shape)
    r0 = rc.ncc(B, R0)
    d, info = rc.refine(B, f2, o2, A1, c1, P)
    n, pitch, aniso, flag, _ = rc.sheet_normal_pitch(B)
    rctrl = None
    if pitch:
        Rc, _ = rc.sample(f2, o2, A1, c1, P, B.shape, d=0.5 * pitch * n)
        rctrl = rc.ncc(B, Rc)
    pc = np.array(m["origin9_zyx"][::-1], float) + (np.array(B.shape[::-1]) - 1) / 2
    q0 = np.asarray(A0) @ (pc + d) + np.asarray(c0)  # measured correspondence, level-0 rescan vox
    return dict(id=pid, ncc_zero_shift=r0, inside_frac_zero=ins0, d9=d.tolist(), p=pc.tolist(), q=q0.tolist(),
                pitch9=pitch, pitch_flag=flag, aniso=aniso, r_ctrl=rctrl, zero_frac9=m["zero_frac9"], **info)


def fit_aff(P, Q):
    return rc.fit_affine(P, Q)


def loo_aff(P, Q):
    e = []
    for i in range(len(P)):
        k = np.arange(len(P)) != i
        A, c = fit_aff(P[k], Q[k])
        e.append(np.linalg.solve(A, Q[i] - (A @ P[i] + c)))
    return np.array(e)


def main():
    A, c = np.array(plan["organizer_affine"])[:, :3], np.array(plan["organizer_affine"])[:, 3]
    out = {"passes": [], "sigma2_prefilter_level1": rc.SIGMA2}
    for ps in range(2):
        t = time.time()
        with Pool(2) as pool:
            rows = pool.map(one, [(p["id"], A.tolist(), c.tolist()) for p in FIT])
        P = np.array([r["p"] for r in rows]); Q = np.array([r["q"] for r in rows])
        An, cn = fit_aff(P, Q)
        res9 = np.linalg.solve(An, (Q - (P @ An.T + cn)).T).T
        loo = loo_aff(P, Q)
        dmap = np.linalg.solve(An, ((P @ An.T + cn) - (P @ A.T + c)).T).T
        s = dict(A=An.tolist(), c=cn.tolist(), det=float(np.linalg.det(An)),
                 rms_resid9=float(np.sqrt((np.linalg.norm(res9, axis=1) ** 2).mean())),
                 loo_rms9=float(np.sqrt((np.linalg.norm(loo, axis=1) ** 2).mean())),
                 loo_max9=float(np.linalg.norm(loo, axis=1).max()),
                 map_change_vs_input_rms9=float(np.sqrt((np.linalg.norm(dmap, axis=1) ** 2).mean())),
                 median_r_zero_shift_input=float(np.median([r["ncc_zero_shift"] for r in rows])),
                 median_r_after_local_shift=float(np.median([r["ncc_after_shift"] for r in rows])))
        out["passes"].append(dict(rows=rows, fit=s, seconds=round(time.time() - t, 1)))
        print(f"pass {ps}:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k not in ('A', 'c')}, flush=True)
        A, c = An, cn
    rows = out["passes"][-1]["rows"]
    P = np.array([r["p"] for r in rows]); Q = np.array([r["q"] for r in rows])
    U = np.linalg.solve(A, (Q - c - P @ A.T).T).T
    aff_loo = out["passes"][-1]["fit"]["loo_rms9"]
    sel = dict(affine_loo_rms9=aff_loo, rule="affine if LOO <= 1.5; else Q field if its LOO < affine LOO")
    model = dict(kind="affine", A=A.tolist(), c=c.tolist(), form="q2 = A p9 + c, level-0 voxels (x, y, z)",
                 voxel_um=plan["voxel_um"], F0=9.362 / 2.215)
    if aff_loo > 1.5:
        e = []
        for i in range(len(P)):
            k = np.arange(len(P)) != i
            W = np.linalg.lstsq(quad_feats(P[k]), U[k], rcond=None)[0]
            e.append(U[i] - quad_feats(P[i]) @ W)
        e = np.array(e).reshape(len(P), 3)
        q_loo = float(np.sqrt((np.linalg.norm(e, axis=1) ** 2).mean()))
        sel["q_field_loo_rms9"] = q_loo
        if q_loo < aff_loo:
            W = np.linalg.lstsq(quad_feats(P), U, rcond=None)[0]
            model = dict(kind="affine+Q", A=A.tolist(), c=c.tolist(), W=W.tolist(), feats="x,y,z,1,x^2,xy,y^2 of p/1000",
                         form="q2 = A (p9 + u(p9)) + c, u = feats(p9) @ W, level-0 voxels (x, y, z)",
                         voxel_um=plan["voxel_um"], F0=9.362 / 2.215)
    sel["chosen"] = model["kind"]
    out["selection"] = sel
    json.dump(out, open(f"{OUT}/fit_result.json", "w"), indent=1)
    json.dump(model, open(f"{OUT}/model_final.json", "w"), indent=1)
    print("SELECTION", json.dumps(sel))


if __name__ == "__main__":
    main()
