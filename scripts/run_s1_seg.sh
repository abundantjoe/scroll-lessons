#!/bin/sh
# Cross-segment transfer: apply the segment-1-trained models (v1b template, v2 config, v3 weights, v5 U-Net) to another labelled segment's crops.
# Usage: run_s1_seg.sh <SEG> <K0> <K1>. All crops are held-out here (nothing is fitted). Sequential, disk-bounded, idempotent.
cd "$(dirname "$0")/.."
SEG=$1; K0=$2; K1=$3; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels_L.png; test -f $LAB || LAB=data/s1/labels/${SEG}_inklabels.png
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
until test -f $CJ; do sleep 20; done
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
    .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1a_template_from_w028.json --tag v1a || exit 1
    rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
    .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB v1b $P || exit 1
    .venv/bin/python scripts/s1_ds_stack.py $D || exit 1
    .venv/bin/python scripts/s1_v3.py apply $D $P stats/s1_v3_weights.json || exit 1
    rm -f $D/I_stack_top.npy $D/I_stack_bot.npy $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy
  fi
  .venv/bin/python scripts/v03p.py $D $P || exit 1
  .venv/bin/python scripts/s1_team_comparator.py $D $CJ $name data/s1/$SEG/overview/ink_ds8.jpg || exit 1
  .venv/bin/python scripts/s1_v2.py apply $D $P stats/s1_v2_config.json || exit 1
  .venv/bin/python scripts/s1_v5.py predict $D data/s1/20231005123336/v5_unet.pt || exit 1
  for tag in v0.1b v1a v1b v0.3p team v2 v3 v5; do test -f $D/judge_$tag.json || .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB $tag $P || exit 1; done
  for t in v2 v3 v5 v0.3p team; do f=$D/s_top_$t.npy; if [ -f "$f" ] && [ ! -L "$f" ]; then rm -f "$f"; ln -s s_bot_$t.npy "$f"; fi; done
  rm -f $D/proj_top_v1b.npy $D/S_top.npy $D/S_bot.npy $D/onsheet.npy $D/valid.npy $D/damage_d.npy $D/k_top.npy $D/k_bot.npy $D/peak.npy $D/s_*_u8.npy
  echo "$name $SEG done $(date)"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo SEG_DONE
