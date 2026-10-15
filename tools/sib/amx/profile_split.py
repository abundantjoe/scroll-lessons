# Provenance: Project HERCULES | owner the owner | [id removed]
"""Item 4: time and FLOP split per module of the official base model, fp32 vs bf16 autocast. Random inputs only.

Segments (the model's own forward, run piecewise; the piecewise output is checked bitwise against model(x)):
  stem    model.depth_fusion (LocalDepthFusionStem: the 3-D part, 2 Conv3d + attention/max depth pooling)
  enc2d   model.network.shared_encoder (2-D residual encoder, 6 stages, returns 6 skips)
  dec2d   model.network.shared_decoder + model.network.task_heads['ink'] (2-D decoder and 1x1 head)
Inference: batch 4, inference_mode, each segment timed separately (5 warm-up, 20 timed).
Training: batch 8, forward timed per segment; backward run piecewise through detached boundary tensors
(requires_grad leaves), so each segment's backward is timed on its own; loss = official create_loss on the
official prepare_loss_inputs targets (random labels). Optimizer time is measured separately (AdamW over all params,
and over the decoder params only).
FLOPs: torch.utils.flop_counter.FlopCounterMode per segment, forward and backward (counts conv/matmul/deconv only;
norms, activations, softmax and pooling are not counted)."""
import os, sys, argparse, json, time
ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--warmup", type=int, default=5)
ap.add_argument("--iters", type=int, default=20)
ap.add_argument("--out", required=True)
args = ap.parse_args()
os.environ["OMP_NUM_THREADS"] = str(args.threads)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
from torch.utils.flop_counter import FlopCounterMode
torch.set_num_threads(args.threads)
from common import load, rand_batch, stats, env_info, utc, peak_rss_mb

model, ink, tc, loss_fn, cfg = load()
from vesuvius.ink_detection.training.train import prepare_loss_inputs
from vesuvius.ink_detection.training.deep_supervision import concatenate_deep_supervision_ignore
net = model.network
head = net.task_heads["ink"]


def stem(x):
    return model.depth_fusion(x)


def enc(s):
    return net.shared_encoder(s)


def dec(f):
    return head(net.shared_decoder(f))


def ac(dtype):
    return torch.autocast("cpu", dtype=torch.bfloat16) if dtype == "bf16" else torch.autocast("cpu", enabled=False)


gen = torch.Generator().manual_seed(20260925)
res = dict(utc=utc(), threads=args.threads, env=env_info(), warmup=args.warmup, iters=args.iters,
           params=dict(stem=sum(p.numel() for p in model.depth_fusion.parameters()),
                       enc2d=sum(p.numel() for p in net.shared_encoder.parameters()),
                       dec2d=sum(p.numel() for p in net.shared_decoder.parameters()) + sum(p.numel() for p in head.parameters())),
           infer={}, train={}, flops={})
assert sum(res["params"].values()) == sum(p.numel() for p in model.parameters())

# piecewise == full (bitwise), both dtypes
model.eval()
x4 = rand_batch(4, gen)
with torch.inference_mode():
    for dt in ("fp32", "bf16"):
        with ac(dt):
            full = model(x4)["ink"]
            pw = dec(enc(stem(x4)))
        res.setdefault("piecewise_equals_full", {})[dt] = float((full.float() - pw.float()).abs().max())

# inference timing per segment
for dt in ("fp32", "bf16"):
    xs = [rand_batch(4, gen) for _ in range(2)]
    t = dict(stem=[], enc2d=[], dec2d=[], total=[])
    with torch.inference_mode(), ac(dt):
        for i in range(args.warmup + args.iters):
            x = xs[i % 2]
            t0 = time.perf_counter(); s = stem(x); t1 = time.perf_counter(); f = enc(s); t2 = time.perf_counter()
            y = dec(f); t3 = time.perf_counter()
            if i >= args.warmup:
                t["stem"].append(t1 - t0); t["enc2d"].append(t2 - t1); t["dec2d"].append(t3 - t2); t["total"].append(t3 - t0)
    r = {k: stats(v) for k, v in t.items()}
    tot = r["total"]["median_s"]
    for k in ("stem", "enc2d", "dec2d"):
        r[k]["share_of_total_median"] = r[k]["median_s"] / tot
    res["infer"][dt] = r

