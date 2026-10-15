#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output under /work/flat1/runlogs, and
# append {utc, command, exit_code, output_file, output_sha256} to
# logs/sib/flat1/runs.jsonl. Usage: logrun.sh <label> <command...>
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
label="$1"; shift
mkdir -p /work/flat1/runlogs
out=/work/flat1/runlogs/$(date -u +%Y%m%dT%H%M%SZ)_${label}.log
utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$out" 2>&1
rc=$?
sha=$(sha256sum "$out" | cut -d' ' -f1)
/opt/hv/bin/python - "$REPO/logs/sib/flat1/runs.jsonl" "$utc" "$rc" "$out" "$sha" "$label" "$@" <<'PY'
import json, sys
path, utc, rc, out, sha, label, *cmd = sys.argv[1:]
with open(path, "a") as f:
    f.write(json.dumps({"utc": utc, "label": label, "command": cmd, "exit_code": int(rc),
                        "output_file": out, "output_sha256": sha}) + "\n")
PY
tail -5 "$out"
exit $rc
