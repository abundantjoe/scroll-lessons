# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 smoke tests (numbers only): (1) every arm 5 steps (finite loss; NULLA derangement has no fixed point; REVA input
is the exact depth reverse; final-weights save path), (2) checkpoint save/resume test on FA: a reference run of 12
steps with checkpoints every 4, versus a run that hard-exits after step 10 (checkpoints at 4 and 8; the step-8 save
forced through the delete-then-write branch with --budget-bytes 1) and is then re-run (must resume from step 8 and
finish), then re-run once more (must be a no-op). Smoke model files are hashed and deleted.
Writes /work/d3/work/smoke/smoke_results.json."""
import os, sys, json, subprocess, hashlib, shutil
import torch

SM = "/work/d3/work/smoke"
PY = "/opt/hv-ink/bin/python"
TR = "/work/d3/scripts/d3_train.py"
ENV = dict(os.environ, PYTHONPATH="/work/d3_timing/pylib", OMP_NUM_THREADS="3", MKL_NUM_THREADS="3")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def run(args, log):
    with open(log, "a") as lf:
        return subprocess.run([PY, TR, *args], stdout=lf, stderr=subprocess.STDOUT, env=ENV).returncode


def log_records(out):
    return [json.loads(l) for l in open(f"{out}/train_log.jsonl")]


res = {"arms": {}, "resume_test": {}}
os.makedirs(SM, exist_ok=True)
for arm in ("CTRL", "FA", "NULLA", "REVA"):
    out = f"{SM}/{arm}"
    shutil.rmtree(out, ignore_errors=True)
    rc = run(["--arm", arm, "--steps", "5", "--out", out, "--smoke"], f"{SM}/{arm}.log")
    s = json.load(open(f"{out}/summary.json"))
    recs = [r for r in log_records(out) if "loss" in r]
    res["arms"][arm] = dict(rc=rc, steps=s["steps"], finite_loss_steps=s["finite_loss_steps"],
                            losses=[r["loss"] for r in recs], n_fold_a_in_batch=[r["n_fold_a_in_batch"] for r in recs],
                            checks=s["checks"], derangement=s["meta"].get("derangement"),
                            n_fold_a=s["meta"].get("n_fold_a"), n_replay=s["meta"]["n_replay"],
                            median_s_per_step=s["median_s_per_step"], peak_rss_kb=s["peak_rss_kb"],
                            strict_load=s["strict_load"], model_final_sha256=s["model_final"]["sha256"],
                            model_final_bytes=s["model_final"]["bytes"])
    os.remove(f"{out}/model_final.pth")
    print(arm, json.dumps(res["arms"][arm]), flush=True)

# ---- save/resume test (FA)
ref, rsm = f"{SM}/resume_ref_FA", f"{SM}/resume_FA"
for d in (ref, rsm):
    shutil.rmtree(d, ignore_errors=True)
common = ["--arm", "FA", "--steps", "12", "--ckpt-every", "4"]
rc_ref = run(common + ["--out", ref], f"{SM}/resume_ref.log")
rc_die = run(common + ["--out", rsm, "--die-after", "10", "--budget-bytes", "1"], f"{SM}/resume_die.log")
had_ckpt = os.path.exists(f"{rsm}/resume_latest.pth")
ck_step = torch.load(f"{rsm}/resume_latest.pth", map_location="cpu", weights_only=False)["step"] if had_ckpt else None
rc_res = run(common + ["--out", rsm], f"{SM}/resume_resume.log")
rc_noop = run(common + ["--out", rsm], f"{SM}/resume_noop.log")
sref, sres = json.load(open(f"{ref}/summary.json")), json.load(open(f"{rsm}/summary.json"))
a = torch.load(f"{ref}/model_final.pth", map_location="cpu", weights_only=False)["model"]
b = torch.load(f"{rsm}/model_final.pth", map_location="cpu", weights_only=False)["model"]
maxdiff = max(float((a[k].float() - b[k].float()).abs().max()) for k in a)
bitwise = all(torch.equal(a[k], b[k]) for k in a)
lref = [r for r in log_records(ref) if "loss" in r]
lres = [r for r in log_records(rsm) if "loss" in r]
res["resume_test"] = dict(
    rc_reference=rc_ref, rc_simulated_crash=rc_die, checkpoint_present_after_crash=had_ckpt,
    checkpoint_step_after_crash=ck_step, rc_resumed=rc_res, rc_rerun_after_complete=rc_noop,
    noop_message=open(f"{SM}/resume_noop.log").read().strip().splitlines()[-1],
    resumptions=sres["resumptions"], checkpoint_events_resumed_run=sres["checkpoint_events"],
    checkpoint_events_reference=sref["checkpoint_events"],
    resume_file_deleted_after_completion=not os.path.exists(f"{rsm}/resume_latest.pth"),
    steps_reference=sref["steps"], steps_resumed=sres["steps"], finite_loss_steps_resumed=sres["finite_loss_steps"],
    losses_reference=sref.get("loss_last"), final_loss_resumed=sres["loss_last"],
    loss_by_step_reference={r["step"]: r["loss"] for r in lref},
    loss_by_step_resumed_log=[(r["step"], r["run_index"], r["loss"]) for r in lres],
    final_weights_bitwise_identical=bitwise, final_weights_max_abs_diff=maxdiff,
    model_final_sha256=dict(reference=sref["model_final"]["sha256"], resumed=sres["model_final"]["sha256"]))
for d in (ref, rsm):
    os.remove(f"{d}/model_final.pth")
res["note"] = "smoke model_final.pth files were hashed (above) and deleted"
json.dump(res, open(f"{SM}/smoke_results.json", "w"), indent=1)
print(json.dumps(res["resume_test"], indent=1)[:4000])
print("SMOKE_RESULTS_SHA256", sha256(f"{SM}/smoke_results.json"))
