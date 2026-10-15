#!/bin/sh
# S1-v6: v5 recipe trained on segment-1 TRAIN + 8 extra-segment crops (12000 steps); held-out = seg1 held1-3 and seg2 held1-4.
cd /home/user/megara
until grep -q "SEG_DONE" /tmp/s1seg2.log; do sleep 60; done
scripts/run_s1_prep.sh 20230929220926 24 84 >> /tmp/s1prep.log 2>&1 || { echo PREP_FAILED; exit 1; }
scripts/run_s1_prep.sh 20231012184424 24 84 >> /tmp/s1prep.log 2>&1 || { echo PREP_FAILED; exit 1; }
DIRS=data/s1/20231005123336/derived/train
for s in 20230929220926 20231012184424; do for n in held1 held2 held3 held4; do test "$s$n" = "20231012184424held4" && continue; test -f data/s1/$s/derived/$n/ds8_x.npy && DIRS="$DIRS,data/s1/$s/derived/$n"; done; done
VALD=data/s1/20231012184424/derived/held4
echo "training dirs: $DIRS"
test -f data/s1/v6_unet.pt || V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=$VALD .venv/bin/python scripts/s1_v5.py train $DIRS data/s1/v6_unet.pt 12000 || exit 1
for pair in "20231005123336 held1" "20231005123336 held2" "20231005123336 held3" "20231005123336 train" "20231210121321 held1" "20231210121321 held2" "20231210121321 held3" "20231210121321 held4"; do
  set -- $pair; SEG=$1; name=$2; D=data/s1/$SEG/derived/$name; LAB=data/s1/labels/${SEG}_inklabels_L.png; test -f $LAB || LAB=data/s1/labels/${SEG}_inklabels.png
  .venv/bin/python scripts/s1_v5.py predict $D data/s1/v6_unet.pt v6 || exit 1
  .venv/bin/python scripts/s1_judge.py $D data/s1/$SEG/crops.json $name $LAB v6 2.4 || exit 1
done
for SEG in 20231005123336 20231210121321; do .venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json; done; echo S1_V6_DONE
