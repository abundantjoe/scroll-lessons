#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command, keep its full output under /work/rr/runlogs, append one JSON line
# (utc start/end, command, exit code, output sha256) to logs/sib/regrescan/runs.jsonl.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/rr/runlogs
U0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT=/work/rr/runlogs/$(date -u +%Y%m%dT%H%M%S)_$$.log
"$@" > "$OUT" 2>&1
RC=$?
U1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SHA=$(sha256sum "$OUT" | cut -d' ' -f1)
/opt/hv/bin/python - "$REPO/logs/sib/regrescan/runs.jsonl" "$U0" "$U1" "$RC" "$SHA" "$OUT" "$@" <<'PY'
import json, sys
f, u0, u1, rc, sha, out, *cmd = sys.argv[1:]
with open(f, "a") as fh:
    fh.write(json.dumps({"utc_start": u0, "utc_end": u1, "command": " ".join(cmd),
                         "exit_code": int(rc), "output_sha256": sha, "output_log": out}) + "\n")
PY
tail -n 40 "$OUT"
exit $RC
