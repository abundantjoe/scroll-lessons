"""p4-purple-mo dev-tile steps (PROTOCOL sections 2, 3.2 and 6): T_face, face diagnostics, planted positive control.

Provenance: Project HERCULES | owner the owner | [id removed]

No AUC or ink/background statistic of any feature is computed on dev tiles. Numbers only.
Usage: python dev.py <scratch> tface|posctl
"""
import json
import os
import sys
import time

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mo  # noqa: E402

SCR = sys.argv[1]
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
OUT = os.path.join(REPO, "logs/sib/p4-purple/mo")


def region_chunks(r, c):
    """Central 16 x 16 chunk region (2048 x 2048 px) of tile (r, c)."""
    cy = round((r * mo.T + mo.T / 2) / mo.CH) - 8
    cx = round((c * mo.T + mo.T / 2) / mo.CH) - 8
    return cy, cy + 16, cx, cx + 16


def load_region(r, c, vg):
    cy0, cy1, cx0, cx1 = region_chunks(r, c)
    p = os.path.join(SCR, f"reg_r{r}_c{c}.npy")
    if os.path.exists(p):
        arr, present = np.load(p), np.load(p + ".present.npy")
    else:
        arr, present = mo.fetch_window(cy0, cy1, cx0, cx1)
        if (r, c) == mo.DEV[0]:
            np.save(p, arr)
            np.save(p + ".present.npy", present)
    v = mo.valid4(vg, cy0 * 32, cy1 * 32, cx0 * 32, cx1 * 32)
    v &= np.repeat(np.repeat(present, 32, 0), 32, 1)
    return arr, v, (cy0, cy1, cx0, cx1)


