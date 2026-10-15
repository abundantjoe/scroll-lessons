#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Order-naming check: render the same crop WITHOUT --flip-normals, then the official REVERSE order in fp32.
set -u
R=/home/user/dominion; T=$R/tools/sib/chain2um; V=s3://vesuvius-challenge-open-data/PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/
[ -d /work/c2um/render/w043_n63_noflip.zarr ] || $T/runlog.sh render_w043_n63_noflip - /work/bin/vc vc_render_tifxyz -v $V --remote-url $V \
  --segmentation /work/c2um/org/mesh --scale 1 --group-idx 0 --num-slices 63 --slice-step 1 --voxel-size 2.399 --voxel-unit micrometer \
  --crop-x 22016 --crop-y 14208 --crop-width 3456 --crop-height 1408 --cache-gb 4 --zarr-output /work/c2um/render/w043_n63_noflip.zarr > /work/logs/render_noflip.log 2>&1
out=/work/c2um/maps/noflip_reverse_fp32
[ -f $out/summary.json ] || $T/runlog.sh infer_noflip_reverse_fp32 $out/map.npz env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python $T/infer2um.py \
  --render /work/c2um/render/w043_n63_noflip.zarr --ckpt /work/ckpt/ink_canonical_2um/r152_3ddec_v2_l5_epoch13.ckpt --out $out \
  --direction reverse --precision fp32 --start 0 --layers 62 --tile 256 --stride 128 --batch 1 --threads 4 --parts 10 > /work/logs/infer_noflip_reverse_fp32.log 2>&1
echo "noflip rc=$?"
