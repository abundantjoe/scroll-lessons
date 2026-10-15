#!/usr/bin/env python
"""rctrl55.py -- RULES R-CTRL55: run the FROZEN rule 5.5 on the w040 known-text control's full canvas.

Nothing here is tuned. rule55.evaluate is called with its defaults; the only choices are the on-sheet mask
(the maps' own valid footprint) and the grid origin, which the frozen best_origin picks from the mask alone.
"""
import argparse, json, os, sys
import numpy as np, tifffile, zarr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA


def label_slice(path, z):
    g = zarr.open_group(path, mode="r")
    a = g["0"] if "0" in g else g
    return np.asarray(a[z])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forward", default=os.path.join(D, "gates", "gateA", "w040_full_plain.tif"))
    ap.add_argument("--reverse", default=os.path.join(D, "gates", "gateA", "w040_full_plain_reverse.tif"))
    ap.add_argument("--labels", default=os.path.join(D, "labels", "w040", "w040_inklabels.zarr"))
    ap.add_argument("--slice", type=int, default=14)
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--out", default=os.path.join(D, "gates", "rctrl55", "rctrl55.json"))
    a = ap.parse_args()

    fwd = tifffile.imread(a.forward); rev = tifffile.imread(a.reverse)
    assert fwd.shape == rev.shape, (fwd.shape, rev.shape)
    onsheet = (fwd > 0) | (rev > 0)
    print("maps %s ; on-sheet footprint %d px = %.2f cm2 (%.1f %% of canvas)"
          % (fwd.shape, onsheet.sum(), rule55.px_to_cm2(onsheet.sum(), a.um), 100.0 * onsheet.mean()))

    # DEFECT FIXED 2026-09-19 03:05 UTC: evaluate() takes unit_origin as the STRING "auto"/"fixed"; the first version
    # of this script passed the best_origin TUPLE, which fell into the else branch and silently tiled from (0, 0) while
    # the log line claimed (94, 188). "auto" is what every corpus read uses (read_chart's default), so "auto" it is.
    side = rule55.unit_side(a.um)
    origin, n_best = rule55.best_origin(onsheet, side)
    print("frozen best_origin (mask only): %s -> %d valid units at %d px" % (origin, n_best, side))
    res, _tables = rule55.evaluate(fwd, rev, onsheet, a.um, unit_origin="auto")
    assert tuple(res["grid_origins"]["0.5cm2"]) == tuple(origin), (res["grid_origins"], origin)
    tab = (res.get("units") or res)["0.5cm2"]

    lab = label_slice(a.labels, a.slice) > 128
    oy, ox = tuple(tab.get("origin", (0, 0))); s = int(tab["side_px"])
    for u in tab.get("valid_units", []):
        y0, x0 = oy + u["row"] * s, ox + u["col"] * s
        u["phi_label_ink"] = float(lab[y0:y0 + s, x0:x0 + s].mean())

    us = sorted(tab.get("valid_units", []), key=lambda u: -u["phi_label_ink"])
    print("\nvalid units %d ; FLAGGED %d ; clusters %s ; largest cluster %s"
          % (tab["n_valid"], tab["n_flagged"], tab.get("cluster_sizes"), tab.get("largest_cluster")))
    print("\nthe 15 units with the most labelled ink (phi = true ink area fraction of the unit):")
    print("%4s %4s %8s %8s %8s %9s  %s" % ("row", "col", "phi", "fwd", "rev", "margin", "flagged"))
    for u in us[:15]:
        print("%4d %4d %8.4f %8.4f %8.4f %+9.4f  %s"
              % (u["row"], u["col"], u["phi_label_ink"], u["fwd_mean"], u["rev_mean"], u["margin"], u["flagged"]))
    inked = [u for u in us if u["phi_label_ink"] >= 0.02]
    print("\nunits with phi >= 0.02 (i.e. genuinely text-bearing): %d ; of those flagged: %d"
          % (len(inked), sum(1 for u in inked if u["flagged"])))
    if inked:
        print("  their forward mean %.4f, margin mean %+.4f, best margin %+.4f"
              % (np.mean([u["fwd_mean"] for u in inked]), np.mean([u["margin"] for u in inked]),
                 max(u["margin"] for u in inked)))
    verdict = ("CTRL55-STRONG" if (tab.get("largest_cluster") or 0) >= rule55.MIN_CLUSTER
               else "CTRL55-PASS" if tab["n_flagged"] >= 1 else "CTRL55-BLIND")
    print("\nOUTCOME: %s" % verdict)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(dict(outcome=verdict, forward=a.forward, reverse=a.reverse, um=a.um, origin=list(origin),
                   onsheet_px=int(onsheet.sum()), table=tab, thresholds=rule55.THRESHOLDS),
              open(a.out, "w"), indent=1)
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
