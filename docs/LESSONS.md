# Lessons

This document lists the defects this project found in its own pipeline and in its own record, what each defect did
to a number, and what was changed so that it cannot happen again without being noticed. Lessons 1 to 33 keep the
numbering of the release's evidence extraction (topic T6, "Defects found and fixed"). Lessons 34 to 37 were found
while preparing this release on 2026-10-15.

Nothing in this document reports a letter, a reading or ink on an eligible scroll. No PROMISING CANDIDATE has ever
been produced on an eligible scroll. **MEASURED** [`STATE.md:6`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L6) `@23528c9` [`STATE.md:20`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L20) `@71720ce`

Related documents: every result in [RESULTS](RESULTS.md), the pipeline and its parameters in [METHODS](METHODS.md),
withdrawn and corrected claims in [SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md), and the commands that re-create the
control numbers in [REPRODUCE](REPRODUCE.md). The lab notebook is [`RULES.md`](../RULES.md). There is one line per
read in [`LEDGER.md`](../LEDGER.md).

## How to read this document

- **Labels.** Each factual statement carries one label.
  - **VERIFIED**: re-checked for this release. That means code read at the cited commit, a test run on 2026-10-15, a
    recomputation by a committed script, or a committed file or external file read on 2026-10-15.
  - **MEASURED**: a value from one recorded run, as the notebook states it, not re-derived here.
  - **INFERENCE**: an interpretation, a declared practice or a decision.
- **Registration**, where a result is quoted: PRE-REGISTERED (bar committed before the result), EXPLORATORY or
  DESCRIPTIVE.
- **Citations.** Each `file:line` link is a permalink at commit `71720ce`. Lines 1 to 3202 of `RULES.md` are
  byte-identical at `71720ce` and in the release tree. The short hash after the link is the commit that introduced
  the text. Lines of `RULES.md` above 3202, and files added after `71720ce`, link to their introducing commit
  instead. Some files were edited after `71720ce` (scripts in `fed6602`, `e993fbe` and `091c2fa`; `STATE.md` in
  `5cf8976`; `scripts/release_stats.py` and `records/release/release_stats.json` in `7925b3a`), so a cited line can
  sit lower in the release tree: by up to 14 lines in `scripts/read_chart.py` and 37 in `STATE.md`. The permalinks
  still resolve to the exact text cited.
- **Tests.** Each **Fix** names the tests that pin it, written as `file::test`. For this document the 21 test files
  named below were run on 2026-10-15 at `4d4ef53`, with `HERCULES_DATA` pointing at an empty directory: **229
  passed, 0 failed** (229 collected; some tests are parametrised). **VERIFIED** That run does not exercise behaviour
  that needs the public data. Where no test pins a fix, the lesson says so.
- **"Why it matters"** and **"Generalises to"** are this document's reasoning, **INFERENCE** throughout, unless a
  sentence carries its own label and citation.
