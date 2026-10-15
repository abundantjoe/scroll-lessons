#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# pairs0139b copy of tools/sib/pairs0139/run.sh: identical except rows go to logs/sib/pairs0139b/runs.jsonl and
# outputs to /work/p139b/runlogs. Usage: run.sh <tag> <cmd...>
set -u
REPO=/home/user/dominion
tag="$1"; shift
mkdir -p /work/p139b/runlogs
out=/work/p139b/runlogs/$(date -u +%Y%m%dT%H%M%SZ)_$tag.log
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$out" 2>&1
rc=$?
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sha=$(sha256sum "$out" | cut -d' ' -f1)
python3 - "$tag" "$start" "$end" "$rc" "$sha" "$out" "$*" >> "$REPO/logs/sib/pairs0139b/runs.jsonl" <<'PY'
import json, sys
t, s, e, rc, sha, out, cmd = sys.argv[1:8]
print(json.dumps(dict(tag=t, utc_start=s, utc_end=e, command=cmd, exit=int(rc), output=out, output_sha256=sha)))
PY
tail -n 40 "$out"
exit $rc
