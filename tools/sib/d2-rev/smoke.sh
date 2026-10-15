#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# d2-rev PHASE 1 synthetic smoke of arm REV seed 1 (SYNTHETIC data only; no real data, no image written or opened).
#  0. synthetic registry (d2_data.write_synthetic_registry: n 40, S 546 = corner-free for T 384 with 24 x 15 deg)
#  1. pairing check (rev_pairing_check.py): P384 / REV / P384-on-reversed, 2 steps, batch 32 = 8 x micro 4
#  2. U: REV seed 1, 10 steps uninterrupted, fp32, 4 threads, batch 32 via micro-batch 4, full forward, ckpt every 5
#  3. I: same config, killed after step 7 (--die-after 7, resume state saved at step 5), then resumed to step 10
#  4. compare U vs I (per-step losses, final weights sha256) -> smoke.json
# Resume state is kept local only (no --remote-ref): nothing is pushed anywhere.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
TD=$REPO/tools/sib/d2-rev
RL=$TD/rl.sh
W=${W:-/work/sib/d2rev_smoke}
PY=/opt/hv-ink/bin/python
export PYTHONPATH=/work/d3_timing/pylib OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
mkdir -p "$W"
REG=$W/syn546/registry.json
[ -f "$REG" ] || $RL smoke_registry $PY -c "import sys; sys.path.insert(0,'$TD'); import d2_data; print(d2_data.write_synthetic_registry('$W/syn546', n=40, size=546, seed=11, shard_n=20))" || exit 1

[ -f "$W/pair/pairing_check.json" ] || $RL smoke_pairing $PY "$TD/rev_pairing_check.py" --registry "$REG" --out "$W/pair" \
  --steps 2 --batch 32 --micro-batch 4 --threads 4 --forward full

CFG=$W/cfg_rev_smoke.json
$RL smoke_make_config $PY "$TD/d2_train.py" make-config --arm REV --seed 1 --batch 32 --micro-batch 4 --steps 10 \
  --rot24 --subtile --threads 4 --z-jitter 2 --z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --forward full \
  --precision fp32 --source "syn=pairs:$REG" --hash-sources --log-every 1 --ckpt-every 5 --out "$CFG" || exit 1

[ -f "$W/U/summary.json" ] || $RL smoke_U $PY "$TD/d2_train.py" train --config "$CFG" --out "$W/U"
[ -f "$W/I/summary.json" ] || { $RL smoke_I_die7 $PY "$TD/d2_train.py" train --config "$CFG" --out "$W/I" --die-after 7
                                 $RL smoke_I_resume $PY "$TD/d2_train.py" train --config "$CFG" --out "$W/I"; }

$RL smoke_compare $PY - "$W" "$REPO/logs/sib/d2-rev/smoke.json" <<'PY'
import json, sys, hashlib, os
W, OUT = sys.argv[1], sys.argv[2]
def L(p):
    return [json.loads(l) for l in open(p) if l.strip()]
U, I = json.load(open(f"{W}/U/summary.json")), json.load(open(f"{W}/I/summary.json"))
ul = [r for r in L(f"{W}/U/train_log.jsonl") if "loss" in r]
il = [r for r in L(f"{W}/I/train_log.jsonl") if "loss" in r]
ilast = {}
for r in il:
    ilast[r["step"]] = r          # the resumed rows overwrite the pre-crash rows of steps 6-7
pair = json.load(open(f"{W}/pair/pairing_check.json"))
cfg = json.load(open(f"{W}/cfg_rev_smoke.json"))
res = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]", id="d2rev_phase1_smoke",
    data="SYNTHETIC (d2_data.write_synthetic_registry n 40, S 546, seed 11)", arm=cfg["arm"], seed=cfg["seed"],
    config_sha256=U["config_sha256"], config=dict((k, cfg[k]) for k in ("tile", "rot24", "null", "rev", "subtile", "batch",
        "micro_batch", "steps", "forward", "precision", "threads", "z", "optimizer", "ckpt", "log_every")),
    steps=U["steps"], finite_loss_steps=U["finite_loss_steps"], losses_U=U["losses"],
    median_s_per_step=U["median_s_per_step"], s_per_step_U=[r["s_per_step"] for r in ul],
    peak_rss_kb_U=U["peak_rss_kb"], peak_rss_gb_U=round(U["peak_rss_kb"] / 1024 ** 2, 3), peak_rss_kb_I_resumed=I["peak_rss_kb"],
    wall_s_U=U["wall_s"], threads=U["threads"], checks=U["checks"],
    checkpoint_events_U=U["checkpoint_events"], resumptions_I=I["resumptions"],
    resume=dict(
        losses_I=I["losses"], per_step_equal=[ilast[r["step"]]["loss"] == r["loss"] for r in ul],
        losses_bitwise_equal=I["losses"] == U["losses"],
        model_final_sha256_U=U["model_final"]["sha256"], model_final_sha256_I=I["model_final"]["sha256"],
        final_weights_bitwise_equal=U["model_final"]["sha256"] == I["model_final"]["sha256"],
        sample_digest_equal=U["sample_digest_final"] == I["sample_digest_final"],
        resumed_from_step=I["resumptions"][-1]["from_step"] if I["resumptions"] else None),
    pairing=dict(pass_=pair["pass_"], steps=pair["steps"], batch=pair["batch"], micro_batch=pair["micro_batch"],
                 per_step=[{k: v for k, v in p.items() if k not in ("rotations", "z_offsets")} for p in pair["per_step"]],
                 rev_trainer_checks=pair["rev_trainer_checks"],
                 pairing_check_json_sha256=hashlib.sha256(open(f"{W}/pair/pairing_check.json", "rb").read()).hexdigest()),
    note="model weights stay local (/work); never pushed")
res["pass_"] = bool(pair["pass_"] and res["resume"]["losses_bitwise_equal"] and res["resume"]["final_weights_bitwise_equal"]
                    and U["finite_loss_steps"] == U["steps"] and U["checks"].get("rev_syn_exact_depth_reverse") is True)
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(dict(pass_=res["pass_"], median_s_per_step=res["median_s_per_step"], peak_rss_gb=res["peak_rss_gb_U"],
                      resume=res["resume"], pairing=pair["pass_"])))
sys.exit(0 if res["pass_"] else 1)
PY
