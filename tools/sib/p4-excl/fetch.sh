#!/bin/bash
# Fetch official tifxyz meshes (x/y/z tif + meta.json) on 20260411134726 for the 8 labelled Paris 4 segments.
# Anonymous S3 HTTPS; records sha256 + size of every file. Coordinate arrays only; never viewed as images.
set -euo pipefail
OUT=${1:-/tmp/claude-0/p4excl/mesh}
LOG=/home/user/dominion/logs/sib/p4-excl/downloads.jsonl
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
mkdir -p "$OUT"
for id in 20231016151002 20230702185753 20231031143852 20231106155351 20231012184424 20231210121321 20231007101619 20230929220926; do
  pre=PHercParis4/segments/$id/mesh/$id-on-20260411134726-2.4um.tifxyz
  mkdir -p "$OUT/$id"
  for f in meta.json x.tif y.tif z.tif; do
    curl -sS --fail --retry 4 -o "$OUT/$id/$f" "$B/$pre/$f"
    h=$(sha256sum "$OUT/$id/$f" | cut -d' ' -f1); n=$(stat -c %s "$OUT/$id/$f")
    echo "{\"utc\":\"$(date -u +%FT%TZ)\",\"segment\":\"$id\",\"url\":\"s3://vesuvius-challenge-open-data/$pre/$f\",\"bytes\":$n,\"sha256\":\"$h\"}" >> "$LOG"
  done
done
curl -sS --fail -o "$OUT/vol_metadata.json" "$B/PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/metadata.json" || echo "no metadata.json at zarr root"
