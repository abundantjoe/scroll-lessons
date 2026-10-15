#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output under /work/handed/out/, and append
# {utc, command, exit_code, output_sha256, output_path} to logs/sib/handed/runs.jsonl.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUTDIR=/work/handed/out; mkdir -p "$OUTDIR"
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT="$OUTDIR/run_$(date -u +%Y%m%dT%H%M%S)_$$.log"
bash -o pipefail -c "$*" > "$OUT" 2>&1
RC=$?
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
/opt/hv/bin/python - "$UTC" "$*" "$RC" "$SHA" "$OUT" >> "$REPO/logs/sib/handed/runs.jsonl" <<'PY'
import json, sys
u, c, rc, sha, out = sys.argv[1:]
print(json.dumps({"utc": u, "command": c, "exit_code": int(rc), "output_sha256": sha, "output_path": out}))
PY
cat "$OUT" | tail -n 60
exit $RC
