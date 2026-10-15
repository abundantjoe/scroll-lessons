#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O PHerc.1667-iteration-2, DECL-P4-14-A2 order and precision rule. Idempotent and resumable: re-run after any
# restart (the builder skips finished tiles; the check is skipped once bf16_check.json exists).
#  0. r0 c5 in bf16 (check dir, not pushed) and in fp32 (real tile), then the equivalence check (<= 1 % > 2/255).
#  1..4. stages from ORDER.json, in bf16 if the check passed, else fp32; a partial manifest after every stage.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
export CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf PYTHONPATH=src
T=tools/sib/dev-distft; PY=/opt/hv-ink/bin/python
OUT=logs/sib/dev-distft/p4o/iteration-2
FN=20260701183124-w010-027_r0_c5.png
mkdir -p /work/p4o_bf16
[ -f /work/p4o_bf16/mesh_valid.npy ] || cp /work/p4o/mesh_valid.npy /work/p4o_bf16/
if [ ! -f $OUT/bf16_check.json ]; then
  P4O_WORK=/work/p4o_bf16 $T/runlog.sh p4o_it2_r0c5_bf16 $PY $T/p4o_bf16.py --iteration 2 --tiles "0,5" \
    --out /work/p4o_bf16/check --threads 4 || exit 1
  P4O_WORK=/work/p4o $T/runlog.sh p4o_it2_r0c5_fp32 $PY $T/p4o_resumable.py --iteration 2 --tiles "0,5" \
    --out $OUT --threads 4 || exit 1
  $T/runlog.sh p4o_it2_bf16_check $PY $T/p4o_bf16_check.py /work/p4o/it2/full/$FN.npy \
    /work/p4o_bf16/it2/full/$FN.npy $OUT/bf16_check.json || exit 1
fi
if $PY -c "import json,sys; sys.exit(0 if json.load(open('$OUT/bf16_check.json'))['pass'] else 1)"; then
  RUNNER=$T/p4o_bf16.py; PREC=bf16
else
  RUNNER=$T/p4o_resumable.py; PREC=fp32
fi
echo "{\"precision_after_check\": \"$PREC\", \"r0_c5\": \"fp32\"}" > $OUT/PRECISION.json
for S in stage1 stage2 stage3 stage4; do
  TILES=$($PY -c "import json; print(';'.join(f'{r},{c}' for r,c in json.load(open('$OUT/ORDER.json'))['$S']))")
  P4O_WORK=/work/p4o $T/runlog.sh p4o_it2_$S $PY $RUNNER --iteration 2 --tiles "$TILES" --out $OUT --threads 4 || exit 1
  $T/runlog.sh p4o_it2_finalize_$S $PY $T/p4o_finalize.py $OUT || exit 1
  cp $OUT/manifest.json $OUT/manifest_after_$S.json
  touch /work/p4o/${S}_DONE
done
touch /work/p4o/RUN_DONE
echo P4O_STAGES_DONE
