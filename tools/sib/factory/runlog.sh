#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its combined output under /work/factory/runs/, append one JSON line to
# logs/sib/factory/runs.jsonl: utc start/end, command, exit code, output sha256 and bytes.
# Usage: tools/sib/factory/runlog.sh <label> -- <command...>
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
label=$1; shift; [ "${1:-}" = "--" ] && shift
mkdir -p /work/factory/runs "$REPO/logs/sib/factory"
t0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
out=/work/factory/runs/${label}_$(date -u +%Y%m%dT%H%M%SZ).log
"$@" > "$out" 2>&1; rc=$?
t1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sha=$(sha256sum "$out" | cut -d' ' -f1); n=$(stat -c %s "$out")
/opt/hv/bin/python - "$REPO/logs/sib/factory/runs.jsonl" "$label" "$t0" "$t1" "$rc" "$sha" "$n" "$out" "$@" <<'PY'
import json, sys
f, label, t0, t1, rc, sha, n, out, *cmd = sys.argv[1:]
with open(f, "a") as fh:
    fh.write(json.dumps({"label": label, "utc_start": t0, "utc_end": t1, "command": cmd, "exit_code": int(rc),
                         "output_sha256": sha, "output_bytes": int(n), "output_log": out}) + "\n")
PY
tail -n 40 "$out"
exit $rc
