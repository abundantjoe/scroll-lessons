#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A1: re-run run.sh until the lane's ALL_DONE marker exists (keepalive.sh relaunches this if it dies).
# Each loop refreshes the kit from the orchestrator branch, so environment fixes reach every worker without turns.
source /work/fl4/conf.sh; K=$(cd "$(dirname "$0")" && pwd); REPO=$(git -C "$K" rev-parse --show-toplevel); MAIN=origin/claude/gifted-bell-gavnl5
while [ ! -f $REPO/logs/sib/$ME/fl4/$SCROLL/ALL_DONE ]; do
  if git -C $REPO fetch -q origin claude/gifted-bell-gavnl5 2>/dev/null; then
    for f in run.sh setup_gp.sh gp_infer.py fl4.py; do git -C $REPO show $MAIN:tools/fl4/$f > $K/.$f.new 2>/dev/null && [ -s $K/.$f.new ] && mv $K/.$f.new $K/$f; done
  fi
  bash $K/run.sh >> /work/fl4/run.out 2>&1; sleep 60
done
