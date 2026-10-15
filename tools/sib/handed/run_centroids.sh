#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Resumable: skips volumes whose output JSON exists.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
while read -r scroll prefix; do
  out=/work/handed/centroids/$scroll.json
  [ -s "$out" ] && continue
  ex=""
  [ "$scroll" = "PHerc0841" ] && ex="--exclude-npy /work/handed/j_points_0841.npy --exclude-radius 175"
  "$REPO/tools/sib/handed/logrun.sh" "source /opt/hv/bin/activate && PYTHONPATH=$REPO/src python $REPO/tools/sib/handed/centroid_fetch.py $prefix $out.tmp --zstride 8 $ex && mv $out.tmp $out"
done < /work/handed/centroid_jobs.txt
echo ALL_DONE
