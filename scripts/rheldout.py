#!/usr/bin/env python
"""rheldout.py -- RULES.md R-HELDOUT: the reader on known text from a scroll the model never saw (PHerc0841).

Written and tested BEFORE any held-out output existed (R-HELDOUT was declared 2026-10-15, commit 661ff64). Nothing
here is tuned: the frozen rule 5.5 (`rule55.evaluate`, unit_origin="auto"), the standard on-sheet mask (pooled CT
middle slice > 0) and the declared bars are applied to each segment as they come.

Per segment directory (layout written by the R-HELDOUT runner):
  pooled.zarr                        21-slice input (group, array "0", z y x uint8), from prepare_9um_isotropic_input
  pred.tif, pred_reverse.tif         ink_9um maps, both depth orders (uint8 = p x 255)
  labels/inklabels.zarr/2            level 2 of the 2.403 um labels (> 0 = ink); same canvas as pooled.zarr
  labels/supervision.zarr/2          level 2 of the supervision mask (> 0 = supervised)
Measures (R-HELDOUT): pixel ROC AUC of both maps on supervised pixels, per segment and pooled; the frozen rule in
both depth orders; every valid unit's labelled ink fraction phi and supervised fraction; flag rates on text-bearing
units (phi >= 0.02) and on supervised blank units (phi == 0, >= 50 % supervised) with exact 95 % intervals.
Bars: HELDOUT-AUC  TRANSFERS (pooled forward AUC >= 0.75 and reverse <= 0.60) / NO TRANSFER (forward < 0.60) / PARTIAL
      HELDOUT-RULE STRONG (a >= 3 cluster on any segment) / PASS (>= 1 flagged valid unit) / BLIND (none)
usage: rheldout.py <segment_dir> [...] --um 9.612 --json out.json
"""
import argparse, json, os, sys
import numpy as np, tifffile, zarr
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rule55  # noqa: E402
from release_stats import clopper_pearson  # noqa: E402

UM = 2.403 * 4                 # level 2 of a 2.403 um volume
PHI_TEXT, SUP_BLANK = 0.02, 0.50
AUC_TRANSFER, AUC_REV_MAX, AUC_NONE = 0.75, 0.60, 0.60


def level(path, lvl="2"):
    g = zarr.open_group(path, mode="r")
    return np.asarray(g[lvl])


