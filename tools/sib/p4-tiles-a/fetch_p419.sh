#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-P4-19 inputs: M1 prediction and the 2.4 um tifxyz z.tif of 20260701183124-w010-027.
set -euo pipefail
W="$1"; OUT="$2"
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
S=PHercParis4/segments/20260701183124-w010-027
KEYS="$S/mesh/20260701183124-on-20260411134726-2.4um.tifxyz/z.tif $S/ink-detection/PHercParis4-20260701183124-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif"
: > "$OUT"
for k in $KEYS; do
  f="$W/$(basename "$k")"
  for i in 1 2 3 4; do curl -sS --fail -o "$f" "$B/$k" && break; sleep $((2**i)); done
  echo "{\"key\":\"$k\",\"bytes\":$(stat -c %s "$f"),\"sha256\":\"$(sha256sum "$f" | cut -d' ' -f1)\"}" >> "$OUT"
done
echo DONE
