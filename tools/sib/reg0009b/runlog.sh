#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Usage: runlog.sh <outfile> <command...>  -- runs the command, tees stdout+stderr to <outfile>,
# appends {utc, command, exit, output sha256} to logs/sib/reg0009b/runs.jsonl
REPO=/home/user/dominion
OUT=$1; shift
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$OUT" 2>&1; RC=$?
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
/opt/hv/bin/python - "$UTC" "$RC" "$SHA" "$OUT" "$@" >> $REPO/logs/sib/reg0009b/runs.jsonl <<'PY'
import json,sys
utc,rc,sha,out,*cmd=sys.argv[1:]
print(json.dumps({"utc":utc,"command":" ".join(cmd),"exit":int(rc),"output":out,"output_sha256":sha}))
PY
exit $RC
