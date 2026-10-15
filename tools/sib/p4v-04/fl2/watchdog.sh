#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog (template fl-pherc0257 watchdog.sh, paths changed): (re)starts pipeline.sh until PIPELINE_DONE, or until the
# official pass is complete while the DENSE arm is not yet enabled (relaunched then); at most 6 attempts.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/p4v-04/fl2
mkdir -p /work/fl2 $L; echo $$ > /work/fl2/watchdog.pid; n=0
while [ ! -f $L/PIPELINE_DONE ] && [ $n -lt 6 ]; do
  [ -f $L/OFFICIAL_DONE ] && [ ! -f /work/fl2/dense.env ] && break
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> $L/pipeline.log
  bash $REPO/tools/sib/p4v-04/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1
  [ -f $L/PIPELINE_DONE ] || [ -f $L/OFFICIAL_DONE ] || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$([ -f $L/PIPELINE_DONE ] && echo yes || echo no), official=$([ -f $L/OFFICIAL_DONE ] && echo yes || echo no), attempts=$n)" >> $L/pipeline.log
touch /work/fl2/watchdog.exited
