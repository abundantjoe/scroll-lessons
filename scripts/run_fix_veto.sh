#!/bin/sh
# Rebuild the training-segment class masks with the redeclared quantile veto, then ds8_y, then refit v7.
cd "$(dirname "$0")/.."
for SEG in 20230929220926 20231012184424; do
  for n in held1 held2 held3 held4; do
    D=data/s1/$SEG/derived/$n; test -d $D || continue
    rm -f $D/cls_text.npy $D/cls_blank.npy $D/label.npy
    .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png none 2.4 data/s1/$SEG/overview/ink_ds8.jpg 0.40 || exit 1
    .venv/bin/python scripts/rebuild_ds8_y.py $D || exit 1
  done
done
echo VETO_FIXED
OMP_NUM_THREADS=1 .venv/bin/python scripts/s1_v7.py fit stats/s1_v7_weights.json && echo V7_FIT_DONE
