#!/bin/sh
echo "v0.3f disabled 2026-09-17: Scroll 1 ground-truth work takes the disk; see RULES.md"; exit 0
# v0.3f: refetch each crop's raw stack, sample the D1 depths, delete the raw. Disk-bounded, idempotent. Runs after the v0.2 chain.
cd /home/user/megara
until grep -q "blank2 v0.2 done" /tmp/chain.log; do sleep 30; done
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1667/segments/20251208130119-w028_20251208130119156_flatboi/surface-volumes/2.399um-0.22m-78keV-volume-20251217075048.zarr"
J="data/w028/crops.json 2.399 data/w028/pred_2.4um_team.tif data/labels/w028_inklabels.zarr 4 10 240"
D=""
for spec in "text2 18432 12288" "text3 23552 21504" "text4 13312 3072" "text5 14336 21504" "blank1 0 0" "blank2 2048 3072" "text1 23552 3072"; do
  set -- $spec; name=$1; y0=$2; x0=$3
  if [ "$name" = blank1 ]; then y0=$(.venv/bin/python -c "import json;c=json.load(open('data/w028/crops.json'));print([x for x in c['crops'] if x['name']=='blank1'][0]['y0'])"); x0=$(.venv/bin/python -c "import json;c=json.load(open('data/w028/crops.json'));print([x for x in c['crops'] if x['name']=='blank1'][0]['x0'])"); fi
  y1=$((y0+8337)); x1=$((x0+8337)); D="$D data/w028/derived/$name"
  if ! test -f data/w028/derived/$name/s_top_v0.3f.npy; then
    rm -f data/w028/stack.zarr/0/.done_${y0}_${y1}_${x0}_${x1}
    .venv/bin/python scripts/fetch_zarr_region.py $Z 0 $y0 $y1 $x0 $x1 data/w028/stack.zarr --workers 24 || exit 1
    .venv/bin/python scripts/v03f_sample.py data/w028/stack.zarr 0 $y0 $y1 $x0 $x1 6 102 data/w028/derived/$name 2.399 || exit 1
    rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' $((y0/128)) $((y1/128)))
  fi
  test -f data/w028/derived/$name/gate_v0.3f.json || .venv/bin/python scripts/gate_eval.py eval data/w028/derived/$name $name $J v0.3f || exit 1
  echo "$name v0.3f done $(date)"
done
.venv/bin/python scripts/gate_eval.py summary v0.3f stats/w028_gate_t1_v0.3f.json $D && echo V03F_DONE