- **Numbers** are copied from their sources and never rounded. Where two sources disagree, both are given. The
  disagreements are collected in the [appendix](#appendix-a-source-conflicts-and-open-items).

## Index

Categories: **data integrity** (a file, list or count that was wrong or incomplete), **statistics** (an estimate,
bound or test that was wrong), **validation** (a check of the instrument that was missing or misread),
**operations** (processes, queues, disk and clocks), **interpretation** (a reading of correct numbers that went
further than they allow).

| # | Rule | Category | Fix in |
|---|---|---|---|
| [1](#1-check-that-both-maps-of-a-pair-are-complete-before-scoring-them) | Check that both maps of a pair are complete before scoring them | data integrity | `scripts/read_chart.py`, `scripts/map_integrity.py`, `scripts/run_patch_dir.py` |
| [2](#2-write-integrity-checks-as-relative-tests-not-absolute-bars) | Write integrity checks as relative tests, not absolute bars | data integrity | `scripts/map_integrity.py` |
| [3](#3-when-two-code-paths-disagree-use-neither-number-until-the-disagreement-is-explained) | When two code paths disagree, use neither number until the disagreement is explained | validation | `scripts/rctrl55.py` |
| [4](#4-measure-how-much-of-each-unit-is-labelled-before-binning-units-by-labelled-ink) | Measure how much of each unit is labelled before binning units by labelled ink | statistics | `RULES.md` (curve withdrawn); `scripts/rheldout.py` |
| [5](#5-check-a-list-against-its-own-recorded-count-before-drawing-a-population-from-it) | Check a list against its own recorded count before drawing a population from it | data integrity | `scripts/rpop.py` |
| [6](#6-restart-every-running-loop-after-fixing-its-script-committing-is-not-deploying) | Restart every running loop after fixing its script; committing is not deploying | operations | `scripts/rbest2.sh`, `scripts/rdepth_part2.sh` |
| [7](#7-never-edit-a-shell-script-while-it-is-running) | Never edit a shell script while it is running | operations | none (practice) |
| [8](#8-key-every-cache-by-its-source-as-well-as-its-item) | Key every cache by its source as well as its item | data integrity | `scripts/seeds.py` |
| [9](#9-report-progress-with-the-same-counter-the-gate-uses) | Report progress with the same counter the gate uses | operations | progress monitor (code not located) |
| [10](#10-track-processes-by-their-own-pid-files-not-by-matching-command-lines) | Track processes by their own pid files, not by matching command lines | operations | `scripts/ggp5_when_ready.sh` |
| [11](#11-gate-commits-on-the-test-runners-own-exit-status-and-keep-tests-independent-of-machine-state) | Gate commits on the test runner's own exit status, and keep tests independent of machine state | operations | `scripts/run_patch_dir.py`, `scripts/tests/test_run_patch_dir.py` |
| [12](#12-take-timestamps-from-the-system-clock-not-from-notifications-or-estimates) | Take timestamps from the system clock, not from notifications or estimates | operations | none (practice) |
| [13](#13-ship-the-inputs-a-verifier-needs-inside-the-package-it-verifies) | Ship the inputs a verifier needs inside the package it verifies | data integrity | `scripts/package_submission.py`, `scripts/verify_package.py` |
| [14](#14-derive-identifiers-from-the-one-configured-source-never-from-memory) | Derive identifiers from the one configured source, never from memory | data integrity | `scripts/protocol9_for.sh`, `scripts/rbest2.sh` |
| [15](#15-delete-only-files-that-are-marked-complete-and-have-been-idle-for-a-set-time) | Delete only files that are marked complete and have been idle for a set time | operations | `scripts/sweep_renders.py`, `scripts/rbest.sh` |
| [16](#16-do-not-reclaim-disk-from-under-a-live-process) | Do not reclaim disk from under a live process | operations | `scripts/disk_guard.sh` |
| [17](#17-read-a-queue-into-memory-before-the-loop-and-close-the-stdin-of-every-child) | Read a queue into memory before the loop, and close the stdin of every child | operations | `scripts/dense_loop.sh` |
| [18](#18-check-that-a-published-tool-image-can-run-the-documented-command-before-using-it) | Check that a published tool image can run the documented command before using it | validation | `scripts/build_vc3d.sh` |
| [19](#19-do-not-read-a-high-forward-level-as-ink-decide-on-the-depth-order-margin) | Do not read a high forward level as ink; decide on the depth-order margin | interpretation | none (no bar moved) |
| [20](#20-compute-expected-candidate-counts-from-the-real-per-surface-layouts-not-from-one-pooled-grid) | Compute expected candidate counts from the real per-surface layouts, not from one pooled grid | statistics | `scripts/cluster_power.py` |
| [21](#21-test-a-models-independence-assumption-on-the-control-before-quoting-its-estimate) | Test a model's independence assumption on the control before quoting its estimate | statistics | `RULES.md` (claim withdrawn); `scripts/release_stats.py` |
| [22](#22-test-competing-explanations-of-a-number-before-naming-its-cause) | Test competing explanations of a number before naming its cause | interpretation | `RULES.md` (reading withdrawn) |
| [23](#23-use-a-proxy-only-after-it-has-predicted-the-quantity-it-stands-for) | Use a proxy only after it has predicted the quantity it stands for | validation | `scripts/coverage_proxy.py` (used for nothing) |
| [24](#24-prove-that-a-conservative-bound-is-a-bound-before-relying-on-it) | Prove that a "conservative" bound is a bound before relying on it | statistics | `scripts/rblank2.py` |
| [25](#25-give-every-output-directory-a-reader-and-check-that-it-has-one) | Give every output directory a reader, and check that it has one | operations | `scripts/supervisor.sh` |
| [26](#26-run-one-queue-per-population-enforced-by-a-process-check-rather-than-a-marker-file) | Run one queue per population, enforced by a process check rather than a marker file | operations | `scripts/supervisor.sh`, `scripts/rbest.sh`, `scripts/rbest2.sh` |
| [27](#27-sweep-away-the-partial-outputs-of-killed-runs-before-anything-can-score-them) | Sweep away the partial outputs of killed runs before anything can score them | data integrity | `scripts/sweep_partial_reads.py` |
| [28](#28-write-a-number-into-the-record-only-after-its-computation-has-printed) | Write a number into the record only after its computation has printed | statistics | `scripts/release_stats.py` |
| [29](#29-count-a-surface-once-however-many-files-it-was-written-to) | Count a surface once, however many files it was written to | data integrity | `scripts/cluster_power.py` |
| [30](#30-after-a-restart-check-what-actually-stopped-before-acting) | After a restart, check what actually stopped before acting | operations | `scripts/supervisor.sh` |
| [31](#31-give-every-component-of-the-chain-including-your-own-tracer-a-positive-control-on-known-text) | Give every component of the chain, including your own tracer, a positive control on known text | validation | `scripts/gown_result.py` |
| [32](#32-when-sheet-orientation-is-unknown-read-both-depth-orders-and-keep-a-tripwire-on-the-swapped-one) | When sheet orientation is unknown, read both depth orders and keep a tripwire on the swapped one | interpretation | `scripts/read_chart.py`, `scripts/gown_result.py` |
| [33](#33-optimise-the-quantity-that-decides-the-result-valid-units-not-a-proxy-for-it-area) | Optimise the quantity that decides the result (valid units), not a proxy for it (area) | interpretation | none; `scripts/cluster_power.py --read-stats` |
| | **Found while preparing this release** | | |
| [34](#34-read-the-models-training-config-before-calling-a-control-held-out) | Read the model's training config before calling a control held-out | validation | `RULES.md` (R-HELDOUT), `scripts/rheldout.py` |
| [35](#35-do-not-compute-unit-level-p-values-as-if-clustered-units-were-independent) | Do not compute unit-level p-values as if clustered units were independent | statistics | `scripts/release_stats.py` |
| [36](#36-re-check-published-tool-images-at-release-a-web-page-calling-an-image-up-to-date-is-not-a-test) | Re-check published tool images at release; a web page calling an image up to date is not a test | validation | `docs/REPRODUCE.md`, `scripts/build_vc3d.sh` |
| [37](#37-recompute-numbers-from-the-files-that-produced-them-do-not-copy-them-by-hand) | Recompute numbers from the files that produced them; do not copy them by hand | data integrity | `scripts/release_stats.py`, `examples/check_quickstart.py` |

---

### 1. Check that both maps of a pair are complete before scoring them

**What happened.** R-DEPTH was first recorded as ADMITTED: `max(M) − M(CENTRE) = +0.13786` against the declared bar
of +0.05, with M(HIGH) = 0.60594. **MEASURED** (PRE-REGISTERED) [`RULES.md:1576`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1576) `@8328202` The HIGH reverse map
`gates/rdepth/high_reverse.tif` was 25.00 % non-zero, exactly one quadrant, while its forward map was 100 % non-zero.
The inference had exited 0 and the file was scored as complete. **MEASURED** [`RULES.md:1620`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1620) `@750629f` Every HIGH
number was withdrawn. **INFERENCE** [`RULES.md:1625`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1625) `@750629f` The truncation was caught only because R-CTRL55-W ran
the frozen rule on the same maps and every unit came back with `rev 0.0000`. **MEASURED** [`RULES.md:1632`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1632) `@750629f`
Re-run on a complete, audited pair, M(HIGH) is 0.39948 and R-DEPTH FAILS. The earlier 0.60594 was computed on a reverse map
that was 0 on the other 75 % of its pixels, and those zeros were averaged in. **MEASURED** (PRE-REGISTERED)
[`RULES.md:2015`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2015) `@0423a76` That those zeros account for the whole difference is **INFERENCE**: no
comparison of the non-zero quadrant with the complete re-run is recorded. An audit of every pair on disk then found 55 pairs checked, 54 sound and exactly one
suspect, `gates/rdepth/high`. **MEASURED** [`RULES.md:1638`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1638) `@750629f` A second truncated reverse map (PHerc1203
`team_20250923163331524` TTA, coverage 0.9404 against forward 1.0000, footprints 0.0486 apart) was refused by the new
guard before it was scored. **MEASURED** [`RULES.md:1741`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1741) `@2d9e698`

**Why it matters.** **INFERENCE** Reverse pixels with no prediction read as zero. They lower the reverse mean and inflate the
margin, so a truncated reverse map pushes a unit toward FLAGGED, not away from it [`RULES.md:1746`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1746) `@2d9e698`. Here
the artefact turned a pre-registered FAIL into ADMITTED. An exit status of 0 said nothing about the file.

**Fix.** `scripts/read_chart.py` refuses any read whose two maps' non-zero footprints differ by more than 0.02, or
whose on-sheet coverage is below 0.99. There is no switch to turn the guard off. **VERIFIED** [`RULES.md:1645`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1645) `@750629f`
[`scripts/read_chart.py:35`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L35) `@750629f` `scripts/map_integrity.py` applies the same two tests across the corpus (coverage only
where the read's render survives), and since `fed6602` to a single pair with `--pair` (coverage only when
`--render-dir` is given). **VERIFIED** [`scripts/map_integrity.py:38`](https://github.com/abundantjoe/hercules/blob/fed6602/scripts/map_integrity.py#L38) `@fed6602` Seven scripts had used separate inference locks, none
serialising against the others, so the locks allowed up to eight inferences to share four cores; the runner of the
first truncation (`rdepth.sh`) took no lock at all (commit `acc775f`). The load average was 10–14 that night, and both truncations happened
under that load. **INFERENCE**
[`RULES.md:1757`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1757) `@a0c1f8c` A global cap of two inference slots now applies to every caller. **VERIFIED**
[`RULES.md:1762`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1762) `@a0c1f8c` [`scripts/run_patch_dir.py:148`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L148) `@a0c1f8c` The cause of the truncation itself
is still unproven. **MEASURED** [`RULES.md:1768`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1768) `@a0c1f8c` Pinned by
`scripts/tests/test_read_chart.py::test_truncated_reverse_map_is_refused`,
`scripts/tests/test_read_chart.py::test_a_complete_pair_is_not_refused_by_the_guard`,
`scripts/tests/test_map_integrity.py::test_catches_the_one_quadrant_reverse_map`,
`scripts/tests/test_map_integrity.py::test_single_pair_cli_refuses_a_truncated_pair_and_passes_a_sound_one` and
`scripts/tests/test_run_patch_dir.py::test_slots_are_exclusive_and_block_beyond_the_cap`. On the committed w040
window, a reverse map with only one quadrant non-zero is refused by both tools (PAIR 0.7500). Without the guard the same
maps report unit margins up to +0.3132, against a true maximum of +0.0818. **VERIFIED** (quick start run for this
document, 2026-10-15) [`examples/check_quickstart.py:44`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/check_quickstart.py#L44) `@0afc07e` [`examples/check_quickstart.py:50`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/check_quickstart.py#L50) `@0afc07e`
[`examples/README.md:31`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L31) `@2bf30b3`

**Generalises to.** Before scoring any pair of prediction maps, compare their footprints and coverage: an inference
that exits 0 can still leave regions of a map at 0, and in a forward-minus-reverse statistic an incomplete reverse map
looks like ink.

### 2. Write integrity checks as relative tests, not absolute bars

**What happened.** The first map-integrity checker used an absolute bar on the non-zero fraction and flagged 19
perfectly good corpus maps, because auto-cropped surface renders normally sit at a non-zero fraction of 0.60-0.84.
**MEASURED** [`RULES.md:1641`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1641) `@750629f` A STALE-pair check added later used another absolute bar (maps written more
than an hour apart), on the false assumption that `--direction both` writes both maps together. It flagged 4 sound
pairs on its first run. **MEASURED** [`RULES.md:2957`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2957) `@4ac46f1` [`RULES.md:2958`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2958) `@4ac46f1` For those four, the mtime skew was half the recorded
inference time in every case (ratios 0.50, 0.46, 0.52, 0.52), which is what sequential forward-then-reverse writing
produces. **VERIFIED** [`RULES.md:2964`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2964) `@4ac46f1` [`RULES.md:2965`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2965) `@4ac46f1`
[`RULES.md:2966`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2966) `@4ac46f1` [`RULES.md:2967`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2967) `@4ac46f1` [`RULES.md:2969`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2969) `@4ac46f1`

**Why it matters.** **INFERENCE** A fixed threshold on a quantity that varies by design flags normal outputs. A
check that raises false alarms gets ignored, and then it misses the real failure.

**Fix.** PAIR and COVERAGE in `scripts/map_integrity.py` compare the two maps of a pair with each other. STALE
compares the skew with the read's own inference time (`s_infer`) plus 600 s of slack, and skips reads with no
throughput record. The live audit after the fix gave 64 pairs, 64 sound, 0 SUSPECT. **MEASURED**
[`RULES.md:2975`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2975) `@4ac46f1` [`scripts/map_integrity.py:41`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/map_integrity.py#L41) `@4ac46f1` Pinned by
`scripts/tests/test_map_integrity.py::test_does_not_flag_an_auto_cropped_surface_whose_maps_are_partly_zero`,
`::test_sequential_writes_on_a_slow_read_are_NOT_stale`, `::test_the_bar_is_the_reads_own_cost_not_a_constant` and
`::test_a_read_with_no_recorded_inference_time_is_SKIPPED_not_guessed`.

**Generalises to.** Segment renders differ in crop, coverage and run time, so integrity bars should compare a file
with its own partner or with its own recorded cost.

### 3. When two code paths disagree, use neither number until the disagreement is explained

**What happened.** `scripts/rctrl55.py` passed the `best_origin` tuple `(94, 188)` where `rule55.evaluate` expects
the string `"auto"` or `"fixed"`. The call fell into the `else` branch and silently tiled from `(0, 0)`, while the
log printed `(94, 188)`. **VERIFIED** [`RULES.md:1478`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1478) `@140730b` The first R-CTRL55 run therefore reported FLAGGED 6
of 67, cluster sizes [3, 1, 1, 1]. **MEASURED** (PRE-REGISTERED) [`RULES.md:1408`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1408) `@3084d12` It was caught because
`read_chart.py --maps-only` on the same two maps reported 7 of 71. **VERIFIED** [`RULES.md:1482`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1482) `@140730b` The
authoritative result is 80 units, 71 valid, 7 flagged, cluster sizes [4, 2, 1], and the two code paths agree exactly.
**VERIFIED** [`RULES.md:1487`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1487) `@140730b` [`RULES.md:1488`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1488) `@140730b` The standing practice was written down with the
fix: when two paths over the same data disagree, neither number is used until the disagreement is explained.
**INFERENCE** [`RULES.md:1484`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1484) `@140730b` On 2026-10-15 a fresh-container re-run gave 71 valid, 7 flagged, clusters
[4, 2, 1] from `rctrl55.py`, and 7/71, largest cluster 4, from `read_chart.py --maps-only`. **VERIFIED**
[`RULES.md:3275`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3275) `@eed0fac` [`RULES.md:3277`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3277) `@eed0fac`

**Why it matters.** **INFERENCE** The wrong grid changed a headline count, and the script's own log line hid the
change. Only a second, independent path exposed it. The same habit exposed lesson 1.

**Fix.** `rctrl55.py` now passes `"auto"` and asserts that the grid origin it gets back equals `best_origin`'s.
**VERIFIED** [`scripts/rctrl55.py:38`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rctrl55.py#L38) `@140730b` [`scripts/rctrl55.py:45`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rctrl55.py#L45) `@140730b` Pinned by
`scripts/tests/test_rsym_rpop_rctrl55.py::test_rctrl55_passes_the_auto_grid_not_a_tuple`.

**Generalises to.** Compute every headline number along two independent code paths, and treat any disagreement
between them as a defect to explain before either number is used.

### 4. Measure how much of each unit is labelled before binning units by labelled ink

**What happened.** The first R-CTRL55 write-up claimed a sensitivity curve: of 17 valid units with φ ≥ 0.02, 3
flagged, with firing beginning around φ ≈ 0.11 and absent below φ ≈ 0.09. **INFERENCE** (EXPLORATORY)
[`RULES.md:1415`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1415) `@3084d12` The w040 supervision mask covers 3.19 % of the canvas. Over the 67 valid units the median
per-unit coverage is 0.0000 (maximum 0.3118; only 18 units above 5 % and 3 above 20 %), so the bins and the curve
were withdrawn. **MEASURED** [`RULES.md:1457`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1457) `@fc54855` Recomputed over supervised pixels only, the 5 of the 6
flagged units that had any supervision were all heavily inked where the labeller looked (φ|sup 0.4132 to 0.9108);
the sixth had no supervised pixels, and none was demonstrably blank. **MEASURED** [`RULES.md:1462`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1462) `@fc54855`
[`RULES.md:1463`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1463) `@fc54855` [`RULES.md:1464`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1464) `@fc54855` Separately, R-SENS arm 1's area-mixture floor (binding φ ≥ 0.2608) proved
wrong as a bound: unit (1,3) fired at φ 0.1087, forward 0.4043, margin +0.0919. **MEASURED** [`RULES.md:1412`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1412) `@3084d12`

**Why it matters.** **INFERENCE** Where most of a unit was never labelled, its labelled-ink fraction φ describes the
labeller's coverage, not the papyrus. A φ = 0 unit was mostly unexamined, not blank. A sensitivity curve built on it
would have been used to price every corpus negative.

**Fix.** No code changed at the time. The curve was withdrawn in `RULES.md`. The held-out test declared on
2026-10-15 builds the lesson into code: a blank unit needs φ = 0 with at least 50 % of it supervised, and a
text-bearing unit needs φ ≥ 0.02. **VERIFIED** [`RULES.md:3258`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3258) `@661ff64` [`RULES.md:3259`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3259) `@661ff64`
[`scripts/rheldout.py:30`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L30) `@d8c39a3` The supervision threshold is exercised by
`scripts/tests/test_rheldout.py::test_text_units_flag_blank_units_do_not_and_the_verdict_is_strong`. No test
isolates it. On PHerc0841 no unit met the blank criterion (0 of 0), so R-HELDOUT's blank arm is empty, not passed.
**MEASURED** [`RULES.md:3309`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3309) `@7925b3a` [`RULES.md:3310`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3310) `@7925b3a`

**Generalises to.** Before using sparse labels to call a tile blank or to bin tiles by ink fraction, report each
tile's label coverage and leave out tiles the labeller never examined.

### 5. Check a list against its own recorded count before drawing a population from it

**What happened.** 41 of the 50 reads that carry a rule 5.5 table had a correct `n_valid` but an empty `valid_units`
list in the forward table. The first R-POP therefore drew its corpus from 9 reads and 24 units, and reported
POP-SHIFT (−0.0389). **MEASURED** [`RULES.md:1528`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1528) `@2fffd22` The forward population was rebuilt exactly from the
swapped table's mirror: "106 plain units over 29 reads (9 direct + 37 mirrored), 54 TTA units over 17 reads". No
verdict was affected, because `n_valid` and `n_flagged` are computed from the arrays. **VERIFIED**
[`RULES.md:1536`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1536) `@2fffd22` With the corrected population R-POP is POP-SHIFT at a margin median difference of −0.0210
(missing POP-MATCH by 0.001), and POP-NARROW is ruled out at an IQR ratio of 0.967. **MEASURED** (DESCRIPTIVE. The
entry's heading says the bars were declared before the run, but the bars and the result were committed together in
`2fffd22`, after a first, invalid run, so git order cannot confirm pre-registration.)
[`RULES.md:1543`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1543) `@2fffd22` [`RULES.md:1502`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1502) `@2fffd22` [`RULES.md:1525`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1525) `@2fffd22`

**Why it matters.** **INFERENCE** The count and the list disagreed silently. A population of 24 units drawn from 9
reads would have been reported as the corpus.

**Fix.** `units_of()` in `scripts/rpop.py` uses the forward list when it is populated. Otherwise it mirrors the
swapped table, and it refuses to mirror when the two tables disagree on `n_valid`. **VERIFIED**
[`scripts/rpop.py:14`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rpop.py#L14) `@2fffd22` [`scripts/rpop.py:33`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rpop.py#L33) `@2fffd22` The writer that produced the empty lists was not
fixed at source. The record says only that "a later summarisation path wrote them" [`RULES.md:1530`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1530) `@2fffd22`.
Pinned by `scripts/tests/test_rsym_rpop_rctrl55.py::test_units_of_mirrors_the_swapped_table_when_the_forward_list_is_empty`,
`::test_units_of_refuses_to_mirror_when_the_two_tables_disagree_on_n_valid` and
`::test_mirror_round_trips_to_the_forward_table_on_a_read_that_has_both`.

**Generalises to.** When a record carries both a count and the list it counts, check that they agree before
building a population from the list.

### 6. Restart every running loop after fixing its script; committing is not deploying

**What happened.** `rbest2.sh` passed the patches directory name as `--scroll`, so `volume_info` raised
`KeyError: 'PHerc0826_small'` and every `PHerc0826_small` member of the declared R-BEST-2 population crashed.
**MEASURED** [`RULES.md:1750`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1750) `@2d9e698` It was fixed in `rbest2.sh`, and pre-emptively in `rdepth_part2.sh`, which passes
`--scroll "${scroll%%_*}"`. **VERIFIED** (code read) [`scripts/rdepth_part2.sh:26`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rdepth_part2.sh#L26) `@2d9e698` The fix was
committed at ~03:05 and did nothing until 05:24: the loop running since before then kept raising the same KeyError
on every pass until it was killed and restarted through the supervisor. **MEASURED** [`RULES.md:2083`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2083) `@0f73e04` The
practice written down: a fix to a script is not in effect until every loop running that script has been restarted,
and the restart is part of the fix. **INFERENCE** [`RULES.md:2089`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2089) `@0f73e04` The same thing happened with the
one-trace-slot decision (lesson 16).

**Why it matters.** **INFERENCE** The notebook recorded the defect as fixed while it was still crashing every pass.

**Fix.** `rbest2.sh` derives the scroll from the directory name. **VERIFIED** [`scripts/rbest2.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rbest2.sh#L19) `@2d9e698`
Pinned by `scripts/tests/test_loop_scripts.py::test_read_loops_pass_the_real_scroll_not_the_patches_directory` and
`::test_read_loops_still_use_the_directory_for_the_patches_path`. No test pins the restart practice.

**Generalises to.** After fixing a script that long-running jobs execute, restart those jobs and confirm from their
logs that the new code is running.

### 7. Never edit a shell script while it is running

**What happened.** `rdepth.sh` was edited while it was running (~03:05 UTC, to add the `infer_slot.sh` wrapper).
bash reads a script lazily by byte offset, so the HIGH result was declared not believed until its maps had been
audited by hand. **INFERENCE** [`RULES.md:1982`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1982) `@688f515` The hazard then happened. The edited script died on a
shifted byte offset (`line 38: f.tif: command not found`, `line 40: syntax error`) after writing and scoring both
maps and before `rdepth_result.py`. The pair was audited by hand and scored manually. **MEASURED**
[`RULES.md:1996`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1996) `@0423a76`

**Why it matters.** **INFERENCE** A running bash process executes whatever bytes now sit at its old offset, so a
partial run can complete some steps and silently skip others.

**Fix.** Practice only: copy the script, edit the copy and swap it in between runs, or stop the job first.
**INFERENCE** [`RULES.md:1990`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1990) `@688f515` It was applied later: the disk guard's two-tier change was made with the
guard stopped. **VERIFIED** [`scripts/disk_guard.sh:17`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L17) `@658d5c2` No test pins this practice.

**Generalises to.** Treat a shell script that a long job is executing as read-only until the job has stopped.

### 8. Key every cache by its source as well as its item

**What happened.** Regenerating R-SMALL-2 seeds for PHerc0826 and then PHerc0358 through one shared `--cache`
produced 90 seeds identical between the two scrolls. PHerc0826's level-3 shape [2115, 1022, 1022] appeared under
PHerc0358's own URL, because cache files were named by chunk key alone. **MEASURED** [`RULES.md:1886`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1886) `@c2cafd6` The
historical seed files `seeds/PHerc0826.json` and `seeds/PHerc0358.json` have zero overlap in 90 seeds, so no trace
on record was seeded from the wrong volume. **VERIFIED** [`RULES.md:1893`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1893) `@c2cafd6`

**Why it matters.** **INFERENCE** The output looked valid. It was caught only because two different scrolls cannot
have identical numbers.

**Fix.** `scripts/seeds.py` keeps cache files under a namespace `sha1(base)[:12]` derived from the source URL.
**VERIFIED** [`RULES.md:1897`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1897) `@c2cafd6` [`scripts/seeds.py:54`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/seeds.py#L54) `@c2cafd6` The fixed seeder gives zero overlapping seeds, with
distinct shapes [2115, 1022, 1022] and [1843, 973, 973]. **MEASURED** [`RULES.md:1903`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1903) `@6582782`
[`RULES.md:1904`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1904) `@6582782` Pinned by
`scripts/tests/test_seeds_cache.py::test_two_sources_get_different_cache_namespaces`,
`::test_the_namespace_is_stable_and_ignores_a_trailing_slash` and `::test_cached_chunks_land_under_the_namespace`.

**Generalises to.** A chunk cache shared across volumes must include the volume URL in its key, or one volume's data
will be served for another's.

### 9. Report progress with the same counter the gate uses

**What happened.** The progress monitor counted `x.tif` files in `patches/PHerc0826_dense`, which also holds part
4's 25 patches, against a part-5 denominator of 60. It read "59/60" and then "60/60" while the gate's own `.done`
counter stood at 34 and then 36 of 60. The owner was told twice that the queue was finishing. **MEASURED**
[`RULES.md:2098`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2098) `@6370950`

**Why it matters.** **INFERENCE** Decisions about waiting, pausing and reporting were being made on a number that
counted something else.

**Fix.** The monitor now reports the number the gate uses. Nothing measured was affected, because
`ggp5_when_ready.sh` always gated on the `.done` counter. **INFERENCE** [`RULES.md:2101`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2101) `@6370950` The monitor's code
was not located for this release, and no test pins it.

**Generalises to.** A progress display should read the same counter as the gate it reports on, not a file count in a
directory that other jobs share.

### 10. Track processes by their own pid files, not by matching command lines

**What happened.** `ggp5_when_ready.sh` guarded the part-5 consensus build with `pgrep -fc "dense_loop.sh $sc"`. That
pattern matched the script's own launching shell, so it refused to build with both dense queues already finished (84
and 85 patches). **MEASURED** [`RULES.md:2149`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2149) `@ad8359f` The record also says `pkill -f` had matched the operator's
own shell three times. **MEASURED** [`RULES.md:2989`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2989) `@8aab40d` After the 13:38 UTC session restart on 2026-09-19, a
check reported a second queue pid that was the check's own `grep` subshell. A single queue (pid 13503) was confirmed
with `ps -eo pid,ppid,lstart,args`. **MEASURED** [`RULES.md:3181`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3181) `@db29af2` [`RULES.md:3182`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3182) `@db29af2`
[`RULES.md:3183`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3183) `@db29af2`

**Why it matters.** **INFERENCE** A guard that matches its own caller either blocks forever or reports a duplicate
that does not exist.

**Fix.** `ggp5_when_ready.sh` checks the loops' own pid files with `kill -0`. **VERIFIED**
[`scripts/ggp5_when_ready.sh:18`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/ggp5_when_ready.sh#L18) `@ad8359f` [`scripts/ggp5_when_ready.sh:24`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/ggp5_when_ready.sh#L24) `@ad8359f` No test pins this switch.
`scripts/tests/test_supervisor_inline.py::test_ggp5_consensus_build_is_armed_and_cannot_fire_twice` still asserts
that `pgrep -f` appears in the supervisor's G-GP part 5 block, and `supervisor.sh` still uses `pgrep -f` as a guard.
**VERIFIED** [`scripts/supervisor.sh:215`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L215) `@4d7ac37` That use has not been shown to be a defect. It is the remaining
surface of the pattern.

**Generalises to.** Identify a job by the pid it wrote at start-up; a pattern match on command lines also matches the
shell that runs the match.

### 11. Gate commits on the test runner's own exit status, and keep tests independent of machine state

**What happened.** A commit was made on a red suite. The command was `pytest ... | tail -4 && git commit && git
push`, and `&&` chains off `tail`, whose exit status is 0 whatever pytest returned. Ten tests had failed.
**MEASURED** [`RULES.md:333`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L333) `@6694d0a` The ten failures came from a test-isolation defect. The render disk floor
called `os.statvfs(DATA_ROOT)`, the real data root, so `process_patch` refused to render in unit tests whenever free
disk was under 5 GB. The suite passed or failed with the state of the machine. **MEASURED** [`RULES.md:334`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L334) `@6694d0a`

**Why it matters.** **INFERENCE** A pipeline whose gate reads the wrong exit status ships whatever the tests say.
Tests that depend on free disk fail exactly when the guarded situation occurs.

**Fix.** The floor now measures `os.statvfs(patch)`, the filesystem the render is written to, and the test fixture
sets `MIN_FREE_RENDER_GB = 0`. **VERIFIED** [`scripts/run_patch_dir.py:301`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/run_patch_dir.py#L301) `@6694d0a`
[`scripts/tests/test_run_patch_dir.py:88`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_run_patch_dir.py#L88) `@6694d0a` The floor itself is exercised by
`scripts/tests/test_run_patch_dir.py::test_a_render_does_not_start_below_the_disk_floor`. For pipes, the record says
only that any future gating run must read pytest's own exit status, and no test pins that practice
[`RULES.md:333`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L333) `@6694d0a`. The release's quick start runs under `set -euo pipefail`. **VERIFIED**
[`examples/quickstart.sh:6`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/quickstart.sh#L6) `@0afc07e`

**Generalises to.** In shell, `cmd | tail` returns `tail`'s status: use `set -o pipefail` or `PIPESTATUS` wherever an
exit code gates anything, and give tests their own resource limits.

### 12. Take timestamps from the system clock, not from notifications or estimates

**What happened.** Timestamps taken from scheduled-trigger notifications and from a running estimate were about two
hours fast. The container clock read 03:00:31 UTC when the entries said 05:20. Order and measured numbers are
unaffected, the entries were not edited, and later timestamps come from `date -u`. **MEASURED**
[`RULES.md:1737`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1737) `@2d9e698` Durations taken from the fast labels disagree with git. "I am correcting it 35 minutes
later" [`RULES.md:1631`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1631) `@750629f` rests on the labels 03:45 and 04:20 [`CHANGELOG.md:420`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L420) `@5c6613d`, while the ADMITTED commit
[`8328202`](https://github.com/abundantjoe/hercules/commit/8328202) is dated 2026-09-19 02:33:11 UTC and the
withdrawal commit [`750629f`](https://github.com/abundantjoe/hercules/commit/750629f) 02:45:37 UTC. **VERIFIED**
(`git log`, 2026-10-15)

**Why it matters.** **INFERENCE** Claims such as "declared before the run" and "corrected within minutes" rest on
timestamps. Commit times are the record a sceptical reader can check.

**Fix.** Practice: loops stamp their own logs with `date -u`. **VERIFIED** [`scripts/dense_loop.sh:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/dense_loop.sh#L22) `@2a7f98e` No
test pins this.

**Generalises to.** Take timestamps from the system clock at the moment of the event, and check any duration that
matters against commit times.

### 13. Ship the inputs a verifier needs inside the package it verifies

**What happened.** Re-running P-DRY's verifier reported 3 FAIL where P-DRY declares exactly 2. The third check
failed because it re-opened the source render zarr, which the disk guard and `--delete-renders` remove, so a package
stopped being verifiable once its render was pruned. **MEASURED** [`RULES.md:1942`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1942) `@2255b76`

**Why it matters.** **INFERENCE** A submission that can only be verified on the machine and the day that produced
it cannot be verified by a judge.

**Fix.** `scripts/package_submission.py` writes the raw CT crop into the package as `ct_window_source.tif` and
records its sha256 in the manifest. `scripts/verify_package.py` checks the sha, checks the PNG against the crop,
checks the live render only when it is present, and reports a check whose input is gone as N/A. **VERIFIED**
[`RULES.md:1948`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1948) `@2255b76` [`scripts/package_submission.py:204`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/package_submission.py#L204) `@2255b76` [`scripts/verify_package.py:84`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/verify_package.py#L84) `@2255b76`
Pinned by `scripts/tests/test_package_submission.py::test_package_carries_its_own_ct_crop_and_verifies_without_the_render`,
`::test_a_tampered_packaged_ct_crop_is_caught_by_its_sha256` and
`::test_a_package_with_no_ct_crop_is_refused_not_skipped`. The P-DRY pass count itself was recorded wrongly; see
lesson 37.

**Generalises to.** A package should verify from its own contents and hashes, with nothing fetched from the working
data tree.

### 14. Derive identifiers from the one configured source, never from memory

**What happened.** `protocol9_for.sh` takes the volume id from the supervisor's COVERAGE string, "never from memory".
The record says the mistake "has already cost one wrong read and was caught before a second". **VERIFIED**
[`RULES.md:2044`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2044) `@b6db282` The changelog instead records "a guessed PHerc0358 volume id caught before it ran".
**VERIFIED** [`CHANGELOG.md:420`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L420) `@5c6613d` The two statements disagree, and no record of the wrong read itself was
found.

**Why it matters.** **INFERENCE** A wrong volume id fetches a different scan, and the read can still look
plausible.

**Fix.** The launcher parses the COVERAGE map and refuses a scroll with no entry. **VERIFIED**
[`scripts/protocol9_for.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/protocol9_for.sh#L19) `@cdb5303` Pinned by `scripts/tests/test_protocol9.py::test_launcher_refuses_an_unknown_scroll`,
`::test_launcher_derives_scroll_um_and_volume_and_never_hardcodes_a_volume_id` and
`scripts/tests/test_loop_scripts.py::test_rbest2_volume_ids_match_the_supervisors_coverage_map`.

**Generalises to.** Keep volume ids, pitches and URLs in one table that code parses, and test that no script holds a
literal copy.

### 15. Delete only files that are marked complete and have been idle for a set time

**What happened.** `sweep_renders.py` was deleting renders mid-write. A re-read's in-progress render was judged
removable because an earlier read of the same patch had finished. That killed PHerc1203's render three times in a
row and failed that R-CREST-POWER surface out of the queue. **MEASURED** [`RULES.md:360`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L360) `@27f78c6` The same family of
defect, a started marker read as a done marker, recurred: `rbest.sh` treated an existing read directory as a
finished read and skipped the surface it had been interrupted on. **INFERENCE** [`RULES.md:933`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L933) `@9d18317`

**Why it matters.** **INFERENCE** A cleanup job that cannot tell "started" from "finished" destroys live work.

**Fix.** A render is removable only with a completion marker and after 10 minutes untouched. **VERIFIED**
[`scripts/sweep_renders.py:16`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_renders.py#L16) `@27f78c6` [`scripts/sweep_renders.py:27`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_renders.py#L27) `@27f78c6` The R-BEST completion test is now
`read_stats.json` [`RULES.md:933`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L933) `@9d18317`. Pinned by
`scripts/tests/test_sweep_renders.py::test_a_render_being_written_is_never_swept` and
`::test_a_freshly_written_render_is_never_swept`.

**Generalises to.** Existence is not completion: a job must write an explicit done marker, and anything without one
is treated as live.

### 16. Do not reclaim disk from under a live process

**What happened.** The disk guard pruned normal grids under a live tracer. The first two 40-generation interior
traces took 269 s and 333 s. Over all 14 at that budget the median was 1052 s and the maximum 2358 s, a ~4x
slowdown. **MEASURED** [`RULES.md:562`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L562) `@0974977` The first replacement exemption was uncapped and took the box from
8.1 GB to 3.8 GB free. It was then capped at 1500 MB. **MEASURED** [`CHANGELOG.md:409`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L409) `@78532c5` The single 1500 MB
cap then kept pruning PHerc0826's grids every eight minutes under two live tracers. **MEASURED**
[`RULES.md:2064`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2064) `@658d5c2` Separately, the
one-trace-slot decision did not take effect at first. The loops read `TRACE_SLOTS` with a default of 2 and had been
started before the supervisor exported 1, so two traces kept running at 886-910 s. The default became 1 inside both
loops and the loops were restarted. **MEASURED** [`RULES.md:336`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L336) `@573c94e`

**Why it matters.** **INFERENCE** Throughput decided how much canvas could be traced. A cleanup that forces live
jobs to refetch their inputs costs more than the disk it frees.

**Fix.** `prune_grids` in `scripts/disk_guard.sh` skips any scroll with `vc_grow_seg_from_seed` or `vc_render_tifxyz`
running, except below the 3 GB hard floor, where it prunes with force. **VERIFIED** [`RULES.md:566`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L566) `@0974977` The
live-tracer exemption has two tiers: `ACTIVE_CAP_ROOMY=3000` above 5.5 GB free and `ACTIVE_CAP_TIGHT=1500` below.
**VERIFIED** [`RULES.md:2067`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2067) `@658d5c2` [`scripts/disk_guard.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/disk_guard.sh#L19) `@658d5c2` The record says seven tests pin the
first fix. `scripts/tests/test_disk_guard.py` now holds ten test functions (the tenth,
`::test_the_ct_cache_keep_list_actually_keeps`, was added with the keep-list fix in `091c2fa`; see Appendix B), including
`::test_grids_are_kept_while_that_scroll_is_being_traced`, `::test_force_prunes_even_under_a_live_tracer` and
`::test_the_live_tracer_exemption_has_two_tiers_like_the_prune_target`. **VERIFIED** Two declared throughput checks
have no recorded outcome: "the next five 40-generation traces come in under 400 s each" [`RULES.md:329`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L329) `@ce886a7`,
and the next 10 completed traces compared against the 14 above (median 1052 s) [`RULES.md:569`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L569) `@0974977`.
**INFERENCE** (PRE-REGISTERED, outcome not found)

**Generalises to.** A disk cleaner must know which files running jobs are using, and must re-check after a fix that
the jobs actually run faster.

### 17. Read a queue into memory before the loop, and close the stdin of every child

**What happened.** The G-GP part 4 dense loop logged one seed and then "dense queue done", having traced 1 of 25.
**MEASURED** [`RULES.md:743`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L743) `@2fcbbcd` The cause is not established. The likeliest explanation is a duplicate loop.
A pipe into `while read` is a second, real hazard. **INFERENCE** [`RULES.md:745`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L745) `@2fcbbcd`

**Why it matters.** **INFERENCE** A queue that ends early looks exactly like a queue that finished. With a pipe-fed
`while read`, any command in the loop body that reads stdin can consume the queue.

**Fix.** The loop was fixed by shape: the queue is read into an array with `mapfile`, the tracer call has its stdin
closed, and the loop logs per-seed progress. **VERIFIED** [`scripts/dense_loop.sh:19`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/dense_loop.sh#L19) `@2fcbbcd`
[`scripts/dense_loop.sh:48`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/dense_loop.sh#L48) `@2fcbbcd` Pinned by `scripts/tests/test_loop_scripts.py::test_parses`,
`::test_queue_is_materialised_before_the_loop`, `::test_the_tracer_call_cannot_read_the_queue` and
`::test_the_loop_reports_its_progress`. The docstring of
`scripts/tests/test_loop_scripts.py::test_rsmall_loop_materialises_its_queue_and_closes_stdin` calls the pipe "how
dense_loop.sh lost 24 seeds", which contradicts the record and the test module's own docstring.
**VERIFIED** [`scripts/tests/test_loop_scripts.py:139`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_loop_scripts.py#L139) `@4bb3af8` [`scripts/tests/test_loop_scripts.py:3`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_loop_scripts.py#L3) `@2fcbbcd`

**Generalises to.** In shell queue loops, materialise the list first and run children with `</dev/null`; when the
cause of a failure is unknown, fix the shape that allows it and say the cause is unknown.

### 18. Check that a published tool image can run the documented command before using it

**What happened.** The published VC3D image (`:edge` = `:main`, built 2026-05-13, villa `1e3f4c0`) lacks
`--flip-normals`. A 256×256 smoke render with it matched the team stack only with the slice order reversed, at
Pearson 0.42–0.82 per slice (identical-pixel fraction 0.40), so the tools were rebuilt from villa `5ab585f`.
**MEASURED** [`RULES.md:28`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28) `@2e62892` The rebuilt renderer matched the team stack on the 2048×2048 crop at Pearson
min 0.999999 over 28 slices, passing G-B Bar 1 (≥ 0.999). **MEASURED** (PRE-REGISTERED) [`RULES.md:29`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29) `@5ca0c22`

**Why it matters.** **INFERENCE** The model scores the wrong depth order at chance on known text: on the 2026-10-15
reproduction, forward AUC 0.99659 and reverse 0.49633 on w040. **VERIFIED** [`RULES.md:3273`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3273) `@eed0fac` A render with
the slices reversed would make every read uninformative without any error message.

**Fix.** `scripts/build_vc3d.sh` builds the tools from villa source inside the project's builder image.
**VERIFIED** [`scripts/build_vc3d.sh:3`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/build_vc3d.sh#L3) `@2e62892` G-B Bar 1 is the check that the rebuild matches the team stack. No
unit test can pin an external image. `scripts/tests/test_vc_tools.py::test_render_argv` pins the render command line
the pipeline issues. The image was still stale on 2026-10-15; see lesson 36.

**Generalises to.** Before trusting a published binary, run the documented command with it on an input whose correct
output you already have.

### 19. Do not read a high forward level as ink; decide on the depth-order margin

**What happened.** Over 50 reads, on-sheet CT standard deviation correlates with the fraction of the forward map
above 0.75 at r = −0.4960. Renders with CT std < 25 (n = 3) have a median fraction above 0.75 of 0.0501, against
0.0036 for std ≥ 25 (n = 47). **MEASURED** (DESCRIPTIVE) [`RULES.md:1916`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1916) `@5bb4e28` [`RULES.md:1921`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1921) `@5bb4e28`
[`RULES.md:1922`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1922) `@5bb4e28` Under TTA, the CT-std-8.63 render (`PHerc0826_small|auto_grown_20260918152701336`) reads forward
0.4522, above the w040 control's known-text units (0.4109 median), at margin +0.0003. Its high-texture sibling read
on the same scroll has CT std 45.44, forward 0.2991, margin −0.0263. **MEASURED** [`RULES.md:2134`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2134) `@22e440f`
[`RULES.md:2135`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2135) `@22e440f` [`RULES.md:2138`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2138) `@22e440f` [`RULES.md:2141`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2141) `@22e440f` On one scroll, budget and recipe,
the forward level tracks how little texture the render has, while the margin stays near zero. **INFERENCE**
(DESCRIPTIVE) [`RULES.md:2143`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2143) `@22e440f`

**Why it matters.** **INFERENCE** A probability map can rise on smooth, textureless papyrus. Rule 5.5 flags a unit
only when its forward mean is ≥ 0.36 AND its forward-minus-reverse mean is ≥ 0.08 [`scripts/rule55.py:9`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rule55.py#L9) `@a2170dd`;
the texture effect raises the first quantity and not the second. The group is n = 3 and gates nothing.

**Fix.** No code change; no bar moved. The frozen thresholds are pinned by
`scripts/tests/test_rule55.py::test_thresholds_are_the_frozen_ones`. The notebook's attribution of forward levels to
these surfaces contains recording errors; see lesson 37.

**Generalises to.** Do not treat a high ink probability on a low-texture render as ink; require a depth-order or
orientation contrast that texture alone does not produce.

### 20. Compute expected candidate counts from the real per-surface layouts, not from one pooled grid

**What happened.** R-DEFICIT predicted 1.59 qualifying clusters from the 113 corpus units at the control's cluster
density, with P(0) = 0.20. **INFERENCE** (EXPLORATORY) [`RULES.md:2234`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2234) `@e38ac0f` R-SHAPE recomputed it from the
recorded per-surface layouts (flag rate 7/71 = 0.0986, 20 000 Monte Carlo trials, seed 20260919). The expected
number of candidates from everything screened is 0.079, twenty times lower than 1.59, because 1.59 silently assumed
one contiguous 71-unit grid. **MEASURED** [`RULES.md:2464`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2464) `@8f459e0` [`RULES.md:2469`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2469) `@8f459e0`
[`RULES.md:2470`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2470) `@8f459e0` 10 of 31 corpus surfaces have fewer than 3 valid
units and cannot produce a candidate at any flag rate. **MEASURED** (DESCRIPTIVE) [`RULES.md:2476`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2476) `@8f459e0`
R-DEFICIT's unit-level rate comparison (1 flagged of 113 against 7 of 71, Fisher p = 0.0058) was untouched by this
correction. **VERIFIED** [`RULES.md:2481`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2481) `@8f459e0` [`RULES.md:2482`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2482) `@8f459e0` Lesson 35 qualifies that comparison,
and R-HELDOUT (lesson 34) narrows it: against the held-out known-text rate 1/60, the same 1/113 gives Fisher
one-sided p = 0.575. **VERIFIED** (EXPLORATORY; recomputed by `scripts/release_stats.py`) [`RULES.md:3321`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3321) `@7925b3a`
[`RULES.md:3322`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3322) `@7925b3a` [`records/release/release_stats.json:40`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L40) `@7925b3a` The flag rate therefore does not separate the
eligible canvas from known text on an unseen scroll, and it is not evidence of absent ink. **INFERENCE**
[`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a` [`RULES.md:3325`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3325) `@7925b3a` [`RULES.md:3326`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3326) `@7925b3a`

**Why it matters.** **INFERENCE** The pooled figure made zero candidates look like a meaningful deficit. On the real
layouts, zero candidates was the expected outcome.

**Fix.** `scripts/cluster_power.py` computes the expectation from each surface's recorded layout. **VERIFIED**
[`scripts/cluster_power.py:5`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L5) `@8f459e0` Pinned by
`scripts/tests/test_cluster_power.py::test_a_big_grid_beats_several_small_ones_at_the_same_unit_count`,
`::test_a_surface_with_fewer_than_three_valid_units_can_never_produce_a_candidate` and
`::test_three_units_that_are_not_4_connected_are_not_a_candidate_even_when_all_flag`.

**Generalises to.** When a detection needs adjacent tiles, compute its power on the actual shapes of the surfaces
read; pooled tile counts overstate it.

### 21. Test a model's independence assumption on the control before quoting its estimate

**What happened.** R-SHAPE's independence assumption was tested on the control (7 flagged of 71, 40 000 draws).
Under independence P(largest cluster ≥ 4) = 0.0257, and the control observed a 4-cluster, a 1-in-39 event.
**MEASURED** [`RULES.md:2496`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2496) `@cf64ed9` [`RULES.md:2501`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2501) `@cf64ed9` [`RULES.md:2504`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2504) `@cf64ed9` Because real ink clusters more than independence
assumes, R-SHAPE's 0.079 is a lower bound (near 0.5 after scaling by the control's measured excess). The strong claim
"our canvas cannot form a candidate" was withdrawn in favour of "zero candidates is the expected outcome at this size
and shape". **INFERENCE** [`RULES.md:2505`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2505) `@cf64ed9`

**Why it matters.** **INFERENCE** The estimate's main assumption was false on the one surface where it could be
checked, and the check reversed the direction in which the estimate could be trusted.

**Fix.** The strong claim was withdrawn in `RULES.md`. The same clustering is carried into the release statistics
as a cluster-collapsed sensitivity analysis (lesson 35). **VERIFIED** [`scripts/release_stats.py:13`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L13) `@0afc07e` That
analysis is pinned by `scripts/tests/test_release_stats.py::test_collapsing_clusters_weakens_the_unit_level_evidence`.
No test pins R-SHAPE's independence check itself.

**Generalises to.** If a power or null model treats tiles as independent, check that assumption on a positive
control where clustering is visible.

### 22. Test competing explanations of a number before naming its cause

**What happened.** R-COVER9 measured papyrus coverage (on-sheet area over render canvas) of 0.412 for the part-5
consensus surface (5 valid of 18 units) and 0.427 for part 4 (2 of 8), against a corpus median of 0.584 and the
control's 0.907. **MEASURED** (DESCRIPTIVE) [`RULES.md:2551`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2551) `@e23b2fe` [`RULES.md:2539`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2539) `@e23b2fe`
[`RULES.md:2540`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2540) `@e23b2fe` It first read these as traces that "spend two fifths of their area off the papyrus".
**INFERENCE** [`RULES.md:2546`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2546) `@e23b2fe` The correction: the consensus surfaces are not off the papyrus but ragged.
They fill 0.476 and 0.495 of their own bounding grid, where the control fills 0.862 and a small trace 0.905.
**MEASURED** [`RULES.md:2594`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2594) `@b2765f7` A second explanation, nodes stretched across wrap gaps, also failed: median
adjacent-node distance was 20.0–20.1 for small traces and consensus surfaces, against 20.0 for the control.
**MEASURED** [`RULES.md:2579`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2579) `@b2765f7`

**Why it matters.** **INFERENCE** The first reading would have sent tracing effort after the wrong defect.

**Fix.** The reading was withdrawn in `RULES.md`, and the numbers stand. No code changed, and there is no test.

**Generalises to.** A low coverage figure has several geometric causes (off-sheet, ragged, stretched); measure each
before writing one down.

### 23. Use a proxy only after it has predicted the quantity it stands for

**What happened.** The docstring of `coverage_proxy.py` commits that the proxy is validated against 31 surfaces with
recorded coverage and "used for nothing unless it predicts". **INFERENCE** (a rule written into the script's
docstring. The script and its result were committed together in `b2765f7`, so git order cannot confirm that the
docstring came before the run. The docstring names 31 surfaces; the recorded validation used 9.)
[`scripts/coverage_proxy.py:9`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/coverage_proxy.py#L9) `@b2765f7` The level-4 CT proxy scored both consensus surfaces firmly
on papyrus (0.857, 0.823) against rendered coverage of 0.427 and 0.412. Its Pearson r was 0.43–0.63 over 9
surfaces, carried by the small traces. It is used for nothing. **MEASURED** [`RULES.md:2576`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2576) `@b2765f7`

**Why it matters.** **INFERENCE** A cheap proxy that had been adopted untested would have called the worst surfaces
good.

**Fix.** No script outside `coverage_proxy.py` imports or calls it. **VERIFIED** (grep of `scripts/`, 2026-10-15) No
test pins its non-use.

**Generalises to.** Write a proxy's acceptance test before running it, and drop the proxy if it fails.

### 24. Prove that a "conservative" bound is a bound before relying on it

**What happened.** R-BLANK part 2's first implementation took the max-pooled cell centre-to-centre distance as
conservative. It is not: it can overstate the true pixel distance by up to 106 µm. **VERIFIED**
[`RULES.md:2335`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2335) `@8f49fce`

**Why it matters.** **INFERENCE** A distance band called conservative that can be 106 µm too generous would admit
units the declaration excludes.

**Fix.** The distance is now `max(0, D − √2) · pool · µm`, a provable lower bound, fixed before the run.
**VERIFIED** [`scripts/rblank2.py:30`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/rblank2.py#L30) `@8f49fce` Pinned by a randomised property test over twelve ink layouts,
`scripts/tests/test_rblank2.py::test_the_conservative_bound_holds_for_many_random_ink_layouts`.

**Generalises to.** Pooling moves every pixel up to half a cell diagonal from its cell centre; a distance bound
computed on pooled cells must subtract that, and a property test should check it.

### 25. Give every output directory a reader, and check that it has one

**What happened.** R-SMALL-2's traces land in `patches/<scroll>_rs2`, but the supervisor's reduced-budget read loop
was hard-coded to `_small`. 15 traces had been grown and none had been QC'd or read, so R-SMALL-2's readable-fraction
bar could never have been evaluated. **MEASURED** [`RULES.md:2640`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2640) `@e87c53b` STATE.md lists it among the day's errors.
**INFERENCE** [`STATE.md:82`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L82) `@ca3452c`

**Why it matters.** **INFERENCE** Hours of tracing produced nothing measurable, and nothing reported the gap.

**Fix.** The supervisor's read loop iterates over `RSMALL_SUFFIXES` (default `_small _rs2`), with a pid file and a
log per suffix. **VERIFIED** [`RULES.md:2647`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2647) `@e87c53b` [`scripts/supervisor.sh:127`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L127) `@e87c53b` Pinned by
`scripts/tests/test_supervisor_inline.py::test_the_reduced_budget_read_loop_covers_rs2_as_well_as_small`,
`::test_the_suffix_loop_is_closed_and_the_script_parses` and
`::test_the_pid_file_and_log_are_per_suffix_so_two_loops_cannot_collide`.

**Generalises to.** Whenever a new output location is introduced, check that something consumes it.

### 26. Run one queue per population, enforced by a process check rather than a marker file

**What happened.** Deleting both R-CREST-POWER pause markers let the supervisor start the PHerc1203 subset queue
alongside the full 12-member queue. Two `run_patch_dir.py --only team_20251005230830031` processes were then in
flight, writing one read directory. **MEASURED** [`RULES.md:2985`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2985) `@8aab40d` Nothing measured was affected. No read
completed under the race, the contested directory held only the previous day's stale forward map and was deleted,
and the post-fix audit is 64 pairs, 64 sound, 0 SUSPECT. **MEASURED** [`RULES.md:2998`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2998) `@8aab40d` Earlier, both R-BEST
loops had started a second inference on a read in progress: two processes wrote one output directory, one 4595 s in
and the other 98 s. **MEASURED** [`RULES.md:1095`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1095) `@ebbf673`

**Why it matters.** **INFERENCE** Two writers on one directory can produce a forward map from one run and a reverse
map from another.

**Fix.** The supervisor's subset queue stands down whenever the full queue's pid is alive, marker or no marker.
**VERIFIED** [`RULES.md:2994`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2994) `@8aab40d` [`scripts/supervisor.sh:152`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L152) `@8aab40d` Pinned by
`scripts/tests/test_supervisor_inline.py::test_the_1203_subset_queue_stands_down_when_the_full_phase1_queue_is_alive`,
`::test_one_queue_is_the_invariant_not_the_pause_marker` and
`scripts/tests/test_loop_scripts.py::test_rbest_loops_do_not_start_a_second_read_of_the_same_surface`.

**Generalises to.** State the invariant (one writer per output directory) and test the invariant itself, not the
marker files that are meant to maintain it.

### 27. Sweep away the partial outputs of killed runs before anything can score them

**What happened.** A sweep of the whole tree found three read directories holding a forward map with no reverse, no
`read_stats.json` and no `.read_complete` (10.6 h, 13.7 h and 19.2 h old). None had been scored, so no verdict was
affected. **MEASURED** [`RULES.md:3028`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3028) `@d494084` The first attempt to wire the sweeper into the supervisor put it
inside the map-integrity case block and broke `bash -n`. It was caught immediately and reverted. **MEASURED**
[`RULES.md:3038`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3038) `@d494084`

**Why it matters.** **INFERENCE** A leftover map paired with a fresh one is exactly the stale-pair failure of lesson
2.

**Fix.** `scripts/sweep_partial_reads.py` deletes only directories with no `.read_complete`, at least one `.tif`,
and untouched for 6 h, against a longest observed single-direction write of 1.9 h. It is dry-run by default and runs
at every supervisor check-in. **VERIFIED** [`RULES.md:3035`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3035) `@d494084` [`scripts/sweep_partial_reads.py:21`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/sweep_partial_reads.py#L21) `@d494084`
Pinned by the six tests in `scripts/tests/test_sweep_partial_reads.py`, among them `::test_a_killed_reads_leftover_is_found`,
`::test_a_live_read_is_never_touched_however_slow` and `::test_dry_run_is_the_default_and_deletes_nothing`, and by
`scripts/tests/test_supervisor_inline.py::test_the_supervisor_sweeps_killed_reads_leftovers_every_checkin`.

**Generalises to.** Every killed job leaves a half-written output; give outputs a completion marker and sweep
whatever lacks one once it is clearly older than the longest real run.

### 28. Write a number into the record only after its computation has printed

**What happened.** The 4-of-12 R-CREST-POWER interim recorded 0 flagged of 83 valid units with binomial P(0) =
0.0002 and Fisher exact one-sided p = 0.0023. **INFERENCE** [`RULES.md:3154`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3154) `@201e3c0` The correction: for 0 of 83
against the control's 7 of 71, expected 8.18, binomial P(0) = 1.81 × 10⁻⁴ and Fisher exact one-sided p = 0.00375,
not 0.0023 (wrong by a factor of 1.6). **VERIFIED** [`RULES.md:3162`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3162) `@d94ea58` The record calls this the third time
that day a message or number was composed before its input was read. **INFERENCE** [`RULES.md:3164`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3164) `@d94ea58`

**Why it matters.** **INFERENCE** The conclusion did not change, but a p-value written from memory is not evidence.

**Fix.** Practice: a figure goes into the notebook only after its computation has printed [`RULES.md:3164`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3164) `@d94ea58`.
At release, `scripts/release_stats.py` recomputes all ten hand-written Fisher and binomial values from their counts,
including this one. **VERIFIED** [`scripts/release_stats.py:55`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L55) `@0afc07e`
[`records/release/release_stats.json:224`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L224) `@0afc07e` Pinned by
`scripts/tests/test_release_stats.py::test_every_recorded_value_is_reproduced`. Run on 2026-10-15, all ten checks
print OK. **VERIFIED**

**Generalises to.** Compute, print, then copy; and keep a script that recomputes every published statistic from its
counts.

### 29. Count a surface once, however many files it was written to

[line withheld: prize-candidate detail under review]
the same grid 174×258 and the same 22 228 valid nodes: one surface written twice, not 19 cm² of canvas.
**MEASURED** [`RULES.md:2710`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2710) `@53f35cd`

**Why it matters.** **INFERENCE** Counting both outputs doubles the canvas and the unit count that every power
calculation rests on.

**Fix.** `scripts/cluster_power.py` dedupes automatically: identical layouts within one `*_cons_part*` directory are
counted once. Re-running R-SHAPE with the fix reproduces 0.079 exactly, and R-DEFICIT (30 surfaces, 113 units) and
R-SHAPE (31, 118) were checked and found not inflated. **VERIFIED** [`RULES.md:2719`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2719) `@cf78e64` [`RULES.md:2723`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2723) `@cf78e64`
[`RULES.md:2724`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2724) `@cf78e64`
[`scripts/cluster_power.py:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/cluster_power.py#L22) `@cf78e64` Pinned by
`scripts/tests/test_cluster_power.py::test_a_consensus_builds_two_outputs_are_counted_once`,
`::test_two_DIFFERENT_consensus_surfaces_are_both_kept`, `::test_different_consensus_PARTS_are_never_merged` and
`::test_ordinary_traces_are_never_deduped_even_with_identical_layouts`.

**Generalises to.** Segmentation tools can write one surface under two names; dedupe by content before summing area
or units.

### 30. After a restart, check what actually stopped before acting

**What happened.** At 17:02 UTC on 2026-09-17 a worker restart moved the egress proxy from port 34301 to 37007. The
loops kept the old `HTTPS_PROXY`, so every S3 fetch failed, and a 4.99 cm² trace was discarded. **MEASURED**
[`CHANGELOG.md:8`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L8) `@fe7334e` [`CHANGELOG.md:9`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L9) `@fe7334e` [`CHANGELOG.md:13`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L13) `@fe7334e` At the 13:38 UTC
session-container restart on 2026-09-19 the machine did not reboot (uptime 12:57). Only loops holding a stale
`HTTPS_PROXY` broke, and the supervisor's `stale_proxy` check restarted exactly those. **MEASURED** [`RULES.md:3169`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3169) `@db29af2`
[`RULES.md:3170`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3170) `@db29af2` [`RULES.md:3171`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3171) `@db29af2` The operator's first reading, "every job is gone", was wrong; acting on it would have repeated the duplicate-queue
defect of lesson 26. **INFERENCE** [`RULES.md:3174`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3174) `@db29af2` The restart cost one member's render, and the audit read
69 pairs, 69 sound. **MEASURED** [`RULES.md:3177`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3177) `@db29af2` [`RULES.md:3180`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3180) `@db29af2` The stale-proxy restart itself
had earlier thrown away 77 minutes of an R-DEPTH inference, although R-DEPTH fetches nothing. **MEASURED**
[`RULES.md:922`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L922) `@9d18317` [`RULES.md:923`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L923) `@9d18317`

**Why it matters.** **INFERENCE** Losing the session's watchers is not losing the work. A blanket restart destroys
running jobs, and doing nothing leaves broken ones running.

**Fix.** `stale_proxy <pid>` in `scripts/supervisor.sh` is true when a process was started under a different
`HTTPS_PROXY` from the current one, and such loops are killed and restarted. R-DEPTH is exempt. **VERIFIED**
[`scripts/supervisor.sh:22`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L22) `@fe7334e` [`scripts/supervisor.sh:23`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L23) `@6244cd1` Only partly pinned:
`scripts/tests/test_supervisor_inline.py::test_rdepth_is_exempt_from_the_stale_proxy_restart` tests the R-DEPTH
exemption and that the check is still present for R-BEST. The `stale_proxy` function has no direct unit test.

**Generalises to.** After any restart, check uptime and the process table before acting, and restart only the jobs
that depend on what changed.

### 31. Give every component of the chain, including your own tracer, a positive control on known text

**What happened.** G-OWN traced the w040 known-text sheet with the project's own tracer. On 4.32 cm² where the team's
maps return +0.0416, the project's geometry returns |margin| 0.0594, keeping 142.7 % of the team mesh's signal: PASS
against the ≥ 0.0128 bar. **MEASURED** (PRE-REGISTERED) [`RULES.md:2813`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2813) `@d29112c` [`RULES.md:2814`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2814) `@d29112c` The
entry concluded that "the corpus negatives are therefore real negatives" [`RULES.md:2822`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2822) `@d29112c`.

**Why it matters.** **INFERENCE** Until G-OWN, the tracer was the one component with no positive control, and every
corpus negative was read on its surfaces. The conclusion went further than the test allows: w040 is a training-set
sheet of the ink model (lesson 34) [`RULES.md:3240`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3240) `@661ff64`. The 142.7 % compares the project's tracer with the
team's mesh on the same papyrus, so the training-set problem does not invalidate that comparison. "The corpus
negatives are real negatives" no longer follows from it. R-HELDOUT then measured the frozen screen on known text
from an unseen scroll: it flags 1 of 60 valid units there (lesson 34). **MEASURED** (PRE-REGISTERED)
[`RULES.md:3319`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3319) `@7925b3a`

**Fix.** `scripts/gown_result.py` evaluates the declared statistic against the declared bars. Pinned by
`scripts/tests/test_gown_result.py::test_bars_are_the_declared_ones_and_are_not_computed`,
`::test_the_statistic_is_the_absolute_margin_so_orientation_cannot_decide_it` and
`::test_the_matched_figure_cannot_change_the_declared_verdict`. The superseded conclusion is listed in
[SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md).

**Generalises to.** Run your own segmentation on a known-text sheet and compare it with the reference mesh over the
same area, on a sheet the ink model did not train on where one exists.

### 32. When sheet orientation is unknown, read both depth orders and keep a tripwire on the swapped one

**What happened.** The project's traces have unknown sheet orientation, and rule 5.5 flags a signed margin. R-ORIENT
found that over 52 reads the depth-swap tripwire never fired. Across 189 reconstructed unit margins the extremes are
−0.0714 and +0.0873, so orientation correction adds zero flagged units. **MEASURED** [`RULES.md:2365`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2365) `@8f49fce` On
G-OWN the tripwire fired for the first time. The forward table reads 0 flagged of 9 valid (BLANK), while the swapped
table has 2 flagged at +0.1150 and +0.1048, clusters [1, 1]. The whole-map on-sheet margin is −0.0594. **MEASURED**
[`RULES.md:2817`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2817) `@d29112c` [`RULES.md:2812`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2812) `@d29112c` On the committed w040 window with the orders swapped, the
signed rule says BLANK and the tripwire fires. **VERIFIED** (quick start run, 2026-10-15)
[`examples/check_quickstart.py:41`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/check_quickstart.py#L41) `@0afc07e` [`examples/check_quickstart.py:42`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/check_quickstart.py#L42) `@0afc07e`

**Release-time evidence (2026-10-15).** The project's render path never passes `--flip-normals`: `scripts/vc_tools.sh render`'s usage line says "no flip" and its renderer call carries no such flag. **VERIFIED** (code read, 2026-10-15) [`scripts/vc_tools.sh:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L6) `@e3a0717` [`scripts/vc_tools.sh:107`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/vc_tools.sh#L107) `@e3a0717`. The team's published renders, whose depth orientation is the one `--flip-normals` reproduces [`records/release/edge_image_check_2026-10-15.md:21`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L21) `@0afc07e`, were used only where a surface volume is published (PHerc1447 and PHerc0800; PHerc1203 publishes none) [`scripts/fetch_surface_volumes.py:6`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L6) `@f600d41` [`scripts/fetch_surface_volumes.py:7`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/fetch_surface_volumes.py#L7) `@f600d41`. **All 11 R-CREST-POWER members — the 3 PHerc1203 and the 8 PHerc1447 team meshes — were rendered by the project**: their reads record render times of 170.6–431.6 s (members 1 and 5 show 0.0 s only because their render was already on disk), where a published render records none. **MEASURED** [`records/throughput.jsonl:190`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L190) `@e439b85` [`records/throughput.jsonl:192`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L192) `@201e3c0` [`records/throughput.jsonl:199`](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L199) `@ecf1dd8`. Their "forward" map is therefore presumably the reverse of the trained orientation, and R-ORIENT's premise that team meshes are read in the orientation `--flip-normals` gives [`RULES.md:2355`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2355) `@8f49fce` does not hold for them. **INFERENCE** No verdict depends on it: both depth orders are always read, phase 1 flags 0 of 190 units in either order, the PHerc1203 half 0 of 64 with 0 swapped, and the tripwire never fired. **MEASURED** [`RULES.md:3127`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3127) `@f9bfe3b` [`RULES.md:3136`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3136) `@f9bfe3b` [`STATE.md:33`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L33) `@71720ce`

**Why it matters.** **INFERENCE** A mirrored surface turns ink into a negative margin, and a signed rule then calls
known text blank. Without the tripwire, the signed rule 5.5 table would have recorded G-OWN's known text as BLANK,
with nothing to show that two units flag in the reversed order. G-OWN's own verdict used |margin|, so it did not
depend on the tripwire [`RULES.md:2813`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2813) `@d29112c` [`RULES.md:2816`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2816) `@d29112c`.

**Fix.** `scripts/read_chart.py` records `depth_swap_tripwire` whenever the swapped table flags a unit. It changes no
verdict. **VERIFIED** [`scripts/read_chart.py:257`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/read_chart.py#L257) `@5ab18b3` G-OWN's declared statistic is the absolute margin. Pinned
by `scripts/tests/test_read_chart.py::test_depth_swap_tripwire_is_recorded_and_changes_no_verdict` and
`scripts/tests/test_gown_result.py::test_the_statistic_is_the_absolute_margin_so_orientation_cannot_decide_it`. The
notebook disagrees with itself on which read the +0.0873 unit came from; see lesson 37.

**Generalises to.** If you cannot fix a surface's recto/verso orientation, score both depth orders and record when
the reversed order would have flagged.

### 33. Optimise the quantity that decides the result (valid units), not a proxy for it (area)

**What happened.** R-YIELD found that consensus surfaces carry a median of 18.0 grid units but only 5.0 valid units
(44 % validity), against 4.0 and 60 % for single traces and 6.0 and 57 % for team meshes. **MEASURED**
(DESCRIPTIVE) [`RULES.md:2879`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2879) `@a8b2fc4` [`RULES.md:2880`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2880) `@a8b2fc4` [`RULES.md:2881`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2881) `@a8b2fc4`
[`RULES.md:2884`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2884) `@a8b2fc4` The entry states that the programme optimised the wrong quantity.
**INFERENCE** [`RULES.md:2887`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2887) `@a8b2fc4` A sweep of `consensus_default_th` over 4/6/8/10 refuted the pre-registered
prediction: threshold 6 is best on area (9.52 cm² against 3.7–4.0), grid fill (0.495) and mid-plane landing.
**MEASURED** (PRE-REGISTERED) [`RULES.md:2867`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2867) `@7fdf466` R-YIELD also recorded a ceiling: nine valid units was the
best any surface had produced, giving P(candidate) 0.017 at the control's flag rate. **MEASURED**
[`RULES.md:2889`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2889) `@a8b2fc4` [`RULES.md:2891`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2891) `@a8b2fc4` Later that morning an R-CREST-POWER member yielded 28 valid units
at 96 % unit validity. **MEASURED** [`RULES.md:3084`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3084) `@fd3b816` [`RULES.md:3085`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3085) `@fd3b816` The notebook says "two hours ago";
the commits are 90 min 40 s apart ([`a8b2fc4`](https://github.com/abundantjoe/hercules/commit/a8b2fc4) at 10:21:04
and [`fd3b816`](https://github.com/abundantjoe/hercules/commit/fd3b816) at 11:51:44 UTC). **VERIFIED** (`git log`,
2026-10-15)

**Why it matters.** **INFERENCE** Rule 5.5 needs three adjacent valid units, so area that yields no valid units buys
nothing. The "ceiling" described only what had been tried.

**Fix.** No code change; the notebook's measure of progress became valid units. `scripts/cluster_power.py
--read-stats` scores a single read's layout. On the committed w040 window, 2136 × 2136 px at 9.362 µm/px = 3.9989
cm² [`packages/DRYRUN_PHerc0139_w040/verify_report.txt:1`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/verify_report.txt#L1) `@a2d0e59` (a 2x2 grid, 4 valid units), the probability of at least
one 4-connected flagged triple at the control's flag rate (p = 0.0986) is 0.0029 (Monte Carlo, 20,000 trials, SE 0.0004; exact 0.0035499).
**VERIFIED** (quick start run, 2026-10-15) [`examples/quickstart.sh:38`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/quickstart.sh#L38) `@0afc07e` [`examples/README.md:32`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L32) `@2bf30b3` Pinned by
`scripts/tests/test_cluster_power.py::test_read_stats_cli_scores_a_read_without_touching_the_corpus`.

**Generalises to.** Count valid units per surface, the quantity the decision rule consumes, rather than square
centimetres traced.

---

## Found while preparing this release

### 34. Read the model's training config before calling a control held-out

**In short: the known-text control w040 is a training-set sheet** (**VERIFIED** [`RULES.md:3239`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3239) `@661ff64`). **On
known text from an unseen scroll the model's pixel signal transfers (forward AUC 0.8393, reverse 0.5486), but the
frozen unit screen flags 1 of 60 valid units** (**MEASURED**, PRE-REGISTERED [`RULES.md:3301`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3301) `@7925b3a` [`RULES.md:3302`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3302) `@7925b3a`
[`RULES.md:3319`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3319) `@7925b3a`), **so the eligible-scroll negatives are not evidence of absent ink** (**INFERENCE**
[`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a` [`RULES.md:3325`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3325) `@7925b3a` [`RULES.md:3326`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3326) `@7925b3a`). Details under "R-HELDOUT result" below.

**What happened.** villa's training config for this checkpoint, `aligned21_hybrid_3d2d.json` at `5ab585f`, lists
`w040` among its five native-9.362 µm training segments and `pherc0139-w040` among its aligned ones. The model card
says "plus 5 native 9.362 µm segments from PHerc. 0139", and no `w040_validation_mask.zarr` exists in the label
bucket. **VERIFIED** (external files read on 2026-10-15) [`RULES.md:3235`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3235) `@661ff64` [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`
[`RULES.md:3238`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3238) `@661ff64` Gate A's AUC on w040 and R-CTRL55's 7/71 were therefore measured on a training-set
sheet. **VERIFIED** [`RULES.md:3239`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3239) `@661ff64` They are a best case for the detector, not a held-out validation.
**INFERENCE** [`RULES.md:3240`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3240) `@661ff64` The master prompt had already said that "w028 and w040 are in its training corpus, so label
AUC measures memorisation". **INFERENCE** [`docs/MASTER_PROMPT_v4.md:38`](https://github.com/abundantjoe/hercules/blob/71720ce/docs/MASTER_PROMPT_v4.md?plain=1#L38) `@8a52745` The notebook applied that caveat
to w028 in Gate C [`RULES.md:35`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L35) `@8a52745`, but R-CTRL55's bar and conclusions and STATE.md call w040 a sheet "the
model did not memorise". **VERIFIED** [`RULES.md:1391`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1391) `@dcf2553` [`RULES.md:1410`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1410) `@3084d12` [`RULES.md:1470`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1470) `@fc54855`
[`STATE.md:144`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L144) `@cc9675b` [`STATE.md:171`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L171) `@5c6613d` G-OWN concluded on the same basis that "the corpus negatives are
therefore real negatives". **VERIFIED** [`RULES.md:2822`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2822) `@d29112c` On 2026-10-15, R-REPRO re-created the
September control from public data in a fresh container. Forward AUC is 0.99659 and reverse 0.49633; the frozen rule
gives 71 valid, 7 flagged, clusters [4, 2, 1]; and the whole output TIFFs hash to the values the September package
recorded. **VERIFIED** (PRE-REGISTERED) [`RULES.md:3273`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3273) `@eed0fac` [`RULES.md:3275`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3275) `@eed0fac`
[`RULES.md:3278`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3278) `@eed0fac` [`RULES.md:3283`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3283) `@eed0fac` That is a reproduced best case on a training-set sheet, not a
held-out validation. **INFERENCE** [`RULES.md:3292`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3292) `@eed0fac`

**Why it matters.** **INFERENCE** Before R-HELDOUT, all label-based evidence on record that this reader can see text
came from sheets in the model's training set. The eligible-scroll negatives (1/113, 0/190) are only as informative
as the reader's sensitivity on text the model has not seen, and until R-HELDOUT no result on record measured that.
The declaration wrote down in advance that, if the reader could not be shown to fire on unseen known text, those
negatives would not be evidence of absent ink [`RULES.md:3265`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3265) `@661ff64` [`RULES.md:3267`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3267) `@661ff64`. R-HELDOUT (below)
measured it. The pixel signal transfers, but on unseen PHerc0841 text the frozen unit screen flags 1 of 15
text-bearing units [`RULES.md:3309`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3309) `@7925b3a`, so those negatives are still not evidence of absent ink
[`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a` [`RULES.md:3325`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3325) `@7925b3a` [`RULES.md:3326`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3326) `@7925b3a`.

**Fix.** R-HELDOUT was declared before any of its data was downloaded [`RULES.md:3231`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3231) `@661ff64`. Its population is
PHerc0841, three labelled segments outside the training config [`RULES.md:3244`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3244) `@661ff64`. Its bars
[`RULES.md:3261`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3261) `@661ff64` [`RULES.md:3263`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3263) `@661ff64` and what follows from each outcome [`RULES.md:3265`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3265) `@661ff64` were
written in advance. **VERIFIED** The analysis code `scripts/rheldout.py` was committed before any held-out output
existed. **VERIFIED** [`scripts/rheldout.py:15`](https://github.com/abundantjoe/hercules/blob/d8c39a3/scripts/rheldout.py#L15) `@d8c39a3` Pinned by
`scripts/tests/test_rheldout.py::test_text_units_flag_blank_units_do_not_and_the_verdict_is_strong`,
`::test_a_detector_with_no_depth_asymmetry_is_blind`, `::test_partial_band_and_pass_without_cluster` and
`::test_labels_on_a_different_canvas_are_refused`. No test can check an external training config; reading it is a
manual step. Every statement resting on "unmemorised" is listed in [SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md), and no
earlier notebook entry was edited [`RULES.md:3242`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3242) `@661ff64`.

**R-HELDOUT result (2026-10-15).** In one line: the model's pixel signal transfers to an unseen scroll, but the
frozen unit screen flags 1 of 60 valid units on that known text.

- **HELDOUT-AUC: TRANSFERS.** Pooled over 3,669,681 supervised px: forward AUC **0.8393**, reverse **0.5486** (per
  segment 0.8531 / 0.5324, 0.8176 / 0.5938, 0.8294 / 0.5363). **MEASURED** (PRE-REGISTERED; the analysis code was
  committed before the output) [`RULES.md:3301`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3301) `@7925b3a` [`RULES.md:3302`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3302) `@7925b3a` [`RULES.md:3303`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3303) `@7925b3a`
- **HELDOUT-RULE: PASS, not STRONG.** 60 valid units, **1 flagged**, no cluster; swapped order 0 flagged.
  Text-bearing units (φ ≥ 0.02): **1 of 15** flagged (exact 95 % CI 0.0016–0.3195; RULES.md prints 0.0017, rounded to nearest). Supervised blank units: none
  exist on these segments (0 of 0), so the blank arm is empty, not passed. **MEASURED** (PRE-REGISTERED)
  [`RULES.md:3306`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3306) `@7925b3a` [`RULES.md:3307`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3307) `@7925b3a` [`RULES.md:3308`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3308) `@7925b3a` [`RULES.md:3309`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3309) `@7925b3a` [`RULES.md:3310`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3310) `@7925b3a`
- **The most-inked units do not fire.** The seven units with φ ≥ 0.10 (max 0.2347) flag **0 of 7**, at margins
  +0.0360 to +0.0663 and forward means 0.3388–0.3729 (corrected from 0.3432–0.3729 by a later note). **MEASURED**
  [`RULES.md:3314`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3314) `@7925b3a` [`RULES.md:3315`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3315) `@7925b3a` [`RULES.md:3316`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3316) `@7925b3a` [`RULES.md:3334`](https://github.com/abundantjoe/hercules/blob/091c2fa/RULES.md?plain=1#L3334) `@091c2fa` [`RULES.md:3335`](https://github.com/abundantjoe/hercules/blob/091c2fa/RULES.md?plain=1#L3335) `@091c2fa`
- **Second code path.** The ordinary reader (`read_chart.py --maps-only`) calls the three known-text segments NOT
  ESTABLISHED, NOT ESTABLISHED, BLANK. It agrees with `rheldout.py` on the auto grid, and neither grid has a ≥ 3
  cluster. **MEASURED** [`RULES.md:3311`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3311) `@7925b3a` [`RULES.md:3312`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3312) `@7925b3a` [`RULES.md:3313`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3313) `@7925b3a`
- **Against w040.** On w040, a training-set sheet, the same grid flags 5 of 16 text-bearing units. **MEASURED**
  [`RULES.md:3317`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3317) `@7925b3a`
- **Held-out reference rate**, reported beside 7/71 as declared: 1 of 60 valid units (exact 95 % CI 0.0004–0.0894);
  1 of 15 text-bearing units. **MEASURED** [`RULES.md:3318`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3318) `@7925b3a` [`RULES.md:3319`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3319) `@7925b3a`
- **EXPLORATORY comparisons.** Against the held-out rate 1/60, the eligible-scroll counts are not distinguishable
  from known text on an unseen scroll: R-DEFICIT 1/113, Fisher one-sided p = 0.575; R-CREST-POWER 0/190, p = 0.24.
  The held-out rate against the training-set control 7/71 gives p = 0.0523. **VERIFIED** (EXPLORATORY; recomputed by
  `scripts/release_stats.py` on 2026-10-15) [`RULES.md:3320`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3320) `@7925b3a` [`RULES.md:3321`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3321) `@7925b3a` [`RULES.md:3322`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3322) `@7925b3a` [`RULES.md:3323`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3323) `@7925b3a`
  [`records/release/release_stats.json:40`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L40) `@7925b3a` [`records/release/release_stats.json:112`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L112) `@7925b3a` [`records/release/release_stats.json:297`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L297) `@7925b3a`
- **Reading.** The eligible negatives are what this screen returns on real unseen text, so they are not evidence of
  absent ink. The limiting factor exposed is the unit screen's sensitivity on unseen text (margins diluted to
  +0.04–0.07 by 0.5 cm² averaging, against a +0.08 bar calibrated on training-set text), not the model's pixel-level
  transfer. **INFERENCE** [`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a` [`RULES.md:3326`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3326) `@7925b3a` [`RULES.md:3327`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3327) `@7925b3a`

**Generalises to.** Before calling a labelled segment a validation sheet, search the model's training config and the
label bucket for its id; a sheet the model trained on measures memorisation.

### 35. Do not compute unit-level p-values as if clustered units were independent

**In short: the unit-level p-values overstate the evidence. With clusters collapsed, R-DEFICIT is not significant
(p = 0.161), and against the held-out rate 1/60 no comparison falls below p = 0.24.** **VERIFIED** (EXPLORATORY)
[`records/release/release_stats.json:37`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L37) `@0afc07e` [`records/release/release_stats.json:112`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L112) `@7925b3a`; all values in the table below.

**What happened.** The control's flagged units sit in clusters [4, 2, 1] on one sheet. **VERIFIED**
[`RULES.md:1487`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1487) `@140730b` Under independence a 4-cluster has probability 0.0257. **MEASURED**
[`RULES.md:2501`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2501) `@cf64ed9` R-DEFICIT's unit-level comparison, 1 flagged of 113 against 7 of 71, gives Fisher exact
one-sided p = 0.00576 in the release recomputation, printed as p = 0.0058 in the notebook. **VERIFIED**
[`records/release/release_stats.json:34`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L34) `@0afc07e` [`RULES.md:2230`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2230) `@e38ac0f` Collapsing each control cluster to one
event (3 events in 71 units) gives p = 0.161, not significant. **VERIFIED** (EXPLORATORY, added at release)
[`records/release/release_stats.json:37`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L37) `@0afc07e` The table gives every comparison under the same collapse and against the held-out rate of lesson 34:

| Comparison | Unit-level Fisher p vs 7/71 | Cluster-collapsed Fisher p vs 7/71 | Fisher p vs held-out 1/60 | Source |
|---|---|---|---|---|
| R-DEFICIT, 1/113 | 0.00576 | 0.161 | 0.575 | [`records/release/release_stats.json:34`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L34) `@0afc07e` [`records/release/release_stats.json:37`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L37) `@0afc07e` [`records/release/release_stats.json:40`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L40) `@7925b3a` |
| R-CREST-POWER PHerc1203 half, 0/64 | 0.00961 | 0.143 | 0.484 | [`records/release/release_stats.json:56`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L56) `@0afc07e` [`records/release/release_stats.json:59`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L59) `@0afc07e` [`records/release/release_stats.json:64`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L64) `@7925b3a` |
| R-CREST-POWER phase 1, 6 of 12, 0/114 | 0.00101 | 0.0551 | 0.345 | [`records/release/release_stats.json:78`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L78) `@0afc07e` [`records/release/release_stats.json:81`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L81) `@0afc07e` [`records/release/release_stats.json:88`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L88) `@7925b3a` |
| R-CREST-POWER phase 1, 11 of 12, 0/190 | 8.81e-05 | 0.0195 | 0.24 | [`records/release/release_stats.json:100`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L100) `@0afc07e` [`records/release/release_stats.json:103`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L103) `@0afc07e` [`records/release/release_stats.json:112`](https://github.com/abundantjoe/hercules/blob/7925b3a/records/release/release_stats.json#L112) `@7925b3a` |

All four rows: **VERIFIED** (recomputed by `scripts/release_stats.py` on 2026-10-15; the collapse and the held-out
comparison are EXPLORATORY, both added at release).

**Why it matters.** **INFERENCE** The unit-level tests assume independence that the control itself violates, so
they overstate the evidence. Under the conservative reading, R-DEFICIT is not significant. Every comparison against
7/71 also uses a reference rate from one surface, so at the surface level the control's effective n is 1, and that
surface is a training-set sheet (lesson 34). R-HELDOUT declared that on PASS a held-out rate becomes the reference
for unseen text [`RULES.md:3268`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3268) `@661ff64`, and the result reports 1/60 beside 7/71
[`RULES.md:3318`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3318) `@7925b3a` [`RULES.md:3319`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3319) `@7925b3a`. Against 1/60, none of the four comparisons falls below p = 0.24.

**Fix.** `scripts/release_stats.py` reports the unit-level and the cluster-collapsed value for every comparison.
**VERIFIED** [`scripts/release_stats.py:23`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L23) `@0afc07e` [`scripts/release_stats.py:112`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L112) `@0afc07e` Since `7925b3a` it also reports each
comparison against the held-out rate 1/60. **VERIFIED** [`scripts/release_stats.py:63`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L63) `@7925b3a` [`scripts/release_stats.py:66`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L66) `@7925b3a` Pinned by
`scripts/tests/test_release_stats.py::test_collapsing_clusters_weakens_the_unit_level_evidence`; no test pins the
held-out comparison. No earlier verdict was edited. See [RESULTS](RESULTS.md) for both values beside each comparison.

**Generalises to.** Tiles and pixels on one surface are not independent observations; collapse clusters or work at
the surface level before quoting a p-value, and say what the effective n is.

### 36. Re-check published tool images at release; a web page calling an image up to date is not a test

**What happened.** On 2026-10-15, `ghcr.io/scrollprize/villa/volume-cartographer:edge` and `:main` still resolve to
an image created 2026-05-13, with revision label `1e3f4c021f4e53bea3867772ed05f51a7e586a9c`. **VERIFIED**
[`records/release/edge_image_check_2026-10-15.md:8`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L8) `@0afc07e` [`records/release/edge_image_check_2026-10-15.md:9`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L9) `@0afc07e`
Its `vc_render_tifxyz --help` lists no `--flip-normals`, and running it with `--flip-normals` prints
`Error: unrecognised option '--flip-normals'` and exits 1. **VERIFIED**
[`records/release/edge_image_check_2026-10-15.md:14`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L14) `@0afc07e` [`records/release/edge_image_check_2026-10-15.md:15`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L15) `@0afc07e`
scrollprize.org/segmentation calls it "an up-to-date image". The ink-detection tutorial (scrollprize.org/tutorial5)
uses `--flip-normals` and says it "reproduces the depth orientation of the published renders and the training
labels". **VERIFIED** (pages fetched 2026-10-15) [`records/release/edge_image_check_2026-10-15.md:18`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L18) `@0afc07e`
[`records/release/edge_image_check_2026-10-15.md:20`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L20) `@0afc07e` [`records/release/edge_image_check_2026-10-15.md:21`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L21) `@0afc07e`
In September, a smoke render with this binary matched the team stack only with the slice order reversed, at Pearson
0.42–0.82 (lesson 18). **MEASURED** [`RULES.md:28`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28) `@2e62892`

**Why it matters.** **INFERENCE** A user who drops the unrecognised flag to make the tutorial command run gets the
depth order the model was not trained on, and on known text that order scores at chance. This was not run end to end
with the stale binary. [`records/release/edge_image_check_2026-10-15.md:27`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L27) `@0afc07e`
[`records/release/edge_image_check_2026-10-15.md:28`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/edge_image_check_2026-10-15.md?plain=1#L28) `@0afc07e`

**Fix.** [REPRODUCE](REPRODUCE.md) tells users not to use the published image and to build the tools from villa
`5ab585f` with `scripts/build_vc3d.sh`. **VERIFIED** [`docs/REPRODUCE.md:22`](https://github.com/abundantjoe/hercules/blob/2bf30b3/docs/REPRODUCE.md?plain=1#L22) `@2bf30b3` The image's help text is saved
in `records/release/vc_render_tifxyz_help_edge_2026-05-13.txt`. No test can pin an external image; the check is
repeatable with the commands described in the record.

**Generalises to.** At every release, run the documented render command inside the published image on an input
whose correct output you know.

### 37. Recompute numbers from the files that produced them; do not copy them by hand

**What happened.** Reading the notebook against the files that produced its numbers found these recording errors.
None changes a verdict. **INFERENCE**

| # | Notebook says | The producing file or another record says | Label |
|---|---|---|---|
| a | P-DRY: "Verifier: 20 PASS ... and exactly 2 FAIL" [`RULES.md:87`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L87) `@a2d0e59` | `verify_report.txt` has 19 PASS and 2 FAIL lines, 21 checks [`packages/DRYRUN_PHerc0139_w040/verify_report.txt:21`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/verify_report.txt#L21) `@a2d0e59`; a later entry says "21 checks, exactly 2 FAIL" [`RULES.md:993`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L993) `@8c43c62` | **VERIFIED** (line count, 2026-10-15) |
| b | G-A-crop: "Identical to G-B Bar 2 on the rendered crop to 4 decimals" [`RULES.md:19`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L19) `@acfe631` | True for the forward AUCs. Reverse is 0.50301 against G-B Bar 2's 0.50265, TTA reverse 0.56597 against 0.56576 [`RULES.md:30`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L30) `@e3a0717` | **VERIFIED** |
| c | Forward 0.4979 and 0.4980 attributed to the two featureless surfaces, CT std 8.6 and 10.0 [`RULES.md:386`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L386) `@71e81b2` | The std-8.63 surface is recorded at forward 0.4436 [`LEDGER.md:189`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L189) `@d4d0a6a` [`RULES.md:1931`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1931) `@5bb4e28`; forward 0.4979 is the PHerc0358 read `auto_grown_20260918123053821` [`LEDGER.md:175`](https://github.com/abundantjoe/hercules/blob/71720ce/LEDGER.md?plain=1#L175) `@8f51af5` | **VERIFIED** |
| d | CT std 10.05 is "the lowest in the corpus" [`RULES.md:1928`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1928) `@5bb4e28` | 8.63 is given as the lowest [`RULES.md:1931`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1931) `@5bb4e28` [`RULES.md:2134`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2134) `@22e440f` | **VERIFIED** |
| e | The +0.0873 unit is a "plain read" [`RULES.md:2754`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2754) `@5ec1aee` | Its key is `ink9um_seed42+tta` [`RULES.md:389`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L389) `@71e81b2`, and +0.0873 is the maximum of the TTA population [`RULES.md:1542`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1542) `@2fffd22` | **VERIFIED** |
| f | Canvas labelled-ink fraction 1.46 % [`RULES.md:2283`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2283) `@e38ac0f` [`RULES.md:2396`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2396) `@07bfb73` | 0.0161 for the whole canvas [`RULES.md:2693`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2693) `@6ebbca0`; the denominators are not stated | **VERIFIED** |
| g | G-OWN trace area 4.845 cm² [`RULES.md:2657`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2657) `@3adee87` | 4.86 cm² on the QC line [`RULES.md:2695`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2695) `@6ebbca0` | **VERIFIED** |
| h | `heldout.md`: "Gate C and the w028 judge: pending (queued)." [`packages/DRYRUN_PHerc0139_w040/heldout.md:4`](https://github.com/abundantjoe/hercules/blob/71720ce/packages/DRYRUN_PHerc0139_w040/heldout.md?plain=1#L4) `@a2d0e59` | Gate C's forward result was recorded [`RULES.md:36`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L36) `@aa32a21` and its reverse result and PASS later the same day [`RULES.md:36`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L36) `@2fff337`; the package file, written earlier, was never updated | **VERIFIED** |
| i | `release_stats.py` as first committed listed 0.00576, 1.08e-4 and 0.00961 as "Values printed in RULES.md" [`scripts/release_stats.py:49`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L49) `@0afc07e` [`scripts/release_stats.py:51`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L51) `@0afc07e` [`scripts/release_stats.py:52`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L52) `@0afc07e` [`scripts/release_stats.py:53`](https://github.com/abundantjoe/hercules/blob/0afc07e/scripts/release_stats.py#L53) `@0afc07e` | The notebook prints 0.0058 [`RULES.md:2230`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2230) `@e38ac0f`, 1.1 × 10⁻⁴ [`RULES.md:2231`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2231) `@e38ac0f` and 0.0096 [`RULES.md:3134`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3134) `@f9bfe3b`. They agree after rounding, but the constants were not the printed strings. Fixed in `7925b3a`: the script now holds each value as printed, with its significant figures and RULES.md line, and all ten reproduce at that precision [`scripts/release_stats.py:49`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L49) `@7925b3a` [`scripts/release_stats.py:52`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L52) `@7925b3a` | **VERIFIED** (fixed at release; script run 2026-10-15) |

**Why it matters.** **INFERENCE** Each error is small. A sceptical reader who finds one hand-copied number that does
not match its file has reason to doubt the rest.

**Fix.** `scripts/release_stats.py` recomputes every headline statistic of the release from its recorded counts,
with exact intervals, and checks the ten hand-written Fisher and binomial values at the precision the notebook
printed them. **VERIFIED** [`scripts/release_stats.py:49`](https://github.com/abundantjoe/hercules/blob/7925b3a/scripts/release_stats.py#L49) `@7925b3a` Pinned by `scripts/tests/test_release_stats.py::test_every_recorded_value_is_reproduced`
and `::test_intervals_are_never_narrowed_by_rounding`. `examples/check_quickstart.py` compares ten outputs of the
quick start with the recorded values and fails on any difference. `examples/quickstart.sh` runs it as its last step.
On 2026-10-15 all ten checks passed. **VERIFIED**
[`examples/check_quickstart.py:32`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/check_quickstart.py#L32) `@0afc07e` [`examples/quickstart.sh:41`](https://github.com/abundantjoe/hercules/blob/0afc07e/examples/quickstart.sh#L41) `@0afc07e` The quick start takes about 16 s on a 4-core
CPU. **MEASURED** [`examples/README.md:5`](https://github.com/abundantjoe/hercules/blob/2bf30b3/examples/README.md?plain=1#L5) `@2bf30b3` Neither tool covers counts such as
P-DRY's pass count or attributions in prose (rows a to h). Those were found by reading, and they are listed in
[SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md) under "Recording errors found at release". No notebook entry was edited.

**Generalises to.** Let code write the numbers that go into a report, and check every copied number mechanically
against the file that produced it.

---

## Appendix A. Source conflicts and open items

Conflicts between sources found while writing this document. Each is cited where it arises above.

| Lesson | Conflict or open item | Sources |
|---|---|---|
| 12 | "I am correcting it 35 minutes later" rests on fast wall-clock labels (03:45, 04:20). The commits are dated 02:33:11 and 02:45:37 UTC. | [`RULES.md:1631`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1631) `@750629f` [`RULES.md:1737`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1737) `@2d9e698`; commits [`8328202`](https://github.com/abundantjoe/hercules/commit/8328202), [`750629f`](https://github.com/abundantjoe/hercules/commit/750629f) |
| 14 | RULES: the guessed volume id "has already cost one wrong read". CHANGELOG: it was "caught before it ran". No record of a wrong read was found. | [`RULES.md:2044`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2044) `@b6db282` [`CHANGELOG.md:420`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L420) `@5c6613d` |
| 16 | The median 1052 s is "over all 14 at that budget" in one entry, which includes the two pre-pruning traces at 269 s and 333 s, and "over the 14 traces after" in others. | [`RULES.md:562`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L562) `@0974977` [`RULES.md:2066`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2066) `@658d5c2` [`STATE.md:232`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L232) `@a7fac67` |
| 16 | Two declared throughput checks have no recorded outcome. | [`RULES.md:329`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L329) `@ce886a7` [`RULES.md:569`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L569) `@0974977` |
| 16 | The record says seven tests pin the first disk-guard fix and the changelog says 8; the test file now holds ten test functions (the tenth added in `091c2fa`). | [`RULES.md:566`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L566) `@0974977` [`CHANGELOG.md:409`](https://github.com/abundantjoe/hercules/blob/71720ce/CHANGELOG.md?plain=1#L409) `@78532c5` |
| 17 | The record and the test module's docstring say the cause of the 1-of-25 dense queue was not established. One test docstring calls the pipe-fed `while read` "how dense_loop.sh lost 24 seeds". | [`RULES.md:745`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L745) `@2fcbbcd` [`scripts/tests/test_loop_scripts.py:3`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_loop_scripts.py#L3) `@2fcbbcd` [`scripts/tests/test_loop_scripts.py:139`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/tests/test_loop_scripts.py#L139) `@4bb3af8` |
| 5 | "106 plain units over 29 reads (9 direct + 37 mirrored), 54 TTA units over 17 reads": the parenthesis counts 46 reads, which matches the plain and TTA reads together, not the 29 plain reads. | [`RULES.md:1536`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1536) `@2fffd22` |
| 5 | The writer that left forward `valid_units` lists empty was worked around, not fixed at source. | [`RULES.md:1530`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1530) `@2fffd22` |
| 10 | A test still asserts `pgrep -f` in the supervisor's G-GP part 5 block, and `supervisor.sh` still guards with `pgrep -f`. Not shown to be a defect. | `scripts/tests/test_supervisor_inline.py::test_ggp5_consensus_build_is_armed_and_cannot_fire_twice`; [`scripts/supervisor.sh:215`](https://github.com/abundantjoe/hercules/blob/71720ce/scripts/supervisor.sh#L215) `@4d7ac37` |
| 1 | The root cause of both reverse-map truncations is unproven; the fixes are detection and lower load. | [`RULES.md:1768`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1768) `@a0c1f8c` |
| 20, 35 | R-DEFICIT's Fisher p is printed as 0.0058 in the notebook and as 0.00576 in the release recomputation; these are the same value at different precision. | [`RULES.md:2230`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2230) `@e38ac0f` [`records/release/release_stats.json:34`](https://github.com/abundantjoe/hercules/blob/0afc07e/records/release/release_stats.json#L34) `@0afc07e` |
| 31, 34 | Several entries call w040 a sheet "the model did not memorise"; it is a training-set sheet. | [`RULES.md:1391`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1391) `@dcf2553` [`RULES.md:2822`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2822) `@d29112c` [`STATE.md:171`](https://github.com/abundantjoe/hercules/blob/71720ce/STATE.md?plain=1#L171) `@5c6613d` against [`RULES.md:3240`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3240) `@661ff64` |
| 37 | Rows a to i of lesson 37. | see lesson 37 |
| 6, 7, 9, 12, 21, 22, 23 | No automated test pins these practices: restarting loops after a fix, not editing running scripts, the progress monitor, `date -u` timestamps, R-SHAPE's independence check, the R-COVER9 reading, the proxy's non-use. | this document |
| 10, 28, 15 | Counts the record reports about itself were not re-derived: `pkill -f` matching the operator's shell "three times", "the third time today" a number was composed before its input was read, and the started-vs-done defect counts ("third", "fifth"). | [`RULES.md:2989`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2989) `@8aab40d` [`RULES.md:3164`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L3164) `@d94ea58` [`RULES.md:933`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L933) `@9d18317` [`RULES.md:1187`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1187) `@303a5ce` |

## Appendix B. Other defects on record

Defects on record that fall outside the 37 numbered lessons, or are only mentioned within them.

| Defect | What happened | Fix and test |
|---|---|---|
| Cleanup corrupted a result file (R-CROSS) | A disk cleanup gzipped every self-intersection report over 100 KB (533 MB -> 57 MB). `rcross_result.py` then skipped every compressed report, shrinking the populations from 66 and 107 to 55 and 17, and overwrote `rcross.json`. **MEASURED** [`RULES.md:890`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L890) `@ba3c259` | Reads `.json` and `.json.gz` alike. **VERIFIED** (test run 2026-10-15) `scripts/tests/test_rcross_result.py::test_compressed_reports_are_read`. The regenerated numbers are identical to those recorded before the cleanup (ratio 1.87x, NOT ADMITTED). **MEASURED** [`RULES.md:899`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L899) `@ba3c259` |
| Duplicate traces after a loop restart (G-GP-4) | A stale-proxy restart kills the loop but not its in-flight trace, so the restarted loop traced the same seed again, twice in one evening. **MEASURED** [`RULES.md:909`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L909) `@fc07ede` | The loop waits for an orphaned trace of the same seed. **VERIFIED** [`RULES.md:915`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L915) `@fc07ede` `scripts/tests/test_loop_scripts.py::test_the_loop_waits_for_an_orphaned_trace_of_the_same_seed`, `scripts/tests/test_patch_agreement.py::test_two_traces_from_the_same_seed_count_once` |
| Reader skipped consensus surfaces (G-GP-4) | `run_patch_dir.py` enumerated only `auto_grown_*` and `team_*`, so every consensus surface (`auto_trace_*`) was skipped, including the 4.077 cm² surface that met milestone 2. **MEASURED** [`RULES.md:1182`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1182) `@303a5ce` | `auto_trace_*` is enumerated, and an `--only` naming a missing patch exits with an error. **VERIFIED** [`RULES.md:1187`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1187) `@303a5ce` `scripts/tests/test_run_patch_dir.py::test_consensus_surfaces_are_enumerated`, `::test_only_that_names_a_missing_patch_fails_loudly` |
| Container reclaims killed long reads | A reclaim at 01:35 UTC killed every running job, including a TTA read at 4 h 10 m. **MEASURED** [`RULES.md:1227`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1227) `@b278590` | The consensus surface was read with the plain screening recipe, which fits inside the reclaim interval. **INFERENCE** [`RULES.md:1241`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1241) `@a9d18ab` No test. |
| Protocol 9 step 6 looked in the wrong directory | The `P9_DRY=1` rehearsal found that step 6, the seed43 confirmatory read, looked in `patches/<scroll>` and would have failed on any candidate from `_cons_partN`, `_small`, `_src` or `_dense`. **MEASURED** [`RULES.md:1718`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1718) `@eeb9fc6` | Step 6 uses the candidate's parent directory. `scripts/tests/test_protocol9.py::test_step_six_reads_the_candidate_where_it_actually_lives` |
| R-ROWS implementations | The mask-overlap denominator collapsed at large lags, returning "autocorrelation" 26.6 and 5.1 where a normalised ACF caps at 1.0, and the band maximum was taken where the declaration said first peak. **MEASURED** [`RULES.md:348`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L348) `@1eed321` | Overlap ≥ 30 %, local maxima only. No test named in the record. |
[line withheld: prize-candidate detail under review]
| Racy trace cap and partial renice | `rsmall_loop.sh` capped traces with a racy `ps` count, and renicing an inference by its main pid left dataloader workers at the old priority (174 % CPU against 127 % and 107 %). **MEASURED** [`RULES.md:375`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L375) `@6e0f06a` | The loop takes the flock slot pool; the whole process tree is reniced. No test named in the record. |
| Deceleration read from a growing trace | A recorded deceleration to +0.06 cm² per trace was a sampling error taken while a trace was still growing. Sampled at completed traces it was about +0.4 cm² per completed trace. **MEASURED** [`RULES.md:1112`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1112) `@1e2c5ca` | Corrected in the notebook. No test. |
| Absolute symlinks inside the container | The consensus source directory used absolute symlinks that do not resolve inside the container, so the tool reported "no source surfaces found". **MEASURED** [`RULES.md:1073`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1073) `@0689329` | Relative links, and a runner check that every link resolves. No test named in the record. |
| Stale render markers | Five of the ten R-BEST-2 surfaces carried a stale `render.zarr.complete` marker with no render. **MEASURED** [`RULES.md:1007`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1007) `@dffc2ee` | Both markers are dropped when the render directory is absent. `scripts/tests/test_run_patch_dir.py::test_stale_render_markers_are_dropped_before_a_reread` |
| CT keep-list never matched (`disk_guard.sh`, found at release) | Below the 3 GB hard floor the guard cleared the level-4 CT caches with `case $name in $KEEP_CT)`, where `KEEP_CT="PHerc0826\|PHerc0358\|..."`. A `\|` that arrives through a variable expansion is a literal character in a case pattern, not alternation, so the pattern matched nothing and the five kept caches were deleted with the rest. The cost was refetch time only; no map or verdict was touched. **VERIFIED** (code read, 2026-10-15) [`scripts/disk_guard.sh:13`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L13) `@925c037` [`scripts/disk_guard.sh:43`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L43) `@0974977` [`scripts/disk_guard.sh:25`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L25) `@091c2fa` [`scripts/disk_guard.sh:27`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L27) `@091c2fa` [`scripts/disk_guard.sh:28`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L28) `@091c2fa` | Fixed in `091c2fa` with `keep_ct()` [`scripts/disk_guard.sh:29`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L29) `@091c2fa` [`scripts/disk_guard.sh:88`](https://github.com/abundantjoe/hercules/blob/091c2fa/scripts/disk_guard.sh#L88) `@091c2fa`. `scripts/tests/test_disk_guard.py::test_the_ct_cache_keep_list_actually_keeps` |
