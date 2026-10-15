#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog: (re)starts pipeline.sh until logs/sib/fl2-pherc0846a/PIPELINE_DONE exists; at most 6 attempts.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/fl2-pherc0846a
mkdir -p /work/fl2_0846a $L; echo $$ > /work/fl2_0846a/watchdog.pid; n=0
while [ ! -f $L/PIPELINE_DONE ] && [ $n -lt 6 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> $L/pipeline.log
  bash $REPO/tools/sib/fl2-pherc0846a/pipeline.sh >> /work/fl2_0846a/pipeline.out 2>&1
  [ -f $L/PIPELINE_DONE ] || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$([ -f $L/PIPELINE_DONE ] && echo yes || echo no), attempts=$n)" >> $L/pipeline.log
