Provenance: Project HERCULES | owner the owner | [id removed]

# d2-p384 PHASE 1: READY (synthetic only; waiting for GO D2)

Task: D2 (TRAIN-1), fold L-0841, arm P384, seed 1. This session is a trainer. No real data was loaded or trained on.
No image, rendered slice or ink map was opened, written or described. No PHerc0841 data, eligible data, seal or
key was touched. Weights stay under /work and are not committed. Every run is logged in `runs.jsonl`
(utc, command, exit code, output sha256; outputs in `out/`).

## 1. Environment

- `tools/sib/d2-p384/setup_env_d2.sh` is the training-only subset of `docker/env/setup_env.sh`: villa sparse checkout
  plus `/opt/hv-ink`. There is no docker and no C++ build.
  - Villa is at 41701aa0eaa1aa765523db3f9f972b5830abf549; `vesuvius/ink_detection/training/train.py` sha256 f87f882d...,
    matching DECL-D3-A1.
  - Villa vesuvius is linked by a `.pth` path entry, because the editable install needs Python 3.14. The trainer
    sibling did the same.
  - Python 3.13.12, torch 2.14.0+cpu, torchvision 0.29.0+cpu.
  - The env matches `hv-ink-freeze.txt`. Added on top: pytest, pygments, scipy, scikit-image, and the five villa
    train-path deps below. Full list: `hv-ink-freeze-d2.txt`.
- **Failure, recorded:** the first test run (`pytest_all`) failed 12 of 26 tests on `No module named 'cc3d'`.
  - The train-path imports also needed numba, fft-conv-pytorch, SimpleITK and pandas.
  - All five are declared in villa 41701aa `vesuvius/pyproject.toml` (models extra). None is a community package.
  - I installed them (connected-components-3d 4.1.0, numba 0.67.0, llvmlite 0.49.0, fft-conv-pytorch 1.2.0,
    simpleitk 2.5.6, pandas 3.0.6) and added them to the setup script.

## 2. Code (copied unchanged from origin/claude/gifted-bell-gavnl5-sib-trainer @ 8475920fa1a8dd7a753c426be0ebd592851ad884)

The files are in `tools/sib/d2-p384/trainer/` and `tools/sib/d2-p384/tests/`. Each is byte-identical (`cmp`) to the
pinned commit, and each sha256 equals `logs/sib/trainer/report.json` `code_sha256`.

| File | sha256 |
|---|---|
| trainer/d2_train.py | fdbe236cc2cf46664c3d0558e58c7594220a4ce105fde3b5453d634680496f24 |
| trainer/d2_data.py | 5b7a6a5df4f07cf75ef84b63899e531c040b0cb13d8b45b7c180ac2b10a7676b |
| trainer/ckpt_shards.py | ba6db9991e14000b9ba051244c6ae2fa59928b4c6094cc64316ca559cbf3b974 |
| trainer/contam_check.py | 0e30cabbc762979f5b197c0365815dc5915048626c6a01ffb571c643b9f1321e |
| trainer/bench_throughput.py | a30101ccbd05b7cb6d4fc862301ea57ce3d46d183f8f466ebc01ab0e942b5181 |
| trainer/runlog.sh | 44805ecfe195bc3cd08d0139bbb3a9d2ebcbf2de880f97150b4674c64b715b2c |
| tests/sib_trainer_units_test.py | f4f8046173403f36edc16c3e938f4bdfa912ddd696dc253cd0d6063068405346 |
| tests/sib_trainer_integration_test.py | 162a48a7754c3a867854f0ffe06d47ffa6ec4679ab41939e6301d80b493df4b6 |

Written by this session:

| File | Role | sha256 |
|---|---|---|
| runlog.sh | runs.jsonl logger | 9cdb8544f93efaf48feec3a54031d37a6ee99a426c27da1e21d23dbf86cb587b |
| setup_env_d2.sh | env setup | 4d52dda91d39d9231631d52c9e53c787df1b1e985de440f48172202146c39b6b |
| smoke_p384.sh | smoke driver | c583e9fa27c2c6071871b426aac622ac1080d876ce21b55c6391c9eaf8951fb7 |
| smoke_compare.py | smoke comparison | 133682258d112491217a02f0c3458d36c9a13561da6a6f8c174195c71f9cba9f |
| timed.py | wall time and peak RSS | 7405b3b6debfd572acc0d490155da4486cfee1d6ece8bd26761f571015b891f2 |
| param_diff.py | 128 vs 384 build diff | f9af89faf8769e1220eae4f95bd73d10568818a00a8e44f0582d19f3cb7416c3 |
| pairing_check.py | pairing and hold-out check | 2b8e7b0da8314cfb82777d6cc9566c379af7558721f2336190d0dd5953610073 |

