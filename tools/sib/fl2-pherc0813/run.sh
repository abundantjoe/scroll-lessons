#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restart loop around pipeline.sh (idempotent; finished units are skipped). Gives up after 6 failed passes,
# records the failure in STATUS.md and pushes it. Launch: setsid nohup bash tools/sib/fl2-pherc0813/run.sh > /work/fl2/run.log 2>&1 &
REPO=/home/user/dominion; L=$REPO/logs/sib/fl2-pherc0813
mkdir -p /work/fl2
[ -f /work/fl2/ALLDONE ] && exit 0
for i in 1 2 3 4 5 6; do
  bash $REPO/tools/sib/fl2-pherc0813/pipeline.sh && exit 0
  echo "[$(date -u +%FT%TZ)] pipeline pass $i failed; retry in 120 s"; sleep 120
done
printf '%s | FAILED after 6 passes; see /work/fl2/run.log (tail in run_tail.log)\n' "$(date -u +%FT%TZ)" > $L/STATUS.md
tail -n 60 /work/fl2/run.log > $L/run_tail.log 2>/dev/null || true
cd $REPO && git add logs/sib/fl2-pherc0813 && git commit -q -F - <<MSG && git push -q origin claude/gifted-bell-gavnl5-sib-handed
fl2-pherc0813: pipeline failed after 6 passes

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01AzryPCp51bY9mCGLY8nFwg
MSG
