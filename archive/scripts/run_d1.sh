#!/bin/sh
cd /home/user/megara
until grep -q ALL_CROPS_DONE /tmp/run_crops.log; do sleep 20; done
Z="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1667/segments/20251208130119-w028_20251208130119156_flatboi/surface-volumes/2.399um-0.22m-78keV-volume-20251217075048.zarr"
rm -f data/w028/stack.zarr/0/.done_23552_31889_3072_11409
.venv/bin/python scripts/fetch_zarr_region.py $Z 0 23552 31889 3072 11409 data/w028/stack.zarr --workers 24 || exit 1
.venv/bin/python scripts/depth_profile_diag.py data/w028/stack.zarr 0 23552 31889 3072 11409 6 102 data/w028/derived/text1 stats/d1_text1_depth_profile.json || exit 1
rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' 184 249)
echo D1_DONE
