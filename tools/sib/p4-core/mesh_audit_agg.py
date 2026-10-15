# Provenance: Project HERCULES | owner the owner | [id removed]
"""Aggregate mesh_audit rows: reference = tiles c0-c8 (known text), compared
tiles c9-c19. A compared tile is flagged on a metric when it lies outside the
reference tiles' [min, max] range in the bad direction, or on any absolute
bar (self-intersection > 0, s-jumps > 0).
usage: mesh_audit_agg.py <rows.jsonl> <tile_winding_a.json> <out.json>
"""

from __future__ import annotations

import json
import sys

import numpy as np

METRICS = [  # (name, getter, bad direction)
    ("ratio_p5", lambda t: t["ratio"]["p5"], "low"),
    ("ratio_frac_lt_0p6", lambda t: t["ratio"]["frac_lt_0p6"], "high"),
    ("ratio_frac_lt_0p3", lambda t: t["ratio"]["frac_lt_0p3"], "high"),
    ("normal_flip_frac", lambda t: t["normal_flip_frac"], "high"),
    ("normal_inward_frac", lambda t: t["normal_inward_frac"], "high"),
    ("self_intersection_pairs", lambda t: t["self_intersection_pairs"], "high"),
    ("s_jumps_gt0p25", lambda t: t["s_jumps_gt0p25"], "high"),
    ("ct_edge_offset_abs_p50_mm", lambda t: abs(t["ct_edge_offset_mm"]["p50"]), "high"),
    ("ct_centre_offset_abs_p50_mm", lambda t: abs(t["ct_centre_offset_mm"]["p50"]), "high"),
    ("ct_centre_at_window_edge", lambda t: t["ct_centre_offset_mm"]["frac_at_window_edge"], "high"),
    ("w027_to_w028_p5_mm", lambda t: t["w027_to_w028_mm"]["p5"], "low"),
]


def get(t, f):
    try:
        v = f(t)
        return None if v is None else float(v)
    except (KeyError, TypeError):
        return None


def main(rows_path, wind_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    rows = [r for r in rows if "skip" not in r]
    wind = json.load(open(wind_path))["tiles"]
    ref = [r for r in rows if r["c"] <= 8]
    cmp_ = [r for r in rows if 9 <= r["c"] <= 19]
    refsum = {}
    for name, f, bad in METRICS:
        v = [get(r, f) for r in ref]
        v = np.array([x for x in v if x is not None])
        refsum[name] = None if v.size == 0 else {"n": int(v.size), "min": float(v.min()), "p50": float(np.median(v)), "max": float(v.max())}
    flags = []
    per = []
    for r in cmp_ + ref:
        w = wind.get(f"r{r['r']}_c{r['c']}", {})
        rec = {"tile": f"r{r['r']}_c{r['c']}", "winding_median": w.get("winding_median"), "flags": []}
        for name, f, bad in METRICS:
            v = get(r, f)
            rec[name] = v
            rs = refsum[name]
            if v is None or rs is None:
                continue
            out_ = v < rs["min"] if bad == "low" else v > rs["max"]
            absbar = name in ("self_intersection_pairs", "s_jumps_gt0p25") and v > 0
            if (r["c"] >= 9) and (out_ or absbar):
                rec["flags"].append(name)
        per.append(rec)
        if r["c"] >= 9 and rec["flags"]:
            flags.append({"tile": rec["tile"], "flags": rec["flags"]})

    def pool(sel, key, q):
        a = [r[key][q] for r in sel if r.get(key, {}).get(q) is not None]
        return {"n_tiles": len(a), "median_of_tile_p50_mm": float(np.median(a)) if a else None,
                "iqr_mm": [float(np.percentile(a, 25)), float(np.percentile(a, 75))] if a else None}

    dstar = {grp: {k: pool(sel, k, "p50") for k in ("ct_edge_offset_mm", "ct_centre_offset_mm")}
             for grp, sel in (("c0_c8", ref), ("c9_c19", cmp_))}
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "entry": "HYPOTHESES L10 mesh sheet-switch audit, 20260701183124 w010-027 (2.4 um), strip-a tiles",
           "viewing": "No image, tile or CT pixel was viewed or described; CT values were streamed as numbers into 1-D normal profiles.",
           "method": "tools/sib/p4-core/mesh_audit.py docstring",
           "n_tiles": len(rows), "n_reference_c0_c8": len(ref), "n_compared_c9_c19": len(cmp_),
           "reference_summary": refsum, "flags_c9_c19": flags,
           "offset_distributions_not_dstar": dstar, "tiles": per}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("n_tiles", "n_reference_c0_c8", "n_compared_c9_c19", "flags_c9_c19", "offset_distributions_not_dstar")}, indent=1))
    print(json.dumps(refsum, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
