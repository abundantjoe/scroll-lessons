#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Parent worker after the bf16 check FAILED (fp32 only), with ckpt-screen-b at 98cd075 (bounded chunk reads).
# Resumable: finished tiles are skipped; a tile in progress resumes from its 15-min checkpoint.
R=/home/user/dominion; T=$R/tools/sib/ckpt-screen-c
export OMP_NUM_THREADS=4 CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf P4O_WORK=/work/p4o_c/fp32
/opt/hv-1667/bin/python $T/p4o_run.py --tiles "${1:-1,5;0,6;1,6}" --out $R/logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4 --precision fp32
echo PARENT_DONE
