# Provenance: Project HERCULES | owner the owner | [id removed]
"""Step 5: evaluate the frozen affine (affine_final.json) on patches of the given role, exactly as
pre-registered in logs/sib/reg0841/prereg_heldout.md. Usage: heldout_run.py heldout|fit OUT.json"""
import json, os, sys
from multiprocessing import Pool
import numpy as np
from scipy.ndimage import gaussian_filter
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc
import model_loo
REPO = "/home/user/dominion"; BL = "/work/reg/blocks"
aff = json.load(open(f"{REPO}/logs/sib/reg0841/affine_final.json"))
A = np.array(aff["A"]); c = np.array(aff["c"])
plan = json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))
ROLE = sys.argv[1]
IDS = [p["id"] for p in plan["patches"] if p["role"] == ROLE]
MODELS = {m: model_loo.model_fn(m) for m in ("M1", "M3")}  # secondary, prereg addendum 1


def local_affine(f, pc, h=50.0):
    J = np.zeros((3, 3))
    for k in range(3):
        e = np.zeros(3); e[k] = h
        J[:, k] = (f(pc + e)[0] - f(pc - e)[0]) / (2 * h)
    return J, f(pc)[0] - J @ pc


def one(pid):
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape); o2 = m["origin2_zyx"]
    R, ins = rc.sample(f2, o2, A, c, P, B.shape)
    r = rc.ncc(B, R)
    d, info = rc.refine(B, f2, o2, A, c, P); info.pop("hist")
    n, pitch, aniso, flag, ac = rc.sheet_normal_pitch(B)
    Bl = gaussian_filter(B, 1.0); r_lp = rc.ncc(Bl, gaussian_filter(R, 1.0))
    pc = np.array(m["origin9_zyx"][::-1], float) + (np.array(B.shape[::-1]) - 1) / 2
    q_meas = A @ (pc + d) + c
    sec = {}
    for name, f in MODELS.items():
        Jm, cm = local_affine(f, pc)
        Rm, _ = rc.sample(f2, o2, Jm, cm, P, B.shape)
        sec[name] = dict(r=rc.ncc(B, Rm), r_lp=rc.ncc(Bl, gaussian_filter(Rm, 1.0)),
                         resid9=float(np.linalg.norm(np.linalg.solve(A, q_meas - f(pc)[0]))))
    ctrl = {}
    for sgn in (+1, -1):
        Rc, insc = rc.sample(f2, o2, A, c, P, B.shape, sgn * 0.5 * pitch * n)
        ctrl[sgn] = (rc.ncc(B, Rc), rc.ncc(Bl, gaussian_filter(Rc, 1.0)), insc)
    r_ctrl = max(ctrl[1][0], ctrl[-1][0]); r_ctrl_lp = max(ctrl[1][1], ctrl[-1][1])
    return dict(id=pid, r=r, inside_frac=ins, d9=d.tolist(), resid9=float(np.linalg.norm(d)),
                resid2=float(np.linalg.norm(A @ d)), normal_xyz=n.tolist(), pitch9=pitch, normal_aniso=aniso,
                pitch_flag=flag, r_ctrl_plus=ctrl[1][0], r_ctrl_minus=ctrl[-1][0], r_ctrl=r_ctrl,
                drop=r - r_ctrl, r_lp=r_lp, r_ctrl_lp=r_ctrl_lp, drop_lp=r_lp - r_ctrl_lp,
                ctrl_inside=[ctrl[1][2], ctrl[-1][2]], p=pc.tolist(), q_meas=q_meas.tolist(), secondary=sec, **{f"refine_{k}": v for k, v in info.items()})


def main():
    with Pool(2) as pool:
        rows = pool.map(one, IDS)
    r = np.array([x["r"] for x in rows]); e9 = np.array([x["resid9"] for x in rows]); e2 = np.array([x["resid2"] for x in rows])
    drop = np.array([x["drop"] for x in rows])
    s = dict(role=ROLE, n=len(rows), median_r=float(np.median(r)), min_r=float(r.min()),
             rms_resid9=float(np.sqrt((e9 ** 2).mean())), rms_resid2=float(np.sqrt((e2 ** 2).mean())),
             max_resid9=float(e9.max()), median_drop=float(np.median(drop)),
             n_ctrl_clear=int(sum(x["r_ctrl"] < x["r"] - 0.15 for x in rows)),
             median_r_lp=float(np.median([x["r_lp"] for x in rows])),
             median_drop_lp=float(np.median([x["drop_lp"] for x in rows])),
             median_pitch9=float(np.median([x["pitch9"] for x in rows if x["pitch9"] is not None])))
    for name in MODELS:
        s[f"secondary_{name}"] = dict(median_r=float(np.median([x["secondary"][name]["r"] for x in rows])),
                                      median_r_lp=float(np.median([x["secondary"][name]["r_lp"] for x in rows])),
                                      rms_resid9=float(np.sqrt(np.mean([x["secondary"][name]["resid9"] ** 2 for x in rows]))))
    s["bar_median_r_ge_0.85"] = "PASS" if s["median_r"] >= 0.85 else "FAIL"
    s["bar_rms_le_1.5_9umvox"] = "PASS" if s["rms_resid9"] <= 1.5 else "FAIL"
    s["bar_rms_le_1.5_rescanvox"] = "PASS" if s["rms_resid2"] <= 1.5 else "FAIL"
    s["bar_control_clear_drop"] = "PASS" if (s["median_drop"] >= 0.30 and s["n_ctrl_clear"] >= 14 * len(rows) / 16) else "FAIL"
    out = dict(affine_sha256=__import__("hashlib").sha256(open(f"{REPO}/logs/sib/reg0841/affine_final.json", "rb").read()).hexdigest(),
               prereg_sha256=__import__("hashlib").sha256(open(f"{REPO}/logs/sib/reg0841/prereg_heldout.md", "rb").read()).hexdigest(),
               summary=s, rows=rows)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(json.dumps(s, indent=1))
    for x in rows:
        print(x["id"], round(x["r"], 3), round(x["resid9"], 2), x["pitch9"], round(x["r_ctrl"], 3), round(x["r_lp"], 3), x["pitch_flag"])


if __name__ == "__main__":
    main()
