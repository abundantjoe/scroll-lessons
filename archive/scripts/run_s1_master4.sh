#!/bin/sh
# Mask-J recomputation: segment 1 (all 4 crops), segment 2 (4 crops), then v6 (extra-segment prep + training + held-out judging).
cd /home/user/megara
scripts/run_s1_seg.sh 20231005123336 2 82 >> /tmp/s1seg1b.log 2>&1 || echo SEG1_FAILED
scripts/run_s1_seg.sh 20231210121321 24 84 >> /tmp/s1seg2.log 2>&1 || echo SEG2_FAILED
scripts/run_s1_v6.sh >> /tmp/s1v6.log 2>&1 || echo V6_FAILED
echo MASTER4_DONE
