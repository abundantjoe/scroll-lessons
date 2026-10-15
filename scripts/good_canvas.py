#!/usr/bin/env python
"""How much GEOMETRICALLY SOUND canvas has this project actually read?

Descriptive only. It gates nothing, changes no verdict and is not a bar. It answers one question that the raw
"cm2 read" figure does not: of the area that reached the ink model, how much of it was on a surface that a papyrus
sheet could physically be?

"Sound" here is the G-GP part 3 geometry bar -- at most 14.2 transverse self-intersections per cm2, ten times the
w040 known-text control's measured 1.42 -- taken from the R-CROSS census. Reads vetoed by R-CREST (VOID) never
reached the model and are excluded. The radial split uses R-RADIAL's per-read r/R median.
"""
import argparse, glob, json, os, sys
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BAR = 14.2
CONTROL = 1.42


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bar", type=float, default=BAR)
    ap.add_argument("--rcross", default=DATA + "/gates/rcross/rcross.json")
    ap.add_argument("--radial-glob", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records", "radial_*.json"))
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    rc = json.load(open(a.rcross))
    rate = {r["patch"]: r["per_cm2"] for pop in rc["rows"] for r in rc["rows"][pop] if r["per_cm2"] is not None}
    bands = {"inner": dict(n=0, cm2=0.0, verdicts={}), "outer": dict(n=0, cm2=0.0, verdicts={})}
    total_reads = reached = 0
    reached_cm2 = 0.0
    for f in sorted(glob.glob(a.radial_glob)):
        for r in json.load(open(f))["reads"]:
            total_reads += 1
            v = r.get("verdict") or ""
            if v.startswith("VOID"):
                continue
            reached += 1
            reached_cm2 += r.get("onsheet_cm2") or 0.0
            pr = rate.get(r["patch"])
            if pr is None or pr > a.bar:
                continue
            b = bands["inner" if r["r_over_R_median"] < 0.5 else "outer"]
            b["n"] += 1
            b["cm2"] += r.get("onsheet_cm2") or 0.0
            b["verdicts"][v] = b["verdicts"].get(v, 0) + 1
    good_cm2 = bands["inner"]["cm2"] + bands["outer"]["cm2"]
    print("Geometrically sound canvas actually read (descriptive; gates nothing)")
    print("  reads with a radial position on record: %d" % total_reads)
    print("  reached the ink model (non-VOID):       %d reads, %.1f cm2" % (reached, reached_cm2))
    print("  of those, on sound geometry (<= %.1f self-intersections/cm2, control %.2f): %d reads, %.1f cm2"
          % (a.bar, CONTROL, bands["inner"]["n"] + bands["outer"]["n"], good_cm2))
    for name in ("inner", "outer"):
        b = bands[name]
        print("      %s half of the radius: %d reads, %5.1f cm2   %s" % (name, b["n"], b["cm2"], b["verdicts"] or "-"))
    out = dict(bar_per_cm2=a.bar, control_per_cm2=CONTROL, total_reads=total_reads,
               reached_model=dict(n=reached, cm2=round(reached_cm2, 2)),
               sound=dict(n=bands["inner"]["n"] + bands["outer"]["n"], cm2=round(good_cm2, 2)), bands=bands)
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
