#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Anonymous HTTPS fetch of official files for M2b (DECL-P4-4): 20260623142658-w028-037,
# 1 um model on 20260608103018 L1. Records bytes + sha256 per file.
set -euo pipefail
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
SEG=PHercParis4/segments/20260623142658-w028-037
V=PHercParis4/volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr
M1=$SEG/mesh/20260623142658-on-20260608103018-1.129um.tifxyz
M2=$SEG/mesh/20260623142658-on-20260411134726-2.4um.tifxyz
P=$SEG/ink-detection/PHercParis4-20260623142658-1.129um-0.23m-78keV-volume-20260608103018-L1-20260709123958-mrg20736-1um-s1z2-tile256-stride128.tif
OUT=$1; LOG=$2
for k in "$V/metadata.json" "$V/.zattrs" "$V/transform.json" \
         "$M1/meta.json" "$M1/x.tif" "$M1/y.tif" "$M1/z.tif" \
         "$M2/meta.json" "$M2/x.tif" "$M2/y.tif" "$M2/z.tif" "$P"; do
  f=$OUT/$(echo "$k" | tr '/' '_')
  t0=$(date +%s)
  curl -sS --retry 5 --retry-delay 4 -o "$f" "$B/$k"
  h=$(sha256sum "$f" | cut -d' ' -f1); n=$(stat -c %s "$f")
  echo "{\"key\":\"$k\",\"url\":\"$B/$k\",\"bytes\":$n,\"sha256\":\"$h\",\"local\":\"$f\",\"secs\":$(( $(date +%s)-t0 )),\"utc\":\"$(date -u +%FT%TZ)\"}" >> "$LOG"
done
echo DONE >> "$LOG.done"
