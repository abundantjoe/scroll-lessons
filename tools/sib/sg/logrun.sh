#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run a command and append {utc, command, exit, output_sha256, output_bytes} to
# logs/sib/sg/runs.jsonl (utc from date -u). Output (stdout+stderr) is kept in
# logs/sib/sg/out/<utc>.txt when it is under 200 kB. Usage: tools/sib/sg/logrun.sh CMD...
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
mkdir -p logs/sib/sg/out
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP=$(mktemp)
"$@" >"$TMP" 2>&1
RC=$?
SHA=$(sha256sum "$TMP" | cut -d' ' -f1)
BYTES=$(stat -c %s "$TMP")
if [ "$BYTES" -lt 200000 ]; then cp "$TMP" "logs/sib/sg/out/${UTC//:/}.txt"; fi
tail -n 5 "$TMP"
rm -f "$TMP"
CMD=$(printf '%q ' "$@")
/opt/hv/bin/python - "$UTC" "$CMD" "$RC" "$SHA" "$BYTES" <<'EOF' >> logs/sib/sg/runs.jsonl
import json, sys
u, c, r, s, b = sys.argv[1:]
print(json.dumps({"utc": u, "command": c.strip(), "exit": int(r), "output_sha256": s, "output_bytes": int(b)}, sort_keys=True))
EOF
exit $RC
