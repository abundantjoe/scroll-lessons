Provenance: Project HERCULES | owner the owner | [id removed]

# dev-distft: PHASE 1 READY (DEV recipe DIST-FT, DECL-DEVLOOP-A1 item 2, recipe 3)

STATUS: READY for 'GO DEV DIST-FT'. No real data has been trained on, loaded or fetched. Every number below comes from
SYNTHETIC data (d2_data.write_synthetic_registry) or from registry metadata counts. No image, map, render or CT pixel
was opened, viewed or described. Open parameters and their defaults are in ASK.md (A1-A9).

## 1. What was built (tools/sib/dev-distft/)

| File | Role |
|---|---|
| `pinned/d2_train.py`, `pinned/d2_data.py`, `pinned/ckpt_shards.py`, `pinned/contam_check.py` | Byte-identical copies from trainer branch commit 8475920fa1a8dd7a753c426be0ebd592851ad884. sha256 fdbe236c..., 5b7a6a5d..., ba6db999..., 0e30cabb... (all four equal the trainer's report.json `code_sha256`). They are verified at every import and the code refuses to run if any differs. |
| `distft.py` | The DIST-FT layer: soft-target loaders, `DistFTTrainer` (a subclass of the pinned Trainer), CLI `make-config` / `train` / `bench` / `synth`. |
| `tests/test_distft.py` | 12 tests, synthetic only. |
| `smoke.sh`, `bench_ab.py`, `runlog.sh`, `env/setup_env.sh` | Smoke driver, timing A/B, run logger (every run is in runs.jsonl), environment setup. |

The only declared change is the target.
- Pinned rule (DECL-D2): ink = ref9 >= 150, blank = ref9 <= 100, and the band and invalid pixels are ignored.
- DIST-FT: target = ref9 / 255, supervised on every pair-valid pixel.

Three code sites in the pinned pipeline assume a binary target. Each is generalised so that a {0, 1} target gives
the pinned result bit for bit:
1. `_rotate`: `a & b` becomes `a * b`.
2. The uint8 target is divided by 255 just before the official augmentations. Those augmentations only permute label
   values; this is checked on the first 4000 samples of every run and recorded in `summary.json`.
3. The official `prepare_loss_inputs` (flat mode) is used without its `amax(...) > 0` binarisation.

Everything else is the pinned trainer, unchanged:
- the official villa 41701aa model and loss (smoothed BCE + Dice, ignore channel);
- AdamW, robust_mad normalisation, the official augmentations;
- the 17-of-21 z window with jitter +-2, 24 x 15 deg rotations and sub-tiles;
- paired epoch-wise streams, resume state every 250 steps, and the patch and checkpoint registries.

Official training script: villa train.py sha256 f87f882d3aed60818037abf1b04f42606d5882dcbd087f0b057065335c7061c2,
equal to the one pinned in DECL-D3-A1.

Resume state stays local only. `--remote-ref` is refused, so no weights or optimiser state ever go to git.

Controls:
- NULL: one derangement drawn with `default_rng(20260925)`, independent of the run seed. It permutes the soft targets
  and their validity masks across the role=train patches. Any other derangement seed is refused.
- REV: every 21-slice input stack is reversed in depth, with the targets unchanged.
- CHANCE needs no training and belongs to the evaluator.

## 2. Verification

**Base checkpoint.**
- ink_9um hybrid_3d2d seed42 step-075000, downloaded from HF scrollprize/ink_9um rev 7109667e (138,360,039 bytes).
- sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab: MATCH (downloads.jsonl).
- It is re-checked at the start of every run.

**Tests: 12 passed, 0 failed** (runs.jsonl label `pytest_distft`, last run 68 s).
- **Hard target through the layer is bitwise the pinned Trainer.** 3 steps with rot24 and sub-tiles give equal
  losses, final weights and sample digests.
- **Rotation override** equals the pinned `_rotate` bitwise on binary labels, at all 24 angles. On soft labels it keeps
  the soft values (more than 50 distinct values survive, where `&` would leave only {0, 1}).
- **Soft loss input** equals the official `prepare_loss_inputs` bitwise on binary labels, both with and without deep
  supervision and resize. On soft labels it passes the values through.
- **Soft loader alignment.** Applying the DECL-D2 threshold to the soft target reproduces the pinned loader's labels
  exactly, and the images are identical. The loader refuses the source otherwise, on every source kind. Each layout
  has a synthetic test:
  - `pairs`;
  - `stagec`, with and without an allowlist (patch order and allowlist filtering match the pinned loader);
  - `tilegrid` and `tilegrid3` (the 3 x 3 mosaic places the soft map pixel-exactly; the A7 validity rule).
- **Soft batch.** Supervised label values lie in [0, 1], are multiples of 1/255, and take more than 20 distinct values.
  The augmentation value-multiset check reports 0 changes, and the loss is finite.
- **NULL.** 0 fixed points. The same permutation sha256 comes out under run seeds 11 and 12, and it equals an
  independent re-draw with seed 20260925. Every patch gets exactly `soft[perm]` and `valid[perm]`.
- **REV.** The stacks are exactly depth-reversed and the targets are unchanged.
- **Paired sampling.** DIST-FT, NULL and REV have an identical chained sample digest.
- **Guardrails.** Refused: a derangement seed other than 20260925, and `--remote-ref`.
- **Resume.** A run killed after step 3 (last save at step 2) and resumed gives losses and final weights bitwise equal
  to an uninterrupted 4-step run.

## 3. Synthetic smoke: 20 steps per arm at the full-run settings

Settings:
- tile 128, rot24, sub-tiles of 384 px patches;
- batch 32, fp32, 4 threads;
- seed 20260925, resume save at step 10;
- SYNTHETIC pool of 64 patches = 576 sub-tiles.

| Arm | config sha256 | loss step 1 -> 20 | finite steps | median s/step | peak RSS | check |
|---|---|---|---|---|---|---|
| DIST-FT | e21fc6b8f910... | 0.6283 -> 0.5325 | 20/20 | 16.66 | 6.94 GB | aug label multiset changed 0/640 |
| DIST-FT-NULL | 9c5bda226b05... | 0.6316 -> 0.5688 | 20/20 | 17.26 | 7.00 GB | derangement fixed points 0 (perm e06a168f5fb7...), 0/640 |
| DIST-FT-REV | c3e0319221ab... | 0.6244 -> 0.5321 | 20/20 | 16.30 | 7.03 GB | exact depth reverse True, 0/640 |

- All three arms have the identical final sample digest (e64e68217708...), so the sampling is paired.
- The resume save (414,977,916 bytes) took 0.4 s.
- Summaries, logs, configs and checkpoint registries are in `smoke/<arm>/`. The final weights stayed in /work and are
  not in git.
- The losses are synthetic training losses. They say nothing about ink and are not evidence of any kind.

**Timing and its spread** (bench_ab.json; the same synthetic pool, 5 timed steps after 1 warm-up step, one process):

| Path | median s/step |
|---|---|
| pinned Trainer, hard target | 12.78 |
| DIST-FT soft, augmentation check off | 12.65 |
| DIST-FT soft, augmentation check on (first 125 steps only) | 13.16 |
| DIST-FT via the CLI, 8 steps, recheck | 14.67 |
| smoke runs above | 16.30 - 17.26 |

- The soft target adds no measurable cost (12.65 s against 12.78 s pinned).
- The spread between runs (12.65 to 17.26 s, 36 %) comes from the container itself, not from the recipe. The trainer
  sibling measured 11.94 s on its container. I did not find a cause beyond machine load: the smoke was the only job
  running.

**Hours per full run** (fp32, 4 threads, batch 32):

| Steps | at 12.65 s/step | at 16.66 s/step (smoke median) | at 17.26 s/step (slowest) |
|---|---|---|---|
| 2500 (ASK A1 default) | 8.8 h | 11.6 h | 12.0 h |
| 3000 | 10.5 h | 13.9 h | 14.4 h |
| 12,000 (DECL-D2 P128) | 42.2 h | 55.5 h | 57.5 h |

- Three arms at 2500 steps, run one after another: 26 to 36 h of wall time.
- Memory: 7.0 GB peak on 64 synthetic patches. The real pairs0814 pool (564 patches) adds about 1.6 GB of uint8
  stacks, which fits in 15 GB.

## 4. Needed before PHASE 2 (none of it exists yet)

1. **The frozen hold-out list** (DECL-DEVLOOP-A1 item 6). The devloop branch at 5e7fd18 has no frozen list, no
   EVAL_API.md and no METRIC-HASH.
2. **A named training-pair registry.**
   - pairs0814 and pairs0814b have 564 GATED and passed staged patches, but no stage-C `shards.json` yet.
   - pairs0139's shards are not on git.
   - The loaders for both layouts, plus the soft-target alignment check, are implemented and tested on synthetic data.
3. **Answers to ASK A1-A9**, or acceptance of the defaults. The most consequential are:
   - A1: 2500 steps;
   - A2: official label smoothing 0.5 is kept on the soft targets;
   - A7: pairs0139 has no validity mask.

On GO, the commands are:

```
distft.py make-config --arm <DIST-FT|DIST-FT-NULL|DIST-FT-REV> --batch 32 --steps 2500 --threads 4 --subtile \
   --source p0814=stagec:<dir> --source p0139=tilegrid3:<dir> --allow-ids p0814=<allow.json> \
   --allow-ids p0139=<allow.json> --hash-sources --out cfg_<arm>.json
nohup distft.py train --config cfg_<arm>.json --out /work/distft/<arm>      (re-run the same command to resume)
```

The allowlists are built from the frozen hold-out list and the named registry, and are sha256-pinned in the config.
