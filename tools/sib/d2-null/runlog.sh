#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Usage: runlog.sh LABEL CMD...   Runs CMD, saves combined output to logs/sib/d2-null/out/<utc>_<LABEL>.log and
# appends {utc_start, utc_end, label, command, exit_code, output_path, output_sha256} to logs/sib/d2-null/runs.jsonl.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
LOGD="$REPO/logs/sib/d2-null"; mkdir -p "$LOGD/out"
label=$1; shift
t0=$(date -u +%Y-%m-%dT%H:%M:%SZ); ts=$(date -u +%Y%m%dT%H%M%SZ)
out="$LOGD/out/${ts}_${label}.log"
"$@" > "$out" 2>&1; rc=$?
t1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sha=$(sha256sum "$out" | cut -d' ' -f1)
/usr/local/bin/python3 - "$LOGD/runs.jsonl" "$t0" "$t1" "$label" "$rc" "${out#$REPO/}" "$sha" "$@" <<'PY'
import json, sys
p, t0, t1, label, rc, out, sha, *cmd = sys.argv[1:]
open(p, "a").write(json.dumps(dict(utc_start=t0, utc_end=t1, label=label, command=cmd, exit_code=int(rc),
                                   output_path=out, output_sha256=sha)) + "\n")
PY
exit $rc
