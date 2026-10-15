"""p4-highz: are the brightest voxels point-like (inclusions, sand, ash) or layer-like (a pigment layer on the
recto)? Orchestrator request under DECL-P4-6/-A1. 3-D connected components (26-conn) of voxels > T_hi over the
full 116-slice depth of whole level-0 chunks; per component: voxel count, PCA eigenvalues (planarity), normal
direction vs the depth axis, and centroid distance to the mesh surface (slice 58). Control vs E1. Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python morph3d.py <scratch> <repo> [n_chunks_per_material]
"""
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

M = TID = None
TH = None
S26 = np.ones((3, 3, 3), bool)


def one(yx):
    yc, xc = yx
    b = C.get(f"{M['url0']}/{yc}/{xc}")
    if b is None:
        return None
    a = np.frombuffer(b, np.uint8).reshape(M["n_slices"], C.CH, C.CH)
    v, ti = C.chunk_masks(M, TID, yc, xc)
    mask = (a > TH) & (ti >= 0)[None]
    lab, n = ndimage.label(mask, S26)
    if n == 0:
        return {"n": np.zeros(0), "vox_valid": int((ti >= 0).sum()) * M["n_slices"]}
    z, y, x = np.nonzero(lab)
    L = lab[z, y, x]
    cnt = np.bincount(L, minlength=n + 1)[1:].astype(float)
    def s(w):
        return np.bincount(L, weights=w, minlength=n + 1)[1:]
    zf, yf, xf = z.astype(float), y.astype(float), x.astype(float)
    mz, my, mx = s(zf) / cnt, s(yf) / cnt, s(xf) / cnt
    czz, cyy, cxx = s(zf * zf) / cnt - mz ** 2, s(yf * yf) / cnt - my ** 2, s(xf * xf) / cnt - mx ** 2
    czy, czx, cyx = s(zf * yf) / cnt - mz * my, s(zf * xf) / cnt - mz * mx, s(yf * xf) / cnt - my * mx
    cov = np.stack([np.stack([czz, czy, czx], -1), np.stack([czy, cyy, cyx], -1), np.stack([czx, cyx, cxx], -1)], -2)
    w, V = np.linalg.eigh(cov + np.eye(3) * 1e-9)  # ascending
    normal_z = np.abs(V[:, 0, 0])  # z component of the smallest-variance axis (plane normal)
    # border-touching (truncated) components
    mn = np.full(n, 1e9); mxb = np.full(n, -1e9)
    for arr in (y, x):
        lo = np.full(n + 1, 10 ** 6); hi = np.full(n + 1, -1)
        np.minimum.at(lo, L, arr); np.maximum.at(hi, L, arr)
        mn = np.minimum(mn, lo[1:]); mxb = np.maximum(mxb, hi[1:])
    border = (mn == 0) | (mxb == C.CH - 1)
    peak = np.zeros(n + 1, np.uint8)
    np.maximum.at(peak, L, a[z, y, x])
    return {"n": cnt, "zc_um": (mz - M["centre"]) * M["um"], "ev": w, "normal_z": normal_z, "border": border,
            "peak": peak[1:], "vox_valid": int((ti >= 0).sum()) * M["n_slices"]}


def work(items):
    with cf.ThreadPoolExecutor(12) as ex:
        return [r for r in ex.map(one, items) if r is not None]


