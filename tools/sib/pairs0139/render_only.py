# Provenance: Project HERCULES | owner the owner | [id removed]
"""Render one segment with build_pairs.render (same command and record) ahead of the tiling step."""
import sys, json
import build_pairs as B
out, rec = B.render(sys.argv[1], lambda d: print(json.dumps(d), flush=True))
print(out, json.dumps(rec))
