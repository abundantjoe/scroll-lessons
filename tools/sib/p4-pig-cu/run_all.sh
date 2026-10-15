#!/bin/bash
# p4-pig-cu: score all materials sequentially with the frozen code (numbers only). Provenance: Project HERCULES | owner the owner | [id removed]
cd /home/user/dominion
export CU_SCRATCH=/tmp/claude-0/sp/cu
for M in E2 C2 C1 E1; do
  python3 tools/sib/p4-pig-cu/cu.py score $M 0-99 logs/sib/p4-pig-cu/scores/$M >> /tmp/claude-0/sp/score_$M.log 2>&1
done
echo ALLDONE >> /tmp/claude-0/sp/score_E1.log
