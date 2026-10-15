#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Watchdog: (re)starts pipeline.sh until logs/sib/fl-pherc1545/PIPELINE_DONE exists; at most 6 attempts.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/fl-pherc1545
mkdir -p /work/fl $L; echo $$ > /work/fl/watchdog.pid; n=0
while [ ! -f $L/PIPELINE_DONE ] && [ $n -lt 6 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> $L/pipeline.log
  bash $REPO/tools/sib/fl-pherc1545/pipeline.sh >> /work/fl/pipeline.out 2>&1
  [ -f $L/PIPELINE_DONE ] || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$([ -f $L/PIPELINE_DONE ] && echo yes || echo no), attempts=$n)" >> $L/pipeline.log
