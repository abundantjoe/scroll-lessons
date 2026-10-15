"""DECL-P4-19 line-structure test on the M1 prediction (strip-a grid). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

Never opens, views or prints image pixels; only 0.5 mm binned sums and derived numbers.

Definitions (fixed here, before any number of the test exists):
- Grid: 20260701183124-w010-027 canvas, T = 8343 canvas px, tile (r, c) = rows [rT,(r+1)T),
  cols [cT,(c+1)T). Rows r0-r2 = canvas rows [0, 3T). Groups: T = c11-c13, B1 = c7-c9,
  B2 = c3-c5, each 3T canvas px wide.
- Bins: each 3T span is cut into 120 equal bins (edges round(linspace(0, 3T, 121))), i.e.
  3T/120 = 208.575 px = 0.50002 mm at 417.131 px/mm, along z (canvas rows) and x (canvas cols).
  S[i, j] = sum of the raw uint8 prediction in z-bin i, x-bin j (0 outside mesh-valid, as published).
- Line profile P_G[i] = sum_j S[i, j].
- Pitch p_G: autocorrelation of P_G - mean(P_G), ac[k] = sum x[n]x[n+k] / sum x^2; the first
  lag k with 2 mm <= k*0.5 mm <= 12 mm and ac[k-1] < ac[k] >= ac[k+1]; refined by a parabola
  through ac[k-1..k+1]. None if there is no such lag.
- Lines: local maxima of P_G (P[i] > P[i-1] and P[i] >= P[i+1]) with P[i] > median(P) + 2 *
  1.4826 * MAD(P); taken greedily by height, dropping any within 0.6 p_G of a kept peak.
- FWHM h_G: per peak, the width between the linear-interpolated crossings of the level
  base + (P[i] - base)/2, base = median(P_G), searched outward from the peak (clipped at the
  profile ends; clipped widths are flagged). h_G = mean over lines.
- Left edge per line: x-profile X[j] = sum of S[i, j] over the z-bins between the two
  half-level crossings (inclusive, rounded outward); left edge = centre (mm from the group's
  left boundary) of the first x-bin with X[j] > 0.5 * max(X). s_G = SD (ddof 1) over lines.
  Also reported, not used in the decision: right edges (last such bin) and their SD.
- Validity (item 2): p and h ratios B2/B1 within [1/1.15, 1.15] and s_B2 <= 1.5 mm.
- Decision (item 3): r_p = p_T/p_B1, r_h = h_T/h_B1; TITLE-LIKE if r_p > 1.3 or r_h > 1.3 or
  s_T > 3 mm; BODY-LIKE if r_p and r_h in [1/1.15, 1.15] and s_T <= 1.5 mm; else INDETERMINATE.
  Any needed number missing (no pitch, < 2 lines) -> INVALID for B1/B2, INDETERMINATE for T.

Usage: python p419_profile.py <prediction.tif> <z.tif> <out.json>
"""
import json
import os
import sys
import time

import numpy as np

BIN_MM = 0.5
PITCH_LO_MM, PITCH_HI_MM = 2.0, 12.0
NBINS = 120
GROUPS = {"T": (11, 13), "B1": (7, 9), "B2": (3, 5)}
ROWS = (0, 2)
PROV = "Project HERCULES | owner the owner | [id removed]"


def autocorr_pitch(P, bin_mm=BIN_MM, lo=PITCH_LO_MM, hi=PITCH_HI_MM):
    x = np.asarray(P, np.float64) - np.mean(P)
    den = float(np.sum(x * x))
    if den <= 0:
        return None
    n = x.size
    kmax = min(int(np.floor(hi / bin_mm)) + 1, n - 1)
    ac = np.array([np.sum(x[:n - k] * x[k:]) / den for k in range(kmax + 1)])
    for k in range(max(int(np.ceil(lo / bin_mm)), 1), min(int(np.floor(hi / bin_mm)), kmax - 1) + 1):
        if ac[k] > ac[k - 1] and ac[k] >= ac[k + 1]:
            a, b, c = ac[k - 1], ac[k], ac[k + 1]
            d = a - 2 * b + c
            off = 0.5 * (a - c) / d if d != 0 else 0.0
            return {"pitch_mm": (k + off) * bin_mm, "lag_bins": k, "pitch_mm_unrefined": k * bin_mm,
                    "ac_peak": float(b)}
    return None


def robust_threshold(P):
    med = float(np.median(P))
    mad = float(np.median(np.abs(P - med)))
    return med + 2 * 1.4826 * mad, med, mad


