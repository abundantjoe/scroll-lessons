#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog: (re)starts pipeline.sh until logs/sib/p4v-15/fl2/PIPELINE_DONE exists for the current arms; at most 6 attempts.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/p4v-15/fl2
mkdir -p /work/fl2 $L; echo $$ > /work/fl2/watchdog.pid; n=0
want() { [ -f /work/fl2/dense/dense.env ] && echo "official dense" || echo "official"; }
done_() { [ -f $L/PIPELINE_DONE ] && [ "$(cat $L/PIPELINE_DONE)" = "$(want)" ]; }
while ! done_ && [ $n -lt 6 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> $L/pipeline.log
  bash $REPO/tools/sib/p4v-15/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1
  done_ || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$(done_ && echo yes || echo no), attempts=$n)" >> $L/pipeline.log
