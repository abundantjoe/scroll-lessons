#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Parent worker (resumable; finished tiles are skipped, a tile in progress resumes from its 15-min checkpoint):
# 1. r0 c5 fp32 into the material; 2. r0 c5 bf16 into a check dir outside the material; 3. equivalence check
# (DECL-P4-14-A2 item 2); 4. the parent's remaining stage-(i) tiles in the precision the check allows.
set -uo pipefail
R=/home/user/dominion; T=$R/tools/sib/ckpt-screen-c; PY=/opt/hv-1667/bin/python
OUT=$R/logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4; CHK=/work/p4o_c/bf16check
export OMP_NUM_THREADS=4 CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf
P4O_WORK=/work/p4o_c/fp32 $PY $T/p4o_run.py --tiles "0,5" --out $OUT --precision fp32
P4O_WORK=/work/p4o_c/bf16 $PY $T/p4o_run.py --tiles "0,5" --out $CHK --precision bf16
$PY $T/p4o_bf16check.py /work/p4o_c/fp32 /work/p4o_c/bf16 $R/logs/sib/ckpt-screen-c/p4o/bf16_check.json
P=$(python3 -c "import json;print('bf16' if json.load(open('$R/logs/sib/ckpt-screen-c/p4o/bf16_check.json'))['pass'] else 'fp32')")
echo "precision after check: $P"
P4O_WORK=/work/p4o_c/$P $PY $T/p4o_run.py --tiles "1,5;0,6;1,6" --out $OUT --precision $P
echo PARENT_STAGE_I_DONE
