#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Task d2-p128 phase 1: SYNTHETIC smoke of arm P128 (tile 128, 24 x 15 deg rotations), seed 1, fp32, 4 threads,
# batch 32, 30 steps, with the pinned trainer copy (tools/sib/d2-p128, = sib-trainer commit 8475920f).
# Run A: 30 steps uninterrupted. Run B: same config, hard exit after step 25 (last save at step 20), then resumed to 30.
# Bar: B's per-step losses (steps 1-30) and final weights bitwise equal to A's. No real data; no image is written.
# ckpt-every is 10 here (not 250) only so that a save and a resume happen inside 30 steps; no remote ref (weights stay local).
set -euo pipefail
T=$(cd "$(dirname "$0")" && pwd); W=${W:-/work/sib/d2p128_smoke}; PY=/opt/hv-ink/bin/python
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
rm -rf "$W"; mkdir -p "$W"
$PY -c "import sys; sys.path.insert(0,'$T'); import d2_data; print(d2_data.write_synthetic_registry('$W/syn', n=256, size=184, seed=1, shard_n=64))"
$PY "$T/d2_train.py" make-config --arm P128 --seed 1 --batch 32 --micro-batch 32 --steps 30 --threads 4 --precision fp32 \
    --subtile --z-jitter 2 --z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --log-every 1 --ckpt-every 10 \
    --source syn=pairs:$W/syn/registry.json --hash-sources --out "$W/cfg.json"
sha256sum "$W/cfg.json"
$PY "$T/d2_train.py" train --config "$W/cfg.json" --out "$W/A"
set +e; $PY "$T/d2_train.py" train --config "$W/cfg.json" --out "$W/B" --die-after 25; rc=$?; set -e
echo "B first leg exit code $rc (99 = simulated crash)"; test "$rc" = 99
ls -l "$W/B"
$PY "$T/d2_train.py" train --config "$W/cfg.json" --out "$W/B"
$PY - "$W" <<'PY'
import json, sys, hashlib, torch
W = sys.argv[1]
A, B = (json.load(open(f"{W}/{r}/summary.json")) for r in "AB")
ma = torch.load(f"{W}/A/model_final.pth", map_location="cpu", weights_only=False)["model"]
mb = torch.load(f"{W}/B/model_final.pth", map_location="cpu", weights_only=False)["model"]
wt_eq = ma.keys() == mb.keys() and all(torch.equal(ma[k], mb[k]) for k in ma)
loss_eq = A["losses"] == B["losses"]
res = dict(steps=A["steps"], loss_bitwise_equal=loss_eq, weights_bitwise_equal=wt_eq,
           digest_equal=A["sample_digest_final"] == B["sample_digest_final"],
           finite_A=A["finite_loss_steps"], resumptions_B=B["resumptions"],
           median_s_per_step_A=A["median_s_per_step"], median_s_per_step_B_resumed_leg=B["median_s_per_step"],
           peak_rss_kb_A=A["peak_rss_kb"], peak_rss_kb_B_resumed_leg=B["peak_rss_kb"],
           loss_first=A["loss_first"], loss_last=A["loss_last"],
           model_final_sha256_A=A["model_final"]["sha256"], model_final_sha256_B=B["model_final"]["sha256"],
           checks=A["checks"], ckpt_events_A=A["checkpoint_events"], threads=A["threads"], config_sha256=A["config_sha256"])
print(json.dumps(res, indent=1))
json.dump(res, open(f"{W}/smoke_result.json", "w"), indent=1)
assert loss_eq and wt_eq, "resume not bitwise identical"
print("SMOKE OK")
PY
