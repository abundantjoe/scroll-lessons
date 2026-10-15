#!/usr/bin/env bash
# reproduce.sh: the headline result from scratch (docs/REPRODUCE.md): fetch + verify the inputs, run the d = +1 arms
# (all but the original run's exploratory X13) of the PHerc0343 positive-control strip experiment through the reference
# pipeline, score, compare with the committed run.
#   WORK=/fast/disk ERWIN=<pherc343-first-letters @ e8370f1> PYH=... PYI=... VC_BIN=... VC_MOUNTS="..." bash scripts/reproduce.sh
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd); WORK=${WORK:?set WORK (a directory with ~3 GB free)}; mkdir -p "$WORK"; WORK=$(cd "$WORK" && pwd)
: "${ERWIN:?set ERWIN to a checkout of github.com/Nieuwlaar/pherc343-first-letters at commit e8370f1}"
echo "release commit: $(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
(cd "$ERWIN/outputs" && sha256sum -c --quiet SHA256SUMS) || { echo "segment checksum FAILED" >&2; exit 1; }
(cd "$ERWIN" && sha256sum -c --quiet "$REPO/docs/inputs.sha256") || { echo "input checksum FAILED" >&2; exit 1; }
echo "input checksums OK (segment, letter boxes, umbilicus)"
export CKPT=${CKPT:-$WORK/ckpt}; bash "$REPO/scripts/get_weights.sh" "$CKPT"
export BI_ROOT=$WORK/bi
export OUT=${OUT:-$WORK/out}   # never overwrite the committed results/control_strips_rerun
bash "$REPO/scripts/control_strips/run.sh"
echo "results: $OUT/results.json (compare with results/control_strips_rerun/results.json)"
