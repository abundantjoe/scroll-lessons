#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-E E2 driver: tiles in batches of 40 eligible tiles (push after each), level-1 cross-check of r0 c0, manifest.
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=logs/sib/pairs0814b/e2; PY=/opt/hv/bin/python; B=claude/gifted-bell-gavnl5-sib-pairs0814b
git show e25635c:logs/sib/p4-tiles-a/grid.json > /work/e2/strip_a_grid.json
git show e25635c:logs/sib/p4-tiles-a/manifest.json > /work/e2/strip_a_manifest.json
log() { python3 - "$@" <<'PY'
import json, sys; open("logs/sib/pairs0814b/runs.jsonl", "a").write(json.dumps({"utc_start": sys.argv[1], "utc_end": sys.argv[2], "command": sys.argv[4:], "exit_code": int(sys.argv[3])}) + "\n")
PY
}
push() {
  local i
  git add $E tools/sib/pairs0814b logs/sib/pairs0814b/runs.jsonl
  git diff --cached --quiet && return 0
  git commit -q -F - <<MSG
sib pairs0814b: P4-E E2 $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NfS4bhpLVnt2ShveEY6pYF
MSG
  for i in 1 2 3 4 5; do git push -q -u origin $B && return 0; sleep $((2**i)); done
  echo "push refused/failed $(date -u +%FT%TZ)" >> $E/push_failures.log
}
mapfile -t EL < <(python3 -c "
import json; [print('%d,%d' % (t['r'], t['c'])) for t in json.load(open('/work/e2/strip_a_manifest.json'))['tiles']]")
n=${#EL[@]}
for ((i=0; i<n; i+=40)); do
  only=$(IFS=';'; echo "${EL[*]:i:40}")
  s=$(date -u +%FT%TZ); $PY tools/sib/pairs0814b/e2_tiles.py /work/e2/mesh $E --only "$only" >> /work/e2/run.log 2>&1; rc=$?
  log "$s" "$(date -u +%FT%TZ)" $rc $PY tools/sib/pairs0814b/e2_tiles.py /work/e2/mesh $E --only "batch $((i/40+1)): ${EL[i]}..."
  push "tiles batch $((i/40+1)) ($(ls $E/tiles | wc -l) tiles)"
done
# ineligible tiles: census rows only (no pixels read)
s=$(date -u +%FT%TZ); $PY tools/sib/pairs0814b/e2_tiles.py /work/e2/mesh $E >> /work/e2/run.log 2>&1; log "$s" "$(date -u +%FT%TZ)" $? e2_tiles.py census remainder
mkdir -p /work/e2/l1
s=$(date -u +%FT%TZ); $PY tools/sib/pairs0814b/e2_tiles.py /work/e2/mesh /work/e2/l1 --level 1 --only "0,0" --tag _L1 >> /work/e2/run.log 2>&1; log "$s" "$(date -u +%FT%TZ)" $? e2_tiles.py level-1 check r0 c0
s=$(date -u +%FT%TZ); $PY tools/sib/pairs0814b/e2_finalize.py $E /work/e2/strip_a_grid.json /work/e2/strip_a_manifest.json /work/e2/l1/census_L1.jsonl >> /work/e2/run.log 2>&1; log "$s" "$(date -u +%FT%TZ)" $? e2_finalize.py
push "manifest.json, grid.json, census"
echo E2_DONE >> /work/e2/run.log
