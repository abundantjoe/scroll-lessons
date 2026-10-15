#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Phase-1 SYNTHETIC smoke: DIST-FT, DIST-FT-NULL, DIST-FT-REV, 20 steps each at the full-run settings
# (tile 128, rot24, sub-tiles of 384 px patches, batch 32, fp32, 4 threads, seed 20260925), resume state every
# 10 steps (local only). Synthetic registry: 64 patches of 384 px (576 sub-tiles). Never real data.
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
PY=/opt/hv-ink/bin/python; T=tools/sib/dev-distft; W=/work/distft/smoke
mkdir -p $W
[ -f $W/syn/registry.json ] || $T/runlog.sh smoke_synth $PY $T/distft.py synth --out $W/syn --n 64 --size 384 --seed 7
for ARM in DIST-FT DIST-FT-NULL DIST-FT-REV; do
  $T/runlog.sh smoke_cfg_$ARM $PY $T/distft.py make-config --arm $ARM --out $W/$ARM.json --batch 32 --steps 20 \
    --threads 4 --ckpt-every 10 --log-every 1 --subtile --source syn=pairs:$W/syn/registry.json --hash-sources
  rm -rf $W/run_$ARM
  $T/runlog.sh smoke_train_$ARM $PY $T/distft.py train --config $W/$ARM.json --out $W/run_$ARM
done
echo SMOKE_DONE
