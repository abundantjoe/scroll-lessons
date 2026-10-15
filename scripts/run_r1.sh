#!/bin/sh
# Reading run R1 (RULES.md): prepare the declared unread and control windows, run v8 exactly as judged, render.
cd "$(dirname "$0")/.."
B=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments
for SPEC in "20231005123336 2 82" "20231210121321 24 84"; do
  set -- $SPEC; SEG=$1; K0=$2; K1=$3
  Z=$B/$SEG/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
  for name in unread1 control1; do
    D=data/s1/$SEG/derived/$name; mkdir -p $D
    test -f $D/ds8_x.npy && continue
    y0=$(.venv/bin/python -c "import json;print([c for c in json.load(open('data/s1/$SEG/unread.json'))['crops'] if c['name']=='$name'][0]['y0'])")
    x0=$(.venv/bin/python -c "import json;print([c for c in json.load(open('data/s1/$SEG/unread.json'))['crops'] if c['name']=='$name'][0]['x0'])")
    y1=$((y0+6250)); x1=$((x0+6250))
    .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/s1/$SEG/stack.zarr --workers 24 || exit 1
    test -f $D/topo.done || .venv/bin/python scripts/topo_faces.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D --tile 1024 || exit 1
    test -f $D/residual_v0.1b.done || .venv/bin/python scripts/residual.py $D 2.4 --tag v0.1b --edge-margin-mm 0.1 || exit 1
    .venv/bin/python scripts/s1_score.py data/s1/$SEG/stack.zarr 0 $y0 $y1 $x0 $x1 $K0 $K1 $D 2.4 --dump || exit 1
    rm -rf data/s1/$SEG/stack.zarr/0/0/$(seq -s " data/s1/$SEG/stack.zarr/0/0/" $((y0/128)) $((y1/128)))
    .venv/bin/python scripts/s1_ds_stack.py $D || exit 1
    rm -f $D/I_stack_top.npy $D/I_stack_bot.npy $D/D_top.npy $D/D_bot.npy $D/kstar.npy $D/relief_*.npy $D/e_*.npy $D/s_*_v0.1b*.npy $D/S_top.npy $D/S_bot.npy $D/onsheet.npy $D/valid.npy $D/damage_d.npy $D/k_top.npy $D/k_bot.npy $D/peak.npy $D/ct_mid.npy
    echo "$SEG $name prepared $(date)"
  done
done
echo R1_PREPARED
for SPEC in "20231005123336" "20231210121321"; do
  for name in unread1 control1; do
    D=data/s1/$SPEC/derived/$name
    OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v5.py predict $D data/s1/v8_unet.pt v8 || exit 1
    .venv/bin/python scripts/render_reading.py $D v8 review_sheets/r1/${SPEC}_${name}_v8.png "R1 $SPEC $name - v8 detector on UNREAD papyrus" || exit 1
  done
done
echo R1_RENDERED
