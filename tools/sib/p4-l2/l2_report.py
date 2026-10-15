"""P4-L numeric summary from manifest.json (numbers only; no pixel is opened). Prints markdown tables.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: l2_report.py <manifest.json>
"""
import json
import statistics as st
import sys

m = json.load(open(sys.argv[1]))
ts = m["tiles"]
f = lambda k: [t["stats"][k] for t in ts]  # noqa: E731
print("| statistic over %d tiles | min | median | max |" % len(ts))
print("|---|---|---|---|")
for k in ("max_p1", "max_p50", "max_p99", "max_p99.9", "vox_median", "vox_p99.9", "frac_valid_max_gt_T_hi",
          "frac_valid_max_le_T_mid", "frac_valid_max_zero", "out_mean", "frac_out_255"):
    v = f(k)
    print("| %s | %.4g | %.4g | %.4g |" % (k, min(v), st.median(v), max(v)))
print()
print("Per column, median over rows of frac_valid_max_gt_T_hi (descriptive; not a score):")
print()
print("| c | n | median frac > T_hi | median out_mean |")
print("|---|---|---|---|")
for c in sorted({t["c"] for t in ts}):
    tc = [t for t in ts if t["c"] == c]
    print("| %d | %d | %.5f | %.1f |" % (c, len(tc), st.median(t["stats"]["frac_valid_max_gt_T_hi"] for t in tc),
                                        st.median(t["stats"]["out_mean"] for t in tc)))
print()
print("Per row: median out_mean / vox_median")
for r in sorted({t["r"] for t in ts}):
    tr = [t for t in ts if t["r"] == r]
    print("- r%d: n %d, out_mean %.1f, vox_median %d" % (r, len(tr), st.median(t["stats"]["out_mean"] for t in tr),
                                                        st.median(t["stats"]["vox_median"] for t in tr)))
s = [t["read_s"] for t in ts if "read_s" in t]
print()
print("chunks read %d, missing (404, fill 0) %d" % (sum(t["chunks_read"] for t in ts), sum(t["chunks_missing"] for t in ts)))
