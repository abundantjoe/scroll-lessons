#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# CHAIN VALID runner (DECL-CHAINVALID). Refuses to run inference unless /work/cv/GO exists (written only after the
# orchestrator's GO and the chain2um gate report). Resumable: a crop whose two map.npz exist is skipped.
# usage: run_chainvalid.sh primary|secondary PRECISION [--dry-run]
set -u
SET=$1; PREC=$2; DRY=${3:-}
R=/home/user/dominion; T=$R/tools/sib/reg0841/chainvalid; C=$R/tools/sib/reg0841na/chain2um_copy
LOG=$R/tools/sib/reg0841na/run.sh
V=s3://vesuvius-challenge-open-data/PHerc0841/volumes/20260319124803-2.403um-0.2m-77keV-masked.zarr/
CK=/work/ckpt/ink_canonical_2um/r152_3ddec_v2_l5_epoch13.ckpt
if [ "$DRY" != "--dry-run" ] && [ ! -f /work/cv/GO ]; then echo "REFUSED: /work/cv/GO missing (no GO from the orchestrator)"; exit 3; fi
run() { if [ "$DRY" = "--dry-run" ]; then echo "DRY: $*"; else "$@"; fi; }
/opt/hv/bin/python -c "
import json; p=json.load(open('$R/logs/sib/reg0841/chainvalid_plan.json'))
for c in p['crops_$SET']: print(c['segment'], c['y'], c['x'])" | while read seg y x; do
  out=/work/cv/maps; rz=/work/cv/render/${seg}_${y}_${x}.zarr
  if [ -f $out/reverse/$seg/${y}_${x}/map.npz ] && [ -f $out/forward/$seg/${y}_${x}/map.npz ]; then echo "skip $seg $y $x"; continue; fi
  run $LOG cv_render_${seg}_${y}_${x} /work/bin/vc vc_render_tifxyz -v $V --remote-url $V --segmentation /work/cv/mesh/$seg \
    --scale 1 --group-idx 0 --num-slices 63 --slice-step 1 --voxel-size 2.403 --voxel-unit micrometer --flip-normals \
    --crop-x $x --crop-y $y --crop-width 2048 --crop-height 2048 --cache-gb 4 --zarr-output $rz || exit 1
  for d in reverse forward; do
    run $LOG cv_infer_${d}_${seg}_${y}_${x} env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python $C/infer2um.py --render $rz --ckpt $CK \
      --out $out/$d/$seg/${y}_${x} --direction $d --precision $PREC --start 0 --layers 62 --tile 256 --stride 128 --batch 1 \
      --threads 4 --parts 5 || exit 1
  done
  # the render is kept: orchestrator 2026-09-26, no deletion without approval
done
run $LOG cv_eval_$SET /opt/hvz/bin/python $T/cv_eval.py /work/cv/maps $R/logs/sib/reg0841/chainvalid/eval_${SET}_${PREC}.json
