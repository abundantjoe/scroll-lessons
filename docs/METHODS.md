# Methods

This document describes the pipeline behind every read in this repository, from seed to ledger line, with every
parameter, constant and command. The pipeline is a quality-control instrument for ink-detection reads on Herculaneum
scroll segments. Nothing here reports a letter, a reading or ink on an eligible scroll. No PROMISING CANDIDATE has
ever been produced on an eligible scroll. **MEASURED** [`STATE.md:20`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L20) `@71720ce`

Related documents: results in [RESULTS](RESULTS.md), withdrawn and corrected claims in
[SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md), environments, checksums and commands in [REPRODUCE](REPRODUCE.md),
defects and their fixes in [LESSONS](LESSONS.md). The lab notebook itself is [`RULES.md`](../RULES.md); one line
per read is in [`LEDGER.md`](../LEDGER.md).

## Changed at release (2026-10-15)

- w040, the known-text control behind Gate A and R-CTRL55, is in the model's training set (section 1.3).
  **VERIFIED** [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`
- R-REPRO re-created Gate A and R-CTRL55 from public data in a fresh container. Both whole output maps are
  byte-identical to September's (sections 11 and 12). **VERIFIED** [`RULES.md:3283`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3283) `@eed0fac`
- R-HELDOUT ran the frozen pipeline on known text from PHerc0841, a scroll outside the training set (section 10.5).
  The pixel signal transfers: forward AUC 0.8393, reverse 0.5486. **MEASURED** [`RULES.md:3301`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3301) `@7925b3a`
  The frozen unit screen flags 1 of 60 valid units, and two code paths agree on the flags (0, 1 and 0 on the three
  segments). **VERIFIED**
  [`RULES.md:3306`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3306) `@7925b3a` [`RULES.md:3312`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3312) `@7925b3a`
- `disk_guard.sh`'s CT keep-list never matched, and `091c2fa` fixed it (section 9.3). Scripts read their data root
  from `$HERCULES_DATA`, and the shell scripts read the repository from `$HERCULES_ROOT` (section 9.8). **VERIFIED** [`scripts/disk_guard.sh:29`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L29) `@091c2fa`
  [`scripts/run_patch_dir.py:22`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/run_patch_dir.py#L22) `@fed6602`
- Team meshes that this pipeline renders get no `--flip-normals`. That covers every PHerc1203 surface and the
  PHerc1447 segments without a published render (section 5.2). **VERIFIED** [`scripts/vc_tools.sh:109`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L109) `@9600000`

## How to read this document

- **Labels.** Each factual statement carries one label. VERIFIED and MEASURED mean what they mean across the
  release (see [RESULTS](RESULTS.md)). This document adds configured parameters to MEASURED and declared rules to
  INFERENCE.
  - **VERIFIED**: reproduced by an independent code path or by a re-run, or re-checked for this release.
    "Reproduced" covers the September gates whose result was checked against an earlier or independent reference
    (section 11) and the 2026-10-15 reproduction (R-REPRO). "Re-checked" means a hash, arithmetic, an external file
    read on 2026-10-15, or a check run on 2026-10-15 against files or code already on record.
  - **MEASURED**: one recorded run, not independently repeated, or a configured parameter. It is a value as written
    in the notebook or in the code at the cited commit, not re-derived for this release. A new measurement made on
    2026-10-15 by a single code path, such as R-HELDOUT's pixel AUC, is MEASURED.
  - **INFERENCE**: a declared rule, a design decision, a statement carried over from the previous session's master
    prompt, an interpretation, or a projection.
- **Registration**, where a result is quoted: PRE-REGISTERED (bar committed before the result), EXPLORATORY or
  DESCRIPTIVE.
- **Citations.** `file:line` links to a permalink at commit `71720ce`; the short hash after it is the commit that
  introduced the text. Lines of `RULES.md` above 3202, and files or lines added after `71720ce`, are pinned to their
  introducing commit instead. Scripts edited after `71720ce` (for example by the portable-path change in `fed6602`)
  can sit at different line numbers in the current tree. For example, `disk_guard.sh` was rewritten around its
  keep-list in `091c2fa`. The permalinks resolve to the exact text cited.
  **VERIFIED** [`scripts/run_patch_dir.py:22`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/run_patch_dir.py#L22) `@fed6602`
- Numbers are copied from their sources. Where two sources disagree, both are given. The disagreements are
  collected in the [appendix](#appendix-source-conflicts-found-while-writing-this-document).

## Pipeline at a glance

| Stage | Script | Section |
|---|---|---|
| Seeds from the team's surface prediction | `scripts/seeds.py` | [2](#2-seeds) |
| Trace (stage 1) and consensus (stage 2) | `scripts/vc_tools.sh trace`, `scripts/vc_consensus.sh` | [3](#3-tracing) |
| Patch QC | `scripts/patch_qc.py` | [4](#4-patch-qc) |
| Render, 28 slices | `scripts/vc_tools.sh render` | [5](#5-rendering) |
| Crest pre-check, inference in both depth orders | `scripts/run_patch_dir.py` | [6](#6-inference) |
| Read, rule 5.5, contact sheet, ledger line | `scripts/read_chart.py`, `scripts/rule55.py` | [7](#7-reading), [8](#8-rule-55) |
| Integrity checks and operations | `map_integrity.py`, sweepers, `disk_guard.sh`, `supervisor.sh`, `ledger_audit.py` | [9](#9-integrity-and-operations) |
| Data and repository paths | `$HERCULES_DATA`, `$HERCULES_ROOT` | [9.8](#98-data-and-repository-paths) |
| Reproduction and held-out runs (2026-10-15) | `scripts/reproduce_control.sh`; `records/release/heldout_2026-10-15/prep.sh`, `run_infer.sh`; `scripts/rheldout.py` | [10.5](#105-rheldoutpy-r-heldout), [11](#11-validation-gates-summary) |

`run_patch_dir.py` chains QC, render, inference and read for every patch in a directory. Each stage writes a
completion marker, and a key that is already in `LEDGER.md` is skipped before any work. **MEASURED**
[`scripts/run_patch_dir.py:4`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L4) `@e3a0717` [`scripts/run_patch_dir.py:9`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L9) `@e3a0717`

---

## 1. Scope and data

### 1.1 The 23 eligible volumes

The master prompt lists 23 eligible volumes with their volume ids. Their pitch is 8.64 µm for 0175A, 0175B, 0268,
0306B, 0343, 0483A, 0483B, 0490A, 0490B, 0800, 1218 and 1447, and 9.362 µm for the rest. **INFERENCE** (copied from
the prize page as saved on 2026-09-11) [`docs/MASTER_PROMPT_v4.md:5`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L5) `@8a52745` [`docs/MASTER_PROMPT_v4.md:7`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L7) `@8a52745`

The supervisor's coverage list names nine of the 23 scrolls, with volume id, µm/px and pitch string.
**MEASURED** [`scripts/supervisor.sh:10`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L10) `@7bbb415`

| Scroll | Volume id | µm/px | In supervisor coverage list |
|---|---|---|---|
| PHerc0125 | 20250821151825 | 9.362 | |
| PHerc0175A | 20250521115057 | 8.64 | yes (`8.640um-1.2m-116keV`) |
| PHerc0175B | 20250521125822 | 8.64 | |
| PHerc0191 | 20250821151635 | 9.362 | yes (`9.362um-1.2m-113keV`) |
| PHerc0211 | 20250821151803 | 9.362 | |
| PHerc0257 | 20250821151750 | 9.362 | |
| PHerc0268 | 20251110183117 | 8.64 | |
| PHerc0306B | 20250521133212 | 8.64 | |
| PHerc0343 | 20250521140437 | 8.64 | yes (`8.640um-1.2m-116keV`) |
| PHerc0358 | 20250821151737 | 9.362 | yes (`9.362um-1.2m-113keV`) |
| PHerc0483A | 20250521140913 | 8.64 | |
| PHerc0483B | 20251124083638 | 8.64 | |
| PHerc0490A | 20250521151210 | 8.64 | |
| PHerc0490B | 20250521151215 | 8.64 | |
| PHerc0800 | 20250521135224 | 8.64 | yes (`8.640um-1.2m-116keV`) |
| PHerc0813 | 20250821151723 | 9.362 | yes (`9.362um-1.2m-113keV`) |
| PHerc0826 | 20250821151701 | 9.362 | yes (`9.362um-1.2m-113keV`) |
| PHerc0846A | 20250728152254 | 9.362 | |
| PHerc0846B | 20250804142305 | 9.362 | |
| PHerc1203 | 20250820131727 | 9.362 | yes (`9.362um-1.2m-113keV`) |
| PHerc1218 | 20250521120456 | 8.64 | |
| PHerc1447 | 20250521151220 | 8.64 | yes (`8.640um-1.2m-116keV`) |
| PHerc1545 | 20250821151648 | 9.362 | |

- PHerc0846A and PHerc1203 also have 2.403 µm rescans, volumes 20260319102732 and 20260319130212.
  **INFERENCE** [`docs/MASTER_PROMPT_v4.md:7`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L7) `@8a52745` Their surface predictions are computed at level 2 of the
  2.4 µm volume (about 9.6 µm voxels), and traces on them are in level-2 units. **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:22`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L22) `@8a52745`
- CT volumes are OME-zarr v2, levels 0..5 at scale 2^level, uint8, 128³ chunks, `/` separator, no compressor, axes
  z y x, zero outside the scroll. The team surface prediction used for seeds and tracing is
  `<vol>-surface-20260413222639-surface-m7-L0-th0.2.zarr` (uint8, 192³ chunks, blosc-zstd). **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:22`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L22) `@8a52745`
- µm/px is read from the volume's own `metadata.json` (`samplePixelSize` × 1000) and must agree with the catalogue
  within 0.005 × the catalogue value, or the run stops. **MEASURED** [`scripts/run_patch_dir.py:62`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L62) `@e3a0717`

### 1.2 Model and its training data

- Model: `scrollprize/ink_9um`, checkpoint `hybrid_3d2d-seed42/step-075000.pth` (the default) and
  `hybrid_3d2d-seed43/step-075000.pth`. The master prompt states it was trained on PHerc0139, PHerc1667,
  PHercParis4 and PHerc0814 renders at about 9.6 µm and that none of the 23 eligible scrolls is in its training data.
  **INFERENCE** [`docs/MASTER_PROMPT_v4.md:26`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L26) `@8a52745`
- R-HELDOUT names the same four training scrolls (0139, 1667, Paris4, 0814) from villa's training config.
  **VERIFIED** [`RULES.md:3247`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3247) `@661ff64`

### 1.3 Controls and their training-set status

| Control | Data | µm/px, slices | Used for | Training-set status |
|---|---|---|---|---|
| **w040** | PHerc0139 segment `20250831000000-w040_2025083102`, native stack 28×6400×7980, tifxyz mesh at scale 0.05 (one grid cell per 20 voxels); labels at Z=14 | 9.362, 28 | Gate A, Gate B, R-CTRL55, G-OWN, R-REPRO | **in the training set** |
| **w028** | PHerc1667 segment `20251208130119-w028_20251208130119156_flatboi`, 2.399 µm surface volume 109×37420×30340 (level 2 = 109×9355×7585); labels at Z=10 | 2.399 pooled by 4 planes to 21 slices at about 9.596 | Gate C, the w028 judge, the rule 5.5 self-test, B-2UM | **in the training set** |
| **PHerc0841** (held out) | three segments with `inklabels`, `supervision` and `validation` zarrs, 2.403 µm, level 2 pooled to 21 slices | 9.612, 21 | R-HELDOUT | not in the training config |

Sources for the table: w040 and w028 data **INFERENCE** [`docs/MASTER_PROMPT_v4.md:24`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L24) `@8a52745`
[`docs/MASTER_PROMPT_v4.md:25`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L25) `@8a52745` [`docs/MASTER_PROMPT_v4.md:38`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L38) `@8a52745`; PHerc0841 **VERIFIED**
[`RULES.md:3244`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3244) `@661ff64` [`RULES.md:3249`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3249) `@661ff64` [`RULES.md:3252`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3252) `@661ff64`.

- **w040 is a training-set sheet.** villa's training config for this checkpoint
  (`vesuvius/src/vesuvius/ink_detection/configs/aligned21_hybrid_3d2d.json` at `5ab585f`) lists w040 among its
  five native 9.362 µm training segments (w035, w039, w040, w041, w044) and `pherc0139-w040` among its aligned ones.
  The model card says "plus 5 native 9.362 µm segments from PHerc. 0139", and no `w040_validation_mask.zarr`
  exists in the label bucket. **VERIFIED** [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`
- Consequence: Gate A's AUC on w040 and R-CTRL55's 7/71 are measurements on a training-set sheet. They are a best
  case for the detector, not a held-out validation. **INFERENCE** [`RULES.md:3239`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3239) `@661ff64`
- The master prompt had already said that "w028 and w040 are in its training corpus, so label AUC measures
  memorisation". **INFERENCE** [`docs/MASTER_PROMPT_v4.md:38`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L38) `@8a52745` RULES applied that caveat to w028 (Gate C)
  and not to w040. **VERIFIED** [`RULES.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L35) `@8a52745` [`RULES.md:3241`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3241) `@661ff64` R-CTRL55's bar text and STATE.md
  call w040 "a sheet the model did not memorise" [`RULES.md:1391`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1391) `@dcf2553` [`STATE.md:144`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L144) `@cc9675b`. Those statements
  are superseded; see [SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md). **VERIFIED** [`RULES.md:3242`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3242) `@661ff64`
- The same config file is cited on 2026-09-18 for the model's `patch_size [17,128,128]`. Its training-segment list
  first appears in the notebook on 2026-10-15 (checked with `git log -S` on RULES, STATE, METHOD and CHANGELOG).
  **VERIFIED** [`RULES.md:96`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L96) `@92f139b` [`RULES.md:3235`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3235) `@661ff64`
- The frozen rule 5.5 levels were validated on w028 text, and w028 is in the training corpus. **MEASURED**
  [`RULES.md:341`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L341) `@2b23e09`

---

## 2. Seeds

`scripts/seeds.py` implements master-prompt section 5.6. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:40`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L40) `@8a52745`

