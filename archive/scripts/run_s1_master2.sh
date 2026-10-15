#!/bin/sh
# Sequential chain from v5 onward: v5 -> segment-2 transfer -> extra-segment prep + v6.
cd /home/user/megara
scripts/run_s1_v5.sh >> /tmp/s1v5.log 2>&1 || echo V5_FAILED
scripts/run_s1_seg2_chain.sh >> /tmp/s1seg2.log 2>&1 || echo SEG2_FAILED
scripts/run_s1_v6.sh >> /tmp/s1v6.log 2>&1 || echo V6_FAILED
echo MASTER2_DONE
