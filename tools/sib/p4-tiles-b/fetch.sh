#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Anonymous HTTPS fetch of official files for 20260701183125-w028-037; records bytes + sha256.
set -euo pipefail
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
SEG=PHercParis4/segments/20260701183125-w028-037
OUT=$1; LOG=$2
M=$SEG/mesh/20260701183125-on-20260411134726-2.4um.tifxyz
P=$SEG/ink-detection/PHercParis4-20260701183125-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif
V=PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/metadata.json
for k in "$V" "$M/meta.json" "$M/x.tif" "$M/y.tif" "$M/z.tif" "$P"; do
  f=$OUT/$(echo "$k" | tr '/' '_')
  t0=$(date +%s)
  curl -sS --retry 5 --retry-delay 4 -C - -o "$f" "$B/$k" || curl -sS --retry 5 -o "$f" "$B/$k"
  h=$(sha256sum "$f" | cut -d' ' -f1); n=$(stat -c %s "$f")
  echo "{\"key\":\"$k\",\"url\":\"$B/$k\",\"bytes\":$n,\"sha256\":\"$h\",\"local\":\"$f\",\"secs\":$(( $(date +%s)-t0 )),\"utc\":\"$(date -u +%FT%TZ)\"}" >> "$LOG"
done
echo DONE >> "$LOG.done"
