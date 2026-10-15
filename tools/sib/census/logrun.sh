#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# logrun.sh <logfile> <cmd...>: run a command, append {utc, command, exit code, output sha256} to runs.jsonl
set -u
LOG=$1; shift
RUNS=/home/user/dominion/logs/sib/census/runs.jsonl
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$LOG" 2>&1
RC=$?
SHA=$(sha256sum "$LOG" | cut -d' ' -f1)
/opt/hv/bin/python -c 'import json,sys; print(json.dumps(dict(utc=sys.argv[1], utc_end=sys.argv[2], command=sys.argv[3], exit_code=int(sys.argv[4]), output=sys.argv[5], output_sha256=sys.argv[6])))' \
  "$UTC" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" "$RC" "$LOG" "$SHA" >> "$RUNS"
exit $RC
