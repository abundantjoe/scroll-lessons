# Provenance: Project HERCULES | owner the owner | [id removed]
"""Item 5: frozen-encoder cached-feature path of the official base model, plus a 2-D letter-context block. Random
inputs only; no scroll data.

Split: "encoder" = model.depth_fusion (3-D stem) + model.network.shared_encoder (2-D encoder), 30.22 M of 34.55 M
params; "decoder" = model.network.shared_decoder + task_heads['ink'] (4.32 M). The cache holds the six encoder skips
per tile (32x128^2, 64x64^2, 128x32^2, 256x16^2, 320x8^2, 320x4^2 = 1,008,640 values).

A. Equivalence (random N(0,1) tiles, eval mode):
   A1 fp32: full model(x)['ink'] vs decoder(cache), the cache written to disk (.pt, native dtype) and reloaded;
       same batching (batch 4) and re-batched (encoded at batch 4, decoded at batch 8 and batch 1).
   A2 bf16 autocast: cached bf16 path vs full bf16 model (same batching and re-batched), and vs full fp32.
   A3 storage in bf16 of fp32 features (half the bytes), decoded in fp32, vs full fp32.
   Reported: max |diff| of logits and of the official uint8 map (clip(sigmoid, 0, 1) * 255, truncated).
B. Throughput (training, batch 8, D3 recipe: official loss, clip 1.0, AdamW lr 2e-5 wd 3e-5), fp32 and bf16:
   B1 full model step (reference); B2 decoder-only step from cached features; B3 decoder + LetterContext step.
LetterContext (new, prototype): for a 3 x 3 block of adjacent 128 px tiles (384 px of context) it stitches the cached
level-4 (320 x 8 x 8) and level-5 (320 x 4 x 4) skips of the nine tiles into 320 x 24 x 24 and 320 x 12 x 12 mosaics,
applies at each level two 3x3 conv blocks (dilation 1 and 2; InstanceNorm, LeakyReLU as the base model) and, at
level 5, one multi-head self-attention layer over the 144 mosaic cells (full 384 px receptive field), then a zero-
initialised 1x1 projection; the centre-tile crop is added to the centre tile's skips, which then go through the
(trainable) base decoder. Zero init makes the block an exact identity at step 0 (checked: max |diff| = 0)."""
import os, sys, argparse, json, time, tempfile
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
from torch import nn
torch.set_num_threads(args.threads)
from common import load, rand_batch, stats, env_info, utc, peak_rss_mb, TRAIN_BATCH
from vesuvius.ink_detection.training.train import prepare_loss_inputs
from vesuvius.ink_detection.training.deep_supervision import concatenate_deep_supervision_ignore

model, ink, tc, loss_fn, cfg = load()
net = model.network
head = net.task_heads["ink"]
gen = torch.Generator().manual_seed(20260925)
res = dict(utc=utc(), threads=args.threads, env=env_info(), equivalence={}, throughput={})


def encode(x):
    return net.shared_encoder(model.depth_fusion(x))


def decode(f):
    return head(net.shared_decoder(list(f)))


def u8(logits):
    p = logits.float().sigmoid().clamp_(0, 1).mul_(255)
    return p.to(torch.uint8)  # truncation, as the official encoder (astype uint8 after * 255)


def cmp(a, b):
    d = (a.float() - b.float()).abs()
    ua, ub = u8(a), u8(b)
    du = (ua.int() - ub.int()).abs()
    return dict(logit_max_abs=float(d.max()), logit_mean_abs=float(d.mean()), u8_max_abs=int(du.max()),
                u8_frac_identical=float((du == 0).float().mean()), u8_frac_within_2=float((du <= 2).float().mean()))


def ac(dt):
    return torch.autocast("cpu", dtype=torch.bfloat16) if dt == "bf16" else torch.autocast("cpu", enabled=False)