| Parameter | Value | Source | Label |
|---|---|---|---|
| Prediction level read | level 3 (level-3 voxel = 8 level-0 voxels) | [`scripts/seeds.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L21) `@e3a0717` [`scripts/seeds.py:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L22) `@e3a0717` | MEASURED |
| Predicted voxel | value ≥ 128 | [`scripts/seeds.py:24`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L24) `@e3a0717` | MEASURED |
| Slices per z-band | 5 | [`scripts/seeds.py:26`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L26) `@e3a0717` | MEASURED |
| Radial classes | outer, middle, inner thirds by centroid-distance rank | [`scripts/seeds.py:27`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L27) `@e3a0717` [`scripts/seeds.py:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L6) `@e3a0717` | MEASURED |
| Minimum separation | ≥ 40 level-3 voxels, greedy farthest-first | [`scripts/seeds.py:25`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L25) `@e3a0717` [`scripts/seeds.py:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L6) `@e3a0717` | MEASURED |
| `--auto-bands` | three bands centred at 25 / 50 / 75 % of the level-0 z extent | [`scripts/seeds.py:122`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L122) `@e3a0717` | MEASURED |
| Band height | 1000 level-0 voxels | [`scripts/seeds.py:28`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L28) `@e3a0717` | MEASURED |
| Seeds per band | 30 (`--n-per-band` default) | [`scripts/seeds.py:230`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L230) `@e3a0717` | MEASURED |
| CT gate | candidate's level-4 CT value > 0 | [`scripts/seeds.py:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L23) `@e3a0717` [`RULES.md:134`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L134) `@e3a0717` | MEASURED |
| Density gate (declared) | level-3 prediction density ≤ 0.20 in a 31 px window: `--max-density 0.20 --density-window 31` | [`RULES.md:138`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L138) `@604d137` | INFERENCE |
| Density gate (code defaults) | `--max-density` default `None`, `--density-window` default 15 | [`scripts/seeds.py:238`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L238) `@46f2b7f` [`scripts/seeds.py:240`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L240) `@604d137` | MEASURED |
| Order | outer → middle → inner | [`RULES.md:138`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L138) `@604d137` | INFERENCE |
| Output | level-0 (x, y, z) = (col×8, row×8, slice×8) | [`docs/MASTER_PROMPT_v4.md:40`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L40) `@8a52745` | INFERENCE |
| Cache namespace | `sha1(base)[:12]` of the source URL | [`scripts/seeds.py:54`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L54) `@c2cafd6` | MEASURED |

