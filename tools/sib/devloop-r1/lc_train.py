# Provenance: Project HERCULES | owner the owner | [id removed]
"""LC384 trainer on cached frozen-encoder features (task devloop-r1). Numbers only; fp32 (bf16 is not permitted for
this recipe class: DECL-AMX-1 covers only batch 8 / lr 2e-5 / 2000-step D3-class fine-tunes).

Arms (identical except for one factor; same seed, same tile/batch sequence):
  RECIPE : forward-order cache (lc_cache.py --order forward), true labels.
  NULL   : forward-order cache; tile i is trained on the labels (ink AND ignore mask) of tile perm[i], one fixed
           derangement of the training tiles (numpy default_rng(20260925).permutation, redrawn until no fixed point).
  REV    : reverse-order cache (every input stack reversed in depth before the frozen encoder), true labels.
Loss: the official objective (vesuvius create_loss from the base checkpoint config: BCE with label smoothing 0.5 +
0.25 Dice, ignore channel) through the official prepare_loss_inputs / concatenate_deep_supervision_ignore; labels
1 = ink, 0 = blank, 255 = ignored.
Optimizer: AdamW, weight decay 3e-5; lr --lr-new (default 1e-4) for the new modules (context, light head) and
--lr-base (default 2e-5, the D3 fine-tune rate) for the fine-tuned base decoder + head ('basedec'); constant; grad clip
1.0; batch 8; epoch-wise permutation sampling from SeedSequence(20260925). No augmentation (input-space augmentation
cannot act on cached features; recorded as a limitation).
Hold-out: a seeded 5 % of cache tiles, stratified by nothing, never trained on, scored every --val-every steps (loss
only; monitoring, never a selection criterion: the FINAL checkpoint is the one evaluated).
Resumable: <out>/resume.pt every --ckpt-every steps (weights, optimizer, RNG, sampler state); final <out>/lc_final.pt
(trainable parameters only, lc_model.save_ckpt format) + summary.json + train_log.jsonl."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lc_model as LM  # noqa: E402
from lc_cache import Cache, sha  # noqa: E402

SEED = 20260925


def derangement(n, seed=SEED):
    rng = np.random.default_rng(seed)
    while True:
        p = rng.permutation(n)
        if n < 2 or not np.any(p == np.arange(n)):
            return p


class Stream:
    """Epoch-wise permutations without replacement."""

    def __init__(self, items, seed):
        self.items = np.asarray(items)
        self.rng = np.random.default_rng(seed)
        self.order, self.pos, self.epochs = self.rng.permutation(self.items), 0, 0

    def take(self, k):
        out = []
        while len(out) < k:
            if self.pos >= len(self.order):
                self.order, self.pos = self.rng.permutation(self.items), 0
                self.epochs += 1
            out.append(int(self.order[self.pos])); self.pos += 1
        return out

    def state(self):
        return dict(order=self.order.tolist(), pos=self.pos, epochs=self.epochs, rng=self.rng.bit_generator.state)

    def load(self, s):
        self.order, self.pos, self.epochs = np.array(s["order"]), s["pos"], s["epochs"]
        self.rng.bit_generator.state = s["rng"]


def split(n, frac=0.05, seed=SEED):
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(2)[1])
    idx = rng.permutation(n)
    k = max(1, int(round(frac * n))) if n >= 20 else 0
    return np.sort(idx[k:]), np.sort(idx[:k])


def make_targets(lab_u8):
    """uint8 (B,128,128) 1/0/255 -> official batch keys (B,1,1,H,W)."""
    lab = torch.from_numpy(np.ascontiguousarray(lab_u8)).long()
    ink = (lab == 1).float()[:, None, None]
    sup = (lab != 255).float()[:, None, None]
    return dict(inklabels=ink, supervision_mask=sup)


def loss_on(logits, batch, ink, loss_fn):
    from vesuvius.ink_detection.training.train import prepare_loss_inputs
    from vesuvius.ink_detection.training.deep_supervision import concatenate_deep_supervision_ignore
    lp, targets, ignore = prepare_loss_inputs(logits, batch, mode=ink.data.mode)
    return loss_fn(lp.float(), concatenate_deep_supervision_ignore(targets, ignore, lp).float())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="forward cache (RECIPE, NULL) or reverse cache (REV)")
    ap.add_argument("--arm", required=True, choices=("RECIPE", "NULL", "REV"))
    ap.add_argument("--variant", default="basedec", choices=("basedec", "light"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr-new", type=float, default=1e-4)
    ap.add_argument("--lr-base", type=float, default=2e-5)
    ap.add_argument("--wd", type=float, default=3e-5)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--val-every", type=int, default=250)
    ap.add_argument("--ckpt-every", type=int, default=250)
    ap.add_argument("--die-after", type=int, default=0, help="TEST ONLY: stop (return 99) right after this step")
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    torch.manual_seed(SEED)
    os.makedirs(a.out, exist_ok=True)
    final, summ_p, resume_p = f"{a.out}/lc_final.pt", f"{a.out}/summary.json", f"{a.out}/resume.pt"
    if os.path.exists(final) and os.path.exists(summ_p):
        print("complete; nothing to do"); return 0
    man = json.load(open(f"{a.cache}/manifest.json"))
    want = "reverse" if a.arm == "REV" else "forward"
    assert man["order"] == want, f"arm {a.arm} needs a {want}-order cache, got {man['order']}"
    C = Cache(a.cache)
    tr, va = split(C.n)
    perm = derangement(C.n) if a.arm == "NULL" else np.arange(C.n)  # label source per tile
    model, cfg, ink = LM.build(a.variant)
    from vesuvius.ink_detection.training.losses import create_loss
    loss_fn = create_loss(ink)
    new = [p for n, p in model.named_parameters() if p.requires_grad and n.startswith(("context.", "light."))]
    base = [p for n, p in model.named_parameters() if p.requires_grad and n.startswith(("decoder.", "head."))]
    groups = [dict(params=new, lr=a.lr_new)] + ([dict(params=base, lr=a.lr_base)] if base else [])
    opt = torch.optim.AdamW(groups, weight_decay=a.wd, betas=(0.9, 0.999))
    params = new + base
    stream = Stream(tr, np.random.SeedSequence(SEED).spawn(2)[0])
    start, log_rows = 0, []
    if os.path.exists(resume_p):
        st = torch.load(resume_p, map_location="cpu", weights_only=False)
        model.load_state_dict(st["model"], strict=False); opt.load_state_dict(st["opt"])
        stream.load(st["stream"]); torch.set_rng_state(st["torch_rng"]); start = st["step"]
        log_rows.append(dict(event="resume", from_step=start))
    logf = open(f"{a.out}/train_log.jsonl", "a" if start else "w")
    for r in log_rows:
        logf.write(json.dumps(r) + "\n")

    def run_batch(idx, train=True):
        cen, n4, n5, pres = C.batch(idx)
        b = make_targets(C.labels[perm[np.asarray(idx)]])
        logits = model(cen, n4, n5, pres)
        return loss_on(logits, b, ink, loss_fn), pres

    losses, walls = [], []
    model.train()
    t_loop = time.time()
    for step in range(start, a.steps):
        t0 = time.perf_counter()
        idx = stream.take(a.batch)
        loss, pres = run_batch(idx)
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        gn = float(torch.nn.utils.clip_grad_norm_(params, 1.0))
        opt.step(); opt.zero_grad(set_to_none=True)
        walls.append(time.perf_counter() - t0); losses.append(float(loss.item()))
        s1 = step + 1
        if s1 % a.log_every == 0 or step == 0:
            rec = dict(step=s1, loss=losses[-1], loss_mean_window=float(np.mean(losses[-a.log_every:])), grad_norm_preclip=gn,
                       s_per_step_window=float(np.mean(walls[-a.log_every:])), epochs=stream.epochs,
                       neighbours_present_frac=float(pres.float().mean()))
            if s1 % a.val_every == 0 and len(va):
                model.eval()
                with torch.no_grad():
                    vl = [float(run_batch(va[i:i + a.batch], False)[0]) for i in range(0, len(va), a.batch)]
                model.train()
                rec["val_loss"] = float(np.mean(vl))
            logf.write(json.dumps(rec) + "\n"); logf.flush(); print(json.dumps(rec), flush=True)
        if s1 % a.ckpt_every == 0 and s1 < a.steps:
            torch.save(dict(model={k: v for k, v in model.state_dict().items() if k in model.trainable_state()}, opt=opt.state_dict(),
                            stream=stream.state(), torch_rng=torch.get_rng_state(), step=s1), resume_p + ".tmp")
            os.replace(resume_p + ".tmp", resume_p)
        if a.die_after and s1 == a.die_after:
            logf.close()
            return 99
    meta = dict(arm=a.arm, variant=a.variant, steps=a.steps, batch=a.batch, lr_new=a.lr_new, lr_base=a.lr_base, wd=a.wd,
                seed=SEED, feature_dtype=man["dtype"], cache_manifest_sha256=sha(f"{a.cache}/manifest.json"),
                n_train=int(len(tr)), n_val=int(len(va)), null_fixed_points=int(np.sum(perm == np.arange(C.n))) if a.arm == "NULL" else None,
                code_sha256={f: sha(os.path.join(HERE, f)) for f in ("lc_train.py", "lc_model.py", "lc_cache.py")})
    LM.save_ckpt(final, model, meta)
    summ = dict(meta, final_sha256=sha(final), final_bytes=os.path.getsize(final),
                loss_mean_last200=float(np.mean(losses[-200:])) if losses else None,
                median_s_per_step=float(np.median(walls)) if walls else None, loop_s=round(time.time() - t_loop, 1),
                threads=a.threads)
    json.dump(summ, open(summ_p, "w"), indent=1)
    if os.path.exists(resume_p):
        os.remove(resume_p)
    print(json.dumps(summ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