# ---------------- A. equivalence ----------------
model.eval()
X = [rand_batch(4, gen) for _ in range(4)]  # 16 random tiles
tmp = tempfile.mkdtemp(dir="/work/amx")
with torch.inference_mode():
    full = {dt: [] for dt in ("fp32", "bf16")}
    for dt in ("fp32", "bf16"):
        with ac(dt):
            for i, x in enumerate(X):
                full[dt].append(model(x)["ink"])
                torch.save([v.clone() for v in encode(x)], f"{tmp}/{dt}_{i}.pt")
    cache_bytes = {dt: sum(os.path.getsize(f"{tmp}/{dt}_{i}.pt") for i in range(len(X))) / (4 * len(X)) for dt in ("fp32", "bf16")}
    for dt in ("fp32", "bf16"):
        feats = [torch.load(f"{tmp}/{dt}_{i}.pt") for i in range(len(X))]
        with ac(dt):
            same = [decode(f) for f in feats]
            cat = [torch.cat([feats[i][k] for i in range(len(X))]) for k in range(6)]
            reb8 = torch.cat([decode([c[j:j + 8] for c in cat]) for j in range(0, 16, 8)])
            reb1 = torch.cat([decode([c[j:j + 1] for c in cat]) for j in range(16)])
        F = torch.cat(full[dt])
        res["equivalence"][f"A{1 if dt == 'fp32' else 2}_{dt}_cached_vs_full_{dt}"] = dict(
            same_batching=cmp(torch.cat(same), F), rebatched_8=cmp(reb8, F), rebatched_1=cmp(reb1, F))
    F32 = torch.cat(full["fp32"])
    res["equivalence"]["A2_bf16_full_vs_fp32_full"] = cmp(torch.cat(full["bf16"]), F32)
    feats16 = [[v.to(torch.bfloat16).float() for v in torch.load(f"{tmp}/fp32_{i}.pt")] for i in range(len(X))]
    res["equivalence"]["A3_fp32_decode_of_bf16_stored_fp32_features_vs_fp32_full"] = cmp(torch.cat([decode(f) for f in feats16]), F32)
    res["cache_bytes_per_tile_on_disk"] = cache_bytes
    res["cache_values_per_tile"] = int(sum(v.numel() for v in feats[0]) // 4)
    res["input_values_per_tile"] = 17 * 128 * 128
for f_ in os.listdir(tmp):
    os.remove(os.path.join(tmp, f_))
os.rmdir(tmp)


# ---------------- LetterContext ----------------
class ConvBlock(nn.Module):
    def __init__(self, c, dil):
        super().__init__()
        self.conv = nn.Conv2d(c, c, 3, padding=dil, dilation=dil)
        self.norm = nn.InstanceNorm2d(c, affine=True)
        self.act = nn.LeakyReLU(0.01, inplace=True)

    def forward(self, x):
        return x + self.act(self.norm(self.conv(x)))


class LetterContext(nn.Module):
    """3 x 3 tiles of cached level-4/5 skips -> residual update of the centre tile's level-4/5 skips."""

    def __init__(self, c4=320, c5=320, heads=8):
        super().__init__()
        self.l4 = nn.Sequential(ConvBlock(c4, 1), ConvBlock(c4, 2))
        self.l5 = nn.Sequential(ConvBlock(c5, 1), ConvBlock(c5, 2))
        self.pos5 = nn.Parameter(torch.zeros(1, 144, c5))
        self.attn = nn.MultiheadAttention(c5, heads, batch_first=True)
        self.ln = nn.LayerNorm(c5)
        self.out4 = nn.Conv2d(c4, c4, 1)
        self.out5 = nn.Conv2d(c5, c5, 1)
        for m in (self.out4, self.out5):
            nn.init.zeros_(m.weight); nn.init.zeros_(m.bias)

    @staticmethod
    def mosaic(t):  # (B, 9, C, h, w) row-major 3x3 -> (B, C, 3h, 3w)
        B, _, C, h, w = t.shape
        return t.view(B, 3, 3, C, h, w).permute(0, 3, 1, 4, 2, 5).reshape(B, C, 3 * h, 3 * w)

    def forward(self, n4, n5):
        m4 = self.l4(self.mosaic(n4))
        m5 = self.l5(self.mosaic(n5))
        B, C, H, W = m5.shape
        tok = m5.flatten(2).transpose(1, 2) + self.pos5
        q = self.ln(tok)
        tok = tok + self.attn(q, q, q, need_weights=False)[0]
        m5 = tok.transpose(1, 2).reshape(B, C, H, W)
        h4, h5 = n4.shape[-1], n5.shape[-1]
        return (self.out4(m4)[..., h4:2 * h4, h4:2 * h4], self.out5(m5)[..., h5:2 * h5, h5:2 * h5])


ctx = LetterContext()
res["letter_context"] = dict(params=sum(p.numel() for p in ctx.parameters()), context_px=384, levels=[4, 5])


def decode_ctx(centre, n4, n5):
    d4, d5 = ctx(n4, n5)
    f = list(centre)
    f[4] = f[4] + d4.to(f[4].dtype)
    f[5] = f[5] + d5.to(f[5].dtype)
    return decode(f)


# identity at init (fp32): decoder with context block == decoder without it
with torch.inference_mode():
    fe = encode(X[0])
    nb = [encode(rand_batch(4, gen)) for _ in range(9)]
    n4 = torch.stack([nb[k][4] for k in range(9)], 1)
    n5 = torch.stack([nb[k][5] for k in range(9)], 1)
    res["letter_context"]["identity_at_init_fp32"] = cmp(decode_ctx(fe, n4, n5), decode(fe))
    with torch.autocast("cpu", dtype=torch.bfloat16):
        fe16 = encode(X[0]); a = decode_ctx(fe16, n4, n5); b = decode(fe16)
    res["letter_context"]["identity_at_init_bf16"] = cmp(a, b)

# ---------------- B. throughput ----------------
model.train(); ctx.train()
dec_params = list(net.shared_decoder.parameters()) + list(head.parameters())
B = TRAIN_BATCH


def labels_like(n):
    b = rand_batch(n, gen, with_labels=True)
    return b


def run(name, dt, make_step):
    step = make_step()
    t = []
    for i in range(args.warmup + args.iters):
        t0 = time.perf_counter(); step(i); dt_ = time.perf_counter() - t0
        if i >= args.warmup:
            t.append(dt_)
    s = stats(t)
    s["tiles_per_s"] = B / s["median_s"]
    s["h_per_2000_steps"] = 2000 * s["median_s"] / 3600
    res["throughput"].setdefault(name, {})[dt] = s


def loss_on(y, b):
    lp, targets, ignore = prepare_loss_inputs(y, b, mode=ink.data.mode)
    return loss_fn(lp.float(), concatenate_deep_supervision_ignore(targets, ignore, lp).float())


for dt in ("fp32", "bf16"):
    def mk_full():
        opt = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=3e-5)
        bs = [labels_like(B) for _ in range(2)]

        def step(i):
            b = bs[i % 2]
            with ac(dt):
                y = model(b["image"])["ink"]
            loss_on(y, b).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); opt.zero_grad(set_to_none=True)
        return step

    def cached(n):  # cached features in the dtype the encoder produced them in (fp32, or bf16 under autocast)
        with torch.no_grad(), ac(dt):
            return [v.detach() for v in encode(rand_batch(n, gen))]

    def mk_dec():
        opt = torch.optim.AdamW(dec_params, lr=2e-5, weight_decay=3e-5)
        bs = [(cached(B), labels_like(B)) for _ in range(2)]

        def step(i):
            f, b = bs[i % 2]
            with ac(dt):
                y = decode(f)
            loss_on(y, b).backward()
            torch.nn.utils.clip_grad_norm_(dec_params, 1.0); opt.step(); opt.zero_grad(set_to_none=True)
        return step

    def mk_ctx():
        ps = dec_params + list(ctx.parameters())
        opt = torch.optim.AdamW(ps, lr=2e-5, weight_decay=3e-5)
        bs = []
        for _ in range(2):
            c = cached(B)
            nb = [cached(B) for _ in range(9)]
            bs.append((c, torch.stack([nb[k][4] for k in range(9)], 1), torch.stack([nb[k][5] for k in range(9)], 1), labels_like(B)))

        def step(i):
            c, n4, n5, b = bs[i % 2]
            with ac(dt):
                y = decode_ctx(c, n4, n5)
            loss_on(y, b).backward()
            torch.nn.utils.clip_grad_norm_(ps, 1.0); opt.step(); opt.zero_grad(set_to_none=True)
        return step

    run("B1_full_model", dt, mk_full)
    run("B2_decoder_only_cached", dt, mk_dec)
    run("B3_decoder_plus_letter_context_cached", dt, mk_ctx)

