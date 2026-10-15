# Provenance: Project HERCULES | owner the owner | [id removed]
"""D2 trainer (DECL-D2, DECL-KILL; generalises tools/d3/d3_train.py). Numbers only: no image is written or opened.

Every arm starts from the official base ink_9um hybrid_3d2d seed42 step-075000 (sha256 e635558a...9cab) and uses the
official villa 41701aa components exactly as tools/d3/d3_train.py does: TrainingConfig/InkConfig, make_model,
load_model_state, create_loss (smoothed BCE 0.5 + 0.25 Dice, ignore channel), create_training_optimizer (AdamW),
prepare_model_input, run_model_forward, prepare_loss_inputs, concatenate_deep_supervision_ignore,
flat_z_window_bbox (17-of-21, jitter +-2), normalize_image (robust_mad), build_augmentations('default').
With tile 128, no rotation, no z offset, fp32, micro-batch = batch and the D3 source layout, one training step is
bit-for-bit the D3 step (tested: tests/sib_trainer_d3equiv_test.py runs both scripts on the same synthetic pools).

Subcommands
  make-config  build a config JSON from flags (arm presets P128 / P384 / NULL / REV per DECL-D2) and print its sha256
  train        run (or resume) one arm-seed from a config JSON
  bench        throughput only (synthetic or real sources; writes no model; bf16 allowed without the gate here)

Per-sample pipeline (order fixed, all RNG draws in the same order as D3 when the new options are off):
  pick patch (epoch-wise permutation stream per source) -> [REV: stack reversed in depth, 21 slices]
  -> official z window (python `random`) shifted by z_centre_offset -> crop R x R about the patch centre
     (R = T, or ceil(T*sqrt2)+2 when rot24 is on and the stored patch is large enough)
  -> [rot24: angle k*15 deg, k from a dedicated numpy generator; bilinear image, nearest labels; pixels whose source
     falls outside the stored patch are ignored] -> centre crop T -> normalize_image -> official augmentations.
NULL: label arrays of the role=train patches permuted by ONE derangement (default_rng(seed).permutation redrawn
until no fixed point), fixed for the whole run. REV: every role=train 21-slice input stack reversed in depth.
Micro-batching: the batch is drawn whole, then split; loss/n_micro per micro-batch; one clip + optimizer step.
Resume state (every ckpt_every steps): weights, AdamW state, python/numpy/torch RNG, every sampling generator, the
rotation generator, stream buffers, losses and draw counts; kept locally (latest only) and, if configured, pushed as
< 90 MB shards to a dedicated git ref (ckpt_shards.py). Resume prefers the local copy, else the remote ref."""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import resource
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BASE_CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
BASE_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
CONFIG_SCHEMA = "hercules-d2-trainer-config/1"
TILES = (128, 384, 512)

# DECL-D2 arms: P128 (base recipe, batch 32, 12k steps, 24 x 15 deg rotations); P384; NULL (P384, shuffled labels);
# REV (P384, depth-flipped). The optimiser recipe defaults to the section 4.D2 archive fine-tune recipe that D3 used
# (AdamW lr 2e-5 constant, wd 3e-5, clip 1.0); the orchestrator pins it in the D2 amendment.
ARM_PRESETS = {
    "P128": dict(tile=128, rot24=True, null=False, rev=False),
    "P384": dict(tile=384, rot24=True, null=False, rev=False),
    "NULL": dict(tile=384, rot24=True, null=True, rev=False),
    "REV": dict(tile=384, rot24=True, null=False, rev=True),
}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def config_sha256(cfg: dict) -> str:
    return hashlib.sha256(canonical_json(cfg)).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def rot_crop_size(tile: int) -> int:
    r = int(math.ceil(tile * math.sqrt(2.0))) + 2
    return r + (r - tile) % 2          # same parity as tile so the centre crop is symmetric


# ------------------------------------------------------------------------------------------------ config

def validate_config(cfg: dict) -> dict:
    if cfg.get("schema") != CONFIG_SCHEMA:
        raise ValueError(f"config schema {cfg.get('schema')!r} != {CONFIG_SCHEMA!r}")
    if cfg["tile"] not in TILES:
        raise ValueError(f"tile must be one of {TILES}")
    if cfg["batch"] < 1 or cfg["micro_batch"] < 1 or cfg["batch"] % cfg["micro_batch"]:
        raise ValueError("micro_batch must divide batch")
    if cfg["forward"] not in ("full", "stitched"):
        raise ValueError("forward must be full or stitched")
    if cfg["precision"] not in ("fp32", "bf16"):
        raise ValueError("precision must be fp32 or bf16")
    z = cfg["z"]
    if z["window"] != 17 or z["stack_depth"] != 21:
        raise ValueError("the base model takes a 17-slice window of a 21-slice stack")
    if abs(z["centre_offset"]) + z["jitter"] > (z["stack_depth"] - z["window"]) // 2:
        raise ValueError("|centre_offset| + jitter must be <= 2 (window must stay inside the 21-slice stack)")
    if cfg["base_checkpoint"]["sha256"] != BASE_SHA:
        raise ValueError("every D2 arm starts from base ink_9um seed42 step-075000 only")
    opt = cfg["optimizer"]
    if opt["name"] != "adamw" or opt["schedule"] != "constant":
        raise ValueError("only AdamW with a constant lr is implemented")
    quotas = [s.get("per_batch") for s in cfg["sources"]]
    if any(q is not None for q in quotas):
        if any(q is None for q in quotas) or sum(quotas) != cfg["batch"]:
            raise ValueError("per-source per_batch quotas must all be set and sum to batch")
    if not any(s.get("role", "train") == "train" for s in cfg["sources"]) and (cfg["null"] or cfg["rev"]):
        raise ValueError("NULL/REV need at least one role=train source")
    return cfg