def tface():
    vg, mrec = mo.mesh_valid_grid(SCR)
    hist = np.zeros(256, np.int64)
    per = {}
    for r, c in mo.DEV:
        t0 = time.time()
        arr, v, rc = load_region(r, c, vg)
        P = mo.block_profile(arr)
        del arr
        q = np.clip(np.rint(P[:, v]), 0, 255).astype(np.int64)
        h = np.bincount(q.ravel(), minlength=256)
        hist += h
        per[f"r{r}_c{c}"] = {"chunks": list(rc), "n_valid_cells": int(v.sum()), "secs": round(time.time() - t0, 1)}
        np.save(os.path.join(SCR, f"P_r{r}_c{c}.npy"), P)
        np.save(os.path.join(SCR, f"v_r{r}_c{c}.npy"), v)
    tf = mo.tface_from_hist(hist)
    # face diagnostics at the frozen T_face (fractions only; no ink statistic)
    for r, c in mo.DEV:
        P = np.load(os.path.join(SCR, f"P_r{r}_c{c}.npy"))
        v = np.load(os.path.join(SCR, f"v_r{r}_c{c}.npy"))
        hp, hm, zp, zm, okc = mo.faces(P, tf["T_face"])
        n = max(1, int(v.sum()))
        per[f"r{r}_c{c}"].update({
            "frac_centre_in_papyrus": float((okc & v).sum() / n),
            "frac_face_plus": float((np.isfinite(hp) & v).sum() / n),
            "frac_face_minus": float((np.isfinite(hm) & v).sum() / n),
            "frac_both": float((np.isfinite(hp) & np.isfinite(hm) & v).sum() / n),
            "median_h_plus_um": float(np.nanmedian(np.where(v, hp, np.nan))),
            "median_h_minus_um": float(np.nanmedian(np.where(v, hm, np.nan))),
        })
        os.remove(os.path.join(SCR, f"P_r{r}_c{c}.npy"))
    rec = {"provenance": mo.PROV, "serves": "PROTOCOL.md section 3.2 (T_face) and section 2 (c) diagnostics",
           "dev_tiles": [f"r{r}_c{c}" for r, c in mo.DEV], "mesh_inputs": mrec,
           "histogram_smoothed_P_all_slices": hist.tolist(), "T_face": tf, "per_tile": per,
           "viewing": "no image, tile or CT pixel was opened, displayed or described",
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(rec, open(os.path.join(OUT, "tface.json"), "w"), indent=1)
    print(json.dumps({"T_face": tf, "per_tile": per}, indent=1))


def glyph_mask(n=2048):
    px_mm = 1000.0 / mo.UM
    m = np.zeros((n, n), np.uint8)
    cc = (n // 2, n // 2)
    ro, w = 1.2 * px_mm, 0.4 * px_mm
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(yy - cc[0] + 0.5, xx - cc[1] + 0.5)
    ring = (d <= ro) & (d > ro - w)
    # bar through the centre at 45 degrees, 3.0 mm long, 0.4 mm wide
    u = ((xx - cc[1] + 0.5) + (yy - cc[0] + 0.5)) / np.sqrt(2)
    vv = ((xx - cc[1] + 0.5) - (yy - cc[0] + 0.5)) / np.sqrt(2)
    bar = (np.abs(u) <= 1.5 * px_mm) & (np.abs(vv) <= w / 2)
    return ring | bar


def plant(arr, P, z, side, D, g):
    """Add a D um deposit outward of face `side` at glyph px (in place on a copy)."""
    out = arr.copy()
    ys, xs = np.nonzero(g)
    cy, cx = ys // 4, xs // 4
    zc = z[cy, cx]
    ok = np.isfinite(zc)
    ys, xs, cy, cx, zc = ys[ok], xs[ok], cy[ok], cx[ok], zc[ok]
    d = D / mo.UM
    if side == "+":
        ins = np.floor(zc).astype(int)[None, :] - np.arange(5)[:, None]
        a, b = zc, zc + d
    else:
        ins = np.ceil(zc).astype(int)[None, :] + np.arange(5)[:, None]
        a, b = zc - d, zc
    ins = np.clip(ins, 0, mo.NZ - 1)
    vpap = np.median(P[ins, cy[None, :], cx[None, :]], axis=0)
    for k in range(mo.NZ):
        f = np.clip(np.minimum(b, k + 0.5) - np.maximum(a, k - 0.5), 0, 1)
        s = f > 0
        if not s.any():
            continue
        V = out[k, ys[s], xs[s]].astype(np.float32)
        out[k, ys[s], xs[s]] = np.clip(np.rint(V + f[s] * (np.maximum(V, vpap[s]) - V)), 0, 255).astype(np.uint8)
    return out, int(ok.sum()), int(len(ok))


def med_diff_auc(F, gin, gfar):
    a, b = F[gin & np.isfinite(F)], F[gfar & np.isfinite(F)]
    return {"recovered_um": float(np.median(a) - np.median(b)), "auc": mo.auc_float(a.astype(np.float64), b.astype(np.float64)),
            "n_glyph": int(a.size), "n_far": int(b.size)}


def posctl():
    tf = json.load(open(os.path.join(OUT, "tface.json")))["T_face"]["T_face"]
    vg, _ = mo.mesh_valid_grid(SCR)
    r, c = mo.DEV[0]
    arr, v, rc = load_region(r, c, vg)
    g = glyph_mask(arr.shape[1])
    gc = g.reshape(512, 4, 512, 4).mean(axis=(1, 3))
    gin = (distance_transform_edt(gc >= 1.0) * 9.6 > 50.0) & v
    gfar = (distance_transform_edt(gc <= 0.0) * 9.6 >= 100.0) & v

    def run(a):
        P = mo.block_profile(a)
        hp, hm, zp, zm, _ = mo.faces(P, tf)
        hp, hm = np.where(v, hp, np.nan), np.where(v, hm, np.nan)
        nan = np.full(hp.shape, np.nan, np.float32)
        return P, zp, zm, mo.features(hp, hm, nan, nan)

    P0, zp0, zm0, F0 = run(arr)
    res = {"baseline_unplanted": {k: med_diff_auc(F0[k], gin, gfar) for k in ("F1+", "F1-", "F2")}}
    nv = max(1, int(v.sum()))
    res["A1_face_fractions_region"] = {"plus": float((np.isfinite(zp0) & v).sum() / nv),
                                       "minus": float((np.isfinite(zm0) & v).sum() / nv),
                                       "both": float((np.isfinite(zp0) & np.isfinite(zm0) & v).sum() / nv)}
    print(json.dumps(res), flush=True)
    for side in "+-":
        for D in (5.0, 10.0, 20.0):
            t0 = time.time()
            a2, n_pl, n_g = plant(arr, P0, zp0 if side == "+" else zm0, side, D, g)
            _, _, _, F = run(a2)
            del a2
            opp = "-" if side == "+" else "+"
            res[f"face{side}_D{int(D)}"] = {
                "planted_px": n_pl, "glyph_px": n_g,
                "F1_planted_face": med_diff_auc(F["F1" + side], gin, gfar),
                "F2": med_diff_auc(F["F2"], gin, gfar),
                "F1_opposite_face": med_diff_auc(F["F1" + opp], gin, gfar), "secs": round(time.time() - t0, 1)}
            print(side, D, json.dumps(res[f"face{side}_D{int(D)}"]), flush=True)
    verdict = {}
    for side in "+-":
        x = res[f"face{side}_D10"]
        f1, f2 = x["F1_planted_face"], x["F2"]
        verdict[side] = bool(5 <= f1["recovered_um"] <= 13 and f1["auc"] >= 0.90 and 5 <= f2["recovered_um"] <= 13)
    rec = {"provenance": mo.PROV, "serves": "PROTOCOL.md section 6 (pipeline positive control)",
           "tile": f"r{r}_c{c}", "region_chunks": list(rc), "T_face": tf,
           "glyph": "ring outer radius 1.2 mm, stroke 0.4 mm, plus a 3.0 mm x 0.4 mm bar at 45 deg; centred",
           "n_cells_glyph_eroded": int(gin.sum()), "n_cells_far": int(gfar.sum()), "results": res,
           "pass_rule": "D=10: F1 planted-face recovered in [5,13] um and AUC >= 0.90, and F2 recovered in [5,13] um",
           "PASS": verdict, "viewing": "no image, tile or CT pixel was opened, displayed or described",
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(rec, open(os.path.join(OUT, "posctl.json"), "w"), indent=1)
    print(json.dumps({"PASS": verdict}))


if __name__ == "__main__":
    {"tface": tface, "posctl": posctl}[sys.argv[2]]()
