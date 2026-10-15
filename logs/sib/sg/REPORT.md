Provenance: Project HERCULES | owner the owner | [id removed]

# Task sg: the submission gate SG as mechanical, unit-tested code

## sg-pkg2: STATUS: DONE (2026-09-26; orchestrator task of 00:42Z; Q9 and Q10 defaults accepted)

1. **SG 11 REF-calibration runner** (`hercules.sg.refcal`; PROPOSAL-DECL-SG11-REFCAL-1). It is coded and hashed but **not run**.
   - It reports the SG 11 pass rate on REF reader boxes and the rate of each component. The height component is given with SG semantics and also alone over windows with >= 2 rows.
   - It reports the pass rate at a grid of candidate B8 fraction bars, and the pitch-CV and pitch/height distributions, two-row windows included.
   - Tests: 5 known-answer.
   - Hashes: `refcal.py` 669429e06050e1793b4e9eddf18f81c0eabb3ab3642a03cf196d854d7730e99a; `test_sg_refcal.py` 2f80176dcd0d392775c64f2b10b1ce7c0227c36c3f9442c6b3735077946da6ec. Both match the values recorded in the proposal before any use.
2. **Licence-lineage checker** (`tools/sib/sg/licence/lineage.py`, sha256 db6608c1694e8719614b1eae51079d5cba21bf4d1884c811f42ff05e8e52053a; 24 tests). It gives PERMITS-RELEASE / UNVERIFIED / BLOCKS from public metadata only. It is a pre-submission item, never an SG bar.
   - **Current base lineage: overall BLOCKS.**
     - The ink_9um checkpoint is MIT: PERMITS-RELEASE.
     - The open-data bucket's LICENSE.txt is CC BY-NC 4.0, so permissive release of derived data is not possible: BLOCKS.
     - The ink_9um labels state no licence: UNVERIFIED.
   - This is the owner's to settle with the organizers (ASK Q11). Details: `logs/sib/sg/licence/lineage_base_ink9um.json`.
3. **Paris 4 Title Prize kit** (`tools/sib/sg/submit_kit/p4_generate.py`, `tp_requirements.py`; DRY RUN only; DECL-P4-2 item 7):
   - **Page:** re-fetched 2026-09-26T00:47Z, raw sha256 7e653247...; the rendered text is unchanged from 2026-09-25, so the byte difference is build noise.
   - **Form:** the Title Prize form was read without sign-in. It has an Email field plus 4 required items, all OWNER-ONLY.
   - **Requirements:** TP-01..TP-22, requirement sentences only, verbatim and tested.
   - **Drafts:** answer sheet, methodology, FP mitigation and disclosure. The disclosure covers the blind LLM readers with correlated errors, the uncalibrated reader change (DECL-P4-2-A1), that the output is official model output and not ours, that there is no reference to seal against, and that the project names no title words.
   - **Guards:** the generator refuses any reader-text field or Greek character, so no title words can pass through. Every number, including the declared bars, comes from a named field.
   - **TP-16** (held-out validation) is honestly MISSING DATA, because no ground truth exists for the title region.
   - DRY RUN output is in `logs/sib/sg/submit_kit/dryrun_p4_output/`.
4. **Checklist rows:** the FL checklist now carries PKG-01 (licence lineage), PKG-02 (SG 11 REF calibration record) and PKG-03 (the P4 kit, a separate filing). The P4 checklist carries PKG-01. Submit-kit tests: 26.

**Tests and hashes**
- Merged-layout suite: **726 passed, 7 skipped, 0 failed**.
- SG package combined_sha256 at the merged paths (now including `refcal.py`): **b34b05c553eb83ad439bb1a0027118b5ca074b0755e39555848941a592460720**
- Tests combined_sha256: **7d9fd9bd08901bf7f9ea6ce9890555c34822ead4174a8ff9e424977baec7b510**
- Submit-kit combined_sha256: 988ec1aa7599cda82b4ce502bd11de7bfdc0c61379cf611be289c4db243f43a0
- Licence checker combined_sha256: 6cfdd60316febae8c13332fab7e7095238272f0e85a7abc8cb87a22bd07ae4bf
- The other SG files are unchanged from the table below. `refcal.py` is the only new code file.

**Open:** ASK Q7 and Q8 (prediction-calibration defaults) and Q11 (licence).


## STATUS: DONE (SG code, rulings incl. B8 revision, Q6 calibration, submit-kit)

**SG code** (`tools/sib/sg/pkg`, version `hercules-sg-1.2.0`; B8 revised to the median-only bar). The merged-layout suite (`run_merged_tests.sh`) gives **721 passed, 7 skipped, 0 failed**. Final hashes (`hercules.records.codehash` file_sha256 / combined_sha256; the bytes are identical staged and merged):

