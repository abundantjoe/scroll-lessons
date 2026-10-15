Provenance: Project HERCULES | owner the owner | [id removed]

# d2-null READY (PHASE 1 complete; waiting for GO D2)

Task d2-null: decision D2 (TRAIN-1), fold L-0841, arm NULL (P384 with labels permuted by one seeded derangement),
seed 1. Status: **READY**. Environment built. Code copied and hashed. Base checkpoint verified. Tests pass.
Synthetic smoke, pairing and hold-out checks pass.

Nothing here touched real data. No image, rendered slice or ink map was opened or written. No 0841, eligible or seal
data was touched. No weights went to git. **No training step on real data will start without all three of:**
- the D2 pair-freeze record;
- the D2 amendments in RULES.md;
- an explicit "GO D2" from the orchestrator.

RULES.md on claude/gifted-bell-gavnl5 had no D2 amendment at 2026-09-26 11:20Z.

## 1. Headline numbers (SYNTHETIC; this host)

| Item | Value |
|---|---|
| NULL arm, P384 full forward, fp32, 4 threads, batch 32 = 8 x micro-batch 4 | **median 148.75 s/step** (10 steps: 161.3 on step 1, then 145.5-151.0) |
| Peak RSS (full forward) | **9.70 GB** (ru_maxrss = GNU time; the resume run peaked at 9.87 GB) |
| Projection, 12000 steps | **495.8 h = 20.7 days** of one 4-vCPU session, fp32 (restarts, inference and reads excluded) |
| Stitched forward, same config (micro-batch 4, 3 timed steps after 1 warm-up) | median 148.63 s/step, peak RSS 3.53 GB |
| Local resume state (weights, AdamW moments, all RNG and stream states) | 414,964,028 bytes; save took 0.26 s |
| Config sha256 of the smoke configs (canonical, d2_train.config_sha256) | NULL 8bf5591a4bba0d93990dfab7768343595e7be767e38f4c46723adc5937ed3134; P384 013ffa217b7809534f504559378af10bc345737618d85fb52617e0cc8b117e75; NULL stitched cad154cac6e4419b0c9fe23d9e308a9ee1bbe3d3324bbf774ea0ee5b663f3f74 |

This host is slower than the trainer sibling's host: 148.75 s/step against its 103.98 s/step for the same full fp32
cell (a factor of 1.43). Its CPU is Cascade Lake with no AMX (section 3). The 20.7-day fp32 projection is therefore
longer than the proposal's 14.4 days. bf16 is impossible here (no AMX, no avx512_bf16), and DECL-AMX-1 is not in scope
for this host anyway. Timing note: DECL-D2-A1 section 6 keeps the 2026-11-15 NOT-RUN default. At 20.7 days per arm on
this host type, a seed-1 NULL arm that starts after about 2026-10-25 cannot finish by 2026-11-15.

The smoke configs are synthetic identities. The Phase 2 config will be made with the frozen sources (`--allow-ids`,
`--hash-sources`), so its hash will differ. It will be recorded before step 1.

## 2. Code (copied unchanged; sha256)

Pinned trainer = claude/gifted-bell-gavnl5-sib-trainer @ 8475920fa1a8dd7a753c426be0ebd592851ad884, in
`tools/sib/d2-null/trainer/` and `tools/sib/d2-null/tests/`. Every file matches the trainer's report.json at that commit.

| File | sha256 |
|---|---|
| trainer/d2_train.py | fdbe236cc2cf46664c3d0558e58c7594220a4ce105fde3b5453d634680496f24 |
| trainer/d2_data.py | 5b7a6a5df4f07cf75ef84b63899e531c040b0cb13d8b45b7c180ac2b10a7676b |
| trainer/ckpt_shards.py | ba6db9991e14000b9ba051244c6ae2fa59928b4c6094cc64316ca559cbf3b974 |
| trainer/contam_check.py | 0e30cabbc762979f5b197c0365815dc5915048626c6a01ffb571c643b9f1321e |
| trainer/bench_throughput.py | a30101ccbd05b7cb6d4fc862301ea57ce3d46d183f8f466ebc01ab0e942b5181 |
| trainer/runlog.sh | 44805ecfe195bc3cd08d0139bbb3a9d2ebcbf2de880f97150b4674c64b715b2c |
| tests/sib_trainer_integration_test.py | 162a48a7754c3a867854f0ffe06d47ffa6ec4679ab41939e6301d80b493df4b6 |
| tests/sib_trainer_units_test.py | f4f8046173403f36edc16c3e938f4bdfa912ddd696dc253cd0d6063068405346 |

