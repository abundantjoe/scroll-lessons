#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output, append one line to logs/sib/pairs0814/runs.jsonl.
# Usage: runlog.sh <out_file> <command...>
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT="$1"; shift
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$OUT" 2>&1
RC=$?
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
python3 - "$REPO/logs/sib/pairs0814/runs.jsonl" "$START" "$END" "$RC" "$SHA" "$OUT" "$@" <<'PY'
import json, sys
f, s, e, rc, sha, out, *cmd = sys.argv[1:]
with open(f, "a") as fh:
    fh.write(json.dumps({"utc_start": s, "utc_end": e, "command": cmd, "exit_code": int(rc),
                         "output_file": out, "output_sha256": sha}) + "\n")
PY
exit $RC
