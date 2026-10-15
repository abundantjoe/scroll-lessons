#!/usr/bin/env bash
# Reproduce every number in results/ from public data (about 7 MB of mesh files, about 2 min on 1 CPU).
set -euo pipefail
cd "$(dirname "$0")/.."
VOL=20250728140407-9.362um   # PHerc0139 volume, 9.362 um voxels
SEGS="20260227000000-w052_2026022705 20260220000000-w053_2026022021 20260306000001-w051_2026030600"
mkdir -p results
for s in $SEGS; do
  python scripts/fetch_segment.py PHerc0139 "$s" "$VOL" data_cache > /dev/null
  M="data_cache/PHerc0139/$s/${s%%-*}-on-$VOL.tifxyz"
  echo "== PHerc0139 $s: whole mesh, grid flattening (add --compare for SLIM/ARAP; 10+ min per mesh)"
  python -m flatcheck report "$M" --json "results/whole_$s.json"
  echo "== PHerc0139 $s: 3 most curved 4 cm^2 windows"
  python -m flatcheck scan "$M" --voxel-um 9.362 -k 3 --json "results/scan_$s.json"
done
python scripts/summarize.py results > results/SUMMARY.md
cat results/SUMMARY.md
