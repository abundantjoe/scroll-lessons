#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# d2-null PHASE 1 smoke, SYNTHETIC data only (d2_data.write_synthetic_registry). Numbers and hashes only.
# Arm NULL, seed 1, fp32, 4 threads, batch 32 = 8 micro-batches of 4, P384 forward (full; stitched timed separately),
# 24 x 15 deg rotations, --subtile, z jitter 2, AdamW 2e-5 / wd 3e-5 (DECL-D2-A1 proposal common config), 10 steps.
# ckpt_every is 5 here (production 250) so that a resume can be tested inside 10 steps. No remote ref: weights stay local.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
D=$REPO/tools/sib/d2-null
PY=/opt/hv-ink/bin/python
TR=$D/trainer/d2_train.py
RL=$D/runlog.sh
W=/work/d2null/smoke
mkdir -p "$W"
cd "$W"
step() { echo "== $(date -u +%FT%TZ) $*"; }

if [ ! -f "$W/syn384/registry.json" ]; then
  step synthetic registry
  $RL syn_registry $PY -c "import sys; sys.path.insert(0, '$D/trainer'); import d2_data; \
print(d2_data.write_synthetic_registry('$W/syn384', n=96, size=384, seed=20260926, source='synthetic', shard_n=32))"
fi
COMMON=(--seed 1 --subtile --batch 32 --micro-batch 4 --steps 10 --forward full --precision fp32 --threads 4
        --z-jitter 2 --z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --log-every 1 --ckpt-every 5
        --source syn=pairs:$W/syn384/registry.json --hash-sources --decl DECL-D2)
for arm in NULL P384; do
  [ -f "$W/cfg_$arm.json" ] || $RL "make_config_$arm" $PY $TR make-config --arm $arm "${COMMON[@]}" --out "$W/cfg_$arm.json"
done
[ -f "$W/cfg_NULL_stitched.json" ] || $RL make_config_NULL_stitched $PY $TR make-config --arm NULL \
  "${COMMON[@]/full/stitched}" --out "$W/cfg_NULL_stitched.json"

# 1. timed uninterrupted 10-step NULL run (peak RSS from GNU time as well as ru_maxrss)
step run A
$RL smoke_A_null_10 /usr/bin/time -v $PY $TR train --config "$W/cfg_NULL.json" --out "$W/A"
# 2. crash after step 7 (last save at step 5), then the identical command resumes to step 10
step run B crash
$RL smoke_B_null_crash7 $PY $TR train --config "$W/cfg_NULL.json" --out "$W/B" --die-after 7
step run B resume
$RL smoke_B_null_resume /usr/bin/time -v $PY $TR train --config "$W/cfg_NULL.json" --out "$W/B"
# 3. pairing: P384 and NULL, same seed, 2 real train steps then 8 batch-only draws each
step pair checks
$RL paircheck_P384 $PY $D/pair_check.py --config "$W/cfg_P384.json" --out "$W/pair_P384.json" --steps 10 --train-steps 2
$RL paircheck_NULL $PY $D/pair_check.py --config "$W/cfg_NULL.json" --out "$W/pair_NULL.json" --steps 10 --train-steps 2
# 4. stitched forward, throughput only (3 timed steps after 1 warm-up; writes no model)
step bench stitched
$RL bench_NULL_stitched /usr/bin/time -v $PY $TR bench --config "$W/cfg_NULL_stitched.json" --out "$W/bench_stitched" --steps 3 --warmup 1
step compare
$RL smoke_compare $PY $D/smoke_compare.py "$W" "$REPO/logs/sib/d2-null/smoke.json"
step done
