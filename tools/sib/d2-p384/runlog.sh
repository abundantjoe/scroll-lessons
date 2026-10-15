#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, capture its output to logs/sib/d2-p384/out/<utc>_<label>.log and append a row to
# logs/sib/d2-p384/runs.jsonl (utc start/end from date -u, command, exit code, output sha256).
# Usage: runlog.sh <label> <command...>
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
D=$REPO/logs/sib/d2-p384; mkdir -p "$D/out"
LABEL=$1; shift
N=$(date -u +%Y%m%dT%H%M%SZ)_$LABEL
OUT=$D/out/$N.log
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$OUT" 2>&1
RC=$?
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
python3 - "$D/runs.jsonl" "$T0" "$T1" "$RC" "$SHA" "${OUT#$REPO/}" "$LABEL" "$@" <<'PY'
import json, sys
f, t0, t1, rc, sha, out, label, *cmd = sys.argv[1:]
open(f, "a").write(json.dumps(dict(utc_start=t0, utc_end=t1, label=label, command=cmd, exit_code=int(rc),
                                   output=out, output_sha256=sha)) + "\n")
PY
exit $RC
