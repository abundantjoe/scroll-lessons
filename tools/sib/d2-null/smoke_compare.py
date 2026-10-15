# Provenance: Project HERCULES | owner the owner | [id removed]
"""Summarise the d2-null PHASE 1 smoke (SYNTHETIC) into one JSON: timing, peak RSS, derangement, pairing with P384,
resume identity. Numbers and hashes only. Usage: smoke_compare.py WORKDIR OUT.json"""
import glob
import hashlib
import json
import os
import re
import statistics
import sys

import torch

W, OUT = sys.argv[1], sys.argv[2]
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def gnu_time_max_rss_kb(label):
    logs = sorted(glob.glob(os.path.join(REPO, "logs/sib/d2-null/out", f"*_{label}.log")))
    if not logs:
        return None
    m = re.findall(r"Maximum resident set size \(kbytes\): (\d+)", open(logs[-1]).read())
    return int(m[-1]) if m else None


def jl(p):
    return [json.loads(x) for x in open(p) if x.strip()]


A = json.load(open(os.path.join(W, "A/summary.json")))
B = json.load(open(os.path.join(W, "B/summary.json")))
la = [r for r in jl(os.path.join(W, "A/train_log.jsonl")) if "step" in r and "loss" in r]
lb = [r for r in jl(os.path.join(W, "B/train_log.jsonl")) if "step" in r and "loss" in r]
wa = torch.load(os.path.join(W, "A/model_final.pth"), map_location="cpu", weights_only=False)["model"]
wb = torch.load(os.path.join(W, "B/model_final.pth"), map_location="cpu", weights_only=False)["model"]
maxdiff = max(float((wa[k].float() - wb[k].float()).abs().max()) for k in wa)
bitwise = all(torch.equal(wa[k], wb[k]) for k in wa)
lbd = {r["step"]: r for r in lb}
PN = json.load(open(os.path.join(W, "pair_NULL.json")))
PP = json.load(open(os.path.join(W, "pair_P384.json")))
pairs = []
for a, b in zip(PP["steps"], PN["steps"]):
    pairs.append(dict(step=a["step"], kind=a["kind"], image_equal=a["image_sha256"] == b["image_sha256"],
                      draws_equal=a["draws_sha256"] == b["draws_sha256"], digest_equal=a["sample_digest"] == b["sample_digest"],
                      ink_differs=a["ink_sha256"] != b["ink_sha256"], sup_differs=a["sup_sha256"] != b["sup_sha256"],
                      torch_rng_after_step_equal=a["torch_rng_after_step"] == b["torch_rng_after_step"]))
digest_A = {r["step"]: r["sample_digest"] for r in la}
bench = json.load(open(os.path.join(W, "bench_stitched/bench.json")))
out = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
    data="SYNTHETIC (d2_data.write_synthetic_registry n=96 size=384 seed=20260926); no real data, no image opened",
    config_NULL_sha256=A["config_sha256"], config_P384_sha256=PP["config_sha256"],
    run_A=dict(steps=A["steps"], finite_loss_steps=A["finite_loss_steps"], losses=A["losses"],
               s_per_step=[r["s_per_step"] for r in la], median_s_per_step=A["median_s_per_step"],
               median_s_per_step_excl_step1=statistics.median([r["s_per_step"] for r in la][1:]),
               peak_rss_kb_ru_maxrss=A["peak_rss_kb"], peak_rss_kb_gnu_time=gnu_time_max_rss_kb("smoke_A_null_10"),
               wall_s=A["wall_s"], loop_s=A["loop_s"], threads=A["threads"], checks=A["checks"],
               derangement=A["meta"].get("derangement"), checkpoint_events=A["checkpoint_events"],
               model_final_sha256=A["model_final"]["sha256"], sample_digest_final=A["sample_digest_final"]),
    resume=dict(
        crash_after_step=7, resumed_from_step=[r.get("from_step") for r in B["resumptions"]],
        resumptions=B["resumptions"],
        losses_steps_1_7_equal_A=[lbd[s]["loss"] == la[s - 1]["loss"] for s in range(1, 8)],
        losses_after_resume_B=[r["loss"] for r in lb if r.get("run_index") == 1],
        losses_steps_6_10_A=[r["loss"] for r in la if r["step"] >= 6],
        final_losses_equal=B["losses"] == A["losses"],
        final_weights_bitwise_equal=bitwise, final_weights_max_abs_diff=maxdiff,
        model_final_sha256_A=A["model_final"]["sha256"], model_final_sha256_B=B["model_final"]["sha256"],
        sample_digest_equal=A["sample_digest_final"] == B["sample_digest_final"],
        peak_rss_kb_gnu_time_resume=gnu_time_max_rss_kb("smoke_B_null_resume")),
    pairing=dict(
        per_step=pairs,
        all_images_equal=all(p["image_equal"] for p in pairs), all_draws_equal=all(p["draws_equal"] for p in pairs),
        labels_differ_every_step=all(p["ink_differs"] for p in pairs),
        rng_consumed_by_model_step_P384=PP["rng_consumed_by_model_step"],
        rng_consumed_by_model_step_NULL=PN["rng_consumed_by_model_step"],
        pair_NULL_digest_matches_run_A=[PN["steps"][i]["sample_digest"] == digest_A.get(i + 1) for i in range(len(PN["steps"]))],
        losses_train_steps_P384=[s["loss"] for s in PP["steps"] if s["kind"] == "train_step"],
        losses_train_steps_NULL=[s["loss"] for s in PN["steps"] if s["kind"] == "train_step"],
        losses_NULL_pair_equal_run_A=[s["loss"] == la[s["step"] - 1]["loss"] for s in PN["steps"] if s["kind"] == "train_step"]),
    derangement_independent=PN.get("derangement_independent"),
    null_checks_trainer=PN["checks"],
    bench_stitched=dict(micro_batch=bench["micro_batch"], forward=bench["forward"], s_per_step=bench["s_per_step"],
                        median_s_per_step=bench["median_s_per_step"], peak_rss_kb_ru_maxrss=bench["peak_rss_kb"],
                        peak_rss_kb_gnu_time=gnu_time_max_rss_kb("bench_NULL_stitched")),
)
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps({k: out[k] for k in ("run_A", "resume", "derangement_independent")}, indent=1)[:6000])
