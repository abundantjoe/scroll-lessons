#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, capture its output, append {utc, command, exit_code, output_sha256, output_file}
# to logs/sib/devloop/runs.jsonl. Usage: tools/sib/devloop/runlog.sh <label> <command...>
set -uo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUTD=${DEVLOOP_OUT:-/work/devloop/runlogs}
mkdir -p "$OUTD" "$ROOT/logs/sib/devloop"
label="$1"; shift
utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
out="$OUTD/${label}_$(date -u +%Y%m%dT%H%M%SZ).log"
"$@" > "$out" 2>&1
rc=$?
sha=$(sha256sum "$out" | cut -d' ' -f1)
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$ROOT/logs/sib/devloop/runs.jsonl" "$utc" "$end" "$label" "$rc" "$sha" "$out" "$@" <<'PY'
import json, sys
p, utc, end, label, rc, sha, out, *cmd = sys.argv[1:]
with open(p, "a") as f:
    f.write(json.dumps({"utc": utc, "utc_end": end, "label": label, "command": " ".join(cmd),
                        "exit_code": int(rc), "output_sha256": sha, "output_file": out}) + "\n")
PY
exit $rc
