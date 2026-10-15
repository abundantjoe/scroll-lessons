# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4 validation item 1 (numbers only): which strip-a (w010-027) tiles hold the published final columns,
from the P4-B census summary (letter counts per tile; no image), plus P4-L manifest checks.

    python tools/sib/tribunal/p4val_locate.py census_a_summary.json l2_manifest.json OUT.json
"""
import hashlib
import json
import sys
from pathlib import Path

from hercules.tribunal import p4val as V

cen_p, man_p, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
cen = json.loads(cen_p.read_text())
grid = [[None] * 20 for _ in range(8)]
for t in cen["tiles"].values():
    if t.get("strip") == "w010-027" and int(t["r"]) < 8 and int(t["c"]) < 20:
        grid[int(t["r"])][int(t["c"])] = int(t["n_letters"]) if t.get("rows") == "Y" else None
win = V.known_text_windows(grid, null_max=int(cen.get("null_p99", 4)))
man = json.loads(man_p.read_text())
res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
       "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (cen_p, man_p)},
       "census_grid_w010_027_letters_or_rowsN": grid, "windows": win,
       "p4l_known_text_tiles": {"rule": "strip-a tiles in the known-text slots (c0-c8 gate columns per DECL-P4-12 item 2)",
                                "slots": [s for s in win["slots"] if max(s["tile_cols"]) <= 9]},
       "l2_manifest_check": V.check_l2_manifest(man)}
out.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({"last_text_col": win["last_text_col"], "slots": [(s["col"], s["tile_cols"]) for s in win["slots"]],
                  "short_block": win["short_block_cols_r0r1"], "inter": win["intercolumn_candidates"],
                  "l2_manifest_passed": res["l2_manifest_check"]["passed"],
                  "l2_failed": [c["check"] for c in res["l2_manifest_check"]["checks"] if not c["passed"]]}))
