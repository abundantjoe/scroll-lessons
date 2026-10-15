#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog (DECL-FL-2, p4v-01): (re)runs pipeline.sh until /work/fl2/STOP exists. Finished units are skipped, so a pass
# after the seed list is exhausted only picks up late work (e.g. the dense arm once enabled). 10 min between passes.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/p4v-01/fl2
mkdir -p /work/fl2 $L; echo $$ > /work/fl2/watchdog.pid; n=0
while [ ! -f /work/fl2/STOP ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: pass $n" >> $L/pipeline.log
  bash $REPO/tools/sib/p4v-01/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1
  [ -f /work/fl2/STOP ] || sleep 600
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (STOP), passes=$n" >> $L/pipeline.log