Trainer head = claude/gifted-bell-gavnl5-sib-trainer @ 08d7e42da1bc2a01c55b8ca0659f00c2b2c33935. It is copied
unchanged into `tools/sib/d2-null/trainer_head/` for the PAIR_FREEZE_SPEC hold-out check; its unit test is at
`tests/sib_trainer_units_test_head.py`. Files that differ from the pin:

| File | sha256 |
|---|---|
| d2_train.py | 2c94ca54ab7699487868a32090d9646040a8f0ef93598fe0b288c4a7bedb4531 |
| d2_data.py | e23ac6e69963d7472af71920c418b8f6df9170a9e5450b1a312e4709c60479a2 |
| pair_freeze.py | 4e407f53d697db33272a4e3cf623a9b50cbb4ea12431051db3772502e0768f64 |
| full_conv_check.py | 2191d1a37036433eb43a5cce7ba46d04a6cc6ce7fdab822926968a268079eb1f |

In d2_train.py, the per-step training path is unchanged between the pin and the head. The diff covers only:
- the network-remote refusal for the shard store (the Q6 ruling);
- the `--data-root` flag;
- the removal of `remote_url_default`.

**Finding (for the freeze):** the head's own report.json `code_sha256` still lists the 5bc29e1 hashes for
d2_data.py (71dd6152...), d2_train.py (2c58dbf3...) and pair_freeze.py (d0ea04a3...). Commit 08d7e42 changed all three
without updating report.json. The freeze should pin actual file hashes (above), not report.json.

**Which code trains:** the orchestrator's GO names it. The real pair layouts (`blockpairs`, `stagec` with data_root,
`--allow-ids` from pair_freeze.py) need the head code. The pinned copy has no blockpairs adapter and no `--data-root`.

My helpers (tools/sib/d2-null/; numbers and hashes only):

| File | sha256 | Role |
|---|---|---|
| smoke.sh | 7063c0af998807802023ffb88de436427952bcd1a4959a9cd23f8c1b1aec6ea2 | smoke driver |
| pair_check.py | d3a25d71471d00eae817f5ccf56c5ce0e60ce8c4802bc5127f2fbe3fe4f8f400 | per-step hashes of batch images, labels and draws; RNG states; independent derangement check |
| smoke_compare.py | 6cb6eb118238c091ce3706ba8805f1dccf556f0f89d433fb7ca27543b213908d | summary to smoke.json |
| holdout_check.py | 4a61993bcf1f1af9edf4e9e1510dc30fd5886ea32b8e9615087718138efb7f79 | synthetic freeze + hold-out check |
| runlog.sh | 952987ddf31df1d7b00987a837ed5b2076e4610613e304991588c98675e986d5 | writes runs.jsonl rows |

pair_check.py gained a `--trainer-dir` option after the smoke. With the option absent, behaviour is unchanged.

## 3. Environment

- **Host.**
  - CPU: Intel Xeon @ 2.80 GHz, family 6 model 85 stepping 7 (Cascade Lake), KVM guest.
  - nproc 4; 1 thread per core.
  - AVX-512 F/DQ/CD/BW/VL + VNNI. **amx_bf16 ABSENT** (no amx_* flags, no avx512_bf16).
  - torch CPU capability AVX512.
  - Memory: 15 GB, no swap.
  - Disk: 23 GB free at 11:20Z; /work uses 5.0 GB.
  - Raw outputs: `out/*_lscpu.log`, `*_nproc.log`, `*_free_g.log`, `*_df.log`.
- **Build.** `/work/setup_d2null.sh`, the setup_env.sh route without docker or C++ (training needs neither):
  - villa sparse checkout of `vesuvius` at 41701aa0eaa1aa765523db3f9f972b5830abf549, added via a `.pth` path entry
    (as TOOLING.md `--ignore-requires-python`);
  - /opt/hv-ink: Python 3.13.12, torch 2.14.0+cpu, torchvision 0.29.0+cpu;
  - the other packages from docker/env/hv-ink-freeze.txt.