def make_config(a) -> dict:
    preset = dict(ARM_PRESETS.get(a.arm, dict(rot24=False, null=False, rev=False)))
    for k in ("tile", "rot24", "null", "rev"):
        v = getattr(a, k)
        if v is not None:
            preset[k] = v
    if a.arm not in ARM_PRESETS and "tile" not in preset:
        raise SystemExit("custom arm: --tile required")
    sources = []
    for s in a.source:
        # name=kind:path[:role[:per_batch[:stream]]]
        name, rest = s.split("=", 1)
        parts = rest.split(":")
        spec = dict(name=name, kind=parts[0], path=os.path.abspath(parts[1]),
                    role=parts[2] if len(parts) > 2 and parts[2] else "train")
        if len(parts) > 3 and parts[3]:
            spec["per_batch"] = int(parts[3])
        if len(parts) > 4 and parts[4]:
            spec["stream"] = int(parts[4])
        for dr in a.data_root:
            n2, pth = dr.split("=", 1)
            if n2 == name:
                spec["data_root"] = os.path.abspath(pth)
        for al in a.allow_ids:
            n2, pth = al.split("=", 1)
            if n2 == name:
                spec["allow_ids"] = os.path.abspath(pth)
                spec["allow_ids_sha256"] = sha256_file(pth)
        if a.hash_sources:
            import d2_data
            spec["sha256"] = d2_data.load_source(spec).registry_sha256
        sources.append(spec)
    gate = None
    if a.amx_gate:
        gate = dict(path=os.path.abspath(a.amx_gate), sha256=sha256_file(a.amx_gate))
    micro = a.micro_batch or a.batch
    cfg = dict(schema=CONFIG_SCHEMA, arm=a.arm, seed=a.seed, tile=preset["tile"], rot24=bool(preset["rot24"]),
               null=bool(preset["null"]), rev=bool(preset["rev"]), subtile=bool(a.subtile), batch=a.batch, micro_batch=micro, steps=a.steps,
               forward=a.forward, precision=a.precision, amx_gate=gate, threads=a.threads,
               z=dict(stack_depth=21, window=17, jitter=a.z_jitter, centre_offset=a.z_centre_offset),
               optimizer=dict(name="adamw", lr=a.lr, weight_decay=a.weight_decay, betas=[0.9, 0.999],
                              schedule="constant", grad_clip=1.0),
               label_rule=dict(ink_min=150, blank_max=100),
               base_checkpoint=dict(path=BASE_CK, sha256=BASE_SHA,
                                    name="ink_9um hybrid_3d2d seed42 step-075000 (HF scrollprize/ink_9um rev 7109667e)"),
               lineage=dict(parent="base", parent_sha256=BASE_SHA, decl=a.decl),
               sources=sources, ckpt=dict(every=a.ckpt_every, remote_ref=a.remote_ref, shard_bytes=90_000_000),
               log_every=a.log_every, deterministic=True)
    return validate_config(cfg)


# ------------------------------------------------------------------------------------------------ trainer

class Stream:
    """Epoch-wise permutation stream of pool indices (no replacement within an epoch) - as tools/d3/d3_train.py."""

    def __init__(self, n, rng):
        self.n, self.rng, self.buf, self.epochs = n, rng, [], 0

    def take(self, k):
        out = []
        while len(out) < k:
            if not self.buf:
                self.buf = list(self.rng.permutation(self.n)); self.epochs += 1
            out.append(int(self.buf.pop(0)))
        return out