# one-off encoder cost to build the cache (inference, batch 4) and cache size
model.eval()
for dt in ("fp32", "bf16"):
    xs = [rand_batch(4, gen) for _ in range(2)]
    t = []
    with torch.inference_mode(), ac(dt):
        for i in range(args.warmup + args.iters):
            t0 = time.perf_counter(); encode(xs[i % 2]); d = time.perf_counter() - t0
            if i >= args.warmup:
                t.append(d)
    s = stats(t); s["per_tile_s"] = s["median_s"] / 4
    res["throughput"].setdefault("encoder_cache_build_infer_b4", {})[dt] = s
for dt in ("fp32", "bf16"):
    f = res["throughput"]["B1_full_model"][dt]["median_s"]
    for k in ("B2_decoder_only_cached", "B3_decoder_plus_letter_context_cached"):
        res["throughput"][k][dt]["speedup_vs_full_same_dtype"] = f / res["throughput"][k][dt]["median_s"]
    res["throughput"]["B1_full_model"][dt]["speedup_vs_full_fp32"] = res["throughput"]["B1_full_model"]["fp32"]["median_s"] / f
res["peak_rss_mb"] = peak_rss_mb()
json.dump(res, open(args.out, "w"), indent=1)
print(json.dumps(dict(eq={k: (v if "logit_max_abs" in v else {kk: vv["logit_max_abs"] for kk, vv in v.items()}) for k, v in res["equivalence"].items()},
                      ctx={k: v for k, v in res["letter_context"].items()},
                      thr={k: {d: round(v[d]["median_s"], 4) for d in v} for k, v in res["throughput"].items()}), default=str))
