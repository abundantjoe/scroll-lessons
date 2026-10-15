#!/usr/bin/env python
"""RULES R-CROSS, the declared outcome split.

Bar as declared before the run: split OUR read traces at the team's pooled 90th-percentile crossing rate
(sites per cm2). The high group must be VOID-or-unreadable at >= 2x the low group's rate, with >= 30 traces on
EACH side. If either side has fewer than 30, or the ratio is below 2x, R-CROSS is recorded as a descriptive
statistic and gates nothing -- it is not retuned, re-split or re-run with other parameters.

"VOID-or-unreadable" is the same outcome measure R-SMALL and the seeds density gate were judged by: a trace that
never reached the reader (QC FAIL / UNREADABLE) or was vetoed by R-CREST (VOID). Traces with no outcome yet are
counted in neither direction.
"""
import glob, json, os, sys
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

G = DATA + "/gates/rcross"
PATCHES = DATA + "/patches"
BAR_RATIO, MIN_PER_SIDE = 2.0, 30


def outcome(patch_dir):
    """'unreadable' (VOID or stopped at QC), 'readable' (reached the reader), or None (no outcome yet)."""
    verdict = None
    for sp in sorted(glob.glob(os.path.join(patch_dir, "read_*", "read_stats.json"))):
        verdict = json.load(open(sp)).get("verdict")
    if verdict:
        return "unreadable" if str(verdict).startswith("VOID") else "readable"
    qc = os.path.join(patch_dir, "qc.json")
    if os.path.exists(qc):
        qv = json.load(open(qc)).get("verdict")
        if qv in ("FAIL", "UNREADABLE"):
            return "unreadable"
    return None


def find_patch_dir(name):
    for d in glob.glob(os.path.join(PATCHES, "*", name)):
        if os.path.exists(os.path.join(d, "x.tif")):
            return d
    return None


def main():
    data = json.load(open(os.path.join(G, "rcross.json")))
    team = data["summary"].get("team") or {}
    thr = team.get("p90_per_cm2")
    if thr is None:
        sys.exit("the team population has no p90 rate yet; run the census on it first")
    rows = []
    for r in data["rows"].get("ours", []):
        if r["per_cm2"] is None:
            continue
        d = find_patch_dir(r["patch"])
        if not d:
            continue
        o = outcome(d)
        if o is None:
            continue
        rows.append(dict(patch=r["patch"], per_cm2=r["per_cm2"], sites=r["transverse_min"],
                         area_cm2=r["area_cm2"], outcome=o, high=bool(r["per_cm2"] > thr)))
    hi = [r for r in rows if r["high"]]
    lo = [r for r in rows if not r["high"]]
    def frac(g):
        return (sum(1 for r in g if r["outcome"] == "unreadable") / len(g)) if g else float("nan")
    fh, fl = frac(hi), frac(lo)
    ratio = (fh / fl) if fl else float("inf")
    enough = len(hi) >= MIN_PER_SIDE and len(lo) >= MIN_PER_SIDE
    admitted = bool(enough and ratio >= BAR_RATIO)
    print("RULES R-CROSS, declared outcome split")
    print("  threshold = the team's pooled p90 crossing rate = %.2f sites/cm2" % thr)
    print("  HIGH (above it): n=%-4d unreadable %5.1f %%" % (len(hi), 100 * fh) if hi else "  HIGH: n=0")
    print("  LOW  (at or below): n=%-4d unreadable %5.1f %%" % (len(lo), 100 * fl) if lo else "  LOW: n=0")
    print("  ratio HIGH/LOW = %s   (bar: >= %.1fx with >= %d on each side)"
          % ("inf" if ratio == float("inf") else "%.2f" % ratio, BAR_RATIO, MIN_PER_SIDE))
    if not enough:
        print("  NOT ADMITTED: %d high / %d low, the bar needs >= %d on each side."
              % (len(hi), len(lo), MIN_PER_SIDE))
        print("  R-CROSS is recorded as a DESCRIPTIVE STATISTIC and gates nothing. It is not retuned or re-split.")
    else:
        print("  R-CROSS %s" % ("ADMITTED as a pre-render VOID gate for traces made from now on"
                                if admitted else "NOT ADMITTED: the split does not reach the declared ratio"))
    res = dict(threshold_per_cm2=thr, n_high=len(hi), n_low=len(lo),
               unreadable_frac_high=None if hi else None, bar=dict(ratio=BAR_RATIO, min_per_side=MIN_PER_SIDE),
               admitted=admitted, enough_per_side=bool(enough))
    if hi: res["unreadable_frac_high"] = round(fh, 4)
    if lo: res["unreadable_frac_low"] = round(fl, 4)
    res["ratio"] = None if ratio == float("inf") else round(ratio, 4)
    res["rows"] = rows
    json.dump(res, open(os.path.join(G, "rcross_split.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