| sha256 | merged path |
|---|---|
| b679418a908647dda8e0e565a25371a8a15c080b5ddcc4308ab3b623ac3a4594 | src/hercules/sg/__init__.py |
| 4f7ad650526667722438f9a3acc5bba0c135a65dec66d5179f0e78e9ba35ec3c | src/hercules/sg/cli.py |
| 1285ed3c3bffa4f7a84f00dbbc07379eea8782508c235b55f13ec581ad770263 | src/hercules/sg/constants.py |
| e43a9b7dbaac32eff70e593d17e611bc7110e4631dd327449deeb7ff0db5132e | src/hercules/sg/copytest.py |
| 62ef2f9f54bab428d9ac43ee0a0de40a6ccb24f7aad5d4dc8daacabc0f14da2e | src/hercules/sg/copytest_null.py |
| f0e3f51840eb45bf08c520c453325ac2fb49fcaa9a1652bca6ae7b685a253076 | src/hercules/sg/gate.py |
| 215b0237795ef36795ae96ae9d8e2b7bdf9fcdef922bd8b137f3da137deb28c5 | src/hercules/sg/synth.py |
| d8263b18083cde663f9032fe96da45800691bbef6ef41c92f0b02b262baaf3b7 | tests/test_sg_cli.py |
| a9287ba4c10288f29e25eed9092ccc56fc3e49ad02dcfdea39c1261388247095 | tests/test_sg_copytest.py |
| 6f40013d5618d6dda84235a1afdcff48ce04f29ba252b7ab947790ba4437a3bd | tests/test_sg_gate.py |
| 1f4c946d1c90a2f974c28faaa7639f61c8672ba043793f265b0f5d9fc613e628 | tests/test_sg_region.py |

- combined_sha256, code at the merged paths `src/hercules/sg/*`: **cabfd26c6259623e7f43a6799c2754a4ebe2debc8e0d3a7c3fbec3cf037b1a86**
- combined_sha256, tests at the merged paths `tests/test_sg_*`: **b21a14b4c3358658f13f0b250f395922189c04b8dcc42627863439b742c8bae5**
- combined_sha256, code at the staged paths: 5ae22ba019d9f4d2f9c084575157b416654c5bcd69e51a17c0bec729ffd211c6
- These supersede the earlier hashes (`2368c348...` / `e1929294...`), which predate the B8 revision.

**Q6 calibration** (organizer model output, calibration only): see PROPOSAL-SG-LINESPACING-1 section 5.
- Known-text row pitch: median 4.7 mm; pitch/band 1.2-2.1 (p5-p95).
- Angles within 10 deg of horizontal in 91-100 % of tiles.
- **Only 58-68 % of known-text tiles meet the SG 11 pitch-CV bar** (measured risk, P5).

**Submit-kit** (`tools/sib/sg/submit_kit/`, combined_sha256 d5ea98e305fa509e696bd61a7df2c76750e79d87acf0b4743cb815c6658bfeb2; 14 tests in `tests/sib_sg_submit_kit.py`):
- **Output:** a draft-only generator (answer sheet, methodology, FL-14/24/25, FL-15 table, disclosure, FL-01..FL-25 checklist, trace). Every number comes from a named JSON field, and missing data is marked.
- **OWNER-ONLY:** email, name, team, the hosting link and the terms acceptance stay empty.
- **No submission path:** there is no network or submission code, and every file is headed "DRAFT - NOT SUBMITTED - K7".
- **Example:** a DRY RUN example is in `logs/sib/sg/submit_kit/dryrun_output/`.
- **Automatic filing (ASK Q9):** not built. K7 requires the owner to be present, and filing needs the owner's identity and terms acceptance.

**Live prize page change (2026-09-25; `logs/sib/sg/submit_kit/prizes_20260925_live.*`, raw sha256 2bc4b6df...):**
- **The eligible set is now 22: PHerc1447 has been removed** ("excludes those where letters have now been found").
- The open-source condition is now "code, data, model weights and results".
- `data/catalogue/eligible_products.json` (23) is outdated; it is outside my write scope.

## 0. Update 2026-09-25 (after the orchestrator's rulings)

