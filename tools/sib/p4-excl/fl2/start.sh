#!/bin/bash
# wait for the in-flight setup_env.sh, then run the watchdog (DECL-FL-2 p4-excl PHerc0826)
while kill -0 $(cat /work/fl2/setup.pid) 2>/dev/null; do sleep 20; done
tail -n 2 /work/fl2/setup_env.log >> /work/fl2/start.log
cd /home/user/dominion && exec bash tools/sib/p4-excl/fl2/watchdog.sh
