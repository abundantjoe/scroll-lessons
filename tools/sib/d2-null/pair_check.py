# Provenance: Project HERCULES | owner the owner | [id removed]
"""d2-null pairing and derangement check (numbers and hashes only; no image is written or opened).

Builds the pinned trainer's Trainer (tools/sib/d2-null/trainer/d2_train.py, unchanged) from one config and records,
per step, sha256 of the batch image tensor, the label tensors and the (source, patch, z offset, rotation) draws, plus
sha256 of the torch / python / numpy RNG states before and after the optimizer step. The first --train-steps steps
run the real train_step (forward, backward, AdamW); the rest draw batches only. Drawing batches only is faithful to
training iff train_step consumes no RNG beyond make_batch, which is measured here (rng_consumed_by_model_step).

For a NULL config it also re-derives the derangement independently (default_rng(seed).permutation redrawn until no
fixed point, over the concatenated role=train patches), and checks against a freshly loaded copy of the sources that
patch i carries exactly patch perm[i]'s ink and supervision, that no patch keeps its own index, how many patches
still carry label arrays equal to their own, and that images are untouched.

Usage: pair_check.py --config CFG.json --out OUT.json [--steps 10] [--train-steps 2] [--trainer-dir DIR]
"""
import argparse
import hashlib
import json
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# --trainer-dir DIR selects the trainer copy (default: the pinned copy in ./trainer)
_td = sys.argv[sys.argv.index("--trainer-dir") + 1] if "--trainer-dir" in sys.argv else os.path.join(HERE, "trainer")
sys.path.insert(0, os.path.abspath(_td))


def h(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--train-steps", type=int, default=2)
    ap.add_argument("--trainer-dir", default=None)
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(cfg["threads"])
    import d2_train
    import d2_data
    import numpy as np
    cfg = d2_train.validate_config(cfg)
    wd = a.out + ".work"
    os.makedirs(wd, exist_ok=True)
    tr = d2_train.Trainer(cfg, wd)
    torch = tr.torch

    def rng_hash():
        return h(pickle.dumps((tr.random.getstate(), tr.np.random.get_state()[1].tobytes(),
                               torch.get_rng_state().numpy().tobytes(),
                               [g.bit_generator.state for g in tr.gens], tr.rot_gen.bit_generator.state)))

    def torch_rng_hash():
        return h(torch.get_rng_state().numpy().tobytes())

    rec = dict(provenance=d2_train.PROV, config=os.path.abspath(a.config), config_sha256=tr.csha, arm=cfg["arm"],
               seed=cfg["seed"], steps=[], checks=tr.checks, meta=tr.meta, data="SYNTHETIC")
    orig_make = tr.make_batch
    cap = {}

    def make_batch_rec():
        batch, srcs = orig_make()
        cap["img"] = h(batch["image"].contiguous().numpy().tobytes())
        cap["ink"] = h(batch["inklabels"].contiguous().numpy().tobytes())
        cap["sup"] = h(batch["supervision_mask"].contiguous().numpy().tobytes())
        cap["srcs"] = srcs
        cap["torch_after_batch"] = torch_rng_hash()
        cap["all_after_batch"] = rng_hash()
        return batch, srcs

    tr.make_batch = make_batch_rec
    for step in range(a.steps):
        if step < a.train_steps:
            loss, gn, _, supf = tr.train_step(step)
            kind = "train_step"
        else:
            tr.make_batch()
            loss = gn = supf = None
            kind = "batch_only"
        rec["steps"].append(dict(step=step + 1, kind=kind, image_sha256=cap["img"], ink_sha256=cap["ink"],
                                 sup_sha256=cap["sup"], draws_sha256=h(json.dumps(cap["srcs"]).encode()),
                                 sample_digest=tr.sample_digest, loss=loss, grad_norm_preclip=gn,
                                 supervised_frac=supf, torch_rng_after_batch=cap["torch_after_batch"],
                                 torch_rng_after_step=torch_rng_hash(),
                                 all_rng_after_batch=cap["all_after_batch"], all_rng_after_step=rng_hash()))
        print(json.dumps(rec["steps"][-1]), flush=True)
    ts = [s for s in rec["steps"] if s["kind"] == "train_step"]
    rec["rng_consumed_by_model_step"] = any(s["all_rng_after_batch"] != s["all_rng_after_step"] for s in ts)

    if cfg["null"]:
        fresh = [d2_data.load_source(s) for s in cfg["sources"]]
        tidx = [k for k, s in enumerate(fresh) if s.role == "train"]
        n = int(sum(len(fresh[k]) for k in tidx))
        drng = np.random.default_rng(int(cfg["seed"]))
        attempts = 0
        while True:
            attempts += 1
            perm = drng.permutation(n)
            if not np.any(perm == np.arange(n)):
                break
        f_ink = np.concatenate([fresh[k].ink for k in tidx])
        f_sup = np.concatenate([fresh[k].sup for k in tidx])
        f_img = np.concatenate([fresh[k].images for k in tidx])
        t_ink = np.concatenate([tr.sources[k].ink for k in tidx])
        t_sup = np.concatenate([tr.sources[k].sup for k in tidx])
        t_img = np.concatenate([tr.sources[k].images for k in tidx])
        own_equal = int(sum(np.array_equal(t_ink[i], f_ink[i]) and np.array_equal(t_sup[i], f_sup[i])
                            for i in range(n)))
        cyc = []
        seen = np.zeros(n, bool)
        for i in range(n):
            if not seen[i]:
                L, j = 0, i
                while not seen[j]:
                    seen[j] = True; j = int(perm[j]); L += 1
                cyc.append(L)
        rec["derangement_independent"] = dict(
            n_train_patches=n, attempts=attempts,
            perm_sha256=h(perm.astype(np.int64).tobytes()),
            matches_trainer_perm_sha256=h(perm.astype(np.int64).tobytes()) == tr.meta["derangement"]["perm_sha256"],
            fixed_points=int(np.sum(perm == np.arange(n))),
            is_derangement=bool(np.all(perm != np.arange(n))),
            is_permutation=bool(np.array_equal(np.sort(perm), np.arange(n))),
            labels_equal_fresh_perm=bool(np.array_equal(t_ink, f_ink[perm]) and np.array_equal(t_sup, f_sup[perm])),
            patches_whose_labels_equal_their_own=own_equal,
            images_untouched=bool(np.array_equal(t_img, f_img)),
            cycle_lengths_min=int(min(cyc)), n_cycles=len(cyc),
            pool_ink_frac_before=float(f_ink.mean()), pool_ink_frac_after=float(t_ink.mean()),
            pool_sup_frac_before=float(f_sup.mean()), pool_sup_frac_after=float(t_sup.mean()))
    json.dump(rec, open(a.out, "w"), indent=1)
    print("PAIRCHECK " + json.dumps({k: v for k, v in rec.items() if k not in ("steps", "meta")}), flush=True)


if __name__ == "__main__":
    main()