- **Rulings applied:** B1, B6, B7, B8, B9, B13 and B14 are implemented. Each has a test where it alone fails; `rulings_applied.md` maps every ruling to code, test and commit. Version `hercules-sg-1.1.0`.
- **Staged package:** the code is now staged as the package `hercules.sg` at `tools/sib/sg/pkg/src/hercules/sg/`, with tests at `tools/sib/sg/pkg/tests/test_sg_*.py`. The merge into `src/` is two `cp` commands (`pkg/MERGE.md`). My brief's write scope does not include `src/`, so this waits on ASK Q1.
- **Merged-layout test:** `pkg/run_merged_tests.sh` runs a plain `pytest` on a scratch copy with the package overlaid: **719 passed, 7 skipped, 0 failed**.
- **B9 statistics: not computable.** The official PHerc0139 human labels (13 sets, label_set 20260918) hold only 4-25 isolated letters per segment, 68 distinct letters in total. That supports letter size but not row pitch. The line-spacing tool is validated on synthetic text (6 known-answer tests) and is ready for a dense source (ASK Q6).
- **B8 risk (measured):** on those 68 known-text letters only 75-78 % fall in 2-4 mm, whichever box side is used, against B8's >= 80 % bar. The median is 2.5-3.1 mm (ASK Q5; PROPOSAL-SG-LINESPACING-1).
- **B7 check under |NCC|:** the rerun null (`copytest_null_abs.json`) gives 0 false flags in all 10 cells with n_eff >= 30. The highest chance value was 0.743, rising from 0.691 to 0.743 between 100 and 1000 patches, so the pre-SG empirical-null check on the real patch set is essential.
- **Failures logged in runs.jsonl:**
  - a SyntaxError run of label_spacing.py (`global` placement);
  - a first merged-suite run whose scratch copy lacked `tools/` (1 collection error, then 4 errors; fixed by copying `tools/`);
  - `label_spacing_0139_t20/t30.json`, which fitted rows to 2-13 blobs per tile. It is invalid as a statistic and is kept only as a record.
- **Sections below:** they describe the first delivery. File paths there refer to the pre-move names, for example `tools/sib/sg/sg_gate.py`, which is now `pkg/src/hercules/sg/gate.py`.

Builder session, branch `claude/gifted-bell-gavnl5-sib-sg`. The work is code and synthetic tests only. No real data was read, no image was produced or viewed, and no seal, scorer key or encrypted file was touched. Machine-readable companion: `logs/sib/sg/sg_report.json`, which holds the code, test and scorer-module sha256 hashes, every constant, the null sweep and the run log.

## 1. What was built

| File | Contents |
|---|---|
| `tools/sib/sg/sg_constants.py` | Every bar of DECL-SG and DECL-EMPNULL, each line citing its item. Implementation choices are marked "choice" with the reason. |
| `tools/sib/sg/sg_gate.py` | Discovery rule and FDR calibration, the R rule, SG 1 (a-d), 2, 3, 4, 5, 6, 9, 11, 13, the rotation part of 14, and the runner `sg_check(inputs) -> per-item JSON`. |
| `tools/sib/sg/sg_copytest.py` | SG 7: masked FFT NCC over 24 rotation steps of 15 deg, plus an n_eff diagnostic. |
| `tools/sib/sg/sg_cli.py` | `sg_cli.py INPUTS.json --out R.json [--crops C.npz --patches P.npz]`. Exit code 0 = SG pass, 1 = not pass, 2 = error. |
| `tools/sib/sg/sg_synth.py` | Synthetic known-answer inputs (3 rows x 7 letters, 3.0 mm high, 5.0 mm pitch, 9.366 um metadata). |
| `tools/sib/sg/copytest_null.py` | Synthetic null of the SG 7 statistic. |
| `tools/sib/sg/logrun.sh`, `make_report_json.py` | Run log (`runs.jsonl`) and report assembly. |
| `tests/sib_sg_{gate,region,copytest,cli}.py` | 122 tests. |
| `logs/sib/sg/proposals/PROPOSAL-SG-CODE-1.md` | Interpretations B1-B15 and the SG 7 risk. These need the orchestrator's ruling. |