- **Deviation from hv-ink-freeze.txt.** The official training import path (vesuvius.ink_detection.training.train
  and data.augmentations) needs scipy, scikit-image, connected-components-3d, numba, fft_conv_pytorch, SimpleITK and
  pandas. None of these are in the freeze.
  - numba 0.66.0 refuses numpy > 2.4 at import (verified: "Numba needs NumPy 2.4 or less").
  - So numpy is **2.4.6** (villa uv.lock), not the freeze's 2.5.3.
  - All added packages are pinned to villa 41701aa uv.lock versions: scipy 1.18.0, scikit-image 0.26.0,
    connected-components-3d 4.0.0, numba 0.66.0, llvmlite 0.48.0, fft-conv-pytorch 1.2.0, simpleitk 2.5.5,
    pandas 3.0.3, imageio 2.37.3, lazy-loader 0.5.
  - Also pytest and pygments.
  - Full list: `env_freeze.txt` (sha256 51cce907...6b15c66). `uv pip check`: all compatible.
- **Base checkpoint.** ink_9um hybrid_3d2d seed42 step-075000, HF scrollprize/ink_9um rev
  7109667e2607db1b90c37c8b09cb876ea7fe7bb1:
  - path /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth, 138,360,039 bytes;
  - **sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab = required value (verified,
    `sha256sum -c` OK)**;
  - it matches data/catalogue/checkpoints.json.

## 4. Tests

| Suite | Code | Result |
|---|---|---|
| sib_trainer_units_test.py | pin 8475920 | 14 passed (7 s) |
| sib_trainer_integration_test.py | pin 8475920 | **12 passed** (1286 s) |
| sib_trainer_units_test.py | head 08d7e42 | 18 passed (11 s) |

The integration suite covers:
- determinism x3;
- seed change;
- P384/NULL/REV paired sampling;
- subtile coverage;
- bitwise resume, from local state and from shards;
- D3 bitwise equivalence for CTRL/FA/NULLA/REVA;
- bf16 refusal.

All suites ran from a pristine `git archive` of the named commit.

## 5. Smoke of exactly this arm (SYNTHETIC; `smoke.json` sha256 0f75533e...a366bf2)

**Data.** `d2_data.write_synthetic_registry(n=96, size=384, seed=20260926)`, 3 shards; registry sha256 3ef3d1b6...a48.

**Config.** `make-config --arm NULL --seed 1 --subtile --batch 32 --micro-batch 4 --steps 10 --forward full
--precision fp32 --threads 4 --z-jitter 2 --z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --log-every 1
--ckpt-every 5 --hash-sources`.
- This is the DECL-D2-A1 proposal's common config, with steps, log and checkpoint intervals shrunk for the smoke.
  Production uses 12000 / 50 / 250.
- No remote ref.
- Configs: `smoke_configs/`.

**A. Uninterrupted run, 10 steps.**
- 10/10 losses finite: 0.652 -> 0.566.
- Checkpoint at step 5.
- model_final sha256 1040fb27...f60f (local only).

**B. Crash and resume.** The run was killed after step 7 (`--die-after 7`, exit 99; the last save was at step 5).
The same command resumed it from step 5 to step 10.
- Losses at steps 1-10 are identical to A.
- **Final weights are bitwise equal to A** (max abs diff 0.0; same model_final sha256).
- Same sample digest.

**Derangement.** Checked independently by re-deriving `default_rng(1).permutation` redrawn until it has no fixed
point, then comparing with a fresh load of the sources.
- n = 96. It was accepted on the first draw. perm sha256 9507b796...7aba equals the trainer's.
- **0 fixed points.** It is a valid permutation, with 5 cycles, the shortest of length 4.
- Every patch i carries exactly patch perm[i]'s ink and supervision arrays.
- **0 patches carry label arrays equal to their own.** The trainer's own count is 96 of 96 differing.
- Images are untouched.
- Pool ink and supervised fractions are unchanged (0.3803 / 0.7373).

