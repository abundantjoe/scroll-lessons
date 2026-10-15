#!/bin/sh
# S1-v5 driver: after v3, per crop refetch raw -> dump face-aligned stacks -> pool 8x -> delete; train on TRAIN; predict + judge all.
cd /home/user/megara
SEG=20231005123336; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels.png
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
until grep -q -E "STAGE3_OK|STAGE3_FAILED" /tmp/s1rj.log; do sleep 60; done
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name; test -f $D/ds8_x.npy && continue
  y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
  x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
  y1=$((y0+6250)); x1=$((x0+6250))
  .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
  .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 2 82 $D $P --dump || exit 1
  rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
  .venv/bin/python scripts/s1_ds_stack.py $D || exit 1
  rm -f $D/I_stack_top.npy $D/I_stack_bot.npy
  echo "$name ds8 done $(date)"
done
test -f data/s1/$SEG/v5_unet.pt || .venv/bin/python scripts/s1_v5.py train data/s1/$SEG/derived/train data/s1/$SEG/v5_unet.pt || exit 1
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name
  .venv/bin/python scripts/s1_v5.py predict $D data/s1/$SEG/v5_unet.pt || exit 1
  .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB v5 $P || exit 1
  echo "$name v5 done"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo S1_V5_DONE
