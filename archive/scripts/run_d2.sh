#!/bin/sh
# Diagnostic D2 (RULES.md): can our 19.2 um pooled surface stack reproduce the TEAM model's output?
# DIAGNOSTIC ONLY - distillation from the team model, never one of our methods, excluded from every results table.
# Waits for the v8 run to finish so the two never share the CPU.
cd /home/user/megara
until grep -q -E "V8_JUDGED|Traceback|Error" /tmp/v8.log 2>/dev/null; do sleep 60; done

SPECS=""
for SEG in 20230929220926 20231012184424; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/$SEG/crops.json'))['crops']))"); do
    test -f data/s1/$SEG/derived/$n/ds8_x.npy && SPECS="$SPECS $SEG:$n"
  done
done
SPECS="$SPECS 20231005123336:train 20231005123336:held1 20231005123336:held2 20231005123336:held3"
SPECS="$SPECS 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4"
.venv/bin/python scripts/d2_target.py $SPECS || exit 1
echo D2_TARGETS_BUILT

DIRS=data/s1/20231005123336/derived/train
for SEG in 20230929220926 20231012184424; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/$SEG/crops.json'))['crops']))"); do
    test "$SEG/$n" = "20231012184424/held4" && continue
    test -f data/s1/$SEG/derived/$n/ds8_team.npy && DIRS="$DIRS,data/s1/$SEG/derived/$n"
  done
done
echo "D2 training dirs: $DIRS"
rm -f data/s1/d2_unet.pt
V5_Y=ds8_team.npy V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 \
  .venv/bin/python scripts/s1_v5.py train "$DIRS" data/s1/d2_unet.pt 12000 || exit 1

EVAL='20231005123336 held1|20231005123336 held2|20231005123336 held3|20231210121321 held1|20231210121321 held2|20231210121321 held3|20231210121321 held4'
OLDIFS=$IFS
IFS='|'
for spec in $EVAL; do
  IFS=$OLDIFS
  set -- $spec
  SEG=$1; n=$2; DD=data/s1/$SEG/derived/$n
  OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v5.py predict $DD data/s1/d2_unet.pt d2 || exit 1
  .venv/bin/python scripts/s1_judge.py $DD data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png d2 2.4 || exit 1
  IFS='|'
done
IFS=$OLDIFS
echo D2_JUDGED
