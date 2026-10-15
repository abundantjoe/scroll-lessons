#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Keeps run_arms.py running (orchestrator 2026-09-30 03:28Z): relaunch it whenever it is not running, until
# /work/own/ALL_DONE exists. Start detached: setsid nohup tools/sib/own-lead/watchdog.sh >> /work/own/watchdog.log 2>&1 < /dev/null &
cd /home/user/dominion
while [ ! -f /work/own/ALL_DONE ]; do
  if [ -f /work/own/PAUSE ]; then sleep 60; continue; fi    # a priority runner (run_O3.sh) holds the CPUs
  if ! pgrep -f "^/opt/ckb/bin/python tools/sib/own-lead/run_arms.py" > /dev/null; then
    echo "$(date -u +%FT%TZ) launching run_arms.py"
    setsid nohup /opt/ckb/bin/python tools/sib/own-lead/run_arms.py --pred-threads 2 >> /work/own/run_arms.log 2>&1 < /dev/null &
  fi
  sleep 120
done
echo "$(date -u +%FT%TZ) ALL_DONE present; watchdog exits"
