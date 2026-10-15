#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/flp/DONE exists (max 6 attempts).
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/flp
for a in 1 2 3 4 5 6; do
  [ -f /work/flp/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/flp/watchdog.log
  bash "$H/pipeline.sh" >> /work/flp/pipeline.out 2>&1
  [ -f /work/flp/DONE ] && exit 0; sleep 120
done
