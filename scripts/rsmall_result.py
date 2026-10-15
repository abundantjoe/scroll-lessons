#!/usr/bin/env python
"""RULES R-SMALL: the readable fraction of interior traces grown at a reduced budget, against the declared bar.

Population, fixed in RULES before any trace: interior seeds only (r/R in [0.20, 0.55]), grown at 40 generations, in
patches/<scroll>_small. Traces grown at any other budget are EXCLUDED and counted in neither direction — the two
20-generation traces that showed the budget was too small stay on disk and are filtered out here by their own
`max_gen`, so the exclusion is checkable rather than asserted.

Readable = a trace that produced a chart, i.e. reached the reader and got a rule 5.5 verdict (BLANK, NOT ESTABLISHED
or PROMISING CANDIDATE). Not readable = stopped at QC or vetoed by R-CREST (VOID). That is the same measure the seeds
density gate was judged by (10 % -> 59 %).

Bar: >= 30 % readable over at least 15 traces, against the 60-generation interior baseline of 1 readable of 18 (5.6 %).

usage: rsmall_result.py [--gen 40] [--scrolls PHerc0826 PHerc0358]
"""
import argparse, glob, json, os, sys
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BAR_FRAC, BAR_N, BASELINE = 0.30, 15, (1, 18)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gen", type=int, default=40)
    ap.add_argument("--scrolls", nargs="*", default=["PHerc0826", "PHerc0358"])
    ap.add_argument("--patches", default=DATA + "/patches")
    a = ap.parse_args(argv)
    rows, excluded = [], []
    for sc in a.scrolls:
        for d in sorted(glob.glob(os.path.join(a.patches, f"{sc}_small", "auto_grown_*"))):
            try:
                mg = json.load(open(os.path.join(d, "meta.json"))).get("max_gen")
                area = json.load(open(os.path.join(d, "meta.json"))).get("area_cm2")
            except Exception:
                continue
            if mg != a.gen:
                excluded.append((sc, os.path.basename(d), mg, area)); continue
            qc = os.path.join(d, "qc.json")
            verdict = None
            for sp in glob.glob(os.path.join(d, "read_*", "read_stats.json")):
                verdict = json.load(open(sp)).get("verdict")
            qv = json.load(open(qc)).get("verdict") if os.path.exists(qc) else None
            if verdict:
                stage = "VOID" if str(verdict).startswith("VOID") else "read"
            elif qv in ("FAIL", "UNREADABLE"):
                stage = "qc " + qv                       # an outcome: the trace never reaches the reader
            else:
                stage = "pending"                        # not QC'd yet, or QC PASS and the read has not run
            rows.append(dict(scroll=sc, patch=os.path.basename(d), area_cm2=area, stage=stage, verdict=verdict))
    done = [r for r in rows if r["stage"] != "pending"]     # a QC PASS whose read has not run yet is not an outcome
    readable = [r for r in done if r["stage"] == "read"]
    print(f"R-SMALL at {a.gen} generations: {len(rows)} traces, {len(done)} with an outcome, {len(readable)} readable")
    if excluded:
        print(f"excluded (other budgets, counted in neither direction): {len(excluded)}")
        for e in excluded:
            print(f"   {e[0]} {e[1]} max_gen={e[2]} area={e[3]:.2f} cm2")
    for r in rows:
        print(f"  {r['scroll']:10} {r['patch']:32} {(r['area_cm2'] or 0):5.2f} cm2  {r['stage']:14} {str(r['verdict'] or '')[:22]}")
    if done:
        frac = len(readable) / len(done)
        print(f"\nreadable fraction {len(readable)}/{len(done)} = {frac:.1%}   baseline {BASELINE[0]}/{BASELINE[1]} = {BASELINE[0]/BASELINE[1]:.1%}")
        if len(done) < BAR_N:
            print(f"bar NOT YET DECIDABLE: {len(done)} outcomes, the bar needs at least {BAR_N}")
        else:
            print(f"bar >= {BAR_FRAC:.0%} over >= {BAR_N} traces: {'PASS' if frac >= BAR_FRAC else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
