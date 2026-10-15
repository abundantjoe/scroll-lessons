# Provenance: Project HERCULES | owner the owner | [id removed]
"""AMX benchmark of the official base ink model (task amx, items 3). Random inputs only; no scroll data.

One configuration per process (thread count fixed before torch starts its pools; clean peak RSS):
  --mode infer : model.eval(), torch.inference_mode(), batch 4, input (4,1,17,128,128) N(0,1)
  --mode train : D3 recipe step (tools/d3/d3_train.py): model.train(), official prepare_loss_inputs +
                 concatenate_deep_supervision_ignore + create_loss (smoothed BCE 0.5 + 0.25 Dice, ignore channel),
                 backward, clip_grad_norm_(1.0), AdamW(lr 2e-5, wd 3e-5) step, zero_grad; batch 8, random labels
  --dtype bf16 : torch.autocast('cpu', dtype=torch.bfloat16) around the forward only (loss on .float() logits as
                 in the official trainer; AdamW keeps fp32 master weights; no grad scaler is needed for bf16)
  --cl 1       : channels_last_3d for the 3-D stem weights and the input, channels_last for the 2-D network weights
                 and (via a forward pre-hook) for the stem output fed to the 2-D network
5 warm-up + 20 timed iterations (time.perf_counter around the whole step). Appends one JSON row to --out."""
import os, sys, argparse, json, time

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=("infer", "train"), required=True)
ap.add_argument("--dtype", choices=("fp32", "bf16"), required=True)
ap.add_argument("--threads", type=int, required=True)
ap.add_argument("--cl", type=int, default=0)
ap.add_argument("--warmup", type=int, default=5)
ap.add_argument("--iters", type=int, default=20)
ap.add_argument("--batch", type=int, default=0, help="0 = task default (infer 4, train 8)")
ap.add_argument("--out", required=True)
args = ap.parse_args()
os.environ["OMP_NUM_THREADS"] = str(args.threads)
os.environ["MKL_NUM_THREADS"] = str(args.threads)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
torch.set_num_threads(args.threads)
from common import load, rand_batch, stats, peak_rss_mb, cur_rss_mb, env_info, utc, LR, WD, INFER_BATCH, TRAIN_BATCH

torch.manual_seed(20260925)
gen = torch.Generator().manual_seed(20260925)
model, ink, tc, loss_fn, cfg = load()
rss_after_load = cur_rss_mb()
batch_n = args.batch or (INFER_BATCH if args.mode == "infer" else TRAIN_BATCH)


def to_cl(x):
    return x.contiguous(memory_format=torch.channels_last_3d) if x.ndim == 5 else x.contiguous(memory_format=torch.channels_last)


if args.cl:
    model.depth_fusion.to(memory_format=torch.channels_last_3d)
    model.network.to(memory_format=torch.channels_last)
    model.network.register_forward_pre_hook(lambda mod, inp: (inp[0].contiguous(memory_format=torch.channels_last),) + tuple(inp[1:]))

autocast = (lambda: torch.autocast("cpu", dtype=torch.bfloat16)) if args.dtype == "bf16" else (lambda: torch.autocast("cpu", enabled=False))
row = dict(utc=utc(), mode=args.mode, dtype=args.dtype, threads=args.threads, channels_last=bool(args.cl), batch=batch_n,
           warmup=args.warmup, iters=args.iters, rss_after_load_mb=rss_after_load, env=env_info())

if args.mode == "infer":
    model.eval()
    xs = [rand_batch(batch_n, gen) for _ in range(4)]
    if args.cl:
        xs = [to_cl(x) for x in xs]

    def step(i):
        with torch.inference_mode(), autocast():
            y = model(xs[i % len(xs)])["ink"]
        return y
else:
    from vesuvius.ink_detection.training.train import prepare_model_input, prepare_loss_inputs
    from vesuvius.ink_detection.training.stitching import run_model_forward
    from vesuvius.ink_detection.training.deep_supervision import concatenate_deep_supervision_ignore
    from vesuvius.ink_detection.training.optimizers import create_training_optimizer
    model.train()
    opt = create_training_optimizer(model, tc)
    assert type(opt).__name__ == "AdamW" and opt.param_groups[0]["lr"] == LR and opt.param_groups[0]["weight_decay"] == WD
    batches = [rand_batch(batch_n, gen, with_labels=True) for _ in range(4)]
    losses = []

    def step(i):
        b = batches[i % len(batches)]
        x = prepare_model_input(b, tc)
        if args.cl:
            x = to_cl(x)
        with autocast():
            preds = run_model_forward(model, x, tc.model_crop_size, stitched=tc.use_stitched_forward,
                                      use_gradient_checkpointing=tc.stitched_gradient_checkpointing)
        lp, targets, ignore = prepare_loss_inputs(preds, b, mode=ink.data.mode, force_full_supervision=tc.force_full_supervision)
        twi = concatenate_deep_supervision_ignore(targets, ignore, lp)
        loss = loss_fn(lp.float(), twi.float())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), tc.grad_clip)
        opt.step()
        opt.zero_grad(set_to_none=True)
        losses.append(float(loss.item()))
        return loss

times = []
t_all = time.perf_counter()
for i in range(args.warmup + args.iters):
    t0 = time.perf_counter()
    step(i)
    dt = time.perf_counter() - t0
    if i >= args.warmup:
        times.append(dt)
row.update(stats(times))
row["times_s"] = times
row["per_tile_median_s"] = row["median_s"] / batch_n
row["tiles_per_s"] = batch_n / row["median_s"]
row["peak_rss_mb"] = peak_rss_mb()
row["wall_total_s"] = time.perf_counter() - t_all
if args.mode == "train":
    row["loss_first"], row["loss_last"] = losses[0], losses[-1]
    row["grad_clip"] = tc.grad_clip
with open(args.out, "a") as f:
    f.write(json.dumps(row) + "\n")
print(json.dumps({k: v for k, v in row.items() if k not in ("times_s", "env")}))
