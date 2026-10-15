#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/flx/DONE exists (max 8 attempts). Start detached:
#   nohup setsid bash tools/sib/fl-pherc0483b/watchdog.sh >/dev/null 2>&1 &
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/flx
for a in 1 2 3 4 5 6 7 8; do
  [ -f /work/flx/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/flx/watchdog.log
  bash "$H/pipeline.sh" >> /work/flx/pipeline.out 2>&1
  [ -f /work/flx/DONE ] && exit 0; sleep 120
done
