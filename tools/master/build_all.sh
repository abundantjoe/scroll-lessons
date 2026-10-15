#!/usr/bin/env bash
# Build every shard in logs/fl7_manifest.json sequentially into /dev/shm/shards (RAM). usage: build_all.sh [max_crops=600]
M=${1:-600}; cd /home/user/dominion; mkdir -p /dev/shm/shards; n=$(python3 -c "import json;print(len(json.load(open('logs/fl7_manifest.json'))))")
for i in $(seq 0 $((n-1))); do read -r sc seg sv <<<"$(python3 -c "import json;m=json.load(open('logs/fl7_manifest.json'))[$i];print(m['scroll'],m['segment'],m['coarse_sv'])")"
  out=/dev/shm/shards/${sc}_${seg:0:14}.npz; [ -f $out ] && continue
  echo "[$(date -u +%T)] $i $sc $seg"; timeout 2400 /opt/hv/bin/python tools/master/build_data.py $sc $seg $sv $out --stride 48 --max $M 2>&1 | tail -2
done; echo "ALL SHARDS DONE $(date -u +%T)"; ls -la /dev/shm/shards | awk '{s+=$5} END {print "total MB", s/1e6}'
