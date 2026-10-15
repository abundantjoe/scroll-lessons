#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# PHASE-1 smoke of arm P384 on SYNTHETIC data only (d2_data.write_synthetic_registry; never real data).
# 10 steps, fp32, 4 threads, batch 32 via micro-batch 4, full 384 px forward of the unchanged base model,
# rotations 24 x 15 deg, local resume checkpoint every 5 steps.
# Run A: uninterrupted. Run B: same config, hard exit after step 7 (last save at step 5), then resumed to step 10.
# Output: numbers only (JSON). No image is written or opened. Weights stay under /work (never committed).
set -euo pipefail
PY=/opt/hv-ink/bin/python
HERE=$(cd "$(dirname "$0")" && pwd)
TR=$HERE/trainer/d2_train.py
W=/work/d2/smoke
mkdir -p "$W"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
REG=$W/syn560/registry.json
[ -f "$REG" ] || $PY -c "import sys; sys.path.insert(0,'$HERE/trainer'); import d2_data; print(d2_data.write_synthetic_registry('$W/syn560', n=40, size=560, seed=101, shard_n=20))"
$PY "$TR" make-config --arm P384 --seed 1 --batch 32 --micro-batch 4 --steps 10 --forward full --precision fp32 \
  --threads 4 --subtile --z-jitter 2 --z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --log-every 1 --ckpt-every 5 \
  --source "syn=pairs:$REG" --hash-sources --decl "SMOKE-SYNTHETIC (not a declared recipe)" --out "$W/cfg.json"
rm -rf "$W/A" "$W/B"
$PY "$HERE/timed.py" "$W/time_A.json" $PY "$TR" train --config "$W/cfg.json" --out "$W/A"
set +e
$PY "$HERE/timed.py" "$W/time_B1.json" $PY "$TR" train --config "$W/cfg.json" --out "$W/B" --die-after 7
RC=$?
set -e
echo "B1 exit code: $RC (99 = simulated crash)"
test "$RC" = 99
ls -la "$W/B"
$PY "$HERE/timed.py" "$W/time_B2.json" $PY "$TR" train --config "$W/cfg.json" --out "$W/B"
$PY "$HERE/smoke_compare.py" "$W"
