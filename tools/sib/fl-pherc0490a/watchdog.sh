#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/fl0490a/DONE exists (max 8 attempts). Launch detached:
#   setsid nohup bash tools/sib/fl-pherc0490a/watchdog.sh >/dev/null 2>&1 < /dev/null &
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/fl0490a
exec 9>/work/fl0490a/watchdog.lock; flock -n 9 || exit 0   # one watchdog only
for a in 1 2 3 4 5 6 7 8; do
  [ -f /work/fl0490a/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/fl0490a/watchdog.log
  bash "$H/pipeline.sh" >> /work/fl0490a/pipeline.out 2>&1
  [ -f /work/fl0490a/DONE ] && exit 0; sleep 300
done
