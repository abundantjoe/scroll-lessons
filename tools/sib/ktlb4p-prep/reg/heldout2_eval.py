# Provenance: Project HERCULES | owner the owner | [id removed]
"""Attempt 2: fetch the 16 NEW blocks (new_heldout_plan.json) and evaluate the frozen field map ONCE
(prereg_attempt2.md). r = NCC at zero shift under f(p) = A (p + u(p)) + c; residual = converged
phase-correlation shift on top of f. Writes heldout2_result.json."""
import hashlib, json, os, sys
from multiprocessing import Pool
import numpy as np
from scipy.interpolate import RBFInterpolator
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc, zio
from fit_model import to_l1
REPO = "/home/user/dominion"; OUT = f"{REPO}/logs/sib/ktlb4p-prep/reg"; BL = "/work/k4p/blocks2"
os.makedirs(BL, exist_ok=True)
assert os.path.exists(f"{OUT}/field_final.json")
mod = json.load(open(f"{OUT}/model_final.json")); A0 = np.array(mod["A"]); c0 = np.array(mod["c"])
fld = json.load(open(f"{OUT}/field_final.json"))
FP, FU = np.array(fld["points_p9"]), np.array(fld["displacements_u9"])
if fld["kind"] == "Q":
    W = np.array(fld["W"])
    def u_of(X):
        x, y, z = (X / 1000.0).T
        return np.c_[x, y, z, np.ones(len(x)), x * x, x * y, y * y] @ W
else:
    R = RBFInterpolator(FP / 1000.0, FU, kernel=fld["kind"], degree=1, smoothing=fld["smoothing"])
    def u_of(X):
        return np.concatenate([R(X[i:i + 400000] / 1000.0) for i in range(0, len(X), 400000)])
plan = json.load(open(f"{OUT}/new_heldout_plan.json"))
G9, G1 = 12, 6


def fetch(p):
    if os.path.exists(f"{BL}/{p['id']}.json"):
        return
    x, y, z = [int(v) for v in p["centre_xyz"]]
    hz, hy, hx = [s // 2 for s in plan["block_zyx"]]
    o9 = [z - hz, y - hy, x - hx]
    b9, i9 = zio.read("v9", 0, o9[0], o9[0] + 2 * hz, o9[1], o9[1] + 2 * hy, o9[2], o9[2] + 2 * hx, tag=p["id"])
    lo = np.array([x - hx - G9, y - hy - G9, z - hz - G9], float); hi = np.array([x + hx + G9, y + hy + G9, z + hz + G9], float)
    cr = np.array([[a, b, e] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for e in (lo[2], hi[2])])
    cr = (cr + u_of(cr)) @ A0.T + c0
    q1lo = np.floor((cr.min(0) - 0.5) / 2).astype(int) - G1; q1hi = np.ceil((cr.max(0) - 0.5) / 2).astype(int) + G1
    o2 = [int(q1lo[2]), int(q1lo[1]), int(q1lo[0])]
    b2, i2 = zio.read("v2", 1, o2[0], int(q1hi[2]), o2[1], int(q1hi[1]), o2[2], int(q1hi[0]), tag=p["id"])
    np.save(f"{BL}/{p['id']}_v9.npy", b9); np.save(f"{BL}/{p['id']}_v2.npy", b2)
    json.dump(dict(id=p["id"], origin9_zyx=o9, origin2_zyx_level1=o2, v9=i9, v2=i2, zero_frac9=float((b9 == 0).mean())),
              open(f"{BL}/{p['id']}.json", "w"), indent=1)


def one(pid):
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape)
    U = u_of(P)
    A1, c1 = to_l1(A0, c0); o2 = m["origin2_zyx_level1"]
    R0, ins = rc.sample(f2, o2, A1, c1, P, B.shape, d=U)
    r = rc.ncc(B, R0)
    s_tot = np.zeros(3)
    for _ in range(8):
        Rk, _ = rc.sample(f2, o2, A1, c1, P, B.shape, d=U + s_tot)
        s, pk = rc.phase_corr(B, Rk); s_tot += s
        if np.linalg.norm(s) < 0.02:
            break
    Rk, _ = rc.sample(f2, o2, A1, c1, P, B.shape, d=U + s_tot)
    n, pitch, aniso, flag, _ = rc.sheet_normal_pitch(B)
    rctrl = None
    if pitch:
        Rc, _ = rc.sample(f2, o2, A1, c1, P, B.shape, d=U + 0.5 * pitch * n)
        rctrl = rc.ncc(B, Rc)
    return dict(id=pid, r=r, inside_frac=ins, d9=s_tot.tolist(), abs_d9=float(np.linalg.norm(s_tot)), pitch9=pitch,
                r_ctrl=rctrl, ncc_after_local_shift=rc.ncc(B, Rk), u_centre=U[len(U) // 2].tolist(), zero_frac9=m["zero_frac9"])


if __name__ == "__main__":
    for p in plan["patches"]:
        fetch(p)
        print("fetched", p["id"], flush=True)
    with Pool(2) as pool:
        rows = pool.map(one, [p["id"] for p in plan["patches"]])
    r = np.array([x["r"] for x in rows]); dd = np.array([x["abs_d9"] for x in rows])
    drop = np.array([x["r"] - x["r_ctrl"] if x["r_ctrl"] is not None else np.nan for x in rows])
    res = dict(model_sha256=hashlib.sha256(open(f"{OUT}/model_final.json", "rb").read()).hexdigest(),
               field_sha256=hashlib.sha256(open(f"{OUT}/field_final.json", "rb").read()).hexdigest(), rows=rows,
               median_r=float(np.median(r)), min_r=float(r.min()), rms_abs_d9=float(np.sqrt((dd ** 2).mean())), max_abs_d9=float(dd.max()),
               ctrl_median_drop=float(np.nanmedian(drop)), ctrl_n_clear=int(np.nansum(drop > 0.15)),
               median_r_after_local_shift=float(np.median([x["ncc_after_local_shift"] for x in rows])))
    res["bars"] = dict(median_r_ge_085=res["median_r"] >= 0.85, rms_le_15=res["rms_abs_d9"] <= 1.5,
                       control=res["ctrl_median_drop"] >= 0.30 and res["ctrl_n_clear"] >= 14)
    res["verdict"] = "PASS" if all(res["bars"].values()) else "FAIL"
    json.dump(res, open(f"{OUT}/heldout2_result.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
