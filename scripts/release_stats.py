#!/usr/bin/env python
"""release_stats.py -- recompute every headline statistic of the release from its recorded counts, with exact CIs.

Nothing here is measured: the counts are the ones recorded in RULES.md / LEDGER.md (the source of each is written next
to it). What this script adds is the arithmetic, done by code instead of by hand, so every p-value and interval in
README.md and docs/RESULTS.md is reproducible:
  * Clopper-Pearson (exact) and Wilson 95 % intervals for every proportion;
  * Fisher's exact test, one-sided (corpus rate LOWER than the control's), for every corpus-vs-control comparison;
  * the binomial probability of the observed corpus count if units flagged at the control's rate (control rate
    treated as known -- the less conservative of the two, so both are always given);
  * the expected flagged count at the control's rate;
  * a CLUSTER-COLLAPSED sensitivity analysis (added at release, exploratory): flagged units are not independent -- the
    control's 7 flags sit in clusters [4, 2, 1], and R-SHAPE measured P(largest cluster >= 4) = 0.0257 under
    independence -- so unit-level p-values overstate the evidence. Collapsing each 4-connected cluster to ONE event
    gives the control 3 events in 71 units; the corpus counts are unchanged (its flagged units are isolated).
Interval bounds are written with the lower bound rounded DOWN and the upper bound rounded UP (never narrower than
computed); p-values are written to 3 significant figures.
usage: release_stats.py [--json out.json]
"""
import argparse, json, math, sys
from scipy import stats

CONTROL_EVENTS = 3          # clusters [4, 2, 1] collapsed to one event each (RULES.md R-CTRL55)
CONTROL = dict(k=7, n=71, what="w040 known-text control, flagged 0.5 cm2 units / valid units (frozen rule 5.5)",
               source="RULES.md R-CTRL55, 'Authoritative result' (2026-09-19 03:05 UTC)")
CORPUS = [
    dict(name="R-DEFICIT", k=1, n=113, what="eligible-scroll corpus, screening reads (30 surfaces, 56.50 cm2 of valid units)",
         source="RULES.md R-DEFICIT (2026-09-19 08:30)"),
    dict(name="R-CREST-POWER PHerc1203 half", k=0, n=64, what="3 team surfaces of PHerc1203, crest veto off, 36.54 cm2 on-sheet",
         source="RULES.md 'R-CREST-POWER: the PHerc1203 half is COMPLETE' (2026-09-19 12:32)"),
    dict(name="R-CREST-POWER phase 1, 6 of 12", k=0, n=114, what="first 6 members, 92.62 cm2 on-sheet",
         source="RULES.md 'R-CREST-POWER at the HALFWAY mark' (2026-09-19 14:49)"),
    dict(name="R-CREST-POWER phase 1, 11 of 12", k=0, n=190, what="11 of 12 members (member 12 incomplete), 150.67 cm2 on-sheet",
         source="LEDGER.md rows for keys '...|ink9um_seed42+plain+nocrest|both' (valid counts 28+18+18+19+14+17+19+20+18+10+9); "
                "area from commit ecf1dd8 message"),
]
PROPORTIONS = [
    dict(name="R-SMALL-2 readable fraction", k=2, n=40, bar=0.30, what="interior traces at the reduced budget that were readable",
         source="RULES.md 'R-SMALL-2 FINAL' (2026-09-19 12:01)"),
    dict(name="R-ORIENT positive margins", k=60, n=118, bar=0.50, what="corpus unit margins > 0 (50.8 % recorded)",
         source="RULES.md R-ORIENT (2026-09-19 08:45)"),
    dict(name="Depth-swap tripwire firings", k=0, n=52, what="reads carrying the swapped table on which the tripwire fired",
         source="RULES.md R-ORIENT (2026-09-19 08:45)"),
    dict(name="Rule 5.5 self-test, w028 text units", k=5, n=5, what="strict text units flagged on the w028 pooled map",
         source="RULES.md R-5.5 result (2026-09-17)"),
    dict(name="Rule 5.5 self-test, w028 blank units", k=0, n=8, what="strict blank units flagged on the w028 pooled map",
         source="RULES.md R-5.5 result (2026-09-17)"),
]
# Values exactly AS PRINTED in RULES.md (value, the significant figures it was printed with, line). The script must
# reproduce each at that precision; a mismatch means the record or the code is wrong.
RECORDED = [
    ("Fisher one-sided 1/113 vs 7/71", lambda: fisher(1, 113), 0.0058, 2, "RULES.md:2230"),
    ("binomial P(<=1) for 1/113 at 7/71", lambda: stats.binom.cdf(1, 113, 7 / 71), 1.1e-4, 2, "RULES.md:2231"),
    ("binomial P(0) for 0/64 at 7/71", lambda: (1 - 7 / 71) ** 64, 0.0013, 2, "RULES.md:3134"),
    ("Fisher one-sided 0/64 vs 7/71", lambda: fisher(0, 64), 0.0096, 2, "RULES.md:3134"),
    ("binomial P(0) for 0/83 at 7/71", lambda: (1 - 7 / 71) ** 83, 1.81e-4, 3, "RULES.md:3162"),
    ("Fisher one-sided 0/83 vs 7/71 (the corrected value)", lambda: fisher(0, 83), 0.00375, 3, "RULES.md:3162"),
    ("binomial P(0) for 0/97 at 7/71", lambda: (1 - 7 / 71) ** 97, 4.24e-5, 3, "RULES.md:3190"),
    ("Fisher one-sided 0/97 vs 7/71", lambda: fisher(0, 97), 0.00201, 3, "RULES.md:3190"),
    ("binomial P(0) for 0/114 at 7/71", lambda: (1 - 7 / 71) ** 114, 7.26e-6, 3, "RULES.md:3197"),
    ("Fisher one-sided 0/114 vs 7/71", lambda: fisher(0, 114), 0.00101, 3, "RULES.md:3198"),
]
# EXPLORATORY, added after R-HELDOUT reported (RULES.md R-HELDOUT RESULT): the same eligible-scroll counts against the
# reference rate measured on known text from a scroll the model never saw (PHerc0841, 3 segments): 1 flagged of 60 valid
# units (records/release/heldout_2026-10-15/rheldout.json). R-HELDOUT declared that this rate is reported beside 7/71.
HELDOUT = dict(k=1, n=60, what="PHerc0841 held-out known text, flagged / valid 0.5 cm2 units (frozen rule, auto grid)",
               source="records/release/heldout_2026-10-15/rheldout.json; RULES.md R-HELDOUT RESULT")
