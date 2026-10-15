# Provenance: Project HERCULES | owner the owner | [id removed]
"""Which segment's bf16 autocast moves the uint8 map, and what mixed-precision placement costs. Random inputs only.

Segments as profile_split.py: stem (3-D depth-fusion), enc2d, dec2d (decoder + head). Each variant autocasts a subset
of segments to bf16 (the rest fp32; bf16 outputs are cast to fp32 at a segment boundary entering an fp32 segment).
Compared with all-fp32 over 32 random N(0,1) tiles (eval, batch 4): logit max/mean |diff|, uint8 map (official
clip(sigmoid)*255 truncation) max |diff|, fraction identical, fraction within +-2 levels, and the 99.9th percentile
of |logit diff|. Timing: batch 4, 4 threads, 5 warm-up + 20 timed."""
import os, sys, json, time, itertools
os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
torch.set_num_threads(int(os.environ["OMP_NUM_THREADS"]))
from common import load, rand_batch, stats, env_info, utc

model, *_ = load()
model.eval()
net = model.network
head = net.task_heads["ink"]
gen = torch.Generator().manual_seed(20260925)
X = [rand_batch(4, gen) for _ in range(8)]


def ctx(b):
    return torch.autocast("cpu", dtype=torch.bfloat16) if b else torch.autocast("cpu", enabled=False)


def run(x, v):
    with ctx(v[0]):
        s = model.depth_fusion(x)
    s = s if v[1] else s.float()
    with ctx(v[1]):
        f = net.shared_encoder(s)
    f = f if v[2] else [t.float() for t in f]
    with ctx(v[2]):
        return head(net.shared_decoder(f))


def u8(l):
    return l.float().sigmoid().clamp(0, 1).mul(255).to(torch.uint8)


res = dict(utc=utc(), env=env_info(), threads=torch.get_num_threads(), n_tiles=32, variants={})
with torch.inference_mode():
    ref = [run(x, (0, 0, 0)).float() for x in X]
    for v in itertools.product((0, 1), repeat=3):
        name = "stem%s_enc%s_dec%s" % tuple("bf16" if b else "fp32" for b in v)
        out = [run(x, v).float() for x in X]
        dl = torch.cat([(o - r).abs().flatten() for o, r in zip(out, ref)])
        du = torch.cat([(u8(o).int() - u8(r).int()).abs().flatten() for o, r in zip(out, ref)])
        t = []
        for i in range(25):
            t0 = time.perf_counter(); run(X[i % 2], v); d = time.perf_counter() - t0
            if i >= 5:
                t.append(d)
        res["variants"][name] = dict(logit_max_abs=float(dl.max()), logit_mean_abs=float(dl.mean()),
                                     logit_p999_abs=float(torch.quantile(dl[::7], 0.999)),
                                     u8_max_abs=int(du.max()), u8_frac_identical=float((du == 0).float().mean()),
                                     u8_frac_within_2=float((du <= 2).float().mean()), timing=stats(t))
        r = res["variants"][name]
        print(name, round(r["u8_frac_within_2"], 5), r["u8_max_abs"], round(r["logit_max_abs"], 4), round(r["timing"]["median_s"], 4), flush=True)
base = res["variants"]["stemfp32_encfp32_decfp32"]["timing"]["median_s"]
for r in res["variants"].values():
    r["speedup_vs_fp32"] = base / r["timing"]["median_s"]
json.dump(res, open(sys.argv[1], "w"), indent=1)
