#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O PHerc.1667-iteration-2 (DECL-P4-14-A1) with ckpt-screen-b's builder byte-identical (p4o_tiles.py sha256
# 5ec64557..., infer_1667.py 431067ee..., from commit ca732aef). Resumable: finished tiles are skipped.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
export P4O_WORK=/work/p4o CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf PYTHONPATH=src
OUT=logs/sib/dev-distft/p4o/iteration-2
TILES=$(cat /work/p4o/tiles_r0-5_c0-17.txt)
tools/sib/dev-distft/runlog.sh p4o_it2_run /opt/hv-ink/bin/python tools/sib/dev-distft/p4o_tiles.py --iteration 2 \
  --tiles "$TILES" --out "$OUT" --threads 4
tools/sib/dev-distft/runlog.sh p4o_it2_finalize /opt/hv-ink/bin/python tools/sib/dev-distft/p4o_tiles.py --finalize \
  --iteration 2 --out "$OUT"
echo P4O_RUN_DONE
