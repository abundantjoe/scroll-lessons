#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Factory dry run: window from logs/sib/factory/window_pick.json -> package under packages/dryrun/ ->
# verifier -> reproduce.sh in a clean temp dir -> fault drill. Every step logged in runs.jsonl.
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
T=tools/sib/factory; L=logs/sib/factory; PY=/opt/hv/bin/python
read R0 R1 C0 C1 < <($PY -c "import json;c=json.load(open('$L/window_pick.json'))['chosen'];print(*c['grid_rows'],*c['grid_cols'])")
NAME=$(printf 'PHerc0139_w035_r%03d-%03d_c%03d-%03d' "$R0" "$R1" "$C0" "$C1")
VOL=s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/
SRCK=PHerc0139/segments/20260317000000-w035_2026031718/mesh/20260317000000-on-20250728140407-9.362um.tifxyz
PKG=packages/dryrun/DRY_RUN_$NAME
[ -e "$PKG" ] && { echo "exists: $PKG"; exit 1; }
rm -rf /work/factory/dryrun_work
$T/runlog.sh factory_make -- $PY $T/factory.py --volume-url "$VOL" --mesh-src "/work/factory/s3/$SRCK" \
  --mesh-src-url "s3://vesuvius-challenge-open-data/$SRCK/" --rows "$R0" "$R1" --cols "$C0" "$C1" \
  --mesh-name "$NAME" --out-root packages/dryrun --workdir /work/factory/dryrun_work --dry-run \
  --selection "$L/window_pick.json"
$T/runlog.sh verify_dryrun -- $PY $T/verify.py "$PKG" --json "$L/verify_dryrun.json" || true
$T/runlog.sh reproduce_dryrun -- bash "$PKG/reproduce.sh" "$VOL" "mesh/$NAME" || true
cp "$(ls -dt /work/repro/hrc_repro_*/work/reproduce_result.json | head -1)" "$L/reproduce_dryrun.json" || true
$T/runlog.sh fault_drill -- $PY $T/fault_drill.py "$PKG" "$L/fault_drill.json" || true