**Pinned code vs the trainer tip (the orchestrator decides which to freeze).** The trainer branch has moved on to
08d7e42da1bc2a01c55b8ca0659f00c2b2c33935, which adds:
- the Q6 guard, which refuses any network remote for weight shards;
- the `blockpairs` adapter;
- `data_root` for `stagec`;
- `pair_freeze.py`.

Two consequences for the pinned 8475920:
- If `--remote-ref` is set, it pushes the resume state (weights plus AdamW) to origin by default. That would break
  DECL-OFFLOAD-1. This session will never pass `--remote-ref`.
- It cannot load the `blockpairs` kind that PAIR_FREEZE_SPEC.md names for pairs0814 and 0814b.

The pinned copy is fit for the synthetic phase only. PHASE 2 needs the orchestrator to re-pin the trainer (for example
to 08d7e42) in the D2 amendment. I have not changed the copy.

## 3. Base checkpoint

- ink_9um hybrid_3d2d seed42 step-075000 (data/catalogue/checkpoints.json).
- Source: HF scrollprize/ink_9um rev 7109667e2607db1b90c37c8b09cb876ea7fe7bb1.
- 138,360,039 bytes, sha256 **e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab: VERIFIED**. It matches
  the catalogue LFS hash.
- Local path: /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth.

## 4. Machine (`lscpu.txt`, `machine.txt`)

- Intel Xeon Processor @ 2.10 GHz, 4 CPUs (1 thread per core, 1 socket).
- **amx_bf16 present** (also amx_int8, amx_tile).
- L2 8 MiB, L3 260 MiB.
- nproc 4, RAM 15 GB total, no swap.
- Disk: 29 GB free on / (252 GB device, fixed per-session allowance).

## 5. Tests

`pytest_all_2` (05:30:38Z-05:47:20Z): **26 passed, 0 failed**, 1001 s. That is 14 unit and 12 integration tests.
- They ran from a detached worktree of 8475920 at /work/sib/src, because the tests import `tools/sib/trainer` and
  `tools/d3/d3_train.py` (sha256 2943b1b6...). That worktree's trainer and test files are byte-identical to the
  copies above.
- The suite covers D3 bitwise equivalence, determinism, paired sampling, and bitwise resume from local state and from
  shards in a local bare repo.

## 6. Smoke of this arm (`smoke_result.json`, `cfg.json`; SYNTHETIC)

Config (`make-config`):
- `--arm P384 --seed 1`, tile 384, rotations 24 x 15 deg;
- `--batch 32 --micro-batch 4 --steps 10 --forward full --precision fp32 --threads 4`;
- `--subtile --z-jitter 2 --lr 2e-5 --weight-decay 3e-5 --log-every 1 --ckpt-every 5`;
- one pairs source built by `d2_data.write_synthetic_registry(n=40, size=560, seed=101)`.

Config sha256 (trainer canonical) 37c0d81572ab2259f981daf408c4c2b5717665ebfe56a8a62da94f8a188b1ce2; the cfg.json file
sha256 is d6832342.... This is a smoke config, not a declared recipe.

- **Forward mode:** full 384 px on the unchanged base architecture, built from its own 128 config. The strict load
  reports "All keys matched successfully". No architecture change was needed, so this is not the stitched mode.
- **Throughput:** median **129.16 s/step** (129.10 excluding step 1). The ten steps were 134.4, 127.1, 127.7, 129.5,
  126.1, 129.9, 128.2, 129.2, 129.1 and 130.8 s.
  - Projected 12,000 steps: **430.5 h = 17.9 days** at fp32 in one session. Real-data I/O is not included.
  - This is 24 % slower than the trainer sibling's 103.98 s/step for the same cell (3 timed steps,
    throughput.json). The cause is not established; it may be host variance.
