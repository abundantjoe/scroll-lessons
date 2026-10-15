#!/bin/sh
# Baseline GP-R1 (RULES.md): Grand-Prize-style 3D->2D detector on the existing 19.2 um stacks. Waits for v8 so they never share CPU.
cd "$(dirname "$0")/.."
until grep -q -E "V8_JUDGED|Traceback|Error" /tmp/v8.log 2>/dev/null; do sleep 60; done
DIRS=data/s1/20231005123336/derived/train
for SEG in 20230929220926 20231012184424; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/$SEG/crops.json'))['crops']))"); do
    test "$SEG/$n" = "20231012184424/held4" && continue
    test -f data/s1/$SEG/derived/$n/ds8_y_noveto.npy && DIRS="$DIRS,data/s1/$SEG/derived/$n"
  done
done
echo "GP-R1 training dirs: $DIRS"
rm -f data/s1/gpr1.pt
GPR_X=ds8_x.npy GPR_Y=ds8_y_noveto.npy GPR_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 \
  .venv/bin/python scripts/gpr.py train "$DIRS" data/s1/gpr1.pt 4000 || exit 1
EVAL='20231005123336 held1|20231005123336 held2|20231005123336 held3|20231210121321 held1|20231210121321 held2|20231210121321 held3|20231210121321 held4'
OLDIFS=$IFS
IFS='|'
for spec in $EVAL; do
  IFS=$OLDIFS
  set -- $spec
  SEG=$1; n=$2; DD=data/s1/$SEG/derived/$n
  OMP_NUM_THREADS=3 .venv/bin/python scripts/gpr.py predict $DD data/s1/gpr1.pt gpr1 || exit 1
  .venv/bin/python scripts/s1_judge.py $DD data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png gpr1 2.4 || exit 1
  IFS='|'
done
IFS=$OLDIFS
S='20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4'
.venv/bin/python scripts/stroke_test.py $S
.venv/bin/python scripts/local_stroke_test.py $S
echo GPR1_JUDGED
