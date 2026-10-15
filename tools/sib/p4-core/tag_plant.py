# Provenance: Project HERCULES | owner the owner | [id removed]
"""Planted-tab tests for P4-TAG (DECL-P4-15 c). Synthetic tabs of known
thickness, area and position are inserted, with a partial-volume model, into
real L4 blocks at the roll ends. The identical detector (tag_search) then
runs on the block. Reports detection, area error and thickness error. Numbers
only.

usage: tag_plant.py <outer_dir> <umb.json> <tag_raw.json> <out.json>
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tag_search as ts  # noqa: E402
import tag_run as tr  # noqa: E402

F = ts.F
V = ts.VOX_MM
MM_L0 = 1 / 2.4e-3


def cover(d, t):
    """Fraction of a voxel (extent V along d) covered by a slab |d| <= t/2."""
    lo = np.maximum(d - V / 2, -t / 2)
    hi = np.minimum(d + V / 2, t / 2)
    return np.clip(hi - lo, 0, None) / V


def plant(blk, za, origin_yx, ol, tab, val):
    """Insert the tab into blk (in place). Returns the true tab voxel mask."""
    H, W = blk.shape[1:]
    z_lo, z_hi = tab["z_l4"]
    true = np.zeros(blk.shape, bool)
    for k in range(blk.shape[0]):
        z = za + k
        if not (z_lo <= z < z_hi):
            continue
        zl0 = (z + 0.5) * F
        ex = ts.excess_map(ol, zl0, (H, W), origin_yx)
        ux, uy = ol.umb(np.array([zl0]))
        yy, xx = np.mgrid[0:H, 0:W]
        X = (xx + origin_yx[1] + 0.5) * F
        Y = (yy + origin_yx[0] + 0.5) * F
        th = np.arctan2(Y - uy[0], X - ux[0])
        r = np.hypot(X - ux[0], Y - uy[0]) * 2.4e-3
        dth = np.angle(np.exp(1j * (th - tab["theta"])))
        if tab["kind"] == "tangential":
            # smooth arc at constant radius: median outline radius over the arc + excess
            ro = ol.rout(zl0) * 2.4e-3
            bins = ((np.linspace(-0.5, 0.5, 64) * tab["arc_mm"] / 25.0 + tab["theta"] + math.pi) / (2 * math.pi) * ts.NBIN).astype(int) % ts.NBIN
            rt = float(np.median(ro[bins])) + tab["excess_mm"]
            half = tab["arc_mm"] / 2 / rt
            inarc = np.abs(dth) <= half
            c = np.where(inarc, cover(r - rt, tab["t_mm"]), 0)
        else:  # radial fin
            dperp = r * dth
            inr = (ex >= tab["excess_mm"]) & (ex <= tab["excess_mm"] + tab["len_mm"])
            c = np.where(inr, cover(dperp, tab["t_mm"]), 0)
        v = np.round(c * val).astype(np.int16)
        blk[k] = np.maximum(blk[k], v.astype(np.uint8))
        true[k] = c > 0.5
    return true


def detect(blk, za, origin_yx, ol, thr):
    H, W = blk.shape[1:]
    C, E = [], []
    cache = {}
    for k in range(blk.shape[0]):
        zl0 = (za + k + 0.5) * F
        zb = int(zl0 // MM_L0)
        if zb not in cache:
            cache = {zb: ts.excess_map(ol, zl0, (H, W), origin_yx)}
        ex = cache[zb]
        m = (blk[k] > thr) & (ex > ts.EXCESS_MM)
        yy, xx = np.nonzero(m)
        C.append(np.stack([np.full(yy.size, za + k), yy + origin_yx[0], xx + origin_yx[1]], 1))
        E.append(ex[yy, xx])
    C = np.concatenate(C).astype(np.int32)
    E = np.concatenate(E).astype(np.float32)
    lab, n = ts.components(C)
    return C, E, lab, n


def main(outer_dir, umb, raw_json, out_path):
    t0 = time.time()
    ol = ts.Outline(Path(outer_dir), Path(umb))
    raw = json.load(open(raw_json))
    thr = raw["threshold"]["thr"]
    win = tr.xy_window(ol)
    y0, y1, x0, x1 = win
    rng = np.random.default_rng(20260927)
    results = []
    for band in ("bottom", "top"):
        edge_l4 = int((ol.zmin if band == "bottom" else ol.zmax) // F)
        za = max(0, edge_l4 - 64) if band == "top" else edge_l4
        zb = za + 128
        blk0, _, _ = ts.read_block(ts.LEVEL, za, zb, y0, y1, x0, x1)
        # papyrus value: nonzero median at outer-mesh vertices in this block
        P = ol.P
        sel = (P[:, 2] // F >= za) & (P[:, 2] // F < zb)
        Q = (P[sel] // F).astype(int)
        vals = blk0[Q[:, 2] - za, Q[:, 1] - y0, Q[:, 0] - x0]
        val = float(np.median(vals[vals > 0])) if (vals > 0).any() else 40.0
        for kind in ("tangential", "radial"):
            for t_mm in (0.06, 0.10, 0.15, 0.25):
                for e0 in ((1.0, 2.5) if kind == "tangential" else (0.6,)):
                    theta = float(rng.uniform(-math.pi, math.pi))
                    hz = int(round(4.0 / V))
                    zlo = za + 12
                    tab = {"band": band, "kind": kind, "t_mm": t_mm, "excess_mm": e0, "theta": theta,
                           "z_l4": [zlo, zlo + hz], "arc_mm": 12.0, "len_mm": 3.0}
                    area_true = (12.0 if kind == "tangential" else 3.0) * hz * V
                    blk = blk0.copy()
                    true = plant(blk, za, (y0, x0), ol, tab, val)
                    bg = blk0[true]
                    C, E, lab, n = detect(blk, za, (y0, x0), ol, thr)
                    Tz, Ty, Tx = np.nonzero(true)
                    tkeys = set(zip((Tz + za).tolist(), (Ty + y0).tolist(), (Tx + x0).tolist()))
                    hit = np.array([tuple(c) in tkeys for c in C.tolist()]) if len(C) else np.zeros(0, bool)
                    rec = {**tab, "val": val, "true_area_mm2": area_true, "n_true_vox": int(true.sum()),
                           "background_zero_frac": float(np.mean(bg == 0)) if bg.size else None}
                    if hit.any():
                        best = np.bincount(lab[hit]).argmax()
                        m = lab == best
                        st = ts.component_stats(C[m], E[m], np.zeros(int(m.sum()), int), 1, min_vox=1)[0]
                        overlap = float(hit[m].sum() / max(1, true.sum()))
                        rec.update({"detected": bool(overlap >= 0.5), "sheet_like": st["sheet_like"],
                                    "overlap_frac_of_true": overlap, "area_mm2": st["area_mm2"],
                                    "area_rel_err": (st["area_mm2"] - area_true) / area_true,
                                    "thickness_mm": st["thickness_mm"], "attached": st["attached"],
                                    "component_extra_vox": int(m.sum() - hit[m].sum())})
                    else:
                        rec.update({"detected": False, "sheet_like": False, "overlap_frac_of_true": 0.0})
                    results.append(rec)
                    print(json.dumps({k: rec.get(k) for k in ("band", "kind", "t_mm", "excess_mm", "detected", "sheet_like", "overlap_frac_of_true", "area_rel_err", "thickness_mm", "background_zero_frac")}), flush=True)
    det = [r for r in results if r["detected"]]
    summ = {"n_tabs": len(results), "n_detected": len(det), "n_detected_sheet_like": sum(r["sheet_like"] for r in det),
            "by_thickness": {str(t): {"n": sum(r["t_mm"] == t for r in results),
                                      "detected": sum(r["t_mm"] == t and r["detected"] for r in results),
                                      "sheet_like": sum(r["t_mm"] == t and r["detected"] and r["sheet_like"] for r in results)}
                             for t in (0.06, 0.10, 0.15, 0.25)},
            "area_rel_err_detected_median_abs": float(np.median([abs(r["area_rel_err"]) for r in det])) if det else None,
            "area_rel_err_detected_p90_abs": float(np.percentile([abs(r["area_rel_err"]) for r in det], 90)) if det else None}
    json.dump({"provenance": "Project HERCULES | owner the owner | [id removed]", "thr": thr,
               "summary": summ, "tabs": results, "wall_s": time.time() - t0}, open(out_path, "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
