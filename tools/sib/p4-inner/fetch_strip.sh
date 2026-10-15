#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
[line withheld: prize-candidate detail under review]
set -euo pipefail
W="$1"; OUT="$2"; SEG="$3"; SID="${SEG%%-*}"
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
S=PHercParis4/segments/$SEG
M=$S/mesh/$SID-on-20260411134726-2.4um.tifxyz
V=PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr
KEYS="$V/metadata.json $V/.zattrs $M/meta.json $M/x.tif $M/y.tif $M/z.tif $S/ink-detection/PHercParis4-$SID-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif"
: > "$OUT"
for k in $KEYS; do
  f="$W/$(echo "$k" | tr '/' '_')"
  t0=$(date +%s)
  for i in 1 2 3 4; do curl -sS --fail -o "$f" "$B/$k" && break; sleep $((2**i)); done
  sz=$(stat -c %s "$f"); h=$(sha256sum "$f" | cut -d' ' -f1)
  echo "{\"key\":\"$k\",\"bytes\":$sz,\"sha256\":\"$h\",\"local\":\"$f\",\"seconds\":$(( $(date +%s)-t0 ))}" >> "$OUT"
done
echo DONE
