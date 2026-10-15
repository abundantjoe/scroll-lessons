"""P4-L3 (RULES.md DECL-P4-12-A3): depth-calibrated thin-slab channel.

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Numbers, hashes and PNG bytes only.
Rules are frozen in logs/sib/p4-depth/calib_params.json (pushed at faccba7 before any number).
Reuses p4-l2's code verbatim (tools/sib/p4-depth/l2.py = origin/...-sib-p4-l2 tools/sib/p4-l2/l2.py,
sha256 c6dad892...): grid, canvas_mask, eligibility, chunk layout, T_hi 203.

Usage:
  depth.py calib <ctl_mesh_dir> <out_dir> --worker k --nworkers n     # per-tile per-slice histograms (control only)
  depth.py calib-merge <ctl_mesh_dir> <out_dir> <thresholds.json>      # f(o), d*, z, verdict -> calib.json
  depth.py sign <ctl_mesh_dir> <out_dir>                               # SV slice direction vs du x dv vs outward
  depth.py l3 <mesh_dir> <out_dir> <calib.json> --ref-manifest ... --worker k --nworkers n
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(__file__))
import l2  # noqa: E402  (p4-l2 code, verbatim; puts src on sys.path)

PROV = l2.PROV
NZ, CH, T, CENTRE = l2.NZ, l2.CH, l2.T, l2.CENTRE
UM = 2.4  # um per slice (.zattrs scale 2.4, slice_step 1.0)
CAL_SEED, CAL_N = 20260927, 24
MAX_ABS_UM, Z_MIN = 100.0, 3.0
HALF_WIN_UM = 10.0
VOL = "PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr"


def offsets_um(nz=NZ, centre=CENTRE):
    return (np.arange(nz) - centre) * UM


# ---------------------------------------------------------------------------
# pure rules (unit-tested)
# ---------------------------------------------------------------------------

def f_from_hist(hist, t_hi):
    """hist: (nz, 256) counts of voxels at mesh-valid px per slice -> f(o) = frac of voxels > t_hi per slice."""
    h = np.asarray(hist, np.int64)
    n = h.sum(1)
    return h[:, t_hi + 1:].sum(1) / np.maximum(n, 1)


def peak_verdict(f, off_um, max_abs_um=MAX_ABS_UM, z_min=Z_MIN):
    """DECL-P4-12-A3 item 1 peak rule, as frozen in calib_params.json."""
    f = np.asarray(f, np.float64)
    off_um = np.asarray(off_um, np.float64)
    med = float(np.median(f))
    rsd = float(1.4826 * np.median(np.abs(f - med)))
    ex = f - med
    best = ex.max()
    cand = np.flatnonzero(ex == best)
    i = int(cand[np.argmin(np.abs(off_um[cand]))])  # ties: smallest |o|
    if rsd > 0:
        zp = float(ex[i] / rsd)
    else:
        zp = math.inf if ex[i] > 0 else 0.0
    ok_pos = abs(off_um[i]) <= max_abs_um + 1e-9
    ok_z = zp >= z_min
    return {"d_star_um": float(off_um[i]), "z_index": i, "f_peak": float(f[i]), "median_f": med,
            "robust_sd": rsd, "z_peak": zp, "within_100um": bool(ok_pos), "z_ge_3": bool(ok_z),
            "verdict": "PASS" if (ok_pos and ok_z) else "STOP"}


def l3_slices(z_star, nz=NZ):
    """Slices within +-10 um of the calibrated slice: |z - z*| * 2.4 <= 10 -> z* - 4 .. z* + 4, clipped."""
    h = int(math.floor(HALF_WIN_UM / UM + 1e-9))
    return max(0, z_star - h), min(nz - 1, z_star + h)


# ---------------------------------------------------------------------------
# chunk IO (full 109-slice chunks, or a slice range)
# ---------------------------------------------------------------------------

def get_chunk_range(key_prefix, cy, cx, z0, z1, shape_zyx=(NZ, CH, CH), cz=0):
    """Slices [z0, z1) of chunk (cz, cy, cx) at level 0 as one HTTP range request (C-order uncompressed)."""
    nz, h, w = shape_zyx
    key = f"{key_prefix}/0/{cz}/{cy}/{cx}"
    a, b = z0 * h * w, z1 * h * w - 1
    for i in range(7):
        try:
            r = l2._s.get(f"{l2.HTTP}/{key}", headers={"Range": f"bytes={a}-{b}"}, timeout=90)
            if r.status_code == 404:
                return None, {"k": f"0/{cz}/{cy}/{cx}", "status": 404}
            if r.status_code == 206 and len(r.content) == b - a + 1:
                d = np.frombuffer(r.content, np.uint8).reshape(z1 - z0, h, w)
                return d, {"k": f"0/{cz}/{cy}/{cx}", "status": 206, "range": [a, b],
                           "sha256": hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"chunk read failed: {key}")


def cal_sample(valid, H, W):
    nr, nc = -(-H // T), -(-W // T)
    el = []
    for r in range(nr):
        for c in range(nc):
            vf = float(l2.canvas_mask(valid, H, W, r * T, (r + 1) * T, c * T, (c + 1) * T).mean())
            if vf >= l2.ELIG:
                el.append((r, c, vf))
    idx = np.random.default_rng(CAL_SEED).choice(len(el), CAL_N, replace=False)
    return nr, nc, el, [el[i] for i in sorted(idx)]


def tile_depth_hist(seg, y0, y1, x0, x1, shape, m, ex, t_hi):
    """Per-slice uint8 histogram (NZ, 256) of voxels at mask m, plus an independent rot90 count of voxels > t_hi."""
    H, W = shape
    hist = np.zeros(NZ * 256, np.int64)
    rot_hi = np.zeros(NZ, np.int64)
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W) - 1) // CH + 1)]
    recs = []
    base = np.arange(NZ, dtype=np.int64)[:, None] * 256
    base16 = base.astype(np.uint16)
    def fetched():  # bounded prefetch (<= 64 chunks, ~114 MB, in flight) so memory stays flat
        for i in range(0, len(jobs), 64):
            yield from zip(jobs[i:i + 64], ex.map(lambda j: get_chunk_range(l2.sv_key(seg), *j, 0, NZ), jobs[i:i + 64]))

    for (cy, cx), (d, rec) in fetched():
        recs.append(rec)
        ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H)
        xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W)
        mm = m[ya - y0:yb - y0, xa - x0:xb - x0]
        k = int(mm.sum())
        if k == 0:
            continue
        if d is None:
            hist[base[:, 0]] += k
            continue
        sub = d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH]
        vox = sub[:, mm]  # (NZ, k)
        hist += np.bincount((vox.astype(np.uint16) + base16).ravel(), minlength=NZ * 256)
        rs, rm = np.rot90(sub, axes=(1, 2)), np.rot90(mm)
        rot_hi += (rs[:, rm] > t_hi).sum(1)
    return hist.reshape(NZ, 256), rot_hi, recs


def cmd_calib(a):
    th = json.load(open(a.thresholds))
    t_hi = int(th["T_hi"])
    za, _ = l2.zarray(l2.CTL)
    H, W = za["shape"][1:]
    valid = l2.load_valid(a.mesh_dir)
    assert valid.shape == (H // 20, W // 20)
    nr, nc, el, pick = cal_sample(valid, H, W)
    ex = cf.ThreadPoolExecutor(a.threads)
    fn = os.path.join(a.out, "cal_w%d.jsonl" % a.worker)
    done = {(d["r"], d["c"]) for d in map(json.loads, open(fn))} if os.path.exists(fn) else set()
    for r, c, vf in pick[a.worker::a.nworkers]:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        m = l2.canvas_mask(valid, H, W, y0, y1, x0, x1)
        h, rot_hi, recs = tile_depth_hist(l2.CTL, y0, y1, x0, x1, (H, W), m, ex, t_hi)
        vp = int(m.sum())
        assert (h.sum(1) == vp).all()
        with open(fn, "a") as fo:
            fo.write(json.dumps({"r": r, "c": c, "valid_fraction": vf, "valid_px": vp,
                                 "rot90_n_hi": rot_hi.tolist(),
                                 "chunks_read": sum(x["status"] == 206 for x in recs),
                                 "chunks_missing": sum(x["status"] == 404 for x in recs),
                                 "chunks_sha256_of_sorted_list": hashlib.sha256("\n".join(sorted(
                                     f'{x["k"]} {x.get("sha256", "404")}' for x in recs)).encode()).hexdigest(),
                                 "seconds": round(time.time() - t0, 1), "utc": l2.utc(),
                                 "hist": h.tolist()}) + "\n")
        print("cal r%d c%d %.1fs" % (r, c, time.time() - t0), flush=True)
    ex.shutdown()
    print("WORKER_DONE", a.worker, l2.utc(), flush=True)


def cmd_calib_merge(a):
    th = json.load(open(a.thresholds))
    t_hi, t_mid = int(th["T_hi"]), int(th["T_mid"])
    za, za_sha = l2.zarray(l2.CTL)
    H, W = za["shape"][1:]
    valid = l2.load_valid(a.mesh_dir)
    nr, nc, el, pick = cal_sample(valid, H, W)
    per = {}
    for fn in sorted(os.listdir(a.out)):
        if fn.startswith("cal_w") and fn.endswith(".jsonl"):
            for line in open(os.path.join(a.out, fn)):
                d = json.loads(line)
                per[(d["r"], d["c"])] = d
    assert set(per) == {(r, c) for r, c, _ in pick}, "sample incomplete"
    off = offsets_um()
    hist = np.zeros((NZ, 256), np.int64)
    rot = np.zeros(NZ, np.int64)
    band = {"r0-r1": np.zeros((NZ, 256), np.int64), "r2-r8": np.zeros((NZ, 256), np.int64)}
    per_tile = []
    for (r, c) in sorted(per):
        d = per[(r, c)]
        h = np.array(d["hist"], np.int64)
        hist += h
        rot += np.array(d["rot90_n_hi"], np.int64)
        band["r0-r1" if r <= 1 else "r2-r8"] += h
        ft = f_from_hist(h, t_hi)
        pv = peak_verdict(ft, off)
        per_tile.append({"r": r, "c": c, "valid_px": d["valid_px"], "chunks_read": d["chunks_read"],
                         "chunks_missing": d["chunks_missing"],
                         "chunks_sha256_of_sorted_list": d["chunks_sha256_of_sorted_list"],
                         "argmax_um": pv["d_star_um"], "z_peak": pv["z_peak"], "verdict_alone": pv["verdict"],
                         "f": [round(float(x), 8) for x in ft]})
    f = f_from_hist(hist, t_hi)
    n_hi = hist[:, t_hi + 1:].sum(1)
    pv = peak_verdict(f, off)
    med_vox = [l2.q_hist(hist[z], 0.5) for z in range(NZ)]
    gap = [int(z) for z in range(NZ) if med_vox[z] < t_mid]
    near = sum(abs(t["argmax_um"] - pv["d_star_um"]) <= 5.0 + 1e-9 for t in per_tile)
    plus = off > 0
    minus = off < 0
    ip, im = int(np.flatnonzero(plus)[np.argmax(f[plus])]), int(np.flatnonzero(minus)[np.argmax(f[minus])])
    sign = json.load(open(os.path.join(a.out, "sign.json"))) if os.path.exists(os.path.join(a.out, "sign.json")) else None
    out = {"provenance": PROV, "declaration": "RULES.md DECL-P4-12-A3 item 1",
           "params": "logs/sib/p4-depth/calib_params.json (frozen at faccba7)",
           "computed_utc": l2.utc(), "computed_before": "any title-strip (w010-027) read by p4-depth and any L3 tile",
           "material": f"s3://vesuvius-challenge-open-data/{l2.sv_key(l2.CTL)}", "level": 0,
           "level0_zarray_sha256": za_sha, "level0_shape": za["shape"],
           "T_hi": t_hi, "T_mid": t_mid, "thresholds_sha256": hashlib.sha256(open(a.thresholds, "rb").read()).hexdigest(),
           "sample": {"seed": CAL_SEED, "n": CAL_N, "n_eligible": len(el), "tiles": [[r, c] for r, c, _ in pick]},
           "n_valid_px": int(hist[0].sum()),
           "offsets_um": [round(float(x), 1) for x in off],
           "f": [float(x) for x in f], "n_hi": n_hi.tolist(),
           "median_voxel_per_slice": med_vox,
           "rot90_check": {"n_hi_rot90": rot.tolist(), "identical": bool((rot == n_hi).all())},
           "gap_depths": {"rule": "slices with pooled median voxel < T_mid (calib_params.json)",
                          "slices": gap, "offsets_um": [round(float(off[z]), 1) for z in gap],
                          "f": [float(f[z]) for z in gap],
                          "max_f": float(max((f[z] for z in gap), default=float("nan")))},
           "peak": pv,
           "d_star_um": pv["d_star_um"], "z_star": pv["z_index"], "z_peak": pv["z_peak"],
           "verdict": pv["verdict"],
           "l3_slices_inclusive": list(l3_slices(pv["z_index"])) if pv["verdict"] == "PASS" else None,
           "sides": {"plus (o > 0)": {"best_um": float(off[ip]), "f": float(f[ip]),
                                      "z": float((f[ip] - pv["median_f"]) / pv["robust_sd"]) if pv["robust_sd"] > 0 else None},
                     "minus (o < 0)": {"best_um": float(off[im]), "f": float(f[im]),
                                       "z": float((f[im] - pv["median_f"]) / pv["robust_sd"]) if pv["robust_sd"] > 0 else None},
                     "d_star_side": "plus" if pv["d_star_um"] > 0 else ("minus" if pv["d_star_um"] < 0 else "mesh (o = 0)")},
           "sign_convention": sign,
           "recto_verso_of_d_star": None,
           "bands": {k: [float(x) for x in f_from_hist(v, t_hi)] for k, v in band.items()},
           "band_peaks": {k: peak_verdict(f_from_hist(v, t_hi), off) for k, v in band.items()},
           "per_tile_consistency": {"n_tiles_argmax_within_5um_of_d_star": int(near), "n_tiles": len(per_tile)},
           "per_tile": per_tile,
           "histogram_per_slice": hist.tolist()}
    # specificity diagnostics (ASK.md item 2; reported, they do NOT enter the declared verdict)
    from statistics import NormalDist
    on = np.array([m >= t_mid for m in med_vox])
    zs = pv["z_index"]
    ms = float(np.median(f[on])) if on.any() else float("nan")
    rs = float(1.4826 * np.median(np.abs(f[on] - ms))) if on.any() else float("nan")
    exc = f - pv["median_f"]
    half = exc[zs] / 2
    lo_, hi_ = zs, zs
    while lo_ > 0 and exc[lo_ - 1] >= half:
        lo_ -= 1
    while hi_ < NZ - 1 and exc[hi_ + 1] >= half:
        hi_ += 1
    z_bonf = NormalDist().inv_cdf(1 - (1 - NormalDist().cdf(3.0)) / NZ)
    out["calibration_specificity"] = {
        "declared_rule_unit_tests": "FAILED no-layer tests b1 (25/100 iid-noise sheets PASS) and b2 (10/10 no-ink "
                                    "sheet+gap profiles PASS); see unit_tests.json and ASK.md item 2",
        "on_sheet_slices": {"rule": "pooled median voxel >= T_mid", "n": int(on.sum()),
                            "offsets_um": [round(float(off[z]), 1) for z in np.flatnonzero(on)]},
        "d_star_is_on_sheet": bool(on[zs]),
        "z_vs_on_sheet_baseline": float((f[zs] - ms) / rs) if rs and rs > 0 else None,
        "on_sheet_median_f": ms if on.any() else None, "on_sheet_robust_sd": rs if on.any() else None,
        "bonferroni_z_bar_109_offsets": z_bonf, "z_peak_ge_bonferroni": bool(pv["z_peak"] >= z_bonf),
        "peak_fwhm_um": round((hi_ - lo_ + 1) * UM, 1), "peak_half_max_offsets_um": [round(float(off[lo_]), 1), round(float(off[hi_]), 1)],
        "n_tiles_argmax_within_5um": int(near), "n_tiles": len(per_tile)}
    if sign and sign.get("recto_side") in ("plus", "minus") and pv["d_star_um"] != 0:
        side = out["sides"]["d_star_side"]
        out["recto_verso_of_d_star"] = ("recto" if side == sign["recto_side"] else "verso") + \
            (" (UNCERTAIN: sign test ambiguous)" if sign.get("ambiguous") else "")
    json.dump(out, open(os.path.join(a.out, "calib.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("d_star_um", "z_star", "z_peak", "verdict", "recto_verso_of_d_star")}),
          flush=True)


# ---------------------------------------------------------------------------
# sign: SV slice direction vs du x dv (empirical, CT) and du x dv vs outward (geometry)
# ---------------------------------------------------------------------------

def cmd_sign(a):
    from hercules.geometry.level_mesh import normal_sign_report
    from hercules.geometry.tifxyz import vertex_normals
    from hercules.geometry.level_mesh import CentreCurve
    from hercules.pipeline.centre import geometric_centre_curve
    import tifffile
    P = np.stack([tifffile.imread(os.path.join(a.mesh_dir, n)) for n in ("x.tif", "y.tif", "z.tif")], -1).astype(np.float64)
    P[(P == -1).any(-1)] = np.nan
    N = vertex_normals(P)
    za, _ = l2.zarray(l2.CTL)
    H, W = za["shape"][1:]
    valid = l2.load_valid(a.mesh_dir)
    _, _, _, pick = cal_sample(valid, H, W)
    vz = requests.get(f"{l2.HTTP}/{VOL}/0/.zarray", timeout=60).json()
    VZ, VY, VX = vz["shape"]
    rng = np.random.default_rng(CAL_SEED + 1)
    gh, gw = valid.shape
    cand = []
    for r, c, _ in pick:  # vertices inside the sampled tiles, away from the grid border
        g = np.argwhere(np.isfinite(N[(r * T) // 20:((r + 1) * T) // 20, (c * T) // 20:((c + 1) * T) // 20]).all(-1))
        g += [(r * T) // 20, (c * T) // 20]
        g = g[(g[:, 0] > 2) & (g[:, 0] < gh - 3) & (g[:, 1] > 2) & (g[:, 1] < gw - 3)]
        if len(g):
            cand.append(g[rng.choice(len(g), min(15, len(g)), replace=False)])
    cand = np.concatenate(cand)
    s = np.arange(NZ) - CENTRE
    cache = {}

    def vchunk(k):
        if k not in cache:
            d, _ = get_chunk_range(VOL, k[1], k[2], 0, CH, (CH, CH, CH), cz=k[0])
            cache[k] = d
        return cache[k]

    res = []
    ex = cf.ThreadPoolExecutor(16)
    for gr, gc in cand:
        y, x = gr * 20, gc * 20
        sv, _ = get_chunk_range(l2.sv_key(l2.CTL), y // CH, x // CH, 0, NZ)
        if sv is None:
            continue
        prof_sv = sv[:, y % CH, x % CH].astype(np.float64)
        p, n = P[gr, gc], N[gr, gc]
        prof = {}
        for sg in (1, -1):
            q = np.rint(p[None, :] + sg * s[:, None] * n[None, :]).astype(int)  # (x, y, z)
            ks = {(qz // CH, qy // CH, qx // CH) for qx, qy, qz in q}
            list(ex.map(vchunk, [k for k in ks if k not in cache]))
            v = []
            for qx, qy, qz in q:
                d = cache[(qz // CH, qy // CH, qx // CH)] if (0 <= qz < VZ and 0 <= qy < VY and 0 <= qx < VX) else None
                v.append(0.0 if d is None else float(d[qz % CH, qy % CH, qx % CH]))
            prof[sg] = np.array(v)
        if prof_sv.std() == 0 or prof[1].std() == 0 or prof[-1].std() == 0:
            continue
        rp = float(np.corrcoef(prof_sv, prof[1])[0, 1])
        rm = float(np.corrcoef(prof_sv, prof[-1])[0, 1])
        res.append({"g": [int(gr), int(gc)], "r_plus_n": rp, "r_minus_n": rm})
        if len(cache) > 3000:
            cache.clear()
    ex.shutdown()
    json.dump(res, open(os.path.join(a.out, "sign_vertices.json"), "w"))
    rp = np.array([x["r_plus_n"] for x in res])
    rm = np.array([x["r_minus_n"] for x in res])
    frac_plus = float((rp > rm).mean())
    sv_dir = 1 if frac_plus > 0.5 else -1  # +1: SV slice index grows along +n (du x dv)
    sv_ambig = not (max(frac_plus, 1 - frac_plus) >= 0.95 and len(res) >= 200)
    cc, info = geometric_centre_curve(P)
    rep = normal_sign_report(P, N, cc)
    ac = CentreCurve.straight((VX - 1) / 2.0, (VY - 1) / 2.0)  # = centre.volume_axis_centre, via HTTPS (no boto3)
    rep2 = normal_sign_report(P, N, ac)
    n_out = rep.sign  # +1: du x dv points outward
    # SV index grows toward: outward if sv_dir * n_out > 0
    plus_is_outward = sv_dir * n_out > 0
    recto_side = "minus" if plus_is_outward else "plus"  # recto = inward-facing surface
    amb = bool(sv_ambig or rep.ambiguous or rep.sign == 0 or rep2.sign != rep.sign)
    out = {"provenance": PROV, "declaration": "RULES.md DECL-P4-12-A3 item 1 (both mesh sides reported)",
           "computed_utc": l2.utc(), "volume": f"s3://vesuvius-challenge-open-data/{VOL}",
           "a_sv_vs_normal": {"n_vertices": len(res), "median_r_plus_n": float(np.median(rp)),
                              "median_r_minus_n": float(np.median(rm)), "frac_r_plus_gt_r_minus": frac_plus,
                              "sv_slice_index_grows_along": "+(du x dv)" if sv_dir > 0 else "-(du x dv)",
                              "ambiguous": bool(sv_ambig), "rule": ">= 200 vertices and >= 95 % agreement"},
           "b_normal_vs_outward": {"geometric_centre": {"sign": rep.sign, "frac_clear": rep.frac_clear,
                                                        "frac_positive": rep.frac_positive, "ambiguous": rep.ambiguous,
                                                        "centre_info": {k: [float(v) for v in vals] if isinstance(vals, list) else vals
                                                                        for k, vals in info.items()}},
                                   "volume_axis_centre": {"sign": rep2.sign, "frac_clear": rep2.frac_clear,
                                                          "frac_positive": rep2.frac_positive, "ambiguous": rep2.ambiguous}},
           "plus_side_is": "outward (away from the scroll axis)" if plus_is_outward else "inward (toward the scroll axis)",
           "recto_side": recto_side,
           "recto_rule": "recto = the inward-facing surface of the rolled sheet (papyrological convention, not measured)",
           "ambiguous": amb,
           "per_vertex": res}
    json.dump(out, open(os.path.join(a.out, "sign.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("plus_side_is", "recto_side", "ambiguous")}),
          json.dumps(out["a_sv_vs_normal"]), flush=True)


# ---------------------------------------------------------------------------
# L3 tiles (title strip; only after calib.json PASS is pushed)
# ---------------------------------------------------------------------------

def l3_max(seg, y0, y1, x0, x1, shape, ex, za, zb):
    H, W = shape
    out = np.zeros((y1 - y0, x1 - x0), np.uint8)
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W) - 1) // CH + 1)]
    recs = []
    def fetched():  # bounded prefetch
        for i in range(0, len(jobs), 256):
            yield from zip(jobs[i:i + 256], ex.map(lambda j: get_chunk_range(l2.sv_key(seg), *j, za, zb + 1),
                                                   jobs[i:i + 256]))

    for (cy, cx), (d, rec) in fetched():
        recs.append(rec)
        if d is None:
            continue
        ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H)
        xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W)
        out[ya - y0:yb - y0, xa - x0:xb - x0] = l2.slab_max_from_stack(
            d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH])
    return out, recs


def cmd_l3(a):
    import cv2
    from hercules.display import builder
    cal = json.load(open(a.calib))
    assert cal["verdict"] == "PASS", "calibration verdict is not PASS: P4-L3 stops"
    za_, zb_ = cal["l3_slices_inclusive"]
    assert (za_, zb_) == l3_slices(cal["z_star"])
    za, _ = l2.zarray(l2.SEG)
    H0, W0 = za["shape"][1:]
    assert (H0, W0) == (69760, 170000)
    valid = l2.load_valid(a.mesh_dir)
    ref = json.load(open(a.ref_manifest))
    ref_t = {(t["r"], t["c"]): t for t in ref["tiles"]}
    tiles = l2.order_tiles(list(ref_t))
    if a.rows:
        rows = {int(x) for x in a.rows.split(",")}
        tiles = [t for t in tiles if t[0] in rows]
    tiles = tiles[a.worker::a.nworkers]
    tdir = os.path.join(a.out, "tiles")
    os.makedirs(tdir, exist_ok=True)
    cen = os.path.join(a.out, "census_w%d.jsonl" % a.worker)
    done = {(d["r"], d["c"]) for d in map(json.loads, open(cen))} if os.path.exists(cen) else set()
    ex = cf.ThreadPoolExecutor(a.threads)
    for r, c in tiles:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        m = l2.canvas_mask(valid, H0, W0, y0, y1, x0, x1)
        vf = float(m.mean())
        assert vf == ref_t[(r, c)]["valid_fraction"] and int(m.sum()) == ref_t[(r, c)]["stats"]["valid_px"], (r, c)
        mx, recs = l3_max(l2.SEG, y0, y1, x0, x1, (H0, W0), ex, za_, zb_)
        t1 = time.time()
        sv = m & (mx > 0)
        disp, (lo, hi) = builder.linear_window_ct(mx, valid=sv)
        disp[~sv] = 0
        out = cv2.resize(disp, (l2.OUT_SIDE, l2.OUT_SIDE), interpolation=cv2.INTER_AREA)
        assert out.shape == (l2.OUT_SIDE, l2.OUT_SIDE) and out.dtype == np.uint8
        b = builder.png_bytes(out)
        ch = l2.png_chunks(b)
        assert set(ch) <= {"IHDR", "IDAT", "IEND"} and ch[0] == "IHDR" and ch[-1] == "IEND", ch
        assert b[16:24] == l2.OUT_SIDE.to_bytes(4, "big") * 2 and b[24] == 8 and b[25] == 0
        fn = f"{l2.SEG}_r{r}_c{c}.png"
        with open(os.path.join(tdir, fn), "wb") as fh:
            fh.write(b)
        vals = mx[m]
        vh = np.bincount(vals, minlength=256)
        rec = {"file": "tiles/" + fn, "r": r, "c": c, "png_sha256": hashlib.sha256(b).hexdigest(),
               "png_bytes": len(b), "png_chunks": sorted(set(ch)), "valid_fraction": vf,
               "canvas_rows": [y0, y1], "canvas_cols": [x0, x1], "level": 0,
               "raw_max_sha256": hashlib.sha256(np.ascontiguousarray(mx).tobytes()).hexdigest(),
               "stats": {"domain": "L3 max (slices %d..%d, level 0) at mesh-valid canvas px" % (za_, zb_),
                         "valid_px": int(vals.size), "stretch_px": int(sv.sum()),
                         "stretch_p1": lo, "stretch_p99": hi,
                         "max_mean": float(vals.mean()), "max_std": float(vals.std()),
                         **{"max_p%s" % q: l2.q_hist(vh, float(q) / 100) for q in ("1", "50", "99", "99.9")},
                         "frac_valid_max_zero": float((vals == 0).mean()),
                         "frac_valid_max_gt_T_hi": float((vals > 203).mean()),
                         "frac_out_zero": float((out == 0).mean()), "frac_out_255": float((out == 255).mean()),
                         "out_mean": float(out.mean())},
               "chunks_read": sum(x["status"] == 206 for x in recs),
               "chunks_missing": sum(x["status"] == 404 for x in recs),
               "read_s": round(t1 - t0, 1), "compute_s": round(time.time() - t1, 1), "utc": l2.utc()}
        with open(cen, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("l3 r%d c%d %.1fs" % (r, c, time.time() - t0), flush=True)
        del mx, disp, out
    ex.shutdown()
    print("WORKER_DONE", a.worker, l2.utc(), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("calib")
    p.add_argument("mesh_dir"), p.add_argument("out"), p.add_argument("thresholds")
    p.add_argument("--worker", type=int, default=0), p.add_argument("--nworkers", type=int, default=1)
    p.add_argument("--threads", type=int, default=16)
    p = sp.add_parser("calib-merge")
    p.add_argument("mesh_dir"), p.add_argument("out"), p.add_argument("thresholds")
    p = sp.add_parser("sign")
    p.add_argument("mesh_dir"), p.add_argument("out")
    p = sp.add_parser("l3")
    p.add_argument("mesh_dir"), p.add_argument("out"), p.add_argument("calib")
    p.add_argument("--ref-manifest", required=True)
    p.add_argument("--rows", default="")
    p.add_argument("--worker", type=int, default=0), p.add_argument("--nworkers", type=int, default=1)
    p.add_argument("--threads", type=int, default=16)
    a = ap.parse_args()
    {"calib": cmd_calib, "calib-merge": cmd_calib_merge, "sign": cmd_sign, "l3": cmd_l3}[a.cmd](a)


if __name__ == "__main__":
    main()