class Trainer:
    def __init__(self, cfg: dict, out: str, *, bench: bool = False, sources=None):
        self.cfg, self.out, self.bench = cfg, out, bench
        self.csha = config_sha256(cfg)
        if cfg["precision"] == "bf16" and not bench:
            g = cfg.get("amx_gate")
            if not g:
                raise SystemExit("bf16 training refused: no AMX gate record in the config (orchestrator gate first)")
            if sha256_file(g["path"]) != g["sha256"]:
                raise SystemExit("bf16 training refused: AMX gate record changed since the config was made")
            rec = json.load(open(g["path"]))
            if rec.get("pass") is not True:
                raise SystemExit("bf16 training refused: the AMX gate record does not say pass: true")
        import numpy as np
        import random
        import torch
        self.np, self.random, self.torch = np, random, torch
        th = int(cfg["threads"])
        torch.set_num_threads(th)
        torch.set_num_interop_threads(1)
        if cfg.get("deterministic", True):
            torch.use_deterministic_algorithms(True)
        seed = int(cfg["seed"])
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
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
        self.prepare_model_input, self.prepare_loss_inputs = prepare_model_input, prepare_loss_inputs
        self.run_model_forward, self.cdsi = run_model_forward, concatenate_deep_supervision_ignore
        self.normalize_image, self.flat_z_window_bbox = normalize_image, flat_z_window_bbox

        ck_path = cfg["base_checkpoint"]["path"]
        self.base_sha = sha256_file(ck_path)
        if self.base_sha != BASE_SHA:
            raise SystemExit(f"base checkpoint sha256 {self.base_sha} != {BASE_SHA}")
        ck = load_checkpoint(ck_path)
        self.base_config = copy.deepcopy(ck["config"])
        mapping = copy.deepcopy(ck["config"])
        o = cfg["optimizer"]
        mapping.update(optimizer="adamw", learning_rate=o["lr"], weight_decay=o["weight_decay"],
                       batch_size=cfg["batch"], num_iterations=cfg["steps"], seed=seed, out_dir=out)
        mapping["fixed_scroll_prior"] = dict(mapping["fixed_scroll_prior"], seed=seed)
        jit = dict(mapping["flat_z_window_jitter"])
        jit["max_offset"] = int(cfg["z"]["jitter"])
        mapping["flat_z_window_jitter"] = jit
        tc = TrainingConfig.from_mapping(resolve_training_mapping(mapping))
        self.tc, self.ink = tc, tc.ink
        self.model = make_model(self.ink)
        load_model_state(self.model, ck["model"])
        self.strict = str(self.model.load_state_dict(ck["model"], strict=True))
        del ck
        self.optimizer = create_training_optimizer(self.model, tc)
        assert type(self.optimizer).__name__ == "AdamW" and self.optimizer.param_groups[0]["lr"] == o["lr"]
        assert self.optimizer.param_groups[0]["weight_decay"] == o["weight_decay"]
        self.loss_fn = create_loss(self.ink)
        T = int(cfg["tile"])
        self.T = T
        self.aug = build_augmentations(self.ink.data.augmentation.preset, (17, T, T),
                                       rotation_axes=self.ink.data.augmentation.rotation_axes)
        assert tuple(self.ink.data.patch_size) == (17, 128, 128)
        self.model_crop = tuple(tc.model_crop_size)

        # ---------------- data
        import d2_data
        self.d2_data = d2_data
        self.sources = sources if sources is not None else [d2_data.load_source(s) for s in cfg["sources"]]
        for s, spec in zip(self.sources, cfg["sources"]):
            if s.size < T:
                raise SystemExit(f"source {s.name}: stored patch {s.size} px < tile {T}")
            if spec.get("sha256") and spec["sha256"] != s.registry_sha256:
                raise SystemExit(f"source {s.name}: registry sha256 mismatch")
        self.checks, self.meta = {}, dict(sources=[dict(name=s.name, role=s.role, n=len(s), size=s.size,
                                                        registry_sha256=s.registry_sha256, kind=s.meta.get("kind"))
                                                   for s in self.sources])
        train_idx = [k for k, s in enumerate(self.sources) if s.role == "train"]
        if cfg["null"]:
            self._apply_null(train_idx, seed)
        if cfg["rev"]:
            for k in train_idx:
                s = self.sources[k]
                orig = s.images
                s.images = np.ascontiguousarray(orig[:, ::-1])
                self.checks[f"rev_{s.name}_exact_depth_reverse"] = bool(all(
                    np.array_equal(s.images[i], orig[i][::-1]) for i in range(len(orig))))
                del orig
        ss = np.random.SeedSequence(seed)
        nstreams = max([spec.get("stream", k) for k, spec in enumerate(cfg["sources"])] + [len(cfg["sources"]) - 1]) + 1
        kids = ss.spawn(nstreams + 1)
        self.gens = [np.random.default_rng(kids[spec.get("stream", k)]) for k, spec in enumerate(cfg["sources"])]
        self.rot_gen = np.random.default_rng(kids[nstreams])
        # subtile: each stored S px patch contributes a centred (S // T)^2 grid of T px sub-tiles to the stream, so
        # arms with different tiles see the same labelled pixels; else one centred T crop per patch
        self.subtile = bool(cfg.get("subtile", False))
        self.nsub = [((s.size // T) ** 2 if self.subtile else 1) for s in self.sources]
        self.streams = [Stream(len(s) * m, g) for s, g, m in zip(self.sources, self.gens, self.nsub)]
        self.quotas = [spec.get("per_batch") for spec in cfg["sources"]]
        if all(q is None for q in self.quotas):
            # pooled: one stream over the concatenation of all sources (DECL-D2 pooled training)
            self.pool_offsets = np.cumsum([0] + [len(s) * m for s, m in zip(self.sources, self.nsub)])
            self.pooled = Stream(int(self.pool_offsets[-1]), self.gens[0])
        else:
            self.pooled = None
        self.draws = {s.name: np.zeros(len(s), np.int64) for s in self.sources}
        self.R = T
        if cfg["rot24"]:
            # subtile: context comes from neighbouring pixels, padding beyond the stored patch is ignored
            self.R = rot_crop_size(T) if self.subtile else min(rot_crop_size(T), min(s.size for s in self.sources))
        self.checks["rot_margin_full"] = (bool(min(s.size for s in self.sources) >= rot_crop_size(T))
                                          if cfg["rot24"] and not self.subtile else
                                          ("per-subtile (edge sub-tiles padded, padding ignored)" if cfg["rot24"]
                                           else None))
        self.checks["subtiles_per_patch"] = {s.name: m for s, m in zip(self.sources, self.nsub)}
        self.losses, self.walls, self.nfin = [], [], 0
        self.sample_digest = ""
        self.resumptions, self.ckpt_events = [], []
        self.start_step = 0

    # ------------------------------------------------------------------ NULL
    def _apply_null(self, train_idx, seed):
        np = self.np
        sizes = [len(self.sources[k]) for k in train_idx]
        n = int(sum(sizes))
        drng = np.random.default_rng(seed)
        attempts = 0
        while True:
            attempts += 1
            perm = drng.permutation(n)
            if not np.any(perm == np.arange(n)):
                break
        ink = np.concatenate([self.sources[k].ink for k in train_idx])
        sup = np.concatenate([self.sources[k].sup for k in train_idx])
        own = ink.copy()
        ink, sup = ink[perm].copy(), sup[perm].copy()
        off = 0
        for k, m in zip(train_idx, sizes):
            self.sources[k].ink, self.sources[k].sup = ink[off:off + m], sup[off:off + m]
            off += m
        self.meta["derangement"] = dict(rule="default_rng(seed).permutation over the concatenated role=train patches, "
                                             "redrawn until no fixed point; patch i gets patch perm[i]'s labels",
                                        attempts=attempts, fixed_points=int(np.sum(perm == np.arange(n))),
                                        perm_sha256=hashlib.sha256(perm.astype(np.int64).tobytes()).hexdigest(),
                                        perm_head=perm[:10].tolist())
        self.checks["null_fixed_points"] = int(np.sum(perm == np.arange(n)))
        self.checks["null_patches_whose_ink_differs_from_own"] = int(sum(
            1 for i in range(n) if not np.array_equal(ink[i], own[i])))

    # ------------------------------------------------------------------ sampling
    def _window(self, stack21):
        z = self.cfg["z"]
        bbox, off = self.flat_z_window_bbox((0, 0, 0, 21, self.R, self.R), config=self.ink.data,
                                            do_augmentations=True, is_validation=False)
        z0, z1 = bbox[0] + z["centre_offset"], bbox[3] + z["centre_offset"]
        assert 0 <= z0 and z1 <= 21 and z1 - z0 == 17, (z0, z1)
        return stack21[z0:z1], off

    def _rotate(self, img, ink, sup):
        """img (17, R, R) uint8; ink/sup (R, R) -> float32 (17, T, T), uint8 (T, T) x2, plus k."""
        np, torch, T, R = self.np, self.torch, self.T, img.shape[-1]
        k = int(self.rot_gen.integers(0, 24))
        if k % 6 == 0:                               # multiples of 90 deg: exact
            q = k // 6
            im = np.rot90(img, q, axes=(1, 2)); a = np.rot90(ink, q); b = np.rot90(sup, q)
            valid = np.ones((R, R), np.uint8)
            c0 = (R - T) // 2
            sl = (slice(c0, c0 + T), slice(c0, c0 + T))
            return (np.ascontiguousarray(im[:, sl[0], sl[1]]).astype(np.float32),
                    np.ascontiguousarray(a[sl]), np.ascontiguousarray(b[sl]) & valid[sl], k)
        th = math.radians(15.0 * k)
        # output grid (T x T, centred) -> source coordinates in the R x R patch (pixel centres, align_corners=False)
        c, s = math.cos(th), math.sin(th)
        ys, xs = torch.meshgrid(torch.arange(T, dtype=torch.float64) - (T - 1) / 2,
                                torch.arange(T, dtype=torch.float64) - (T - 1) / 2, indexing="ij")
        sx = c * xs - s * ys
        sy = s * xs + c * ys
        grid = torch.stack([(sx * 2 + 0) / R, (sy * 2 + 0) / R], -1).float()[None]     # normalised, R px span
        src = torch.from_numpy(np.ascontiguousarray(img)).float()[None]                   # (1, 17, R, R)
        im = torch.nn.functional.grid_sample(src, grid, mode="bilinear", padding_mode="border", align_corners=False)
        lab = torch.from_numpy(np.stack([ink, sup, np.ones_like(sup)]).astype(np.float32))[None]
        lb = torch.nn.functional.grid_sample(lab, grid, mode="nearest", padding_mode="zeros", align_corners=False)
        inside = ((sx.abs() <= (R - 1) / 2) & (sy.abs() <= (R - 1) / 2)).numpy()
        a = lb[0, 0].numpy().astype(np.uint8)
        b = (lb[0, 1].numpy().astype(np.uint8) & lb[0, 2].numpy().astype(np.uint8) & inside.astype(np.uint8))
        return im[0].numpy(), a & b, b, k

    def _crop(self, src, i, w, y0, x0):
        """R x R crop at (y0, x0) of window w (17, S, S) and of the labels; outside the stored patch the image is
        edge-padded and the supervision is 0 (ignored)."""
        np, R, S = self.np, self.R, w.shape[-1]
        if 0 <= y0 and 0 <= x0 and y0 + R <= S and x0 + R <= S:
            return (w[:, y0:y0 + R, x0:x0 + R], src.ink[i][y0:y0 + R, x0:x0 + R],
                    src.sup[i][y0:y0 + R, x0:x0 + R])
        pads = [(max(0, -y0), max(0, y0 + R - S)), (max(0, -x0), max(0, x0 + R - S))]
        ys, xs = slice(max(0, y0), min(S, y0 + R)), slice(max(0, x0), min(S, x0 + R))
        im = np.pad(w[:, ys, xs], [(0, 0)] + pads, mode="edge")
        ink = np.pad(src.ink[i][ys, xs], pads, mode="constant")
        sup = np.pad(src.sup[i][ys, xs], pads, mode="constant")
        return im, ink, sup

    def sample(self, src, j):
        np, T = self.np, self.T
        S, R = src.size, self.R
        if self.subtile:
            g = S // T
            i, q = divmod(j, g * g)
            gy, gx = divmod(q, g)
            m = (S - g * T) // 2
            y0, x0 = m + gy * T - (R - T) // 2, m + gx * T - (R - T) // 2
        else:
            i = j
            y0 = x0 = (S - R) // 2
        img21 = src.images[i]
        w, off = self._window(img21)
        w, ink2, sup2 = self._crop(src, i, w, y0, x0)
        k = None
        if self.cfg["rot24"]:
            w, ink2, sup2, k = self._rotate(w, ink2, sup2)
        elif R != T:
            raise AssertionError("R != T without rotation")
        im = self.normalize_image(np.ascontiguousarray(w), self.ink.data.normalization)
        lab = np.broadcast_to(ink2, (17, T, T)).astype(np.float32)
        sm = np.broadcast_to(sup2, (17, T, T)).astype(np.float32)
        torch = self.torch
        d = {"image": torch.from_numpy(np.ascontiguousarray(im)).float().unsqueeze(0),
             "inklabels": torch.from_numpy(lab.copy()).unsqueeze(0),
             "supervision_mask": torch.from_numpy(sm.copy()).unsqueeze(0)}
        d = self.aug(**d)
        return {kk: d[kk] for kk in ("image", "inklabels", "supervision_mask")}, off, k

    def make_batch(self):
        items, srcs = [], []
        B = self.cfg["batch"]
        if self.pooled is not None:
            for g in self.pooled.take(B):
                k = int(self.np.searchsorted(self.pool_offsets, g, side="right") - 1)
                i = g - int(self.pool_offsets[k])
                it, off, rk = self.sample(self.sources[k], i)
                items.append(it); srcs.append((k, i, off, rk))
        else:
            for k, (s, st, q) in enumerate(zip(self.sources, self.streams, self.quotas)):
                if q:
                    for i in st.take(q):
                        it, off, rk = self.sample(s, i)
                        items.append(it); srcs.append((k, i, off, rk))
        for k, j, _, _ in srcs:
            self.draws[self.sources[k].name][j // self.nsub[k]] += 1
        # chained digest of (source, patch, z offset, rotation) draws: equal across arms that share a seed and pool
        # (paired sampling: P384 / NULL / REV); labels and pixel values do not enter it
        self.sample_digest = hashlib.sha256((self.sample_digest + json.dumps(srcs)).encode()).hexdigest()
        torch = self.torch
        return {kk: torch.stack([it[kk] for it in items]) for kk in items[0]}, srcs

    # ------------------------------------------------------------------ step
    def forward(self, x):
        torch = self.torch
        stitched = self.cfg["forward"] == "stitched"
        if self.cfg["precision"] == "bf16":
            with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
                return self.run_model_forward(self.model, x, self.model_crop, stitched=stitched,
                                              use_gradient_checkpointing=self.tc.stitched_gradient_checkpointing)
        return self.run_model_forward(self.model, x, self.model_crop, stitched=stitched,
                                      use_gradient_checkpointing=self.tc.stitched_gradient_checkpointing)

    def train_step(self, step):
        torch, cfg = self.torch, self.cfg
        batch, srcs = self.make_batch()
        B, M = cfg["batch"], cfg["micro_batch"]
        nmic = B // M
        total, sup_frac = 0.0, []
        for j in range(nmic):
            mb = {k: v[j * M:(j + 1) * M] for k, v in batch.items()}
            x = self.prepare_model_input(mb, self.tc)
            preds = self.forward(x)
            lp, targets, ignore = self.prepare_loss_inputs(preds, mb, mode=self.ink.data.mode,
                                                           force_full_supervision=self.tc.force_full_supervision)
            twi = self.cdsi(targets, ignore, lp)
            loss = self.loss_fn(lp.float(), twi.float())
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss at step {step}")
            (loss / nmic if nmic > 1 else loss).backward()
            total += float(loss.item()) / nmic
            sup_frac.append(float((ignore <= 0).float().mean()))
        self.nfin += 1
        gn = float(torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.tc.grad_clip))
        self.optimizer.step()
        self.optimizer.zero_grad(set_to_none=True)
        return total, gn, srcs, float(sum(sup_frac) / len(sup_frac))

    # ------------------------------------------------------------------ resume state
    def rng_state(self):
        return dict(python=self.random.getstate(), numpy=self.np.random.get_state(), torch=self.torch.get_rng_state(),
                    gens=[g.bit_generator.state for g in self.gens], rot=self.rot_gen.bit_generator.state)

    def state(self, done):
        return dict(schema="hercules-d2-resume/1", config_sha256=self.csha, step=done,
                    model=self.model.state_dict(), optimizer=self.optimizer.state_dict(), rng=self.rng_state(),
                    streams=[(list(s.buf), s.epochs) for s in self.streams],
                    pooled=None if self.pooled is None else (list(self.pooled.buf), self.pooled.epochs),
                    draws={k: v.copy() for k, v in self.draws.items()},
                    losses=list(self.losses), walls=list(self.walls), nfin=self.nfin, sample_digest=self.sample_digest,
                    resumptions=list(self.resumptions), ckpt_events=list(self.ckpt_events))

    def load_state(self, st, how):
        if st["config_sha256"] != self.csha:
            raise SystemExit(f"resume state is for config {st['config_sha256']}, not {self.csha}")
        self.model.load_state_dict(st["model"], strict=True)
        self.optimizer.load_state_dict(st["optimizer"])
        r = st["rng"]
        self.random.setstate(r["python"]); self.np.random.set_state(r["numpy"]); self.torch.set_rng_state(r["torch"])
        for g, s in zip(self.gens, r["gens"]):
            g.bit_generator.state = s
        self.rot_gen.bit_generator.state = r["rot"]
        for s, (buf, ep) in zip(self.streams, st["streams"]):
            s.buf, s.epochs = list(buf), ep
        if self.pooled is not None:
            self.pooled.buf, self.pooled.epochs = list(st["pooled"][0]), st["pooled"][1]
        self.draws = {k: v.copy() for k, v in st["draws"].items()}
        self.losses, self.walls, self.nfin = list(st["losses"]), list(st["walls"]), st["nfin"]
        self.sample_digest = st["sample_digest"]
        self.ckpt_events = list(st["ckpt_events"])
        self.start_step = int(st["step"])
        self.resumptions = list(st["resumptions"]) + [dict(event="resume", utc=utc(), from_step=self.start_step,
                                                           source=how)]


def run_train(cfg, out, *, die_after=0, remote_url=None, bare=None):
    import ckpt_shards
    os.makedirs(out, exist_ok=True)
    FINAL, SUMMARY = os.path.join(out, "model_final.pth"), os.path.join(out, "summary.json")
    RESUME = os.path.join(out, "resume_latest.pth")
    if os.path.exists(FINAL) and os.path.exists(SUMMARY):
        print(f"already complete ({FINAL}); nothing to do", flush=True)
        return json.load(open(SUMMARY))
    json.dump(cfg, open(os.path.join(out, "config.json"), "w"), indent=1, sort_keys=True)
    ref = cfg["ckpt"].get("remote_ref")
    if ref:
        # orchestrator ruling on ASK 6 (DECL-OFFLOAD-1): no weights or optimiser state to any git branch. The shard
        # store may only target a LOCAL bare repository (tests, or a local disk mirror); network remotes are refused.
        if not remote_url or "://" in remote_url or ":" in remote_url.split("/")[0] or not os.path.isdir(remote_url):
            raise SystemExit("remote shard push refused: weights/optimiser state may not go to any git remote "
                             "(DECL-OFFLOAD-1 ruling); only an existing local bare repository path is accepted")
    t_start, started = time.time(), utc()
    tr = Trainer(cfg, out)
    np, torch = tr.np, tr.torch
    ref = cfg["ckpt"].get("remote_ref")
    bare = bare or os.path.join(out, "ckpt_git.bare")
    if os.path.exists(RESUME + ".tmp"):
        os.remove(RESUME + ".tmp")
    if os.path.exists(RESUME):
        tr.load_state(torch.load(RESUME, map_location="cpu", weights_only=False), "local")
    elif ref:
        got = ckpt_shards.fetch_latest(bare, remote_url, ref)
        if got is not None:
            blob, man = got
            if man["config_sha256"] == tr.csha and man.get("kind", "resume") == "resume":
                tr.load_state(ckpt_shards.bytes_to_state(blob), f"remote {ref} commit-step {man['step']}")
    # patch registry: every pool patch (conservative contamination set), written before training starts
    reg0 = tr.d2_data.write_patch_registry(os.path.join(out, "patch_registry_pool.npz"), tr.sources, {})
    log_path = os.path.join(out, "train_log.jsonl")
    logf = open(log_path, "a" if tr.resumptions else "w")
    if tr.resumptions:
        logf.write(json.dumps(tr.resumptions[-1]) + "\n"); logf.flush()
    every, L = int(cfg["ckpt"]["every"]), int(cfg["log_every"])
    t_loop = time.time()
    for step in range(tr.start_step, cfg["steps"]):
        t0 = time.perf_counter()
        loss, gn, srcs, supf = tr.train_step(step)
        tr.walls.append(time.perf_counter() - t0)
        tr.losses.append(loss)
        rec = dict(step=step + 1, loss=loss, grad_norm_preclip=gn, s_per_step=tr.walls[-1], supervised_frac=supf,
                   epochs=[s.epochs for s in tr.streams] if tr.pooled is None else [tr.pooled.epochs],
                   run_index=len(tr.resumptions), sample_digest=tr.sample_digest)
        if (step + 1) % L == 0 or step == 0 or L == 1:
            rec["loss_mean_window"] = float(np.mean(tr.losses[-L:]))
            logf.write(json.dumps(rec) + "\n"); logf.flush()
            print(json.dumps(rec), flush=True)
        if every > 0 and (step + 1) % every == 0 and step + 1 < cfg["steps"]:
            st = tr.state(step + 1)
            ev = dict(event="checkpoint", step=step + 1, utc=utc())
            t1 = time.time()
            torch.save(st, RESUME + ".tmp"); os.replace(RESUME + ".tmp", RESUME)
            ev["local_bytes"] = os.path.getsize(RESUME)
            if ref:
                try:
                    r = ckpt_shards.save_and_push(bare, st, step=step + 1, config_sha256=tr.csha,
                                                  remote_url=remote_url, ref=ref,
                                                  max_shard=int(cfg["ckpt"]["shard_bytes"]),
                                                  extra=dict(kind="resume"))
                    ev.update(remote=r)
                except Exception as e:                      # recorded, never worked around
                    ev.update(remote_error=str(e)[-600:])
            ev["seconds"] = round(time.time() - t1, 2)
            tr.ckpt_events.append(ev)
            logf.write(json.dumps(ev) + "\n"); logf.flush()
            print(json.dumps(ev), flush=True)
        if die_after and step + 1 == die_after:
            logf.flush()
            print(f"TEST: simulated crash after step {step + 1}", flush=True)
            os._exit(99)
    logf.close()
    reg = tr.d2_data.write_patch_registry(os.path.join(out, "patch_registry.npz"), tr.sources, tr.draws)
    data_reg_sha = hashlib.sha256(canonical_json([s.registry_sha256 for s in tr.sources])).hexdigest()
    registry = dict(provenance=PROV, schema="hercules-d2-checkpoint-registry/1", config_sha256=tr.csha,
                    config=cfg, lineage=dict(cfg["lineage"], base_sha256=tr.base_sha, steps=cfg["steps"]),
                    data_registry_sha256=data_reg_sha,
                    data_registries=[dict(name=s.name, role=s.role, sha256=s.registry_sha256, n=len(s))
                                     for s in tr.sources],
                    patch_registry=reg, patch_registry_pool_sha256=reg0["sha256"])
    final_meta = dict(config_sha256=tr.csha, arm=cfg["arm"], seed=cfg["seed"], steps=cfg["steps"],
                      lineage=registry["lineage"], data_registry_sha256=data_reg_sha,
                      patch_registry_sha256=reg["sha256"], meta=tr.meta)
    torch.save({"model": tr.model.state_dict(), "config": tr.base_config, "step": cfg["steps"], "d2": final_meta},
               FINAL + ".tmp")
    os.replace(FINAL + ".tmp", FINAL)
    registry["model_final"] = dict(path=FINAL, sha256=sha256_file(FINAL), bytes=os.path.getsize(FINAL))
    registry["train_log_sha256"] = sha256_file(log_path)
    if ref:
        # final weights replace the resume state on the ref (latest only), so they survive a reclaim
        try:
            with open(FINAL, "rb") as fh:
                r = ckpt_shards.save_and_push(bare, fh.read(), step=cfg["steps"], config_sha256=tr.csha,
                                              remote_url=remote_url, ref=ref,
                                              max_shard=int(cfg["ckpt"]["shard_bytes"]),
                                              extra=dict(kind="final", model_final_sha256=registry["model_final"]["sha256"]))
            registry["model_final"]["remote"] = r
        except Exception as e:
            registry["model_final"]["remote_error"] = str(e)[-600:]
    json.dump(registry, open(os.path.join(out, "checkpoint_registry.json"), "w"), indent=1, sort_keys=True)
    summary = dict(provenance=PROV, arm=cfg["arm"], seed=cfg["seed"], config_sha256=tr.csha, started_utc=started,
                   finished_utc=utc(), steps=cfg["steps"], finite_loss_steps=tr.nfin, losses=tr.losses,
                   loss_first=tr.losses[0], loss_last=tr.losses[-1],
                   median_s_per_step=float(np.median(tr.walls)), loop_s=round(time.time() - t_loop, 1),
                   wall_s=round(time.time() - t_start, 1),
                   peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, strict_load=tr.strict,
                   threads=dict(intra=torch.get_num_threads(), interop=torch.get_num_interop_threads()),
                   sample_digest_final=tr.sample_digest, checks=tr.checks, meta=tr.meta, resumptions=tr.resumptions, checkpoint_events=tr.ckpt_events,
                   model_final=registry["model_final"],
                   checkpoint_registry_sha256=sha256_file(os.path.join(out, "checkpoint_registry.json")),
                   script=dict(path=os.path.abspath(__file__), sha256=sha256_file(os.path.abspath(__file__))))
    json.dump(summary, open(SUMMARY + ".tmp", "w"), indent=1)
    os.replace(SUMMARY + ".tmp", SUMMARY)
    if os.path.exists(RESUME):
        os.remove(RESUME)
    return summary


def run_bench(cfg, out, n_steps, warmup):
    """Throughput: warmup steps, then n_steps timed optimizer steps. Writes JSON only (no model)."""
    os.makedirs(out, exist_ok=True)
    tr = Trainer(cfg, out, bench=True)
    walls = []
    for step in range(warmup + n_steps):
        t0 = time.perf_counter()
        loss, gn, _, _ = tr.train_step(step)
        dt = time.perf_counter() - t0
        if step >= warmup:
            walls.append(dt)
        print(json.dumps(dict(step=step + 1, loss=loss, s=dt)), flush=True)
    import statistics
    res = dict(provenance=PROV, utc=utc(), config_sha256=config_sha256(cfg), tile=cfg["tile"], batch=cfg["batch"],
               micro_batch=cfg["micro_batch"], forward=cfg["forward"], precision=cfg["precision"],
               rot24=cfg["rot24"], threads=cfg["threads"], warmup=warmup, n_steps=n_steps, s_per_step=walls,
               median_s_per_step=statistics.median(walls), steps_per_hour=3600.0 / statistics.median(walls),
               peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, data="SYNTHETIC")
    json.dump(res, open(os.path.join(out, "bench.json"), "w"), indent=1)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    mc = sub.add_parser("make-config")
    mc.add_argument("--arm", required=True, help="P128 | P384 | NULL | REV | any custom name")
    mc.add_argument("--seed", type=int, required=True)
    mc.add_argument("--tile", type=int, choices=TILES)
    mc.add_argument("--rot24", action=argparse.BooleanOptionalAction, default=None)
    mc.add_argument("--null", action=argparse.BooleanOptionalAction, default=None)
    mc.add_argument("--rev", action=argparse.BooleanOptionalAction, default=None)
    mc.add_argument("--subtile", action=argparse.BooleanOptionalAction, default=False,
                    help="split each stored S px patch into a (S // tile)^2 grid of sub-tiles (all in the stream)")
    mc.add_argument("--batch", type=int, default=32)
    mc.add_argument("--micro-batch", type=int, default=0, help="gradient-accumulation micro-batch (0 = batch)")
    mc.add_argument("--steps", type=int, default=12000)
    mc.add_argument("--forward", choices=("full", "stitched"), default="full")
    mc.add_argument("--precision", choices=("fp32", "bf16"), default="fp32")
    mc.add_argument("--amx-gate", default=None, help="gate record JSON with pass: true (required for bf16 training)")
    mc.add_argument("--threads", type=int, default=4)
    mc.add_argument("--z-jitter", type=int, default=2)
    mc.add_argument("--z-centre-offset", type=int, default=0)
    mc.add_argument("--lr", type=float, default=2e-5)
    mc.add_argument("--weight-decay", type=float, default=3e-5)
    mc.add_argument("--source", action="append", default=[],
                    help="name=kind:path[:role[:per_batch[:stream]]], kind pairs (registry.json) | stagec (dir with shards.json) | blockpairs (dir with registry/*.jsonl + staged block npz) | tilegrid, tilegrid3, tilegrid4 (dir with registry/*.jsonl + shards/; 3 or 4 = k x k mosaics) | d3_pool (dir)")
    mc.add_argument("--data-root", action="append", default=[],
                    help="name=dir: tree against which a stagec source's repo-relative shard paths resolve")
    mc.add_argument("--allow-ids", action="append", default=[],
                    help="name=path.json: declared patch_id allowlist for a stagec source (sha256 pinned)")
    mc.add_argument("--hash-sources", action="store_true", help="load every source now and pin its sha256")
    mc.add_argument("--ckpt-every", type=int, default=250)
    mc.add_argument("--remote-ref", default=None, help="ref for resume shards in a LOCAL bare repo given by train --remote-url (network remotes are "
                         "refused: DECL-OFFLOAD-1 ruling, no weights to any git branch)")
    mc.add_argument("--log-every", type=int, default=50)
    mc.add_argument("--decl", default="DECL-D2")
    mc.add_argument("--out", required=True)
    tr = sub.add_parser("train")
    tr.add_argument("--config", required=True)
    tr.add_argument("--out", required=True)
    tr.add_argument("--die-after", type=int, default=0, help="TEST ONLY: hard exit (99) after this many steps")
    tr.add_argument("--remote-url", default=None)
    tr.add_argument("--bare", default=None)
    be = sub.add_parser("bench")
    be.add_argument("--config", required=True)
    be.add_argument("--out", required=True)
    be.add_argument("--steps", type=int, default=3)
    be.add_argument("--warmup", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "make-config":
        cfg = make_config(a)
        json.dump(cfg, open(a.out, "w"), indent=1, sort_keys=True)
        print(json.dumps(dict(config=os.path.abspath(a.out), sha256=config_sha256(cfg))))
        return 0
    cfg = validate_config(json.load(open(a.config)))
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(cfg["threads"])
    if a.cmd == "train":
        s = run_train(cfg, a.out, die_after=a.die_after, remote_url=a.remote_url, bare=a.bare)
        print("SUMMARY " + json.dumps({k: v for k, v in s.items() if k not in ("meta", "losses")}), flush=True)
    else:
        r = run_bench(cfg, a.out, a.steps, a.warmup)
        print("BENCH " + json.dumps({k: v for k, v in r.items() if k != "s_per_step"}), flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("train", "bench"):
        # thread env must be set before torch is imported (it is imported lazily inside Trainer)
        try:
            i = sys.argv.index("--config")
            th = str(json.load(open(sys.argv[i + 1]))["threads"])
            os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = th
        except (ValueError, IndexError, OSError, KeyError):
            pass
    sys.exit(main())
