# Provenance: Project HERCULES | owner the owner | [id removed]
"""Aggregate dev results (logs/sib/tracer/dev/*.jsonl) into logs/sib/tracer/dev/summary.json.
Per config: per-seed rows and medians of the T0 quantities (dev set only; T0 bars are applied
here only as a dry indication, never as a T0 verdict). Seeds that saved no segment count as
v2 area 0, crossings undefined."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path("/home/user/dominion")
D = REPO / "logs/sib/tracer/dev"


def load(name):
    p = D / name
    return [json.loads(l) for l in open(p)] if p.exists() else []


def main():
    res = load("results.jsonl")
    ctl = {(c["config"], c["segment"]): c for c in load("control.jsonl")}
    by = {}
    for r in res:
        by.setdefault(r["config"], {})[r["segment"]] = r  # last run wins
    out = {}
    for cfg, rows in sorted(by.items()):
        T = []
        for seg, r in sorted(rows.items()):
            m = r.get("metrics")
            c = ctl.get((cfg, seg), {})
            if m is None:
                T.append({"segment": seg, "wall_s": r["wall_s"], "saved": False, "v2_area_cm2": 0.0})
                continue
            sc = json.loads(Path(f"/work/dev/{cfg}_{seg}/metrics/selfcross_raw.json").read_text())
            T.append({
                "segment": seg, "wall_s": r["wall_s"], "saved": True,
                "raw_area_cm2": m["raw"]["area_cm2"], "crossings": m["raw"]["crossings"],
                "crossings_per_cm2": m["raw"]["crossings_per_cm2"],
                "coplanar_contacts": [x["coplanar"] for x in sc["census"]],
                "v2_cutoff_gen": m["v2"]["cutoff_generation"], "v2_area_cm2": m["v2"]["area_cm2"],
                "v2_crossings_after": m["v2"]["crossings_after"],
                "edge_frac_10pct_v2": m["v2"]["edges"].get("frac_within_10pct"),
                "team_frac_within_3_v2": c.get("frac_within_3", m.get("team", {}).get("frac_within_3")),
                "half_pitch": c.get("half_pitch"), "control": c.get("control"),
                "margin_vs_control": c.get("margin_vs_control"),
                "ours_m7_frac_le_1p5": c.get("ours_m7_frac_le_1p5"),
                "team_near_m7_frac_le_1p5": c.get("team_near_m7_frac_le_1p5"),
                "gate": {k: v for k, v in r["trace_meta"].items() if k.startswith("hrc_n")},
            })

        def med(k):
            v = [t[k] for t in T if t.get(k) is not None]
            return float(np.median(v)) if v else None
        summ = {"n_seeds": len(T), "n_saved": sum(t["saved"] for t in T),
                "median_crossings_per_cm2_saved": med("crossings_per_cm2"),
                "median_v2_area_cm2_all": med("v2_area_cm2"),
                "median_edge_frac_10pct_saved": med("edge_frac_10pct_v2"),
                "median_team_frac_within_3_saved": med("team_frac_within_3_v2"),
                "median_margin_vs_control_saved": med("margin_vs_control"),
                "median_wall_s": med("wall_s")}
        dry = {"crossings<=5/cm2": summ["median_crossings_per_cm2_saved"] is not None and summ["median_crossings_per_cm2_saved"] <= 5,
               "v2_area>=3.0": (summ["median_v2_area_cm2_all"] or 0) >= 3.0,
               "edges>=0.85": (summ["median_edge_frac_10pct_saved"] or 0) >= 0.85,
               "team>=0.70": (summ["median_team_frac_within_3_saved"] or 0) >= 0.70,
               "team>=control+0.25": (summ["median_margin_vs_control_saved"] or -1) >= 0.25}
        out[cfg] = {"summary": summ, "dry_indication_on_dev_only": dry, "seeds": T}
    (D / "summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for cfg, o in out.items():
        print(cfg, json.dumps(o["summary"]), json.dumps(o["dry_indication_on_dev_only"]))


if __name__ == "__main__":
    main()
