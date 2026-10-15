#!/bin/bash
# R-HELDOUT input preparation: pool each PHerc0841 segment's 2.403 um surface volume (level 2) to 21 slices.
cd /home/user/hdata/heldout
U=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0841/segments
for seg in 20260220213127-w00 20260220214732-auto_grown_20260220144552896 20260221022814-auto_grown_20260220174252405; do
  [ -d $seg/pooled.zarr ] && continue
  mkdir -p $seg
  echo "$seg start $(date -u +%FT%TZ)" >> prep_timing.txt
  for i in 1 2 3 4; do
    nice -n 5 /home/user/ext/venv-infer/bin/python -m vesuvius.ink_detection.preprocessing.prepare_9um_isotropic_input \
      $U/$seg/surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr $seg/pooled.zarr --level 2 --workers 6 \
      >> $seg/prep.log 2>&1 && break
    rm -rf $seg/pooled.zarr.partial; sleep $((2**i))
  done
  echo "$seg end $(date -u +%FT%TZ) exit $?" >> prep_timing.txt
done
