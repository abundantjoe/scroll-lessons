#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output, and append one JSON line to
# logs/sib/tribunal/runs.jsonl: utc start/end, command, exit code, output sha256.
# Usage: tools/sib/tribunal/logrun.sh <label> <command...>
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
LOGDIR="$REPO/logs/sib/tribunal"
mkdir -p "$LOGDIR/out"
label=$1; shift
utc0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
out="$LOGDIR/out/${label}.log"
( cd "$REPO" && "$@" ) > "$out" 2>&1
rc=$?
utc1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sha=$(sha256sum "$out" | cut -d' ' -f1)
/opt/hv/bin/python - "$LOGDIR/runs.jsonl" "$label" "$utc0" "$utc1" "$rc" "$sha" "${out#$REPO/}" "$@" <<'EOF'
import json, sys
path, label, u0, u1, rc, sha, out, *cmd = sys.argv[1:]
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps({"label": label, "utc_start": u0, "utc_end": u1, "command": cmd, "exit_code": int(rc),
                        "output_file": out, "output_sha256": sha}, sort_keys=True) + "\n")
EOF
exit $rc
