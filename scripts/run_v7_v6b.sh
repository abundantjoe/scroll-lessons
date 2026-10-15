#!/bin/sh
# Declared chain: fit v7 on TRAINING crops, judge once; then train v6b on corrected data, judge once.
cd "$(dirname "$0")/.."
test -f stats/s1_v7_weights.json || OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v7.py fit stats/s1_v7_weights.json || exit 1
echo V7_FIT_DONE
EVAL='20231005123336 held1|20231005123336 held2|20231005123336 held3|20231210121321 held1|20231210121321 held2|20231210121321 held3|20231210121321 held4|20231005123336 train'
OLDIFS=$IFS; IFS='|'
for spec in $EVAL; do IFS=$OLDIFS; set -- $spec; SEG=$1; n=$2; D=data/s1/$SEG/derived/$n
  OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v7.py apply $D stats/s1_v7_weights.json || exit 1
  .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png v7 2.4 || exit 1
  IFS='|'
done
IFS=$OLDIFS
S='20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4'
.venv/bin/python scripts/stroke_test.py $S 20231005123336:train
.venv/bin/python scripts/local_stroke_test.py $S
echo V7_JUDGED
DIRS=data/s1/20231005123336/derived/train
for s in 20230929220926 20231012184424; do for n in held1 held2 held3 held4; do
  test "$s/$n" = "20231012184424/held4" && continue
  test -f data/s1/$s/derived/$n/ds8_x.npy && DIRS="$DIRS,data/s1/$s/derived/$n"
done; done
echo "v6b training dirs: $DIRS"
rm -f data/s1/v6b_unet.pt
V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 .venv/bin/python scripts/s1_v5.py train "$DIRS" data/s1/v6b_unet.pt 12000 || exit 1
IFS='|'
for spec in $EVAL; do IFS=$OLDIFS; set -- $spec; SEG=$1; n=$2; D=data/s1/$SEG/derived/$n
  OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v5.py predict $D data/s1/v6b_unet.pt v6b || exit 1
  .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png v6b 2.4 || exit 1
  IFS='|'
done
IFS=$OLDIFS
.venv/bin/python scripts/stroke_test.py $S
.venv/bin/python scripts/local_stroke_test.py $S
echo V6B_JUDGED
