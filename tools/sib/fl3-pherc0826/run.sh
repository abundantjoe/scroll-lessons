#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restart loop around pipeline.sh (idempotent). Gives up after 6 failed passes and pushes a FAILED line.
mkdir -p /work/fl3
for i in 1 2 3 4 5 6; do
  [ -f /work/fl3/ALLDONE ] && exit 0
  bash /home/user/dominion/tools/sib/fl3-pherc0826/pipeline.sh && exit 0
  echo "[$(date -u +%FT%TZ)] pipeline pass $i failed; retry in 120 s"; sleep 120
done
printf '%s | fl3-pherc0826 | FAILED after 6 passes; see /work/fl3/run.log\n' "$(date -u +%FT%TZ)" >> /home/user/dominion/logs/sib/fl3-pherc0826/STATUS.md
cd /home/user/dominion && git add logs/sib/fl3-pherc0826 && git commit -qm "fl3-pherc0826: pipeline failed after 6 passes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q origin claude/gifted-bell-gavnl5-sib-p4-pig-cu