def find_lines(P, pitch_mm, bin_mm=BIN_MM):
    P = np.asarray(P, np.float64)
    thr, med, mad = robust_threshold(P)
    cand = [i for i in range(1, P.size - 1) if P[i] > P[i - 1] and P[i] >= P[i + 1] and P[i] > thr]
    if P.size > 1 and P[0] > P[1] and P[0] > thr:
        cand.append(0)
    if P.size > 1 and P[-1] > P[-2] and P[-1] > thr:
        cand.append(P.size - 1)
    min_d = 0.6 * pitch_mm / bin_mm
    kept = []
    for i in sorted(cand, key=lambda i: (-P[i], i)):
        if all(abs(i - j) >= min_d for j in kept):
            kept.append(i)
    return sorted(kept), thr, med, mad


def half_width(P, i, base, bin_mm=BIN_MM):
    P = np.asarray(P, np.float64)
    lvl = base + (P[i] - base) / 2.0
    clipped = False
    j = i
    while j > 0 and P[j - 1] > lvl:
        j -= 1
    if j == 0:
        left = 0.0
        clipped = True
    else:
        left = (j - 1) + (lvl - P[j - 1]) / (P[j] - P[j - 1])
    k = i
    while k < P.size - 1 and P[k + 1] > lvl:
        k += 1
    if k == P.size - 1:
        right = float(P.size - 1)
        clipped = True
    else:
        right = k + (P[k] - lvl) / (P[k] - P[k + 1])
    return {"left_bin": left, "right_bin": right, "fwhm_mm": (right - left) * bin_mm, "clipped": clipped}


def line_edges(S, band, bin_mm=BIN_MM):
    lo = int(np.floor(band["left_bin"]))
    hi = int(np.ceil(band["right_bin"]))
    X = S[max(lo, 0):min(hi, S.shape[0] - 1) + 1].sum(0).astype(np.float64)
    if X.max() <= 0:
        return None, None
    idx = np.flatnonzero(X > 0.5 * X.max())
    return (idx[0] + 0.5) * bin_mm, (idx[-1] + 0.5) * bin_mm


def analyse_group(S, bin_mm=BIN_MM):
    """S: (z-bins, x-bins) binned sums of one group. Returns every number of item 1."""
    P = S.sum(1).astype(np.float64)
    out = {"profile_sum": P.tolist()}
    pc = autocorr_pitch(P, bin_mm)
    out["pitch"] = pc
    if pc is None:
        out.update({"p_mm": None, "n_lines": None, "h_mm": None, "s_mm": None})
        return out
    lines, thr, med, mad = find_lines(P, pc["pitch_mm"], bin_mm)
    out.update({"p_mm": pc["pitch_mm"], "threshold": thr, "median": med, "mad": mad, "n_lines": len(lines)})
    per = []
    for i in lines:
        hw = half_width(P, i, med, bin_mm)
        le, re = line_edges(S, hw, bin_mm)
        per.append({"peak_bin": i, "peak_mm": (i + 0.5) * bin_mm, "peak_value": P[i], **hw,
                    "left_edge_mm": le, "right_edge_mm": re})
    out["lines"] = per
    out["h_mm"] = float(np.mean([p["fwhm_mm"] for p in per])) if per else None
    out["n_fwhm_clipped"] = int(sum(p["clipped"] for p in per))
    le = [p["left_edge_mm"] for p in per if p["left_edge_mm"] is not None]
    re = [p["right_edge_mm"] for p in per if p["right_edge_mm"] is not None]
    out["s_mm"] = float(np.std(le, ddof=1)) if len(le) >= 2 else None
    out["right_edge_sd_mm"] = float(np.std(re, ddof=1)) if len(re) >= 2 else None
    return out


def within(r, tol=1.15):
    return r is not None and (1.0 / tol) <= r <= tol


def ratio(a, b):
    return None if (a is None or b is None or b == 0) else a / b


def decide(gT, gB1, gB2):
    need = lambda g: g["p_mm"] is not None and g["h_mm"] is not None and g["s_mm"] is not None
    v = {"rp_B2_B1": ratio(gB2["p_mm"], gB1["p_mm"]), "rh_B2_B1": ratio(gB2["h_mm"], gB1["h_mm"]),
         "s_B2": gB2["s_mm"]}
    if not (need(gB1) and need(gB2)):
        return {"validity": v, "valid": False, "verdict": "INVALID", "reason": "missing B1/B2 number"}
    valid = within(v["rp_B2_B1"]) and within(v["rh_B2_B1"]) and gB2["s_mm"] <= 1.5
    if not valid:
        return {"validity": v, "valid": False, "verdict": "INVALID", "reason": "B2 vs B1 not body-like"}
    d = {"r_p": ratio(gT["p_mm"], gB1["p_mm"]), "r_h": ratio(gT["h_mm"], gB1["h_mm"]), "s_T": gT["s_mm"]}
    title = (d["r_p"] is not None and d["r_p"] > 1.3) or (d["r_h"] is not None and d["r_h"] > 1.3) or \
            (d["s_T"] is not None and d["s_T"] > 3.0)
    body = within(d["r_p"]) and within(d["r_h"]) and d["s_T"] is not None and d["s_T"] <= 1.5
    verdict = "TITLE-LIKE" if title else ("BODY-LIKE" if body else "INDETERMINATE")
    return {"validity": v, "valid": True, "decision_inputs": d, "verdict": verdict}


