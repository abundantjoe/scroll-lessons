#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output, append one JSON line to logs/sib/tracer/runs.jsonl.
# Usage: tools/sib/tracer/runlog.sh <label> <outfile> -- cmd args...
set -uo pipefail
REPO=/home/user/dominion
label="$1"; out="$2"; shift 3
t0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$out" 2>&1; rc=$?
t1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sha=$(sha256sum "$out" | cut -d' ' -f1)
python3 - "$label" "$t0" "$t1" "$rc" "$sha" "$out" "$@" >> "$REPO/logs/sib/tracer/runs.jsonl" <<'PY'
import json,sys
a=sys.argv[1:]
print(json.dumps({"label":a[0],"utc_start":a[1],"utc_end":a[2],"exit":int(a[3]),"out_sha256":a[4],"out":a[5],"cmd":a[6:]}))
PY
exit $rc