# R-HELDOUT's declaration (RULES.md:3268) named the rate on TEXT-BEARING units (phi >= 0.02) as the replacement
# reference: 1 of 15. The eligible counts are over ALL valid units (unknown ink content), as are 7/71 and 1/60, so 1/60
# is the like-for-like comparison and is reported first; 1/15 -- the reference if every eligible unit carried text like
# the held-out text units -- is reported beside it so neither reading is hidden.
HELDOUT_TEXT = dict(k=1, n=15, what="PHerc0841 held-out known text, flagged / text-bearing (phi >= 0.02) valid units",
                    source="records/release/heldout_2026-10-15/rheldout.json (pooled.text_units); RULES.md:3309")


def fisher(k, n, k0=CONTROL["k"], n0=CONTROL["n"]):
    return float(stats.fisher_exact([[k, n - k], [k0, n0 - k0]], alternative="less")[1])


def clopper_pearson(k, n, a=0.05):
    lo = 0.0 if k == 0 else float(stats.beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def wilson(k, n, z=1.959963984540054):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def down(x, d=4):
    return math.floor(x * 10 ** d) / 10 ** d


def up(x, d=4):
    return math.ceil(x * 10 ** d) / 10 ** d


def sig(x, s=3):
    return float("%.*g" % (s, x))


def interval(k, n):
    cp, wi = clopper_pearson(k, n), wilson(k, n)
    return dict(k=k, n=n, rate=k / n, cp95=[down(cp[0]), up(cp[1])], wilson95=[down(wi[0]), up(wi[1])])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    p0 = CONTROL["k"] / CONTROL["n"]
    out = dict(control=dict(CONTROL, **interval(CONTROL["k"], CONTROL["n"])), comparisons=[], proportions=[], recorded_checks=[])
    print("CONTROL  %d/%d = %.4f  CP95 %s  Wilson95 %s   [%s]" % (CONTROL["k"], CONTROL["n"], p0, out["control"]["cp95"],
                                                            out["control"]["wilson95"], CONTROL["source"]))
    for c in CORPUS:
        r = dict(c, **interval(c["k"], c["n"]))
        r["expected_at_control_rate"] = round(c["n"] * p0, 2)
        r["fisher_one_sided_p"] = sig(fisher(c["k"], c["n"]))
        r["binomial_p_le_k_at_control_rate"] = sig(float(stats.binom.cdf(c["k"], c["n"], p0)))
        r["rate_ratio_upper_cp95"] = up(r["cp95"][1] / p0, 3)
        r["cluster_collapsed_fisher_one_sided_p"] = sig(fisher(c["k"], c["n"], CONTROL_EVENTS, CONTROL["n"]))
        r["cluster_collapsed_binomial_p"] = sig(float(stats.binom.cdf(c["k"], c["n"], CONTROL_EVENTS / CONTROL["n"])))
        out["comparisons"].append(r)
        print("%-34s %3d/%-3d rate %.4f CP95 %s  expected %.2f  Fisher p %.3g  binomial p %.3g  rate <= %.3f x control (CP upper)"
              % (c["name"], c["k"], c["n"], r["rate"], r["cp95"], r["expected_at_control_rate"], r["fisher_one_sided_p"],
                 r["binomial_p_le_k_at_control_rate"], r["rate_ratio_upper_cp95"]))
        print("%-34s cluster-collapsed (control 3 events / 71): Fisher p %.3g  binomial p %.3g"
              % ("", r["cluster_collapsed_fisher_one_sided_p"], r["cluster_collapsed_binomial_p"]))
    for c in PROPORTIONS:
        r = dict(c, **interval(c["k"], c["n"]))
        if "bar" in c:
            r["binomial_two_sided_p_vs_bar"] = sig(float(stats.binomtest(c["k"], c["n"], c["bar"]).pvalue))
        out["proportions"].append(r)
        print("%-34s %3d/%-3d rate %.4f CP95 %s Wilson95 %s%s" % (c["name"], c["k"], c["n"], r["rate"], r["cp95"], r["wilson95"],
              "  two-sided p vs %.2f = %.3g" % (c["bar"], r["binomial_two_sided_p_vs_bar"]) if "bar" in c else ""))
    ph = HELDOUT["k"] / HELDOUT["n"]
    out["heldout_reference"] = dict(HELDOUT, **interval(HELDOUT["k"], HELDOUT["n"]),
                                    fisher_one_sided_p_vs_control=sig(fisher(HELDOUT["k"], HELDOUT["n"])))
    out["heldout_text_reference"] = dict(HELDOUT_TEXT, **interval(HELDOUT_TEXT["k"], HELDOUT_TEXT["n"]))
    print("HELDOUT  %d/%d = %.4f  CP95 %s  (vs control 7/71: Fisher one-sided p %.3g)   [%s]"
          % (HELDOUT["k"], HELDOUT["n"], ph, out["heldout_reference"]["cp95"], out["heldout_reference"]["fisher_one_sided_p_vs_control"], HELDOUT["source"]))
    for r in out["comparisons"]:
        r["expected_at_heldout_rate"] = round(r["n"] * ph, 2)
        r["fisher_one_sided_p_vs_heldout"] = sig(fisher(r["k"], r["n"], HELDOUT["k"], HELDOUT["n"]))
        print("%-34s vs held-out 1/60: expected %.2f  Fisher one-sided p %.3g" % (r["name"], r["expected_at_heldout_rate"], r["fisher_one_sided_p_vs_heldout"]))
        r["expected_at_heldout_text_rate"] = round(r["n"] * HELDOUT_TEXT["k"] / HELDOUT_TEXT["n"], 2)
        r["fisher_one_sided_p_vs_heldout_text"] = sig(fisher(r["k"], r["n"], HELDOUT_TEXT["k"], HELDOUT_TEXT["n"]))
        print("%-34s vs held-out text units 1/15: expected %.2f  Fisher one-sided p %.3g"
              % ("", r["expected_at_heldout_text_rate"], r["fisher_one_sided_p_vs_heldout_text"]))
    bad = 0
    for name, f, rec, sf, where in RECORDED:
        got = f(); ok = sig(got, sf) == sig(rec, sf)
        bad += not ok
        out["recorded_checks"].append(dict(check=name, printed=rec, printed_sig_figs=sf, where=where, recomputed=got, ok=ok))
        print("%s %-52s printed %-9g (%s, %d s.f.) recomputed %.6g" % ("OK  " if ok else "DIFF", name, rec, where, sf, got))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print("wrote", a.json)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
