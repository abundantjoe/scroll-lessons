# Provenance: Project HERCULES | owner the owner | [id removed]
"""Aggregate holes.py rows into holes.json (DECL-P4-24 rules, holes.py header).
usage: holes_agg.py <rows.jsonl> <out holes.json>
"""

from __future__ import annotations

import json
import sys

import numpy as np

KEYS = ["invalid_frac", "n_holes", "b_zero_or_missing_frac", "flat_ratio_bad_frac", "d_nopeak_frac"]


def main(rows_path, out):
    rows = {(j["r"], j["c"]): j for j in map(json.loads, open(rows_path))}
    ref = [v for (r, c), v in rows.items() if c <= 8 and "skip" not in v]
    pool = [p for v in ref for p in v["d_best_prom"]]
    pmin = 0.25 * float(np.median(pool)) if pool else None
    for v in rows.values():
        if "d_best_prom" in v and pmin is not None:
            a = np.array(v["d_best_prom"])
            v["d_nopeak_frac"] = float(np.mean(a < pmin))
        if v.get("e_rays") is not None and pmin is not None:
            e = {}
            for dmm in ("0.5", "1.0", "2.0", "5.0"):
                vals = [ray["prom"][dmm] for ray in v["e_rays"] if ray.get("prom") and ray["prom"].get(dmm) is not None]
                e[dmm] = {"n_rays": len(vals), "frac_sheet": float(np.mean(np.array(vals) >= pmin)) if vals else None}
            v["e_sheet_beyond_edge"] = e
    refmax = {}
    for k in KEYS:
        a = [v[k] for v in ref if v.get(k) is not None]
        refmax[k] = {"min": float(min(a)), "max": float(max(a)), "n": len(a)} if a else None
    tiles = []
    for (r, c), v in sorted(rows.items()):
        rec = {"tile": f"r{r}_c{c}", **{k: v.get(k) for k in KEYS},
               "b_missing_chunk_frac": v.get("b_missing_chunk_frac"), "b_zero_frac": v.get("b_zero_frac"),
               "holes": v.get("holes"), "flat_ratio_p1_p50_p99": v.get("flat_ratio_p1_p50_p99"),
               "e_sheet_beyond_edge": v.get("e_sheet_beyond_edge"), "skip": v.get("skip"), "flags": []}
        if c >= 9 and "skip" not in v and pmin is not None:
            for k in KEYS:
                if refmax[k] and v.get(k) is not None and v[k] > refmax[k]["max"]:
                    rec["flags"].append(k)
            e2 = (v.get("e_sheet_beyond_edge") or {}).get("2.0", {})
            if e2.get("frac_sheet") is not None and e2["frac_sheet"] >= 0.25:
                rec["flags"].append("e_sheet_ge2mm_on_ge25pct_rays")
        rec["hole_flag"] = bool(rec["flags"])
        tiles.append(rec)
    tiles.sort(key=lambda t: (not t["hole_flag"], t["tile"]))
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "entry": "DECL-P4-24 mesh holes and edges, 20260701183124-w010-027 (2.4 um), strip-a r0-r8 x c0-c19",
           "viewing": "No image, tile or CT pixel was viewed or described; CT values were streamed as numbers (single voxels and 1-D normal profiles) and discarded.",
           "rules": "tools/sib/p4-core/holes.py header (committed before any number)",
           "p_min_prominence": pmin, "n_tiles": len(rows), "n_reference_tiles": len(ref),
           "reference_min_max_c0_c8": refmax,
           "hole_flagged": [t["tile"] for t in tiles if t["hole_flag"]],
           "reference_complete": len(ref) == 81 - sum(1 for (r, c), v in rows.items() if c <= 8 and "skip" in v),
           "tiles": tiles}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("p_min_prominence", "n_tiles", "n_reference_tiles", "hole_flagged")}))
    print(json.dumps(refmax))


if __name__ == "__main__":
    main(*sys.argv[1:3])
