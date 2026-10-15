#!/bin/sh
# Prepare and judge every crop listed in a crop file with the RELEASED models (v8, GP-R1 -> E, v7, team comparator).
# Usage: scripts/run_judge_crops.sh <SEG> <K0> <K1> <crop-json> [<crop-name> ...]
#   K0/K1 = slice range searched for the sheet faces: 2 82 for 20231005123336, 24 84 for the other Scroll 1 segments.
#   crop-json = data/s1/<SEG>/crops.json (evaluation crops) or data/s1/<SEG>/confirm.json (C1 crops).
# The commands are exactly those of scripts/run_s1_seg.sh / run_c1.sh for these methods. Sequential, disk-bounded (one raw crop of
# ~4.4 GB at a time, deleted after use), idempotent (a prepared crop is not fetched again). 13.6–15.1 min per crop on 4 CPU cores
# (measured for the C1 driver, results/logs/c1.log; not logged for this driver).
set -u
cd "$(dirname "$0")/.."
SEG=$1; K0=$2; K1=$3; CJ=$4; shift 4
P=2.4
LAB=data/s1/labels/${SEG}_inklabels_L.png; test -f $LAB || LAB=data/s1/labels/${SEG}_inklabels.png
Z=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
PY=${PY:-.venv/bin/python}
NAMES="$*"
[ -z "$NAMES" ] && NAMES=$($PY -c "import json;print(' '.join(x['name'] for x in json.load(open('$CJ'))['crops']))")
for name in $NAMES; do
  D=data/s1/$SEG/derived/$name; mkdir -p $D
  y0=$($PY -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
  x0=$($PY -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
  y1=$((y0+6250)); x1=$((x0+6250))
  if ! test -f $D/ds8_x.npy; then
    $PY scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
    test -f $D/topo.done || $PY scripts/topo_faces.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D --tile 1024 || exit 1
    test -f $D/residual_v0.1b.done || $PY scripts/residual.py $D $P --tag v0.1b --edge-margin-mm 0.1 || exit 1
    $PY scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --template stats/s1_v1b_template_train.json --tag v1b --dump || exit 1
    rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
    $PY scripts/s1_judge.py $D $CJ $name $LAB v1b $P || exit 1
    $PY scripts/s1_ds_stack.py $D || exit 1
    rm -f $D/I_stack_top.npy $D/I_stack_bot.npy $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy
    rm -f $D/S_top.npy $D/S_bot.npy $D/onsheet.npy $D/valid.npy $D/damage_d.npy $D/k_top.npy $D/k_bot.npy $D/peak.npy $D/ct_mid.npy $D/s_*_u8.npy $D/proj_*.npy
  fi
  $PY scripts/s1_team_comparator.py $D $CJ $name data/s1/$SEG/overview/ink_ds8.jpg || exit 1
  OMP_NUM_THREADS=3 $PY scripts/s1_v5.py predict $D models/v8_unet.pt v8 || exit 1
  OMP_NUM_THREADS=3 $PY scripts/gpr.py predict $D models/gpr1.pt gpr1 || exit 1
  OMP_NUM_THREADS=2 $PY scripts/s1_v7.py apply $D stats/s1_v7_weights.json || exit 1
  $PY scripts/ensemble_e.py $SEG:$name || exit 1
  for tag in v8 gpr1 v7 e team; do $PY scripts/s1_judge.py $D $CJ $name $LAB $tag $P || exit 1; done
  rm -f $D/s_top_v7.npy $D/s_top_v8.npy $D/s_top_gpr1.npy $D/s_*_u8.npy
  $PY scripts/stroke_test.py $SEG:$name
  $PY scripts/local_stroke_test.py $SEG:$name
  echo "$SEG $name judged $(date -u)"
done
