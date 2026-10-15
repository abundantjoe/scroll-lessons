#!/bin/sh
# GATE-S1 driver (RULES.md). One crop at a time, disk-bounded, idempotent. TRAIN first (template measurement), then held-out crops.
cd /home/user/megara
SEG=20231005123336; P=2.4
B=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com
Z="$B/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels.png
until test -f $CJ; do sleep 20; done
K0=2; K1=82
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name; mkdir -p $D
  y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
  x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
  y1=$((y0+6250)); x1=$((x0+6250))
  if ! test -f $D/s_top_v1a.npy; then
    .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
    test -f $D/topo.done || .venv/bin/python scripts/topo_faces.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D --tile 1024 || exit 1
    test -f $D/residual_v0.1b.done || .venv/bin/python scripts/residual.py $D $P --tag v0.1b || exit 1
    .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB v0.1b $P || exit 1
    if [ "$name" = train ]; then
      .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1a_template_from_w028.json --tag v1a --dump || exit 1
      .venv/bin/python scripts/s1_template.py measure $D stats/s1_v1b_template_train.json || exit 1
      rm -f $D/I_stack_top.npy $D/I_stack_bot.npy
      .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1b_template_train.json --tag v1b || exit 1
    else
      .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1a_template_from_w028.json --tag v1a || exit 1
      .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1b_template_train.json --tag v1b || exit 1
    fi
    rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
    rm -f $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy
  fi
  .venv/bin/python scripts/v03p.py $D $P || exit 1
  .venv/bin/python scripts/s1_team_comparator.py $D $CJ $name data/s1/$SEG/overview/ink_ds8.jpg || exit 1
  for tag in v1a v1b v0.3p team; do test -f $D/judge_$tag.json || .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB $tag $P || exit 1; done
  echo "$name S1 done $(date)"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo S1_DONE
