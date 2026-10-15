#!/bin/sh
cd /home/user/megara
scripts/run_s1_seg2_chain.sh >> /tmp/s1seg2.log 2>&1 || echo SEG2_FAILED
scripts/run_s1_v6.sh >> /tmp/s1v6.log 2>&1 || echo V6_FAILED
echo MASTER3_DONE
