#!/bin/sh
# Method E (RULES.md): ensemble of v8 and GP-R1. Waits for GP-R1, then judges once.
cd "$(dirname "$0")/.."
until grep -q -E "GPR1_JUDGED|Traceback|Error" /tmp/gpr1.log 2>/dev/null; do sleep 60; done
grep -q GPR1_JUDGED /tmp/gpr1.log || { echo E_ABORTED_GPR1_FAILED; exit 1; }
S='20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4'
.venv/bin/python scripts/ensemble_e.py $S || exit 1
for spec in $S; do
  SEG=$(echo $spec | cut -d: -f1); n=$(echo $spec | cut -d: -f2)
  .venv/bin/python scripts/s1_judge.py data/s1/$SEG/derived/$n data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png e 2.4 || exit 1
done
.venv/bin/python scripts/stroke_test.py $S
.venv/bin/python scripts/local_stroke_test.py $S
echo E_JUDGED
