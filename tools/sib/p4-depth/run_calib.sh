#!/bin/sh
# Provenance: Project HERCULES | owner the owner | [id removed]
# Control-only depth calibration workers (DECL-P4-12-A3 item 1).
cd "$(dirname "$0")/../../.."
N=${N:-3}
k=0
while [ $k -lt $N ]; do
  nohup python3 tools/sib/p4-depth/depth.py calib /home/user/work/ctlmesh /home/user/work/cal /home/user/work/thresholds.json \
    --worker $k --nworkers $N --threads 24 > /home/user/work/cal/run_w$k.log 2>&1 &
  k=$((k+1))
done
