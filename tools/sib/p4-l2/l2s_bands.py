"""Per row band (r0-r1, r2-r7) numbers for STATUS.md from l2s/manifest.json. Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
"""
import json
import statistics as st
import sys

m = json.load(open(sys.argv[1]))
for name, rows in (("r0-r1", (0, 1)), ("r2-r7", tuple(range(2, 8)))):
    ts = [t for t in m["tiles"] if t["r"] in rows]
    if not ts:
        continue
    s = [t["stats"] for t in ts]
    kc = [t["stats"] for t in ts if t["c"] <= 8]
    print(f"- {name}: n {len(ts)}; median over tiles of the per-tile median raw max {st.median(x['max_p50'] for x in s)}"
          f" (range {min(x['max_p50'] for x in s)}-{max(x['max_p50'] for x in s)}); median raw max mean"
          f" {st.median(x['max_mean'] for x in s):.1f}; stretch p1 median {st.median(x['stretch_p1'] for x in s)}"
          f" (range {min(x['stretch_p1'] for x in s)}-{max(x['stretch_p1'] for x in s)}), p99 median"
          f" {st.median(x['stretch_p99'] for x in s)} (range {min(x['stretch_p99'] for x in s)}-"
          f"{max(x['stretch_p99'] for x in s)}); L2S out_mean median {st.median(x['out_mean'] for x in s):.1f};"
          f" known-text columns c0-c8: n {len(kc)}, median raw max {st.median(x['max_p50'] for x in kc)}")
print()
print("Per-tile stretch p1 / p99 (raw uint8 slab-max scale), r c: p1 p99")
print()
for r in sorted({t["r"] for t in m["tiles"]}):
    print(f"- r{r}: " + ", ".join(f"c{t['c']} {t['stats']['stretch_p1']:g}/{t['stats']['stretch_p99']:g}"
                                   for t in sorted(m["tiles"], key=lambda t: t["c"]) if t["r"] == r))