def summarise(rs):
    n = np.concatenate([r["n"] for r in rs])
    zc = np.concatenate([r["zc_um"] for r in rs if len(r["n"])])
    ev = np.concatenate([r["ev"] for r in rs if len(r["n"])])
    nz = np.concatenate([r["normal_z"] for r in rs if len(r["n"])])
    bd = np.concatenate([r["border"] for r in rs if len(r["n"])])
    pk = np.concatenate([r["peak"] for r in rs if len(r["n"])])
    vox = sum(r["vox_valid"] for r in rs)
    tot = n.sum()
    bins = [(1, 1), (2, 7), (8, 63), (64, 511), (512, 10 ** 12)]
    size = {f"{a}-{b if b < 10 ** 12 else 'inf'}": {"components": int(((n >= a) & (n <= b)).sum()),
                                                  "frac_of_hi_voxels": float(n[(n >= a) & (n <= b)].sum() / tot)} for a, b in bins}
    def dist(sel):
        if not sel.any():
            return None
        l1, l2, l3 = ev[sel, 2], ev[sel, 1], ev[sel, 0]
        return {"components": int(sel.sum()), "voxels": int(n[sel].sum()),
                "planarity_l3_over_l2_median": float(np.median(l3 / np.maximum(l2, 1e-9))),
                "linearity_l2_over_l1_median": float(np.median(l2 / np.maximum(l1, 1e-9))),
                "frac_planar_l3_l2_lt_0p1": float(np.mean(l3 / np.maximum(l2, 1e-9) < 0.1)),
                "normal_z_abs_median": float(np.median(nz[sel])),
                "frac_normal_along_depth_gt_0p9": float(np.mean(nz[sel] > 0.9)),
                "centroid_offset_um_quantiles": [float(v) for v in np.percentile(zc[sel], [5, 25, 50, 75, 95])],
                "frac_centroid_within_15um_of_surface": float(np.mean(np.abs(zc[sel]) <= 15)),
                "frac_border_truncated": float(np.mean(bd[sel])),
                "frac_peak_255": float(np.mean(pk[sel] == 255))}
    return {"chunks": len(rs), "valid_voxels": int(vox), "hi_voxels": int(tot), "hi_density": float(tot / max(1, vox)),
            "components": int(len(n)), "size_bins": size,
            "ge8": dist(n >= 8), "ge64": dist(n >= 64), "ge512": dist(n >= 512),
            "ge64_within_15um": dist((n >= 64) & (np.abs(zc) <= 15)),
            "frac_hi_voxels_in_components_centred_within_15um": float(n[np.abs(zc) <= 15].sum() / tot),
            "uniform_depth_expectation_within_15um": None}


def run(name, scr, nch):
    global M, TID
    M = C.load_material(name, scr)
    TID = C.tile_index_map(M)
    allc = sorted({ch for t in M["tiles"] for ch in C.tile_chunks(M, t["r"], t["c"])})
    rng = np.random.default_rng(20260927)
    sample = [allc[i] for i in sorted(rng.choice(len(allc), nch, replace=False))]
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        rs = [r for part in pool.map(work, [sample[i::16] for i in range(16)]) for r in part]
    out = summarise(rs)
    out.update({"material": name, "sampled_chunks": nch, "present_chunks": len(rs), "secs": round(time.time() - t0, 1),
                "uniform_depth_expectation_within_15um": (2 * int(15 / M["um"]) + 1) / M["n_slices"]})
    return out


if __name__ == "__main__":
    scr, repo = sys.argv[1], sys.argv[2]
    os.chdir(repo)
    nch = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
    names = sys.argv[4:] or ["C", "E1"]
    thf = {n: "logs/sib/p4-highz/" + ("thresholds.json" if n in ("C", "E1") else "thresholds_2p4.json") for n in names}
    mats = {}
    for n in names:
        TH = json.load(open(thf[n]))["T_hi"]
        mats[n] = run(n, scr, nch)
        mats[n]["T_hi"] = TH
    res = {"provenance": C.PROV,
           "serves": "orchestrator request (DECL-P4-6/-A1): point-like vs layer-like bright voxels, control vs E1",
           "method": "whole level-0 chunks (116 x 128 x 128, 2.258 um isotropic), random (default_rng(20260927)) "
                                 "among chunks of eligible tiles; voxels > T_hi at mesh-valid px of eligible tiles; "
                                 "26-connected components; PCA of voxel coordinates; centroid offset = (z - 58) x 2.258 um "
                                 "(negative = towards slice 0); components touching the chunk's y/x border are truncated",
           "materials": mats,
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(res, open("logs/sib/p4-highz/morph3d" + ("" if names == ["C", "E1"] else "_" + "_".join(names)) + ".json", "w"), indent=1)
    for n, d in res["materials"].items():
        print(n, json.dumps({k: d[k] for k in ("hi_density", "components", "size_bins", "frac_hi_voxels_in_components_centred_within_15um")}))
        print("  ge64", d["ge64"]); print("  ge512", d["ge512"])
