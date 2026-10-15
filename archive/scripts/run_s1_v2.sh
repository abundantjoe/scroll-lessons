#!/bin/sh
# S1-v2: wait for held1's raw to be gone, refetch TRAIN, regenerate proj (v1b), select on TRAIN, then apply to held crops as they finish.
cd /home/user/megara
SEG=20231005123336; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels.png
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
until grep -q "held1 S1 done" /tmp/s1.log; do sleep 30; done
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name
  if ! test -f $D/proj_bot_v1b.npy; then
    y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
    x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
    y1=$((y0+6250)); x1=$((x0+6250))
    .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
    .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 2 82 $D $P --template stats/s1_v1b_template_train.json --tag v1b || exit 1
    rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
  fi
done
D=data/s1/$SEG/derived/train
test -f stats/s1_v2_config.json || .venv/bin/python scripts/s1_v2.py select $D $P stats/s1_v2_config.json || exit 1
.venv/bin/python scripts/s1_v2.py apply $D $P stats/s1_v2_config.json && .venv/bin/python scripts/s1_judge.py $D $CJ train $LAB v2 $P
for name in held1 held2 held3; do
  H=data/s1/$SEG/derived/$name
  until test -f $H/proj_bot_v1b.npy && grep -q "$name S1 done" /tmp/s1.log; do sleep 30; done
  .venv/bin/python scripts/s1_v2.py apply $H $P stats/s1_v2_config.json || exit 1
  .venv/bin/python scripts/s1_judge.py $H $CJ $name $LAB v2 $P || exit 1
  echo "$name v2 done"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo S1_V2_DONE
