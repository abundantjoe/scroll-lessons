# Provenance: Project HERCULES | owner the owner | [id removed]
"""Item 3 (report only): int8 inference feasibility for the official base model on this CPU. Random inputs only.

Attempts (each isolated; an exception is recorded, never worked around by editing official code):
  dyn      torch.ao.quantization.quantize_dynamic on {nn.Linear} (the only conv-free dynamic path in torch)
  fx       FX graph-mode static PTQ (get_default_qconfig_mapping('x86'), prepare_fx / convert_fx) on the 2-D network
           (model.network), stem kept fp32; calibration on 8 random N(0,1) tiles
  fx_parts FX static PTQ of the traceable sub-modules only (2-D encoder; 2-D decoder + head), stem kept fp32
  pt2e     torch.export + X86InductorQuantizer (prepare_pt2e / convert_pt2e) + torch.compile (inductor), whole model
Timing: batch 4, inference_mode, 5 warm-up + 20 timed, 4 threads. Output difference vs fp32 on random inputs is
reported (logits and official uint8 map), but random-input calibration says nothing about fidelity on real data."""
import os, sys, argparse, json, time, copy, traceback
ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--warmup", type=int, default=5)
ap.add_argument("--iters", type=int, default=20)
ap.add_argument("--out", required=True)
ap.add_argument("--only", default="dyn,fx,fx_parts,pt2e")
args = ap.parse_args()
os.environ["OMP_NUM_THREADS"] = str(args.threads)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from torch import nn
torch.set_num_threads(args.threads)
from common import load, rand_batch, stats, env_info, utc, peak_rss_mb

model, ink, tc, loss_fn, cfg = load()
model.eval()
gen = torch.Generator().manual_seed(20260925)
calib = [rand_batch(4, gen) for _ in range(2)]
xs = [rand_batch(4, gen) for _ in range(2)]
res = dict(utc=utc(), threads=args.threads, env=env_info(), attempts={})


def u8(l):
    return l.float().sigmoid().clamp(0, 1).mul(255).to(torch.uint8)


with torch.inference_mode():
    ref = [model(x)["ink"] for x in xs]


def bench(fn):
    t = []
    with torch.inference_mode():
        for i in range(args.warmup + args.iters):
            t0 = time.perf_counter(); fn(xs[i % 2]); d = time.perf_counter() - t0
            if i >= args.warmup:
                t.append(d)
        outs = [fn(x) for x in xs]
    s = stats(t)
    dl = max(float((o.float() - r.float()).abs().max()) for o, r in zip(outs, ref))
    du = [(u8(o).int() - u8(r).int()).abs() for o, r in zip(outs, ref)]
    s.update(logit_max_abs_diff_vs_fp32=dl, u8_max_abs_diff_vs_fp32=int(max(int(d.max()) for d in du)),
             u8_frac_within_2_vs_fp32=float(sum(int((d <= 2).sum()) for d in du) / sum(d.numel() for d in du)))
    return s


res["fp32_eager"] = bench(lambda x: model(x)["ink"])


def attempt(name, fn):
    t0 = time.time()
    try:
        res["attempts"][name] = dict(status="ok", **fn())
    except Exception as e:
        res["attempts"][name] = dict(status="failed", error=f"{type(e).__name__}: {str(e)[:600]}",
                                     trace_tail=traceback.format_exc().strip().splitlines()[-6:])
    res["attempts"][name]["setup_wall_s"] = time.time() - t0
    print(name, json.dumps({k: v for k, v in res["attempts"][name].items() if k != "trace_tail"})[:800], flush=True)


def dyn():
    n_lin = sum(isinstance(m, nn.Linear) for m in model.modules())
    q = torch.ao.quantization.quantize_dynamic(copy.deepcopy(model), {nn.Linear}, dtype=torch.qint8)
    out = dict(n_linear_modules=n_lin, n_conv_modules=sum(isinstance(m, (nn.Conv2d, nn.Conv3d, nn.ConvTranspose2d)) for m in model.modules()))
    out.update(bench(lambda x: q(x)["ink"]))
    return out


def fx():
    from torch.ao.quantization import get_default_qconfig_mapping
    from torch.ao.quantization.quantize_fx import prepare_fx, convert_fx
    torch.backends.quantized.engine = "x86"
    m = copy.deepcopy(model)
    with torch.inference_mode():
        s_ex = m.depth_fusion(calib[0])
    qm = get_default_qconfig_mapping("x86")
    p = prepare_fx(m.network, qm, example_inputs=(s_ex,))
    with torch.inference_mode():
        for c in calib:
            p(m.depth_fusion(c))
    qn = convert_fx(p)
    return bench(lambda x: qn(m.depth_fusion(x))["ink"])


def fx_parts():
    """FX static PTQ of the traceable sub-modules (2-D encoder and 2-D decoder + head); stem fp32."""
    from torch.ao.quantization import get_default_qconfig_mapping
    from torch.ao.quantization.quantize_fx import prepare_fx, convert_fx
    torch.backends.quantized.engine = "x86"
    m = copy.deepcopy(model)
    net = m.network
    qm = get_default_qconfig_mapping("x86")
    with torch.inference_mode():
        s_ex = m.depth_fusion(calib[0])
        f_ex = net.shared_encoder(s_ex)
    pe = prepare_fx(net.shared_encoder, qm, example_inputs=(s_ex,))

    class DecHead(nn.Module):
        def __init__(self):
            super().__init__(); self.dec = net.shared_decoder; self.head = net.task_heads["ink"]

        def forward(self, f0, f1, f2, f3, f4, f5):
            return self.head(self.dec([f0, f1, f2, f3, f4, f5]))
    pd = prepare_fx(DecHead().eval(), qm, example_inputs=tuple(f_ex))
    with torch.inference_mode():
        for c in calib:
            s = m.depth_fusion(c); pd(*net.shared_encoder(s)); pe(s)
    qe, qd = convert_fx(pe), convert_fx(pd)
    return bench(lambda x: qd(*qe(m.depth_fusion(x))))


def pt2e():
    try:
        from torch.ao.quantization.quantize_pt2e import prepare_pt2e, convert_pt2e
        import torch.ao.quantization.quantizer.x86_inductor_quantizer as xiq
        src = "torch.ao"
    except Exception:
        from torchao.quantization.pt2e.quantize_pt2e import prepare_pt2e, convert_pt2e
        import torchao.quantization.pt2e.quantizer.x86_inductor_quantizer as xiq
        src = "torchao"

    class Wrap(nn.Module):
        def __init__(self, m):
            super().__init__(); self.m = m

        def forward(self, x):
            return self.m(x)["ink"]
    w = Wrap(copy.deepcopy(model)).eval()
    ep = torch.export.export(w, (calib[0],)).module()
    q = xiq.X86InductorQuantizer()
    q.set_global(xiq.get_default_x86_inductor_quantization_config())
    p = prepare_pt2e(ep, q)
    for c in calib:
        p(c)
    cm = convert_pt2e(p)
    with torch.no_grad():
        comp = torch.compile(cm)
        t0 = time.time(); comp(xs[0]); first = time.time() - t0
    out = dict(api=src, first_call_compile_s=first)
    with torch.no_grad():
        out.update(bench(comp))
    return out


for name in args.only.split(","):
    attempt(name, {"dyn": dyn, "fx": fx, "fx_parts": fx_parts, "pt2e": pt2e}[name])
res["peak_rss_mb"] = peak_rss_mb()
json.dump(res, open(args.out, "w"), indent=1)