- **The density gate.** The gate is active only when the flags are passed, because the code defaults switch it off.
  **MEASURED** [`scripts/seeds.py:238`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L238) `@46f2b7f` The seed files on record carry the declared values: `max_density`
  0.2 and `density_window_px` 31 in `seeds/PHerc0826.json`, `seeds/PHerc0358.json` and `seeds/PHerc0175A.json`.
  **VERIFIED**
  [`seeds/PHerc0826.json:9`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0826.json#L9) `@7f47c64` [`seeds/PHerc0826.json:10`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0826.json#L10) `@7f47c64` [`seeds/PHerc0358.json:10`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0358.json#L10) `@604d137`
  [`seeds/PHerc0175A.json:10`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0175A.json#L10) `@ca7034c` The R-SMALL-2 seed file uses `max_density` 0.3. **VERIFIED**
  [`seeds/PHerc0826_rsmall2.json:5`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0826_rsmall2.json#L5) `@6582782`
- **Calibration of the gate (EXPLORATORY).** On 53 traced seeds, all 15 traces that produced a read sat at
  density ≤ 0.20 (median 0.105), and 16 of 23 VOID traces sat above 0.20 (median 0.224, up to 0.36). **MEASURED**
  [`RULES.md:137`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L137) `@604d137` The thresholds were set after looking at these seeds, and no success bar was declared
  for the before/after comparison. **INFERENCE** [`RULES.md:138`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L138) `@604d137`
- **Effect (EXPLORATORY, one scroll).** On PHerc0358, ten ungated traces gave 10 % readable and 80 % VOID.
  Seventeen gated traces gave 59 % readable and 6 % VOID, and QC rejections rose from 10 % to 35 %. **MEASURED**
  [`RULES.md:139`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L139) `@5757b34`
- **CT gate.** It was added after 7 of 12 PHerc0306B smoke seeds fell off the CT. **MEASURED**
  [`RULES.md:134`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L134) `@e3a0717`
- **Window size conflict.** RULES and METHOD give the 31 px window as 2.9 mm [`RULES.md:137`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L137) `@604d137`
  [`METHOD.md:12`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L12) `@0821bc2`. The `seeds.py` help text says "31 = 2.4 mm at 9.4 um scans"
  [`scripts/seeds.py:240`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L240) `@604d137`. The files do not resolve this. **MEASURED**

---

## 3. Tracing

### 3.1 Stage 1: `vc_grow_seg_from_seed`

- The rebuilt VC3D tools run inside `ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04`.
  **MEASURED** [`scripts/vc_tools.sh:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L16) `@e3a0717`
- Params JSON written to the patches directory:
  `{"mode":"seed","min_area_cm":0.2,"generations":${TRACE_GENERATIONS:-60},"thread_limit":2,"cache_root":…,"direction_fields":[],"voxelsize":<µm>,"normal_grid_path":…}`.
  **MEASURED** [`scripts/vc_tools.sh:72`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L72) `@a84210e`
- Command: `/opt/vc/bin/vc_grow_seg_from_seed --volume s3://vesuvius-challenge-open-data/<scroll>/representations/predictions/surfaces/<vol>-surface-20260413222639-surface-m7-L0-th0.2.zarr/ --target-dir <patches> --params params.json --seed X Y Z`
  (seed in level-0 CT voxels). **MEASURED** [`scripts/vc_tools.sh:77`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L77) `@e3a0717` [`scripts/vc_tools.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L19) `@ea157e8`
- The tracer container runs with 2 OpenMP threads. **MEASURED** [`scripts/vc_tools.sh:76`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L76) `@e3a0717`
- **Normal grids.** The script writes `normal-grids-remote.json` with the URL of the published
  `...-surface-m7-L0-th0.2.normal-grids` store, fetches the store's `metadata.json`, and the tool then fetches grid
  files lazily. **MEASURED** [`scripts/vc_tools.sh:64`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L64) `@e3a0717` The master prompt makes normal grids mandatory: without
  them the tracer is 100× faster and its surfaces cut across windings. **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:41`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L41) `@8a52745` METHOD gives mean |n_z| 0.75-0.83 for traces without grids, a
  previous-session figure; no re-run is recorded. **MEASURED** (DESCRIPTIVE) [`METHOD.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L19) `@0821bc2`
- Output: `auto_grown_<timestamp>/{x,y,z}.tif + meta.json`, float32 level-0 coordinates, one grid cell per 20
  voxels, about 4 cm² after 60 generations, 30-90 min per patch. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:41`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L41) `@8a52745`

**Generations.** 60 is the default and the budget of every standard trace. **MEASURED**
[`scripts/vc_tools.sh:71`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L71) `@a84210e` [`scripts/vc_tools.sh:73`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L73) `@a84210e` Reduced interior budgets were tested and not adopted:

| Budget | Outcome | Label | Source |
|---|---|---|---|
[line withheld: prize-candidate detail under review]
| 40 (R-SMALL, bar ≥ 30 % readable over ≥ 15 outcomes) | 3 of 15 = 20.0 % at the declared 15th outcome: FAIL | MEASURED (PRE-REGISTERED) | [`RULES.md:699`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L699) `@57cc4ae` |
| 40, complete population | 3 of 19 = 15.8 % (21.4 % of the 14 past QC): FAIL; budget back to 60 | MEASURED (PRE-REGISTERED) | [`RULES.md:1838`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1838) `@f729860` [`RULES.md:1839`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1839) `@f729860` [`RULES.md:1842`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1842) `@f729860` |

METHOD.md still quotes the 20.0 % figure. **MEASURED** [`METHOD.md:97`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L97) `@bf7c7f9`

**Concurrency.** RULES records a decision of one trace slot (`TRACERS=1`, `TRACE_SLOTS=1`) with the prediction that
the next five 40-generation traces would take under 400 s each. No outcome of that prediction is recorded.
**INFERENCE** (EXPLORATORY) [`RULES.md:329`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L329) `@ce886a7` The supervisor now exports `TRACE_SLOTS` with default 2
("G-GP part 4 is all on one scroll") and `TRACERS` default 1, and METHOD describes a two-slot pool. No RULES entry
reverting to two slots was located. **MEASURED** [`scripts/supervisor.sh:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L18) `@2a7f98e`
[`scripts/supervisor.sh:17`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L17) `@ce886a7` [`METHOD.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L19) `@0821bc2`

### 3.2 Stage 2: consensus surfaces, `vc_grow_seg_from_segments`

- The team's published PHerc1447 `team_z_dbg_gen_*` segments carry `vc_grow_seg_from_segments_params`
  `consensus_default_th` 6, `consensus_limit_th` 2, `flip_x` false, `global_steps_per_window` 2, `step` 6.
  **MEASURED** (DESCRIPTIVE) [`RULES.md:604`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L604) `@731b16f`
- `scripts/vc_consensus.sh` writes these values verbatim, plus `thread_limit` `${VC_THREADS:-2}`, `voxelsize`,
  `cache_root`, `normal_grid_path` and `direction_fields []`:

| Parameter | Value | Source |
|---|---|---|
| `consensus_default_th` | `${CONSENSUS_TH:-6}` | [`scripts/vc_consensus.sh:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L21) `@a53d62d` |
| `consensus_limit_th` | 2 | [`scripts/vc_consensus.sh:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L22) `@a53d62d` |
| `flip_x` | false | [`scripts/vc_consensus.sh:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L23) `@a53d62d` |
| `global_steps_per_window` | 2 | [`scripts/vc_consensus.sh:24`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L24) `@a53d62d` |
| `step` | 6 | [`scripts/vc_consensus.sh:25`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L25) `@a53d62d` |

  **MEASURED**
- The tool opens its volume with the local-only `VcDataset`, so the prediction store has to be materialised on
  disk. **MEASURED** [`scripts/vc_consensus.sh:39`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_consensus.sh#L39) `@b562c8f` Chunks are 192³ and about 449 KB, about 600 MB for a
  2112³ box. **MEASURED** (DESCRIPTIVE) [`METHOD.md:84`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L84) `@bf7c7f9`
- `ggp4_consensus.sh` passes the threshold with default 6. **MEASURED** [`scripts/ggp4_consensus.sh:11`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/ggp4_consensus.sh#L11) `@08b7f68`
- Threshold sweep 4 / 6 / 8 / 10 (PRE-REGISTERED prediction: fill rises and area falls with the threshold). At 6
  the 86-source grid was 174×258 with 22 228 valid nodes, grid fill 0.495 and 9.52 cm², the best of the four.
  The prediction was refuted. **MEASURED** [`RULES.md:2677`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2677) `@3adee87` RULES concludes that the team's value 6 is
  optimal on three axes (area, grid fill, mid-plane landing). **INFERENCE** [`RULES.md:2867`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2867) `@7fdf466`
- Node-count conflict for the same part-5 surface: 20 692 nodes [`RULES.md:2169`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2169) `@b513b83` against 22 228 valid
  nodes [`RULES.md:2677`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2677) `@3adee87`. The files do not reconcile them. **MEASURED**

### 3.3 Team segments

- Three eligible volumes publish segments in the open-data bucket: PHerc1447 (53 surfaces), PHerc1203 (22) and
  PHerc0800 (6). `fetch_team_segments.py` takes the flattened mesh variant when it exists and stores each surface as
  `team_<uuid>`. **MEASURED** [`scripts/fetch_team_segments.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_team_segments.py#L7) `@97dacf5`
  [`scripts/fetch_team_segments.py:14`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_team_segments.py#L14) `@97dacf5` The subject line of the commit that added the script
  ([`97dacf5`](https://github.com/abundantjoe/hercules/commit/97dacf5)) says "87 published surfaces", which does not
  equal the sum of the docstring's per-scroll counts. **MEASURED**
- PHerc1447 (15) and PHerc0800 (6) also publish the team's own renders of their segments ("surface volumes", 31
  slices, uint8). These are fetched and used in place of a render of ours. PHerc1203 publishes none, so its surfaces
  are rendered by this pipeline. **MEASURED** [`scripts/fetch_surface_volumes.py:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L6) `@f600d41`
  [`scripts/fetch_surface_volumes.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L7) `@f600d41` [`scripts/fetch_surface_volumes.py:8`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L8) `@f600d41`
  [`docs/MASTER_PROMPT_v4.md:23`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L23) `@8a52745`
- PHerc1447 publishes surface volumes for only 15 of its 53 segments, so this pipeline renders its other team
  segments too. In `records/throughput.jsonl`, 29 PHerc1447 `team_*` patches carry a render time of their own
  (`s_render` > 0). They include all nine PHerc1447 members of R-CREST-POWER phase 1, for example
  `team_z_dbg_gen_00701` with `s_render` 338.9 s. **VERIFIED** (counted on 2026-10-15)
  [`records/throughput.jsonl:192`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L192) `@201e3c0` [`records/rcrest_power_phase1.txt:4`](https://github.com/abundantjoe/hercules/blob/71720ce/records/rcrest_power_phase1.txt#L4) `@ca7034c`
- RULES records that every published team segment on the 23 eligible volumes has been read. **INFERENCE**
  [`RULES.md:2130`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2130) `@a2634d3`

---

## 4. Patch QC

`scripts/patch_qc.py` (master-prompt section 5.8) runs before any render. Its verdict is PASS, FAIL or UNREADABLE,
and only a PASS proceeds. **MEASURED** [`scripts/run_patch_dir.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L5) `@e3a0717`

| Check | Rule | Source | Label |
|---|---|---|---|
| Normals | per-cell normal = cross(u difference, v difference) of the tifxyz grid | [`scripts/patch_qc.py:3`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L3) `@e3a0717` | MEASURED |
| Geometry bars | mean \|n_z\| ≤ 0.50 AND fraction(\|n_z\| > 0.7) ≤ 0.25 AND area ≥ 0.5 cm² | [`scripts/patch_qc.py:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L19) `@a2170dd` | MEASURED |
| CT-mask sampling | 100 well-spread valid points at CT level 4 (coordinates ÷ 16, axes z y x); overlay slab ±8 level-0 voxels | [`scripts/patch_qc.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L20) `@a2170dd` [`scripts/patch_qc.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L5) `@e3a0717` | MEASURED |
| CT-mask arm 1 | `zero_frac` ≤ 0.50 | [`scripts/patch_qc.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L20) `@a2170dd` | MEASURED |
| CT-mask arm 2 (in-mask area) | `(1 - zero_frac) * area_cm2` ≥ 1.5 cm² | [`scripts/patch_qc.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L21) `@adcd3d6` [`RULES.md:144`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L144) `@adcd3d6` | MEASURED |
| 2.4 µm traces | `--coord-scale 4` (level-0 CT voxels per coordinate unit) | [`scripts/patch_qc.py:245`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/patch_qc.py#L245) `@a2170dd` | MEASURED |

- The scroll axis is z and a winding's normals lie in the xy plane. The master prompt's reference values are w040
  mesh 0.25 / 0.06 (PASS) and 0.75-0.83 for patches grown without grids (FAIL). Both are previous-session figures
  and no re-run is recorded. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:42`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L42) `@8a52745`
- **Why the area arm exists.** Over all 151 QC'd patches the `ct.zero_frac` histogram in 0.1 bins is
  67, 1, 13, 18, 14 | 18, 5, 8, 5, 2: a continuum with no gap near the 0.50 bar. **MEASURED** (DESCRIPTIVE)
  [`RULES.md:143`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L143) `@adcd3d6` A patch now proceeds when either arm holds. This made 20 traces and 4 published PHerc1447
  surfaces readable and kept every previously readable patch readable. **MEASURED** [`RULES.md:144`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L144) `@adcd3d6`
- **Validation of the area arm.** The target declared before the runs was median `onsheet_cm2 / in_mask_cm2` ≥ 0.5
  over admitted patches, otherwise the arm is withdrawn. No evaluation of it is recorded. **INFERENCE**
  (PRE-REGISTERED, no outcome) [`RULES.md:146`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L146) `@adcd3d6`
- **Published renders.** The level-4 CT-mask proxy rejected most of the team's curated PHerc1447 surfaces
  (`zero_frac` 0.42-0.86 across 13 surfaces). **MEASURED** [`RULES.md:102`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L102) `@2fc94c5` For patches with a published
  render only, the CT-mask proxy is superseded: the read proceeds and `zero_frac` is recorded. A geometry FAIL and
  R-CREST still stop a patch. **INFERENCE** [`RULES.md:104`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L104) `@2fc94c5` The justification relies on Gate B showing the
  renderer reproduces such stacks "pixel for pixel" [`RULES.md:103`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L103) `@2fc94c5`; Gate B's own result says "not
  bit-exact" [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22`. **MEASURED** See [5.3](#53-the-rebuilt-renderer-and-why).

---

## 5. Rendering

### 5.1 The render command

`vc_tools.sh render` builds this argument vector (MEASURED, [`scripts/vc_tools.sh:107`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L107) `@e3a0717`
[`scripts/vc_tools.sh:108`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L108) `@158efec` [`scripts/vc_tools.sh:109`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L109) `@9600000` [`scripts/vc_tools.sh:106`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L106) `@9600000`):

```
/opt/vc/bin/vc_render_tifxyz --volume <cache dir>
  --remote-url s3://vesuvius-challenge-open-data/<scroll>/volumes/<vol>-<pitch>-masked.zarr/
  --segmentation <patch dir> --zarr-output <render.zarr>
  --scale 1 --group-idx ${RENDER_GROUP:-0} --num-slices ${RENDER_SLICES:-28}
  --slice-step 1 --cache-gb ${VC_RENDER_CACHE_GB:-4} --voxel-size <µm> --voxel-unit micrometer
  [--auto-crop] --pyramid 0
```

`--auto-crop` is on unless `RENDER_AUTOCROP=0`, and `RENDER_ARGS` can add flags (the 2.4 µm route uses this).
**MEASURED** [`scripts/vc_tools.sh:103`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L103) `@158efec` [`scripts/vc_tools.sh:104`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L104) `@9600000` [`scripts/vc_tools.sh:106`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L106) `@9600000`

| Item | Value | Source | Label |
|---|---|---|---|
| Slices | 28 (`RENDER_SLICES` default) | [`scripts/vc_tools.sh:108`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L108) `@158efec` | MEASURED |
| Render cache | 4 GB by default (`vc_tools.sh` comment: "4 on this 15 GB box (task instruction)"); master prompt 5.9 says 8 | [`scripts/vc_tools.sh:24`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L24) `@e3a0717` [`docs/MASTER_PROMPT_v4.md:43`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L43) `@8a52745` | MEASURED |
| `--pyramid 0` | added only to skip pyramid levels | [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22` | MEASURED |
| All-zero render | treated as a transient fetch failure; re-rendered, give up after 3 attempts | [`scripts/vc_tools.sh:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L23) `@e3a0717` [`scripts/vc_tools.sh:116`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L116) `@e3a0717` | MEASURED |
| Free-disk floor | no render below 5.0 GB free | [`scripts/run_patch_dir.py:90`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L90) `@54aaf83` | MEASURED |
| Markers | deleting a render must drop both completion markers, or a re-read silently skips rendering | [`METHOD.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L29) `@0821bc2` | INFERENCE |

### 5.2 `--flip-normals`

- The fixed Gate B command renders the w040 team mesh with `--flip-normals`. **MEASURED** [`RULES.md:22`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L22) `@8a52745`
- The master prompt states that the model is not depth-order invariant, that `--flip-normals` gives the trained
  orientation on the team's renders, and that on our own patches the orientation is unknown, so both orders are
  always read. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745`
- Our own patches are rendered with no `--flip-normals`, and a test asserts that the flag is absent. **MEASURED**
  [`scripts/vc_tools.sh:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L6) `@e3a0717` [`scripts/tests/test_vc_tools.py:66`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_vc_tools.py#L66) `@e3a0717`
- Team meshes: where the team published a surface volume (PHerc1447: 15 of its 53 segments; PHerc0800: 6),
  that render is read as published (section 3.3). Every other team mesh goes through `vc_tools.sh render`, which
  passes no `--flip-normals`. That means every PHerc1203 surface and the PHerc1447 segments without a published
  volume, including all nine PHerc1447 `team_z_dbg_gen_*` members of R-CREST-POWER phase 1 (for example
  `team_z_dbg_gen_00701`, `s_render` 338.9 s). **VERIFIED**
  [`scripts/fetch_surface_volumes.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L7) `@f600d41` [`scripts/fetch_team_segments.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_team_segments.py#L7) `@97dacf5`
  [`records/rcrest_power_phase1.txt:4`](https://github.com/abundantjoe/hercules/blob/71720ce/records/rcrest_power_phase1.txt#L4) `@ca7034c` [`records/throughput.jsonl:192`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L192) `@201e3c0`
  [`scripts/vc_tools.sh:109`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L109) `@9600000` No script in the repository passes `--flip-normals` (checked with `grep` on
  2026-10-15); the only render command with it in the notebook is Gate B's. **VERIFIED**
  [`RULES.md:22`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L22) `@8a52745`
- Consequence: for the team meshes this pipeline renders, the ledger's "forward" map is presumably the reverse of
  the trained orientation. **INFERENCE** The direction rests on one observation: the published image, which lacks
  the flag, rendered the w040 team mesh to a stack that matched the team's only with the slice order reversed
  (Pearson 0.42-0.82 per slice). **MEASURED** (EXPLORATORY) [`RULES.md:28`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28) `@2e62892` No verdict on record depends
  on it, because both orders are always read and neither order flags a unit on these meshes. **INFERENCE** The 11
  complete R-CREST-POWER phase-1 members, all rendered by this pipeline, have 0 of 190 valid units flagged in either
  order. Their PHerc1203 half has a swapped table of 0 of 64, and the tripwire never fired. **MEASURED**
  [`STATE.md:33`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L33) `@71720ce` [`RULES.md:3127`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3127) `@f9bfe3b` Over all 52 earlier reads that carry the swapped table, the tripwire
  never fired either. **MEASURED** [`RULES.md:2364`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2364) `@8f49fce`
- Orientation is handled by reading both depth orders and by the swapped-table tripwire ([7](#7-reading)). RULES
  states that the swapped table is exactly the `+flip` read. **INFERENCE** [`RULES.md:2833`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2833) `@d29112c`

### 5.3 The rebuilt renderer, and why

- The published image `ghcr.io/scrollprize/villa/volume-cartographer:edge` (= `main`, built 2026-05-13, villa
  `1e3f4c0`) has no `--flip-normals`, which was added on 2026-06-17. A 256×256 smoke render of the w040 mesh with
  it matched the team stack only with the slice order reversed, at Pearson 0.42-0.82 per slice (identical-pixel
  fraction 0.40). The tools were therefore rebuilt from villa `5ab585f`. **MEASURED** (EXPLORATORY)
  [`RULES.md:28`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28) `@2e62892`
- Build: `scripts/build_vc3d.sh` inside `ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04`,
  targets `vc_render_tifxyz vc_grow_seg_from_seed vc_flatten vc_tifxyz2obj vc_obj2tifxyz vc_gen_normalgrids
  vc_tifxyz_trim`. `build_vc3d_extra.sh` adds `vc_tifxyz_selfcross vc_tifxyz_winding vc_grow_seg_from_segments`.
  **MEASURED** [`scripts/build_vc3d.sh:9`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/build_vc3d.sh#L9) `@2e62892` [`scripts/build_vc3d.sh:11`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/build_vc3d.sh#L11) `@2e62892`
  [`scripts/build_vc3d_extra.sh:14`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/build_vc3d_extra.sh#L14) `@31bcef3`
- villa checkout: `5ab585ffee54331a3362b9ce6b2929b20dcde2c6`, committed 2026-09-16T17:51:11+00:00. **MEASURED**
  [`RULES.md:1969`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1969) `@7e56299` The master prompt says villa was validated at `be09a85`; no run at `be09a85` is
  recorded. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:27`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L27) `@8a52745`
- Gate B Bar 1 (PRE-REGISTERED, Pearson ≥ 0.999 on every slice): the rebuilt renderer matched the team stack on
  the 2048×2048 crop at Pearson min 0.999999 over 28 slices, identical-pixel fraction min 0.9956, mean |diff|
  0.0029 grey levels. The result itself says "not bit-exact". PASS. **VERIFIED** [`RULES.md:24`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L24) `@8a52745`
  [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22`
- Re-checked on 2026-10-15: `:edge` is still the 2026-05-13 build (revision
  `1e3f4c021f4e53bea3867772ed05f51a7e586a9c`). Its `vc_render_tifxyz --help` lists no `--flip-normals`, and running
  it with `--flip-normals` prints `Error: unrecognised option '--flip-normals'` and exits 1. **VERIFIED**
  [`records/release/edge_image_check_2026-10-15.md:8`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L8) `@0afc07e`
  [`records/release/edge_image_check_2026-10-15.md:14`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L14) `@0afc07e`
  [`records/release/edge_image_check_2026-10-15.md:15`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L15) `@0afc07e`
- Overstatement downstream: later text and a docstring describe the renderer as reproducing team stacks "pixel for
  pixel" [`RULES.md:103`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L103) `@2fc94c5` [`scripts/fetch_surface_volumes.py:11`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L11) `@f600d41`, which goes beyond Bar 1's
  identical-pixel fraction of 0.9956 [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22`. **MEASURED**
- The October reproduction (R-REPRO) ran the model on the native w040 stack and did not re-run the renderer.
  **INFERENCE** [`RULES.md:3210`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3210) `@c700273` [`RULES.md:3219`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3219) `@c700273`

### 5.4 The 2.4 µm route (B-2UM)

Renders for the 2.4 µm model use `--scale-segmentation 4 --num-slices 64 --slice-step 1 --voxel-size 2.403
--voxel-unit micrometer --auto-crop`. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:57`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L57) `@8a52745` The runner uses a tile of
256, stride 128, checkpoint `r152_3ddec_v2_l5_epoch13.ckpt`, and the centred 62-layer window (layers 23..85 of 109).
**INFERENCE** (PRE-REGISTERED) [`RULES.md:67`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L67) `@b3503fc` This project made no 2.4 µm map of an eligible trace (the earlier effort it started from ran one PHerc0846A patch
forward only, verdict NOT ESTABLISHED: [`docs/MASTER_PROMPT_v4.md:53`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L53) `@8a52745`). The one PHerc0846A
rescan trace that passed the crest pre-check was stopped as VOID-COVER at 0/1024 tiles, and no sheet-following trace of
the rescan exists (0 of 14). **MEASURED** [`LEDGER.md:76`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L76) `@4d495d8` [`RULES.md:71`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L71) `@507a137`

---

## 6. Inference

### 6.1 The call

`run_patch_dir.py` builds the call (MEASURED, [`scripts/run_patch_dir.py:102`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L102) `@e3a0717`
[`scripts/run_patch_dir.py:105`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L105) `@f0ff387` [`scripts/run_patch_dir.py:106`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L106) `@f0ff387` [`scripts/run_patch_dir.py:107`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L107) `@2141cdb`):

```
python -m vesuvius.ink_detection.inference.infer <render.zarr> <ckpt.pth> <out.tif>
  --direction both [--tta-mirror] [depth-window layer args]
  --batch-size 4 --no-compile --num-workers ${HERCULES_INFER_WORKERS:-2}
```

- Screening reads use checkpoint `hybrid_3d2d-seed42/step-075000.pth`, tag `ink9um_seed42+plain`, and `--no-tta`.
  **MEASURED** [`scripts/supervisor.sh:64`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L64) `@98b6952` [`scripts/run_patch_dir.py:32`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L32) `@e3a0717`
- The master prompt's fixed call adds `--tta-mirror --gpus 0 --num-workers 3`. **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745` `--gpus` is dropped on this CPU box. **MEASURED**
  [`scripts/run_patch_dir.py:102`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L102) `@e3a0717` Screening dropped `--tta-mirror` with the reading-recipe declaration.
  **INFERENCE** (PRE-REGISTERED) [`RULES.md:119`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L119) `@98b6952`
- Checkpoint integrity (R-REPRO, 2026-10-15): sha256 `e635558a...`, equal to the Hugging Face LFS record (repo
  revision 7109667e). **VERIFIED** [`RULES.md:3214`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3214) `@c700273`
- Worker-count conflict: METHOD and the R-REPRO call use `--num-workers 3` [`METHOD.md:37`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L37) `@0821bc2`
  [`RULES.md:3219`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3219) `@c700273`. The pipeline default has been 2 since 2026-09-19 [`scripts/run_patch_dir.py:98`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L98) `@2141cdb`.
  RULES states that worker count affects throughput only. **INFERENCE** (not demonstrated in the files)
  [`RULES.md:1818`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1818) `@2141cdb`
- Output: uint8 TIFF = probability × 255. `--direction both` also writes `<out>_reverse.tif`, the same stack with
  the slice order flipped. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745`

### 6.2 What the model sees

- The model consumes exactly 17 slices (`patch_size [17,128,128]`). `center_crop_layer_indices` crops a 28-slice
  render to indices **6..22**, so slices 0-5 and 23-27 never reach the network. **MEASURED** (DESCRIPTIVE)
  [`RULES.md:96`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L96) `@92f139b`
- Inside villa: robust-MAD 1-99 % normalisation, patch 128, stride 64, Hann blending. **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745`
- Depth windows (R-DEPTH), locked to the ledger depth-offset field:

| Window | Layer arguments | Ledger offset | Centre slice | Source |
|---|---|---|---|---|
| centre (default) | none (indices 6..22, see above) | 0 | 14 | [`scripts/run_patch_dir.py:38`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L38) `@f0ff387` |
| low | `--layer-start 0 --layer-end 17` | -6 | 8 | [`scripts/run_patch_dir.py:39`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L39) `@f0ff387` |
| high | `--layer-start 11 --layer-end 28` | +5 | 19 | [`scripts/run_patch_dir.py:40`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L40) `@f0ff387` |

  **MEASURED.** R-DEPTH (PRE-REGISTERED) failed. Best off-centre minus centre was -0.06860 against the +0.05 bar, and
  worst off-centre over centre was 0.6619 against ≤ 0.50. The centre window stays. **MEASURED**
  [`RULES.md:409`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L409) `@b688eb7` [`RULES.md:2007`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2007) `@0423a76` [`RULES.md:2008`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2008) `@0423a76` An earlier ADMITTED verdict rested
  on a truncated map and was withdrawn [`RULES.md:1618`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1618) `@750629f`. The code comment above the table still read "ADMITTED" at `71720ce`
  [`scripts/run_patch_dir.py:34`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L34) `@f0ff387` and was corrected in `e993fbe` [`scripts/run_patch_dir.py:35`](https://github.com/abundantjoe/hercules/blob/e993fbe/scripts/run_patch_dir.py#L35) `@e993fbe`.
  **VERIFIED**

### 6.3 Plain versus TTA

| Recipe | Where used | Source | Label |
|---|---|---|---|
| Plain (`--direction both`, no `--tta-mirror`), tag `ink9um_seed42+plain` | every screening read from the reading-recipe declaration on | [`RULES.md:119`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L119) `@98b6952` | INFERENCE (PRE-REGISTERED) |
| TTA (`--tta-mirror`) | candidates, plus the 31 reads made before the recipe change | [`scripts/run_patch_dir.py:91`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L91) `@98b6952` [`RULES.md:118`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L118) `@98b6952` [`METHOD.md:46`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L46) `@0821bc2` | MEASURED |

- `--tta-mirror` averages 4 mirror variants in y and x; depth is not mirrored. **MEASURED** (DESCRIPTIVE)
  [`RULES.md:131`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L131) `@73eb297`
- TTA was promoted on 2026-09-12 (w028 judge 0.784 to 0.823, w040 regression 0.990). **MEASURED** (previous session)
  [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745` On the Gate B crop, TTA lowers forward AUC from 0.99680 to 0.99024.
  **VERIFIED** [`RULES.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L30) `@e3a0717` On the w028 judge it raises AUC from 0.7842 to 0.8224. **VERIFIED**
  [`RULES.md:44`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L44) `@aa32a21` [`RULES.md:108`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L108) `@f66337f` The full-canvas Gate A TTA pass was stopped after 2 h 36 min, and
  no result is recorded. **MEASURED** [`RULES.md:115`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L115) `@6542709`
- TTA cost, three conflicting statements: "~2.5× a plain pass" [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745`, "TTA costs
  4x" [`METHOD.md:39`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L39) `@0821bc2`, plain at "a quarter of the inference cost" [`RULES.md:119`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L119) `@98b6952`. The only
  timing on record is not like-for-like: on a 512×512 w040 crop (49 patches, 4 cores), forward-only plain took 16 s
  including model load and `--direction both --tta-mirror` took 61 s. **MEASURED** [`RULES.md:131`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L131) `@73eb297`

### 6.4 The seed43 confirmatory reader

- Role, fixed before the numbers: seed43 is confirmatory only. It never flags or un-flags a unit, and no threshold,
  screening tag or verdict depends on it. **INFERENCE** [`RULES.md:171`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L171) `@3fc9e3d`
- Admission bar (G-B-43, PRE-REGISTERED), on the Gate B render, plain call, both orders: forward AUC ≥ 0.95, margin
  on labelled ink ≥ +0.30, margin on labelled blank ≤ +0.05. **INFERENCE** [`RULES.md:172`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L172) `@3fc9e3d`
  [`RULES.md:173`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L173) `@3fc9e3d` [`RULES.md:175`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L175) `@3fc9e3d`
- Result: forward AUC 0.99562, ink margin +0.45806, blank margin -0.03637 (reverse AUC 0.52689). PASS.
  **MEASURED** [`RULES.md:285`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L285) `@c7ef931`
- RULES then says the two seeds "agree on this surface to within 0.001 of AUC and 0.01 of ink margin"
  [`RULES.md:286`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L286) `@c7ef931`. The recorded pairs are 0.99562 vs 0.99680 and +0.45806 vs +0.4681
  [`RULES.md:285`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L285) `@c7ef931`, and each differs by more than the stated tolerance. **MEASURED**
- seed43 had been retired as a screening checkpoint on the w028 judge (0.781 against 0.784). **MEASURED**
  [`RULES.md:42`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L42) `@8a52745`
- Use: protocol 9 step 6 re-reads a candidate with `--ckpt .../hybrid_3d2d-seed43/step-075000.pth --tag
  ink9um_seed43+tta` (TTA on). **MEASURED** [`scripts/protocol9.sh:54`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/protocol9.sh#L54) `@0b06530` [`scripts/protocol9.sh:55`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/protocol9.sh#L55) `@0b06530`
  RULES specifies the same re-read with tag `ink9um_seed43+plain`; see [appendix](#appendix-source-conflicts-found-while-writing-this-document) row 22.
  **MEASURED** [`RULES.md:286`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L286) `@c7ef931`
  Protocol 9 has not been run on an eligible candidate, because none exists. **INFERENCE** [`STATE.md:20`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L20) `@71720ce`
  Its dry-run rehearsal found and fixed a path bug in step 6. **VERIFIED** [`RULES.md:1718`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1718) `@eeb9fc6`

---

## 7. Reading

`scripts/read_chart.py` (master-prompt section 5.10) works on existing model output and never runs the model.
Its inputs are the render zarr (or, with `--maps-only`, an on-sheet mask image) and the two uint8 maps, which are
never resampled. **MEASURED** [`scripts/read_chart.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L5) `@5ca0c22`

### 7.1 Order of operations and constants

| Step | Rule | Source | Label |
|---|---|---|---|
| 1. Key check | `--key` must have exactly 4 pipes: `scroll\|surface\|depth offset\|checkpoint+TTA\|order` | [`scripts/read_chart.py:203`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L203) `@5ca0c22` [`scripts/read_chart.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L21) `@5ca0c22` | MEASURED |
| 2. Refusal | a key already in `LEDGER.md` is REFUSED unless `--reason` is given | [`scripts/read_chart.py:206`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L206) `@5ca0c22` | MEASURED |
| 3. On-sheet mask | CT mid slice (index `nz // 2`) > 0; with `--maps-only`, the given mask > 0 | [`scripts/read_chart.py:212`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L212) `@5ca0c22` | MEASURED |
| 4. Truncated-map guard | REFUSED if the two maps' non-zero fractions differ by more than `MAP_PAIR_TOL` = 0.02, or if either map's on-sheet coverage is below `MAP_MIN_COVERAGE` = 0.99; there is no flag to switch it off | [`scripts/read_chart.py:35`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L35) `@750629f` [`scripts/read_chart.py:219`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L219) `@750629f` [`scripts/read_chart.py:221`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L221) `@750629f` [`scripts/read_chart.py:226`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L226) `@750629f` | MEASURED |
| 5. UNREADABLE assertions | on-sheet area ≥ 0.5 cm² and on-sheet CT std > 5 (std ≤ 5 fails); on failure the verdict is UNREADABLE, stats and ledger line are still written, exit code 2 | [`scripts/read_chart.py:31`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L31) `@5ca0c22` [`scripts/read_chart.py:235`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L235) `@5ca0c22` [`scripts/read_chart.py:8`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L8) `@e3a0717` [`scripts/read_chart.py:302`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L302) `@e3a0717` | MEASURED |
| 6. Map statistics | on-sheet px and cm²; forward and reverse means; forward minus reverse; fractions > 0.5 and > 0.75 for both maps; connected regions at forward > 0.5 with area > 0.5 mm² (count, largest) | [`scripts/read_chart.py:96`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L96) `@5ca0c22` [`scripts/read_chart.py:36`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L36) `@5ca0c22` [`scripts/read_chart.py:108`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L108) `@5ca0c22` | MEASURED |
| 7. Bright ink in the render | on-sheet CT-mid pixels above the 99.5th percentile, in 8-connected marks with long axis (√12·σ) 2-4 mm and ≥ 2× the short axis; flagged for a human look above 1 % (an implementation decision, recorded in the JSON) | [`scripts/read_chart.py:37`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L37) `@5ca0c22` [`scripts/read_chart.py:14`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L14) `@5ca0c22` | MEASURED |
| 8. Rule 5.5 | at 0.5 and 1 cm², on two grids, combined conservatively (section 8 and 7.3) | [`scripts/read_chart.py:196`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L196) `@448dc29` | MEASURED |
| 9. Swapped table | rule 5.5 on (reverse as forward), stored as `rule55_depth_swapped`; `depth_swap_tripwire` = it flags ≥ 1 unit | [`scripts/read_chart.py:255`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L255) `@5ab18b3` [`scripts/read_chart.py:257`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L257) `@5ab18b3` | MEASURED |
| 10. Crest check | R-CREST on the per-slice profile; a failure overwrites the verdict with VOID | [`scripts/read_chart.py:281`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L281) `@2684784` | MEASURED |
| 11. Contact sheet and ledger | CT mid, forward as stored, reverse as stored, per-unit margin with flagged units circled, 1 cm bar and µm/px on every panel; one ledger row with columns `date, key, fwd mean, rev mean, fwd>0.5, fwd>0.75, flagged 0.5 cm², largest cluster, verdict, sheet` | [`scripts/read_chart.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L16) `@5ca0c22` [`scripts/read_chart.py:40`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L40) `@5ca0c22` | MEASURED |
| `--maps-only` | no render: the CT-std assertion and the crest check are skipped | [`scripts/read_chart.py:209`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L209) `@5ca0c22` [`scripts/read_chart.py:231`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L231) `@5ca0c22` | MEASURED |
| Idempotence | `<out>/.read_complete` skips everything | [`scripts/read_chart.py:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L19) `@5ca0c22` | MEASURED |

- The truncated-map guard was added after an inference exited 0 with a reverse map non-zero on exactly one quadrant
  (25.00 % of its pixels). The pixels with no prediction, read as zeros, produced R-DEPTH's withdrawn ADMITTED verdict. **MEASURED** [`RULES.md:1618`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1618) `@750629f`
  The guard then refused a second truncated reverse map (on-sheet coverage 0.9404 against 1.0000) before it was
  scored. **MEASURED** [`RULES.md:1741`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1741) `@2d9e698` The cause of the truncations is recorded as unproven.
  **INFERENCE** [`RULES.md:1768`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1768) `@a0c1f8c`
- In `--maps-only` mode the first contact-sheet panel shows the real CT when a greyscale CT slice is given as the
  mask. This is display only: no statistic, assertion or verdict reads it. **MEASURED**
  [`scripts/read_chart.py:64`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/read_chart.py#L64) `@fed6602`

### 7.2 R-CREST: the crest check

| Constant | Value | Source |
|---|---|---|
| `CREST_MIN_RATIO` | 1.20 (max / min of the per-slice on-sheet mean); controls w040 1.76, w028 1.37 | [`scripts/read_chart.py:69`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L69) `@2684784` |
| `CREST_CENTRAL` | (0.25, 0.75): crest slice in [floor(0.25·(n-1)), ceil(0.75·(n-1))] | [`scripts/read_chart.py:70`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L70) `@2684784` [`scripts/read_chart.py:80`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L80) `@2684784` [`scripts/read_chart.py:82`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L82) `@2684784` |

**MEASURED.**

- Declared bar: crest ratio ≥ 1.20 AND crest slice within the central half (28 slices: 7..20; 21 slices: 5..15);
  failure gives VOID. **INFERENCE** [`RULES.md:60`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L60) `@2684784`
- **Central-band conflict.** For 28-slice renders the code's bounds are 6..21, as printed in ledger notes
  ("central [6, 21]") [`LEDGER.md:73`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L73) `@4d495d8`, while RULES declares 7..20 [`RULES.md:60`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L60) `@2684784`. For 21 slices
  both give 5..15. In the LEDGER lines found that print crest slice 6 or 21, the ratio (1.00 or 1.01) already fails
  the bar [`LEDGER.md:52`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L52) `@fd22942` [`LEDGER.md:170`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L170) `@e3db8cf`. **VERIFIED**
- Provenance (EXPLORATORY): the test was written after the second PHerc0826 read came back BLANK with a flat
  profile, and its thresholds were taken from the two controls. **MEASURED** [`RULES.md:58`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L58) `@2684784`
- The check runs on the render before the model call, so a failing render gets no inference.
  **MEASURED** [`scripts/run_patch_dir.py:329`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L329) `@1878782`
- Validation over 59 charts: reads at crest ratio 1.23 to 3.19, VOID charts at 1.00 to 1.12 (plus one 1.77 rejected
  on position), and none between 1.12 and 1.23. **MEASURED** (EXPLORATORY) [`RULES.md:91`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L91) `@92f139b` R-CREST-POWER
  later records that this validation is circular, because the readable population was defined by the bar itself.
  **INFERENCE** [`RULES.md:159`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L159) `@4f27c8d`
- `--ignore-crest` disables the veto only for R-CREST-POWER, under tag `ink9um_seed42+plain+nocrest` and its own
  ledger key. **MEASURED** [`scripts/run_patch_dir.py:373`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L373) `@ca7034c` [`RULES.md:160`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L160) `@4f27c8d` Because `read_chart.py`
  overwrites the verdict with VOID whenever the crest check fails, those ledger lines read VOID although the
  inference ran and rule 5.5 was evaluated. **MEASURED** [`scripts/read_chart.py:281`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L281) `@2684784`
  [`RULES.md:3091`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3091) `@fd3b816`
- R-CREST-POWER phase 1 (PRE-REGISTERED decision rule [`RULES.md:163`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L163) `@4f27c8d`) stopped at 11 of 12 members:
  150.67 cm² on-sheet, 190 valid units, 0 flagged in either depth order. The verdict has not been called.
  **MEASURED** [`STATE.md:33`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L33) `@71720ce` [`STATE.md:37`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L37) `@71720ce` Until it is, R-CREST remains a blocking veto.
  **INFERENCE**
- The pre-registered no-flag outcome reads "R-CREST is confirmed to discard nothing this reader could read on
  low-contrast volumes". **INFERENCE** (PRE-REGISTERED) [`RULES.md:163`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L163) `@4f27c8d` At the held-out known-text rate of
  1 flagged in 60 valid units, 3.17 flags are expected in 190, and 0 of 190 is not distinguishable from it (Fisher
  one-sided p = 0.24, EXPLORATORY). **VERIFIED** (arithmetic re-run 2026-10-15)
  [`RULES.md:3322`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3322) `@7925b3a` [`records/release/release_stats.json:111`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L111) `@7925b3a` After R-HELDOUT, a no-flag
  outcome therefore cannot show that R-CREST discards nothing readable. **INFERENCE** [`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a`

### 7.3 Two grids and the conservative verdict

- Rule 5.5 is evaluated at two unit sizes (0.5 and 1 cm²). The verdict comes from the 0.5 cm² units.
  **MEASURED** [`scripts/rule55.py:192`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L192) `@448dc29`
- Grid origin: by default (`--unit-origin auto`) the origin is chosen from the on-sheet mask only, by
  `rule55.best_origin`. The historical (0, 0) tiling is evaluated as well. **MEASURED**
  [`scripts/read_chart.py:196`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L196) `@448dc29` [`scripts/read_chart.py:258`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L258) `@3c6f950` This change was made after 3 reads, when
  (0, 0) tiling of fragmented PHerc0826 renders left 1 valid unit. **INFERENCE** (EXPLORATORY) [`RULES.md:123`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L123) `@448dc29`
  [`RULES.md:124`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L124) `@448dc29`
- Combination (EXPLORATORY; added after the fourth read, narrowed after the seventh):
  - a ≥ 3 cluster on the (0, 0) grid makes the verdict PROMISING CANDIDATE;
  - any flagged unit on the (0, 0) grid turns BLANK into NOT ESTABLISHED;
  - a (0, 0)-grid NOT ESTABLISHED caused only by too few valid units never overrides, so only flags and clusters
    carry over;
  - `flagged_any_grid` records the flags on both grids.

  **MEASURED** [`scripts/read_chart.py:265`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L265) `@770ab3c` [`scripts/read_chart.py:268`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L268) `@770ab3c`
  [`scripts/read_chart.py:269`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L269) `@3c6f950` [`scripts/read_chart.py:272`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L272) `@3c6f950` [`RULES.md:125`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L125) `@3c6f950` `@770ab3c`

### 7.4 Swapped table and tripwire

- Rule 5.5 flags on a signed margin, and "forward" depends on the normal the tracer picked. The swapped evaluation
  is recorded on every read as a tripwire. It changes no verdict. When it fires, it obliges an orientation check
  and, if the surface really is mirrored, a separate read under a `+flip` key. **INFERENCE** (PRE-REGISTERED)
  [`RULES.md:182`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L182) `@5ab18b3`
- The tripwire fired for the first time on G-OWN's trace on w040: forward table 0 flagged of 9 valid, swapped table
  2 flagged (+0.1150, +0.1048), clusters [1, 1]. **MEASURED** [`RULES.md:2817`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2817) `@d29112c`

---

## 8. Rule 5.5

`scripts/rule55.py` holds the frozen candidate rule as pure functions; every constant is copied from RULES R-5.5.

### 8.1 Unit side

side = round(sqrt(A) × 10000 / µm) px, with A = 0.5 cm² for the rule and 1 cm² reported alongside (side
round(10000 / µm)). **MEASURED** [`scripts/rule55.py:39`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L39) `@a2170dd` [`scripts/rule55.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L7) `@a2170dd`

| µm/px | Where it applies | 0.5 cm² unit side | Source | Label |
|---|---|---|---|---|
| 9.362 | w040; 9.362 µm eligible volumes | 755 px | [`RULES.md:47`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L47) `@8a52745` [`scripts/rule55.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L5) `@a2170dd` | MEASURED |
| 8.64 | 8.64 µm eligible volumes | 818 px (the prompt's prose says 819; the formula is the rule) | [`RULES.md:127`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L127) `@73eb297` | VERIFIED |
| 9.596 | w028 pooled | 737 px | [`RULES.md:47`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L47) `@8a52745` [`scripts/rule55.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L5) `@a2170dd` | MEASURED |
| 9.612 | PHerc0841 pooled (R-HELDOUT) | 736 px (round(735.65); the side used in the R-HELDOUT reads) | [`RULES.md:3254`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3254) `@661ff64` [`records/release/heldout_2026-10-15/20260220213127-w00_read_chart_stats.json:677`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/heldout_2026-10-15/20260220213127-w00_read_chart_stats.json#L677) `@7925b3a` | VERIFIED |

The 819 px figure in the master prompt and RULES R-5.5 is superseded by the arithmetic note, recorded before any
read. **VERIFIED** [`RULES.md:47`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L47) `@8a52745` [`RULES.md:127`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L127) `@73eb297`

### 8.2 Constants and verdicts

| Constant | Value | Source |
|---|---|---|
| `VALID_ONSHEET_FRAC` | unit valid if ≥ 90 % of its pixels are on-sheet (CT mid slice > 0) | [`scripts/rule55.py:25`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L25) `@a2170dd` [`RULES.md:47`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L47) `@8a52745` |
| Unit means | over the unit's on-sheet pixels (implementation decision) | [`scripts/rule55.py:13`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L13) `@a2170dd` |
| `FWD_MIN` | forward mean ≥ 0.36 | [`scripts/rule55.py:26`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L26) `@a2170dd` |
| `MARGIN_MIN` | forward minus reverse mean ≥ +0.08 | [`scripts/rule55.py:27`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L27) `@a2170dd` [`scripts/rule55.py:89`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L89) `@a2170dd` |
| Clusters | 4-connected flagged units | [`scripts/rule55.py:95`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L95) `@a2170dd` |
| `MIN_CLUSTER` | PROMISING CANDIDATE needs ≥ 3 units in one cluster | [`scripts/rule55.py:28`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L28) `@a2170dd` |
| `BLANK_MIN_VALID_CM2` | BLANK needs no flagged unit over ≥ 1.5 cm² of valid units, counted as nominal 0.5 cm² units (≥ 3); the exact pixel area (e.g. 3 × 755² px = 1.4988 cm² at 9.362 µm) is reported, not compared | [`scripts/rule55.py:29`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L29) `@a2170dd` [`scripts/rule55.py:12`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L12) `@e3a0717` [`scripts/rule55.py:145`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L145) `@e3a0717` |
| `ROW_PITCH_BAND_MM` | (2.0, 4.0), report-only | [`scripts/rule55.py:30`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L30) `@a2170dd` [`scripts/rule55.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L16) `@e3a0717` [`scripts/rule55.py:204`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L204) `@e3a0717` |
| `best_origin` | offsets in [0, side) on an 8 × 8 lattice (step = side // 8), maximising the number of valid units; mask only; ties to the smallest offset | [`scripts/rule55.py:64`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L64) `@448dc29` [`scripts/rule55.py:69`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L69) `@448dc29` |

**MEASURED.**

- Verdicts: no valid unit gives UNREADABLE; no flagged unit and ≥ 1.5 cm² nominal valid area gives BLANK; no flagged
  unit with less area gives NOT ESTABLISHED; flagged units with largest cluster < 3 give NOT ESTABLISHED; a cluster
  ≥ 3 gives PROMISING CANDIDATE. **MEASURED** [`scripts/rule55.py:146`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L146) `@e3a0717` [`scripts/rule55.py:145`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L145) `@e3a0717`
  [`scripts/rule55.py:152`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L152) `@a2170dd` [`scripts/rule55.py:154`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L154) `@e3a0717`
- **Row pitch conflict.** The master prompt and RULES define PROMISING CANDIDATE as "≥ 3 adjacent (4-connected)
  flagged units on one chart AND marks in rows at 2–4 mm letter height" [`docs/MASTER_PROMPT_v4.md:39`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L39) `@8a52745`
  [`RULES.md:50`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L50) `@8a52745`. In code the row check is report-only ("it has no bar in RULES.md and does not gate the
  verdict"), and the candidate verdict rests on the cluster alone [`scripts/rule55.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L16) `@e3a0717`. No RULES entry
  declaring this split was found. **MEASURED**
- The whole-map mean is not a verdict. **INFERENCE** [`docs/MASTER_PROMPT_v4.md:39`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L39) `@8a52745`

### 8.3 Levels and their validation

- Master-prompt levels on w028 unlabelled text: forward 0.40, margin +0.12; blank papyrus 0.29, 0.00. Power: 1 cm²
  9/9 text vs 0/11 blank; 0.5 cm² 22/24 vs 0/35. These are previous-session figures with unrecorded class
  definitions. **MEASURED** [`RULES.md:49`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L49) `@8a52745`
- Self-test (PRE-REGISTERED bar: ≥ 20/24 text and 0/35 blank flagged at 0.5 cm²) [`RULES.md:51`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L51) `@8a52745`. Under the
  recorded strict definitions only 5 text and 8 blank units exist. Results: text 5/5 and blank 0/8 on plain maps
  [`RULES.md:52`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L52) `@2fff337`, and 5/5 and 0/8 on TTA maps [`RULES.md:110`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L110) `@f66337f`. PASS was judged as a fraction.
  **MEASURED** The self-test runs on w028, a training-set sheet. **INFERENCE** [`RULES.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L35) `@8a52745`
- On w040 (a training-set sheet) the frozen rule on the frozen auto grid (origin (94, 188), side 755 px) gives 80
  units, 71 valid, 7 flagged, clusters [4, 2, 1]. **MEASURED** [`RULES.md:1486`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1486) `@140730b` [`RULES.md:1487`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1487) `@140730b`
  The 71 valid, 7 flagged and [4, 2, 1] at (94, 188) were reproduced on 2026-10-15. **VERIFIED**
  [`RULES.md:3276`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3276) `@eed0fac`

---

## 9. Integrity and operations

### 9.1 `map_integrity.py`

| Test | Rule | Kind | Source |
|---|---|---|---|
| PAIR | \|nz(forward) - nz(reverse)\| > 0.02 means one map of the pair is incomplete; works after the render is pruned | the same test `read_chart.py` refuses on | [`scripts/map_integrity.py:15`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L15) `@750629f` [`scripts/map_integrity.py:41`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L41) `@4ac46f1` [`scripts/read_chart.py:34`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L34) `@750629f` |
| COVERAGE | in the whole-tree audit, where the read's render is still on disk; with `--pair`, only when `--render-dir` names a directory holding `render.zarr`: mean(map > 0 over the on-sheet mask) ≥ 0.99 | the same test `read_chart.py` refuses on | [`scripts/map_integrity.py:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L18) `@750629f` [`scripts/map_integrity.py:107`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/map_integrity.py#L107) `@750629f` [`scripts/map_integrity.py:149`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/map_integrity.py#L149) `@fed6602` |
| STALE | flagged if the maps' mtime skew > the read's own `s_infer` (from `records/throughput.jsonl`, matched by ledger key) + 600 s; a read with no throughput record is not tested | audit flag, not a refusal | [`scripts/map_integrity.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L20) `@4ac46f1` [`scripts/map_integrity.py:32`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L32) `@4ac46f1` [`scripts/map_integrity.py:35`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L35) `@4ac46f1` [`scripts/map_integrity.py:97`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L97) `@4ac46f1` |

**MEASURED.** Exit code 1 if any pair is SUSPECT. `--pair <forward> <reverse>` checks a single pair (COVERAGE only with
`--render-dir`) and was added at release. **MEASURED** [`scripts/map_integrity.py:147`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/map_integrity.py#L147) `@fed6602` The supervisor runs the whole-tree audit at
check-in. **MEASURED** [`scripts/supervisor.sh:222`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L222) `@c638d54`

History, all MEASURED (EXPLORATORY):
- A first version with an absolute bar on the non-zero fraction flagged 19 good corpus maps; auto-cropped renders
  sit at 0.60-0.84. [`RULES.md:1641`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1641) `@750629f`
- The first relative audit checked 55 pairs: 54 sound, exactly one suspect (`gates/rdepth/high`).
  [`RULES.md:1638`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1638) `@750629f`
- A first STALE test with an absolute 1 h bar flagged 4 sound pairs. `--direction both` writes forward then reverse,
  and the skew was about half the inference time in every case. [`RULES.md:2957`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2957) `@4ac46f1` [`RULES.md:2969`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2969) `@4ac46f1`
- After the fix: 64 pairs, 64 sound, 0 SUSPECT. [`RULES.md:2975`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2975) `@4ac46f1`

### 9.2 Sweepers

- `sweep_partial_reads.py` deletes a read directory only if it has no `.read_complete`, holds at least one `.tif`,
  and has been untouched for `MIN_AGE_H` = 6.0 h (against a longest observed single-direction write of 1.9 h).
  Dry-run is the default and deletion needs `--go`. It runs at every supervisor check-in. **MEASURED**
  [`scripts/sweep_partial_reads.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_partial_reads.py#L21) `@d494084` [`scripts/sweep_partial_reads.py:15`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_partial_reads.py#L15) `@d494084`
  [`scripts/sweep_partial_reads.py:17`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_partial_reads.py#L17) `@d494084` [`scripts/supervisor.sh:243`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L243) `@d494084`
- `sweep_renders.py` removes a render only if it has a completion marker, has been untouched for `MIN_AGE_S` = 600 s
  (10 minutes), and every read of the patch has finished. **MEASURED** [`scripts/sweep_renders.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_renders.py#L16) `@27f78c6`
  [`scripts/sweep_renders.py:28`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_renders.py#L28) `@27f78c6` The marker and age guards were added after the sweeper deleted a PHerc1203
  render mid-write three times in a row. **MEASURED** [`RULES.md:360`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L360) `@27f78c6`

### 9.3 `disk_guard.sh` tiers

The guard loops every 60 s. **MEASURED** [`scripts/disk_guard.sh:11`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L11) `@925c037` [`scripts/supervisor.sh:300`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L300) `@925c037`

| Condition (free space on `/`) | Action | Source |
|---|---|---|
| any | VC3D remote chunk cache cleared above 1000 MB when nothing renders or traces, above 1500 MB regardless | [`scripts/disk_guard.sh:63`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L63) `@925c037` |
| < 7000000 kB | run `sweep_renders.py`, then prune normal grids (below) | [`scripts/disk_guard.sh:67`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L67) `@925c037` |
| < 7000000 kB and ≥ 5500000 kB | grids pruned to 900 MB; a live tracer's scroll exempt up to `ACTIVE_CAP_ROOMY` = 3000 MB | [`scripts/disk_guard.sh:75`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L75) `@658d5c2` [`scripts/disk_guard.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L19) `@658d5c2` |
| < 5500000 kB | grids pruned to 500 MB; live-tracer exemption up to `ACTIVE_CAP_TIGHT` = 1500 MB | [`scripts/disk_guard.sh:74`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L74) `@658d5c2` [`scripts/disk_guard.sh:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L20) `@658d5c2` |
| < 3000000 kB | clear every refetchable cache, delete level-4 CT caches except a keep-list of five scrolls (the keep-list works only since `091c2fa`, below), prune all grids by force | [`scripts/disk_guard.sh:78`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L78) `@925c037` [`scripts/disk_guard.sh:13`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L13) `@925c037` [`scripts/disk_guard.sh:87`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L87) `@0974977` |

**MEASURED.**

- The live-tracer exemption exists because pruning grids under a live tracer slowed 40-generation traces from 269 s
  and 333 s to a median of 1052 s. **MEASURED** [`RULES.md:562`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L562) `@0974977`
- **Keep-list defect, found while writing this release and fixed in `091c2fa`.** The keep-list is
  `KEEP_CT="PHerc0826|PHerc0358|PHerc1447|PHerc1203|PHerc0800"`. Up to `71720ce` it was used as
  `case ... in $KEEP_CT) ;;` [`scripts/disk_guard.sh:13`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L13) `@925c037` [`scripts/disk_guard.sh:83`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L83) `@925c037`. In bash a `|` that
  comes from a variable expansion is a literal character in a case pattern, not a separator. Running the old
  construct on 2026-10-15 matched none of the listed names, so below 3000000 kB every level-4 CT cache was deleted,
  the five listed included. **VERIFIED** `091c2fa` replaces it with `keep_ct()`, used at line 88 of the fixed
  script [`scripts/disk_guard.sh:29`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L29) `@091c2fa`. The regression test
  `test_the_ct_cache_keep_list_actually_keeps` pins the keep and drop cases
  [`scripts/tests/test_disk_guard.py:114`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/tests/test_disk_guard.py#L114) `@091c2fa`, and `test_disk_guard.py` passes (10 tests, run on
  2026-10-15). **VERIFIED** The old behaviour cost refetch time only, never a map or verdict. **INFERENCE**

### 9.4 Global inference slots

- `run_patch_dir.py` takes one of `HERCULES_INFER_SLOTS` (default 2) global flock slots before its own named lock.
  `infer_slot.sh` wraps direct `infer` callers in the same slots. **MEASURED**
  [`scripts/run_patch_dir.py:148`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L148) `@a0c1f8c` [`scripts/infer_slot.sh:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/infer_slot.sh#L7) `@acc775f` [`RULES.md:1762`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1762) `@a0c1f8c`
- Before the cap, seven scripts used seven different lock paths, so the locks allowed up to eight 9 µm inferences to
  share four cores, and `rdepth.sh`, the runner of the first truncation, took no lock at all (commit `acc775f`). The
  load average was 10–14 that night, and both map truncations happened under that load. **MEASURED** [`RULES.md:1757`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1757) `@a0c1f8c`

### 9.5 Supervisor guards

- `stale_proxy <pid>` is true when a process was started under a different `HTTPS_PROXY` than the current one. Such
  loops are killed and restarted. **MEASURED** [`scripts/supervisor.sh:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L23) `@fe7334e` R-DEPTH is exempt because it
  fetches nothing. **MEASURED** [`RULES.md:922`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L922) `@9d18317`
- One-queue guard: the PHerc1203 subset queue stands down whenever the full R-CREST-POWER phase-1 queue's pid is
  alive, whether or not a pause marker exists. **MEASURED** [`scripts/supervisor.sh:152`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L152) `@8aab40d`
  [`scripts/supervisor.sh:154`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L154) `@8aab40d` [`RULES.md:2994`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2994) `@8aab40d`

### 9.6 `ledger_audit.py`

- Every read on disk must have a LEDGER line, and every line must parse. Rows are split on unescaped pipes only.
  **MEASURED** [`scripts/ledger_audit.py:2`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/ledger_audit.py#L2) `@f23f470` [`scripts/ledger_audit.py:15`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/ledger_audit.py#L15) `@f23f470` It runs at every
  supervisor check-in. **MEASURED** [`scripts/supervisor.sh:237`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L237) `@c638d54`
- Recorded result: 162 ledger keys, 141 `read_stats.json` on disk, 0 reads on disk with no ledger line.
  **MEASURED** [`RULES.md:1822`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1822) `@f23f470` The first version split on plain pipes and reported all 141 reads as
  unledgered. **MEASURED** [`RULES.md:1826`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1826) `@f23f470`

### 9.7 The guards on committed data

The quick start runs these guards on the committed w040 window. A reverse map with all but its top-left quadrant
zeroed is refused by `map_integrity.py --pair` and `read_chart.py` (`PAIR: non-zero footprints differ by 0.7500`).
The depth-swapped read gives BLANK and the tripwire fires. **VERIFIED** [`examples/README.md:30`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L30) `@2bf30b3`
[`examples/README.md:31`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L31) `@2bf30b3`

### 9.8 Data and repository paths

| Variable | Default | What reads it | Source |
|---|---|---|---|
| `HERCULES_DATA` | `/home/user/hercules_data` | the data root (patches, caches, models) of every script that uses one | [`scripts/run_patch_dir.py:22`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/run_patch_dir.py#L22) `@fed6602` |
| `HERCULES_ROOT` | `/home/user/hercules` | the repository, in the shell scripts; Python scripts derive repository-relative paths from `__file__` | [`scripts/vc_tools.sh:22`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/vc_tools.sh#L22) `@091c2fa` |
| `VILLA` | `$HERCULES_ROOT/external/villa` | the villa checkout that `build_vc3d.sh` and `build_vc3d_extra.sh` compile | [`scripts/build_vc3d.sh:7`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/build_vc3d.sh#L7) `@091c2fa` |

**MEASURED.**

- `fed6602` moved every script to `HERCULES_DATA` and `HERCULES_ROOT`, with unchanged defaults; no default, constant
  or threshold changed. Integration tests that need public data skip with a stated reason when it is absent. `091c2fa` removed
  the hard-coded paths that remained: the villa checkout in `build_vc3d*.sh`, the `VC_PYTHON` default in
  `vc_tools.sh`, the `DENSE` default in `supervisor.sh`, and the quoted-heredoc Python of `gateB43.sh`,
  `ggp6_when_ready.sh` and `run_2um_patch.sh`, which now reads `HERCULES_DATA` / `HERCULES_ROOT` from the
  environment. **VERIFIED** (commit diffs read on 2026-10-15)
  [`scripts/vc_tools.sh:22`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/vc_tools.sh#L22) `@091c2fa` [`scripts/build_vc3d.sh:7`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/build_vc3d.sh#L7) `@091c2fa`
- The quick start (`bash examples/quickstart.sh`) passes every input as a file argument and needs neither
  variable. On 2026-10-15 it ended with `ALL CHECKS PASSED` in an exported copy of the tree with `HERCULES_DATA`
  pointing at a directory that does not exist. **VERIFIED** [`examples/README.md:3`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L3) `@2bf30b3`

---

## 10. Analysis tools

### 10.1 `cluster_power.py` (R-SHAPE)

| Item | Value | Source |
|---|---|---|
| Flag probability per valid unit | `P_CONTROL = 7.0 / 71.0`, each unit independent | [`scripts/cluster_power.py:17`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L17) `@8f459e0` [`scripts/cluster_power.py:10`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L10) `@8f459e0` |
| Trials | 20000 Monte Carlo | [`scripts/cluster_power.py:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L18) `@8f459e0` |
| Seed | 20260919 | [`scripts/cluster_power.py:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L19) `@8f459e0` |
| Statistic | 4-connected flagged triples on each surface's recorded valid-unit layout | [`scripts/cluster_power.py:10`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L10) `@8f459e0` |
| Dedupe | identical layouts inside one `*_cons_part*` directory counted once | [`scripts/cluster_power.py:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L22) `@cf78e64` |
| `--read-stats` mode | scores given `read_stats.json` files (added at release) | [`scripts/cluster_power.py:13`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/cluster_power.py#L13) `@fed6602` |

**MEASURED.**

- R-SHAPE (EXPLORATORY): the expected number of candidates from everything screened, if every unit were as inked as
  the control, is 0.079. **MEASURED** [`RULES.md:2465`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2465) `@8f459e0` With dedupe, the re-run reproduces 0.079.
  **MEASURED** [`RULES.md:2723`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2723) `@cf78e64`
- The independence assumption fails on the control: P(largest cluster ≥ 4) = 0.0257 under independence, and the
  control has a 4-cluster. **MEASURED** [`RULES.md:2501`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2501) `@cf64ed9` So, at the control's rate, 0.079 is a lower bound.
  **INFERENCE** [`RULES.md:2505`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2505) `@cf64ed9`
- p = 7/71 is the w040 rate, measured on a training-set sheet. **INFERENCE** [`RULES.md:3239`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3239) `@661ff64`
- R-HELDOUT declared that, on PASS, the held-out flag rate on text-bearing units replaces w040's 7/71 as the
  reference rate for unseen text, with both reported [`RULES.md:3268`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3268) `@661ff64`. The result is 1 of 60 valid
  units (exact 95 % CI 0.0004-0.0894) and 1 of 15 text-bearing units [`RULES.md:3319`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3319) `@7925b3a`. **MEASURED**
  `cluster_power.py` still defaults to 7/71, and `--p` scores another rate [`scripts/cluster_power.py:89`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L89) `@8f459e0`.
  **MEASURED** Its probabilities, R-SHAPE's 0.079 and the quick start's 0.0029 included, are therefore a
  training-set best case, not the power on unseen text. **INFERENCE**

### 10.2 `rblank.py` and `rblank2.py` (R-BLANK)

- R-BLANK statistic: the median margin of control valid units whose labelled ink fraction is exactly 0. With fewer
  than 5 such units the result is UNDERPOWERED. **MEASURED** [`RULES.md:2258`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2258) `@e38ac0f` [`RULES.md:2259`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2259) `@e38ac0f`
  Bar: blank baseline ≤ +0.0042 (≤ 3× the corpus's +0.0014). **MEASURED** [`RULES.md:2261`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2261) `@e38ac0f`
- Code: `MIN_BLANK_UNITS = 5`, `CORPUS_MARGIN = 0.0014`, `BASELINE_BAR = 3.0 * CORPUS_MARGIN`. **MEASURED**
  [`scripts/rblank.py:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank.py#L19) `@e38ac0f` [`scripts/rblank.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank.py#L20) `@e38ac0f` [`scripts/rblank.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank.py#L21) `@e38ac0f` The R-BLANK
  declaration and result were committed together (`e38ac0f`), so git does not show pre-registration. **VERIFIED**
  [`RULES.md:2261`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2261) `@e38ac0f` [`RULES.md:2282`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2282) `@e38ac0f`
- Part 2 bands (distance from a unit to labelled ink): touching ink, > 0-1 mm, 1-2 mm, 2-4 mm, ≥ 4 mm (in µm:
  0; 0-1000; 1000-2000; 2000-4000; 4000-∞). `POOL = 8`, `MIN_BAND_N = 5`, `BAR = rblank.BASELINE_BAR` (+0.0042).
  **MEASURED** [`scripts/rblank2.py:17`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L17) `@8f49fce` [`scripts/rblank2.py:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L18) `@8f49fce` [`scripts/rblank2.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L20) `@8f49fce`
  [`scripts/rblank2.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L21) `@8f49fce`
- Pooled-distance lower bound: the ink mask is max-pooled by 8, the Euclidean distance transform is taken in cells,
  and distance = max(0, D - √2) · pool · µm. **MEASURED** [`scripts/rblank2.py:45`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L45) `@8f49fce`
  [`RULES.md:2337`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2337) `@8f49fce` This replaced a centre-to-centre version that could overstate the true pixel distance by
  up to 106 µm. A randomised property test over twelve ink layouts pins it. **VERIFIED** [`RULES.md:2335`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2335) `@8f49fce`

### 10.3 `gown_result.py` (G-OWN)

| Constant | Value | Meaning | Source |
|---|---|---|---|
| `UM` | 9.362 | w040 pitch | [`scripts/gown_result.py:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L18) `@ce0eeb8` |
| `WRAP_UM` | 449.0 | R-INTERIOR's measured wrap spacing | [`scripts/gown_result.py:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L19) `@ce0eeb8` [`RULES.md:251`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L251) `@248e217` |
| `MIN_ON_SHEET_FRAC` | 0.50 | admissibility: ≥ 50 % of the trace's valid grid points within 449 µm of the w040 team mesh | [`scripts/gown_result.py:20`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L20) `@ce0eeb8` [`RULES.md:2403`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2403) `@07bfb73` |
| `PASS_BAR` | 0.0128 | half the team mesh's +0.0255 on the same text | [`scripts/gown_result.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L21) `@ce0eeb8` [`RULES.md:2411`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2411) `@07bfb73` |
| `COLLAPSE_BAR` | 0.0042 | the R-BLANK bar | [`scripts/gown_result.py:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L22) `@ce0eeb8` [`RULES.md:2414`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2414) `@07bfb73` |
| `TEAM_MESH_MARGIN` | 0.0255 | reference | [`scripts/gown_result.py:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L23) `@ce0eeb8` |
| `CORPUS_MARGIN` | 0.0014 | reference | [`scripts/gown_result.py:24`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L24) `@ce0eeb8` |
| `CONTROL_BLANK` / `CONTROL_INKED` | 0.0134 / 0.0438 | reference | [`scripts/gown_result.py:25`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L25) `@ce0eeb8` [`scripts/gown_result.py:26`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/gown_result.py#L26) `@ce0eeb8` |

**MEASURED.** The primary statistic is |whole-map on-sheet margin|, because the trace's orientation is unknown.
**INFERENCE** (PRE-REGISTERED) [`RULES.md:2405`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2405) `@07bfb73` Result: PASS; our trace keeps 142.7 % of the team mesh's
signal over the same 4.32 cm². **MEASURED** [`RULES.md:2814`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2814) `@d29112c` This is a relative comparison on a
training-set sheet. **INFERENCE** [`RULES.md:3239`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3239) `@661ff64`

### 10.4 `release_stats.py`

- Recomputes every headline statistic from its recorded count: Clopper-Pearson and Wilson 95 % intervals, one-sided
  Fisher exact tests against the control, binomial probabilities at the control rate, expected counts, and an
  EXPLORATORY cluster-collapsed sensitivity analysis (the control's clusters [4, 2, 1] become 3 events in 71 units).
  Interval bounds are rounded outward, and p-values are written to 3 significant figures. **MEASURED**
  [`scripts/release_stats.py:2`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L2) `@0afc07e` [`scripts/release_stats.py:11`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L11) `@0afc07e` [`scripts/release_stats.py:17`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L17) `@0afc07e`
- All 10 values printed in RULES.md that it checks reproduce at the precision printed. For example, RULES prints
  Fisher one-sided p = 0.0058 for 1/113 against 7/71 [`RULES.md:2230`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2230) `@e38ac0f`, and the script recomputes
  0.00576. **VERIFIED** (re-run on 2026-10-15; its JSON output is identical to the committed file)
  [`scripts/release_stats.py:52`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L52) `@7925b3a` [`records/release/release_stats.json:204`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L204) `@7925b3a`
  Control 7/71: CP95 [0.0405, 0.1927]. **VERIFIED** [`records/release/release_stats.json:9`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L9) `@0afc07e` [`records/release/release_stats.json:10`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L10) `@0afc07e`
  Full tables are in [RESULTS](RESULTS.md).

### 10.5 `rheldout.py` (R-HELDOUT)

| Constant | Value | Source |
|---|---|---|
| `UM` | 2.403 × 4 (level 2 of a 2.403 µm volume) | [`scripts/rheldout.py:29`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L29) `@d8c39a3` |
| `PHI_TEXT`, `SUP_BLANK` | 0.02 (text-bearing unit), 0.50 (supervised blank unit) | [`scripts/rheldout.py:30`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L30) `@d8c39a3` |
| `AUC_TRANSFER`, `AUC_REV_MAX`, `AUC_NONE` | 0.75, 0.60, 0.60 | [`scripts/rheldout.py:31`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L31) `@d8c39a3` |

**MEASURED.**

- Bars, declared before any held-out data was downloaded: HELDOUT-AUC TRANSFERS (pooled forward AUC ≥ 0.75 AND
  reverse ≤ 0.60) / NO TRANSFER (forward < 0.60) / PARTIAL; HELDOUT-RULE STRONG (a ≥ 3 four-connected cluster on any
  segment) / PASS (≥ 1 flagged valid unit) / BLIND (none). **INFERENCE** (PRE-REGISTERED) [`RULES.md:3261`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3261) `@661ff64`
  [`RULES.md:3263`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3263) `@661ff64`
- Preparation (declared with the bars): each segment's
  `surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr`, level 2, pooled to 21 slices by
  `python -m vesuvius.ink_detection.preprocessing.prepare_9um_isotropic_input <url> <out.zarr> --level 2` (villa
  `5ab585f`), giving 2.403 × 4 = 9.612 µm/px and a 0.5 cm² unit side of 736 px (section 8.1). Labels: level 2 of
  `inklabels.zarr` (> 0 = ink) and `supervision.zarr` (> 0 = supervised), on the same canvas. Inference: the
  R-REPRO call (seed42, plain, `--direction both`). **INFERENCE** (PRE-REGISTERED)
  [`RULES.md:3249`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3249) `@661ff64` [`RULES.md:3250`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3250) `@661ff64` [`RULES.md:3252`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3252) `@661ff64` [`RULES.md:3253`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3253) `@661ff64`
- Run as executed, with the scripts committed in `records/release/heldout_2026-10-15/`. `prep.sh` adds
  `--workers 6` to the pooling call. `fetch_labels.py` fetches the labels from the prefix
  `PHerc0841/segments/<segment>/ink-labels/2.403um-volume-20260319124803/20260918/`. `run_infer.sh` runs
  `python -m vesuvius.ink_detection.inference.infer pooled.zarr .../hybrid_3d2d-seed42/step-075000.pth pred.tif
  --direction both --batch-size 4 --no-compile --num-workers 3`. Analysis:
  `scripts/rheldout.py <segment_dir> [...] --um 9.612 --json out.json`. **MEASURED**
  [`records/release/heldout_2026-10-15/prep.sh:11`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/heldout_2026-10-15/prep.sh#L11) `@7925b3a`
  [`records/release/heldout_2026-10-15/fetch_labels.py:7`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/heldout_2026-10-15/fetch_labels.py#L7) `@7925b3a`
  [`records/release/heldout_2026-10-15/run_infer.sh:10`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/heldout_2026-10-15/run_infer.sh#L10) `@7925b3a`
  [`scripts/rheldout.py:18`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L18) `@d8c39a3`
- Method: the frozen rule with `unit_origin="auto"`; on-sheet = pooled CT middle slice > 0; flag rates with exact
  95 % intervals on text-bearing units (φ ≥ 0.02) and supervised blank units (φ = 0, ≥ 50 % supervised). The crest
  check is reported and does not gate. **MEASURED** [`scripts/rheldout.py:13`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L13) `@d8c39a3` [`RULES.md:3254`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3254) `@661ff64`
  [`RULES.md:3259`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3259) `@661ff64`
- The script and its tests were committed before any held-out output existed. **MEASURED**
  [`scripts/rheldout.py:4`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L4) `@d8c39a3`
- Result, HELDOUT-AUC: **TRANSFERS** (PRE-REGISTERED bar). Pooled over 3,669,681 supervised px (914,943 ink),
  forward AUC **0.8393**, reverse **0.5486**. Per segment: 0.8531 / 0.5324 (w00), 0.8176 / 0.5938
  (auto_grown_20260220144552896), 0.8294 / 0.5363 (auto_grown_20260220174252405). **MEASURED** (one code path)
  [`RULES.md:3301`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3301) `@7925b3a` [`RULES.md:3302`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3302) `@7925b3a`
- Result, HELDOUT-RULE: **PASS, not STRONG** (PRE-REGISTERED bar). 60 valid units (20 per segment), **1 flagged**
  (auto_grown_20260220144552896 unit (3,3), φ 0.0935, forward 0.3864, margin +0.0864), no cluster; swapped order 0
  flagged. The second code path, `read_chart.py --maps-only`, agrees on the auto grid (0, 1 and 0 flagged).
  **VERIFIED** (two code paths) [`RULES.md:3306`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3306) `@7925b3a` [`RULES.md:3307`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3307) `@7925b3a` [`RULES.md:3312`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3312) `@7925b3a`
- Text-bearing units (φ ≥ 0.02): **1 of 15** flagged (exact 95 % CI 0.0016-0.3195; RULES.md prints 0.0017, rounded to nearest). Supervised blank units
  (φ = 0, ≥ 50 % supervised): none exist on these segments (0 of 0), so the blank arm is empty, not passed. The
  seven units with φ ≥ 0.10 (max 0.2347) flag **0 of 7**: margins +0.0360 to +0.0663, forward means 0.3388-0.3729
  (as corrected). **MEASURED** [`RULES.md:3309`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3309) `@7925b3a` [`RULES.md:3310`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3310) `@7925b3a` [`RULES.md:3314`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3314) `@7925b3a` [`RULES.md:3334`](https://github.com/abundantjoe/hercules/blob/091c2fa/RULES.md?plain=1#L3334) `@091c2fa`
- On both grids the ordinary reader calls the three segments NOT ESTABLISHED, NOT ESTABLISHED, BLANK. The (0, 0)
  grid adds 1 and 2 flagged units on the first two segments, and neither grid has a ≥ 3 cluster. **MEASURED**
  [`RULES.md:3311`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3311) `@7925b3a` [`RULES.md:3313`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3313) `@7925b3a`
- On w040, a training-set sheet, the same grid flags 5 of 16 text-bearing units, and 2 of 2 at φ ≥ 0.10. **MEASURED**
  [`RULES.md:3317`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3317) `@7925b3a`
- EXPLORATORY, computed after the result: against the held-out rate 1/60, the eligible-scroll counts cannot be told
  apart from known text on an unseen scroll. R-DEFICIT 1/113 gives Fisher one-sided p = 0.575; R-CREST-POWER 0/190
  gives p = 0.24 (expected 3.17). **VERIFIED** (arithmetic re-run 2026-10-15) [`RULES.md:3320`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3320) `@7925b3a` [`RULES.md:3322`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3322) `@7925b3a`
  [`records/release/release_stats.json:40`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L40) `@7925b3a` [`records/release/release_stats.json:112`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L112) `@7925b3a`
- The eligible negatives are what this screen returns on real unseen text, so they are not evidence of absent ink.
  The limit this exposes is the unit screen's sensitivity on unseen text, not the model's pixel-level transfer.
  **INFERENCE** [`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a`

---

## 11. Validation gates summary

Bars were written before the runs unless the Registration column says otherwise.

| Gate | Bar | Result | Registration | Label | Citation |
|---|---|---|---|---|---|
| Gate A (w040 native stack, plain) | forward AUC ≥ 0.98 AND reverse < 0.70; reproduce the reference within 0.01 | forward 0.99659, reverse 0.49633 on 1,629,734 supervised px; PASS. Training-set sheet. | PRE-REGISTERED | VERIFIED | [`RULES.md:12`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L12) `@8a52745` [`RULES.md:13`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L13) `@8a52745` [`RULES.md:14`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L14) `@e3a0717` |
| REPRO-GATE-A (fresh container, 2026-10-15) | forward within 0.01 of 0.99659 AND reverse < 0.70 | forward 0.99659, reverse 0.49633 on 1,629,734 px; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:3222`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3222) `@c700273` [`RULES.md:3273`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3273) `@eed0fac` |
| REPRO-CTRL55 | exactly 71 valid, 7 flagged, clusters [4, 2, 1] at (94, 188), both code paths | `rctrl55.py`: 71 valid, 7 flagged, [4, 2, 1], CTRL55-STRONG; `read_chart.py --maps-only`: 7/71, largest cluster 4; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:3223`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3223) `@c700273` [`RULES.md:3276`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3276) `@eed0fac` [`RULES.md:3277`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3277) `@eed0fac` |
| R-REPRO bit identity (reported, not a bar) | none | both whole output TIFFs hash to the September `package.json` values | reported | VERIFIED | [`RULES.md:3279`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3279) `@eed0fac` [`RULES.md:3281`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3281) `@eed0fac` |
| G-A-crop (partial by construction) | forward ≥ 0.987 AND reverse < 0.60 | plain 0.99680 / 0.50301; TTA 0.99023 / 0.56597; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L19) `@acfe631` |
| Gate B Bar 1 (renderer) | Pearson ≥ 0.999 on every slice | min 0.999999; identical-pixel fraction min 0.9956; not bit-exact; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:24`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L24) `@8a52745` [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22` |
| Gate B Bar 2 | forward ≥ 0.987 AND reverse < 0.60 | 582,314 supervised px: plain 0.99680 / 0.50265; TTA 0.99024 / 0.56576; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:26`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L26) `@8a52745` [`RULES.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L30) `@e3a0717` |
| Gate C (w028) | forward ≥ 0.99 AND reverse < 0.60; reproduce within 0.01 | forward 0.99982 on 844,786 px; reverse 0.53058; PASS. Measures memorisation (training set). | PRE-REGISTERED | VERIFIED | [`RULES.md:34`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L34) `@8a52745` [`RULES.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L35) `@8a52745` [`RULES.md:36`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L36) `@aa32a21` [`RULES.md:36`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L36) `@2fff337` |
| w028 judge, plain | reproduce 0.784 / 0.49 | 0.7842 / 0.4902; reproduces | PRE-REGISTERED | VERIFIED | [`RULES.md:44`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L44) `@aa32a21` [`RULES.md:44`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L44) `@2fff337` |
| w028 judge, TTA | reproduce 0.823 | 0.8224 (reverse 0.4843). RULES calls this a reproduction "to three decimals"; 0.8224 agrees with 0.823 to within 0.001. | PRE-REGISTERED | VERIFIED | [`RULES.md:108`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L108) `@f66337f` |
| R-5.5 self-test (w028) | ≥ 20/24 text and 0/35 blank flagged at 0.5 cm² | strict definitions give 5 text and 8 blank units: 5/5 and 0/8 (plain and TTA); PASS judged as a fraction | PRE-REGISTERED | MEASURED | [`RULES.md:51`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L51) `@8a52745` [`RULES.md:52`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L52) `@2fff337` [`RULES.md:110`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L110) `@f66337f` |
| G-B-43 (seed43 admission) | forward AUC ≥ 0.95, ink margin ≥ +0.30, blank margin ≤ +0.05 | 0.99562, +0.45806, -0.03637; PASS | PRE-REGISTERED | MEASURED | [`RULES.md:173`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L173) `@3fc9e3d` [`RULES.md:285`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L285) `@c7ef931` |
| B-2UM forward (2.4 µm route) | pixel Pearson ≥ 0.9 AND AUC ≥ 0.95 against the team map > 0.5 | Pearson 0.9996, AUC 0.9999; PASS | PRE-REGISTERED | VERIFIED | [`RULES.md:66`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L66) `@8a52745` [`RULES.md:69`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L69) `@fd86019` |
| B-2UM reverse | our mean and text level both below half the team's | reverse mean 0.1877 against 0.5899; PASS | not demonstrable: bar and result first appear in the same commit | MEASURED | [`RULES.md:70`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L70) `@507a137` |
| R-CTRL55 (frozen rule on w040) | PASS ≥ 1 flagged; STRONG ≥ 3-unit cluster; BLIND 0 | 71 valid, 7 flagged, [4, 2, 1]; STRONG on a training-set sheet | PRE-REGISTERED | VERIFIED | [`RULES.md:1390`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1390) `@dcf2553` [`RULES.md:1487`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1487) `@140730b` |
| R-CREST bar | crest ratio ≥ 1.20 AND crest in the central half | 59 charts: reads 1.23-3.19, VOID 1.00-1.12; validation circular | EXPLORATORY | MEASURED | [`RULES.md:60`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L60) `@2684784` [`RULES.md:91`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L91) `@92f139b` [`RULES.md:159`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L159) `@4f27c8d` |
| R-CREST-POWER phase 1 | no flagged unit AND median margin within ±0.02 of the BLANK median: R-CREST stays; any flagged unit: R-CREST stops being a blocking veto on no-dynamic-range volumes | 11 of 12: 150.67 cm², 190 valid, 0 flagged; verdict NOT CALLED. After R-HELDOUT a no-flag call cannot show that R-CREST discards nothing readable (section 7.2) | PRE-REGISTERED | MEASURED | [`RULES.md:163`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L163) `@4f27c8d` [`STATE.md:33`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L33) `@71720ce` |
| R-DEPTH | ADMITTED if max(M(LOW), M(HIGH)) ≥ M(CENTRE) + 0.05 or worst/centre ≤ 0.50 | first ADMITTED withdrawn (truncated map); re-run -0.06860 and 0.6619; FAIL | PRE-REGISTERED | MEASURED | [`RULES.md:409`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L409) `@b688eb7` [`RULES.md:1618`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1618) `@750629f` [`RULES.md:2007`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2007) `@0423a76` [`RULES.md:2008`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2008) `@0423a76` |
| R-SMALL (40 generations) | ≥ 30 % readable over ≥ 15 outcomes | 20.0 % at the 15th outcome; 15.8 % of the complete 19; FAIL | PRE-REGISTERED | MEASURED | [`RULES.md:699`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L699) `@57cc4ae` [`RULES.md:1838`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1838) `@f729860` |
| QC in-mask area arm | median `onsheet_cm2 / in_mask_cm2` ≥ 0.5, else withdrawn | no recorded outcome | PRE-REGISTERED | INFERENCE (bar); no outcome found | [`RULES.md:146`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L146) `@adcd3d6` |
| G-OWN (our tracer on known text) | admissible if ≥ 50 % within 449 µm; PASS \|margin\| ≥ 0.0128; COLLAPSE ≤ 0.0042 | PASS: 142.7 % of the team mesh's signal (relative, training-set sheet) | PRE-REGISTERED | MEASURED | [`RULES.md:2403`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2403) `@07bfb73` [`RULES.md:2411`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2411) `@07bfb73` [`RULES.md:2814`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2814) `@d29112c` |
| P-DRY (packager dry run) | all file-derived checks pass AND exactly 2 FAIL | exactly 2 FAIL as declared. RULES says "20 PASS"; the stored report has 19 PASS + 2 FAIL (21 checks), consistent with the 21-check re-run. Since 2026-09-19 the old package fails four checks. | PRE-REGISTERED | MEASURED | [`RULES.md:86`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L86) `@8a52745` [`RULES.md:87`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L87) `@a2d0e59` [`packages/DRYRUN_PHerc0139_w040/verify_report.txt:17`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/verify_report.txt#L17) `@a2d0e59` [`RULES.md:993`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L993) `@8c43c62` [`RULES.md:1954`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1954) `@2255b76` |
| R-HELDOUT (PHerc0841, held-out scroll) | HELDOUT-AUC TRANSFERS / NO TRANSFER / PARTIAL; HELDOUT-RULE STRONG / PASS / BLIND | TRANSFERS: pooled forward AUC 0.8393, reverse 0.5486 on 3,669,681 supervised px. PASS, not STRONG: 1 flagged of 60 valid units, no cluster; text-bearing units 1 of 15; supervised-blank arm empty (0 of 0) | PRE-REGISTERED | MEASURED (AUC, one code path); VERIFIED (60 valid, 1 flagged, no cluster: two code paths agree) | [`RULES.md:3261`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3261) `@661ff64` [`RULES.md:3263`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3263) `@661ff64` [`RULES.md:3301`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3301) `@7925b3a` [`RULES.md:3306`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3306) `@7925b3a` [`RULES.md:3309`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3309) `@7925b3a` [`RULES.md:3312`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3312) `@7925b3a` |

The 19 PASS + 2 FAIL count was re-checked on 2026-10-15 by counting lines in the stored report. **VERIFIED**
[`packages/DRYRUN_PHerc0139_w040/verify_report.txt:21`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/verify_report.txt#L21) `@a2d0e59`

---

## 12. Software versions

| Component | September 2026 runs | October 2026 reproduction (R-REPRO) |
|---|---|---|
| Hardware | no GPU, 4 CPU cores (Intel Xeon 2.10 GHz), 15 GB RAM, ~30 GB writable disk **MEASURED** [`RULES.md:7`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L7) `@8a52745` | 4 cores; inference 5958 s for both orders (forward 52 min, reverse 47 min) **MEASURED** [`RULES.md:3284`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3284) `@eed0fac` |
| Python | 3.14.0rc2 venv **MEASURED** [`RULES.md:7`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L7) `@8a52745` | 3.14.6 **VERIFIED** [`RULES.md:3217`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3217) `@c700273` |
| torch | 2.14.0+cpu **MEASURED** [`RULES.md:7`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L7) `@8a52745` | 2.14.0+cpu, torchvision 0.29.0+cpu **VERIFIED** [`RULES.md:3218`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3218) `@c700273` [`records/release/env_infer_freeze.txt:82`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/env_infer_freeze.txt#L82) `@0afc07e` [`records/release/env_infer_freeze.txt:83`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/env_infer_freeze.txt#L83) `@0afc07e` |
| villa | `5ab585ffee54331a3362b9ce6b2929b20dcde2c6` **MEASURED** [`RULES.md:1969`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1969) `@7e56299` | same commit, editable install **VERIFIED** [`RULES.md:3217`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3217) `@c700273` |
| Checkpoint | `hybrid_3d2d-seed42/step-075000.pth` (seed43 for confirmation only) **MEASURED** [`scripts/run_patch_dir.py:32`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L32) `@e3a0717` | same file, sha256 `e635558a...` = HF LFS record **VERIFIED** [`RULES.md:3214`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3214) `@c700273` |
| VC3D tools | rebuilt from villa `5ab585f` in the `builder-ubuntu-26.04` image **MEASURED** [`RULES.md:28`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28) `@2e62892` [`scripts/build_vc3d.sh:9`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/build_vc3d.sh#L9) `@2e62892` | not exercised (native stack) **INFERENCE** [`RULES.md:3210`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3210) `@c700273` [`RULES.md:3219`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3219) `@c700273` |
| imagecodecs | listed unpinned in the master prompt's install line **INFERENCE** [`docs/MASTER_PROMPT_v4.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L30) `@8a52745` | 2026.10.10, added after the first scoring attempt stopped at the integrity check ("COMPRESSION.LZW requires the 'imagecodecs' package"); no number came from that attempt **VERIFIED** [`RULES.md:3287`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3287) `@eed0fac` [`requirements.txt:7`](https://github.com/abundantjoe/hercules/blob/eed0fac/requirements.txt#L7) `@eed0fac` |

- R-HELDOUT (2026-10-15) used the same checkpoint and call as R-REPRO, and villa `5ab585f` for the pooling step.
  Its inference took 1825 s, 2274 s and 1940 s for the three segments, both orders each. **MEASURED**
  [`RULES.md:3251`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3251) `@661ff64` [`RULES.md:3298`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3298) `@7925b3a` [`RULES.md:3299`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3299) `@7925b3a`
- Inference install: torch 2.14.0 and torchvision 0.29.0 from the PyTorch CPU index, then `requirements-infer.txt`,
  then villa at `5ab585f` with `pip install --no-deps -e`. **MEASURED** [`requirements-infer.txt:3`](https://github.com/abundantjoe/hercules/blob/0afc07e/requirements-infer.txt#L3) `@0afc07e`
  [`requirements-infer.txt:5`](https://github.com/abundantjoe/hercules/blob/0afc07e/requirements-infer.txt#L5) `@0afc07e`
- The analysis tools (reader, rule 5.5, integrity, statistics) were tested on 2026-10-15 under Python 3.13.16 with the
  versions pinned in `requirements.txt`; the full environment is frozen in `records/release/env_tools_freeze.txt`.
  **MEASURED** [`requirements.txt:2`](https://github.com/abundantjoe/hercules/blob/0afc07e/requirements.txt#L2) `@0afc07e`
- The master prompt requires Python ≥ 3.14 because villa requires it. **INFERENCE**
  [`docs/MASTER_PROMPT_v4.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L30) `@8a52745`
- The published VC3D image `:edge` is not used (section 5.3). **VERIFIED**
  [`records/release/edge_image_check_2026-10-15.md:14`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L14) `@0afc07e`

Full environments, data URLs, checksums and commands are in [REPRODUCE](REPRODUCE.md).

---

## Appendix: source conflicts found while writing this document

| # | Topic | Source A | Source B | Label |
|---|---|---|---|---|
| 1 | Density-gate window | 31 px = 2.9 mm [`RULES.md:137`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L137) `@604d137` [`METHOD.md:12`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L12) `@0821bc2` | "31 = 2.4 mm at 9.4 um scans" [`scripts/seeds.py:240`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L240) `@604d137` | MEASURED |
| 2 | Density-gate defaults | declared `--max-density 0.20 --density-window 31` [`RULES.md:138`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L138) `@604d137` | code defaults `None` and 15 [`scripts/seeds.py:238`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L238) `@46f2b7f` [`scripts/seeds.py:240`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L240) `@604d137`; seed files record 0.2 / 31 [`seeds/PHerc0826.json:10`](https://github.com/abundantjoe/hercules/blob/71720ce/seeds/PHerc0826.json#L10) `@7f47c64` | VERIFIED |
| 3 | R-SMALL figure | final 15.8 % [`RULES.md:1838`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1838) `@f729860` | 20.0 % [`METHOD.md:97`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L97) `@bf7c7f9` | MEASURED |
| 4 | Trace slots | one slot [`RULES.md:329`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L329) `@ce886a7` | default 2 [`scripts/supervisor.sh:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L18) `@2a7f98e` [`METHOD.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L19) `@0821bc2` | MEASURED |
| 5 | Consensus part-5 nodes | 20 692 [`RULES.md:2169`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2169) `@b513b83` | 22 228 [`RULES.md:2677`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2677) `@3adee87` | MEASURED |
| 6 | Team surface count | 53 / 22 / 6 per scroll [`scripts/fetch_team_segments.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_team_segments.py#L7) `@97dacf5` | "87 published surfaces" (subject of commit [`97dacf5`](https://github.com/abundantjoe/hercules/commit/97dacf5)) | MEASURED |
| 7 | Renderer exactness | "not bit-exact", identical-pixel fraction 0.9956 [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22` | "pixel for pixel" [`RULES.md:103`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L103) `@2fc94c5` [`scripts/fetch_surface_volumes.py:11`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L11) `@f600d41` | MEASURED |
| 8 | Team-mesh orientation | `--flip-normals` gives the trained orientation on the team's renders [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745` | team meshes without a published surface volume (every PHerc1203 surface; PHerc1447 segments beyond its 15 published volumes, e.g. `team_z_dbg_gen_00701`) are rendered by `vc_tools.sh`, which passes no `--flip-normals` [`scripts/fetch_surface_volumes.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L7) `@f600d41` [`records/throughput.jsonl:192`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L192) `@201e3c0` [`scripts/vc_tools.sh:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L6) `@e3a0717` | VERIFIED |
| 9 | villa commit | validated at `be09a85` [`docs/MASTER_PROMPT_v4.md:27`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L27) `@8a52745` | every run at `5ab585f` [`RULES.md:1969`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1969) `@7e56299` | INFERENCE |
| 10 | Worker count | `--num-workers 3` [`METHOD.md:37`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L37) `@0821bc2` [`RULES.md:3219`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3219) `@c700273` | default 2 [`scripts/run_patch_dir.py:98`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L98) `@2141cdb` | MEASURED |
| 11 | TTA cost | "~2.5×" [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745` | "4x" [`METHOD.md:39`](https://github.com/abundantjoe/hercules/blob/71720ce/METHOD.md?plain=1#L39) `@0821bc2`; "a quarter" [`RULES.md:119`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L119) `@98b6952` | MEASURED |
| 12 | seed43 agreement | "within 0.001 of AUC and 0.01 of ink margin" [`RULES.md:286`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L286) `@c7ef931` | 0.99562 vs 0.99680; +0.45806 vs +0.4681 [`RULES.md:285`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L285) `@c7ef931` | MEASURED |
| 13 | Unit side at 8.64 µm | 819 px [`docs/MASTER_PROMPT_v4.md:39`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L39) `@8a52745` [`RULES.md:47`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L47) `@8a52745` | 818 px [`RULES.md:127`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L127) `@73eb297` [`scripts/rule55.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L5) `@a2170dd` | VERIFIED |
| 14 | PROMISING CANDIDATE row criterion | part of the definition [`RULES.md:50`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L50) `@8a52745` | report-only in code [`scripts/rule55.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L16) `@e3a0717` | MEASURED |
| 15 | R-CREST central band, 28 slices | 7..20 [`RULES.md:60`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L60) `@2684784` | 6..21 in code and ledger notes [`scripts/read_chart.py:80`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L80) `@2684784` [`LEDGER.md:73`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L73) `@4d495d8` | VERIFIED |
| 16 | w028 TTA judge | "reproduced ... to three decimals" [`RULES.md:108`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L108) `@f66337f` | 0.8224 against 0.823 [`RULES.md:108`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L108) `@f66337f` | MEASURED |
| 17 | P-DRY PASS count | "20 PASS" [`RULES.md:87`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L87) `@a2d0e59` | 19 PASS + 2 FAIL [`packages/DRYRUN_PHerc0139_w040/verify_report.txt:21`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/verify_report.txt#L21) `@a2d0e59`; "21 checks" [`RULES.md:993`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L993) `@8c43c62` | VERIFIED |
| 18 | w040 training status | "a sheet the model did not memorise" [`RULES.md:1391`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1391) `@dcf2553` [`STATE.md:144`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L144) `@cc9675b` | training-set sheet [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64` | VERIFIED |
| 19 | `disk_guard.sh` keep-list | five scrolls kept [`scripts/disk_guard.sh:13`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L13) `@925c037` | the `case` pattern matched none of them (checked 2026-10-15) [`scripts/disk_guard.sh:83`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L83) `@925c037`; fixed in `091c2fa` (`keep_ct()`, regression test) [`scripts/disk_guard.sh:29`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L29) `@091c2fa` | VERIFIED |
| 20 | G-A-crop vs Gate B Bar 2 | "Identical to G-B Bar 2 ... to 4 decimals" [`RULES.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L19) `@acfe631` | holds for forward AUCs; reverse 0.50301 vs 0.50265 and TTA reverse 0.56597 vs 0.56576 [`RULES.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L19) `@acfe631` [`RULES.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L30) `@e3a0717` | MEASURED |
| 21 | Gate A call | master prompt 5.1 fixes the call with `--tta-mirror` [`docs/MASTER_PROMPT_v4.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L35) `@8a52745` | Gate A ran the plain call [`RULES.md:14`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L14) `@e3a0717`; its reference 0.9966 matches the plain result, and TTA on the crop gives 0.99023 [`RULES.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L19) `@acfe631` | MEASURED |
| 22 | seed43 confirmatory recipe | `--tag ink9um_seed43+plain` [`RULES.md:286`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L286) `@c7ef931` | `--tag ink9um_seed43+tta` (TTA on) in protocol 9 step 6 [`scripts/protocol9.sh:55`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/protocol9.sh#L55) `@0b06530` | MEASURED |
