#!/bin/sh
# Sequential fetch -> topography -> delete raw for the remaining w028 crops (disk-bounded). Idempotent.
cd /home/user/megara
B=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com
Z="$B/PHerc1667/segments/20251208130119-w028_20251208130119156_flatboi/surface-volumes/2.399um-0.22m-78keV-volume-20251217075048.zarr"
until test -f data/w028/derived/text2/topo.done; do sleep 10; done
rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' 144 209)
for spec in "text3 23552 21504" "text4 13312 3072" "text5 14336 21504" "blank2 2048 3072"; do
  set -- $spec; name=$1; y0=$2; x0=$3; y1=$((y0+8337)); x1=$((x0+8337))
  if test -f data/w028/derived/$name/topo.done; then continue; fi
  .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/w028/stack.zarr --workers 24 || exit 1
  .venv/bin/python scripts/topo_faces.py data/w028/stack.zarr 0 $y0 $y1 $x0 $x1 6 102 data/w028/derived/$name --tile 1024 || exit 1
  rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' $((y0/128)) $((y1/128)))
  rm -f data/w028/derived/$name/D_top.npy data/w028/derived/$name/D_bot.npy data/w028/derived/$name/kstar.npy
  echo "$name done $(date)"
done
echo ALL_CROPS_DONE
