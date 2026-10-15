#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/handed/spiral
while read -r scroll prefix; do
  out=/work/handed/spiral/$scroll.json
  [ -s "$out" ] && continue
  ex=""
  [ "$scroll" = "PHerc0841" ] && ex="--avoid-z 12300 16400"
  "$REPO/tools/sib/handed/logrun.sh" "source /opt/hv/bin/activate && PYTHONPATH=$REPO/src python $REPO/tools/sib/handed/spiral_sense.py $scroll $prefix $out.tmp --level 1 --n-slices 16 $ex && mv $out.tmp $out"
done < /work/handed/centroid_jobs.txt
echo ALL_DONE
