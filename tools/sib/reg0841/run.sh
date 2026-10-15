#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, save its output under /work/reg/out/<tag>.log and append a record to
# logs/sib/reg0841/runs.jsonl (utc start/end, command, exit code, output sha256).
# usage: run.sh TAG cmd args...
TAG=$1; shift
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/reg/out
OUT=/work/reg/out/$TAG.log
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$OUT" 2>&1; RC=$?
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
/opt/hv/bin/python - "$TAG" "$T0" "$T1" "$RC" "$SHA" "$OUT" "$*" >> "$REPO/logs/sib/reg0841/runs.jsonl" <<'PY'
import json, sys
t, a, b, rc, sha, out, cmd = sys.argv[1:]
print(json.dumps({"tag": t, "utc_start": a, "utc_end": b, "command": cmd, "exit_code": int(rc), "output": out, "output_sha256": sha}))
PY
exit $RC
