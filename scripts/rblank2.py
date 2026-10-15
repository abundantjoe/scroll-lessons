#!/usr/bin/env python
"""rblank2.py -- RULES R-BLANK part 2: margin against DISTANCE TO THE NEAREST LABELLED INK PIXEL.

Declared in RULES before it was run.  Tests the caveat recorded in R-BLANK's own declaration: "unlabelled" is not
"ink-free", and that bias runs upward.  Bands, statistic and interpretation are fixed in the declaration; nothing
here chooses them.  This can only weaken or confirm a caveat on our own claim - it flags nothing and changes no
verdict.
"""
import argparse, json, os, sys
import numpy as np, tifffile
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55, rblank
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA
POOL = 8                                     # max-pool factor for the distance transform
BANDS = ((0.0, 0.0), (0.0, 1000.0), (1000.0, 2000.0), (2000.0, 4000.0), (4000.0, float("inf")))
BAND_NAMES = ("touching ink", ">0-1 mm", "1-2 mm", "2-4 mm", ">=4 mm")
MIN_BAND_N = 5
BAR = rblank.BASELINE_BAR                    # +0.0042, fixed in the R-BLANK declaration


def pooled_distance_um(lab, um, pool=POOL):
    """Distance (um) to the nearest labelled ink pixel, on an 8x MAX-POOLED lattice; returns (d_pooled, pool).

    Max-pooling GROWS the ink mask, so every true ink pixel lies inside an inked cell.  The transform gives the
    distance D in CELL units between cell centres, and centre-to-centre is NOT a bound on pixel-to-pixel: a pixel can
    sit up to (pool/2)*sqrt(2) from its own cell centre, at either end.  So the returned distance is
    max(0, D - sqrt(2)) * pool * um, which IS a lower bound on the true pixel distance:

        |p - q| >= D*pool - 2*(pool/2)*sqrt(2) = pool*(D - sqrt(2))

    A unit can therefore only be placed NEARER to ink than it really is, never further - which is the direction the
    declaration requires.  The cost is that a band edge is conservative by up to sqrt(2)*pool*um = 106 um.
    The transform runs on 1/64 of the pixels, which is why it fits in memory on this box."""
    H, W = lab.shape
    h, w = -(-H // pool), -(-W // pool)                    # ceil, so no row or column of the canvas is dropped
    pad = np.zeros((h * pool, w * pool), bool)
    pad[:H, :W] = lab
    small = pad.reshape(h, pool, w, pool).max(axis=(1, 3))
    if not small.any():
        return np.full((h, w), np.inf, np.float32), pool
    d_cells = ndimage.distance_transform_edt(~small).astype(np.float32)
    return np.maximum(d_cells - np.float32(np.sqrt(2.0)), 0.0) * (pool * um), pool


def unit_min_distance(dsmall, pool, shape_rc, side, origin):
    """Per-unit minimum distance to ink: the min of the pooled field over the pooled cells the unit overlaps."""
    oy, ox = origin
    R, C = shape_rc
    out = np.full((R, C), np.inf, np.float64)
    for r in range(R):
        y0, y1 = (oy + r * side) // pool, -(-(oy + (r + 1) * side) // pool)
        band = dsmall[y0:y1]
        if band.size == 0:
            continue
        for c in range(C):
            x0, x1 = (ox + c * side) // pool, -(-(ox + (c + 1) * side) // pool)
            blk = band[:, x0:x1]
            if blk.size:
                out[r, c] = float(blk.min())
    return out


def measure(fwd, rev, lab, um):
    onsheet = (fwd > 0) | (rev > 0)
    side = rule55.unit_side(um)
    origin, _ = rule55.best_origin(onsheet, side)
    t = rule55.unit_table(fwd, rev, onsheet, side, origin)
    dsmall, pool = pooled_distance_um(lab, um)
    # a unit's distance is the MINIMUM over its pixels: "is any part of this unit near text?"
    dmin = unit_min_distance(dsmall, pool, t["margin"].shape, side, origin)
    v = t["valid"]; m = t["margin"]
    out = dict(um=float(um), side_px=int(side), origin=[int(origin[0]), int(origin[1])], pool=POOL,
               n_valid=int(v.sum()), bar=BAR, min_band_n=MIN_BAND_N, bands=[])
    for (lo, hi), name in zip(BANDS, BAND_NAMES):
        sel = v & ((dmin == 0.0) if hi == 0.0 else ((dmin > lo) & (dmin <= hi)))
        row = dict(band=name, lo_um=lo, hi_um=(None if hi == float("inf") else hi), n=int(sel.sum()))
        if sel.sum():
            row.update(median_margin=float(np.median(m[sel])), mean_margin=float(np.mean(m[sel])),
                       median_fwd=float(np.median(t["fwd_mean"][sel])), n_flagged=int(t["flagged"][sel].sum()))
        out["bands"].append(row)
    powered = [b for b in out["bands"] if b["n"] >= MIN_BAND_N and b["band"] != "touching ink"]
    if not powered:
        out["outcome"] = "UNDERPOWERED"
        out["outcome_reason"] = "no band beyond 'touching ink' has >= %d units" % MIN_BAND_N
    else:
        far = powered[-1]
        if far["median_margin"] <= BAR:
            out["outcome"] = "FLOOR-EXPLAINED-BY-UNLABELLED-INK"
            out["outcome_reason"] = ("the outermost powered band (%s, n=%d) has median margin %+.4f <= the bar %+.4f"
                                     % (far["band"], far["n"], far["median_margin"], BAR))
        elif all(b["median_margin"] > BAR for b in powered):
            out["outcome"] = "FLOOR-NOT-EXPLAINED-BY-PROXIMITY"
            out["outcome_reason"] = ("every powered band stays above the bar %+.4f (outermost %s, n=%d, %+.4f)"
                                     % (BAR, far["band"], far["n"], far["median_margin"]))
        else:
            out["outcome"] = "MIXED"
            out["outcome_reason"] = ("the outermost powered band (%s, n=%d, %+.4f) is above the bar but an inner one "
                                     "is not; neither declared outcome is met"
                                     % (far["band"], far["n"], far["median_margin"], ))
    return out, dmin, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forward", default=os.path.join(D, "gates", "gateA", "w040_full_plain.tif"))
    ap.add_argument("--reverse", default=os.path.join(D, "gates", "gateA", "w040_full_plain_reverse.tif"))
    ap.add_argument("--labels", default=os.path.join(D, "labels", "w040", "w040_inklabels.zarr"))
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--out", default=os.path.join(D, "gates", "rblank", "rblank2.json"))
    a = ap.parse_args()
    fwd = tifffile.imread(a.forward); rev = tifffile.imread(a.reverse)
    lab = rblank.labels_any_over_z(a.labels, fwd.shape)
    out, dmin, t = measure(fwd, rev, lab, a.um)
    out["inputs"] = dict(forward=a.forward, reverse=a.reverse, labels=a.labels, projection="any_over_z")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    print("valid units %d ; grid side %d origin %s ; bar %+.4f" % (out["n_valid"], out["side_px"], out["origin"], BAR))
    print("%-14s %4s %12s %12s %9s" % ("band", "n", "med_margin", "med_fwd", "flagged"))
    for b in out["bands"]:
        if not b["n"]:
            print("%-14s %4d   (none)" % (b["band"], 0)); continue
        print("%-14s %4d %+12.4f %12.4f %9d" % (b["band"], b["n"], b["median_margin"], b["median_fwd"], b["n_flagged"]))
    print("\nOUTCOME: %s -- %s" % (out["outcome"], out["outcome_reason"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
