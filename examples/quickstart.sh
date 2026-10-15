#!/usr/bin/env bash
# Five-minute quick start on REAL known Herculaneum text: the w040 control window (PHerc0139, 2136 x 2136 px = 3.9989 cm^2, 9.362 um/px).
# Runs the reader, the depth-swap tripwire, the truncated-map refusal and the layout-aware power estimate on the
# committed window, then checks every output against the recorded values. CPU only; about 16 s on 4 cores (measured).
#   usage: bash examples/quickstart.sh [out_dir]        (default examples/out; set PYTHON to choose the interpreter)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python}
OUT=${1:-examples/out}
rm -rf "$OUT"; mkdir -p "$OUT"
KEY="PHerc0139|w040_window|0|ink9um_seed42+plain"

echo "== 1. Extract the committed known-text window; every array is checked against its recorded pixel sha256"
$PY examples/extract_w040_window.py "$OUT" --truncate

echo; echo "== 2. Read it: forward vs reverse margin per 0.5 cm^2 unit, frozen rule 5.5, depth-swap tripwire"
$PY scripts/read_chart.py "$OUT/ct_mid.tif" "$OUT/forward.tif" "$OUT/reverse.tif" --maps-only --um 9.362 \
    --out "$OUT/read" --key "$KEY|both" --ledger "$OUT/LEDGER.md"

echo; echo "== 3. Same maps, depth order swapped (what a mirrored surface looks like): the tripwire must fire"
$PY scripts/read_chart.py "$OUT/ct_mid.tif" "$OUT/reverse.tif" "$OUT/forward.tif" --maps-only --um 9.362 \
    --out "$OUT/read_swapped" --key "$KEY+swapped|both" --ledger "$OUT/LEDGER.md"

echo; echo "== 4. A reverse map with only one quadrant written (the real failure of 2026-09-19) must be refused"
if $PY scripts/map_integrity.py --pair "$OUT/forward.tif" "$OUT/reverse_truncated.tif"; then
    echo "UNEXPECTED: map_integrity accepted a truncated map"; exit 1
else
    echo "(map_integrity exit 1 = refused, as required)"
fi
if $PY scripts/read_chart.py "$OUT/ct_mid.tif" "$OUT/forward.tif" "$OUT/reverse_truncated.tif" --maps-only --um 9.362 \
    --out "$OUT/read_truncated" --key "$KEY+truncated|both" --ledger "$OUT/LEDGER.md"; then
    echo "UNEXPECTED: read_chart scored a truncated map"; exit 1
else
    echo "(read_chart refused, as required)"
fi

echo; echo "== 5. Could this surface have produced a candidate at all, even if it were all text? (layout-aware power)"
$PY scripts/cluster_power.py --read-stats "$OUT/read/read_stats.json"

echo; echo "== 6. Check every output against the recorded values"
$PY examples/check_quickstart.py "$OUT"
echo "Contact sheet: $OUT/read/contact_sheet.png"
