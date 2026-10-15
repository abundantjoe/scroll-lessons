#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-L driver: 4 tile workers (r0-r1 first), commit + push every >= 10 new tiles with a partial manifest.
set -u
R=/home/user/dominion; L=$R/logs/sib/p4-l2/l2; W=/work/l2; B=claude/gifted-bell-gavnl5-sib-p4-l2
TOOL=$R/tools/sib/p4-l2
for k in 0 1 2 3; do
  nohup python3 $TOOL/l2.py tiles $W/mesh_e2 $L $L/thresholds.json --ref-manifest $W/ref/e2_manifest.json \
    --worker $k --nworkers 4 --threads 16 >> $W/tiles_w$k.log 2>&1 &
done
push() {
  python3 $TOOL/l2_manifest.py $L $W/ref/e2_manifest.json $W/ref/e2_grid.json $W/mesh_e2 >> $W/manifest.log 2>&1
  git -C $R add logs/sib/p4-l2 tools/sib/p4-l2
  git -C $R diff --cached --quiet && return 0
  git -C $R commit -q -F - <<MSG
p4-l2: P4-L tiles $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VYfh6gj6Kr8Qyurerayy9B
MSG
  for i in 1 2 3 4 5; do git -C $R push -q origin $B 2>>$W/push.log && return 0; sleep $((2**i)); done
  echo "push failed $(date -u +%FT%TZ)" >> $W/push.log
}
last=0
while :; do
  n=$(cat $L/census_w*.jsonl 2>/dev/null | wc -l)
  alive=$(pgrep -f "l2.py tiles" | wc -l)
  if [ "$n" -ge $((last + 10)) ] || { [ "$alive" -eq 0 ] && [ "$n" -gt "$last" ]; }; then
    push "($n of 160)"; last=$n
  fi
  [ "$alive" -eq 0 ] && break
  sleep 20
done
push "($n of 160, final)"
echo "DRIVER_DONE $(date -u +%FT%TZ) n=$n" >> $W/manifest.log
