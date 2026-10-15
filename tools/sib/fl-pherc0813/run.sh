#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restart loop around pipeline.sh (idempotent). Gives up after 6 failed passes.
mkdir -p /work/fl
for i in 1 2 3 4 5 6; do
  bash /home/user/dominion/tools/sib/fl-pherc0813/pipeline.sh && exit 0
  echo "[$(date -u +%FT%TZ)] pipeline pass $i failed; retry in 120 s"; sleep 120
done
printf '%s | FAILED after 6 passes; see /work/fl/run.log\n' "$(date -u +%FT%TZ)" > /home/user/dominion/logs/sib/fl-pherc0813/STATUS.md
cd /home/user/dominion && git add logs/sib/fl-pherc0813 && git commit -qm "fl-pherc0813: pipeline failed after 6 passes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q origin claude/gifted-bell-gavnl5-sib-fl-pherc0813
