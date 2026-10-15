#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog (template fl-pherc0257 @54b29c96): (re)starts fl2/pipeline.sh until PIPELINE_DONE exists; at most 6 attempts.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/fl-pherc0191/fl2
mkdir -p /work/fl2 $L; echo $$ > /work/fl2/watchdog.pid; n=0
while [ ! -f $L/PIPELINE_DONE ] && [ $n -lt 6 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> $L/pipeline.log
  bash $REPO/tools/sib/fl-pherc0191/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1
  [ -f $L/PIPELINE_DONE ] || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$([ -f $L/PIPELINE_DONE ] && echo yes || echo no), attempts=$n)" >> $L/pipeline.log
touch /work/fl2/WATCHDOG_EXIT
