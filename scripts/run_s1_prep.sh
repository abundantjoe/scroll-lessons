#!/bin/sh
# Prepare TRAINING crops on an extra labelled segment: select 4 densest windows, per crop fetch -> topo -> mask -> classes -> pooled stacks. Usage: run_s1_prep.sh SEG K0 K1
cd "$(dirname "$0")/.."
SEG=$1; K0=$2; K1=$3; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels_L.png
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
until test -f data/s1/$SEG/label_registration.json; do sleep 30; done
test -f $CJ || { .venv/bin/python scripts/s1_select_crops.py $SEG $LAB data/s1/$SEG/label_registration.json data/s1/$SEG/overview/onsheet_ds8.png $CJ 4 && .venv/bin/python scripts/s1_refine_reg.py $CJ $LAB data/s1/$SEG/overview/ink_ds8.jpg; } || exit 1
cp $CJ stats/s1_crops_$SEG.json; cp data/s1/$SEG/label_registration.json stats/s1_registration_$SEG.json
for name in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('$CJ'))['crops']))"); do
  D=data/s1/$SEG/derived/$name; mkdir -p $D; test -f $D/ds8_x.npy && continue
  y0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['y0'])")
  x0=$(.venv/bin/python -c "import json;c=json.load(open('$CJ'));print([x for x in c['crops'] if x['name']=='$name'][0]['x0'])")
  y1=$((y0+6250)); x1=$((x0+6250))
  .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
  test -f $D/topo.done || .venv/bin/python scripts/topo_faces.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D --tile 1024 || exit 1
  test -f $D/residual_v0.1b.done || .venv/bin/python scripts/residual.py $D $P --tag v0.1b --edge-margin-mm 0.1 || exit 1
  .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB none $P data/s1/$SEG/overview/ink_ds8.jpg 0.40 || exit 1
  .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D $P --dump || exit 1
  rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
  .venv/bin/python scripts/s1_ds_stack.py $D || exit 1
  rm -f $D/I_stack_top.npy $D/I_stack_bot.npy $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy $D/s_*_v0.1b*.npy $D/S_top.npy $D/S_bot.npy $D/onsheet.npy $D/valid.npy $D/damage_d.npy $D/k_top.npy $D/k_bot.npy $D/peak.npy $D/ct_mid.npy
  echo "$name $SEG prepared $(date)"
done
echo PREP_DONE_$SEG