**Pairing with P384 seed 1.** pair_check.py ran each arm in its own process: 2 real train steps, then 8 batch-only
draws.
- The batch image tensors are sha256-equal at **every one of the 10 steps**.
- The (source, patch, z offset, rotation) draws and the chained sample digest are equal.
- The ink labels differ at every step.
- The torch RNG state is equal after every step.
- The model step (forward, backward, AdamW) consumes no RNG in either arm. So batch-only draws are faithful to
  training, and the jitter, rotation and augmentation sequence is label-independent.
- NULL's digests equal run A's at all 10 steps. NULL's two train-step losses equal run A's.

## 6. Hold-out check against PAIR_FREEZE_SPEC (trainer head; SYNTHETIC; `holdout_check.json` sha256 dd494bb1...933c)

**Setup.**
- A synthetic stage-C tree: the spec's preferred `pairs0814u` layout, with shards.json, pair_registry.json and staged
  block npz files under data_root. It has 24 patches of 384 px.
- A hold-out list of 6 ids: 5 in the pool, 1 not in the pool.
- `pair_freeze.py --verify` on it gives: passed 24, held_out 5, after_holdouts 19; label-rule mismatch 0; record_sha256
  7ea3fd2a...5bf7. The record is `smoke_configs/holdout_pair_freeze_SYNTHETIC.json`.
- Head `make-config` for NULL and P384 used `--allow-ids`, `--data-root` and `--hash-sources`. Config sha256: NULL
  28c3807c...49d3, P384 07b26f18...f652. The allowlist sha256 in both configs equals the freeze record's.

**Results.**
- **Pool:** the loaded patches equal the allowlist (19 in both arms). **0 held-out ids were loaded.**
- **Derangement:** it acts on the 19 allowed patches only and equals the trainer's perm. 0 fixed points. The labels
  equal the fresh allowed labels permuted. **0 label arrays equal a held-out patch's.** P384's labels are unpermuted.
- **Draws:** over 12 batches (384 samples), every drawn patch is allowed and not held out; all 19 were drawn.
- **Pairing** (one process per arm, 12 batch-only draws): images and digests are equal in every batch, and the labels
  differ in every batch.
- **Tamper:** an allowlist edited after the config was made is refused ("allow_ids file changed since the config was
  made").

## 7. Notes for Phase 2 (all recorded; none worked around)

1. **One Trainer per process.** A Trainer seeds and uses the process-global python / numpy / torch RNGs. Two Trainers
   in one process break the pairing: my first in-process hold-out attempt (`holdout_check_2`) showed unequal images for
   that reason. It is superseded by `holdout_check_3`, which uses one process per arm.
   - Separate sessions (one arm per session) are unaffected.
   - The first `holdout_check` run failed (rc 1), also in my checker: torch refuses a second
     `set_num_interop_threads` call.
2. **Pairing across sessions.**
   - The per-50-step `sample_digest` in each train_log.jsonl covers patch, z and rotation. It lets the orchestrator
     compare NULL-s1 with P384-s1 across sessions.
   - The augmentation stream (torch RNG) is not in the digest. Identical augmentations therefore also require
     identical library versions in both sessions (see env_freeze.txt). I recommend that P384-s1 runs with the same
     freeze.
3. **Weights stay local.**
   - The pinned copy's `remote_url_default()` climbs three levels up from its own directory to find the repo root.
     From my copy (tools/sib/d2-null/trainer) that is the wrong path, so no `--remote-ref` will be used. The head
     version refuses network remotes anyway (Q6 ruling, DECL-OFFLOAD-1).
   - Resume state (415 MB) and model_final stay on local disk. A container reclaim therefore loses at most the steps
     since the last 250-step local save, but only if the disk survives. It does not survive a full reclaim.
4. **Throughput.**
   - 148.75 s/step means 250 steps take about 10.3 h between local saves.
   - 20.7 days per arm on this host type. It will hold only if the container is kept alive (hourly check-ins).
5. **Forward mode.** "full" (the ASK-1 default, measured here) and "stitched" cost the same per step on this host,
   and stitched uses 36 % of the RAM. The declared mode will be used exactly.

## 8. Logs

- `runs.jsonl`: every run, failures included, with utc, command, exit code and output sha256.
- `out/`: raw outputs.
- `smoke.json`, `holdout_check.json`, `smoke_configs/`, `env_freeze.txt`.
