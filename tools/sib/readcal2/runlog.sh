#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, capture its output, append {utc, utc_end, label, command, exit_code, output_sha256, output_file}
# to logs/sib/readcal2/runs.jsonl (failures included). Usage: tools/sib/readcal2/runlog.sh <label> <command...>
set -uo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUTD=${RC2_OUT:-/work/rc2/runlogs}
mkdir -p "$OUTD" "$ROOT/logs/sib/readcal2"
label="$1"; shift
utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
out="$OUTD/${label}_$(date -u +%Y%m%dT%H%M%SZ).log"
"$@" > "$out" 2>&1
rc=$?
sha=$(sha256sum "$out" | cut -d' ' -f1)
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$ROOT/logs/sib/readcal2/runs.jsonl" "$utc" "$end" "$label" "$rc" "$sha" "$out" "$@" <<'PY'
import json, sys
p, utc, end, label, rc, sha, out, *cmd = sys.argv[1:]
with open(p, "a") as f:
    f.write(json.dumps({"utc": utc, "utc_end": end, "label": label, "command": " ".join(cmd),
                        "exit_code": int(rc), "output_sha256": sha, "output_file": out}) + "\n")
PY
exit $rc
