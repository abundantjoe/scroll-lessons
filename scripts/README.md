# scripts/

This directory holds every program the project ran: **88 scripts** (58 `*.py`, 30 `*.sh`). There are also
34 test files in [`tests/`](tests/) and one schema note, [`STATS_SCHEMA.md`](STATS_SCHEMA.md). That note
describes the `read_stats.json` record that `read_chart.py` writes and `review_folder.py` reads.

Each script is listed once below, in one of seven groups. Each table gives:

- **purpose**: one line, taken from the script's own docstring or header comment.
- **RULES tag**: the [RULES.md](../RULES.md) section the script belongs to. "—" means the script has no RULES section
  of its own.
- **usage**: copied verbatim from the docstring or header when the script has a usage line. When it has none, the cell
  says so and lists the flags the code actually parses.

Results are not repeated here. They are in [docs/RESULTS.md](../docs/RESULTS.md), and every parameter is in
[docs/METHODS.md](../docs/METHODS.md). [docs/REPRODUCE.md](../docs/REPRODUCE.md) gives the public-data route
back to the control numbers, and [examples/README.md](../examples/README.md) runs the core tools in about 16 s on
a committed known-text window.

> **Read this before any script that touches w040.** The known-text control w040 (PHerc0139) is a **training-set
> sheet** of the `ink_9um` model. villa's training config lists it among the five native 9.362 µm training segments
> (VERIFIED, [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`;
> declared in R-HELDOUT, [`RULES.md:3231`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3231)
> `@661ff64`). Ink-model outputs that these scripts compute on w040 are therefore a best case on training data, not a
> held-out validation. That covers `reproduce_control.sh`, `rctrl55.py`, `rpop.py`, `rblank*.py`, `rsens.py`, `rsym.py`,
> `gown_result.py`, `gateB43.sh` and `rdepth*.sh`. Geometry measured on the w040 mesh, such as the bars in
> `ggp5b_decide.py` and `good_canvas.py`, does not involve the model. `rheldout.py` is the held-out test.

**How to run.** Run Python scripts as `python scripts/<name>.py` and shell scripts as `bash scripts/<name>.sh`. Not
every file has the executable bit. Most group-4 and group-5 scripts are a record of runs made in September 2026.
They read inputs that earlier steps wrote under `$HERCULES_DATA/gates/` and `$HERCULES_DATA/patches/`, and the
September data root no longer exists (VERIFIED,
[`RULES.md:3208`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3208) `@c700273`). Groups 1 and 2
run from public or committed inputs.

## Contents

1. [Reusable QC core](#1-reusable-qc-core) (9)
2. [Reproduction of the known-text control](#2-reproduction-of-the-known-text-control) (2)
3. [Pipeline: survey, seeds, tracing, consensus, QC, rendering, inference orchestration, fetching](#3-pipeline) (16)
4. [Experiments, one script per RULES test](#4-experiments-one-script-per-rules-test) (34)
5. [Operations](#5-operations) (13)
6. [Submission packaging](#6-submission-packaging) (5)
7. [The 2.4 µm route](#7-the-24-µm-route) (9)
8. [Paths and environment variables](#8-paths-and-environment-variables)
9. [Tests](#9-tests)

## 1. Reusable QC core

These are the tools a reviewer can point at any ink-detection read. `rule55.py` and `contact_sheet.py` are
libraries. The others are command-line tools. The quick start ([examples/](../examples/README.md)) runs
`read_chart.py`, `map_integrity.py` and `cluster_power.py`.

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `read_chart.py` | The read step (MASTER_PROMPT_v4 5.10) on existing model output; it never runs the model. Steps: on-sheet assertions, slice profile and crest, rule 5.5 at 0.5 and 1 cm², bright-ink check, contact sheet, one LEDGER line. It refuses a map pair whose non-zero footprints differ by more than 0.02, or whose on-sheet coverage is below 0.99 (`MAP_PAIR_TOL, MAP_MIN_COVERAGE`). | R-5.5, R-CREST | `read_chart.py <render.zarr\|mask> <forward.tif> <reverse.tif> --um <um> --out <dir>`<br>`--key '<scroll>\|<surface>\|<depth offset>\|<ckpt+TTA>\|both' --ledger read/LEDGER.md [--reason ...]`<br>`[--maps-only] [--max-panel-px 1000] [--force]` |
| `rule55.py` | The frozen candidate rule 5.5 as pure functions. A unit is 0.5 cm², side round(sqrt(0.5)·10000/um) px, and is valid at >= 90 % on-sheet. A unit is flagged when forward mean >= 0.36 AND (forward − reverse) mean >= 0.08. The verdict is PROMISING CANDIDATE at >= 3 4-connected flagged units, and BLANK when no unit is flagged over >= 1.5 cm² of valid units. | R-5.5 | library; no CLI (imported by `read_chart.py` and the experiment scorers) |
| `map_integrity.py` | Refuses a pair of prediction maps that is incomplete (regions left at 0). PAIR: the forward and reverse non-zero footprints differ by more than `--pair-tol` (0.02). COVERAGE: a map is non-zero on less than 0.99 of on-sheet pixels (with `--pair`, only when `--render-dir` is given). STALE: an audit flag only. It was written after a one-quadrant reverse map was scored as complete in R-DEPTH. | — (origin: R-DEPTH) | `map_integrity.py --pair <forward.tif> <reverse.tif> [--render-dir <dir with render.zarr>] [--json out.json]`<br>`map_integrity.py [--json out.json]        (audits every pair under $HERCULES_DATA)` |
| `cluster_power.py` | Asks whether a surface's actual layout of valid units could form a rule-5.5 candidate (3 4-connected flagged units) if each unit flagged independently at the control's rate p = 7/71. Monte Carlo with a fixed seed (20,000 trials by default). The `--read-stats` mode prints each estimate's binomial standard error, sqrt(P(1 − P) / trials) (on the quick-start window: 0.0029, SE 0.0004); the corpus mode prints none, but writes `trials` and `seed` to its JSON. | R-SHAPE | `cluster_power.py --read-stats <read_stats.json> [...] [--p 0.0986] [--trials 20000]   (score given reads)`<br>`cluster_power.py [--out cluster_power.json]          (every read under $HERCULES_DATA/patches)` |
| `contact_sheet.py` | Pixel-exact panel drawing, shared by the reader (5.10) and the review sheets (5.12). Maps are shown as stored, with no stretch. Any integer-factor resample is stated. Each panel has a 1 cm bar of round(10000 / um) px in a unique colour. | — | library; no CLI (imported by `read_chart.py`, `review_folder.py`, `package_submission.py` and `verify_package.py`; `make_figures.py` uses it through a `read_chart.py` subprocess) |
| `score_auc.py` | Gate A / Gate C scorer: pixel ROC AUC of a stored uint8 prediction TIFF against one label-zarr slice, on supervised pixels. It never resamples the map. Use `--ink-thr 0` for 0/1 labels. | G-A, G-C (also called by `gateB43.sh`, `rdepth.sh`, `reproduce_control.sh`) | `score_auc.py <pred.tif> <inklabels.zarr> <supervision_mask.zarr> --slice 14 --ink-thr 128 [--crop X Y W H] [--json out.json]` |
| `release_stats.py` | Recomputes every headline statistic of the release from its recorded counts. It gives Clopper-Pearson and Wilson 95 % intervals, one-sided Fisher exact tests, binomial probabilities at the control's rate, and an exploratory cluster-collapsed sensitivity analysis. It measures nothing. | — (counts from RULES.md / LEDGER.md) | `release_stats.py [--json out.json]` |
| `rheldout.py` | Scorer for the held-out known-text test on PHerc0841. It computes pixel AUC of both maps on supervised pixels, the frozen rule 5.5 in both depth orders, per-unit labelled-ink fraction, and flag rates with exact 95 % intervals, then applies the declared HELDOUT-AUC and HELDOUT-RULE bars. It was written and tested before any held-out output existed. | R-HELDOUT | `rheldout.py <segment_dir> [...] --um 9.612 --json out.json` |
| `make_figures.py` | Builds the three README figures from committed inputs only, with no network and no data root. Maps are shown as stored. | — | `make_figures.py [--out docs/figures]` |

R-HELDOUT result (`rheldout.py` on the three PHerc0841 segments): HELDOUT-AUC TRANSFERS (pooled forward AUC 0.8393, reverse 0.5486), HELDOUT-RULE PASS (1 flagged of 60 valid units, no cluster) — MEASURED, [`RULES.md:3296`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296) `@7925b3a`; output [`records/release/heldout_2026-10-15/rheldout.json`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/heldout_2026-10-15/rheldout.json) `@7925b3a`.

## 2. Reproduction of the known-text control

These two scripts re-create Gate A and R-CTRL55 on w040 from the public bucket, the public checkpoint and this
repository. R-REPRO (2026-10-15) passed both bars, and the output maps were byte-identical to the September record
(VERIFIED, [`RULES.md:3271`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3271) `@eed0fac`). Step-by-step
instructions are in [docs/REPRODUCE.md](../docs/REPRODUCE.md). The training-set caveat above applies.

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `fetch_control_w040.py` | Downloads level 0 of the w040 native 9.362 µm surface volume (28 x 6400 x 7980) and its tifxyz mesh from the public bucket, anonymously. Files already present are skipped. It writes `MANIFEST.sha256` and prints one digest over it. Labels and checkpoint come from Hugging Face. The download needs `boto3`, which `requirements.txt` does not pin (`requirements-infer.txt` does); `--manifest-only` needs no `boto3` and also checks the label directory. | R-REPRO | `fetch_control_w040.py <out_dir> [--manifest-only] [--threads 16]` |
| `reproduce_control.sh` | Re-creates the w040 control and checks it against the record. Steps: fetch; ink_9um seed42 step-075000 plain inference in both depth orders; Gate A AUC; R-CTRL55 via `rctrl55.py`; the same maps through `read_chart.py --maps-only`; bit-identity of the September window; sha256 of every output. It resumes after an interruption. In the recorded R-REPRO run its fetch and inference commands were skipped, because their outputs already existed (see docs/REPRODUCE.md, Level 2). Step 1 runs `fetch_control_w040.py` with `$INFER_PY` (since `15d369f`), so the inference environment needs `boto3`, which `requirements-infer.txt` pins; the analysis environment (`$PY`) does not. | R-REPRO (re-runs G-A and R-CTRL55) | `INFER_PY=/path/to/py3.14 PY=python bash scripts/reproduce_control.sh <work_dir>` |

## 3. Pipeline

This group covers the survey, seeds, tracing, consensus, QC, rendering, inference orchestration and fetching steps
for the 9 µm route. The 2.4 µm route is in [group 7](#7-the-24-µm-route).

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `survey_level4.py` | Day-0 level-4 preservation survey of the 23 eligible volumes. It cross-checks pixel size, checks the level-4 array format, computes a mid-slice layer-contrast metric declared before the first run, and draws a montage. | — (MASTER_PROMPT_v4 §1, §6) | `survey_level4.py [--out-dir records] [--cache /home/user/hercules_data/ct_l4_cache] [--only PHerc0125 ...]` |
| `seeds.py` | Seed generation (5.6) from level 3 of the surface-prediction zarr. Candidates are gated by level-4 CT > 0, split into outer/middle/inner thirds per z-band, and spread farthest-first. Output is level-0 seeds in JSON plus one PNG per band. | Seeds (5.6) candidate gate; Seeds density gate | `seeds.py --scroll PHerc0306B --vol 20250521133212 --um 8.64 --auto-bands --out seeds/PHerc0306B.json`<br>`seeds.py --pred-url <dir or https .zarr> --um 8.64 --zband 7000:8000 --n-per-band 12 --out x.json` |
| `sheet_seeds.py` | Samples seeds from one patch's own valid grid points, spread in grid index, so that every trace starts on the same sheet. | G-GP part 4 | `sheet_seeds.py <tifxyz dir> --count 25 [--json out.json]` |
| `interior_seeds.py` | Picks a seed file's interior seeds, i.e. radial position r/R in [`--lo`, `--hi`]. Axis and edge are defined exactly as in `radial_position.py`. | R-SMALL | `interior_seeds.py --scroll PHerc0826 [--seeds seeds/PHerc0826.json] [--lo 0.20] [--hi 0.55] [--out FILE]` |
| `vc_tools.sh` | Runs the rebuilt VC3D tools in the CI builder image, with the data root mounted at `/data`. Subcommands: `trace` (5.7, one seed), `render` (5.9, 28 slices, no flip) and `flatten` (5.13, ABF++). `VC_DRY_RUN=1` prints the docker argv and runs nothing. | — (MASTER_PROMPT_v4 5.7, 5.9, 5.13) | `vc_tools.sh trace   <scroll> <vol> <um> <X> <Y> <Z> <patches_dir>`<br>`vc_tools.sh render  <scroll> <vol> <pitch-string> <um> <patch_dir> <render.zarr>`<br>`vc_tools.sh flatten <patch_dir> <out_dir>`<br>`vc_tools.sh help` |
| `vc_consensus.sh` | Runs `vc_grow_seg_from_segments`, the team's second growth stage: a consensus surface grown from a directory of stage-1 patches. Its parameters are read verbatim off the team's published PHerc1447 segments. | G-GP part 3 | `vc_consensus.sh <scroll> <vol> <um> <X> <Y> <Z> <src_patches_dir> <target_dir>` |
| `build_vc3d.sh` | Builds the VC3D command-line tools from `external/villa` inside the project's CI builder image. The published runtime image (tag edge/main, built 2026-05-13) predates `--flip-normals` and remote normal grids. Output goes to `$HERCULES_DATA/vc_install`. | G-B | no usage line; no arguments (env `JOBS`, `TARGETS`) |
| `build_vc3d_extra.sh` | Builds `vc_tifxyz_selfcross`, `vc_tifxyz_winding` and `vc_grow_seg_from_segments` into the same install tree, then deletes the build tree. It refuses to start below `MIN_FREE_GB`. | R-CROSS, G-GP part 3 (tools) | no usage line; no arguments (env `JOBS`, `TARGETS`, `MIN_FREE_GB`) |
| `patch_qc.py` | Patch QC (5.8) of a tifxyz dir. Geometry passes at mean abs n_z <= 0.50, frac(abs n_z > 0.7) <= 0.25 and area >= 0.5 cm². The CT-mask check samples 100 points at level 4 and passes when zero_frac <= 0.50 or in-mask area >= 1.5 cm². An overlay is optional. | QC 5.8; QC CT-mask bar (in-mask area arm) | no usage line; header gives `patch_qc.py <parent_dir> --batch ...`; flags `patch_dir`, `--um`, `--ct-url`, `--overlay`, `--cache`, `--coord-scale`, `--catalogue`, `--batch`, `--force` |
| `ct_at_points.py` | Crest pre-check of a tifxyz trace in the CT, before any render. It samples the CT along the local surface normal and requires a crest ratio >= 1.20 inside the central half. | R-CREST-CT | `ct_at_points.py PATCH_DIR --volume-url URL --level L --coord-div F [--half N] [--every K] [--cache DIR] [--out JSON]` |
| `run_patch_dir.py` | The 5.11 automation loop over one scroll's patches: QC, then render, then inference in both depth orders, then read. Each stage leaves a marker, and keys already in LEDGER.md are skipped. Throughput goes to `records/throughput.jsonl`. | — (MASTER_PROMPT_v4 5.8–5.11); `--ignore-crest` used by R-CREST-POWER | `run_patch_dir.py <patches_dir> --scroll <PHercXXXX> --vol <vol id> [--ckpt ...] [--tag ink9um_seed42+tta]`<br>`[--delete-renders] [--only NAME ...] [--data-root ...] [--catalogue ...] [--ledger ...] [--records ...]` |
| `infer_slot.sh` | Runs a command under one of the global 9 µm inference slots, the same ones `run_patch_dir.py` takes (`flock`, `HERCULES_INFER_SLOTS`, default 2). | — | `infer_slot.sh <command...>` |
| `fetch_team_segments.py` | Fetches the team's published surface segments for a scroll into the patches dir, so the normal read pipeline reads them with no tracing. It takes the flattened mesh when one exists, else the raw patch. The bucket prefix is recorded in `source.json`, and local dirs are named `team_<uuid>`. | — | `fetch_team_segments.py PHerc1203 [--out /home/user/hercules_data/patches/PHerc1203] [--limit N] [--raw]` |
| `fetch_surface_volumes.py` | Fetches the team's published surface volumes (their renders of their segments) into the patch dirs as `render.zarr`, so the read skips rendering. Provenance goes to `render_source.json`. `--max-ahead` bounds disk use. | — (relies on G-B) | `fetch_surface_volumes.py PHerc0800 [--max-ahead 2] [--loop 120] [--dry-run]` |
| `fetch_pred_box.py` | Materialises only the level-0 chunks of a surface-prediction zarr that cover a voxel box. Absent chunks read as 0 ("not a sheet"), so growth stops at the box edge. | G-GP part 3/4 | `fetch_pred_box.py --scroll PHerc0826 --vol 20250821151701 --box x0 x1 y0 y1 z0 z1 --out <dir>`<br>`[--margin 200] [--min-free-gb 3] [--um 9.362]` |
| `crop_zarr_stack.py` | Crops a local zarr-v2 surface-volume stack into a new zarr group that villa's `infer` accepts. Pure numpy + zarr; idempotent. It is not referenced by RULES.md. | — | `crop_zarr_stack.py <in.zarr> <out.zarr> --x X --y Y --w W --h H [--zrange z0:z1]` |

## 4. Experiments, one script per RULES test

The rows follow the order in which the tests are declared in [RULES.md](../RULES.md). Each scorer applies bars
that were fixed in its RULES declaration and does not choose them. Look up the outcome under the tag in RULES.md
or [docs/RESULTS.md](../docs/RESULTS.md).

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `w028_judge.py` | The w028 judge (5.4): pixel ROC AUC of a 9 µm map on unlabelled w028 text against blank. The reference is the team's 2.4 µm prediction block-averaged 4x4. Text is reference >= 0.40 and blank is <= 0.25, on-sheet only, with pixels within 60 px of a labelled letter excluded. | J-w028 | no `usage:` line; header gives subcommands<br>`build  --team-tif T --pooled P --labels L --out DIR`<br>`score  --ref DIR --forward F.tif [--reverse R.tif] [--json out]` |
| `w028_rule55_selftest.py` | Self-test of the frozen rule 5.5 on the w028 pooled maps. It must flag the units the judge reference calls text and none it calls blank. | R-5.5 (self-test; classes from the J-w028 reference) | `w028_rule55_selftest.py --ref <judge ref dir> --forward F.tif --reverse R.tif [--json out]` |
| `rcrest_power.sh` | Phase 1. Reads the 12 largest-area VOID surfaces of the team's two published volumes with the crest veto off, under their own tag and ledger key. The population is in `records/rcrest_power_phase1.txt`. | R-CREST-POWER | no usage line; no arguments |
| `rcrest_power_1203.sh` | Reads the three PHerc1203 members of the same population on their own inference lock, with the same decision rule and tag. | R-CREST-POWER | no usage line; no arguments |
| `gateB43.sh` | Runs the seed43 checkpoint on the Gate B render, plain, in both depth orders, scored exactly as seed42 was. It writes `gateB43.json` with the bars `auc_forward_min=0.95`, `margin_on_ink_min=0.30`, `margin_on_blank_max=0.05`. | G-B-43 | no usage line; no arguments |
| `reflip_scan.py` | Applies the depth-order tripwire retrospectively to reads made before it existed. It uses stored maps and masks only, with no inference. It adds `rule55_depth_swapped` and `depth_swap_tripwire` to `read_stats.json` and changes no verdict. | R-FLIP | `reflip_scan.py [--patches DIR] [--dry-run]` |
| `lasagna_normal.py` | Compares a trace's own surface normal with the team's published sheet-normal field (lasagna `nx`, `ny`) as abs(cos θ). The uint8 decoding is self-tested first. | R-NORMAL | `lasagna_normal.py PATCH_DIR --scroll PHerc0826 [--every 3] [--cache DIR] [--out JSON]` |
| `radial_position.py` | Computes the radial position r/R of every read surface's points. The axis is the published umbilicus, or the level-4 mask centroid; the edge is the 99th-percentile mask radius at the same z. This is a measurement, not a bar. | R-RADIAL | `radial_position.py --scroll PHerc0826 [--patches DIR] [--out JSON]` |
| `interior_resolve.py` | Counts the wraps resolved by the surface prediction and by the lasagna `cos` field along radial rays in r/R [lo, hi]. Both counts are compared with the sheet spacing in the CT's own autocorrelation. | R-INTERIOR | `interior_resolve.py --scroll PHerc0826 [--n-z 4] [--rays 24] [--lo 0.2] [--hi 0.5] [--out JSON]` |
| `rsmall_result.py` | Readable fraction of 40-generation interior traces, against the bar of >= 30 % readable over >= 15 traces. The baseline is 1 readable of 18. Traces grown at any other budget are excluded by their own `max_gen`. | R-SMALL | `rsmall_result.py [--gen 40] [--scrolls PHerc0826 PHerc0358]` |
| `wrap_span.py` | Divides the 5th–95th percentile spread of a trace's radius about the scroll axis by the wrap spacing. Below about 1, the surface stays inside one wrap. | R-WRAP | `wrap_span.py PATCH_DIR --scroll PHerc0826 [--spacing-vx 48] [--out JSON]` |
| `row_power.py` | Looks for periodic row structure anywhere on a map. It takes a mask-corrected 2-D autocorrelation and reports the largest value at lags of 2–4 mm over all directions, with the direction and pitch. | R-ROWS | `row_power.py MAP.tif --mask MASK.png --um 9.362 [--min-mm 2] [--max-mm 4] [--region REGION.png] [--out JSON]` |
| `rdepth.sh` | Moves the reader's 17-slice window across the 28-slice Gate B render, to a low and a high window, and scores each window with `score_auc.py`. The centre window is not re-run. | R-DEPTH | no usage line; no arguments |
| `rdepth_part2.sh` | Reads the declared part-2 set at both off-centre windows (offsets +5 and −6). Its premise, the R-DEPTH ADMITTED verdict, was withdrawn because that verdict rested on a truncated map (VERIFIED, [`RULES.md:1618`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1618) `@750629f`). R-DEPTH's final verdict is FAILED (VERIFIED, [`RULES.md:1993`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1993) `@0423a76`). | R-DEPTH (part 2) | no usage line; no arguments |
| `rdepth_result.py` | Applies the declared R-DEPTH bar to the three windows' AUC JSON files. ADMITTED if max(M(low), M(high)) >= M(centre) + 0.05, or min(M(low), M(high)) / M(centre) <= 0.50. A window missing either run is reported as pending. | R-DEPTH | no usage line; no arguments |
| `mesh_distortion.py` | Mesh parameterisation quality of a tifxyz grid: stretch, anisotropy, shear and sag (µm). No inference and no render are needed. | G-GP | `mesh_distortion.py <tifxyz dir> [...] --um 9.362 [--label NAME] [--json out.json]`<br>`mesh_distortion.py --batch <dir of tifxyz dirs> --um 9.362 [--json out.json]` |
| `ggp_result.py` | G-GP scorer. A trace is PARAMETERISATION-DEGRADED if its anisotropy_p90 or sag_um_p90 is >= 2x Reference B's pooled p90. Reference B is the team's published segments. | G-GP | no usage line; no arguments |
| `rcross.sh` | Runs the team's `vc_tifxyz_selfcross` census over a population of tifxyz dirs. Report-only: nothing is modified and no verdict changes. | R-CROSS | `rcross.sh <population-name> <tifxyz dir \| dir-of-tifxyz-dirs> ...` |
| `rcross_result.py` | Pools the selfcross reports per population. The headline count is the minimum over the two quad triangulations; both are reported. | R-CROSS | no usage line; flags `--populations` |
| `rcross_split.py` | The declared outcome split. Our traces are split at the team's pooled p90 crossing rate. The high group must be VOID-or-unreadable at >= 2x the low group's rate, with >= 30 traces on each side; otherwise R-CROSS is descriptive only. | R-CROSS | no usage line; no arguments |
| `patch_agreement.py` | Voxelises every patch's valid points at half the measured wrap spacing and counts distinct patches per cell. The result is an upper bound on the area where N patches agree. | G-GP part 3 | `patch_agreement.py --scrolls PHerc0826 PHerc0358 [--cell 24] [--um 9.362] [--json out.json]` |
| `ggp4_consensus.sh` | Builds the consensus surface from a concentrated campaign, via `vc_consensus.sh`: every trace in `patches/<scroll>_dense` plus the patch the seeds came from. `PART=<n>` names the generation. | G-GP part 4 | `ggp4_consensus.sh <scroll> <vol> <um> <X> <Y> <Z> [consensus_th]` |
| `good_canvas.py` | Descriptive only. Measures how much of the area read lies on surfaces under the G-GP part 3 geometry bar (<= 14.2 transverse self-intersections per cm², ten times the control's 1.42). VOID reads are excluded and the result is split by radial position. It gates nothing. | G-GP part 3 bar (descriptive) | no usage line; flags `--bar`, `--rcross`, `--radial-glob`, `--json` |
| `rbest.sh` | Runs the candidate-grade reader (`--tta-mirror`) on the geometrically pristine surfaces. The population was fixed in RULES before the reads, and rule 5.5 is unchanged. | R-BEST | no usage line; no arguments |
| `rbest2.sh` | Runs the candidate-grade reader (`--tta-mirror`) over every sound-geometry surface that lacks one. Renders are deleted after each read. | R-BEST-2 | no usage line; no arguments |
| `rsym.py` | Pearson r(forward, reverse) over the pixels of rule-5.5 valid units, on the Gate B control and on every corpus read. The bars are in RULES: control anchor r <= 0.30, DEPTH-SYMMETRIC at r >= 0.70, nomination at r < 0.30. | R-SYM | no usage line; flags `--patches`, `--gateb`, `--um`, `--out` |
| `rsens.py` | Descriptive only. The ink-coverage floor of rule 5.5 on the Gate B control. One arm is analytic, using Gate A's per-class levels; the other is empirical, using half-unit-stride tiling. | R-SENS | no usage line; flags `--gateb`, `--labels`, `--mask`, `--slice`, `--crop`, `--um`, `--out` |
| `rctrl55.py` | Runs the frozen rule 5.5 on the full canvas of the w040 known-text control. The only choices are the on-sheet mask and the frozen `best_origin`. | R-CTRL55 | no usage line; flags `--forward`, `--reverse`, `--labels`, `--slice`, `--um`, `--out` |
[line withheld: prize-candidate detail under review]
| `ggp5b_decide.py` | Decides from the measurements whether the threshold-4 consensus is read. Bars: worst per-surface transverse self-intersections <= 1.42 per cm², and p90 sag <= 9.93 µm (the w040 control's own values). Exit 0 means ADMITTED. | G-GP part 5b | no usage line; flags `--part`, `--pop` |
| `rblank.py` | Median margin of the valid 0.5 cm² units on the w040 control whose labelled ink fraction is exactly 0.000. Labels are projected by any-over-z. The bar is +0.0042. | R-BLANK | no usage line; flags `--forward`, `--reverse`, `--labels`, `--um`, `--out` |
| `rblank2.py` | Margin against distance to the nearest labelled ink pixel, in five declared bands. It flags nothing and changes no verdict. | R-BLANK (part 2) | no usage line; flags `--forward`, `--reverse`, `--labels`, `--um`, `--out` |
| `gown_result.py` | Applies the admissibility gate (on-sheet fraction >= 0.50), computes the declared statistic, and prints the declared verdict for our tracer's surface on PHerc0139 known text. The pass bar is 0.0128, half the team mesh's +0.0255; the collapse bar is 0.0042. | G-OWN | `gown_result.py --patch <tifxyz dir> [--read <read dir>] [--mesh <w040 mesh dir>] [--out JSON]` (header line, no `usage:` prefix) |
| `coverage_proxy.py` | **Rejected proxy.** It predicts a trace's papyrus coverage from level-4 CT sampled at the trace's grid points. The docstring says it will be validated against "the 31 surfaces whose true rendered coverage is already recorded". RULES reports Pearson r 0.43–0.63 over 9 surfaces (VERIFIED, [`RULES.md:2576`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2576) `@b2765f7`) and concludes: "It is not usable and is used for nothing" (VERIFIED, [`RULES.md:2577`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2577) `@b2765f7`). | R-COVER9 | no usage line; flags `--scroll`, `--vol`, `--every`, `--out` |

## 5. Operations

These scripts were written for the September 2026 container: 4 cores, about 30 GB of disk, restarts without notice.
They schedule and resume queues, guard disk and audit the record. The scorers that these scripts call are listed in
[group 4](#4-experiments-one-script-per-rules-test).

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `supervisor.sh` | Idempotent resume-everything script. It starts dockerd, resumes the gate inference queue, the coverage tracing loop for the scrolls in `COVERAGE` and the QC→render→read loop, and restarts loops started under a stale `HTTPS_PROXY`. Each step skips finished work via markers. | — | no usage line; no arguments (env `COVERAGE`, `DENSE`, `TRACERS`, `TRACE_SLOTS`) |
| `disk_guard.sh` | Disk guard. It prunes caches, but not the normal grids of a scroll that is being traced, except below the hard floor. It also keeps the level-4 CT caches of the `KEEP_CT` scrolls. **Bug fixed in `091c2fa`:** the keep-list test `case $name in $KEEP_CT)` never matched, because a pipe character that arrives through a variable is a literal character in a case pattern, not alternation. Below the floor every CT cache was therefore deleted, the kept ones included; the cost was refetch time only. It is now `keep_ct()`, with the regression test `test_disk_guard.py::test_the_ct_cache_keep_list_actually_keeps` (VERIFIED, [`scripts/disk_guard.sh:29`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L29) `@091c2fa`). | — | `disk_guard.sh [interval_seconds]   (env: HERCULES_DATA, HERCULES_ROOT)` |
| `sweep_partial_reads.py` | Removes a killed read's leftover maps before they can pair with a fresh map. A directory qualifies only with no `.read_complete`, at least one `.tif`, and no change for `--min-age-h` hours (default 6). It is a dry run unless `--go` is given. | — | no usage line; flags `--root`, `--min-age-h`, `--go` |
| `sweep_renders.py` | Deletes renders that no read still needs: the patch has a finished read and no unfinished one. Renders written in the last 10 minutes are kept. | — | `sweep_renders.py [--patches DIR] [--dry-run]` |
| `ledger_audit.py` | Checks that every read on disk has a LEDGER.md line, and that every line parses. Rows are split on unescaped pipes only. | — | no usage line; flags `--ledger`, `--data-root` |
| `tracer_loop.sh` | Runs the tracer over every seed of `seeds/<scroll>.json`, N at a time, skipping seeds already done. | — (MASTER_PROMPT_v4 5.7) | no usage line; positional args in code: `<scroll> <vol> <um> [N]` |
| `dense_loop.sh` | Traces the seeds that `sheet_seeds.py` sampled from one patch into `patches/<scroll>_dense/`. The seed list is read into an array and stdin is closed for every command. | G-GP part 4 | `dense_loop.sh <scroll> <vol> <um> <seeds.json>` |
| `rsmall_loop.sh` | Traces interior seeds at a reduced growth budget (40 generations) into `patches/<scroll>_small/`. R-SMALL-2 reuses it via `RS_SUFFIX` / `RS_SEEDS`. | R-SMALL, R-SMALL-2 | no usage line; positional args in code: `<scroll> <vol> <um>` |
| `ggp5_when_ready.sh` | Builds the part-5 consensus once, when every declared part-5 seed has a `.done` marker and no dense loop is running. | G-GP part 5 | no usage line; no arguments |
| `ggp6_when_ready.sh` | After the G-OWN trace finishes, builds part 6 (threshold 8) and part 6b (threshold 10) and records the grid fill. | G-GP part 6 | no usage line; no arguments |
| `ggp6_read_when_ready.sh` | After G-OWN's read finishes, reads the threshold-8 and threshold-10 consensus surfaces. | G-GP part 6 | no usage line; no arguments |
| `gown_when_ready.sh` | When the PHerc0139 known-text trace finishes, runs the declared chain end to end. The bars live in `gown_result.py`. | G-OWN | no usage line; no arguments |
| `rsmall2_when_ready.sh` | Starts the interior queue when G-GP part 5 releases a trace slot. It fires once per scroll. | R-SMALL-2 | no usage line; no arguments |

## 6. Submission packaging

Everything a First Letters submission needs, built and verified before any candidate exists. No PROMISING
CANDIDATE has been produced on an eligible scroll, so these tools have only run on the w040 dry run
(`packages/DRYRUN_PHerc0139_w040/`).

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `package_submission.py` | Builds the submission package (MASTER_PROMPT_v4 5.14, rule 1). Contents: 4.00 cm² window TIFFs as unaltered crops; PNGs with a 1 cm bar drawn outside the map; letters and rows; the flattened mesh with SHA-256 of every file; held-out text and method. It runs `verify_package.py` at the end. | P-DRY | `package_submission.py --read-dir D --mesh M --window-x X --window-y Y --scroll S --volume V --um UM`<br>`--letters letters.json --heldout heldout.md --method method.md --checkpoint C --call 'CMD'`<br>`--docker-image REF --out packages/<scroll>_<date>/ [--flattened-by 'vc_flatten ABF++'] [--force]` |
| `verify_package.py` | Re-derives every submission check from the package files: window area, bar length, pixel identity with the source map, PNG = TIFF pixels, mesh hashes, >= 10 letters, eligibility. It prints PASS/FAIL per check and exits non-zero on any FAIL. | P-DRY | `verify_package.py <package dir>` |
| `protocol9.sh` | The automatable parts of MASTER_PROMPT_v4 protocol 9. It alters no map: no enhancement, no threshold, no resample. Steps 2, 3 and 6 are printed as a human checklist. `P9_DRY=1` prints every command and checks every input. | — (protocol 9) | `protocol9.sh <scroll> <vol> <um> <patch_dir>` |
| `protocol9_for.sh` | Derives every `protocol9.sh` argument from a `read_stats.json` and always dry-runs first. It refuses to continue if any input is missing. | — (protocol 9) | `protocol9_for.sh <path/to/read_stats.json> [--go]` |
| `review_folder.py` | The review folder (5.12), built from read directories. It writes contact sheets split into eligible and ineligible, an `INDEX.md` sorted by largest cluster, and overlays labelled "DERIVED OVERLAY FOR EYES ONLY". `--loop N` refreshes it. | — (MASTER_PROMPT_v4 5.12) | `review_folder.py --reads-root reads/ [--out review_sheets] [--loop N] [--max-overlay-px 0]` |

## 7. The 2.4 µm route

Rescan traces at 2.403 µm, run through the team's 2.4 µm model (`scrollprize/ink_canonical_2um`) on CPU.
`render_crest.py` and `render_cover.py` are listed here because only the scripts in this route call them.

| script | purpose | RULES tag | usage |
|---|---|---|---|
| `run_2um.py` | Runs the team's 2.4 µm ink model through villa's `optimized_inference` on a local surface-volume zarr, in both depth orders, on CPU. Output is uint8 maps plus the raw pred/count zarrs. | B-2UM (MASTER_PROMPT_v4 §7) | `run_2um.py <surface.zarr> <out_dir> --tag w028calib --start 23 --end 85 --um 2.399 [--orders forward reverse]`<br>`[--tile 256 --stride 128 --batch 4]` |
| `run_2um_patch.sh` | Renders and reads one level-2 traced rescan patch in a 1 cm² window, in both depth orders: window choice, a 64-slice render, the render crest check, R-COVER, `run_2um.py`, then `read_chart.py`. | B-2UM; R-CREST; R-COVER | `run_2um_patch.sh <scroll> <rescan-vol> <pitch e.g. 2.403um-0.2m-77keV> <um> <patch_dir>` |
| `time_2um_model.py` | Loads the 2.4 µm checkpoint and times one CPU forward pass on a 62x256x256 tile (batch 1 and 4). It projects the cost per 5 cm² and touches no real data. | T-2UM | no usage line; no arguments |
| `window_2um.py` | Chooses the 1 cm² render window of a level-2 traced patch from the trace geometry alone: the k x k block of grid cells with the most valid cells, by coverage first when a coverage grid exists. The maps are never consulted. | B-2UM; R-COVER | no usage line; args `patch_dir`, `--k` |
| `compare_2um_calib.py` | Compares our 2.4 µm map of the w028 calibration crop with the team's published map of the same pixels. It reports Pearson r, AUC, means, and unit-rule levels at the J-w028 thresholds. | B-2UM | `compare_2um_calib.py <ours.tif> <team_pred_crop.npy> <out.json> [--y0 48 --x0 64 --size 4160 --border 64]` |
| `precheck_2um.sh` | Runs QC 5.8 and R-CREST-CT on every traced patch under `patches_2um/<scroll>`, looping until the trace queue is done. | QC 5.8; R-CREST-CT | `precheck_2um.sh <scroll> <rescan-volume-id> <pitch e.g. 2.403um-0.2m-77keV>` |
| `trace_seeds_2um.sh` | Traces the CT-gated seeds of a 2.4 µm rescan on its level-2 surface prediction, one at a time, outer → middle → inner, skipping seeds marked done. | — | `trace_seeds_2um.sh <scroll> <rescan-volume-id>` |
| `render_crest.py` | Runs `read_chart.crest_check` on a render's on-sheet per-slice mean profile (ratio >= 1.20, crest in the central half). Exits 0 on pass and 1 on fail. | R-CREST (on a render) | `render_crest.py <render.zarr> <out.json>` |
| `render_cover.py` | Papyrus coverage of a render: the fraction of pixels whose maximum over the rendered layers exceeds 60. The bar is >= 0.80 before any inference. | R-COVER | `render_cover.py <render.zarr> <out.json> [--thr 60] [--bar 0.8] [--cell-px 20] [--step 2]` |

## 8. Paths and environment variables

Where the scripts look for data:

- **Python scripts that need a data root** read `$HERCULES_DATA` (default `/home/user/hercules_data`). They find the
  repository from their own location (`scripts/..`), not from an environment variable.
- **Shell scripts** read `$HERCULES_DATA` and `$HERCULES_ROOT` (defaults `/home/user/hercules_data` and
  `/home/user/hercules`).
- **Pure tools take every path as an argument and read no `HERCULES_*` variable.** These are: `rule55`,
  `contact_sheet`, `read_chart`, `score_auc`, `rheldout`, `release_stats`, `make_figures`, `fetch_control_w040`,
  `reproduce_control.sh`, `package_submission`, `verify_package`, `review_folder`, `mesh_distortion`, `sheet_seeds`,
  `row_power`, `ct_at_points`, `crop_zarr_stack`, `fetch_pred_box`, `w028_*`, `compare_2um_calib`, `window_2um`,
  `render_crest` and `render_cover`. Two of them read other variables: `reproduce_control.sh` reads `INFER_PY`,
  `PY` and `HF`, and `fetch_pred_box.py` reads `CURL_CA_BUNDLE`.

Since `091c2fa`, every data-root and repository path in the scripts can be overridden (VERIFIED, code read
2026-10-15). `/home/user/hercules_data` and `/home/user/hercules` remain only as the defaults of `$HERCULES_DATA`
and `$HERCULES_ROOT`. In addition:

- `build_vc3d.sh` and `build_vc3d_extra.sh` take the villa checkout from `$VILLA` (default
  `$HERCULES_ROOT/external/villa`).
- `vc_tools.sh` takes its helper interpreter from `$VC_PYTHON`, else the repository's own `.venv/bin/python`, else the
  `python3` on `PATH` (the fallback was added before release; without it, a clone outside `/home/user/hercules` failed
  two `test_render_is_zero` cases and silently disabled the zero-render retry).
- `supervisor.sh` takes its `DENSE` default from `$HERCULES_DATA`.
- The quoted-heredoc Python of `gateB43.sh`, `ggp6_when_ready.sh` and `run_2um_patch.sh` reads `HERCULES_DATA` /
  `HERCULES_ROOT` from the environment.

One host-specific path remains: the proxy CA bundle `/root/.ccr/ca-bundle.crt`. It is bind-mounted into the
container as `/ca.crt` by `build_vc3d.sh` (line 16), `build_vc3d_extra.sh` (line 23), `vc_consensus.sh` (line 44) and
`vc_tools.sh` (line 40). Line 40 of `vc_tools.sh` ignores the `CA=${CURL_CA_BUNDLE:-...}` it sets at line 21; that
variable is used only by the script's own `curl`. On another host, edit those `-v` lines.

Other environment variables that scripts read include:

- **Inference**: `HERCULES_INFER_SLOTS` (default 2), `HERCULES_INFER_LOCK`, `HERCULES_INFER_WORKERS`,
  `HERCULES_MIN_FREE_RENDER_GB`.
- **VC3D tools**: `VC_DRY_RUN`, `VC_THREADS`, `VC_IMAGE`, `VC_PYTHON`, `CURL_CA_BUNDLE`, `RENDER_*` (`vc_tools.sh`);
  `JOBS`, `TARGETS` (`build_vc3d*.sh`), `MIN_FREE_GB` (`build_vc3d_extra.sh`).
- **Code and interpreters**: `VILLA` (`run_2um.py`, `time_2um_model.py`, `build_vc3d.sh`, `build_vc3d_extra.sh`),
  `INFER_PY` / `PY` / `HF` (`reproduce_control.sh`).
- **Dry runs**: `P9_DRY` (`protocol9.sh`).
- **Supervisor and queues**: `COVERAGE`, `DENSE`, `TRACERS`, `TRACE_SLOTS` (`supervisor.sh`), `RS_SUFFIX`, `RS_SEEDS`
  (`rsmall_loop.sh`), `PART` (`ggp4_consensus.sh`).

## 9. Tests

- **Size**: 34 test files in [`tests/`](tests/), 295 test cases (`pytest --collect-only` at `106d3ec`, 2026-10-15;
  `091c2fa` added the `disk_guard` regression test, `d097884` the `window_label_stats` test, `106d3ec` the
  `map_integrity --json` regression test).
- **Last run** (2026-10-15, `106d3ec`): 292 passed, 3 skipped without data (296.63 s). At `82409f4`: 291 passed, 3
  skipped (325.28 s). Before `d097884` added one test:
  290 passed, 3 skipped without data (317 s); 293 passed with the public data staged
  (301 s); 290 passed, 3 skipped in a relocated clone with no repository venv, as on CI (281 s).
- **Run**: from the repository root, with the analysis environment (`pip install -r requirements.txt`, which pins
  pytest):

  ```bash
  HERCULES_DATA=/tmp/no_data python -m pytest scripts/tests -q -rs    # -rs prints the reason of each skip
  ```

- **Data**: the suite is synthetic by default. Tests that need data find it through `$HERCULES_DATA` (default
  `/home/user/hercules_data`). Without that data, three integration tests skip and print their reason:

  | test | needs |
  |---|---|
  | `test_patch_qc.py::test_w040_geometry_reference` | the public w040 mesh at `$HERCULES_DATA/controls/w040/mesh` |
  | `test_patch_qc.py::test_w040_ct_mask_check_and_overlay` | the same mesh, plus network access to the public PHerc0139 volume (level 4) |
  | `test_seeds.py::test_real_phherc0306b_smoke` | the bucket catalogue at `$HERCULES_DATA/cat/metadata.min.json`, plus network |

  [docs/REPRODUCE.md](../docs/REPRODUCE.md) ("Level 1: test suite") gives the commands that fetch both inputs.
  `test_rdepth_part2.py::test_coverage_supplies_every_scroll_the_declared_set_names` returns without asserting
  anything when `$HERCULES_DATA/gates/rdepth/part2_set.json` is absent. It is not a skip, so it counts as passed.
- **Isolation**: tests that run a script set `HERCULES_DATA` explicitly (`test_disk_guard`, `test_map_integrity`,
  `test_ggp5b_decide`, `test_vc_tools`). `test_vc_tools` also removes the caller's value first. `test_run_patch_dir`
  does not set it: through `run_patch_dir.acquire_slot` it creates `$HERCULES_DATA/logs/infer_slots/slot0` under the
  caller's data root, so point `HERCULES_DATA` at a directory you can create (CI uses `/tmp/no_data`).

Which scripts each test file covers:

| test file | covers |
|---|---|
| `test_read_chart.py` | `read_chart.py` (including the truncated-map refusal), `contact_sheet.py`, `rule55.py` |
| `test_rule55.py` | `rule55.py` |
| `test_map_integrity.py` | `map_integrity.py` (PAIR, STALE, `--pair` CLI); `infer_slot.sh` blocks past its cap; `rdepth.sh` verifies before scoring and takes a global slot |
| `test_cluster_power.py` | `cluster_power.py` |
| `test_release_stats.py` | `release_stats.py` (every hand-written RULES value is reproduced) |
| `test_rheldout.py` | `rheldout.py` (synthetic segment at 9.612 µm/px, written before any held-out output existed) |
| `test_rsym_rpop_rctrl55.py` | `rsym.py`, `rpop.py`, `rsens.py`, `rctrl55.py` |
| `test_rblank.py`, `test_rblank2.py` | `rblank.py`, `rblank2.py` |
| `test_gown_result.py` | `gown_result.py` |
| `test_ggp5b_decide.py` | `ggp5b_decide.py` |
| `test_mesh_distortion.py` | `mesh_distortion.py` |
| `test_patch_agreement.py` | `patch_agreement.py` |
| `test_rcross_result.py` | `rcross_result.py` |
| `test_rdepth_result.py`, `test_rdepth_part2.py` | `rdepth_result.py`, `rdepth_part2.sh` |
| `test_reflip_scan.py` | `reflip_scan.py` |
| `test_ct_at_points.py` | `ct_at_points.py` |
| `test_patch_qc.py` | `patch_qc.py` |
| `test_seeds.py`, `test_seeds_cache.py` | `seeds.py` |
| `test_survey_level4.py` | `survey_level4.py` |
| `test_run_patch_dir.py` | `run_patch_dir.py` (command builders tested without running anything) |
| `test_vc_tools.py` | `vc_tools.sh` (via `VC_DRY_RUN=1`) |
| `test_package_submission.py` | `package_submission.py`, `verify_package.py` |
| `test_review_folder.py` | `review_folder.py` |
| `test_protocol9.py` | `protocol9.sh` (dry run) |
| `test_ledger_audit.py` | `ledger_audit.py` |
| `test_sweep_partial_reads.py`, `test_sweep_renders.py` | `sweep_partial_reads.py`, `sweep_renders.py` |
| `test_disk_guard.py` | `disk_guard.sh`, incl. the CT keep-list regression test (bug fixed in `091c2fa`) |
| `test_loop_scripts.py` | queue shape, pause markers and duplicate-read guards in `dense_loop.sh`, `rsmall_loop.sh`, `rsmall2_when_ready.sh`, `rbest*.sh`, `rcrest_power*.sh`, `rdepth_part2.sh`, `supervisor.sh` |
| `test_supervisor_inline.py` | `supervisor.sh`; that every script in `scripts/` parses (`bash -n`) and that long jobs live in their own files |
| `test_window_label_stats.py` | `examples/window_label_stats.py` (synthetic labels around the quick-start window) |
