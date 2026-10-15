#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, save its combined output under logs/sib/dev-lcsoft/out/<tag>.log, append a runs.jsonl row
# (utc start/end, tag, command, exit code, output sha256).
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT=$REPO/logs/sib/dev-lcsoft/out; mkdir -p "$OUT"
TAG=$1; shift
U0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
F=$OUT/${TAG}.log
bash -c "$*" > "$F" 2>&1; RC=$?
U1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SHA=$(sha256sum "$F" | cut -d' ' -f1)
python3 -c 'import json,sys; print(json.dumps({"utc_start":sys.argv[1],"utc_end":sys.argv[2],"tag":sys.argv[3],"command":sys.argv[4],"exit_code":int(sys.argv[5]),"output":sys.argv[6],"output_sha256":sys.argv[7]}))' \
  "$U0" "$U1" "$TAG" "$*" "$RC" "logs/sib/dev-lcsoft/out/${TAG}.log" "$SHA" >> "$REPO/logs/sib/dev-lcsoft/runs.jsonl"
exit $RC
