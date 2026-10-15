#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output under /work/sib_contam/runs/, and append
# one line to logs/sib/contam/runs.jsonl (utc from date -u, command, exit code,
# output sha256). Failures are logged too. Usage: tools/sib/contam/run.sh <cmd...>
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUTDIR=/work/sib_contam/runs
mkdir -p "$OUTDIR" "$REPO/logs/sib/contam"
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT="$OUTDIR/run_$(date -u +%Y%m%dT%H%M%S)_$$.log"
"$@" > "$OUT" 2>&1
RC=$?
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
UTC_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$UTC" "$UTC_END" "$RC" "$SHA" "$OUT" "$@" >> "$REPO/logs/sib/contam/runs.jsonl" <<'EOF'
import json, sys
utc, end, rc, sha, out, *cmd = sys.argv[1:]
print(json.dumps({"utc": utc, "utc_end": end, "command": cmd, "exit_code": int(rc),
                  "output_sha256": sha, "output_path": out}))
EOF
tail -n 40 "$OUT"
exit $RC
