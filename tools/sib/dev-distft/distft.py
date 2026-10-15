# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV recipe DIST-FT (DECL-DEVLOOP-A1 item 2, recipe 3; logs/sib/devloop/proposals/first_recipes.md).

Full fine-tune of base ink_9um hybrid_3d2d seed42 step-075000 at 128 px on 9 um inputs, with the official 2.4 um
reference map (area-averaged onto the 9 um canvas by the pairs sessions) as a SOFT / distillation target.
Numbers only: nothing here writes, opens or describes an image.

This file is a thin layer on the trainer sibling's PINNED code (tools/sib/dev-distft/pinned/, byte-identical to
branch claude/gifted-bell-gavnl5-sib-trainer commit 8475920, sha256 checked at import against PINNED). The only
declared change is the TARGET:

  pinned (DECL-D2 rule)                          DIST-FT (soft)
  ink = ref9 >= 150, blank = ref9 <= 100,        target = ref9 / 255 (continuous), supervised wherever the pair
  100 < ref9 < 150 and invalid ignored           is valid (no threshold, no ignored band)

and the three places where the pinned pipeline assumes a binary target are generalised so that a {0, 1} target
gives bit-for-bit the pinned result (tested in tests/test_distft.py):
  1. label rotation: `ink & sup` -> `ink * sup` (identical on {0, 1});
  2. label scale: the uint8 target is divided by 255 immediately before the official augmentations (the official
     label transforms are permutations only - mirror, transpose, rot90 - checked on every smoke sample);
  3. loss input: official prepare_loss_inputs (flat mode) binarises `amax(inklabels, z) > 0`; the soft version is
     the same function without the `> 0` (identical on {0, 1}); nearest resize and the ignore mask are unchanged.
Everything else is the pinned trainer: official model, official loss (smoothed BCE + Dice, ignore channel,
unchanged label smoothing), AdamW, robust_mad normalisation, official augmentations, 17-of-21 z window with
jitter +-2, 24 x 15 deg rotations, sub-tiles, epoch-wise streams, resume every 250 steps (local only: no weights
or optimiser state are ever pushed to git), patch registry, checkpoint registry.

