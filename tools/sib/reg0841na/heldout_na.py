# Provenance: Project HERCULES | owner the owner | [id removed]
"""Evaluate the frozen non-affine map on the 16 new held-out patches (prereg_na.md).
Usage: heldout_na.py OUT.json"""
import hashlib, json, os, sys
from multiprocessing import Pool
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reg0841"))
import reg_core as rc
from field import load_final
REPO = "/home/user/dominion"; BL = "/work/reg/blocks_na"
MAP, FD = load_final()
plan = json.load(open(f"{REPO}/logs/sib/reg0841na/new_heldout_plan.json"))
IDS = [p["id"] for p in plan["patches"]]


def sample_f(f2, o2, o9, shape, shift=None):
    """Rescan sampled at f(p + shift(p)) for every block voxel; u on a 3x5x5 lattice, trilinear between nodes."""
    nz, ny, nx = shape
    lz, ly, lx = np.linspace(0, nz - 1, 3), np.linspace(0, ny - 1, 5), np.linspace(0, nx - 1, 5)
    Z, Y, X = np.meshgrid(lz, ly, lx, indexing="ij")
    L = np.stack([X.ravel() + o9[2], Y.ravel() + o9[1], Z.ravel() + o9[0]], 1)
    if shift is not None:
        L = L + shift
    uL = MAP.u(L).reshape(3, 5, 5, 3)
    zz, yy, xx = np.meshgrid(np.arange(nz) * 2 / (nz - 1), np.arange(ny) * 4 / (ny - 1), np.arange(nx) * 4 / (nx - 1), indexing="ij")
    co = np.stack([zz.ravel(), yy.ravel(), xx.ravel()])
    u = np.stack([map_coordinates(uL[..., k], co, order=1) for k in range(3)], 1)
    P = rc.block_points(o9, shape)
    if shift is not None:
        P = P + shift
    q = (P + u) @ MAP.A.T + MAP.c
    coords = np.stack([q[:, 2] - o2[0], q[:, 1] - o2[1], q[:, 0] - o2[2]])
    ins = float(np.all((coords >= 0) & (coords <= np.array(f2.shape)[:, None] - 1), axis=0).mean())
    return map_coordinates(f2, coords, order=1, mode="nearest").reshape(shape).astype(np.float32), ins


def one(pid):
    m = json.load(open(f"{BL}/{pid}.json"))
    B = np.load(f"{BL}/{pid}_v9.npy").astype(np.float32)
    f2 = rc.prefilter(np.load(f"{BL}/{pid}_v2.npy")); o2 = m["origin2_zyx"]; o9 = m["origin9_zyx"]
    R, ins = sample_f(f2, o2, o9, B.shape)
    r = rc.ncc(B, R); Bl = gaussian_filter(B, 1.0); r_lp = rc.ncc(Bl, gaussian_filter(R, 1.0))
    pc = np.array(o9[::-1], float) + (np.array(B.shape[::-1]) - 1) / 2
    J, cj = MAP.local_affine(pc)
    P = rc.block_points(o9, B.shape)
    d, info = rc.refine(B, f2, o2, J, cj, P); info.pop("hist")
    # affine-only reference (same block): converged shift under the frozen affine
    da, _ = rc.refine(B, f2, o2, MAP.A, MAP.c, P)
    n, pitch, aniso, flag, ac = rc.sheet_normal_pitch(B)
    ctrl = {}
    for sgn in (1, -1):
        Rc, insc = sample_f(f2, o2, o9, B.shape, shift=sgn * 0.5 * pitch * n)
        ctrl[sgn] = (rc.ncc(B, Rc), rc.ncc(Bl, gaussian_filter(Rc, 1.0)), insc)
    r_ctrl = max(ctrl[1][0], ctrl[-1][0])
    return dict(id=pid, p=pc.tolist(), r=r, r_lp=r_lp, inside_frac=ins, d9=d.tolist(), resid9=float(np.linalg.norm(d)),
                resid2=float(np.linalg.norm(J @ d)), affine_only_d9=da.tolist(), affine_only_resid9=float(np.linalg.norm(da)),
                u_pred=MAP.u(pc)[0].tolist(), normal_xyz=n.tolist(), pitch9=pitch, pitch_flag=flag,
                r_ctrl_plus=ctrl[1][0], r_ctrl_minus=ctrl[-1][0], r_ctrl=r_ctrl, drop=r - r_ctrl,
                r_ctrl_lp=max(ctrl[1][1], ctrl[-1][1]), ctrl_inside=[ctrl[1][2], ctrl[-1][2]],
                **{f"refine_{k}": v for k, v in info.items()})


def main():
    with Pool(2) as pool:
        rows = pool.map(one, IDS)
    r = np.array([x["r"] for x in rows]); e9 = np.array([x["resid9"] for x in rows]); e2 = np.array([x["resid2"] for x in rows])
    ea = np.array([x["affine_only_resid9"] for x in rows])
    s = dict(n=len(rows), median_r=float(np.median(r)), min_r=float(r.min()), rms_resid9=float(np.sqrt((e9 ** 2).mean())),
             max_resid9=float(e9.max()), rms_resid2=float(np.sqrt((e2 ** 2).mean())),
             affine_only_rms_resid9=float(np.sqrt((ea ** 2).mean())),
             median_drop=float(np.median([x["drop"] for x in rows])), n_ctrl_clear=int(sum(x["r_ctrl"] < x["r"] - 0.15 for x in rows)),
             median_r_lp=float(np.median([x["r_lp"] for x in rows])),
             median_ncc_after_local_shift=float(np.median([x["refine_ncc_after_shift"] for x in rows])))
    s["bar_median_r_ge_0.85"] = "PASS" if s["median_r"] >= 0.85 else "FAIL"
    s["bar_rms_le_1.5_9umvox"] = "PASS" if s["rms_resid9"] <= 1.5 else "FAIL"
    s["bar_control_clear_drop"] = "PASS" if s["median_drop"] >= 0.30 and s["n_ctrl_clear"] >= 14 else "FAIL"
    h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    out = dict(field_final_sha256=h(f"{REPO}/logs/sib/reg0841na/field_final.json"), prereg_sha256=h(f"{REPO}/logs/sib/reg0841na/prereg_na.md"),
               field=dict(kind=FD["kind"], smoothing=FD["smoothing"]), summary=s, rows=rows)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(s, indent=1))
    for x in rows:
        print(x["id"], round(x["r"], 3), round(x["resid9"], 2), round(x["affine_only_resid9"], 2), x["pitch9"], round(x["r_ctrl"], 3), round(x["refine_ncc_after_shift"], 3))


if __name__ == "__main__":
    main()
