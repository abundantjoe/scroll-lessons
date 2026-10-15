#!/usr/bin/env python
"""RULES R-5.5 self-test on the w028 pooled maps: the frozen unit rule must flag the units the judge reference calls
text and none it calls blank. Unit classes come ONLY from the judge reference (team 2.4 um map pooled 4x4, /255):
text unit = >= 50 % of the unit's pixels have reference >= 0.40; blank unit = >= 90 % have reference <= 0.25;
only valid units (>= 90 % on-sheet); units containing any label-excluded pixel are reported separately.
usage: w028_rule55_selftest.py --ref <judge ref dir> --forward F.tif --reverse R.tif [--json out]
"""
import argparse, json, os, sys
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55

def classes(ref_dir, side, onsheet):
    ref = np.load(os.path.join(ref_dir, "reference_u8.npy")).astype(np.float32) / 255.0
    excl = np.load(os.path.join(ref_dir, "excluded_mask.npy"))
    n = float(side * side)
    f_text = rule55.block_sums((ref >= rule55_TEXT).astype(np.uint8), side) / n
    f_blank = rule55.block_sums((ref <= rule55_BLANK).astype(np.uint8), side) / n
    has_excl = rule55.block_sums(excl.astype(np.uint8), side) > 0
    return f_text >= 0.5, f_blank >= 0.9, has_excl

rule55_TEXT, rule55_BLANK = 0.40, 0.25  # judge constants (w028_judge.py), frozen

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ref", required=True); ap.add_argument("--forward", required=True)
    ap.add_argument("--reverse", required=True); ap.add_argument("--json"); a = ap.parse_args()
    meta = json.load(open(os.path.join(a.ref, "meta.json"))); um = meta["um"]
    onsheet = np.load(os.path.join(a.ref, "onsheet_mask.npy"))
    fwd = tifffile.imread(a.forward); rev = tifffile.imread(a.reverse)
    if fwd.ndim == 3: fwd = fwd[0]
    if rev.ndim == 3: rev = rev[0]
    assert fwd.shape == rev.shape == onsheet.shape, (fwd.shape, rev.shape, onsheet.shape)
    out = {"um": um, "forward": a.forward, "reverse": a.reverse, "thresholds": rule55.THRESHOLDS}
    for name, area in (("0.5cm2", 0.5), ("1cm2", 1.0)):
        side = rule55.unit_side(um, area)
        t = rule55.unit_table(fwd, rev, onsheet, side)
        text, blank, has_excl = classes(a.ref, side, onsheet)
        v, fl = t["valid"], t["flagged"]
        res = {"side_px": side, "n_valid": int(v.sum())}
        for tag, sel in (("all_valid", v), ("valid_no_label_excl", v & ~has_excl)):
            tx, bl = sel & text, sel & blank
            res[tag] = {"text_units": int(tx.sum()), "text_flagged": int((tx & fl).sum()),
                        "blank_units": int(bl.sum()), "blank_flagged": int((bl & fl).sum()),
                        "text_fwd_mean": float(np.nanmean(t["fwd_mean"][tx])) if tx.any() else None,
                        "text_margin_mean": float(np.nanmean(t["margin"][tx])) if tx.any() else None,
                        "blank_fwd_mean": float(np.nanmean(t["fwd_mean"][bl])) if bl.any() else None,
                        "blank_margin_mean": float(np.nanmean(t["margin"][bl])) if bl.any() else None}
        out[name] = res
    h = out["0.5cm2"]["all_valid"]
    out["bar_text_frac_ge_20_of_24"] = (h["text_flagged"] / h["text_units"] >= 20 / 24) if h["text_units"] else None
    out["bar_blank_zero_flagged"] = (h["blank_flagged"] == 0) if h["blank_units"] else None
    print(json.dumps(out, indent=1))
    if a.json: json.dump(out, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