Reused unchanged from `src/hercules/scorer`: `agreed_letters` (same identity, 150 px, >= 2 of 3; greedy complete linkage), `identity_shuffle_null` (exact p = (1 + #null >= obs)/(1 + N)), `match_letters` (one-to-one maximum matching, same kind, distance <= r), `make_seal` (SG 13), the `discovery` core and canonical JSON. SG 1c re-implements the logic of `sg1c_evaluate`, with the bars read from DECL-SG constants (P99 with method "higher", >= 40 tiles, margin >= 10, agreed > null max).

## 2. How each part works (bar -> code)

- **Discovery (DECL-EMPNULL)**: PASS iff the text-order agreed count is >= k and the non-text-order agreed count is <= 1, with exactly 3 readers. Per-reader F_B is reported alongside. **Calibration**: at least 200 null tiles are required, else FAIL. FDR(k) = (null tiles passing)/(tiles). k starts at 5 and rises by 1 while FDR > 1 %, and never goes below 5. Test: counts [5, 6, 6, 7, 7, 7] of 200 give trail 6, 5, 3, 0 passes, so k = 8. Two tiles at 5 (FDR exactly 1 %) keep k = 5.
- **R**: axis-aligned, 4.00 cm^2 exactly (area checked to within +-1 %), aspect <= 2:1, px/mm = 1000 / voxel_um, with the voxel size read from `metadata.json` (`scan.tomo.acquisition.detector.samplePixelSize`, the same field as `hercules.pipeline.window`). The voxel size is never taken from anywhere else, and a missing metadata entry raises. Placement maximises the agreed discovery letters inside; tie-breaks are in PROPOSAL B10. The final placement is centred in its feasible range, which maximises the letter-to-edge margin. `sg_check` requires `R_declared {rect, record}` equal to the recomputed R (fail closed).
  - **Image independence** is tested four ways: the signature takes only namings, px/mm and canvas size; the module imports no image library (AST check); with `open`, `np.load`, `np.fromfile` and `cv2.imread` patched to raise, R is still computed; and the result is invariant to reader order, naming order and extra fields carrying pixel arrays.
  - **Optimality**: on 4 random sets, no one of 20,000 random valid placements enclosed more letters than R.
  - **Speed**: 200 agreed letters take 0.14 s.
- **SG 1**: only namings whose point lies in R are used, from exactly 3 confirmation readers, none of them a discovery reader.
  - (a) agreed >= 12, tested at 11 (fail) and 12 (pass);
  - (b) agreed letters with >= 2 firm members >= 8;
  - (c) >= 40 null tiles, p99 ("higher") margin >= 10 and agreed > null max, tested at margin 9 (fail) and 10 (pass);
  - (d) the identity shuffle on the confirmation reads in R with p < 1/(100 m), exact fractions. N = max(5000, 2000 m), so the smallest attainable p is always below the bar; too few permutations gives FAIL. An all-omicron text gives p = 1 (FAIL).
- **SG 2**: every batch needs canary score >= 0.70 x its REF ceiling (0.699 fails, 0.70 passes) and total blank namings <= 1. A failing batch gives FAIL with consequence VOID_AND_REREAD. The canary numbers come from the scorer; this code never opens a seal.
- **SG 3**: opposite-order namings in R <= 2 (3 fail, 2 pass).
- **SG 4**: both the -1 and +1 re-reads must re-confirm >= 80 % (17/21 passes, 16/21 fails). A wrong identity at the same place does not re-confirm.
- **SG 5**: different seed AND fold, `trained_on_this_scroll is False`, base only if USABLE, and >= 50 % reproduced (11/21 passes, 10/21 fails).
- **SG 6**: overlap >= 0.60 (0.59 fails), no neighbour contradiction (a missing flag counts as a veto), >= 50 % reproduced. `overlap_fraction(mask_R, mask_retrace)` is provided.
- **SG 7**: for every letter crop, 24 rotations about the centre (bilinear), compared on the inscribed disc, masked Pearson NCC at every valid placement in every label patch, all via FFT. The crop count must equal the number of SG letters. Any NCC >= 0.8 is a copy. A flat crop is not evaluable, which gives FAIL.
  - Validation: equal to brute force within 1e-10 at 5 angles. An exact copy gives NCC 1.0 at the right patch, angle and position. Rotated copies at 15, 45, 105, 180 and 345 deg are found at the right step with NCC >= 0.95 on smooth fields.
  - Speed: 21 letters x 24 rotations x 300 patches of 64x64 (151k correlation maps) take 17 s on 4 cores.
- **SG 9**: if trained on this scroll, NULL, REV and CTRL agreed letters in R are each <= 1; a missing arm fails. Otherwise NOT_APPLICABLE.
- **SG 11**: baselines are fitted to the agreed boxes (each the median of its members' boxes). Tests: 9.5 deg passes, 10.5 deg fails; heights 1.9 mm fail, 2.0 and 4.0 mm pass, 4.2 mm fails; pitch CV 0.28 fails, 0.087 passes; one row fails; scattered letters fail.
- **SG 13**: in the band, a 3-sealer seal via `make_seal` must confirm >= 50 % within 250 px (a 200 px shift passes, 300 px fails); otherwise FAIL with alarm. Outside the band, NOT_APPLICABLE.
- **SG 14 (rotation)**: the 2x3 display affine must be a pure rotation of |15| deg. Namings are mapped back to the canvas, and >= 50 % must be kept (10 deg fails; un-mapped namings fail). The RAW-F/B profile and unit-test parts are attestations.
- **Attested items (0, 8, 10, 12, 14 profile, 14 tests)**: each must carry a RULES.md record id. Without one the item is NOT_EVALUATED.
- **Overall**: PASS only if discovery, its calibration, R and items 0-14 are all PASS, NOT_APPLICABLE or ATTESTED_PASS. K7's owner-presence condition is not evaluated by code.

## 3. Measured numbers

- SG tests: **122 passed** (`tests/sib_sg_*.py`, 62 s). Full repository suite: **585 passed, 6 skipped**. The first full run had 11 collection errors because `tifffile` and `PIL` were missing from my freshly built venv. After installing the `setup_env.sh` package list it passed; both runs are logged.
- Synthetic known-answer run: overall PASS, all 15 items passing (`synthetic_pass_result.json`, sha256 in `runs.jsonl`). Every computed item also has a test in which it alone fails.
- **SG 7 null** (independent smoothed fields, so every flag is false; 8 crops per cell, 24 rotations):

| disc d px | sigma px | n_eff | patches | median max NCC | largest | false-flag fraction |
|---|---|---|---|---|---|---|
| 32 | 1 / 2 / 4 / 8 | 89 / 30 / 13 / 6 | 100 | 0.40 / 0.65 / 0.86 / 0.98 | 0.43 / 0.67 / 0.92 / 0.99 | 0 / 0 / 1 / 1 |
| 64 | 1 / 2 / 4 / 8 | 357 / 101 / 33 / 12 | 100 | 0.22 / 0.41 / 0.66 / 0.87 | 0.24 / 0.44 / 0.69 / 0.91 | 0 / 0 / 0 / 1 |
| 128 | 1 / 2 / 4 / 8 | 1430 / 358 / 109 / 31 | 100 | 0.12 / 0.23 / 0.41 / 0.66 | 0.14 / 0.25 / 0.48 / 0.71 | 0 |
| 64 | 2 / 4 | 111 / 31 | 1000 | 0.44 / 0.71 | 0.45 / 0.73 | 0 |

  n_eff is measured by code as disc area / autocorrelation half-max area. The chance maximum depends almost only on n_eff: at n_eff <= 13 every crop was falsely flagged, and at n_eff >= 30 none were. It grows with the number of patches (about +0.05 from 100 to 1000 at n_eff 31). **With a large training-label set or smooth ink maps, SG 7 can fail a genuine letter by chance.** The bar is unchanged. `copy_test` reports `n_eff_median` so the risk is visible.

## 4. Failures and deviations (all logged in `runs.jsonl`)

- My first sweep was stopped deliberately (exit 143) when I changed the n_eff definition. Its partial output was discarded and the sweep was rerun from scratch.
- Found and fixed during the build:
  - `hercules.scorer.canon.hash_json` returns canonical text, not a digest. The SG code hashes with sha256 over it.
  - The first R rule put letters on R's edge, and jitter then lost them. It now centres the set in its feasible range.
  - Two fail-open paths (an undeclared R; a partial crop set) now fail closed.
- Exact-boundary float round-off on inclusive bars is handled by a 1e-9 relative tolerance (PROPOSAL B15).

## 5. What the orchestrator needs to declare next

1. Rule on PROPOSAL-SG-CODE-1 B1-B15. The code implements the stricter reading everywhere: blank and opposite-order counts summed over readers, both slice offsets, identity required for SG 5, signed NCC, and DECL-EMPNULL's non-text *agreed* count rather than the brief's "F_B".
2. Hash the SG code into a METRIC-HASH entry before any candidate exists. The combined hashes are in `sg_report.json` under `code_hashes`, computed with `hercules.records.codehash`.
3. Before any SG attempt, define the training-label patch set and geometry (B7), and run the copy test on letter crops from >= 40 empirical-null tiles against it, with 0 false flags required for SG 7 to be informative. Record the result.

## 6. Exact commands

```
source /opt/hv/bin/activate
PYTHONPATH=src python -m pytest -q tests/sib_sg_gate.py tests/sib_sg_region.py tests/sib_sg_copytest.py tests/sib_sg_cli.py
python tools/sib/sg/sg_cli.py --synthetic --out logs/sib/sg/synthetic_pass_result.json
PYTHONPATH=src python tools/sib/sg/copytest_null.py --out logs/sib/sg/copytest_null.json
python tools/sib/sg/make_report_json.py
```
The tests must be named explicitly: `sib_sg_*.py` does not match pytest's default `test_*.py` pattern.
