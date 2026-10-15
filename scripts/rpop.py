#!/usr/bin/env python
"""rpop.py -- RULES R-POP: corpus 0.5 cm2 units against the R-CTRL55 control population. Descriptive only."""
import glob, json, os, sys
import numpy as np
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA


def table(d, key):
    r = d.get(key) or {}
    return (r.get("units") or r).get("0.5cm2") or {}


def units_of(stats_path):
    """Valid 0.5 cm2 units in the FORWARD depth order.

    DEFECT WORKED AROUND 2026-09-19 03:25 UTC: 41 of the 50 reads that carry a rule 5.5 table have a correct
    `n_valid` but an EMPTY `valid_units` list in the forward table, while their `rule55_depth_swapped` table
    carries the full list (those reads also carry a `flagged_any_grid` key, so they were summarised by a later
    path). The swapped table is the exact mirror -- margin negated, fwd_mean and rev_mean exchanged, verified
    unit by unit on the reads where both lists are populated -- so the forward population is reconstructed from
    it exactly, not approximated. Without this, the corpus population is a biased subsample of 9 reads.
    """
    d = json.load(open(stats_path))
    t = table(d, "rule55")
    us = t.get("valid_units", [])
    if us:
        return us, d, "direct"
    ts = table(d, "rule55_depth_swapped")
    sw = ts.get("valid_units", [])
    if not sw:
        return [], d, "none"
    if t.get("n_valid") is not None and ts.get("n_valid") is not None and t["n_valid"] != ts["n_valid"]:
        return [], d, "mismatch"
    return [dict(row=u["row"], col=u["col"], onsheet_frac=u.get("onsheet_frac"),
                 fwd_mean=u["rev_mean"], rev_mean=u["fwd_mean"], margin=-u["margin"],
                 flagged=None) for u in sw], d, "mirrored"


def describe(name, f, m):
    if not len(f):
        print("%-34s n=0" % name); return None
    q = lambda a, p: float(np.percentile(a, p))
    iqr = q(m, 75) - q(m, 25)
    print("%-34s n=%4d | fwd med %.4f IQR %.4f [%.4f..%.4f] | margin med %+.4f IQR %.4f [%+.4f..%+.4f]"
          % (name, len(f), q(f, 50), q(f, 75) - q(f, 25), f.min(), f.max(), q(m, 50), iqr, m.min(), m.max()))
    return dict(n=len(f), fwd_med=q(f, 50), fwd_iqr=q(f, 75) - q(f, 25), mar_med=q(m, 50), mar_iqr=iqr,
                mar_min=float(m.min()), mar_max=float(m.max()), fwd_min=float(f.min()), fwd_max=float(f.max()))


def main():
    ctl = json.load(open(os.path.join(D, "gates", "rctrl55", "rctrl55.json")))["table"]["valid_units"]
    cf = np.array([u["fwd_mean"] for u in ctl]); cm = np.array([u["margin"] for u in ctl])
    fl = np.array([bool(u["flagged"]) for u in ctl])
    print("== CONTROL (w040 known text, full canvas, R-CTRL55, same code path as a corpus read) ==")
    describe("control ALL valid units", cf, cm)
    ctl_flag = describe("control FLAGGED (text)", cf[fl], cm[fl])
    ctl_un = describe("control UNFLAGGED (reference)", cf[~fl], cm[~fl])

    pops = {"plain": ([], []), "tta": ([], [])}
    n_reads = {"plain": 0, "tta": 0}
    srcs = {}
    for sp in sorted(glob.glob(os.path.join(D, "patches", "*", "*", "read_*", "read_stats.json"))):
        recipe = "tta" if sp.split("/")[-2].endswith("_tta") else "plain"
        us, d, how = units_of(sp)
        srcs[how] = srcs.get(how, 0) + 1
        if not us:
            continue
        n_reads[recipe] += 1
        for u in us:
            pops[recipe][0].append(u["fwd_mean"]); pops[recipe][1].append(u["margin"])
    print("\n== CORPUS ==")
    print("  unit lists taken: %s" % ", ".join("%s %d" % kv for kv in sorted(srcs.items())))
    out = {"unit_list_sources": srcs}
    for k in ("plain", "tta"):
        f = np.array(pops[k][0]); m = np.array(pops[k][1])
        out[k] = describe("corpus %s (%d reads)" % (k, n_reads[k]), f, m)

    print("\n== BARS (corpus plain vs control UNFLAGGED) ==")
    cp = out["plain"]
    if cp and ctl_un:
        dmed = cp["mar_med"] - ctl_un["mar_med"]
        ratio = cp["mar_iqr"] / ctl_un["mar_iqr"] if ctl_un["mar_iqr"] else float("inf")
        print("  margin median difference: %+.4f   (POP-SHIFT if |.| > 0.02)" % dmed)
        print("  margin IQR ratio corpus/control: %.3f   (POP-NARROW if < 0.5; POP-MATCH needs 0.5-2.0)" % ratio)
        verdicts = []
        if abs(dmed) <= 0.02 and 0.5 <= ratio <= 2.0:
            verdicts.append("POP-MATCH")
        if ratio < 0.5:
            verdicts.append("POP-NARROW")
        if abs(dmed) > 0.02:
            verdicts.append("POP-SHIFT (%+.4f)" % dmed)
        print("  OUTCOME: %s" % ", ".join(verdicts))
        out["bars"] = dict(margin_median_diff=dmed, margin_iqr_ratio=ratio, outcome=verdicts)
    os.makedirs(os.path.join(D, "gates", "rpop"), exist_ok=True)
    json.dump(dict(control_all=describe.__name__ and None, control_flagged=ctl_flag, control_unflagged=ctl_un,
                   corpus=out), open(os.path.join(D, "gates", "rpop", "rpop.json"), "w"), indent=1)
    print("\nwrote %s" % os.path.join(D, "gates", "rpop", "rpop.json"))


if __name__ == "__main__":
    main()
