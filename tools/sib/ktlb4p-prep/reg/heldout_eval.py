# Provenance: Project HERCULES | owner the owner | [id removed]
"""ONE evaluation of the frozen model (model_final.json) on the 16 pre-registered held-out
patches (prereg_heldout.md). Writes logs/sib/ktlb4p-prep/reg/heldout_result.json."""
import hashlib, json, os, sys
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc
from fit_model import to_l1
REPO = "/home/user/dominion"; BL = "/work/k4p/blocks"; OUT = f"{REPO}/logs/sib/ktlb4p-prep/reg"
plan = json.load(open(f"{OUT}/patch_plan.json"))
model = json.load(open(f"{OUT}/model_final.json"))
assert model["kind"] == "affine"
A0, c0 = np.array(model["A"]), np.array(model["c"])
HO = [p for p in plan["patches"] if p["role"] == "heldout"]


def one(pid):
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape)
    A1, c1 = to_l1(A0, c0)
    o2 = m["origin2_zyx_level1"]
    R0, ins = rc.sample(f2, o2, A1, c1, P, B.shape)
    r = rc.ncc(B, R0)
    d, info = rc.refine(B, f2, o2, A1, c1, P)
    n, pitch, aniso, flag, _ = rc.sheet_normal_pitch(B)
    rctrl = None
    if pitch:
        Rc, _ = rc.sample(f2, o2, A1, c1, P, B.shape, d=0.5 * pitch * n)
        rctrl = rc.ncc(B, Rc)
    return dict(id=pid, r=r, inside_frac=ins, d9=d.tolist(), abs_d9=float(np.linalg.norm(d)), pitch9=pitch,
                pitch_flag=flag, r_ctrl=rctrl, ncc_after_local_shift=info["ncc_after_shift"], zero_frac9=m["zero_frac9"])


if __name__ == "__main__":
    with Pool(2) as pool:
        rows = pool.map(one, [p["id"] for p in HO])
    r = np.array([x["r"] for x in rows]); dd = np.array([x["abs_d9"] for x in rows])
    drop = np.array([x["r"] - x["r_ctrl"] if x["r_ctrl"] is not None else np.nan for x in rows])
    res = dict(model_sha256=hashlib.sha256(open(f"{OUT}/model_final.json", "rb").read()).hexdigest(), rows=rows,
               median_r=float(np.median(r)), min_r=float(r.min()), rms_abs_d9=float(np.sqrt((dd ** 2).mean())), max_abs_d9=float(dd.max()),
               ctrl_median_drop=float(np.nanmedian(drop)), ctrl_n_clear=int(np.nansum(drop > 0.15)),
               median_r_after_local_shift=float(np.median([x["ncc_after_local_shift"] for x in rows])))
    res["bars"] = dict(median_r_ge_085=res["median_r"] >= 0.85, rms_le_15=res["rms_abs_d9"] <= 1.5,
                       control=res["ctrl_median_drop"] >= 0.30 and res["ctrl_n_clear"] >= 14)
    res["verdict"] = "PASS" if all(res["bars"].values()) else "FAIL"
    json.dump(res, open(f"{OUT}/heldout_result.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
