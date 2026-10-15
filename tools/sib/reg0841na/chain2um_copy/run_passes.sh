#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Sequential chain2um inference passes on the w043 control (resumable: rerun this script after a restart).
set -u
R=/home/user/dominion; T=$R/tools/sib/chain2um
CK=/work/ckpt/ink_canonical_2um/r152_3ddec_v2_l5_epoch13.ckpt
for spec in "$@"; do
  d=${spec%%:*}; p=${spec##*:}; out=/work/c2um/maps/${d}_${p}
  [ -f $out/summary.json ] && { echo "skip $spec"; continue; }
  $T/runlog.sh infer_${d}_${p} $out/map.npz env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python $T/infer2um.py \
    --render /work/c2um/render/w043_n63.zarr --ckpt $CK --out $out --direction $d --precision $p \
    --start 0 --layers 62 --tile 256 --stride 128 --batch 1 --threads 4 --parts 10 > /work/logs/infer_${d}_${p}.log 2>&1
  echo "$spec rc=$?"
done
