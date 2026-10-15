# Provenance: Project HERCULES | owner the owner | [id removed]
"""Step 4: phase-correlate the 24 fit patches and fit the affine (2 passes).
Pass 1 uses the mesh affine (mesh_fit.json joint); pass 2 re-runs every patch under the pass-1
affine and refits. Writes logs/sib/reg0841/fit_result.json and affine_final.json.
Only role == "fit" patches are read."""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc
REPO = "/home/user/dominion"; BL = "/work/reg/blocks"
plan = json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))
FIT = [p for p in plan["patches"] if p["role"] == "fit"]


def one(args):
    pid, A, c = args
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape)
    A = np.array(A); c = np.array(c)
    R0, ins0 = rc.sample(f2, m["origin2_zyx"], A, c, P, B.shape)
    r0 = rc.ncc(B, R0)
    d, info = rc.refine(B, f2, m["origin2_zyx"], A, c, P)
    pc = np.array(m["origin9_zyx"][::-1], float) + (np.array(B.shape[::-1]) - 1) / 2  # block centre (x, y, z)
    q = A @ (pc + d) + c
    return dict(id=pid, ncc_zero_shift=r0, inside_frac_zero=ins0, d9=d.tolist(), p=pc.tolist(), q=q.tolist(), **info)


def fit(rows):
    P = np.array([r["p"] for r in rows]); Q = np.array([r["q"] for r in rows])
    A, c = rc.fit_affine(P, Q)
    res = Q - (P @ A.T + c)
    loo = []
    for i in range(len(P)):
        k = np.arange(len(P)) != i
        Ai, ci = rc.fit_affine(P[k], Q[k]); loo.append((Q[i] - (Ai @ P[i] + ci)).tolist())
    return A, c, res, np.array(loo)


def summarize(A, c, res, loo, rows):
    Ainv = np.linalg.inv(A)
    r9 = res @ Ainv.T; l9 = loo @ Ainv.T
    n2 = np.linalg.norm(res, axis=1); n9 = np.linalg.norm(r9, axis=1)
    return dict(A=A.tolist(), c=c.tolist(), det=float(np.linalg.det(A)),
                resid2=res.tolist(), resid9=r9.tolist(),
                rms_resid2=float(np.sqrt((n2 ** 2).mean())), rms_resid9=float(np.sqrt((n9 ** 2).mean())),
                max_resid9=float(n9.max()),
                loo_rms2=float(np.sqrt((np.linalg.norm(loo, axis=1) ** 2).mean())),
                loo_rms9=float(np.sqrt((np.linalg.norm(l9, axis=1) ** 2).mean())),
                loo_max9=float(np.linalg.norm(l9, axis=1).max()))


def main():
    mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]
    A0, c0 = np.array(mf["A"]), np.array(mf["c"])
    out = {"sigma2_prefilter": rc.SIGMA2, "F": rc.F, "passes": []}
    A, c = A0, c0
    for ps in range(2):
        t = time.time()
        with Pool(2) as pool:
            rows = pool.map(one, [(p["id"], A.tolist(), c.tolist()) for p in FIT])
        An, cn, res, loo = fit(rows)
        s = summarize(An, cn, res, loo, rows)
        # change of the mapping between input and output affine at the patch centres (9 um vox)
        P = np.array([r["p"] for r in rows])
        dmap = (P @ An.T + cn) - (P @ A.T + c)
        s["map_change_vs_input_rms9"] = float(np.sqrt(((dmap @ np.linalg.inv(An).T) ** 2).sum(1).mean()))
        out["passes"].append(dict(input_A=A.tolist(), input_c=c.tolist(), rows=rows, fit=s, seconds=time.time() - t))
        print(f"pass {ps}: rms9 {s['rms_resid9']:.3f} loo9 {s['loo_rms9']:.3f} change {s['map_change_vs_input_rms9']:.3f}",
              "ncc0", np.round([r["ncc_zero_shift"] for r in rows], 3).tolist(),
              "|d|", np.round([np.linalg.norm(r["d9"]) for r in rows], 2).tolist(), flush=True)
        A, c = An, cn
    json.dump(out, open(f"{REPO}/logs/sib/reg0841/fit_result.json", "w"), indent=1)
    F = rc.F
    fitP = np.array([r["p"] for r in out["passes"][-1]["rows"]]); Pm = fitP.mean(0)
    # z0: 9 um z that maps to rescan z = 0 at the mean fit xy: solve (A p + c)_z = 0 for p_z
    z0 = float(-(c[2] + A[2, 0] * Pm[0] + A[2, 1] * Pm[1]) / A[2, 2])
    M = A / F - np.eye(3)
    b = M @ Pm + c / F + np.array([0, 0, z0])  # t(p) = M (p - Pm) + b
    aff = dict(form="q2 = A p9 + c (level-0 voxels, (x, y, z)); equivalently q2 = F (p9 + t(p9) - z0 e_z), t = M (p9 - Pm) + b",
               F=F, voxel_um={"v9": 9.366, "v2": 2.403}, A=A.tolist(), c=c.tolist(), M=M.tolist(), b=b.tolist(),
               Pm=Pm.tolist(), z0=z0, n_fit=len(fitP), prefilter_sigma2=rc.SIGMA2)
    json.dump(aff, open(f"{REPO}/logs/sib/reg0841/affine_final.json", "w"), indent=1)
    print(json.dumps(aff, indent=1))


if __name__ == "__main__":
    main()
