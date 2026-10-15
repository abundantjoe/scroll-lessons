"""Summarise injection-recovery (DECL-P4-10 item 3). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python summarize_inj.py <params.json> <out.json> <inj_*.jsonl ...>
Sensitivity per (material, rho_pap, t) over counted locations, with a Wilson 95 % interval; detection limit = the
smallest tested t whose sensitivity >= the bar (0.8) at that and every thicker t; FP rates of the virtual-glyph
criterion on uninjected patches (unrotated and rot-90).
"""
import json
import math
import sys


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


P = json.load(open(sys.argv[1]))
recs = []
for f in sys.argv[3:]:
    recs += [json.loads(l) for l in open(f)]
out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
       "serves": "DECL-P4-10 item 3", "bar": P["sensitivity_bar"], "materials": {}}
for mat in sorted({r["mat"] for r in recs}):
    rs = [r for r in recs if r["mat"] == mat and r.get("counted")]
    sk = [r for r in recs if r["mat"] == mat and "skipped" in r]
    m = {"n_locations": len(rs), "n_skipped_usable_lt_0.9": len(sk),
         "tiles": sorted({tuple(r["tile"]) for r in rs}), "sensitivity": {}, "detection_limit_um": {}}
    for rho in P["rho_pap"]:
        lim = None
        ts = sorted(P["thicknesses_um"])
        sens = {}
        for t in ts:
            k = sum(r["results"][f"rho{rho}|t{t}"]["recovered"] for r in rs)
            sens[t] = k / len(rs) if rs else None
            m["sensitivity"][f"rho{rho}|t{t}"] = {"k": k, "n": len(rs), "sens": sens[t], "wilson95": wilson(k, len(rs)),
                                                  "median_new_hot_mm2": sorted(r["results"][f"rho{rho}|t{t}"]["new_hot_mm2"] for r in rs)[len(rs) // 2] if rs else None}
        for i, t in enumerate(ts):
            if all(sens[u] is not None and sens[u] >= P["sensitivity_bar"] for u in ts[i:]):
                lim = t
                break
        m["detection_limit_um"][str(rho)] = lim
    n0 = sum(r["null_unrotated"][1] for r in rs)
    n90 = sum(r["null_rot90"][1] for r in rs)
    m["fp_virtual_glyph_unrotated"] = {"k": n0, "n": len(rs), "rate": n0 / len(rs) if rs else None, "wilson95": wilson(n0, len(rs))}
    m["fp_virtual_glyph_rot90"] = {"k": n90, "n": len(rs), "rate": n90 / len(rs) if rs else None, "wilson95": wilson(n90, len(rs))}
    m["base_hot_in_region_mm2_max"] = max((r["base_hot_in_region_mm2"] for r in rs), default=None)
    t0 = str(P["plausible_thickness_um"])
    m["insensitive_at_plausible_t"] = {str(rho): (m["sensitivity"][f"rho{rho}|t{P['plausible_thickness_um']}"]["sens"] or 0) < P["sensitivity_bar"] for rho in P["rho_pap"]}
    out["materials"][mat] = m
json.dump(out, open(sys.argv[2], "w"), indent=1)
for mat, m in out["materials"].items():
    print(mat, m["n_locations"], m["detection_limit_um"], m["fp_virtual_glyph_unrotated"]["rate"], m["fp_virtual_glyph_rot90"]["rate"])
    for k, v in m["sensitivity"].items():
        print("  ", k, v["k"], "/", v["n"])
