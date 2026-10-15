#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Phase-2 driver for LC384-SOFT (task dev-lcsoft). REFUSES to run unless GO_FILE exists, and GO_FILE records the
# orchestrator's GO DEV message, the METRIC-HASH id and the frozen hold-out list sha256.
# Resumable: every stage skips when its output already exists; training resumes from resume.pt (every 250 steps).
# Usage: run_phase2.sh GO_FILE REGISTRY_DIR SHARDS_DIR EXCLUSION_JSON DEV_REGISTRY_JSON HOLDOUT_SHA256
set -euo pipefail
GO=$1; REG=$2; SH=$3; EXC=$4; DEVREG=$5; HSHA=$6
[ -s "$GO" ] || { echo "no GO file: refusing"; exit 2; }
grep -q "GO DEV LC384-SOFT" "$GO" || { echo "GO file lacks 'GO DEV LC384-SOFT': refusing"; exit 2; }
grep -q "METRIC-HASH" "$GO" || { echo "GO file lacks METRIC-HASH id: refusing"; exit 2; }
[ "$(sha256sum "$DEVREG" | cut -d' ' -f1)" = "$HSHA" ] || { echo "hold-out registry sha256 mismatch: refusing"; exit 2; }
T=$(cd "$(dirname "$0")" && pwd); R=$T/run.sh; W=/work/lcsoft/p2; mkdir -p $W
export PYTHONPATH=/work/lcsoft/pylib:/home/user/dominion/src OMP_NUM_THREADS=4
PY=/opt/hv-ink/bin/python
echo "$HSHA  $DEVREG" | sha256sum -c
echo "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab  /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth" | sha256sum -c
[ -s $W/allow.json ] || $R p2_pool "$PY $T/lc_pool.py --registry $REG --exclusion $EXC --dev-registry $DEVREG --out $W/allow.json --report $W/pool_report.json"
for O in forward reverse; do
  [ -s $W/cache_$O/manifest.json ] || $R p2_cache_$O "$PY $T/lc_cache.py --shards $SH --registry $REG --allow $W/allow.json --out $W/cache_$O --order $O --dtype fp16 --threads 4"
  [ -s $W/cache_$O/soft/manifest.json ] || $R p2_soft_$O "$PY $T/soft_targets.py --cache $W/cache_$O --shards $SH --registry $REG"
done
for A in RECIPE NULL REV; do
  C=$W/cache_forward; [ $A = REV ] && C=$W/cache_reverse
  [ -s $W/run_$A/summary.json ] || $R p2_train_$A "$PY $T/lc_train.py --cache $C --arm $A --out $W/run_$A --targets soft --threads 4 --steps 2000 --ckpt-every 250 --val-every 250"
done
echo "phase2 training done; maps only via EVAL_API.md"