# training timing per segment (forward + piecewise backward), batch 8
model.train()
params_all = list(model.parameters())
params_dec = list(net.shared_decoder.parameters()) + list(head.parameters())
opt_all = torch.optim.AdamW(params_all, lr=2e-5, weight_decay=3e-5)
opt_dec = torch.optim.AdamW(params_dec, lr=2e-5, weight_decay=3e-5)
for dt in ("fp32", "bf16"):
    bs = [rand_batch(8, gen, with_labels=True) for _ in range(2)]
    keys = ("fwd_stem", "fwd_enc2d", "fwd_dec2d", "loss", "bwd_dec2d", "bwd_enc2d", "bwd_stem", "adamw_all", "adamw_dec_only", "total")
    t = {k: [] for k in keys}
    for i in range(args.warmup + args.iters):
        b = bs[i % 2]
        x = b["image"].float()
        T = [time.perf_counter()]
        with ac(dt):
            s = stem(x); T.append(time.perf_counter())
            s_leaf = s.detach().requires_grad_(True)
            f = enc(s_leaf); T.append(time.perf_counter())
            f_leaf = [v.detach().requires_grad_(True) for v in f]
            y = dec(f_leaf); T.append(time.perf_counter())
        lp, targets, ignore = prepare_loss_inputs(y, b, mode=ink.data.mode)
        twi = concatenate_deep_supervision_ignore(targets, ignore, lp)
        loss = loss_fn(lp.float(), twi.float()); T.append(time.perf_counter())
        loss.backward(); T.append(time.perf_counter())
        torch.autograd.backward(f, [v.grad for v in f_leaf]); T.append(time.perf_counter())
        s.backward(s_leaf.grad); T.append(time.perf_counter())
        torch.nn.utils.clip_grad_norm_(params_all, 1.0)
        t_opt0 = time.perf_counter(); opt_all.step(); T.append(time.perf_counter())
        # decoder-only AdamW step timed separately on the same grads (the decoder takes a second update; harmless for
        # timing, which does not depend on weight values)
        t_d0 = time.perf_counter(); opt_dec.step(); t_d1 = time.perf_counter()
        opt_all.zero_grad(set_to_none=True); opt_dec.zero_grad(set_to_none=True)
        if i >= args.warmup:
            names = ("fwd_stem", "fwd_enc2d", "fwd_dec2d", "loss", "bwd_dec2d", "bwd_enc2d", "bwd_stem")
            for j, k in enumerate(names):
                t[k].append(T[j + 1] - T[j])
            t["adamw_all"].append(T[-1] - t_opt0)
            t["adamw_dec_only"].append(t_d1 - t_d0)
            t["total"].append(T[-1] - T[0])
    r = {k: stats(v) for k, v in t.items()}
    tot = r["total"]["median_s"]
    for k in keys[:-1]:
        r[k]["share_of_total_median"] = r[k]["median_s"] / tot
    r["seg_share"] = dict(
        stem=(r["fwd_stem"]["median_s"] + r["bwd_stem"]["median_s"]) / tot,
        enc2d=(r["fwd_enc2d"]["median_s"] + r["bwd_enc2d"]["median_s"]) / tot,
        dec2d_plus_loss=(r["fwd_dec2d"]["median_s"] + r["bwd_dec2d"]["median_s"] + r["loss"]["median_s"]) / tot,
        adamw=r["adamw_all"]["median_s"] / tot)
    res["train"][dt] = r
# note: the weights moved during the timed training steps; FLOP counts do not depend on weight values

# FLOPs per segment (per batch), forward (batch 4 and 8) and backward (batch 8)
model.train()
for n in (4, 8):
    x = rand_batch(n, gen)
    fl = {}
    with torch.no_grad():
        with FlopCounterMode(display=False) as fc:
            s = stem(x)
        fl["stem"] = fc.get_total_flops()
        with FlopCounterMode(display=False) as fc:
            f = enc(s)
        fl["enc2d"] = fc.get_total_flops()
        with FlopCounterMode(display=False) as fc:
            y = dec(f)
        fl["dec2d"] = fc.get_total_flops()
    fl["total"] = sum(fl.values())
    fl["share"] = {k: fl[k] / fl["total"] for k in ("stem", "enc2d", "dec2d")}
    res["flops"][f"forward_batch{n}"] = fl
b = rand_batch(8, gen, with_labels=True)
x = b["image"]
s = stem(x); s_leaf = s.detach().requires_grad_(True)
f = enc(s_leaf); f_leaf = [v.detach().requires_grad_(True) for v in f]
y = dec(f_leaf)
lp, targets, ignore = prepare_loss_inputs(y, b, mode=ink.data.mode)
loss = loss_fn(lp.float(), concatenate_deep_supervision_ignore(targets, ignore, lp).float())
fb = {}
with FlopCounterMode(display=False) as fc:
    loss.backward()
fb["dec2d"] = fc.get_total_flops()
with FlopCounterMode(display=False) as fc:
    torch.autograd.backward(f, [v.grad for v in f_leaf])
fb["enc2d"] = fc.get_total_flops()
with FlopCounterMode(display=False) as fc:
    s.backward(s_leaf.grad)
fb["stem"] = fc.get_total_flops()
fb["total"] = sum(fb.values())
fb["share"] = {k: fb[k] / fb["total"] for k in ("stem", "enc2d", "dec2d")}
res["flops"]["backward_batch8"] = fb
res["flops"]["note"] = "FlopCounterMode counts matmul/conv/deconv FLOPs (2 x MACs); norms, activations, pooling, softmax not counted"
# achieved throughput (counted FLOPs / median time) for the inference segments
for dt in ("fp32", "bf16"):
    res["infer"][dt]["achieved_gflops"] = {k: res["flops"]["forward_batch4"][k] / res["infer"][dt][k]["median_s"] / 1e9
                                           for k in ("stem", "enc2d", "dec2d")}
res["peak_rss_mb"] = peak_rss_mb()
json.dump(res, open(args.out, "w"), indent=1)
print(json.dumps(dict(piecewise=res["piecewise_equals_full"],
                      infer={dt: {k: round(res["infer"][dt][k]["median_s"], 4) for k in ("stem", "enc2d", "dec2d", "total")} for dt in ("fp32", "bf16")},
                      train={dt: {k: round(v, 3) for k, v in res["train"][dt]["seg_share"].items()} for dt in ("fp32", "bf16")},
                      flops_fwd4={k: res["flops"]["forward_batch4"]["share"][k] for k in ("stem", "enc2d", "dec2d")},
                      gflop_fwd_per_tile=res["flops"]["forward_batch4"]["total"] / 4 / 1e9)))
