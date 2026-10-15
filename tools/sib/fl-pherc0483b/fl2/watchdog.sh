#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-2 watchdog for fl-pherc0483b (from fl-pherc0257 @54b29c96): reruns pipeline.sh (idempotent) until /work/fl2/STOP
# exists. After a failed run it waits 5 min (gives up after 6 consecutive failures); after a complete pass it re-checks every
# 20 min, so a DENSE arm enabled later (/work/fl2/dense.env) still reaches every kept segment.
# Launch: setsid nohup bash tools/sib/fl-pherc0483b/fl2/watchdog.sh >/dev/null 2>&1 &
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/fl-pherc0483b/fl2
mkdir -p /work/fl2 $L; echo $$ > /work/fl2/watchdog.pid; fails=0; n=0
while [ ! -f /work/fl2/STOP ] && [ $fails -lt 6 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: run $n" >> $L/pipeline.log
  if bash $REPO/tools/sib/fl-pherc0483b/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1; then fails=0; sleep 1200; else fails=$((fails+1)); sleep 300; fi
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (stop=$([ -f /work/fl2/STOP ] && echo yes || echo no), consecutive failures=$fails, runs=$n)" >> $L/pipeline.log
touch /work/fl2/WATCHDOG_EXITED
