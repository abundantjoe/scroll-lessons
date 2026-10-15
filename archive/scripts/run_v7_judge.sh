#!/bin/sh
# One-shot judging of v7 on the 7 evaluation crops, then v6b training on the corrected data.
cd /home/user/megara
until test -f stats/s1_v7_weights.json; do sleep 30; done
for spec in "20231005123336 held1" "20231005123336 held2" "20231005123336 held3" "20231210121321 held1" "20231210121321 held2" "20231210121321 held3" "20231210121321 held4" "20231005123336 train"; do
  set -- $spec; SEG=$1; n=$2; D=data/s1/$SEG/derived/$n
  .venv/bin/python scripts/s1_v7.py apply $D stats/s1_v7_weights.json || exit 1
  .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png v7 2.4 || exit 1
done
.venv/bin/python scripts/stroke_test.py 20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4 20231005123336:train
.venv/bin/python scripts/local_stroke_test.py 20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4
echo V7_JUDGED
DIRS=data/s1/20231005123336/derived/train
for s in 20230929220926 20231012184424; do for n in held1 held2 held3 held4; do test "$s$n" = "20231012184424held4" && continue; test -f data/s1/$s/derived/$n/ds8_x.npy && DIRS="$DIRS,data/s1/$s/derived/$n"; done; done
rm -f data/s1/v6b_unet.pt
V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v5.py train $DIRS data/s1/v6b_unet.pt 12000 || exit 1
for spec in "20231005123336 held1" "20231005123336 held2" "20231005123336 held3" "20231210121321 held1" "20231210121321 held2" "20231210121321 held3" "20231210121321 held4" "20231005123336 train"; do
  set -- $spec; SEG=$1; n=$2; D=data/s1/$SEG/derived/$n
  .venv/bin/python scripts/s1_v5.py predict $D data/s1/v6b_unet.pt v6b || exit 1
  .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png v6b 2.4 || exit 1
done
.venv/bin/python scripts/stroke_test.py 20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4
.venv/bin/python scripts/local_stroke_test.py 20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4
echo V6B_JUDGED
