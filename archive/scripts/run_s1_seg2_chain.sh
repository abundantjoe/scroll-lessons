#!/bin/sh
cd /home/user/megara
until grep -q -E "S1_V5_DONE" /tmp/s1v5.log; do sleep 60; done
scripts/run_s1_seg.sh 20231210121321 24 84
