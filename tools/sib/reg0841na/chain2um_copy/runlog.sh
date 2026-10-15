#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Usage: runlog.sh <label> <output-file-or-dash> <command...>
# Runs the command, then appends {utc_start, utc_end, label, command, exit_code, output, output_sha256} to logs/sib/chain2um/runs.jsonl.
L=/home/user/dominion/logs/sib/chain2um/runs.jsonl
label="$1"; out="$2"; shift 2
t0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@"; rc=$?
t1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
h=null; [ "$out" != "-" ] && [ -f "$out" ] && h="\"$(sha256sum "$out" | cut -d' ' -f1)\""
python3 -c 'import json,sys; print(json.dumps({"utc_start":sys.argv[1],"utc_end":sys.argv[2],"label":sys.argv[3],"command":sys.argv[4],"exit_code":int(sys.argv[5]),"output":sys.argv[6],"output_sha256":json.loads(sys.argv[7])}))' "$t0" "$t1" "$label" "$*" "$rc" "$out" "$h" >> "$L"
exit $rc
