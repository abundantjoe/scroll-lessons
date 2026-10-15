Provenance: Project HERCULES | owner the owner | [id removed]

# READY: DEV recipe LC384-SOFT, phase 1 (task dev-lcsoft)

Status: phase 1 is complete. No real data was read, no training step ran on real data, and no image was opened.
Phase 2 is gated and waits for all of:
- a METRIC-HASH of the frozen v3 registry and evaluator;
- the frozen hold-out list;
- EVAL_API.md;
- "GO DEV LC384-SOFT".

At 05:25Z none of them exists: the RULES.md tip 81a8974 has METRIC-HASH-20 and -21, both P4; the devloop tip is a6af0cb.

## 1. Recipe definition used (READ THIS: it differs from the task text)
- **Task text:** "letter-context 384 px head ... with the encoder unfrozen / soft".
- **Declared protocol** (first_recipes.md recipe 2, devloop 5e7fd18, the source DECL-DEVLOOP-A1 item 2 cites): "recipe 1 with soft-teacher targets: the continuous organizer value / 255, BCE on soft targets, no thresholds and no ignored band".
  - The encoder stays FROZEN, as in LC384-FROZEN.
  - first_recipes.md contains no "soft-encoder" switch.
- I built the declared version. The undeclared reading (unfrozen encoder) is priced only, in section 4. It is not implemented as a recipe.
- If you meant the unfrozen encoder, that needs a declaration: it costs 21x per step and cannot use the feature cache.

## 2. Code (pinned; `logs/sib/dev-lcsoft/config.json`, sha256 c78be1db969b9facabbe26876676578736ff966282c17239551ec00f78365430)
- **Upstream:** amx branch commit d360dd7fa438445b01aae9281dce5bbf5432a3fc, `tools/sib/devloop-r1/`.
- **Byte-identical copies:** lc_model.py f08c9ed1..., lc_cache.py 38372316..., lc_infer.py b59128a5..., lc_pool.py 75a73669...
- **lc_train.py (dc1295a1...):** the only change is the declared switch `--targets soft` (upstream eaa8f68b...). With the switch:
  - the loss is masked mean BCE-with-logits against inkmap_u8/255;
  - there is no label smoothing and no Dice;
  - NULL takes the soft target (value and mask) of perm[i];
  - the default `--targets hard` path is unchanged.
- **soft_targets.py (new, c4818862...):** builds `<cache>/soft/{inkmap,sup}.npy` row-aligned to a cache without modifying it. Its supervision mask is fail-closed:
  - label 0/1 → supervised;
  - label 255 → supervised as band only on tiles with registry valid24_frac == 1.0 and where render slice 15 > 0;
  - otherwise unsupervised (counted).

  It aborts on:
  - label/inkmap threshold inconsistency;
  - a labelled pixel outside render-valid;
  - a recovered band pixel outside [100, 150];
  - a shard hash or label mismatch with the cache.

  If a shard carries an explicit `valid` array, that array is used instead.
- **Base checkpoint:** step-075000.pth, sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab, VERIFIED (HF scrollprize/ink_9um rev 7109667; `out/setup_py3.log`).
- **Environment:** villa 41701aa, torch 2.14.0+cpu, Python 3.13 (vesuvius installed with `--ignore-requires-python`, as in TOOLING.md). The side libraries are the same versions as the amx pylib (`tools/sib/dev-lcsoft/setup_py.sh`).
- **Upstream unit tests:** 11 of 11 pass here (`out/pytest_upstream2.log`; the test file differs only in its path line).

## 3. Synthetic smoke (`smoke_synth.json`, `out/smoke_synth2.log`)
- **Setup:** 75 fake tiles, 3 segments of 5 x 5; fp16 feature cache; 20 steps per arm; 4 threads; fp32.

| arm | s/step (median) | loss step 1 → 20 | finite | notes |
|---|---|---|---|---|
| RECIPE | 0.360 | 0.731 → 0.696 | yes | soft targets |
| NULL | 0.362 | 0.726 → 0.699 | yes | derangement: 0 fixed points |
| REV | 0.376 | 0.749 → 0.697 | yes | reverse cache; identical soft targets |

- **Checks:**
  - NULL ≠ RECIPE and REV ≠ RECIPE final weights: yes.
  - Bitwise resume (10 steps, then die, then resume to 20) equals the uninterrupted run: yes (max abs diff 0.0).
  - The hard default path still runs.
  - soft_targets rejects an inconsistent tile.
- **Soft mask on the synthetic pool:**
  - 95.9 % of pixels supervised;
  - 189 760 band pixels recovered;
  - 45 888 band pixels dropped on tiles with valid24_frac < 1.
- Synthetic losses show only that the code runs. They carry no information about ink.

## 4. Cost estimates (4 threads, fp32)
- **Training:** 2000 steps x 0.36-0.38 s ≈ **0.20-0.21 h per arm**, or about **0.65 h for RECIPE + NULL + REV** with validation.
  - Real mmap reads of a larger cache may add IO time; the phase-2 log reports the measured s/step.
- **Feature cache:**
  - 0.12-0.18 s per tile per depth order;
  - 2.02 MB per tile per order at fp16.
  - For N pool tiles, both orders: ≈ 0.3 x N/1000 h of compute and 4.0 x N/1000 GB of disk.
  - Disk is the binding limit: 30 GB free caps both caches at about 6500 tiles. Above that, the forward cache is dropped after NULL, before REV is built. Nothing is deleted without approval (see ASK 3).
- **Soft target build:** negligible (IO only).
- **DEV maps:** these are produced via EVAL_API.md when it exists; not estimated here.
- **Undeclared unfrozen-encoder reading** (`bench_unfrozen.json`, cost only):
  - 7.67 s/step, 21x the frozen step, ≈ 4.3 h per 2000 steps per arm;
  - 4.1-4.7 s of that is the no-grad encoding of 64 neighbour tiles.
- **bf16:** not used. DECL-AMX-1 does not cover this recipe class (lr 1e-4 on the new modules).

## 5. Open items for phase 2 (details in ASK.md)
1. Confirm the recipe reading in section 1.
2. The 0139 shards have no explicit label-valid mask. The recovery rule above drops band pixels on partial-validity tiles.
3. The 0814 blockpairs are 384 px with ref9/valid, not the 128 px pairs0139 format that lc_cache reads. An adapter is needed if 0814 is in the training registry.
4. The hold-out list, training registry and METRIC-HASH are not yet available. The pool is built with lc_pool.py plus the frozen list, fail-closed.
