#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, save its combined output under logs/sib/amx/out/, append a runs.jsonl row
# (utc, command, exit code, output sha256).
set -u
REPO=/home/user/dominion
OUT=$REPO/logs/sib/amx/out; mkdir -p "$OUT"
TAG=$1; shift
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
F=$OUT/${TAG}.log
bash -c "$*" > "$F" 2>&1; RC=$?
SHA=$(sha256sum "$F" | cut -d' ' -f1)
python3 -c 'import json,sys; print(json.dumps({"utc":sys.argv[1],"tag":sys.argv[2],"command":sys.argv[3],"exit_code":int(sys.argv[4]),"output":sys.argv[5],"output_sha256":sys.argv[6]}))' \
  "$UTC" "$TAG" "$*" "$RC" "logs/sib/amx/out/${TAG}.log" "$SHA" >> $REPO/logs/sib/amx/runs.jsonl
exit $RC