Controls (DECL-DEVLOOP-A1 item 2), identical to the recipe except for one factor, paired sampling:
  NULL: the soft targets (and their validity masks) of the role=train patches permuted by ONE derangement drawn
        with default_rng(20260925) regardless of the run seed (DECL-DEVLOOP-A1: "one fixed derangement of targets,
        seed 20260925");
  REV:  every role=train 21-slice input stack reversed in depth, targets unchanged.

Subcommands
  make-config   pinned make-config + the DIST-FT target block; prints the config sha256
  train         run / resume one arm (the pinned run_train with the DIST-FT trainer class)
  bench         throughput only (pinned run_bench with the DIST-FT trainer class)
  synth         write a SYNTHETIC pairs registry (tests / smoke only; never real data)"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PINNED_DIR = os.path.join(HERE, "pinned")
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
PINNED_COMMIT = "8475920fa1a8dd7a753c426be0ebd592851ad884"
PINNED = {  # trainer branch commit 8475920, logs/sib/trainer/report.json code_sha256
    "d2_train.py": "fdbe236cc2cf46664c3d0558e58c7594220a4ce105fde3b5453d634680496f24",
    "d2_data.py": "5b7a6a5df4f07cf75ef84b63899e531c040b0cb13d8b45b7c180ac2b10a7676b",
    "ckpt_shards.py": "ba6db9991e14000b9ba051244c6ae2fa59928b4c6094cc64316ca559cbf3b974",
    "contam_check.py": "0e30cabbc762979f5b197c0365815dc5915048626c6a01ffb571c643b9f1321e",
}
NULL_SEED = 20260925          # DECL-DEVLOOP-A1 item 2
RECIPE_SEED = 20260925        # ASK.md A3 (default): one seed per recipe; NULL and REV share it (paired sampling)
TARGET_SCHEMA = "hercules-distft-target/1"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def verify_pinned() -> dict:
    got = {f: _sha256_file(os.path.join(PINNED_DIR, f)) for f in PINNED}
    bad = {f: g for f, g in got.items() if g != PINNED[f]}
    if bad:
        raise SystemExit(f"pinned trainer code changed: {bad}")
    return got


verify_pinned()
sys.path.insert(0, PINNED_DIR)
import d2_data  # noqa: E402  (pinned)
import d2_train  # noqa: E402  (pinned)


# ------------------------------------------------------------------------------------------------ soft sources

def _soft_rule_check(src_pinned, soft, valid, name):
    """The pinned DECL-D2 labels must be exactly the threshold of the soft target on the same pixels: proves the
    soft arrays are aligned patch-for-patch and pixel-for-pixel with what the pinned loader delivers."""
    import numpy as np
    k, s = d2_data.labels_from_target(soft, valid)
    if not (np.array_equal(k, src_pinned.ink) and np.array_equal(s, src_pinned.sup)):
        raise ValueError(f"source {name}: soft target does not reproduce the pinned labels "
                         f"(ink diff {int(np.sum(k != src_pinned.ink))} px, sup diff {int(np.sum(s != src_pinned.sup))} px)")


def load_soft_source(spec: dict):
    """Pinned loader (all sha256 / schema / label-rule checks), then the continuous target and validity mask read
    from the same files in the same order. Returns a pinned Source whose `ink` is the uint8 0..255 soft target and
    whose `sup` is the pair-validity mask {0, 1}."""
    import glob
    import numpy as np
    src = d2_data.load_source(spec)
    kind = spec.get("kind", "pairs")
    if kind == "pairs":
        reg = json.load(open(spec["path"]))
        root = os.path.dirname(os.path.abspath(spec["path"]))
        soft, valid = [], []
        for sh in reg["shards"]:
            with np.load(os.path.join(root, sh["file"]), allow_pickle=False) as z:
                soft.append(z["target"].astype(np.uint8))
                valid.append(z["valid"].astype(np.uint8) if "valid" in z.files
                             else np.ones(z["target"].shape, np.uint8))
        soft, valid = np.concatenate(soft), np.concatenate(valid)
        valid_rule = "registry 'valid'"
    elif kind == "stagec":
        man = json.load(open(os.path.join(spec["path"], "shards.json")))
        keep = set(json.load(open(spec["allow_ids"]))) if spec.get("allow_ids") else None
        soft, valid = [], []
        for sh in man["shards"]:
            with np.load(os.path.join(spec["path"], sh["shard"]), allow_pickle=False) as z:
                ids = [str(x) for x in z["patch_id"]]
                sel = np.array([keep is None or i in keep for i in ids], bool)
                if sel.any():
                    soft.append(z["ref9"][sel].astype(np.uint8)); valid.append(z["valid"][sel].astype(np.uint8))
        soft, valid = np.concatenate(soft), np.concatenate(valid)
        valid_rule = "stage-C 'valid'"
    elif kind in ("tilegrid", "tilegrid3", "tilegrid4"):
        # pairs0139 stores no explicit validity mask: valid = label != 255 OR 100 < inkmap < 150 (the ignored band).
        # ASK.md A7: an invalid pixel whose rounded inkmap lies in 101..149 would be wrongly supervised; the pairs
        # session is asked to store `valid` explicitly. The count of such ambiguous pixels cannot be measured here.
        mos = dict(tilegrid=1, tilegrid3=3, tilegrid4=4)[kind]
        rows = []
        for f in sorted(glob.glob(os.path.join(spec["path"], "registry", "*.jsonl"))):
            rows += [json.loads(l) for l in open(f) if l.strip()]
        byid = {r["tile_id"]: r for r in rows if r.get("shard")}
        cache = {}

        def tile(tid):
            r = byid[tid]
            if r["shard"] not in cache:
                with np.load(os.path.join(spec["path"], "shards", r["shard"]), allow_pickle=False) as z:
                    cache[r["shard"]] = {k: z[k] for k in ("label", "inkmap", "tile_id")}
            z = cache[r["shard"]]
            i = int(r["shard_index"])
            assert str(z["tile_id"][i]) == tid
            lab, imap = z["label"][i], z["inkmap"][i]
            v = ((lab != 255) | ((imap > d2_data.BLANK_MAX) & (imap < d2_data.INK_MIN))).astype(np.uint8)
            return imap.astype(np.uint8), v
        soft, valid = [], []
        for pid in src.patch_id:
            parts = pid.split("+") if mos > 1 else [pid]
            ts = [tile(t) for t in parts]
            g = [ts[a * mos:(a + 1) * mos] for a in range(mos)]
            soft.append(np.concatenate([np.concatenate([c[0] for c in rr], axis=1) for rr in g], axis=0))
            valid.append(np.concatenate([np.concatenate([c[1] for c in rr], axis=1) for rr in g], axis=0))
        soft, valid = np.stack(soft), np.stack(valid)
        valid_rule = "label != 255 or 100 < inkmap < 150 (no explicit valid stored; ASK A7)"
    else:
        raise ValueError(f"DIST-FT has no soft target for source kind {kind!r}")
    if soft.shape != src.ink.shape:
        raise ValueError(f"source {src.name}: soft shape {soft.shape} != pinned {src.ink.shape}")
    _soft_rule_check(src, soft, valid, src.name)
    n_band = int(np.sum(valid.astype(bool) & (soft > d2_data.BLANK_MAX) & (soft < d2_data.INK_MIN)))
    src.meta["distft_target"] = dict(
        schema=TARGET_SCHEMA, kind="soft", value="ref9 / 255", supervised=valid_rule,
        pinned_rule_reproduced=True, n_supervised_px=int(valid.sum()),
        n_pinned_supervised_px=int(src.sup.sum()), n_band_px_now_supervised=n_band,
        soft_sha256=hashlib.sha256(soft.tobytes()).hexdigest(),
        valid_sha256=hashlib.sha256(valid.tobytes()).hexdigest())
    src.ink, src.sup = soft, valid
    return src


# ------------------------------------------------------------------------------------------------ soft loss input

def soft_prepare_loss_inputs(predictions, batch, *, mode: str, force_full_supervision: bool = False):
    """villa 41701aa vesuvius/ink_detection/training/train.py::prepare_loss_inputs, flat mode, with the single
    change `targets = amax(inklabels, z)` instead of `(amax(inklabels, z) > 0)`. Identical on {0, 1} labels."""
    import torch
    import torch.nn.functional as F
    if isinstance(predictions, (list, tuple)):
        prepared, targets, ignore = [], None, None
        for index, level in enumerate(predictions):
            p, t, i = soft_prepare_loss_inputs(level, batch, mode=mode, force_full_supervision=force_full_supervision)
            prepared.append(p)
            if index == 0:
                targets, ignore = t, i
        return type(predictions)(prepared), targets, ignore
    if mode != "flat":
        raise ValueError(f"DIST-FT soft loss input is defined for the base model's flat mode only, not {mode!r}")
    targets = torch.amax(batch["inklabels"], dim=2).to(dtype=batch["inklabels"].dtype)
    supervision = torch.amax(batch["supervision_mask"], dim=2)
    ignore_mask = torch.zeros_like(targets) if force_full_supervision else (supervision <= 0).to(dtype=targets.dtype)
    output_size = tuple(int(v) for v in predictions.shape[-2:])
    if tuple(int(v) for v in targets.shape[-2:]) != output_size:
        targets = F.interpolate(targets.float(), size=output_size, mode="nearest").to(dtype=batch["inklabels"].dtype)
        ignore_mask = F.interpolate(ignore_mask.float(), size=output_size, mode="nearest").to(dtype=targets.dtype)
    return predictions, targets, ignore_mask


# ------------------------------------------------------------------------------------------------ trainer

class DistFTTrainer(d2_train.Trainer):
    """Pinned Trainer with the DIST-FT soft target (see module docstring)."""

    def __init__(self, cfg, out, *, bench=False, sources=None):
        dft = cfg.get("distft")
        if not dft or dft.get("schema") != TARGET_SCHEMA:
            raise SystemExit("not a DIST-FT config (no distft block)")
        self.soft = dft["target"] == "soft"
        if sources is None:
            sources = [load_soft_source(s) if self.soft else d2_data.load_source(s) for s in cfg["sources"]]
        super().__init__(cfg, out, bench=bench, sources=sources)
        if self.soft:
            import torch
            official_aug = self.aug
            self.aug_label_checks = dict(samples=0, value_multiset_changed=0)

            def aug(**d):
                d["inklabels"] = d["inklabels"] / 255.0
                chk = self.aug_label_checks["samples"] < self.check_aug_samples
                before = torch.sort(d["inklabels"].flatten()).values if chk else None
                out = official_aug(**d)
                if chk:
                    self.aug_label_checks["samples"] += 1
                    after = torch.sort(out["inklabels"].flatten()).values
                    if before.shape != after.shape or not torch.equal(before, after):
                        self.aug_label_checks["value_multiset_changed"] += 1
                return out
            self.aug = aug
            self.prepare_loss_inputs = soft_prepare_loss_inputs
            self.checks["distft_target"] = [s.meta.get("distft_target") for s in self.sources]
            self.checks["distft_aug_label_value_multiset"] = self.aug_label_checks
        self.meta["distft"] = dict(dft, pinned_commit=PINNED_COMMIT, pinned_sha256=dict(PINNED),
                                   wrapper_sha256=_sha256_file(os.path.abspath(__file__)))

    check_aug_samples = 4000     # the first 4000 samples (125 steps at batch 32) are checked, then no overhead

    def _apply_null(self, train_idx, seed):
        # DECL-DEVLOOP-A1: one fixed derangement, seed 20260925, independent of the run seed
        return super()._apply_null(train_idx, int(self.cfg["distft"]["null_seed"]))

    def _rotate(self, img, ink, sup):
        """Pinned Trainer._rotate with `a & b` -> `a * b` (the soft target is uint8 0..255; identical on {0, 1})."""
        import math
        np, torch, T, R = self.np, self.torch, self.T, img.shape[-1]
        k = int(self.rot_gen.integers(0, 24))
        if k % 6 == 0:
            q = k // 6
            im = np.rot90(img, q, axes=(1, 2)); a = np.rot90(ink, q); b = np.rot90(sup, q)
            valid = np.ones((R, R), np.uint8)
            c0 = (R - T) // 2
            sl = (slice(c0, c0 + T), slice(c0, c0 + T))
            return (np.ascontiguousarray(im[:, sl[0], sl[1]]).astype(np.float32),
                    np.ascontiguousarray(a[sl]), np.ascontiguousarray(b[sl]) & valid[sl], k)
        th = math.radians(15.0 * k)
        c, s = math.cos(th), math.sin(th)
        ys, xs = torch.meshgrid(torch.arange(T, dtype=torch.float64) - (T - 1) / 2,
                                torch.arange(T, dtype=torch.float64) - (T - 1) / 2, indexing="ij")
        sx = c * xs - s * ys
        sy = s * xs + c * ys
        grid = torch.stack([(sx * 2 + 0) / R, (sy * 2 + 0) / R], -1).float()[None]
        src = torch.from_numpy(np.ascontiguousarray(img)).float()[None]
        im = torch.nn.functional.grid_sample(src, grid, mode="bilinear", padding_mode="border", align_corners=False)
        lab = torch.from_numpy(np.stack([ink, sup, np.ones_like(sup)]).astype(np.float32))[None]
        lb = torch.nn.functional.grid_sample(lab, grid, mode="nearest", padding_mode="zeros", align_corners=False)
        inside = ((sx.abs() <= (R - 1) / 2) & (sy.abs() <= (R - 1) / 2)).numpy()
        a = lb[0, 0].numpy().astype(np.uint8)
        b = (lb[0, 1].numpy().astype(np.uint8) & lb[0, 2].numpy().astype(np.uint8) & inside.astype(np.uint8))
        return im[0].numpy(), a * b, b, k


def use_distft_trainer():
    """The pinned run_train / run_bench construct `Trainer` by module-global name; point it at DIST-FT."""
    d2_train.Trainer = DistFTTrainer


# ------------------------------------------------------------------------------------------------ CLI

ARMS = {"DIST-FT": dict(null=False, rev=False), "DIST-FT-NULL": dict(null=True, rev=False),
        "DIST-FT-REV": dict(null=False, rev=True)}


def make_config(argv):
    ap = argparse.ArgumentParser(prog="distft.py make-config")
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--seed", type=int, default=RECIPE_SEED)
    ap.add_argument("--null-seed", type=int, default=NULL_SEED)
    ap.add_argument("--target", choices=("soft", "hard"), default="soft",
                    help="hard = the pinned DECL-D2 label rule (diagnostic / equivalence only, not the recipe)")
    ap.add_argument("--out", required=True)
    a, rest = ap.parse_known_args(argv)
    if a.null_seed != NULL_SEED:
        raise SystemExit(f"DECL-DEVLOOP-A1 fixes the NULL derangement seed at {NULL_SEED}")
    arm = ARMS[a.arm]
    # ASK.md defaults A1-A6: tile 128 with 24 x 15 deg rotations and sub-tiles (DECL-D2 P128 on the 384 px
    # patches), batch 32, AdamW 2e-5 constant, wd 3e-5, fp32, 4 threads, resume every 250 steps (local only)
    pinned_argv = ["make-config", "--arm", a.arm, "--seed", str(a.seed), "--tile", "128", "--rot24",
                   "--null" if arm["null"] else "--no-null", "--rev" if arm["rev"] else "--no-rev",
                   "--decl", "DECL-DEVLOOP-A1 recipe 3 (DIST-FT)"] + rest + ["--out", a.out]
    for flag in ("--remote-ref", "--precision"):
        if flag in rest:
            raise SystemExit(f"{flag} is not allowed for DIST-FT (no weights to git; fp32 only - ASK A5)")
    ns = _pinned_parser().parse_args(pinned_argv)
    cfg = d2_train.make_config(ns)
    cfg["distft"] = dict(schema=TARGET_SCHEMA, recipe="DIST-FT", target=a.target, null_seed=a.null_seed,
                         label_value="ref9 / 255" if a.target == "soft" else "DECL-D2 rule",
                         supervised="pair-valid pixels" if a.target == "soft" else "DECL-D2 rule",
                         loss="official (smoothed BCE + Dice, ignore channel), unchanged",
                         pinned_commit=PINNED_COMMIT)
    d2_train.validate_config(cfg)
    json.dump(cfg, open(a.out, "w"), indent=1, sort_keys=True)
    print(json.dumps(dict(config=os.path.abspath(a.out), sha256=d2_train.config_sha256(cfg))))
    return 0


def _pinned_parser():
    """The pinned make-config argument parser (extracted by running d2_train.main's parser construction)."""
    captured = {}
    orig = argparse.ArgumentParser.parse_args

    def grab(self, args=None, namespace=None):
        captured["p"] = self
        raise _Grab()
    argparse.ArgumentParser.parse_args = grab
    try:
        d2_train.main(["make-config"])
    except _Grab:
        pass
    finally:
        argparse.ArgumentParser.parse_args = orig
    return captured["p"]


class _Grab(Exception):
    pass


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__); return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "make-config":
        return make_config(rest)
    if cmd == "synth":
        ap = argparse.ArgumentParser(prog="distft.py synth")
        ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=64)
        ap.add_argument("--size", type=int, default=384); ap.add_argument("--seed", type=int, default=7)
        a = ap.parse_args(rest)
        print(d2_data.write_synthetic_registry(a.out, a.n, a.size, a.seed, source="synthetic", shard_n=32))
        return 0
    if cmd in ("train", "bench"):
        use_distft_trainer()
        return d2_train.main([cmd] + rest)
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in ("train", "bench"):
        try:
            i = sys.argv.index("--config")
            th = str(json.load(open(sys.argv[i + 1]))["threads"])
            os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = th
        except (ValueError, IndexError, OSError, KeyError):
            pass
    sys.exit(main())