def ct_mid(pooled):
    g = zarr.open_group(pooled, mode="r")
    a = g["0"] if "0" in g else g[sorted(g.keys())[0]]
    return np.asarray(a[a.shape[0] // 2])


def load_segment(d):
    fwd = tifffile.imread(os.path.join(d, "pred.tif")); rev = tifffile.imread(os.path.join(d, "pred_reverse.tif"))
    fwd, rev = (m[0] if m.ndim == 3 else m for m in (fwd, rev))
    ink = level(os.path.join(d, "labels", "inklabels.zarr")) > 0
    sup = level(os.path.join(d, "labels", "supervision.zarr")) > 0
    ct = ct_mid(os.path.join(d, "pooled.zarr"))
    shapes = {fwd.shape, rev.shape, ink.shape, sup.shape, ct.shape}
    if len(shapes) != 1:
        raise SystemExit("%s: canvases differ %s" % (d, sorted(shapes)))
    return fwd, rev, ink, sup, ct


def unit_rows(table, ink, sup):
    oy, ox = table["origin"]; s = int(table["side_px"])
    rows = []
    for u in table["valid_units"]:
        y0, x0 = oy + u["row"] * s, ox + u["col"] * s
        rows.append(dict(u, phi=float(ink[y0:y0 + s, x0:x0 + s].mean()), sup_frac=float(sup[y0:y0 + s, x0:x0 + s].mean())))
    return rows


def rate(units, pred):
    sel = [u for u in units if pred(u)]
    k = sum(1 for u in sel if u["flagged"])
    lo, hi = clopper_pearson(k, len(sel)) if sel else (None, None)
    return dict(n=len(sel), flagged=k, cp95=[lo, hi])


def segment_result(d, um=UM):
    fwd, rev, ink, sup, ct = load_segment(d)
    onsheet = ct > 0
    y = ink[sup]
    out = dict(segment=os.path.basename(os.path.normpath(d)), shape=list(fwd.shape), um_per_px=um,
               onsheet_cm2=round(rule55.px_to_cm2(onsheet.sum(), um), 4), n_supervised=int(sup.sum()), n_ink=int(y.sum()),
               nonzero_forward=float((fwd > 0).mean()), nonzero_reverse=float((rev > 0).mean()))
    for name, m in (("forward", fwd), ("reverse", rev)):
        p = m[sup].astype(np.float64) / 255.0
        out["auc_" + name] = float(roc_auc_score(y, p)) if 0 < y.sum() < y.size else None
        out["mean_on_ink_" + name] = float(p[y].mean()) if y.any() else None
        out["mean_on_blank_" + name] = float(p[~y].mean()) if (~y).any() else None
    res, tables = rule55.evaluate(fwd, rev, onsheet, um, unit_origin="auto")
    sw = rule55.evaluate(rev, fwd, onsheet, um, row_check=False, unit_origin="auto")[0]
    h = res["units"]["0.5cm2"]
    units = unit_rows(dict(h, origin=tables["0.5cm2"]["origin"]), ink, sup)
    out.update(verdict=res["verdict"], verdict_reason=res["verdict_reason"], n_valid=h["n_valid"], n_flagged=h["n_flagged"],
               cluster_sizes=h["cluster_sizes"], largest_cluster=h["largest_cluster"], grid_origin=list(tables["0.5cm2"]["origin"]),
               swapped_n_flagged=sw["units"]["0.5cm2"]["n_flagged"], swapped_cluster_sizes=sw["units"]["0.5cm2"]["cluster_sizes"],
               units=units,
               text_units=rate(units, lambda u: u["phi"] >= PHI_TEXT),
               blank_units=rate(units, lambda u: u["phi"] == 0.0 and u["sup_frac"] >= SUP_BLANK))
    return out, (y, fwd[sup], rev[sup])


def verdicts(segs, pooled_auc_f, pooled_auc_r):
    if pooled_auc_f is not None and pooled_auc_f >= AUC_TRANSFER and pooled_auc_r is not None and pooled_auc_r <= AUC_REV_MAX:
        auc = "TRANSFERS"
    elif pooled_auc_f is None or pooled_auc_f < AUC_NONE:
        auc = "NO TRANSFER"
    else:
        auc = "PARTIAL"
    if any(s["largest_cluster"] >= rule55.MIN_CLUSTER for s in segs):
        rule = "STRONG"
    elif sum(s["n_flagged"] for s in segs):
        rule = "PASS"
    else:
        rule = "BLIND"
    return auc, rule


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments", nargs="+"); ap.add_argument("--um", type=float, default=UM); ap.add_argument("--json")
    a = ap.parse_args(argv)
    segs, ys, fs, rs = [], [], [], []
    for d in a.segments:
        s, (y, f, r) = segment_result(d, a.um)
        segs.append(s); ys.append(y); fs.append(f); rs.append(r)
        print("%-46s AUC fwd %.4f rev %.4f | valid %d flagged %d clusters %s | swapped flagged %d | text units %d/%d | blank units %d/%d | %s"
              % (s["segment"][:46], s["auc_forward"] or float("nan"), s["auc_reverse"] or float("nan"), s["n_valid"], s["n_flagged"],
                 s["cluster_sizes"], s["swapped_n_flagged"], s["text_units"]["flagged"], s["text_units"]["n"],
                 s["blank_units"]["flagged"], s["blank_units"]["n"], s["verdict"]))
    y = np.concatenate(ys); f = np.concatenate(fs).astype(np.float64) / 255.0; r = np.concatenate(rs).astype(np.float64) / 255.0
    pf = float(roc_auc_score(y, f)) if 0 < y.sum() < y.size else None
    pr = float(roc_auc_score(y, r)) if 0 < y.sum() < y.size else None
    allu = [u for s in segs for u in s["units"]]
    tot = dict(n_supervised=int(y.size), n_ink=int(y.sum()), auc_forward=pf, auc_reverse=pr,
               n_valid=sum(s["n_valid"] for s in segs), n_flagged=sum(s["n_flagged"] for s in segs),
               swapped_n_flagged=sum(s["swapped_n_flagged"] for s in segs),
               text_units=rate(allu, lambda u: u["phi"] >= PHI_TEXT),
               blank_units=rate(allu, lambda u: u["phi"] == 0.0 and u["sup_frac"] >= SUP_BLANK),
               all_units=rate(allu, lambda u: True))
    auc_v, rule_v = verdicts(segs, pf, pr)
    out = dict(declared="RULES.md R-HELDOUT (commit 661ff64)", um_per_px=a.um, phi_text=PHI_TEXT, sup_blank=SUP_BLANK,
               bars=dict(auc_transfer=AUC_TRANSFER, auc_rev_max=AUC_REV_MAX, auc_none=AUC_NONE, min_cluster=rule55.MIN_CLUSTER),
               segments=segs, pooled=tot, HELDOUT_AUC=auc_v, HELDOUT_RULE=rule_v)
    print("POOLED  AUC fwd %s rev %s | valid %d flagged %d (swapped %d) | text units %d/%d CP95 %s | blank units %d/%d"
          % (pf, pr, tot["n_valid"], tot["n_flagged"], tot["swapped_n_flagged"], tot["text_units"]["flagged"], tot["text_units"]["n"],
             tot["text_units"]["cp95"], tot["blank_units"]["flagged"], tot["blank_units"]["n"]))
    print("HELDOUT-AUC: %s   HELDOUT-RULE: %s" % (auc_v, rule_v))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
