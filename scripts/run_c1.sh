#!/bin/sh
# Confirmation test C1 (RULES.md, declared 2026-10-15): untouched labelled windows, frozen weights, judged once.
# Prepares each window exactly as the evaluation crops were prepared (run_s1_seg.sh), then predicts with the frozen
# v8, GP-R1 and v7, builds the declared ensemble E, runs the team comparator, and judges every tag with the unchanged judge.
cd "$(dirname "$0")/.."
P=2.4
B=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments
for SPEC in "20231005123336 2 82" "20231210121321 24 84"; do
  set -- $SPEC; SEG=$1; K0=$2; K1=$3
  CJ=data/s1/$SEG/confirm.json
  LAB=data/s1/labels/${SEG}_inklabels_L.png; test -f $LAB || LAB=data/s1/labels/${SEG}_inklabels.png
  Z=$B/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
  for name in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('$CJ'))['crops']))"); do
    D=data/s1/$SEG/derived/$name; mkdir -p $D
    y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
    x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
    y1=$((y0+6250)); x1=$((x0+6250))
    if ! test -f $D/ds8_x.npy; then
      .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
      test -f $D/topo.done || .venv/bin/python scripts/topo_faces.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D --tile 1024 || exit 1
      test -f $D/residual_v0.1b.done || .venv/bin/python scripts/residual.py $D $P --tag v0.1b --edge-margin-mm 0.1 || exit 1
      .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1b_template_train.json --tag v1b --dump || exit 1
      rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
      .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB v1b $P || exit 1
      .venv/bin/python scripts/s1_ds_stack.py $D || exit 1
      rm -f $D/I_stack_top.npy $D/I_stack_bot.npy $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy
      rm -f $D/S_top.npy $D/S_bot.npy $D/onsheet.npy $D/valid.npy $D/damage_d.npy $D/k_top.npy $D/k_bot.npy $D/peak.npy $D/ct_mid.npy $D/s_*_u8.npy $D/proj_*.npy
    fi
    .venv/bin/python scripts/s1_team_comparator.py $D $CJ $name data/s1/$SEG/overview/ink_ds8.jpg || exit 1
    OMP_NUM_THREADS=3 .venv/bin/python scripts/s1_v5.py predict $D data/s1/v8_unet.pt v8 || exit 1
    OMP_NUM_THREADS=3 .venv/bin/python scripts/gpr.py predict $D data/s1/gpr1.pt gpr1 || exit 1
    OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v7.py apply $D stats/s1_v7_weights.json || exit 1
    .venv/bin/python scripts/ensemble_e.py $SEG:$name || exit 1
    for tag in v8 gpr1 v7 e team; do
      .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB $tag $P || exit 1
    done
    rm -f $D/s_top_v7.npy $D/s_top_v8.npy $D/s_top_gpr1.npy
    echo "C1 $SEG $name done $(date -u)"
  done
done
S=""
for SEG in 20231005123336 20231210121321; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/$SEG/confirm.json'))['crops']))"); do S="$S $SEG:$n"; done
done
.venv/bin/python scripts/stroke_test.py $S
.venv/bin/python scripts/local_stroke_test.py $S
echo C1_JUDGED
