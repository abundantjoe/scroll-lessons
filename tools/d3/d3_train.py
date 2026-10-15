# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 (DECL-D3-A1 items 1-4) fine-tune of one arm from the base ink_9um checkpoint. Numbers only.

Official components (villa 41701aa, vesuvius/ink_detection): TrainingConfig/InkConfig, make_model, load_model_state,
create_loss (smoothed BCE 0.5 + 0.25 Dice, ignore channel), create_training_optimizer (AdamW via the vesuvius factory),
prepare_model_input, run_model_forward, prepare_loss_inputs, concatenate_deep_supervision_ignore, flat_z_window_bbox
(17-of-21 window, training jitter +-2), normalize_image (robust_mad p1/p99), build_augmentations('default').
This is train.py::_run_training's inner step run without Accelerate (fp32, CPU, 3 threads).
Recipe: AdamW lr 2e-5 constant, weight decay 3e-5, betas (0.9, 0.999), grad clip 1.0, batch 8, 2000 steps,
seed 20260925 (python, numpy, torch; data sampling streams from numpy SeedSequence(20260925)).
Pools (/work/d3/pool_fa, /work/d3/pool_replay): uint8 (N, 21, 128, 128) = render slices 5..25; stack index 2..18 =
slices 7..23 (C2-NT forward window) is the canonical window.
Arms: FA = 4 fold-A + 4 replay per batch; NULLA = FA with fold-A label tiles permuted by ONE fixed derangement
(numpy default_rng(20260925).permutation, redrawn until no fixed point; tile i gets tile perm[i]'s ink and supervision);
REVA = FA with every fold-A 21-slice input stack reversed in depth (labels unchanged); CTRL = 8 replay per batch.
Sampling: fold-A and replay index streams are epoch-wise permutations (without replacement within an epoch) from two
independent child seeds of SeedSequence(20260925); FA, NULLA and REVA therefore see the identical tile sequence.
Output (full run): <out>/model_final.pth = {'model': final weights, 'config': the base checkpoint's embedded config
(unchanged, so the official infer rebuilds the same model and normalisation), 'step', 'd3': run metadata}; no optimizer
state. <out>/train_log.jsonl (every 50 steps) and <out>/summary.json.
Restart safety (DECL-D3-A2 item 4): every --ckpt-every (250) steps <out>/resume_latest.pth holds weights, AdamW state,
all RNG states (python, numpy global, torch, both sampling generators) and the sampling streams; only the latest is
kept (write-then-replace, or delete-then-write when /work/d3 + /work/d3_timing would exceed --budget-bytes 3e9).
A re-run of the same command resumes from it and logs the resumption; a completed arm (model_final.pth +
summary.json) exits immediately; after completion only the final weights are kept (resume_latest.pth deleted)."""
import os, sys, json, time, argparse, random, hashlib, copy, datetime, resource
os.environ.setdefault("OMP_NUM_THREADS", "3")
os.environ.setdefault("MKL_NUM_THREADS", "3")
import numpy as np
import torch

ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True, choices=("CTRL", "FA", "NULLA", "REVA"))
ap.add_argument("--steps", type=int, default=2000)
ap.add_argument("--out", required=True)
ap.add_argument("--log-every", type=int, default=50)
ap.add_argument("--smoke", action="store_true", help="smoke test: extra checks, per-step log")
ap.add_argument("--ckpt-every", type=int, default=250, help="resumable checkpoint interval (DECL-D3-A2 item 4)")
ap.add_argument("--budget-bytes", type=float, default=3.0e9,
                help="disk cap for /work/d3 + /work/d3_timing; above it the old resumable checkpoint is deleted "
                     "before the new one is written (else write-then-replace)")
ap.add_argument("--die-after", type=int, default=0, help="TEST ONLY: hard-exit (code 99) after this many steps")
args = ap.parse_args()

RESUME = os.path.join(args.out, "resume_latest.pth")
FINAL = os.path.join(args.out, "model_final.pth")
SUMMARY = os.path.join(args.out, "summary.json")
if os.path.exists(FINAL) and os.path.exists(SUMMARY):
    if os.path.exists(RESUME):
        os.remove(RESUME)
    print(f"arm {args.arm}: already complete ({FINAL}); nothing to do", flush=True)
    sys.exit(0)

SEED = 20260925
CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
CK_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
POOL_FA, POOL_RP = "/work/d3/pool_fa", "/work/d3/pool_replay"
N_FA_PER_BATCH = {"CTRL": 0, "FA": 4, "NULLA": 4, "REVA": 4}[args.arm]
BATCH = 8
LR, WD = 2e-5, 3e-5
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"

torch.set_num_threads(3)
torch.set_num_interop_threads(1)
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
os.makedirs(args.out, exist_ok=True)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
from vesuvius.ink_detection.models.model import make_model
from vesuvius.ink_detection.models.checkpoint import load_checkpoint, load_model_state
from vesuvius.ink_detection.training.losses import create_loss
from vesuvius.ink_detection.training.optimizers import create_training_optimizer
from vesuvius.ink_detection.training.train import prepare_model_input, prepare_loss_inputs
from vesuvius.ink_detection.training.stitching import run_model_forward
from vesuvius.ink_detection.training.deep_supervision import concatenate_deep_supervision_ignore
from vesuvius.ink_detection.data.normalization import normalize_image
from vesuvius.ink_detection.data.dataset import flat_z_window_bbox
from vesuvius.ink_detection.data.augmentations import build_augmentations

t_start = time.time()
started_utc = utc()
ck_sha = sha256(CK)
assert ck_sha == CK_SHA, ck_sha
ck = load_checkpoint(CK)
base_config = copy.deepcopy(ck["config"])
mapping = copy.deepcopy(ck["config"])
mapping.update(optimizer="adamw", learning_rate=LR, weight_decay=WD, batch_size=BATCH, num_iterations=args.steps,
               seed=SEED, out_dir=args.out)
# the official config validator requires fixed_scroll_prior.seed == seed; that sampler is not used here (the D3
# pools and streams replace it), so it simply follows the arm seed
mapping["fixed_scroll_prior"] = dict(mapping["fixed_scroll_prior"], seed=SEED)
tc = TrainingConfig.from_mapping(resolve_training_mapping(mapping))
ink = tc.ink
model = make_model(ink)
load_model_state(model, ck["model"])
strict = str(model.load_state_dict(ck["model"], strict=True))
del ck
optimizer = create_training_optimizer(model, tc)            # AdamW(lr 2e-5, wd 3e-5, betas 0.9/0.999)
assert type(optimizer).__name__ == "AdamW" and optimizer.param_groups[0]["lr"] == LR
assert optimizer.param_groups[0]["weight_decay"] == WD
loss_fn = create_loss(ink)
aug = build_augmentations(ink.data.augmentation.preset, ink.data.patch_size,
                          rotation_axes=ink.data.augmentation.rotation_axes)
PZ = ink.data.patch_size[0]
assert PZ == 17 and tuple(ink.data.patch_size) == (17, 128, 128)


def load_pool(pd):
    man = json.load(open(f"{pd}/manifest.json"))
    for f, h in man["files_sha256"].items():
        assert sha256(f"{pd}/{f}") == h, (pd, f)
    return (np.load(f"{pd}/images.npy"), np.load(f"{pd}/inklabels.npy"), np.load(f"{pd}/supervision.npy"),
            sha256(f"{pd}/manifest.json"))


rp_img, rp_ink, rp_sup, rp_man = load_pool(POOL_RP)
meta = dict(arm=args.arm, replay_manifest_sha256=rp_man, n_replay=int(len(rp_img)))
checks = {}
if N_FA_PER_BATCH:
    fa_img, fa_ink, fa_sup, fa_man = load_pool(POOL_FA)
    meta.update(fa_manifest_sha256=fa_man, n_fold_a=int(len(fa_img)))
    if args.arm == "NULLA":
        drng = np.random.default_rng(SEED)
        attempts = 0
        while True:
            attempts += 1
            perm = drng.permutation(len(fa_img))
            if not np.any(perm == np.arange(len(fa_img))):
                break
        fa_ink, fa_sup = fa_ink[perm].copy(), fa_sup[perm].copy()
        meta.update(derangement=dict(rule="default_rng(20260925).permutation redrawn until no fixed point; tile i "
                                          "gets tile perm[i]'s labels", attempts=attempts,
                                     fixed_points=int(np.sum(perm == np.arange(len(perm)))),
                                     perm_sha256=hashlib.sha256(perm.astype(np.int64).tobytes()).hexdigest(),
                                     perm_head=perm[:10].tolist()))
        checks["nulla_fixed_points"] = int(np.sum(perm == np.arange(len(perm))))
        own_ink = np.load(f"{POOL_FA}/inklabels.npy")
        checks["nulla_tiles_whose_ink_label_differs_from_own"] = int(sum(
            1 for i in range(len(perm)) if not np.array_equal(fa_ink[i], own_ink[i])))
        del own_ink
    if args.arm == "REVA":
        orig = fa_img
        fa_img = np.ascontiguousarray(fa_img[:, ::-1])
        checks["reva_stack_is_exact_depth_reverse"] = bool(all(np.array_equal(fa_img[i], orig[i][::-1])
                                                               for i in range(len(orig))))
        del orig

ss = np.random.SeedSequence(SEED)
rng_fa, rng_rp = [np.random.default_rng(s) for s in ss.spawn(2)]


class Stream:
    """Epoch-wise permutation stream of pool indices (no replacement within an epoch)."""
    def __init__(self, n, rng):
        self.n, self.rng, self.buf, self.epochs = n, rng, [], 0

    def take(self, k):
        out = []
        while len(out) < k:
            if not self.buf:
                self.buf = list(self.rng.permutation(self.n)); self.epochs += 1
            out.append(int(self.buf.pop(0)))
        return out


s_fa = Stream(len(fa_img), rng_fa) if N_FA_PER_BATCH else None
s_rp = Stream(len(rp_img), rng_rp)


def window(stack21):
    """official flat z window on the 21-slice stack (base bbox depth 21 -> canonical 2..18, jitter +-2)."""
    bbox, off = flat_z_window_bbox((0, 0, 0, 21, 128, 128), config=ink.data, do_augmentations=True, is_validation=False)
    return stack21[bbox[0]:bbox[3]], off


def sample(img21, ink2, sup2):
    w, off = window(img21)
    im = normalize_image(np.ascontiguousarray(w), ink.data.normalization)
    lab = np.broadcast_to(ink2, (PZ, 128, 128)).astype(np.float32)
    sm = np.broadcast_to(sup2, (PZ, 128, 128)).astype(np.float32)
    d = {"image": torch.from_numpy(np.ascontiguousarray(im)).float().unsqueeze(0),
         "inklabels": torch.from_numpy(lab.copy()).unsqueeze(0),
         "supervision_mask": torch.from_numpy(sm.copy()).unsqueeze(0)}
    d = aug(**d)
    return {k: d[k] for k in ("image", "inklabels", "supervision_mask")}, off


def make_batch():
    items, srcs = [], []
    if N_FA_PER_BATCH:
        for i in s_fa.take(N_FA_PER_BATCH):
            items.append(sample(fa_img[i], fa_ink[i], fa_sup[i])[0]); srcs.append(("fa", i))
    for i in s_rp.take(BATCH - N_FA_PER_BATCH):
        items.append(sample(rp_img[i], rp_ink[i], rp_sup[i])[0]); srcs.append(("rp", i))
    return {k: torch.stack([it[k] for it in items]) for k in items[0]}, srcs


if args.smoke and args.arm == "REVA":
    # exact depth reverse of the model input window before augmentation: REVA(o) == flip(FA(-o))
    forig = np.load(f"{POOL_FA}/images.npy", mmap_mode="r")
    ok_raw, ok_norm = True, True
    for i in range(0, len(fa_img), max(1, len(fa_img) // 16)):
        for o in (-2, -1, 0, 1, 2):
            fa_w = np.asarray(forig[i][2 + o:19 + o]); rv_w = fa_img[i][2 - o:19 - o]
            ok_raw &= bool(np.array_equal(rv_w, fa_w[::-1]))
            a = normalize_image(np.ascontiguousarray(fa_w), ink.data.normalization)
            b = normalize_image(np.ascontiguousarray(rv_w), ink.data.normalization)
            ok_norm &= bool(np.array_equal(b, a[::-1]))
    checks["reva_window_exact_reverse_raw"] = ok_raw
    checks["reva_window_exact_reverse_normalized"] = ok_norm

def du_bytes(*paths):
    import subprocess
    return sum(int(subprocess.run(["du", "-sb", p], capture_output=True, text=True).stdout.split()[0]) for p in paths)


def rng_state():
    return dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(),
                fa=rng_fa.bit_generator.state, rp=rng_rp.bit_generator.state)


def save_resume(done):
    """resumable checkpoint: weights + optimizer + all RNG states + sampling streams; only the latest is kept."""
    est = os.path.getsize(RESUME) if os.path.exists(RESUME) else 4.2e8
    used = du_bytes("/work/d3", "/work/d3_timing")
    mode = "write-then-replace"
    if os.path.exists(RESUME) and used + est > args.budget_bytes:
        os.remove(RESUME); mode = "delete-then-write"
    ev = dict(event="checkpoint", step=done, mode=mode, used_before_bytes=used, utc=utc())
    ckpt_events.append(dict(ev))               # recorded inside the checkpoint itself (bytes/seconds: log only)
    state = dict(arm=args.arm, steps_total=args.steps, step=done, model=model.state_dict(),
                 optimizer=optimizer.state_dict(), rng=rng_state(),
                 streams=dict(fa=(None if s_fa is None else (list(s_fa.buf), s_fa.epochs)),
                              rp=(list(s_rp.buf), s_rp.epochs)),
                 losses=losses, walls=walls, nfin=nfin, resumptions=resumptions, ckpt_events=ckpt_events)
    t0 = time.time()
    torch.save(state, RESUME + ".tmp")
    os.replace(RESUME + ".tmp", RESUME)
    ev.update(bytes=os.path.getsize(RESUME), seconds=round(time.time() - t0, 2))
    logf.write(json.dumps(ev) + "\n"); logf.flush()
    print(json.dumps(ev), flush=True)


model.train()
log_path = os.path.join(args.out, "train_log.jsonl")
losses, walls, nfin = [], [], 0
resumptions, ckpt_events = [], []
start_step = 0
if os.path.exists(RESUME + ".tmp"):
    os.remove(RESUME + ".tmp")                 # partial write from an interrupted save
if os.path.exists(RESUME):
    st = torch.load(RESUME, map_location="cpu", weights_only=False)
    assert st["arm"] == args.arm and st["steps_total"] == args.steps, (st["arm"], st["steps_total"])
    model.load_state_dict(st["model"], strict=True)
    optimizer.load_state_dict(st["optimizer"])
    random.setstate(st["rng"]["python"]); np.random.set_state(st["rng"]["numpy"]); torch.set_rng_state(st["rng"]["torch"])
    rng_fa.bit_generator.state = st["rng"]["fa"]; rng_rp.bit_generator.state = st["rng"]["rp"]
    if s_fa is not None:
        s_fa.buf, s_fa.epochs = list(st["streams"]["fa"][0]), st["streams"]["fa"][1]
    s_rp.buf, s_rp.epochs = list(st["streams"]["rp"][0]), st["streams"]["rp"][1]
    losses, walls, nfin = list(st["losses"]), list(st["walls"]), st["nfin"]
    ckpt_events = list(st["ckpt_events"])
    start_step = int(st["step"])
    resumptions = list(st["resumptions"]) + [dict(event="resume", utc=utc(), from_step=start_step,
                                                   checkpoint_sha256=sha256(RESUME))]
    del st
logf = open(log_path, "a" if resumptions else "w")
if resumptions:
    logf.write(json.dumps(resumptions[-1]) + "\n"); logf.flush()
    print(json.dumps(resumptions[-1]), flush=True)
t_loop = time.time()
for step in range(start_step, args.steps):
    t0 = time.perf_counter()
    batch, srcs = make_batch()
    x = prepare_model_input(batch, tc)
    preds = run_model_forward(model, x, tc.model_crop_size, stitched=tc.use_stitched_forward,
                              use_gradient_checkpointing=tc.stitched_gradient_checkpointing)
    lp, targets, ignore = prepare_loss_inputs(preds, batch, mode=ink.data.mode,
                                             force_full_supervision=tc.force_full_supervision)
    twi = concatenate_deep_supervision_ignore(targets, ignore, lp)
    loss = loss_fn(lp.float(), twi.float())
    if not torch.isfinite(loss):
        raise RuntimeError(f"non-finite loss at step {step}")
    nfin += 1
    loss.backward()
    gn = float(torch.nn.utils.clip_grad_norm_(model.parameters(), tc.grad_clip))
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    walls.append(time.perf_counter() - t0)
    losses.append(float(loss.item()))
    if args.smoke or (step + 1) % args.log_every == 0 or step == 0:
        rec = dict(step=step + 1, loss=losses[-1], loss_mean_window=float(np.mean(losses[-args.log_every:])),
                   grad_norm_preclip=gn, lr=optimizer.param_groups[0]["lr"], s_per_step_window=float(np.mean(walls[-args.log_every:])),
                   elapsed_s=round(time.time() - t_loop, 1), fold_a_epochs=(s_fa.epochs if s_fa else 0),
                   replay_epochs=s_rp.epochs, supervised_frac=float((ignore <= 0).float().mean()),
                   n_fold_a_in_batch=sum(1 for s in srcs if s[0] == "fa"))
        if N_FA_PER_BATCH:
            with torch.no_grad():
                k = N_FA_PER_BATCH
                rec["loss_fold_a_part"] = float(loss_fn(lp[:k].detach().float(), twi[:k].float()).item())
                rec["loss_replay_part"] = float(loss_fn(lp[k:].detach().float(), twi[k:].float()).item())
        rec["run_index"] = len(resumptions)
        logf.write(json.dumps(rec) + "\n"); logf.flush()
        print(json.dumps(rec), flush=True)
    if args.ckpt_every > 0 and (step + 1) % args.ckpt_every == 0 and step + 1 < args.steps:
        save_resume(step + 1)
    if args.die_after and step + 1 == args.die_after:
        logf.flush()
        print(f"TEST: simulated crash after step {step + 1}", flush=True)
        os._exit(99)
logf.close()
loop_s = time.time() - t_loop
summary = dict(provenance=PROV, arm=args.arm, smoke=bool(args.smoke), started_utc=started_utc, finished_utc=utc(),
               steps=args.steps, finite_loss_steps=nfin, loss_first=losses[0], loss_last=losses[-1],
               loss_mean_last50=float(np.mean(losses[-50:])), median_s_per_step=float(np.median(walls)),
               loop_s=round(loop_s, 1), peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               base_checkpoint=dict(path=CK, sha256=ck_sha), strict_load=strict,
               recipe=dict(optimizer="AdamW", lr=LR, weight_decay=WD, betas=[0.9, 0.999], schedule="constant",
                           grad_clip=tc.grad_clip, batch=BATCH, fold_a_per_batch=N_FA_PER_BATCH,
                           replay_per_batch=BATCH - N_FA_PER_BATCH, precision="fp32", seed=SEED,
                           z_window="stack 2..18 (render 7..23) +-2 official jitter", augmentation="official default",
                           threads=dict(intra=torch.get_num_threads(), interop=torch.get_num_interop_threads())),
               sampling=dict(fold_a_epochs=(s_fa.epochs if s_fa else 0), replay_epochs=s_rp.epochs),
               resumptions=resumptions, checkpoint_events=ckpt_events, ckpt_every=args.ckpt_every,
               loop_s_note="loop_s covers the last (resumed) invocation only" if resumptions else "",
               meta=meta, checks=checks, train_log=log_path, train_log_sha256=sha256(log_path),
               script=dict(path=os.path.abspath(__file__), sha256=sha256(os.path.abspath(__file__))))
out_ckpt = os.path.join(args.out, "model_final.pth")
tmp = out_ckpt + ".tmp"
torch.save({"model": model.state_dict(), "config": base_config, "step": args.steps,
            "d3": {k: summary[k] for k in ("arm", "steps", "recipe", "meta", "base_checkpoint", "script")}}, tmp)
os.replace(tmp, out_ckpt)
summary["model_final"] = dict(path=out_ckpt, sha256=sha256(out_ckpt), bytes=os.path.getsize(out_ckpt))
json.dump(summary, open(SUMMARY + ".tmp", "w"), indent=1)
os.replace(SUMMARY + ".tmp", SUMMARY)
if os.path.exists(RESUME):                     # keep only final weights once the arm is complete
    os.remove(RESUME)
print("SUMMARY " + json.dumps({k: v for k, v in summary.items() if k not in ("meta",)}), flush=True)
