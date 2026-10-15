#!/usr/bin/env python3
"""Markdown table of results/*.json (written by scripts/reproduce.sh)."""

import json
import sys
from pathlib import Path

d = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
print("| segment (PHerc0139) | region | area cm^2 | mean abs angle defect (deg) | grid % | SLIM % | ARAP % | fold-overs grid/SLIM/ARAP |")
print("|---|---|---|---|---|---|---|---|")
for f in sorted(d.glob("whole_*.json")):
    r = json.loads(f.read_text())
    seg = f.stem[len("whole_"):]
    res = r["results"]
    area = r["curvature"]["area_vox2"] * (9.362e-4) ** 2
    print(f"| {seg} | whole mesh | {area:.1f} | {r['curvature']['mean_abs_angle_defect_deg']:.3f} | "
          + " | ".join(f"{res[m]['pct_quads_within_5pct']:.2f}" if m in res else "-" for m in ("grid", "slim", "arap"))
          + " | " + "/".join(str(res[m]["fold_overs"]) if m in res else "-" for m in ("grid", "slim", "arap")) + " |")
    s = json.loads((d / f"scan_{seg}.json").read_text())
    for w in s["windows"]:
        res = w["results"]
        print(f"| {seg} | rows {w['rows']}, cols {w['cols']} | {w['area_cm2']:.2f} | {w['mean_abs_angle_defect_deg']:.3f} | "
              + " | ".join(f"{res[m]['pct_quads_within_5pct']:.2f}" for m in ("grid", "slim", "arap"))
              + " | " + "/".join(str(res[m]["fold_overs"]) for m in ("grid", "slim", "arap")) + " |")
