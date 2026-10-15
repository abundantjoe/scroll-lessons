# Provenance: Project HERCULES | owner the owner | [id removed]
"""Compare smoke runs A (uninterrupted) and B (crash after step 7, resumed from the step-5 save): losses, final
weights, timing, peak RSS. Numbers only. Writes <work>/smoke_result.json."""
import hashlib
import json
import os
import statistics
import sys

import torch

W = sys.argv[1]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rss_gb(p):
    return json.load(open(p))["peak_rss_kb"] * 1024 / 1e9


def wall_s(p):
    return json.load(open(p))["wall_s"]


sA = json.load(open(os.path.join(W, "A", "summary.json")))
sB = json.load(open(os.path.join(W, "B", "summary.json")))
wA = torch.load(os.path.join(W, "A", "model_final.pth"), map_location="cpu", weights_only=False)
wB = torch.load(os.path.join(W, "B", "model_final.pth"), map_location="cpu", weights_only=False)
mA, mB = wA["model"], wB["model"]
same_keys = mA.keys() == mB.keys()
maxdiff = max(float((mA[k].float() - mB[k].float()).abs().max()) if mA[k].numel() else 0.0 for k in mA) if same_keys else None
bitwise = same_keys and all(torch.equal(mA[k], mB[k]) for k in mA)
logA = [json.loads(l) for l in open(os.path.join(W, "A", "train_log.jsonl"))]
stepsA = [r for r in logA if "loss" in r]
res = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
    data="SYNTHETIC (d2_data.write_synthetic_registry n=40 size=560 seed=101)",
    config_sha256=sA["config_sha256"], config_sha256_B=sB["config_sha256"],
    steps=sA["steps"], losses_A=sA["losses"], losses_B=sB["losses"],
    losses_equal=sA["losses"] == sB["losses"],
    max_abs_loss_diff=max(abs(a - b) for a, b in zip(sA["losses"], sB["losses"])),
    final_weights_bitwise_equal=bitwise, final_weights_max_abs_diff=maxdiff,
    model_final_sha256_A=sha(os.path.join(W, "A", "model_final.pth")),
    model_final_sha256_B=sha(os.path.join(W, "B", "model_final.pth")),
    resumptions_B=sB["resumptions"], checkpoint_events_A=sA["checkpoint_events"],
    checkpoint_events_B=sB["checkpoint_events"],
    s_per_step_A=[r["s_per_step"] for r in stepsA],
    median_s_per_step_A=sA["median_s_per_step"],
    median_s_per_step_A_excl_step1=statistics.median([r["s_per_step"] for r in stepsA][1:]),
    grad_norm_preclip_A=[r["grad_norm_preclip"] for r in stepsA],
    supervised_frac_A=[r["supervised_frac"] for r in stepsA],
    finite_loss_steps_A=sA["finite_loss_steps"],
    peak_rss_GB_A_time=rss_gb(os.path.join(W, "time_A.json")),
    peak_rss_GB_B1_time=rss_gb(os.path.join(W, "time_B1.json")),
    peak_rss_GB_B2_time=rss_gb(os.path.join(W, "time_B2.json")),
    peak_rss_GB_A_self=sA["peak_rss_kb"] * 1024 / 1e9,
    wall_s_A=wall_s(os.path.join(W, "time_A.json")), wall_s_B1=wall_s(os.path.join(W, "time_B1.json")),
    wall_s_B2=wall_s(os.path.join(W, "time_B2.json")),
    loop_s_A=sA["loop_s"], strict_load=sA["strict_load"], threads=sA["threads"], checks=sA["checks"],
    sample_digest_A=sA["sample_digest_final"], sample_digest_B=sB["sample_digest_final"],
    trainer_script=sA["script"],
    projected_h_12k_steps=12000 * sA["median_s_per_step"] / 3600,
)
res["projected_days_12k_steps"] = res["projected_h_12k_steps"] / 24
json.dump(res, open(os.path.join(W, "smoke_result.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if not isinstance(v, (list, dict))}, indent=1))
