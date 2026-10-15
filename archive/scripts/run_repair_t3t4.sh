#!/bin/sh
# Repair text3/text4 (rows wiped before topo): after the v0.2 chain finishes, refetch, redo topo and every derived product, re-summarise, then v0.3f.
cd /home/user/megara
until grep -q "blank2 v0.2 done" /tmp/chain.log; do sleep 30; done
until grep -q -E "V03PHP_DONE|Traceback|Error" /tmp/v03php.log; do sleep 30; done
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1667/segments/20251208130119-w028_20251208130119156_flatboi/surface-volumes/2.399um-0.22m-78keV-volume-20251217075048.zarr"
for spec in "text3 23552 21504" "text4 13312 3072"; do
  set -- $spec; name=$1; y0=$2; x0=$3; y1=$((y0+8337)); x1=$((x0+8337))
  test -f data/w028/derived/$name/repaired && continue
  rm -f data/w028/derived/$name/*.npy data/w028/derived/$name/*.json data/w028/derived/$name/*.done
  .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/w028/stack.zarr --workers 24 || exit 1
  .venv/bin/python scripts/topo_faces.py data/w028/stack.zarr 0 $y0 $y1 $x0 $x1 6 102 data/w028/derived/$name --tile 1024 || exit 1
  .venv/bin/python -c "
import numpy as np; ct=np.load('data/w028/derived/$name/ct_mid.npy', mmap_mode='r'); z=(np.asarray(ct[::16,::16])==0).mean(); print('$name ct==0 frac', z); assert z < 0.1, 'still black'" || exit 1
  rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' $((y0/128)) $((y1/128)))
  rm -f data/w028/derived/$name/D_top.npy data/w028/derived/$name/D_bot.npy data/w028/derived/$name/kstar.npy
  touch data/w028/derived/$name/repaired; echo "$name repaired $(date)"
done
rm -f stats/w028_gate_t1_v0.1b.json stats/w028_gate_t1_v0.2.json stats/w028_gate_t1_v0.3p.json stats/w028_gate_t1_v0.3php.json
scripts/run_chain_w028.sh || exit 1
scripts/run_v03p.sh || exit 1
scripts/run_v03php.sh || exit 1
echo REPAIR_DONE
scripts/run_v03f.sh