- **Peak RSS:** **9.89 GB** for run A, 9.96 / 10.03 GB for the B runs (getrusage of the child).
- **Losses:** all 10 finite, 0.6235 falling to 0.5115. Grad norm before clipping fell from 0.85 to 0.58.
  Supervised fraction about 0.78 (the synthetic valid mask plus pixels rotated in from outside the patch).
- **Resume test:**
  - Run A ran 10 steps uninterrupted.
  - Run B used the same config, hard-exited with code 99 after step 7 (last save at step 5, a 414,961,596-byte local
    resume state saved in 0.38 s), then was re-run.
  - It resumed from local state at step 5.
  - Per-step losses are identical: max abs diff 0.0.
  - Final weights are **bitwise equal**, model_final sha256
    99987caf4272656bb3ec5a0599ba73213efef91c4667218469e47b68dcfe9d02 for both. Local only, synthetic, never pushed.
  - The final sample digests are equal.
  - This holds at 4 threads. The sibling's determinism tests used 1 thread.

## 7. Forward mode: measured parameter diff (`param_diff.json`)

- **Build from the base config** (patch 17 x 128 x 128), strict=True load:
  - 508 state keys, 34,546,498 parameters, "All keys matched successfully".
  - On a 17 x 384 x 384 input it runs fully convolutionally: output (1, 1, 384, 384), finite, and the backward pass is
    finite.
- **Build with patch_size = crop_size = 17 x 384 x 384:**
  - 614 state keys, 47,871,298 parameters.
  - The auto-configuration plans a deeper and wider network.
  - A strict load of the base weights fails (RuntimeError).
- **The difference:** 146 keys differ.
  - 106 keys exist only in the 384 build.
  - 40 keys exist in both builds with different shapes; 24 of these are trainable parameters. Example:
    `shared_decoder.stages.1.convs.0.conv.weight` is (256, 512, 3, 3) in one build and (320, 640, 3, 3) in the other.
  - By module: shared_encoder 96, shared_decoder 50.
  - Elements in the differing tensors: 3,636,512 in the 128 build, 29,876,192 in the 384 build.
- This agrees with the sibling's `full_conv_check.json` (146 differing, strict load fails).
- Consequences:
  - "full" P384 means training the unchanged 128-built model on 384 px tiles.
  - A 384 px map from it needs a non-official 384-tile inference path with its own gate.
  - "stitched" keeps official 128 px inference.
  - The D2 amendment must decide.

## 8. Pairing and hold-outs against PAIR_FREEZE_SPEC.md (trainer 08d7e42) (`pairing_check.json`)

- **Pairing:** the P384, NULL and REV configs made with identical flags differ only in `arm` plus `null` or `rev`, so
  the arms are paired. The sibling's integration test also shows equal sample digests with different losses.
- **Hold-out order:** for `tilegrid*` the allowlist is applied before the 3 x 3 block-completeness test. One held-out
  tile therefore removes its whole block (fail-closed), as the spec requires. `stagec` applies the allowlist too.
- **FINDING (fail-open):**
  - `load_source` passes `allow_ids` only to `tilegrid*` and `stagec`.
  - For kinds `pairs` and `d3_pool` it is silently ignored, although make-config pins its path and sha256 into the
    config.
  - Measured: an allowlist of 34 of 40 synthetic patches loaded all **40**.
  - The same code is at the trainer tip 08d7e42.
  - The spec lists only tilegrid3, blockpairs and stagec sources, so a spec-conformant freeze is unaffected. A freeze
    that listed a `pairs` or `d3_pool` source would train on held-out patches without any error.
  - Recommended guard, for the trainer owner (I did not edit the code): refuse `allow_ids` on kinds that do not apply
    it.
- **Adapters:** pinned 8475920 lacks `blockpairs` and `stagec` `data_root` (section 2).

## 9. PHASE 2 gate

No training on real data starts until three things hold:
1. an orchestrator message saying "GO D2";
2. that message names the pair-freeze record and the RULES.md IDs of the D2 amendments;
3. those amendments are in RULES.md. At 11:17Z on 2026-09-26, `origin/claude/gifted-bell-gavnl5` RULES.md holds only
   DECL-D2.

Then I verify every shard sha256, train exactly the declared recipe and seed, log every 50 steps, keep weights local,
and write model_final sha256, summary.json and REPORT.md.
