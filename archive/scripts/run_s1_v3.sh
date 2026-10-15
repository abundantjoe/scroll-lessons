#!/bin/sh
# S1-v3 driver: after v2 finishes, per crop: refetch raw, dump the 11-depth stacks (s1_score --dump), fit on TRAIN / apply on held, judge, delete.
cd /home/user/megara
SEG=20231005123336; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels.png
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
until grep -q -E "S1_V2_DONE" /tmp/s1v2.log; do sleep 30; done
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name; test -f $D/judge_v3.json && continue
  y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
  x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
  y1=$((y0+6250)); x1=$((x0+6250))
  .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
  .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 2 82 $D $P --dump || exit 1
  rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
  if [ "$name" = train ]; then .venv/bin/python scripts/s1_v3.py fit $D $P stats/s1_v3_weights.json || exit 1; fi
  .venv/bin/python scripts/s1_v3.py apply $D $P stats/s1_v3_weights.json || exit 1
  rm -f $D/I_stack_top.npy $D/I_stack_bot.npy
  .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB v3 $P || exit 1
  echo "$name v3 done $(date)"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo S1_V3_DONE
