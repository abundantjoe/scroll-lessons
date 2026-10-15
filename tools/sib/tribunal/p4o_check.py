# Provenance: Project HERCULES | owner the owner | [id removed]
"""Run the P4-O provenance consistency check on the ckpt-screen provenance files (text and hashes only).

    python tools/sib/tribunal/p4o_check.py OUT.json provenance_a.json [...]
"""
import json
import sys
from pathlib import Path

from hercules.tribunal import p4val as V

out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]", "files": {}}
for p in sys.argv[2:]:
    out["files"][Path(p).name] = V.check_p4o_provenance(json.loads(Path(p).read_text()))
out["all_passed"] = all(v["passed"] for v in out["files"].values())
out["eligible_sha256"] = sorted({s for v in out["files"].values() for s in v["eligible_sha256"]})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({k: {"passed": v["passed"], "eligible": [r["checkpoint"] for r in v["checkpoints"] if r["eligible"]],
                      "problems": [(r["checkpoint"], r["problems"]) for r in v["checkpoints"] if r["problems"]]}
                  for k, v in out["files"].items()}, indent=1))
