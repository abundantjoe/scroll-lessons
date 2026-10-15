#!/usr/bin/env python
"""rblank.py -- RULES R-BLANK: what does this detector return on LABELLED-BLANK control papyrus?

Declared in RULES before it was run. Nothing here is tuned and no threshold is chosen here: the grid is the one
R-CTRL55 recorded (frozen best_origin on the mask alone), the maps are the ones R-CTRL55 scored, and the decision
bar (+0.0042) is fixed in the declaration.

The statistic is the MEDIAN MARGIN of valid 0.5 cm^2 units whose labelled ink fraction is exactly 0.000, projecting
the published 28-slice label volume to 2D by ANY OVER Z (the conservative projection: it can only shrink the set of
units called blank).
"""
import argparse, json, os, sys
import numpy as np, tifffile, zarr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA
MIN_BLANK_UNITS = 5          # fewer than this -> UNDERPOWERED, declared in RULES
CORPUS_MARGIN = 0.0014       # R-POP's recorded corpus whole-map margin
BASELINE_BAR = 3.0 * CORPUS_MARGIN


def labels_any_over_z(path, shape):
    """2D mask: any labelled ink pixel at any z of the published label volume."""
    g = zarr.open_group(path, mode="r")
    a = g["0"] if "0" in g else g
    assert a.shape[1:] == shape, (a.shape, shape)
    out = np.zeros(shape, bool)
    for z in range(a.shape[0]):
        out |= np.asarray(a[z]) > 128
    return out


def measure(fwd, rev, lab, um):
    onsheet = (fwd > 0) | (rev > 0)
    side = rule55.unit_side(um)
    origin, _ = rule55.best_origin(onsheet, side)
    t = rule55.unit_table(fwd, rev, onsheet, side, origin)
    n_on = t["onsheet_frac"] * float(side * side)
    phi = rule55.block_sums(lab.astype(np.uint8), side, onsheet, origin=origin)
    with np.errstate(invalid="ignore", divide="ignore"):
        phi = phi / n_on
    v = t["valid"]
    blank = v & (np.nan_to_num(phi, nan=1.0) == 0.0)
    inked = v & (np.nan_to_num(phi, nan=0.0) > 0.0)
    m = t["margin"]
    out = dict(um=float(um), side_px=int(side), origin=[int(origin[0]), int(origin[1])],
               n_valid=int(v.sum()), n_flagged=int(t["flagged"].sum()),
               n_blank_units=int(blank.sum()), n_inked_units=int(inked.sum()),
               corpus_margin=CORPUS_MARGIN, baseline_bar=BASELINE_BAR, min_blank_units=MIN_BLANK_UNITS)
    for name, sel in (("blank", blank), ("inked", inked), ("all_valid", v)):
        if sel.sum():
            out[name] = dict(n=int(sel.sum()),
                             median_margin=float(np.median(m[sel])),
                             mean_margin=float(np.mean(m[sel])),
                             p10_margin=float(np.percentile(m[sel], 10)),
                             p90_margin=float(np.percentile(m[sel], 90)),
                             median_fwd=float(np.median(t["fwd_mean"][sel])),
                             median_rev=float(np.median(t["rev_mean"][sel])),
                             n_flagged=int(t["flagged"][sel].sum()),
                             median_phi=float(np.median(phi[sel])))
        else:
            out[name] = dict(n=0)
    if out["n_blank_units"] < MIN_BLANK_UNITS:
        out["outcome"] = "UNDERPOWERED"
        out["outcome_reason"] = ("only %d valid unit(s) have labelled ink fraction 0.000; the declaration requires >= %d"
                                 % (out["n_blank_units"], MIN_BLANK_UNITS))
    else:
        b = out["blank"]["median_margin"]
        out["outcome"] = "DETECTOR-FLOOR-AT-OR-BELOW-CORPUS" if b <= BASELINE_BAR else "DETECTOR-FLOOR-ABOVE-CORPUS"
        out["outcome_reason"] = ("blank baseline %+.4f %s the declared bar %+.4f (3 x the corpus %+.4f)"
                                 % (b, "<=" if b <= BASELINE_BAR else ">", BASELINE_BAR, CORPUS_MARGIN))
    return out, phi, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forward", default=os.path.join(D, "gates", "gateA", "w040_full_plain.tif"))
    ap.add_argument("--reverse", default=os.path.join(D, "gates", "gateA", "w040_full_plain_reverse.tif"))
    ap.add_argument("--labels", default=os.path.join(D, "labels", "w040", "w040_inklabels.zarr"))
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--out", default=os.path.join(D, "gates", "rblank", "rblank.json"))
    a = ap.parse_args()

    fwd = tifffile.imread(a.forward); rev = tifffile.imread(a.reverse)
    assert fwd.shape == rev.shape, (fwd.shape, rev.shape)
    lab = labels_any_over_z(a.labels, fwd.shape)
    print("maps %s ; labelled ink %.4f of canvas (any over z)" % (fwd.shape, lab.mean()))
    out, phi, t = measure(fwd, rev, lab, a.um)
    out["inputs"] = dict(forward=a.forward, reverse=a.reverse, labels=a.labels, projection="any_over_z")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)

    print("grid: side %d px, origin %s (frozen best_origin)" % (out["side_px"], out["origin"]))
    print("valid units %d ; flagged %d ; labelled-BLANK %d ; labelled-INKED %d"
          % (out["n_valid"], out["n_flagged"], out["n_blank_units"], out["n_inked_units"]))
    print("%-10s %4s %10s %10s %10s %10s %10s %8s" % ("set", "n", "med_margin", "p10", "p90", "med_fwd", "med_phi", "flagged"))
    for name in ("blank", "inked", "all_valid"):
        s = out[name]
        if not s["n"]:
            print("%-10s %4d  (none)" % (name, 0)); continue
        print("%-10s %4d %+10.4f %+10.4f %+10.4f %10.4f %10.4f %8d"
              % (name, s["n"], s["median_margin"], s["p10_margin"], s["p90_margin"], s["median_fwd"], s["median_phi"], s["n_flagged"]))
    print("\ncorpus comparator (R-POP, recorded before this run): %+.4f ; declared bar %+.4f" % (CORPUS_MARGIN, BASELINE_BAR))
    print("OUTCOME: %s -- %s" % (out["outcome"], out["outcome_reason"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
