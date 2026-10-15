#!/bin/bash
# R-HELDOUT inference, queued behind R-REPRO so neither run's CPU time is contaminated by the other.
cd /home/user/hdata/heldout
until grep -q "^exit" /home/user/hdata/gateA/timing.txt 2>/dev/null; do sleep 60; done
for seg in 20260220213127-w00 20260220214732-auto_grown_20260220144552896 20260221022814-auto_grown_20260220174252405; do
  [ -f $seg/.infer_complete ] && continue
  t0=$(date +%s); echo "$seg start $(date -u +%FT%TZ)" >> infer_timing.txt
  /home/user/ext/venv-infer/bin/python -m vesuvius.ink_detection.inference.infer $seg/pooled.zarr \
    /home/user/hdata/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth $seg/pred.tif \
    --direction both --batch-size 4 --no-compile --num-workers 3 > $seg/infer.log 2> $seg/infer.err
  rc=$?; echo "$seg end $(date -u +%FT%TZ) exit $rc seconds $(( $(date +%s) - t0 ))" >> infer_timing.txt
  [ $rc -eq 0 ] && touch $seg/.infer_complete
done
