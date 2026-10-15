#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/flb/DONE exists (max 8 attempts). Launch:
#   setsid nohup bash tools/sib/fl-pherc0175b/watchdog.sh >/dev/null 2>&1 < /dev/null &
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/flb
for a in 1 2 3 4 5 6 7 8; do
  [ -f /work/flb/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/flb/watchdog.log
  bash "$H/pipeline.sh" >> /work/flb/pipeline.out 2>&1
  [ -f /work/flb/DONE ] && exit 0; sleep 300
done