def binned_sums(reader, y0, y1, x0, x1, nz=NBINS, nx=NBINS, chunk_bins=6):
    ze = np.rint(np.linspace(y0, y1, nz + 1)).astype(np.int64)
    xe = np.rint(np.linspace(x0, x1, nx + 1)).astype(np.int64)
    S = np.zeros((nz, nx), np.int64)
    for b0 in range(0, nz, chunk_bins):
        b1 = min(b0 + chunk_bins, nz)
        blk = reader.read(int(ze[b0]), int(ze[b1]), x0, x1)
        colsum = np.add.reduceat(blk.astype(np.int64), xe[:-1] - x0, axis=1)
        S[b0:b1] = np.add.reduceat(colsum, ze[b0:b1] - ze[b0], axis=0)
    return S, ze, xe


def main():
    sys.path.insert(0, os.path.dirname(__file__))
    import tifffile
    from tile_w010_027 import TiledReader
    pred, zt, out = sys.argv[1:4]
    t0 = time.time()
    T = 8343
    px_per_mm = 417.1314650253318
    rd = TiledReader(pred)
    y0, y1 = ROWS[0] * T, (ROWS[1] + 1) * T
    Z = tifffile.imread(zt).astype(np.float32)
    gh, gw = Z.shape
    res = {"provenance": PROV, "declaration": "RULES.md DECL-P4-19", "segment": "20260701183124-w010-027",
           "grid": {"T": T, "px_per_mm": px_per_mm, "canvas": [rd.H, rd.W], "rows": list(ROWS),
                    "bin_mm_nominal": BIN_MM, "bin_px": 3 * T / NBINS, "bin_mm_actual": 3 * T / NBINS / px_per_mm},
           "groups": {}}
    for name, (c0, c1) in GROUPS.items():
        x0, x1 = c0 * T, (c1 + 1) * T
        S, ze, xe = binned_sums(rd, y0, y1, x0, x1)
        # mesh-valid pixel count and median z per z-bin (grid rows = canvas rows / 20)
        gz0, gz1, gx0, gx1 = y0 // 20, y1 // 20, x0 // 20, min(x1 // 20, gw)
        zg = Z[gz0:gz1, gx0:gx1]
        zmed = [float(np.median(v[v != -1])) if (v != -1).any() else None
                for v in (zg[(ze[i] - y0) // 20:(ze[i + 1] - y0) // 20] for i in range(NBINS))]
        vfrac = [float((v != -1).mean()) if v.size else None
                 for v in (zg[(ze[i] - y0) // 20:(ze[i + 1] - y0) // 20] for i in range(NBINS))]
        g = analyse_group(S)
        g.update({"cols": [c0, c1], "canvas_cols": [x0, x1], "canvas_rows": [y0, y1],
                  "z_bin_median_z_vox": zmed, "z_bin_valid_frac": vfrac,
                  "x_profile_sum": S.sum(0).tolist()})
        res["groups"][name] = g
        print(name, {k: g[k] for k in ("p_mm", "n_lines", "h_mm", "s_mm")}, flush=True)
    res["decision"] = decide(res["groups"]["T"], res["groups"]["B1"], res["groups"]["B2"])
    # transparency: same decision on unrefined (integer-lag) pitch
    un = {k: dict(v) for k, v in res["groups"].items()}
    for k in un:
        if un[k]["pitch"]:
            un[k]["p_mm"] = un[k]["pitch"]["pitch_mm_unrefined"]
    res["decision_unrefined_pitch"] = decide(un["T"], un["B1"], un["B2"])["verdict"]
    zm = res["groups"]["B1"]["z_bin_median_z_vox"]
    zz = [v for v in zm if v is not None]
    res["orientation"] = {"z_mm_first_bin": zz[0] * 0.0024 if zz else None, "z_mm_last_bin": zz[-1] * 0.0024 if zz else None,
                          "note": "median mesh z (2.4 um vox) of B1 per z-bin; profile index 0 = canvas row 0"}
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out, "w"), indent=1)
    print("VERDICT", res["decision"]["verdict"], "unrefined:", res["decision_unrefined_pitch"], flush=True)


if __name__ == "__main__":
    main()
