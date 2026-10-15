#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Anonymous fetch of official files for P4-D M2a, 20260623141924-w010-027 (DECL-P4-4).
set -euo pipefail
W="$1"; OUT="$2"
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
S=PHercParis4/segments/20260623141924-w010-027
M1=$S/mesh/20260623141924-on-20260608103018-1.129um.tifxyz
M2=$S/mesh/20260623141924-on-20260411134726-2.4um.tifxyz
V1=PHercParis4/volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr
V2=PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr
KEYS="$V1/metadata.json $V1/.zattrs $V1/transform.json $V2/metadata.json $V2/transform.json $M1/meta.json $M2/meta.json $M1/x.tif $M1/y.tif $M1/z.tif $M2/x.tif $M2/y.tif $M2/z.tif $S/ink-detection/PHercParis4-20260623141924-1.129um-0.23m-78keV-volume-20260608103018-L1-20260709123958-mrg20736-1um-s1z2-tile256-stride128.tif"
: > "$OUT"
for k in $KEYS; do
  f="$W/$(echo "$k" | tr '/' '_')"
  t0=$(date +%s)
  for i in 1 2 3 4; do curl -sS --fail -o "$f" "$B/$k" && break; sleep $((2**i)); done
  sz=$(stat -c %s "$f"); h=$(sha256sum "$f" | cut -d' ' -f1)
  echo "{\"key\":\"$k\",\"bytes\":$sz,\"sha256\":\"$h\",\"seconds\":$(( $(date +%s)-t0 ))}" >> "$OUT"
done
echo DONE
