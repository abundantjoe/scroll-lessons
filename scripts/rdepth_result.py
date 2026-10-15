#!/usr/bin/env python
"""RULES R-DEPTH scorer. Reads the three windows' AUC json and answers the bar exactly as declared.

M(w) = mean forward on labelled ink - mean reverse on labelled ink (the Gate B / rule 5.5 convention).
ADMITTED if max(M(low), M(high)) >= M(centre) + 0.05, OR if min(M(low), M(high)) / M(centre) <= 0.50.
FAILS (depth offset closed) if M(centre) is the best AND that ratio > 0.50.
A window whose runs are not both present is reported as pending; the bar is not called until all three are in.
"""
import json, os, sys
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

OUT = DATA + "/gates/rdepth"
GATEB = DATA + "/gates/gateB"
# (name, forward json, reverse json, window centre slice, offset in slices)
WINDOWS = [
    ("low",    os.path.join(OUT, "auc_low.json"),             os.path.join(OUT, "auc_low_reverse.json"),             8,  -6),
    ("centre", os.path.join(GATEB, "auc_render_plain.json"),  os.path.join(GATEB, "auc_render_plain_reverse.json"),  14,  0),
    ("high",   os.path.join(OUT, "auc_high.json"),            os.path.join(OUT, "auc_high_reverse.json"),            19, +5),
]
UM_PER_SLICE = 9.362
MARGIN_GAIN_MIN = 0.05   # RULES R-DEPTH bar 1
RETAINED_MAX = 0.50      # RULES R-DEPTH bar 2


def load(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def main():
    rows, pending = [], []
    for name, fp, rp, centre, off in WINDOWS:
        f, r = load(fp), load(rp)
        if not f or not r or f.get("mean_on_ink") is None or r.get("mean_on_ink") is None:
            pending.append(name)
            rows.append(dict(window=name, centre_slice=centre, offset_slices=off, pending=True))
            continue
        rows.append(dict(window=name, centre_slice=centre, offset_slices=off, pending=False,
                         offset_um=round(off * UM_PER_SLICE, 1),
                         margin_on_ink=round(f["mean_on_ink"] - r["mean_on_ink"], 5),
                         auc_forward=round(f["auc"], 5), auc_reverse=round(r["auc"], 5),
                         fwd_on_ink=round(f["mean_on_ink"], 5), fwd_on_blank=round(f["mean_on_blank"], 5),
                         separation=round(f["mean_on_ink"] - f["mean_on_blank"], 5),
                         n_ink=f["n_ink"], n_blank=f["n_blank"]))
    res = dict(control="gates/gateB/render.zarr (our render of the w040 mesh crop)",
               checkpoint="hybrid_3d2d-seed42/step-075000.pth", tta=False,
               statistic="mean forward on labelled ink - mean reverse on labelled ink",
               bars=dict(margin_gain_min=MARGIN_GAIN_MIN, retained_max=RETAINED_MAX), windows=rows)
    print("RULES R-DEPTH: the reader's 17-slice window swept across the 28-slice control render")
    print("  %-7s %8s %9s %9s %9s %9s" % ("window", "offset", "margin", "AUC fwd", "AUC rev", "fwd sep"))
    for w in rows:
        if w["pending"]:
            print("  %-7s %8s   pending" % (w["window"], "%+d sl" % w["offset_slices"]))
        else:
            print("  %-7s %8s %9.5f %9.5f %9.5f %9.5f" % (w["window"], "%+d sl" % w["offset_slices"],
                  w["margin_on_ink"], w["auc_forward"], w["auc_reverse"], w["separation"]))
    if pending:
        res["verdict"] = "PENDING"
        res["pending_windows"] = pending
        print("  bar NOT YET DECIDABLE: %s still running" % ", ".join(pending))
    else:
        m = {w["window"]: w["margin_on_ink"] for w in rows}
        gain = max(m["low"], m["high"]) - m["centre"]
        retained = min(m["low"], m["high"]) / m["centre"] if m["centre"] else float("nan")
        by_gain = gain >= MARGIN_GAIN_MIN
        by_selectivity = retained <= RETAINED_MAX
        res.update(margin_gain=round(gain, 5), retained_ratio=round(retained, 4),
                   admitted_by_gain=bool(by_gain), admitted_by_selectivity=bool(by_selectivity),
                   verdict="ADMITTED" if (by_gain or by_selectivity) else "FAILED")
        print("  best off-centre minus centre = %+0.5f (bar: >= %+0.2f)  -> %s"
              % (gain, MARGIN_GAIN_MIN, "ADMITS" if by_gain else "does not admit"))
        print("  worst off-centre / centre    =  %0.4f (bar: <= %0.2f)  -> %s"
              % (retained, RETAINED_MAX, "ADMITS" if by_selectivity else "does not admit"))
        print("  R-DEPTH %s" % res["verdict"])
        if res["verdict"] == "FAILED":
            print("  depth offset is CLOSED: the response is centred and broad, so the 135 reads at offset 0")
            print("  lose nothing to mis-centring within a sheet. This says nothing about a wrong-wrap trace.")
    json.dump(res, open(os.path.join(OUT, "rdepth.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
