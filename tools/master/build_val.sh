#!/usr/bin/env bash
# Second builder: the held-out PHerc0343P shards first (so validation can start early), then PHerc0800 unlabelled SSL shards.
cd /home/user/dominion; mkdir -p /dev/shm/shards
python3 -c "import json;[print(m['scroll'],m['segment'],m['coarse_sv']) for m in json.load(open('logs/fl7_manifest.json')) if m['scroll']=='PHerc0343P']" | while read sc seg sv; do out=/dev/shm/shards/${sc}_${seg:0:14}.npz; [ -f $out ] && continue; echo "[$(date -u +%T)] $sc $seg"; timeout 2400 /opt/hv/bin/python tools/master/build_data.py $sc $seg $sv $out --stride 48 --max 600 2>&1 | tail -1; done
for seg in 20251028213516-auto_grown_20251028213516907 20251028222030-auto_grown_20251028222030940; do out=/dev/shm/shards/u_PHerc0800_${seg:0:14}.npz; [ -f $out ] || timeout 1200 /opt/hv/bin/python tools/master/build_unlabeled.py PHerc0800 $seg 8.64um-1.2m-116keV-volume-20250521135224.zarr $out --max 600 2>&1 | tail -1; done
echo "VAL+SSL SHARDS DONE $(date -u +%T)"
