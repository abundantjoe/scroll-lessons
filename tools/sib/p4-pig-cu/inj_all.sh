#!/bin/bash
# p4-pig-cu: injection-recovery on all materials with the frozen code. Provenance: Project HERCULES | owner the owner | [id removed]
cd /home/user/dominion
export CU_SCRATCH=/tmp/claude-0/sp/cu
mkdir -p logs/sib/p4-pig-cu/injection
for M in E2 C2 E1 C1; do
  nice -n 15 python3 tools/sib/p4-pig-cu/inject.py $M logs/sib/p4-pig-cu/injection/inj_$M.jsonl >> /tmp/claude-0/sp/inj_$M.log 2>&1
done
echo ALLDONE >> /tmp/claude-0/sp/inj_C1.log
