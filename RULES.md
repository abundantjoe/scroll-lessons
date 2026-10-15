# RULES.md — declared tests, bars written BEFORE the run, results appended AFTER

A bar is never edited after a result. New tests are appended with their bar before their first run.
Every entry: id | what is measured | bar (written before) | reference | result (date, numbers, PASS/FAIL) | notes.

## Environment facts that constrain every test in this session (recorded 2026-09-16, before any run)
- No GPU. 4 CPU cores (Intel Xeon 2.10 GHz), 15 GB RAM, ~30 GB writable disk. Docker daemon started manually (overlay2, cgroup v1). Python 3.14.0rc2 venv; torch 2.14.0+cpu.
- Consequence declared now: CPU inference of the 9 µm model is slow. Any test run on a crop instead of the full canvas is labelled `-crop` and is a PARTIAL result, never a substitute for the full bar. The full-canvas bars stay as written.

## G-A  Gate A — w040 native stack (PHerc0139 segment 20250831000000-w040_2025083102, 9.362 µm stack 28×6400×7980) through 5.1
- Measure: pixel ROC AUC of forward map vs `w040_inklabels.zarr` level 0 slice 14 (>128 = ink) on pixels where `w040_supervision_mask.zarr` slice 14 > 0. Same for reverse map.
- Bar (before run): forward AUC >= 0.98 AND reverse AUC < 0.70.
- Reference (master prompt v4): forward 0.9966, reverse 0.4963 on 1,629,734 supervised px; forward mean on ink 0.758, on blank 0.252. Must reproduce within 0.01 or stop and diagnose; no target read before it does.
- Result 2026-09-17 (plain call, no TTA, CPU, seed42 step-075000, full 28×6400×7980 stack, 11,076 patches per direction, ~1.9 h per direction under contention): forward AUC **0.99659**, reverse **0.49633** on 1,629,734 supervised px; forward mean on ink 0.758, on blank 0.252. Reproduces the reference to 4 decimals. **PASS.** The TTA variant of the call on the full canvas is queued (G-A-tta below).

## G-A-crop  Gate A on the Gate-B crop of the NATIVE team stack (x 1152..3199, y 2048..4095), CPU fallback declared before any run
- Measure: same AUC on supervised pixels inside the crop. Reference for this crop through 5.1: forward 0.99681 (master prompt 5.3).
- Bar (before run): forward AUC >= 0.987 AND reverse AUC < 0.60. Passing this does NOT pass G-A; it is reported as partial.
- Result 2026-09-17 (native team stack crop, 961 patches per pass): plain forward **0.99680** / reverse 0.50301; `--tta-mirror` forward **0.99023** / reverse 0.56597 (means on ink/blank: plain 0.756/0.253, TTA 0.695/0.294). Identical to G-B Bar 2 on the rendered crop to 4 decimals, which confirms functionally that the rebuilt render and the team stack are the same input. PASS (partial by construction; G-A on the full canvas also PASSED).

## G-B  Gate B — renderer regression (vc_render_tifxyz, w040 mesh crop)
- Command (fixed): `vc_render_tifxyz --volume <cache> --remote-url s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/ --segmentation <w040 tifxyz> --zarr-output <out.zarr> --scale 1 --group-idx 0 --num-slices 28 --slice-step 1 --cache-gb 8 --voxel-size 9.362 --voxel-unit micrometer --flip-normals --crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048` (flags adjusted only if the current binary renames them; any adjustment is recorded here).
- Measure 1: per-slice Pearson r between the render and the team stack on the same crop (28 slices) and the fraction of byte-identical pixels.
- Bar 1 (before run): Pearson >= 0.999 on every slice. Reference: byte-identical (Pearson 1.000 all 28 slices).
- Measure 2: the render through 5.1, AUC as in G-A-crop.
- Bar 2 (before run): forward AUC >= 0.987 AND reverse < 0.60. Reference 0.99681 vs 0.99681 on the team stack.
- Standing regression: after ANY change to sampling or model input this crop must pass Bar 2, else revert.
- Pre-run note (2026-09-16, before the declared G-B run): the published image `ghcr.io/scrollprize/villa/volume-cartographer:edge` (= `main`, built 2026-05-13, villa 1e3f4c0) has no `--flip-normals` (added 2026-06-17) and its tracer has no remote normal-grid marker (added 2026-07-08). A 256×256 smoke render of the w040 mesh at the crop origin with that binary matched the team stack only with the slice order reversed and at Pearson 0.42–0.82 per slice (identical-pixel fraction 0.40), with no in-plane or half-slice shift explaining the difference. That binary is therefore NOT the validated renderer and is not used for any gate; the tools are rebuilt from villa HEAD (5ab585f) with `scripts/build_vc3d.sh`. G-B is run with the rebuilt binary and the command as written above.
- Result Bar 1, 2026-09-16: rebuilt `vc_render_tifxyz` (villa 5ab585f, builder image, `--flip-normals`, exact command; `--pyramid 0` added only to skip pyramid levels) vs the team stack on the 2048×2048 crop: Pearson min 0.999999 over the 28 slices, identical-pixel fraction min 0.9956, mean |diff| 0.0029 grey levels (not bit-exact: a different compiler/build; well inside the bar). **PASS.**
- Result Bar 2, 2026-09-17: the render through 5.1 on the crop's 582,314 supervised px: plain forward AUC **0.99680** (reference 0.99681), reverse 0.50265; with `--tta-mirror` forward **0.99024** (reference 'w040 regression 0.990'), reverse 0.56576. Means on ink/blank: plain 0.756/0.253, TTA 0.695/0.294. **PASS** (both forms). Note recorded, not a bar: TTA lowers this crop's AUC from 0.9968 to 0.9902 and pulls the means toward 0.5; the promotion record of 2026-09-12 rested on the w028 judge (+0.039), which J-w028 will re-measure here before TTA is used on any target.

## G-C  Gate C — w028 pooled stack (PHerc1667, 2.399 µm level 2 mean-pooled 4 planes -> 21 slices at ~9.596 µm) through 5.1
- Measure: AUC vs `pherc1667-w028_inklabels.zarr` slice 10 (>0 = ink) on `pherc1667-w028_supervision_mask.zarr` slice 10 > 0.
- Bar (before run): forward AUC >= 0.99 AND reverse < 0.60; must reproduce the reference within 0.01.
- Reference: forward 0.9998, reverse 0.531; forward mean on ink 0.772, blank 0.235. LEAK: w028 is in the training corpus; this AUC measures memorisation, not generalisation.
- Result 2026-09-17 (plain call, CPU, ~3 h per direction under contention): forward AUC **0.99982** on 844,786 supervised px (230,544 ink); mean on ink 0.772, on blank 0.234; reverse AUC **0.53058** (reference 0.531), mean on ink 0.275, on blank 0.269. **PASS** (reproduces the reference to 3 decimals). TTA variant queued (record only).

## J-w028  The judge — unlabelled text on w028 (calibration for every model/input variant)
- Reference map: the team's 2.4 µm w028 prediction (`...20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif`, 37420×30340) block-averaged 4×4 onto the pooled canvas (9355×7585) and divided by 255.
- Classes: text = reference >= 0.40; blank = reference <= 0.25; on-sheet only (pooled CT mid slice > 0); pixels within 60 px of any labelled letter (inklabels slice 10 > 0, dilated 60 px) excluded.
- Measure: pixel ROC AUC of the forward 9 µm map on those two classes; also the reverse map.
- Reference: seed42 plain 0.784, seed42 + `--tta-mirror` 0.823, reverse 0.49. seed43 plain 0.781 (retired).
- Promotion rule (frozen): a variant is promoted only if it raises this AUC by >= 0.01 over the current recipe (0.823) AND passes G-B Bar 2.
- Result 2026-09-17: reference built (`gates/w028_judge_ref`: on-sheet 58.0 M px, text 13.2 M, blank 40.1 M, 0.84 M excluded around labels). seed42 plain forward judge AUC **0.7842** (reference 0.784; mean on text 0.446, on blank 0.296); plain reverse **0.4902** (reference 0.49; text 0.286, blank 0.289). Both reproduce. The TTA maps (the current recipe, reference 0.823) are queued; until they are scored the recipe stands as promoted on 2026-09-12.

## R-5.5  Frozen candidate rule (SCREEN-POWER; never retuned)
- Unit: square of side round(sqrt(0.5)·10000/µm) px = 0.5 cm² (737 px at 9.596 µm, 819 at 8.64, 755 at 9.362). Valid if >= 90 % of pixels on-sheet (CT mid slice > 0).
- Flagged: forward mean >= 0.36 AND (forward − reverse) mean >= 0.08.
- Levels on w028 unlabelled text: forward 0.40, margin +0.12; blank papyrus 0.29, 0.00. Power: 1 cm² 9/9 text vs 0/11 blank; 0.5 cm² 22/24 vs 0/35.
- PROMISING CANDIDATE = >= 3 adjacent (4-connected) flagged units on one chart AND marks in rows at 2–4 mm letter height. BLANK = no flagged unit over >= 1.5 cm² of valid units. Whole-map mean is never a verdict. Also report 1 cm² units.
- Self-test bar (before run): the implementation must reproduce, on the w028 pooled map, >= 20/24 text units flagged and 0/35 blank units flagged at 0.5 cm² when the same text/blank unit definitions are used (text unit = unit mean of the judge reference >= 0.40 over >= 50 % of its pixels; blank = <= 0.25 over >= 90 %). If the counts differ materially the implementation, not the rule, is wrong.
- Result 2026-09-17 (`scripts/w028_rule55_selftest.py` on the plain seed42 maps, (0, 0) grid, 88 valid 0.5 cm² units on the pooled canvas): with the strict class definitions above only 5 text units and 8 blank units exist (the previous session's 24/35 used looser, unrecorded definitions); text flagged **5/5**, blank flagged **0/8**; unit means text fwd 0.433 / margin +0.149, blank fwd 0.283 / margin −0.005 (master prompt levels 0.40 / +0.12 and 0.29 / 0.00). At 1 cm²: text 2/2, blank 0/2. **PASS** on the fraction bar (100 % >= 83 %) and on zero blank flags; the unit counts differ from the prose and are recorded as such.

## T-2UM  2.4 µm model CPU cost on this box (measured 2026-09-17, `scripts/time_2um_model.py`, other jobs running)
- ResNet-152 3D encoder + 3D decoder, 130.4 M parameters, checkpoint load 145 s; one 62×256×256 tile: 9.1 s (batch 1), 9.3 s/tile (batch 4), output 64×64 per tile. A 5 cm² patch at 2.403 µm (~9441² px, tile 256, stride 128) = 5,329 tiles = **~14 h per depth order** on 4 cores, ~28 h for both orders, plus the w028 calibration crop (4 cm², ~11 h per order). RAM: the runner memory-maps the 64-slice render (~5.7 GB for 5 cm²) on a 15 GB box with no swap. Feasible only as a multi-day exclusive job that stops 9 µm coverage; on a GPU it is ~20 min per pass.

## R-CREST  Render-on-sheet test (declared 2026-09-17 06:40 UTC; applies to every read from now on)
- Provenance, stated plainly: this test was written AFTER the second PHerc0826 read (auto_grown_20260917033643746) came back BLANK with a per-slice on-sheet mean profile flat at 107–108 across all 28 slices (crest ratio 1.01) and a CT panel showing radial cross-cut layers, while the first read had a proper crest (35 → 112 → 66, ratio 3.19, crest slice 14). The thresholds were then taken from the CONTROLS, not from those charts: w040 team render crest ratio 1.76 (crest slice 12 of 28), w028 pooled 1.37 (crest slice 10 of 21). The test only discards verdicts (BLANK/NOT ESTABLISHED/candidate -> VOID); it can never create a candidate.
- Measure: per-slice mean of the render over on-sheet pixels (already recorded by 5.10); crest ratio = max/min; crest slice = argmax.
- Bar: crest ratio >= 1.20 AND crest slice within the central half of the stack (28 slices: 7..20; 21 slices: 5..15). Fail => verdict VOID ("render not centred on a sheet"), the ledger line carries VOID, and the patch counts as no coverage.
- Implementation: `read_chart.crest_check`; tests `test_flat_profile_render_is_void`, `test_crest_check_controls`.
- Result: applied retroactively to the two reads on record: auto_grown_20260917032202909 ratio 3.19 crest 14 PASS (verdict stays NOT ESTABLISHED); auto_grown_20260917033643746 ratio 1.01 FAIL -> VOID (correction line appended to LEDGER.md).

## B-2UM  2.4 µm route bar (CONTROL-2UM), written before any 2.4 µm run
- "Letter-sized marks (2–4 mm) in rows on the UNALTERED 2.4 µm map, present in one depth order and much weaker in the other, and confirmed by the team" = ink visible at 2.4 µm. Anything less = NOT ESTABLISHED.
- Calibration required first: the 2.4 µm model on a 4 cm² crop of the w028 2.399 µm surface volume (level 0, 64 slices around the sheet centre) must agree closely with the team's published w028 prediction of the same region (bar: pixel Pearson >= 0.9 on the crop and AUC >= 0.95 of our map against the team's map thresholded at 0.5). Record on-sheet mean and unit-rule levels on text vs blank as the 2.4 µm calibration.
- Scale-down declared 2026-09-17 (CPU box, T-2UM): the calibration crop is 1.0 cm² (4160² px at 2.399 µm, window y0=28080 x0=20800 of the w028 level-0 volume, chosen from the judge reference as the 1040²-pooled square with the highest text fraction, 63 %, fully on-sheet, no label-excluded pixel) instead of 4 cm², and the 62-layer window is the centred one, layers 23..85 of 109 (villa issue #1813), not 1..63. Runner: villa `optimized_inference` entrypoint, tile 256, stride 128, local checkpoint `r152_3ddec_v2_l5_epoch13.ckpt`, CPU, `scripts/run_2um.py`.
- Result, smoke (768² sub-window at offset (48, 64) of that crop, forward only, 25 tiles, 290 s): ours vs the team's published map on the same pixels (64-px border dropped): Pearson **0.934**, AUC of ours against team > 0.5 **0.979**; means 0.286 (ours) vs 0.265 (team). Meets the calibration bar on the smoke window. Full 1 cm² crop, both orders: running.
- **Result, full 1 cm² crop, forward (2026-09-17 23:35 UTC; 1024 tiles, 5 h 32 min on the contended CPU): PASS.** Ours vs the team's published map on the same 4032² pixels (64-px border dropped): Pearson **0.9996**, AUC of ours against team > 0.5 **0.9999**; means 0.5911 (ours) vs 0.5899 (team). Unit-rule levels (4×4-pooled, J-w028 thresholds): text (team ≥ 0.40, 64.2 % of the window) ours 0.8046 vs team 0.8033; blank (team ≤ 0.25, 26.2 %) ours 0.1674 vs team 0.1658. The runner reproduces the team's 2.4 µm inference to three decimals (`records/2um/w028_calib/compare_team_forward.json`, preview `review_sheets/2um/w028_calib_1cm2_forward_ours_vs_team_pooled4x4.png`). Reverse pass running.
- **Result, full 1 cm² crop, reverse (2026-09-18 04:05 UTC; 1024 tiles, 4 h 29 min): the depth asymmetry is present and large.** Our reverse map on the same pixels: mean **0.1877** against the team's forward map's 0.5899; over the team's text pixels our reverse level is **0.1997** against our forward 0.8046 (team 0.8033); over blank pixels 0.1633 against our forward 0.1674 (team 0.1658). Pearson against the team's FORWARD map drops to 0.141 and AUC to 0.551, which is the expected behaviour, not a failure: the reverse order must NOT reproduce a forward map. Reverse-order bar recorded in `scripts/compare_2um_calib.py --expect-weak` (our mean and our text level both below half the team's): PASS. Records: `records/2um/w028_calib/compare_team_{forward,reverse}.json`.
- **B-2UM calibration is therefore complete and passed in both depth orders.** The 2.4 µm route on this box reproduces the team's published inference to three decimals forward, and collapses to the blank level in reverse. What CONTROL-2UM still lacks is not the reader but the geometry: no sheet-following trace of the PHerc0846A rescan exists yet (0 of 14 traces; see R-CREST-CT / R-COVER above).

## R-CREST-CT  Crest pre-check in the CT for the 2.4 µm route (declared 2026-09-17 18:45 UTC, before any 2.4 µm render of a trace)
- Why: rendering 1 cm² of a trace at 2.403 µm costs ≥ 12,000 chunk fetches of 2 MB and the 62-layer inference ~3 h per depth order on this box; the render-based R-CREST would only be known after that. A trace that cross-cuts the sheets must be recognised before, in the CT itself.
- Measure (`scripts/ct_at_points.py`, tests in `scripts/tests/test_ct_at_points.py`): at every third valid grid cell of the tifxyz trace, the CT (one pyramid level, fetched chunk-wise) is sampled at the point and at ±half voxels along the local surface normal (cross product of the grid edge vectors); half = 300 µm / voxel size of that level (8 at 37.4 µm = level 2 of the 9.362 µm scans; 16 at 19.2 µm = level 3 of the 2.403 µm rescans). Mean profile over the cells; crest ratio = max over the central half of the offsets / mean of the three outermost offsets on each side.
- Bar: crest ratio ≥ 1.20 with the crest inside the central half (same numbers as R-CREST on the render) → the trace may be rendered at 2.4 µm. Otherwise VOID-CT: no render, no inference, a ledger line with the profile. The papyrus fraction at the points is recorded but is NOT a criterion (the team's surface predictions sit at the sheet boundary, so a valid trace can score near the base rate).
- Calibration on three PHerc0826 traces at level 2 of the 9.362 µm volume against their render-based crest: auto_grown_20260917163319741 (read, crest on the render 1.3+) → 1.350 at offset 0 PASS; auto_grown_20260917143012277 (read) → 1.369 at −1 PASS; auto_grown_20260917145105489 (VOID on the render, 1.01) → 1.026 VOID-CT. The CT check reproduces the render verdicts.
- Result on the first rescan trace, PHerc0846A auto_grown_20260917032753495 (L2 prediction, seed 1656 4168 1624 "inner", 5.23 cm², QC 5.8 PASS on geometry): crest ratio **1.043** at −1 (±16 voxels at level 3; 1.031 at ±8) → **VOID-CT**. Its points hit papyrus (above the region's Otsu threshold) in 62.7 % of the cells against a region base rate of 52.1 %, i.e. hardly better than random voxels. The 512² test render (64 slices, `--scale-segmentation 4`, crop (160,160)) confirmed the geometry mapping (output 64×512×512, 85 % non-zero) and showed the air level (median 38 ≈ f32 0 → 35 under the export window [−0.03, 0.19]). The trace is not rendered at 2.4 µm. Disclosure: this trace was measured before the bar text above was written (the render-based R-CREST numbers were simply transposed); no number of the bar was chosen from it.
- Consequence: the five remaining rescan seeds (2 outer, 3 middle) are traced on the L2 prediction and each trace must pass R-CREST-CT before the 1 cm² render (window = the 52×52-cell (4160 px) block with the most valid cells; 64 slices; `--scale-segmentation 4`; depth orders from the runner's FORCE_REVERSE).
- Refinement (2026-09-17 19:25 UTC, after the second rescan trace and before any 2.4 µm render): the crest must lie within ±4 voxels of the surface = the half-depth of the render window that follows (62 layers × 2.403 µm = ±75 µm = ±3.9 voxels at level 3; 28 slices × 9.36 µm = ±131 µm = ±3.5 voxels at level 2), instead of anywhere in the central half of the ±300 µm profile. Reason, disclosed: the trace of smoke seed 1816 5752 1544 (auto_grown_20260917190131466, QC PASS 5.10 cm²) gave ratio 1.448 with the "crest" at −8 voxels (−154 µm) on a profile that falls monotonically from 60 at −307 µm to 1 at +307 µm: it runs along the outside of the outermost wrap, the material lies ≥ 150 µm inward and a render centred on it would hold air. The plateau-safe crest offset (midpoint of the maximal offsets) is used. The three calibration verdicts are unchanged (offsets 0, −1 → PASS; 1.026 → VOID-CT); the first rescan trace reads 1.069 at +8 under the midpoint rule (VOID-CT either way).
- Seeds for the rescan are now CT-gated (`seeds/PHerc0846A_2um.json`, 36 seeds, level-5 CT > 0 eroded by 12 level-3 px, local prediction density ≤ 0.75); the smoke seeds 5544 1352 1544, 920 5848 1664 and 2960 1520 1704 lie outside the masked CT and are dropped (the first was traced: QC UNREADABLE, ct_zero 1.00).
- Superseded as the gate (2026-09-17 20:10 UTC): the level-3 CT profile (19.2 µm voxels, nearest-voxel samples) is too coarse for the thin, tightly packed wraps of the rescan. The gate for the 2.4 µm render is now the ESTABLISHED render bar R-CREST applied to a 28-slice render of the same trace at its own pitch (9.612 µm, pyramid level 2, `RENDER_GROUP=2 --scale-segmentation 4`, trilinear sampling, the exact 9 µm-route render): ratio ≥ 1.20 with the crest in the central half (`scripts/render_crest.py`, run by `scripts/precheck_2um.sh` on every QC-PASS trace; the render is deleted after the check, the profile is kept). R-CREST-CT stays recorded as a diagnostic. Results on the four QC-PASS rescan traces: auto_grown_20260917032753495 (inner) 1.029 flat → VOID; auto_grown_20260917190833513 (middle) 1.024 flat → VOID; auto_grown_20260917194403641 (outer) pending; **auto_grown_20260917190131466 (seed 1816 5752 1544) ratio 3.491, crest at slice 14 of 28 (dead centre), profile 18 → 64 → 48 → PASS**: the trace lies on the outermost wrap with void on one side and papyrus on the other; its CT-at-points profile had put the crest 150 µm inward (coarse sampling; an x/y swap test made every profile flat, so the sampling frame is right). It proceeds to the 2.4 µm render (window cells (67, 23), crop x 1840 y 5360, 4160 px, 64 slices) and the read in both depth orders; launched 20:05 UTC.
- **R-COVER (declared 2026-09-17 20:30 UTC, before any 2.4 µm inference)**: a crest alone does not prove a sheet; the 2.4 µm render of the window above was 69 % non-zero but only **28.6 %** of its pixels see papyrus in any of the 64 layers (max over layers > 60 on the 8-bit scale; air is 30–40 under both export windows, papyrus 80–130): the window is air and masked void with papyrus fragments (`review_sheets/2um/*render_layers*.png`). Reference: the w040 control segment (team mesh) scores 0.997 on the same measure. Bar: a 2.4 µm window is inferred only if its papyrus coverage is ≥ 0.80 (`scripts/render_cover.py`, JSON `render_cover_2um.json`); the 1 cm² window is chosen on the level-2 check render (no auto-crop, one grid cell = 20 px) by maximum per-cell coverage (`window_2um.py`), and a trace whose best window is below 0.80 is VOID-COVER without a 2.4 µm render. Applied to auto_grown_20260917190131466: the inference was stopped after 0 tiles (no 2 µm map exists for it); verdict VOID-COVER. Disclosure: written after seeing that render and before any model output on it; the bar copies the 90 % on-sheet requirement of rule 5.5 in spirit, relaxed to 80 % for the coverage over layers.

## P-DRY  Packager + verifier dry run on w040 (day 0)
- Bar (before run): every file-derived check passes (area 4.00 ± 1 %, bar = 10000/µm ± 1 px, forward window byte-identical to the source TIFF, both orders present, mesh present + SHA-256 + flattened flag, held-out text and method present, image named after the mesh) and the verifier fails on exactly two checks: "not eligible" (PHerc0139 is not on the list) and "fewer than 10 letters" (an empty letter list is supplied).
- Result 2026-09-17: package `packages/DRYRUN_PHerc0139_w040/` built from the full w040 plain maps (window 2136×2136 px at (2000, 1500), 3.9989 cm²), the w040 team mesh (flag recorded as 'team mesh (dry run only)'), empty letter list. Verifier: 20 PASS (area, byte-identity with source SHA-256, both orders, mesh hashes, flattened flag, image named after mesh, 1 cm bar = 1068 px in all four PNGs, PNG map pixels equal the TIFF windows, rows.png untouched outside baselines, ct_window equals the render slice, held-out and method present, call recorded) and exactly 2 FAIL: '>= 10 letters' and 'scroll eligible'. **PASS.**

## R-CREST bar validation (measured 2026-09-18 06:00 UTC over the 59 charts on record; the bar is NOT changed)
- Concern: R-CREST (crest ratio >= 1.20 in the central half of the render) is our own pre-check, not a master-prompt bar, and a bar set too high would silently discard readable surface on tightly packed scrolls - exactly where letters would be hardest to reach.
- Measured crest ratio over every chart on record: charts that produced a read (BLANK / NOT ESTABLISHED) run **1.23 to 3.19**; charts called VOID run **1.00 to 1.12**, plus one at 1.77 rejected on crest POSITION rather than ratio. No chart anywhere lies between 1.12 and 1.23: the two populations are separated by an empty gap, and the 1.20 bar sits inside it.
- Sixteen of the 34 VOID charts have a CENTRED crest (within 3 slices of the middle) yet ratios of only 1.01-1.09, five of them PHerc1203 team surfaces. A centred but flat profile is therefore a distinct population, not a weak version of an on-sheet one.
- Conclusion: R-CREST discards nothing this reader could read; the bar stands unchanged and no verdict on record is altered. Recorded as a validation, not a revision.

## Model depth window (measured 2026-09-18 06:10 UTC; no bar changes)
- The 9 µm model consumes exactly 17 slices (`configs/aligned21_hybrid_3d2d.json`, `patch_size [17,128,128]`), and `center_crop_layer_indices` (external/villa/vesuvius/src/vesuvius/ink_detection/inference/infer.py:200) crops a 28-slice render to indices 6..22: slices 0-5 and 23-27 never reach the network.
- Over all 53 charts then on record, every non-VOID read has its crest at slice 11-16 (median |crest-12| = 2, max 4), inside that window and within the jitter of where both controls sit. The low forward-minus-reverse margins are therefore NOT a windowing artefact, and no re-render at a depth offset is warranted. The charts with crests at 0, 1, 4, 23, 25 and 27 are exactly the ones R-CREST already called VOID.


## QC CT-mask proxy on published renders (declared 2026-09-18 06:40 UTC, before any read it enables)
- QC 5.8 calls a patch UNREADABLE when more than half of 100 points sampled on the level-4 CT mask are zero. At 8.64 µm, level 4 is a 138 µm voxel, so that mask is a coarse proxy for "is this surface inside the scanned material".
- On the surfaces the team published for PHerc1447 it rejects most of the curated set (zero_frac 0.42-0.86 across 13 surfaces, where 0.50 is the bar), including surfaces the team themselves rendered and published. Part of the cause is known: some of those surfaces run past the top of the volume, so their outer region samples empty mask.
- Where a published surface volume exists (`render_source.json` in the patch dir), that render is the ground truth of what lies inside the volume: it is the team's own render of that surface, and Gate B established our renderer reproduces such stacks pixel for pixel. Rule 5.5 then requires >= 90 % on-sheet pixels inside a 0.5 cm² unit before that unit counts at all, and R-CREST still has to pass on the render.
- Therefore, for patches with a published render only, the CT-mask proxy is superseded: the read proceeds and the measured zero_frac is recorded in the read's stats and in the ledger note. Nothing else changes - geometry FAIL still stops a patch, R-CREST still stops a flat render, and no rule 5.5 threshold or verdict definition is touched. Patches without a published render are unaffected.
- Disclosure: this was written after seeing the QC verdicts on those 13 surfaces and before any of them was read.

## Gate C and J-w028 under TTA (completed 2026-09-18 08:41 UTC, 21 h of CPU; results appended, no bar edited)
- **J-w028 judge, TTA: forward AUC 0.8224** against the published reference of **0.823**; text mean 0.4498, blank 0.2989, margin +0.1509. Reverse AUC 0.4843 (text 0.2860, blank 0.2910, margin -0.0050). The plain pass reproduced 0.7842 against its reference 0.784. Both published judge numbers are therefore reproduced on this box to three decimals.
- **Gate C labels AUC, TTA: forward 0.99955** (ink 0.7513, blank 0.2492) and reverse 0.53485, against plain 0.99982 (ink 0.7716, blank 0.2344) and 0.53058. `records`: `gates/gateC/auc_tta_{forward,reverse}.json`.
- **R-5.5 self-test on the TTA maps: PASS.** At 0.5 cm² over 88 valid units: text flagged 5/5, blank flagged 0/8; text forward 0.4392 with margin +0.1567, blank forward 0.2837 with margin -0.0090. At 1 cm²: text 2/2, blank 0/2. The plain maps gave 5/5 and 0/8 with text 0.4328 / +0.1492 and blank 0.2832 / -0.0055. The frozen levels (0.36 forward, +0.08 margin) separate text from blank under BOTH recipes, so a unit that flags plain also flags under TTA and the plain screening recipe loses no sensitivity at the bar.
- Reproducibility fix found while scoring: the w028 ink labels are 0/1, not 0/255, so `score_auc.py --ink-thr` must be 0 for them; the default of 128 silently yields zero ink pixels and a null AUC. The stored plain results were produced with `--ink-thr 0` but did not record it; the script now writes `ink_thr` into its JSON. No stored number changed.

## Gate A full-canvas TTA: NOT RUN, and why (decided 2026-09-18 11:22 UTC after 2 h 36 min of it)
- Gate A passed on the full w040 canvas with the plain call (forward AUC 0.99659 / reverse 0.49633); the TTA variant passed on the 2048² crop (G-A-crop: plain 0.99680, TTA 0.99023); and Gate C reproduced BOTH published judge numbers, plain 0.7842 against 0.784 and TTA 0.8224 against 0.823. A full-canvas TTA pass would confirm a recipe already confirmed twice, and no decision hangs on its value.
- It was consuming a core at nice 19 for 2 h 36 min while the coverage reads, the only thing that can find letters, waited for CPU. It was stopped with no result recorded, and `gates/gateA/.tta_not_run` says the same on disk. Nothing already run is discarded and no bar is changed: this is a gate we chose not to finish, recorded as such rather than left looking complete.

## Reading recipe: screening reads are plain, TTA only on candidates (declared 2026-09-18 00:05 UTC, before the first plain read)
- The R-5.5 self-test that validates the frozen levels (0.36 / +0.08) was run on the PLAIN seed42 maps of w028; the TTA (`--tta-mirror`) maps of the controls are not scored yet (Gate C TTA is still running) and TTA changes the map levels (judge reference 0.784 plain vs 0.823 TTA). The 31 reads on record used TTA; none produced a flagged cluster, and every VOID/BLANK/NOT ESTABLISHED verdict rests on either the crest check or on levels far below the bar, so they stand as recorded.
- From now on the screening read of every patch is the plain call (`--direction both`, no `--tta-mirror`; ledger tag `ink9um_seed42+plain`), the call the levels were validated on, at a quarter of the inference cost (throughput on this 4-core box: ~1 read per hour with TTA under the current load). A PROMISING CANDIDATE is then also read with TTA (protocol 9 needs both maps anyway) and the TTA read gets its own ledger line. A patch already read under one tag is not read again by the screening loop (`--reread` for a deliberate second read).
- This changes the recipe, not a bar: the unit levels, the tiling, the crest rule and the verdict rules are untouched.

## Implementation note on R-5.5 unit tiling (recorded 2026-09-17 07:58 UTC, after 3 on-sheet reads at the (0, 0) grid)
- The master prompt fixes the unit SIZE and the validity/flag THRESHOLDS but not where the grid is anchored; the first implementation tiled from (0, 0). On the fragmented renders of PHerc0826 that left 1 valid 0.5 cm² unit out of 3.3 and 2.5 cm² on sheet, so verdicts came back NOT ESTABLISHED for lack of units, not for lack of evidence.
- From now on the grid origin is chosen from the ON-SHEET MASK ONLY (`rule55.best_origin`: the offset in [0, side) on an 8×8 lattice that maximises the number of valid units; ties to (0, 0)); the maps are never consulted for the choice, so it cannot bias which units get flagged. Every read also records the (0, 0)-grid numbers (`rule55_fixed_origin`) so both are on record, and saves its on-sheet mask (`onsheet_mask.png`). Thresholds, unit sizes, cluster rule and BLANK area are unchanged. The three reads already on record stay as ledgered (their renders were deleted; masks were not yet saved).
- Combination rule (added 2026-09-17 09:00 UTC after the fourth read, auto_grown_20260917051857791, came back BLANK on the mask-origin grid while the (0, 0) grid flagged one unit with fwd 0.50 / margin +0.086): the verdict is the CONSERVATIVE combination of the two tilings. Any flagged unit on either grid rules out BLANK (-> NOT ESTABLISHED); a >= 3-unit 4-connected cluster on either grid is a PROMISING CANDIDATE; BLANK requires no flagged unit on both grids and >= 1.5 cm² of valid units. A grid placement can therefore never dismiss a flag. That read's ledger line is corrected to NOT ESTABLISHED. Narrowed 2026-09-17 12:30 UTC after read 7 (auto_grown_20260917100345246): only FLAGS and CLUSTERS carry over from the (0, 0) grid; a (0, 0)-grid NOT ESTABLISHED that comes only from too few valid units does not override a BLANK on the mask-origin grid (the valid-unit count belongs to that grid). Read 7 corrected to BLANK.

## Arithmetic note on R-5.5 (recorded 2026-09-16 before any read): sqrt(0.5)·10000/8.64 = 818.41, so the formula gives 818 px at 8.64 µm, not the 819 written in the master prompt's prose; the formula is the rule and the implementation uses 818 (the other two pitches agree: 737, 755). This is a documented transcription correction, not a retune.

## T-CPU  CPU throughput record (not a pass/fail bar; recorded so every later time estimate is measured, not guessed)
- Measure: seconds per 128×128×17 patch batch for the 9 µm model on this box, single direction, no TTA and with `--tta-mirror`; projected wall time for w040 full (6400×7980), the 2048² crop, and w028 pooled (9355×7585).
- Result 2026-09-16 (512×512 crop of the w040 stack at (1152, 2048), 49 patches, 4 cores, other jobs running): forward plain 16 s wall including model load (~0.2 s/patch); `--direction both --tta-mirror` 61 s (4 mirror variants in y/x; depth is NOT mirrored: `compute_equal_length_mirror_axes` excludes the 17-slice axis). Projection: w040 full = 11,076 patches -> plain both ≈ 1.3 h, TTA both ≈ 4–5 h; w028 pooled ≈ 1.5× that. Sanity on that crop (15k supervised px, not a gate): plain forward AUC 0.986; TTA forward 0.875, TTA reverse 0.579 — the TTA drop on this small crop is unexplained and is exactly what G-A / G-A-crop must settle before TTA is used on any target.

## Seeds (5.6) candidate gate (recorded 2026-09-16, before the first full seed run)
- Seed candidates restricted to predicted voxels whose level-4 CT value > 0 (5.8 mask criterion); reason: the level-3 surface prediction carries a rim outside the masked CT that otherwise captures the outer/middle farthest-first picks (PHerc0306B smoke: 7 of 12 seeds off-CT before the gate).

## Seeds density gate (declared 2026-09-18 01:00 UTC, before the next seed run; calibrated on the traces so far)
- Observation on the 53 traced seeds of PHerc0826 and PHerc0358 with an outcome: the level-3 surface-prediction density in a 31 px (2.9 mm) window around the seed separates sheet-following traces from cross-cutting ones. Every one of the 15 traces that produced a read (BLANK / NOT ESTABLISHED) sits at density ≤ 0.20 (median 0.105); 16 of the 23 VOID traces (flat crest) sit above 0.20 (median 0.224, up to 0.36), the remaining 7 between 0.05 and 0.17. QC-UNREADABLE traces (off the CT) sit below 0.11 at the scroll edge and are caught by the CT gate.
- Gate: seed candidates must have density ≤ 0.20 in the 31 px window (`seeds.py --max-density 0.20 --density-window 31`), on top of the CT gate; seeds are ordered outer → middle → inner. Applied to PHerc0358 (regenerated, previous file kept as `seeds/PHerc0358_v1_nodensity.json`) and to every later scroll. Expected effect from the calibration: about two thirds of the cross-cutting traces avoided at the cost of at most one read in fifteen. This gates where the tracer is started, not what is read or how; no bar changes.
- **Result, measured 2026-09-18 10:00 UTC on PHerc0358 (the only scroll traced both before and after the gate): the gate works.** Ten traces from the ungated seeds gave 1 readable chart, 8 VOID and 1 QC rejection (10 % readable, 80 % VOID). Seventeen traces from the density-gated seeds gave 10 readable charts (5 BLANK, 5 NOT ESTABLISHED), 1 VOID and 6 QC rejections (**59 % readable, 6 % VOID**). Cost, stated plainly: the QC rejection rate rose from 10 % to 35 %, because sparser prediction neighbourhoods sit nearer the scroll edge where the level-4 CT mask thins out. Net, the readable fraction is about six times higher for the same tracer time, and no verdict rule was involved in the comparison.

## QC CT-mask bar: an in-mask AREA arm beside the zero-fraction arm (declared 2026-09-18 13:45 UTC, before any read it enables)
- Concern: QC 5.8 stops a patch when more than half of 100 points sampled on the level-4 CT mask are zero (`ct_zero_frac_max` 0.50). Unlike R-CREST, that bar has never been shown to sit in a gap. It is a RENDER-COST heuristic, not a verdict bar: nothing downstream depends on it, because the read itself takes its on-sheet mask from the CT mid slice of the render (`> 0`), rule 5.5 counts a 0.5 cm² unit only when >= 90 % of its pixels are on-sheet, and BLANK needs >= 1.5 cm² of valid units. A surface that is half outside the mask therefore cannot smuggle off-mask pixels into a verdict; it can only waste a render.
- **Measured, over all 151 QC'd patches** (histogram of `ct.zero_frac`, 0.1 bins): 67, 1, 13, 18, 14 | 18, 5, 8, 5, 2. The distribution is a CONTINUUM across 0.2-0.9 with no gap anywhere near the bar: 14 patches pass at 0.40-0.50 and 18 are stopped at 0.50-0.60. This is the opposite of the R-CREST validation, where the two populations were separated by an empty band. A bar drawn inside a dense continuum discards canvas for no physical reason.
- **Change (a strict widening; no existing bar is moved or loosened):** a patch proceeds when `zero_frac <= 0.50` **OR** `(1 - zero_frac) * area_cm2 >= 1.5`. The second arm is the estimated in-mask area of the surface — the area that can actually carry valid units — and 1.5 cm² is exactly the area rule 5.5 already requires before it will call anything BLANK. Below it a patch cannot reach any verdict but NOT ESTABLISHED, so rendering it genuinely is not worth the CPU. Every patch readable before stays readable (the first arm is untouched); 20 traces and 4 published PHerc1447 surfaces become readable.
- Recorded in `qc.json` as `ct.in_mask_cm2` and `ct.arm` (`zero_frac` or `in_mask_area`), and every ledger line for a read enabled by the second arm carries the note `qc in-mask area arm`, so the corpus can be re-partitioned later by which arm admitted a patch.
- **Validation method, decided before the runs:** for the patches this arm admits, compare the QC's estimate `(1 - zero_frac) * area_cm2` against the on-sheet area the render actually measures (`onsheet_cm2` in the read's stats). If the renders systematically come back with far less on-sheet area than estimated, the arm is admitting surfaces that cannot be read and the result is recorded here as a falsification, with the arm withdrawn. Target stated in advance: median `onsheet_cm2 / in_mask_cm2 >= 0.5` over the admitted patches.
- Disclosure: the histogram and the per-patch in-mask areas were seen before this was written. No verdict rule, no rule 5.5 threshold, no R-CREST bar and no already-recorded verdict is touched; this widens what gets read, and everything a read must clear is unchanged.

## The corpus margin is not a pipeline artefact: end-to-end margin on OUR OWN render (recorded 2026-09-18 13:50 UTC from stored Gate B results; no bar changes)
- Question the corpus forces: across the 37 on-sheet reads on record the forward level is TEXT-like (median 0.394 plain / 0.403 TTA, against the w028 control's text 0.4328 and blank 0.2832) while the forward-minus-reverse margin is BLANK-like (median +0.002 plain / +0.020 TTA, against text +0.1492 and blank -0.0055). Either these surfaces carry no ink, or something in our own render path destroys the depth asymmetry the rule 5.5 margin depends on.
- The stored Gate B results answer it without a new run. Gate B rendered the w040 mesh crop with OUR rebuilt `vc_render_tifxyz` and read that render, not the team's stack, through the plain 5.1 call (`gates/gateB/auc_render_plain{,_reverse}.json`, 582 314 supervised pixels):
  - forward: mean on ink **0.7561**, on blank **0.2527**  (AUC 0.99680)
  - reverse: mean on ink **0.2880**, on blank **0.2919**  (AUC 0.50265)
  - **margin on ink pixels +0.4681; on blank pixels -0.0039.**
- So our own render of a surface that carries ink yields a per-pixel ink margin of +0.47, and a blank margin indistinguishable from zero. A 0.5 cm² unit whose area is ~17 % covered by ink strokes already clears the frozen +0.08 margin bar; the bar is therefore roughly a sixth of the signal a fully inked pixel gives, not a level only a perfect surface could reach.
- Conclusion, stated as a physical result and not as a bar change: on the surface read so far the low margins are **evidence of absence of ink at this resolution, not absence of evidence**. The chain trace -> our render -> 5.1 -> rule 5.5 preserves the asymmetry it is built on. Nothing about R-5.5, R-CREST or the reading recipe changes; what changes is the priority, which is AREA and BREADTH (more scrolls), because the reader is demonstrably not the limiting factor.

## R-CREST-POWER  Does R-CREST have discriminating power on low-contrast volumes? (experiment declared 2026-09-18 14:05 UTC, before any read it produces; decision rule fixed here, before the data)
- Concern, and why it is serious: R-CREST was calibrated on two controls from volumes with visible layer separation (w040 ratio 1.76, w028 1.37). On the volumes the TEAM curates and publishes it rejects almost everything: PHerc1203 21 of 22 surfaces VOID at ratios 1.03-1.20, PHerc1447 28 of 32 VOID at 1.00-1.02 — including eleven surfaces rendered by the team THEMSELVES and published as 31-slice surface volumes. A curated, flattened, published reading surface that cuts through solid material is not credible in those numbers. The likelier reading is that on tightly compressed wraps the papyrus-to-gap density contrast that R-CREST measures is simply absent, so the test has no power there and vetoes every surface before the ink model ever sees it. The earlier "R-CREST bar validation" does not answer this: it showed two separated populations, but the readable population was defined by the bar itself, so it could not detect canvas the bar was discarding.
- **Experiment.** Read VOID-called surfaces through the same frozen pipeline with the crest veto disabled (`run_patch_dir.py --ignore-crest`, tag `ink9um_seed42+plain+nocrest`, its own ledger key, note `R-CREST-POWER`). Everything else is untouched: same checkpoint, same plain call, both depth orders, same rule 5.5, same thresholds, same QC.
- **Population, chosen map-blind and fixed now:** phase 1 = the 12 VOID surfaces of PHerc1203 and PHerc1447 with the largest on-sheet area (the team's own curated surfaces; ties broken by patch name). Phase 2 = every remaining VOID surface on those two volumes, run only if phase 1 flags anything or once the coverage queue is idle.
- **Decision rule, fixed before the data:**
  - If **no** phase-1 surface produces a flagged 0.5 cm² unit AND the forward/margin distribution over them is within the BLANK population already on record (median margin within +-0.02 of the BLANK median and no unit at or above the frozen 0.36/+0.08 bar), R-CREST is confirmed to discard nothing this reader could read on low-contrast volumes, and it stays exactly as it is.
  - If **any** phase-1 surface produces a flagged unit, R-CREST stops being a blocking veto on any volume whose VOID population sits below ratio 1.20 with a CENTRED crest (that is, where the test has no dynamic range); it remains recorded as a statistic on every read, and every VOID read on such a volume is re-read with the veto off. No rule 5.5 threshold changes either way.
  - If a phase-1 surface produces a PROMISING CANDIDATE, protocol 9 starts on it immediately, exactly as for any other candidate.
- No verdict already in the ledger is edited. The VOID lines stand; the new reads are additional lines under a different key, and both stay on record so the corpus can be split by which gate admitted a read.
- Cost stated in advance: ~15 min of CPU per plain read on this box, so phase 1 is ~3 h of one core, run at a nice level below the coverage loops.

## G-B-43  A second, independently seeded reader (bar written 2026-09-18 14:15 UTC, BEFORE the run)
- Why: the 9 µm release ships two checkpoints trained from different initialisations, `hybrid_3d2d-seed42` and `hybrid_3d2d-seed43`; only seed42 has ever been run here. Two independently seeded networks agree on ink and disagree on texture and noise, so a second reader is the cheapest specificity check there is, and any candidate this project ever submits must survive one.
- **Role, fixed before the numbers:** seed43 is CONFIRMATORY only. It never flags a unit by itself, never un-flags one, and no rule 5.5 threshold, screening tag or verdict depends on it. It is run on candidates (protocol 9) and on controls, alongside seed42, and both maps go on record.
- **Bar to be admitted as a confirmatory reader** — on the Gate B render (our own render of the w040 mesh crop, 2048², 582 314 supervised label pixels), plain call, both depth orders:
  - forward AUC against the w040 ink labels **>= 0.95**, and
  - forward-minus-reverse mean on LABELLED INK pixels **>= +0.30**, and
  - forward-minus-reverse mean on LABELLED BLANK pixels **<= +0.05**.
  (seed42 on the same render: AUC 0.99680, ink margin +0.4681, blank margin -0.0039.)
- If seed43 misses any of the three, it is recorded as not admitted and is not used for confirmation; nothing else changes. If it passes, every PROMISING CANDIDATE is additionally read with it and the agreement is reported with the claim.

## R-FLIP  Depth-order tripwire: would a flipped surface hide a real detection? (declared 2026-09-18 14:30 UTC, before the code that records it)
- The risk: rule 5.5 flags on a SIGNED margin, forward minus reverse. "Forward" means the depth order that matches the model's training convention, and that is a property of the SURFACE's normal, not of the reader. The team's meshes (w040, w028) carry a consistent orientation, but `vc_grow_seg_from_seed` picks the normal direction of a grown patch by its own growth, so a trace can come out mirrored. A mirrored surface that carried ink would put its whole signal in the map we label "reverse", with a large NEGATIVE margin, and rule 5.5 would never flag it.
- **Has this already cost a detection? No, and that is measured, not assumed.** Over the 37 on-sheet reads on record the most negative forward-minus-reverse mean is **-0.0366** (TTA) and **-0.0263** (plain). A mirrored surface carrying ink would sit at about -0.15, the mirror image of the w028 control's text margin of +0.1492, and at worst below the -0.08 mirror of the frozen bar. Nothing on record is within a factor of two of that. No read has been missed by the sign.
- **Tripwire, from now on, as a recorded statistic and nothing more:** every read also evaluates rule 5.5 on the SWAPPED pair (reverse as forward) and stores it as `rule55_depth_swapped`, with `depth_swap_tripwire` true when that swapped evaluation would flag at least one unit. This never changes a verdict, never creates a candidate and never alters a threshold — the ledger verdict stays the signed rule exactly as frozen.
- **What a firing tripwire obliges:** check that surface's orientation in the geometry (the sign of the grid normal against the local outward radial direction of the scroll, measured the same way on the w040 mesh, whose orientation is the convention the model was trained on). If the surface is genuinely mirrored, it is RE-READ as a new read with its own ledger key and a `+flip` tag, and that read is judged by the frozen rule in its correct orientation. If the geometry says the surface is not mirrored, the firing is recorded as a negative-margin artefact and nothing follows.

## R-NORMAL  The published sheet-normal field as a geometry test (declared 2026-09-18 14:10 UTC, BEFORE any measurement)
- What was found: 14 of the 23 eligible volumes publish a `representations/predictions/lasagna/` product that is NOT a surface probability. It carries `cos` (a winding-phase field, CT level 1), `grad_mag`, and **`nx`, `ny` — the sheet normal components, CT level 2, uint8** (`<scroll>.lasagna.json`, `base_shape_zyx` = the CT level-0 shape). Three volumes also publish an `umbilicus` polyline (the scroll axis). None of this has been used here before.
- Why it matters: R-CREST tests geometry through DENSITY CONTRAST, which compressed wraps do not have (see R-CREST-POWER). A normal field tests geometry through ORIENTATION, which does not depend on an air gap at all. If it works, it is the geometry gate that compressed volumes need, and it is the team's own model, not ours.
- **Self-test first, and it gates everything after it:** decode the uint8 as `n = u / 127.5 - 1` and measure `nx² + ny²` over occupied voxels. A sheet normal in a scroll winding about z is essentially in-plane, so the median must lie in **[0.9, 1.1]**. Outside that band the decoding is not understood, and the experiment stops there and is recorded as such — no result from a field we cannot read is used for anything.
- **Statistic:** for each valid grid cell of a trace, the trace's own surface normal from the tifxyz grid (cross product of the two grid edge vectors), projected on xy and normalised, against the published (nx, ny) at the nearest level-2 voxel. Report `|cos θ|` (absolute, because the two sign conventions need not agree), its median and the fraction of cells at `|cos θ| >= 0.9`.
- **Calibration population and bar, fixed before the numbers:** PHerc0826, where R-CREST demonstrably works (its traces span crest 1.00 to 3.19). Group A = traces whose render crest ratio is >= 2.0; group B = traces called VOID at crest <= 1.05. R-NORMAL has discriminating power only if **median |cos θ| >= 0.85 in group A AND <= 0.60 in group B, with the two interquartile ranges not overlapping.**
- **If it passes**, it is measured on the PHerc1203 and PHerc1447 surfaces that R-CREST calls VOID — the ones R-CREST-POWER is reading — and reported with them, as an INDEPENDENT geometric statement about whether those surfaces follow sheets. It becomes a recorded statistic on every trace. It does not by itself veto or admit any read, and it changes no rule 5.5 threshold or verdict; any future use as a gate would be declared here first, before it was used.
- **If it fails**, it is recorded as not usable and nothing changes. Either way the numbers go in this file.

## R-PHASE  Sheet seam consistency from the published winding-phase field (declared 2026-09-18 14:15 UTC, BEFORE any measurement of it)
- Written after seeing the first R-NORMAL numbers and before any `cos` value is read. Those numbers (recorded below when the run finishes) show group B — traces R-CREST calls VOID at crest ~1.00 — with normals that AGREE closely with the team's published sheet-normal field. If that holds, the two candidate explanations are: (a) those traces really do follow sheets and the render crest measures something else, or (b) a trace can be locally TANGENT to the sheets everywhere and still step from one wrap to the next, which would flatten a render's per-slice profile while leaving every local normal correctly aligned.
- (b) is the physically specific one and it is directly testable, because the same lasagna product publishes `cos`, a WINDING-PHASE field at CT level 1. A surface that stays on one sheet samples a narrow band of phase; a surface that steps across wraps samples the whole range. This is sheet seam consistency measured in the volume, not inferred from a render.
- **Statistic:** sample `cos` (decoded `c = u / 127.5 - 1`, the same encoding R-NORMAL's self-test establishes) at every `every`-th valid grid cell of a trace. Report the median, the interquartile range, the standard deviation, and `frac_within_0p2_of_median`. A one-sheet surface is a narrow distribution; a wrap-stepping surface is a broad one.
- **Self-test, same form as R-NORMAL's and decided once from the pooled sample:** the decoded values must fill roughly [-1, 1] over a scroll's occupied voxels (pooled p05 <= -0.5 and pooled p95 >= 0.5). If they do not, the encoding is not understood and no phase result is used.
- **Bar, fixed before the numbers:** R-PHASE separates the two R-CREST classes on PHerc0826 only if the median IQR of group A (crest >= 2.0) is **below half** the median IQR of group B (VOID at crest <= 1.05), with the two groups' IQR ranges not overlapping. Anything less and it is recorded as not a discriminator, exactly like R-NORMAL under its own bar.
- Whatever the outcome, this vetoes nothing and changes no rule 5.5 threshold or verdict. It is a geometric statistic, reported with R-CREST-POWER's ink evidence so that the question "do these surfaces follow one sheet?" is answered by the volume rather than by a render's contrast.

### R-NORMAL result (measured 2026-09-18 14:20 UTC on PHerc0826; the bar is NOT changed)
- **Decoding self-test: PASS.** Pooled over the 15 calibration traces, 39 491 occupied voxels, median `nx² + ny²` = **0.9093**, inside the declared [0.9, 1.1]. The published field is an in-plane sheet normal and `n = u / 127.5 - 1` reads it. Records: `records/rnormal/`.
- **R-NORMAL by |cos θ| FAILS its declared bar and is NOT a discriminator between R-CREST's classes.** Group A (crest >= 2.0, n = 6): median **0.9981**, IQR [0.9980, 0.9985]. Group B (VOID at crest <= 1.05, n = 9): median **0.9887**, IQR [0.9848, 0.9888], minimum 0.9778. The bar required group B at or below 0.60; it is at 0.99. The two IQRs do not overlap, but that was only half of a conjunction and the other half is missed by a wide margin, so the bar fails as written and nothing is retuned.
- What that means physically, stated as an observation and not as a rescue of the test: the traces R-CREST calls VOID are **locally tangent to the sheets everywhere they were sampled**. A trace that genuinely cut ACROSS the sheet stack would have its own normal nearly perpendicular to the sheet normal, |cos θ| near 0. These are at 0.99. So whatever makes their renders flat, it is not that they are driving through the wraps at an angle. R-PHASE (declared above, before this was known) tests the remaining explanation: a surface that is locally tangent everywhere and still steps from one wrap to the next.

### Incidental observation from the same run, and what is NOT being done with it (recorded 2026-09-18 14:20 UTC)
- Found AFTER looking at the data, therefore not a bar and not used for anything yet: the per-trace median of `nx² + ny²` — the LENGTH of the published normal, which behaves as the team model's own confidence in the sheet orientation — separates the two groups without overlap. Group A: 0.970, 0.970, 0.970, 0.970, 0.974, 0.979. Group B: 0.554, 0.754, 0.760, 0.771, 0.778, 0.796, 0.842, 0.869, 0.922. Every A trace is >= 0.970 and every B trace <= 0.922.
- If that holds out of sample it is an independent corroboration of R-CREST from a completely different signal — the team's own model confidence rather than density contrast — and it would work on volumes where R-CREST has no dynamic range.
- **R-NORMMAG, declared now, before the out-of-sample run:** the same statistic is measured on PHerc0358 traces, split by the same crest rule (A: crest >= 2.0, B: VOID at crest <= 1.05), with the boundary taken from PHerc0826 as **0.95** (between the two groups' extremes of 0.970 and 0.922, and not tuned to PHerc0358 in any way). It is confirmed only if, on PHerc0358, **every** group-A trace lies above 0.95 and **every** group-B trace below it. One exception either way and it is recorded as not confirmed. Until it is confirmed it gates nothing, and any later use as a gate is declared here first.

### Render contrast is not the explanation either (measured 2026-09-18 14:25 UTC; no bar changes)
- Third candidate explanation for the corpus's blank-like margins, after the render path (ruled out by Gate B, +0.4681 on ink) and the depth sign (ruled out by R-FLIP, most negative margin -0.0366): that our renders are so much flatter than the controls that villa's robust_mad 1-99 % normalisation stretches noise and the model answers mid-scale regardless of depth order.
- Measured on the CT mid slice, on-sheet standard deviation: **w040 team stack 39.94, our Gate B render of the w040 mesh 43.10**; the corpus reads run **PHerc0826 37.09, PHerc0358 37.38, PHerc1203 33.33, PHerc0800 29.56, PHerc1447 27.77** (medians over on-sheet reads). The scroll renders sit 7-30 % below the controls, in the same regime, not in a different one.
- So the input statistics are not the explanation. What remains, on the surface read so far, is the physical one: these surfaces carry no ink the 9 µm model can see. That is the corpus statement, and it is why the effort goes to area and breadth.

### R-NORMMAG result, out of sample on PHerc0358 (measured 2026-09-18 14:30 UTC): NOT CONFIRMED
- The boundary 0.95 was fixed from PHerc0826 before this run and is not touched. Result: group A (crest >= 2.0, n = 10) **10 of 10 above 0.95** — 0.9546, 0.9647, 0.9696, 0.9723, 0.9734, 0.9745, 0.9753, 0.9760, 0.9769, 0.9796. Group B (VOID at crest <= 1.05, n = 5) **4 of 5 below** — 0.4650, 0.5719, 0.7516, 0.8546 — and one at **0.9875**.
- The rule written before the run says one exception either way and it is not confirmed. **R-NORMMAG is therefore NOT CONFIRMED and gates nothing.** No boundary is moved and no group is redefined to rescue it.
- Recorded because it is informative, not as a new test: the one exception, `auto_grown_20260917225038237`, is the trace with the LOWEST |cos θ| of the twenty measured (0.8711, where every other trace sits at 0.9579-0.9991). So the field is confident about the sheet orientation there and the TRACE disagrees with it, which is the cross-cut signature the |cos| statistic was meant to catch, while every other group-B trace sits where the field itself is unconfident. The two statistics appear to fail on different populations.
- **Standing conclusion after two pre-registered geometry tests on the published field: neither R-NORMAL (by |cos θ|) nor R-NORMMAG (by normal length) is established as a gate, and neither will be used as one.** A third combined statistic is NOT being declared off the back of these two: pre-registering tests until one passes is how a false positive is manufactured, and this project does not have room for one. What remains decisive is R-CREST-POWER, which asks the only question that matters directly — whether the ink model finds anything on the surfaces R-CREST vetoes — and R-PHASE, which was declared before any of these numbers were seen.

### R-FLIP applied retrospectively, and a correction to its first number (2026-09-18 14:35 UTC)
- The tripwire was written into the reader on 2026-09-18; every earlier read predates it. Those reads keep their forward map, their reverse map and their on-sheet mask beside the stats, so the swapped evaluation can be computed with NO inference (`scripts/reflip_scan.py`).
- **Result over all 37 reads whose maps are on disk: 0 tripwire firings.** Not one read anywhere in the corpus flags a unit when the depth order is swapped. No verdict, ledger line or threshold changed; `rule55_depth_swapped` and `depth_swap_tripwire` are now recorded on each of those stats files.
- **Correction to the figure recorded under R-FLIP above.** That entry gave the most negative forward-minus-reverse mean as -0.0366, computed over reads whose `crest_check` block records a pass. Three early reads predate the crest block and were silently outside that filter. Over EVERY read with maps the most negative margin is **-0.0503** (`PHerc0826|auto_grown_20260917032202909`, forward 0.3801, reverse 0.4304, 3.28 cm², NOT ESTABLISHED). The conclusion is unchanged and the margin is unchanged in kind — a mirrored inked surface would sit near -0.15 and at worst past the -0.08 mirror of the frozen bar — but the number is corrected here rather than edited above, so both stay visible.
- Those same three early reads are the only ones that cannot be re-evaluated retrospectively: they were made before `onsheet_mask.png` was saved (the same three named in the R-5.5 tiling note). The one at -0.0503 is being RE-READ through the current pipeline so its swapped evaluation exists rather than being argued from an average; the other two are at +0.0021 and +0.0252 and carry no negative signal at all.

## R-RADIAL  Where in the scroll the corpus has actually been read (measured 2026-09-18 14:40 UTC; a measurement, not a bar; `scripts/radial_position.py`, `records/radial_*.json`)
- Why it was measured: the seeds are ordered outer -> middle -> inner and the density gate prefers sparse prediction neighbourhoods, which sit nearer the scroll edge (its own record notes the QC rejection rate rising from 10 % to 35 % for exactly that reason). Both push coverage OUTWARD, and the outer wraps of a Herculaneum scroll are the most damaged and the least likely to carry legible text. If the corpus is mostly outer wraps, "no ink found in 135 cm²" says much less about these scrolls than it appears to.
- Method: for each read surface, the radial position of its points between the scroll axis and the outer edge of the scanned material at the same z, reported as r/R in [0, 1]. Axis = the published `representations/umbilicus` control points where they exist (PHerc0826, PHerc0211, PHerc0125), interpolated in z; otherwise the centroid of the level-4 CT mask at that z. R = the 99th percentile radius of that mask's pixels at the same z, so one stray voxel cannot set the scale.
- **Corpus result over the 121 reads whose geometry is on disk:**
  - inner half (r/R < 0.50): **62 of 70 VOID (89 %)**, only **35.8 cm²** ever read;
  - outer half (r/R >= 0.50): 20 of 51 VOID (39 %), **99.3 cm²** read.
- **On PHerc0826, where R-CREST demonstrably has dynamic range (crest 1.00 to 3.12), the split is almost total: 15 of 16 inner traces VOID, 17 of 18 outer traces readable.** Every readable surface but one sits at r/R >= 0.717. The single inner exception is at r/R 0.492, crest 2.09, BLANK. PHerc0358 is the same picture with fewer inner attempts (2 of 2 inner VOID, 14 of 21 outer readable).
- **PHerc1203, PHerc1447 and PHerc0800 behave differently and the distinction matters:** they go VOID at BOTH radii (PHerc1203 15/16 inner and 6/6 outer; PHerc1447 27/31 inner and 6/6 outer), with crest never exceeding 1.42 anywhere. That is not a radial effect, it is the no-dynamic-range case R-CREST-POWER was declared to test.
- **What this changes.** The corpus's blank result is a statement about the OUTER WRAPS of two scrolls plus whatever R-CREST-POWER concludes about three others. It is not yet a statement about scroll interiors, where intact text lives and where only 35.8 cm² has been read, 89 % of attempts failing at the geometry stage rather than at the reader. The limiting factor named earlier as "area and breadth" is corrected here: it is **interior geometry**. No bar, threshold or verdict changes; this is a description of what the corpus covers.

## R-INTERIOR  Is the scroll interior resolvable at all, in either published product? (declared 2026-09-18 14:45 UTC, BEFORE the measurement)
- Why: R-RADIAL shows 89 % of inner-half traces fail at the geometry stage while 17 of 18 outer traces on PHerc0826 read fine. The tracer runs on `predictions/surfaces/...-m7-L0-th0.2.zarr`, and the seeds density gate already established that interior neighbourhoods are DENSE in that prediction — which is what adjacent wraps look like when a model cannot separate them. If the interior is unresolved in the product we trace on, no seeding strategy fixes it. The `cos` winding-phase field is the alternative: a continuous field whose level sets are sheets, with no "is this a surface" threshold to merge them.
- **Measurement.** On PHerc0826, at several z, cast radial rays from the published umbilicus outward and sample along each ray, in the interior band r/R in [0.20, 0.50]:
  - wraps resolved by the PHASE field: complete oscillations of `cos` (zero crossings of `cos` minus its along-ray median, counted in pairs, ignoring excursions smaller than 0.2 in decoded units);
  - wraps resolved by the SURFACE PREDICTION: connected runs above the tracer's own threshold (0.2 × 255) separated by at least one voxel below it;
  - the sheet spacing the CT itself shows along the same ray, from the first peak of the autocorrelation of the level-1 CT profile.
- **Criterion, fixed before the numbers.** The phase field resolves the interior materially better than the prediction if, over at least 20 rays, its median wrap count is **>= 1.5x** the prediction's, AND the spacing it implies agrees with the CT's own autocorrelation spacing to within **+-30 %**. Both halves are required: a field that oscillates faster than the sheets do is counting noise, not wraps.
- **If it passes:** interior tracing on the phase field becomes the engineering target, and the method is declared here before it is run. **If it fails:** the honest conclusion is that the scroll interior is not resolvable on this box with the published priors, and that is recorded as the finding rather than worked around. Either way no bar, threshold or verdict changes.

### R-INTERIOR result (measured 2026-09-18 14:50 UTC on PHerc0826, 36 rays at 3 z, band r/R 0.20-0.50): FAILS, and the failure is informative
- `records/interior_PHerc0826.json`. Median wraps resolved over an 898-voxel span (level 1 = 2 level-0 voxels): **phase field 24, surface prediction 28** → ratio **0.857**, where the criterion required >= 1.5. Implied spacing: phase **38.96** level-1 voxels, prediction **30.52**, and **the CT's own autocorrelation 24.0**. Errors against the CT: prediction **27 %** (inside the declared ±30 %), phase **62 %** (outside it).
- **So R-INTERIOR fails as written, and the phase field is NOT the better interior product — the surface prediction we already trace on is.** No criterion is relaxed and the phase field gets no further role from this test.
- The informative part, and the reason this changes the plan rather than ending it: **the interior IS resolved in the data.** The CT itself shows a wrap every 24 level-1 voxels = 48 level-0 voxels = **449 µm**, a sane spacing for papyrus plus gap, and the surface prediction tracks that to 27 %. The interior is not a blur. What fails there is not the data and not the product we trace on — it is the TRACER keeping to one sheet across a 5 cm² patch when the wraps are 449 µm apart. Every interior patch on record was grown with the same budget as an outer one (`generations: 60`, area 4.9-5.5 cm²), and a single 0.5 mm excursion crosses a wrap.
- That is a parameter question, and it is testable with the same measure that validated the seeds density gate (readable fraction 10 % → 59 %). It is declared next, before it is run.

## R-SMALL  Interior traces with a reduced growth budget (declared 2026-09-18 14:55 UTC, BEFORE any such trace)
- Hypothesis, from R-RADIAL and R-INTERIOR: interior traces fail because a 5 cm² patch grown at `generations: 60` has many chances to step across a 449 µm wrap, not because the interior is unresolved. A smaller patch has proportionally fewer.
- **Run:** interior seeds only (r/R in [0.20, 0.55] by the R-RADIAL measure), on PHerc0826 and PHerc0358, with `generations: 20` in a separate params file, everything else identical — same prediction volume, same density gate, same QC, same R-CREST, same reader, same frozen rule 5.5. Patch dirs are tagged so they can never be confused with the 60-generation ones.
- **Bar, fixed before the numbers.** The 60-generation interior baseline on record is **1 readable of 18 interior traces (5.6 %)** across PHerc0826 and PHerc0358 (R-RADIAL: 15 of 16 VOID on PHerc0826, 2 of 2 VOID on PHerc0358). The reduced budget is an improvement only if, over at least 15 interior traces, the readable fraction reaches **>= 30 %** — a better than fivefold gain, chosen so a one- or two-trace fluctuation cannot carry it. Below that it is recorded as no improvement and the budget goes back to 60.
- Cost is stated in advance: a 20-generation trace is roughly a third of a 60-generation one (~150 s against ~450-560 s measured), so 15 interior traces is about 40 minutes of one trace slot.
- This changes where and how coarsely we TRACE. No verdict rule, no rule 5.5 threshold, no R-CREST bar and no reading recipe is touched, and every resulting patch goes through exactly the pipeline every other patch goes through.

### R-SMALL: the declared budget of 20 generations cannot answer the question, and why the budget is re-set (2026-09-18 15:00 UTC, before any 40-generation trace)
- The first two 20-generation interior traces came out at **0.49 and 0.48 cm²** in 95 and 86 s. That is below QC 5.8's own area bar of **0.5 cm²**, so every such patch stops at geometry before the crest test or the reader ever sees it, and it is far below the **1.5 cm²** of valid units rule 5.5 needs before it will call anything BLANK. The run as declared cannot produce the readable fraction its bar is written in terms of. That is a defect in the parameter I chose, not a result about interiors.
- **What changes and what does not.** The BAR is untouched: >= 30 % readable over at least 15 interior traces, against the 5.6 % baseline (1 readable of 18), exactly as written before any trace. Only the growth budget moves, and it is chosen by arithmetic from the two AREA measurements alone, with no readable-fraction outcome in view: area scales roughly with the square of the budget (60 generations -> 4.9-5.5 cm²; 20 -> 0.49 cm²; 5.0/0.49 = 10.2 against (60/20)² = 9). A budget of **40** predicts 5.0 × (40/60)² = **2.2 cm²** — 4 nominal 0.5 cm² units, enough for a BLANK verdict and for the 3-unit cluster a candidate needs, and still under half the area a 60-generation patch has to hold to one sheet across.
- The two 20-generation traces are excluded from the R-SMALL population and counted in neither direction. They stay on disk under `patches/PHerc0826_small/` with `max_gen: 20` in their `meta.json`, so the exclusion is checkable rather than asserted.
- Disclosure: written after seeing those two areas and before any 40-generation trace was started.

### The same normal field, measured on PHerc1203 and PHerc1447, splits them (recorded 2026-09-18 15:10 UTC; a measurement, not a gate)
- R-NORMAL failed its bar as a DISCRIMINATOR between R-CREST's pass and VOID classes on PHerc0826, and it is not used as one. What follows is a descriptive measurement on two other volumes, reported because the effect is an order of magnitude larger than anything that appeared in that calibration (where every trace, pass or VOID, sat between 0.978 and 0.999).
- **PHerc1203, 22 surfaces: |cos θ| median 0.9967, range 0.990-0.999, occupancy 1.00. Not one below 0.90.** Those surfaces agree with the team's own published sheet normal almost exactly — and R-CREST still calls 21 of 22 VOID, at crest 1.03-1.20.
- **PHerc1447, 31 surfaces: |cos θ| median 0.5482, range 0.362-1.000, occupancy 0.73. Twenty-seven of 31 below 0.90**, the lowest at 0.362. A surface whose normal is perpendicular to the sheet normal is one that CONTAINS the stacking direction, i.e. cuts across wraps. Those values are not a marginal disagreement.
- So the three volumes R-CREST rejects wholesale are not one situation but two:
  - **PHerc1447** — two independent signals agree that the surfaces do not follow sheets (flat render AND normal disagreement). R-CREST looks right there, and its VOID verdicts are supported rather than merely unchallenged.
  - **PHerc1203** — the surfaces follow sheets by the published normal field and still render flat. That is the no-dynamic-range case, and R-CREST-POWER's reads on its four phase-1 members are what decide it.
- Nothing is gated on this and no verdict changes. It does tell us which half of the R-CREST-POWER population carries the information: the PHerc1203 members.

### R-PHASE result (measured 2026-09-18 15:15 UTC on PHerc0826; the bar is NOT changed): FAILS, and in the opposite direction
- `records/rphase/`. Group A (crest >= 2.0, n = 6): phase IQR median **0.9402**, range 0.776-1.051, std 0.514, 20.9 % of points within 0.2 of the median. Group B (VOID at crest <= 1.05, n = 8 of 9; one run lost to a transient fetch error): IQR median **0.5647**, range 0.526-0.816, std 0.394, 37.0 % within 0.2.
- The bar required group A's median IQR at or below **half** group B's (<= 0.2823) with non-overlapping ranges. It is **0.9402** — **1.66x group B's, not half of it** — and the ranges overlap. **R-PHASE fails, and the ordering is the reverse of what was predicted.**
- Why the premise was wrong, stated plainly: a scroll sheet is a SPIRAL. A surface that follows it travels along the winding and therefore sweeps phase; a surface that stays put and cuts across wraps samples a narrower band of phase locally. "One sheet = narrow phase" holds for a stack of flat sheets, not for a spiral, and that was an error in the hypothesis rather than in the field. The result is recorded as a failure and the statistic gets no role.
- **Tally of the pre-registered geometry tests on the published lasagna product: R-NORMAL failed, R-NORMMAG failed out of sample, R-INTERIOR failed, R-PHASE failed.** Four bars written before their data and four honest failures; no bar was moved and no fifth variant is being invented to rescue them. The field is real and readable (its decoding self-test passed at 0.9093), and its one durable contribution is the descriptive split of PHerc1203 from PHerc1447 recorded above. Geometry on this box is not going to be gated by it.
- What survives from the whole geometry effort is R-RADIAL, which needed none of it: the corpus is outer wraps, the interior is resolved at a wrap every 449 µm, and R-SMALL is the test of the tracer budget.

### G-B-43 result (completed 2026-09-18 14:46 UTC, ~55 min of CPU): **PASS — seed43 is admitted as a confirmatory reader**
- `records`: `gates/gateB43/gateB43.json`, `auc_render_plain{,_reverse}.json`. Scored exactly as seed42 was: same Gate B render (our own render of the w040 mesh crop), same labels and supervision mask, same slice and crop, same default ink threshold, 272 613 ink and 309 701 blank pixels.
- **Forward AUC 0.99562** (bar >= 0.95; seed42 0.99680). **Margin on labelled ink +0.45806** (bar >= 0.30; seed42 +0.4681), from forward 0.74899 against reverse 0.29093 on the same pixels. **Margin on labelled blank -0.03637** (bar <= +0.05; seed42 -0.0039). Reverse AUC 0.52689. All three bars cleared.
- Two independently seeded networks therefore agree on this surface to within 0.001 of AUC and 0.01 of ink margin. seed43's role stays exactly as written before the run: **confirmatory only** — it never flags a unit, never un-flags one, and no rule 5.5 threshold, screening tag or verdict depends on it. From now on every PROMISING CANDIDATE is additionally read with it (`--ckpt .../hybrid_3d2d-seed43/step-075000.pth --tag ink9um_seed43+plain --reread`) and the agreement is reported with the claim.

### R-CREST-POWER: the phase-1 ORDER is changed, the population is not (2026-09-18 15:30 UTC)
- The twelve surfaces fixed in RULES stay exactly the twelve, and all of them are read. Only the order changes: the four **PHerc1203** members go first, because the published normal field says those surfaces follow sheets (|cos θ| 0.9967) and still render flat — the case this experiment exists to decide — while the PHerc1447 members are the ones it says genuinely cross-cut (27 of 31 below 0.90). On a box where one read holds the inference lock for up to 70 minutes, reading the informative half first is worth an hour.
- This is a scheduling change and nothing else: no surface is added, dropped or reweighted, and the decision rule fixed before the data is untouched.
- Correction to the line above and to two earlier notes: phase 1 contains **three** PHerc1203 members, not four (`team_20251005230830031`, `team_20251005231446965`, `team_20251005221856743`), and nine PHerc1447 members. The reordered list is in `records/rcrest_power_phase1.txt`. Nothing else in those notes changes.

### R-SMALL: what follows from each outcome, written now rather than after the result (2026-09-18 15:35 UTC)
- A caveat that belongs on the record before the numbers arrive: the interior seeds R-SMALL is tracing were taken from the existing density-gated seed files, so they are interior **and sparse** (density <= 0.20 in a 31 px level-3 window). Genuinely dense interior regions carry no seeds at all, and the density gate was calibrated on 60-generation traces. R-SMALL therefore tests the BUDGET on the sparse interior, not the interior as a whole.
- **If R-SMALL passes** (>= 30 % readable over >= 15 traces): the reduced budget becomes the interior recipe, the interior queues run out on both scrolls, and the same seeds-plus-budget combination is declared for the next volumes before it is applied to them.
- **If R-SMALL fails**: the next question is already fixed — whether the density gate, calibrated at 60 generations, is the wrong gate for a 40-generation patch. A smaller patch has proportionally fewer chances to cross a wrap, so a denser neighbourhood may be acceptable for it. That would be run as its own declared test (interior seeds regenerated at a higher density cap, same 40-generation budget, same bar form against the same 5.6 % baseline), and it would be declared with its bar before any such seed was traced. It is written here so that it is a planned next step rather than a rationalisation invented after a disappointing number.
- **If R-SMALL fails and that follow-up also fails**, the honest conclusion is that interior geometry is not recoverable on this box with the published tooling and priors, and that is recorded as the finding — the same way R-NORMAL, R-NORMMAG, R-INTERIOR and R-PHASE were.

## R-WRAP  A measure of "held to one sheet" that does not need an air gap (declared 2026-09-18 15:45 UTC, before it is computed on anything)
- A confound in R-SMALL's own measure, recorded before its numbers arrive: "readable" there means the render passed R-CREST, and R-CREST needs a papyrus-to-gap density contrast. The first 40-generation interior trace renders as a gentle monotonic ramp, 97 to 102 across all 28 slices, crest 1.053 — the signature of a window lying entirely inside solid material. On a fully compressed interior a trace could hold to one sheet perfectly and still render flat, so R-SMALL's bar could fail for a reason that has nothing to do with the budget it is testing.
- **R-WRAP measures the thing directly.** R-INTERIOR established the wrap spacing from the CT's own autocorrelation: 24 level-1 voxels = 48 level-0 voxels = **449 µm** on PHerc0826. For a trace, take the radial coordinate of every valid grid point about the published umbilicus (the same axis R-RADIAL uses) and report the 5th-to-95th percentile spread in units of that spacing: `wrap_span = (r95 - r05) / 449 µm`. A surface that holds to one sheet has a span below 1 wrap plus what the sheet's own curvature contributes; one that steps across wraps has a span of several.
- **Calibration, and the bar, fixed before any number:** the reference populations are the ones R-CREST already sorted on PHerc0826, where it demonstrably has dynamic range — group A (crest >= 2.0, unambiguously one sheet) and group B (VOID at crest <= 1.05). R-WRAP is a usable measure of sheet-holding only if **median wrap_span in group A is below 1.5 AND below half of group B's median**. If it fails that, it is recorded as a failed measure like the other four and R-SMALL is judged on its declared bar alone.
- **If it passes**, it becomes the non-confounded secondary readout for R-SMALL, reported ALONGSIDE the declared readable-fraction bar and never in place of it: the primary bar stays exactly as written. It would then answer the question the readable fraction cannot on a gap-free interior — did the smaller budget actually keep the trace on one sheet?
- Nothing is gated on R-WRAP either way, no verdict changes, and no rule 5.5 threshold is touched.

### R-WRAP result (measured 2026-09-18 15:50 UTC on PHerc0826): FAILS, for the same spiral reason R-PHASE failed
- `records/rwrap/`. Group A (crest >= 2.0, unambiguously one sheet, n = 7): median wrap_span **28.47**, range 24.94-31.11. Group B (VOID at crest <= 1.05, n = 9): median **16.95**, range 9.80-25.44.
- The bar required group A **below 1.5 wraps** and **below half of group B**. It is **28.47** — nineteen times the first condition and 1.68x group B, not half of it. **R-WRAP fails on both halves and is not a usable measure of sheet-holding.** Nothing is retuned.
- Why, and it is the same mistake R-PHASE made: **a scroll sheet is a spiral.** Following it azimuthally through one turn moves you outward by exactly one wrap, so a 5 cm² patch that spans a large arc necessarily spans many radii. The radial spread of a sheet-following surface is not bounded by the wrap spacing at all — it is set by how much of the spiral the patch covers. Group A spans MORE radii than group B precisely because those surfaces travel further along the winding.
- **That is the fifth pre-registered measure to fail today** (R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE, R-WRAP), and the last three failed for one recurring physical reason: no scalar spread statistic distinguishes a good surface from a bad one on a spiral, because the good surface is the one that moves. **No sixth variant is declared.** R-SMALL is judged on its declared readable-fraction bar alone, the confound recorded with R-WRAP stands unresolved and is stated as such in any conclusion drawn from it, and R-CREST-POWER remains the experiment that asks the only question that does not depend on a geometric proxy: what does the ink model find on surfaces the crest veto rejects.
- Transcription correction, made immediately and noted here so the file and the commit history agree: the group A median was first written as 27.66 (that is the minimum of the group, not its median) with a ratio of 1.63x. The correct values are **28.47** and **1.68x**, as printed above. No conclusion changes; the bar was missed by the same wide margin either way.

### Bright-ink-in-render check: disposition of the two reads it flagged (recorded 2026-09-18 16:00 UTC)
- Page item 7 of the master prompt asks for a human look at any render containing bright elongated marks, because a lead-bearing ink would show as bright material in the CT rather than as a detection by the model. Over the 41 reads that carry the check, the count of elongated marks is **0 on 39** and **1 on 2**:
  - `PHerc0358|auto_grown_20260918041900161|0|ink9um_seed42+plain|both` — 1 mark, 7.6 % of bright pixels, verdict **BLANK**;
  - `PHerc0826|auto_grown_20260917143012277|0|ink9um_seed42+tta|both` — 1 mark, 4.5 % of bright pixels, verdict **BLANK**.
- **Disposition: neither is evidence of text, and neither is being treated as a lead.** Each is a SINGLE isolated mark meeting the 2-4 mm elongation criterion; the prize needs ten letters in one 4 cm² area, and one mark in a whole chart is not a letter, a row or a cluster. Rule 5.5 independently called both charts BLANK — no unit anywhere near the frozen levels. A single elongated bright feature in a carbonised scroll is what a mineral inclusion, a crack rim or a delamination edge looks like.
- The checks, the mark geometry and the contact sheets stay on record (`bright_ink_in_render` in each read's stats) so anyone can re-examine them. This is recorded as a closed loop, not as a candidate: nothing here is claimed, and no verdict changes.

### Why R-WRAP failed, part two: these scrolls are not circular (recorded 2026-09-18 16:10 UTC; descriptive)
- The spiral explanation above is real but incomplete, and the fuller reason matters because it rules out ANY radius-based measure, not just this one. Take the corpus's strongest surface, `PHerc0826 auto_grown_20260917090724211` (crest 2.88, 2.94 cm² on-sheet): its radius about the published umbilicus runs from **1567 to 2934 level-0 voxels**, a factor of 1.9, across a patch whose own bounding box is only ~2.4 × 2.2 cm. A circular scroll would hold r nearly constant along a wrap and the spiral would add about **0.1 wrap** of drift over an arc that short. It does not.
- The reason is that a carbonised Herculaneum scroll is **crushed**, not round. Distance from the umbilicus is therefore not a proxy for winding index at all: r varies strongly with azimuth on a single wrap. Any statistic built on radius — R-WRAP, or a "how many wraps did this trace cross" derived from r — is measuring the cross-section's irregularity more than the trace's behaviour.
- Recorded as the reason the measure cannot work, not as a repair of it. R-WRAP stays failed and unused, and this rules out the obvious variants rather than leaving them to be tried later.
- **Descriptive comparison at the two growth budgets, same scroll, same interior band** (this is a like-for-like contrast of one surface type at two budgets, not a good-vs-bad classification, so it is reportable even though R-WRAP failed as a classifier): 40-generation interior traces **10.99, 14.03, 16.13** (median 14.0); 60-generation interior traces **9.80 to 27.60** (median 18.41, n = 10). The reduced budget does give a proportionally smaller radial footprint, about what the area ratio predicts. It is reported as a footprint, and carries no claim about wraps crossed.

### Trace concurrency: one warm tracer against two cold ones (measured 2026-09-18 15:15 UTC; a throughput decision, not a bar)
- With two concurrent 9 µm tracers the normal-grid caches of two scrolls compete for a 30 GB disk that also holds two renders and their inference outputs. The guard then sits permanently at its tight 500 MB cap and every trace refetches its grids over the network.
- **Measured, 40-generation interior traces of the same size (2.1-2.4 cm²):** 269 s and 333 s with a warm cache, against **886 s and 1567 s** while thrashing; median over the five so far **535 s**.
- Decision: **one trace slot** (`TRACERS=1`, `TRACE_SLOTS=1`). Arithmetic stated in advance so it can be checked: one tracer at ~300 s is ~12 traces/hour, two thrashing tracers at ~900 s are ~8/hour. **Prediction to verify: the next five 40-generation traces come in under 400 s each.** If they do not, the throttle is wrong and two slots come back.
- This changes how fast patches arrive, not which patches or how they are read. No bar, threshold or verdict is touched.

### Two process failures of my own, recorded because they are the kind that hide a real result (2026-09-18 15:20 UTC)
1. **I committed on a red suite and did not notice.** The command was `pytest ... | tail -4 && git commit && git push`; `&&` chains off `tail`, whose exit status is 0 whatever pytest returned. Ten tests had failed. The commits themselves are sound (the failures were unrelated to their content, see below) but the check that was supposed to gate them did nothing. Any future gating run must read pytest's own exit status, not a pipeline's.
2. **The cause of those ten failures was a test-isolation defect I introduced hours earlier.** The render disk floor called `os.statvfs(DATA_ROOT)` — the REAL data root — so `process_patch` refused to render in unit tests whenever the machine's free disk was under 5 GB. The suite therefore passed or failed depending on how full the box happened to be, and it failed at exactly the moment the floor was doing its job. Fixed twice over: the floor now measures the filesystem the render will actually be written to (`os.statvfs(patch)`, which is what it always meant), and the test fixture sets `MIN_FREE_RENDER_GB = 0` so no test depends on machine state; the two tests that exercise the floor set it themselves.
- Neither touched a bar, a threshold, a verdict or a ledger line. They are recorded here because a suite that fails for environmental reasons is a suite people learn to ignore, and this project cannot afford that.
- Follow-up on the trace-concurrency decision: the loops read `TRACE_SLOTS` with a default of **2** and had been started before the supervisor exported 1, so two traces kept running and the measured durations stayed at 886-910 s. The default is now **1** inside both loops, the loops were restarted to pick it up, and the regular coverage tracers (PHerc0358, PHerc0175A) are paused so the single slot goes to the R-SMALL interior queues — the decisive test — until they have their 15 outcomes. The under-400 s prediction is judged on traces started after this restart, not before it.
- Scheduling follow-up (2026-09-18 15:36 UTC): the PHerc1447 member in flight selected **9614 patches** and will hold the global inference lock for hours. Since the published normal field puts this experiment's information in the PHerc1203 members, those three now run **in parallel on their own inference lock** (`scripts/rcrest_power_1203.sh`), which wastes no inference already spent and reaches the informative half now. Same population, same tag, same decision rule, same twelve surfaces read in the end; only the order and the lock differ.

## R-ROWS  Text is organised in rows; look for that everywhere, not only where the level bar already fired (declared 2026-09-18 16:05 UTC, BEFORE any measurement)
- **The blind spot, measured first.** Rule 5.5 records a row-periodicity statistic (`rows`: autocorrelation peak, pitch, `in_band` for a 2-4 mm line spacing), but `rule55` computes it only inside the bounding box of an ALREADY-FLAGGED cluster. Over 128 reads exactly **one** carries it. So the text-structure detector only ever looks where the level detector has already fired, and it cannot rescue text the level bar misses.
- **Why that matters here specifically.** The frozen levels (forward >= 0.36, margin >= +0.08) were validated on w028 text — and w028 is IN the 9 µm model's training corpus; RULES G-C records that its label AUC "measures memorisation". On a scroll the model has never seen, a genuine inked unit may sit well below those levels while still being organised in rows, because line spacing is a property of the scribe, not of the model's confidence. Nothing in the pipeline would see it.
- **The statistic.** On the on-sheet forward map of a read: subtract the on-sheet mean, zero outside the mask, take the 2-D autocorrelation by FFT, and for each direction θ read the first autocorrelation peak at a lag corresponding to **2-4 mm**. Report the maximum over θ of that peak height (ACF normalised to 1.0 at zero lag), the direction achieving it, and the pitch in mm. Real text gives a periodic ridge perpendicular to the lines; fibre texture and blob noise do not.
- **Calibration and admission bar, fixed before any number is seen.** On the Gate B render's forward map (our own render of the w040 mesh, with published ink labels): the in-band peak measured over the labelled-TEXT region must be **at least 2x** the peak measured over an equal-area labelled-BLANK region, and the detected pitch must fall inside 2-4 mm. If it does not, R-ROWS is recorded as an unusable indicator and nothing follows from it — the same way R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE and R-WRAP were recorded.
- **What it may and may not do.** R-ROWS **gates nothing and changes no verdict.** Rule 5.5 stays exactly as frozen; no threshold moves. If admitted, it is computed on every read with maps and recorded, and a chart whose in-band peak reaches the control's TEXT level is **flagged for protocol 9 review** — as a flag, never as a claim, and never as a letter count. Every existing verdict stands as ledgered.
- Cost: an FFT on a map already on disk, seconds per read, no inference.

### R-ROWS result (measured 2026-09-18 16:15 UTC on the w040 ground-truth control): FAILS its admission bar
- Two implementations were defective before the bar could be answered, and both are recorded rather than quietly discarded: (1) the mask-overlap denominator collapsed at large lags, returning "autocorrelation" values of 26.6 and 5.1 where a normalised ACF caps at 1.0; (2) I took the band MAXIMUM where the declaration said the first PEAK, so a monotonic trend read as a ridge. Fixed: lags are evaluated only where the mask overlap is >= 30 % of the zero-lag overlap, and only genuine local maxima count.
- The declaration said "the labelled-TEXT region", and the first corrected run masked to the labelled INK PIXELS — which is exactly the operation that destroys row periodicity, because it deletes the inter-line gaps. On that reading neither text nor blank produced any in-band local maximum at all.
- **Final measurement, on the region reading and on identical geometry** (the same contiguous supervised region and the same mask, 145 598 samples; the FORWARD map carries the ink signal at AUC 0.997 and the REVERSE map does not, at 0.503): forward in-band peak **0.00897** at 2.378 mm; reverse **0.08786** at 2.022 mm. The bar required forward >= 2x reverse. **The reverse map's periodicity is ten times the forward map's. R-ROWS FAILS.**
- **What that settles, and it is worth more than a pass would have been.** The worry R-ROWS was built to address was that the frozen levels, validated on a scroll inside the model's training corpus, might be too high for genuine unseen text that is nonetheless organised in rows. The control says there is no such channel to find: **the ink map carries no detectable 2-4 mm row periodicity even where the text is known and the model detects it at AUC 0.997.** So the level bar cannot be rescued by row structure, and no claim that it is "missing organised text" is supportable from this data.
- Sixth pre-registered measure to fail today, none retuned, none rescued by a further variant. `records/rrows_calibration_w040.json`.

## R-EYES  Look at the render before spending inference on it (declared 2026-09-18 16:20 UTC, from ground truth)
- **The finding that prompted it.** After 128 reads I had never once looked at a render or a map. Five minutes of looking produced more than five statistics did. Two images are now kept in `review_sheets/reference/` at matched physical scale (4 cm², the prize's own area):
  - `REFERENCE_w040_known_text_4cm2_9.362um.png` — a KNOWN flat sheet with KNOWN text: a crosshatched papyrus fibre weave, recto and verso fibre bundles crossing at right angles, with dark irregular strokes laid over it. That dark overlay is the "crackle" the 2023 Grand Prize was built on.
  - `PHerc1447_z_dbg_gen_00701_4cm2_8.64um_CROSSCUT.png` — one of our own reads: laminar swirling strata, layer edges seen edge-on like wood grain, no weave anywhere. It is a cross-section THROUGH the wrap stack, not a sheet.
- The two are not the same kind of object, and the difference is obvious at a glance. The published normal field said the same thing numerically for PHerc1447 (|cos θ| 0.36-0.55, 27 of 31 below 0.90), and **R-CREST was right to VOID it**. Our corpus has been feeding the ink model cross-cuts, which is why the model answers with texture.
- **Standing practice from now on, and it is a practice rather than a bar:** before any large or otherwise expensive read, and for every read that reaches protocol 9, the render's mid slice is viewed against the reference at matched scale. A surface that shows laminar strata instead of a fibre weave is not a reading surface whatever any statistic says. This vetoes nothing automatically and changes no verdict — R-CREST and rule 5.5 are untouched — but no candidate leaves this project without its render having been looked at beside the reference.
- Live defect found and fixed while running this (2026-09-18 16:25 UTC): `sweep_renders.py`, added an hour earlier to reclaim orphaned renders, was **deleting renders mid-write**. A patch being RE-read has a finished earlier read, so the sweeper's "every read finished" test called the in-progress re-read's render removable — it killed PHerc1203's render three times in a row and failed that surface out of the queue, the informative half of R-CREST-POWER. Fixed: a render is removable only if a completion marker exists (a render being written has none) AND nothing has touched it for 10 minutes. Both cases are now tests. The affected surface is re-queued; nothing was lost but time.

### R-EYES on the Grand Prize baseline input: PHerc1203's curated surfaces are not clean sheets either (recorded 2026-09-18 16:05 UTC; n = 1 of 22, stated as such)
- `review_sheets/reference/PHerc1203_team_20251005230830031_4cm2_9.362um.png`, the largest PHerc1203 surface the team publishes (16.40 cm² by QC), viewed at the same 4 cm² scale as the w040 reference.
- It shows **curving striations and swirl structures** — layer edges and deformed laminae — not the orthogonal crosshatched fibre weave of the w040 known-text reference. Its on-sheet fraction is **0.142**: 86 % of the render's canvas is empty, so the surface is also heavily fragmented. This is consistent with R-CREST calling 21 of 22 PHerc1203 surfaces VOID at crest ratios of only 1.03-1.20.
- It also resolves the tension with the normal field, which put PHerc1203 at |cos θ| 0.9967. Both can be true: the surface is LOCALLY tangent to the sheet at each sampled point, while the sheet itself is crumpled and fractured through the render's depth window. Local tangency is not the same as a readable flat sheet, and only the render shows the difference.
- **Stated as one surface of 22.** The remaining PHerc1203 members are being read by the R-CREST-POWER queue and their renders will be viewed the same way. This changes no verdict and no bar.
- **What it means for the Grand Prize baseline, stated plainly:** the 2023 Grand Prize was won on large, clean, flattened sheet surfaces of Scroll 1, produced by months of dedicated segmentation work. For these 23 eligible volumes, neither the team's published segments nor our own traces have yet produced a surface of that kind — not on PHerc1447 (laminar strata), not on this PHerc1203 surface (crumpled laminae, 14 % on-sheet), and not in the interiors we have reached. **The blocker is geometry, not reading**, and the reader has now been validated twice over (Gate B +0.4681 ink margin on our own render; G-B-43 +0.4581 on an independent checkpoint). The single lever we have that has produced a genuine crested sheet in an interior is R-SMALL's reduced growth budget, which gave crest 1.250 with 4 valid units where every full-budget interior trace gave a flat ramp.

### Direction fields: a claim I made and am withdrawing (recorded 2026-09-18 16:10 UTC)
- I found that `vc_grow_seg_from_seed` accepts a `direction_fields` array (`{zarr, dir: horizontal|vertical|normal, scale, weight_zarr?, weight?}`, `vc_grow_seg_from_seed.cpp:155`), saw that our params carry `"direction_fields": []`, and said we had been running the team's tracer in a degraded configuration. **That was an overclaim and it is withdrawn.** Three checks against the source say otherwise:
  1. We DO supply a sheet-orientation prior: `normal_grid_path` points at the published `<prediction>.normal-grids` store, and RULES already records that tracing without it cuts across windings (mean |n_z| 0.75-0.83). The tracer is not running without an orientation prior.
  2. The team's own example config (`scripts/evaluation/example_config.json`) populates `direction_fields` with **fiber** directions (`s5-fiber-directions.zarr/horizontal`, `dir: "horizontal"`) — an in-plane signal telling the tracer which way the papyrus fibres run. That is a different quantity from a sheet normal, and **no fibre-direction product is published for any of the 23 eligible volumes.** The same example leaves the OTHER stage's `direction_fields` empty, exactly as ours are.
  3. The lasagna `nx`/`ny` could be dressed as a `dir: "normal"` field, but `VcDataset` is a LOCAL filesystem zarr reader (blosc/zstd/lz4/gzip from `std::ifstream`, no remote driver), so it would have to be materialised on disk — and a missing chunk decodes to a confident WRONG direction under this encoding rather than to "unknown", which would actively mislead the tracer outside whatever box we fetched.
- Conclusion: supplying a second, redundant normal prior at real cost and real risk is not the highest-leverage move, and the "degraded configuration" framing was wrong. Recorded here rather than quietly dropped, because a wrong diagnosis that flatters the project is more dangerous than a blank corpus.
- Two throughput defects found and fixed while the queues ran (2026-09-18 16:25 UTC): (1) `rsmall_loop.sh` capped concurrent traces with a `ps` COUNT, which is racy — two loops that sample it in the same second both start, and two traces were running under a cap of one. It now takes the same flock slot pool `tracer_loop.sh` uses, so the cap holds across every loop on the box. (2) Renicing an inference by its main pid leaves its dataloader WORKER processes at the old priority: the deprioritised PHerc1447 read was taking 174 % CPU against 127 % and 107 % for the two informative reads. Renicing the whole process tree (81 threads across 5 processes) was needed.

### R-EYES: the first interior surface that looks like the known-text reference (recorded 2026-09-18 16:40 UTC)
- `review_sheets/reference/PHerc0826_interior_40gen_FIBRE_WEAVE_std45.4.png` — `PHerc0826_small auto_grown_20260918144212741`, an R-SMALL interior trace at 40 generations, 1.42 × 1.42 cm at native 9.362 µm. It shows the **crosshatched papyrus fibre weave**, recto and verso bundles crossing at right angles, exactly as the w040 known-text reference does. Its dark areas are voids and a crack, not strokes. This is the first surface in this project, from any volume, that looks like the reference.
- **On-sheet CT standard deviation 45.4, against the w040 known-text reference's 43.1.** That is the texture contrast a readable papyrus face has, and this interior surface has it.
- Its ledger verdict is **BLANK** (forward 0.3020, reverse 0.3292, margin −0.0272, 4 valid units, tripwire clear). That blank now means something it never meant before: **a genuine papyrus surface with resolved fibre, in the scroll interior, read correctly, carrying no ink the 9 µm model can see** — as opposed to the corpus's earlier blanks, which were largely cross-cuts through the wrap stack.
- **Crest and surface contrast are independent, and only the first is gated.** The two R-SMALL interior reads make the point sharply: `auto_grown_20260918152701336` has an excellent depth crest of 3.107 and an on-sheet std of only **8.6** — a featureless, fused medium with no fibre at all (`..._featureless_std8.6.png`), while this one has a weaker crest of 1.250 and a std of **45.4**. R-CREST asks whether the depth profile looks like a sheet; it does not ask whether the face carries papyrus texture. `onsheet_ct_std` is already recorded on every read and the w040 reference gives it a target value of ~43.
- Recorded as a measurement and a reference image. **No bar, threshold, gate or verdict changes**, and nothing here is proposed as a new gate — the observation is that the quantity is already on record for every read and now has a ground-truth scale.
- Looking at that surface's ink map (`review_sheets/eligible/overlays/PHerc0826__auto_grown_20260918144212741_overlay.png`): the fibre weave is plainly visible in the CT panel, and the pixels passing the overlay's display threshold form scattered blobs that **follow the dark void and crack boundaries**, not rows and not strokes. The forward-minus-reverse panel is balanced red/blue mottling with no organisation at any scale. So the model's false-positive mode on real papyrus is an EDGE response at voids and cracks, which is visible at a glance and is what a 2 cm² clean negative looks like. Recorded as an observation; the ledger verdict remains the frozen rule's BLANK and nothing is gated on this.

### Surface contrast vs forward level: a weak, under-powered observation, NOT a finding and NOT a gate (recorded 2026-09-18 17:35 UTC)
- Prompted by an apparent pattern in three R-SMALL interior reads: the two FEATURELESS surfaces (on-sheet CT std 8.6 and 10.0) returned high forward levels (0.4979, 0.4980) while the FIBRE-WEAVE surface (std 45.4) returned a low one (0.3020). The hypothesis that suggested itself is that the model answers a textureless fused medium with a high flat level.
- Measured across the whole corpus, n = 44 on-sheet reads carrying both quantities: **Pearson r(on-sheet CT std, forward mean) = −0.217; rank r = −0.120.** Grouped: std < 25, n = **3**, median forward 0.4979; std >= 35, n = 23, median forward 0.3949.
- **This does not support a claim.** r = −0.217 is weak, and the entire low-contrast group is three reads — the same three that prompted the look, so the grouping is not independent of the observation that generated it. Six pre-registered measures failed today; I am not declaring a seventh on n = 3, and I am not treating a post-hoc split as a measurement.
- Against the hypothesis, decisively: the corpus's **two flagged units sit at on-sheet std 10.0 and 33.7** — `PHerc0826|auto_grown_20260918155811706|0|ink9um_seed42+plain` (fwd 0.4980) and `PHerc0826|auto_grown_20260917090724211|0|ink9um_seed42+tta|b` (fwd 0.4195). A flag has occurred at both ends of the contrast range, so surface texture does not explain flagging and cannot be used to discount or promote a flag.
- **Nothing is gated, nothing is thresholded, no verdict changes.** `onsheet_ct_std` remains a recorded statistic with a ground-truth scale (w040 known text ≈ 43). If the low-contrast group ever reaches n >= 15 on its own, it can be declared as a bar BEFORE those reads are looked at; until then this paragraph is the whole of the claim.

### R-SMALL third readable interior surface (recorded 2026-09-18 17:30 UTC)
- `PHerc0826_small auto_grown_20260918155811706`, 2.09 cm², 40 generations: crest 3.06, on-sheet std 10.0, forward 0.4980, reverse 0.4660, margin **+0.0320**, **1 flagged unit of 4 valid**. Rule 5.5 requires >= 3 adjacent flagged units for a PROMISING CANDIDATE, so the verdict is **NOT ESTABLISHED** — not a candidate, not a blank, and no protocol 9.
- It is only the second flagged unit in the entire corpus (131 reads). Recorded as ledgered; no level, adjacency requirement or area unit moves.

## R-DEPTH  Has the corpus been reading the wrong depth? (declared 2026-09-18 17:45 UTC, BEFORE any run)
- **The finding that prompted it.** The ledger key is `scroll|surface|depth offset|checkpoint+TTA|order`. Across **135 reads the depth-offset field is `0` on every single line.** It is the one axis of the key we have never varied. The renders are 28 slices centred on the traced surface; `select_layer_indices` then centre-crops to the model's 17, i.e. slices 6..22, and slices 0..5 and 23..27 have never been shown to the reader. Meanwhile the ink is a thin layer on ONE face of a ~100–200 µm papyrus sheet, and at 9.362 µm the 17-slice window spans only 159 µm. If the tracer lands on the sheet's other face, or in the separation between two laminae, the ink band can sit at the edge of the window or outside it, and every read would look exactly like what we have: nothing, everywhere.
- The team's own published w040 surface volume is **28 slices** (verified: `controls/w040/stack.zarr` is (28, 6400, 7980)), so our render depth matches their convention exactly and the question is only where inside those 28 the reader looks.
- **The control.** The Gate B render — our own `vc_render_tifxyz` render of the w040 mesh crop, 28 × 2048 × 2048 — with the published ink labels and supervision mask, scored by `score_auc.py` at slice 14, crop `1152 2048 2048 2048`, seed42 step-075000, plain, both directions. That is the same render, checkpoint, scorer, crop and slice as Gate B.
- **The three windows**, all reachable with `--layer-start/--layer-end` at **no rendering cost**:
  | window | layer args | indices | centre | offset from centre |
  |---|---|---|---|---|
  | LOW | `--layer-start 0 --layer-end 17` | 0..16 | 8 | **−6 slices = −56.2 µm** |
  | CENTRE | (none; the default) | 6..22 | 14 | 0 |
  | HIGH | `--layer-start 11 --layer-end 28` | 11..27 | 19 | **+5 slices = +46.8 µm** |
- **The statistic** is Gate B's own and rule 5.5's own, forward minus reverse on the labelled INK pixels: `M(w) = mean_fwd_on_ink − mean_rev_on_ink`. AUC and the forward ink-minus-blank separation are recorded alongside but decide nothing.
- **M(CENTRE) = +0.46808**, taken from `gates/gateB/auc_render_plain{,_reverse}.json`, **written before this bar existed** and not re-run — the comparison is against a number recorded in advance.
- **Bars, fixed now:**
  - **ADMITTED if `max(M(LOW), M(HIGH)) >= M(CENTRE) + 0.05`** — an off-centre window genuinely reads ink better, so the corpus has been looking in the wrong place.
  - **ADMITTED if `r = min(M(LOW), M(HIGH)) / M(CENTRE) <= 0.50`** — the response is depth-SELECTIVE at the ±5-slice scale, so a mesh a few slices off the ink face loses half its signal, and the corpus must be swept even though the control's own centre is best.
  - **FAILS, and depth offset is closed permanently, if `M(CENTRE)` is the best AND `r > 0.50`** — the response is both centred and broad, a ±5-slice mesh error costs little, and the 135 reads at offset 0 lose nothing to it. No re-read would be owed and none would be run.
- **Part 2, only on admission**, with the set fixed NOW so it cannot be picked after seeing a result: re-read at both off-centre windows, under ledger keys `|-6|` and `|+5|`, (a) the corpus's two flagged-unit surfaces `PHerc0826|auto_grown_20260918155811706` and `PHerc0826|auto_grown_20260917090724211`, then (b) every read with `onsheet_ct_std >= 35` (genuine papyrus texture on the w040 scale of ≈43), in ledger order. **Rule 5.5 is untouched**: a unit flagged at a nonzero offset is a flagged unit exactly as at 0, and no level moves.
- **Stated limitation, and it is the important one.** ±6 slices is ±56 µm — a fraction of one papyrus sheet, and an eighth of the **449 µm wrap spacing** R-INTERIOR measured. R-DEPTH tests **mis-centring within a sheet**. It says nothing at all about a trace that landed on the wrong wrap, and neither a pass nor a fail may be quoted as if it did.
- Cost: 4 inferences on an existing 2048² render, no tracing and no rendering. Runs at nice 19 behind the production inference lock so no declared queue is delayed.

## G-GP  Reproduce the Grand Prize approach as a baseline: parameterisation quality (declared 2026-09-18 17:55 UTC, BEFORE any run)
- **What the Grand Prize approach actually was, and where ours differs.** The 2023 Grand Prize read large Scroll 1 sheet
  meshes that had been segmented, **flattened to a low-distortion 2D parameterisation**, and rendered as a layer stack,
  then run through a crackle-trained ink model with TTA. Four of those five stages we already match or beat: our reader is
  the team's current `ink_9um` model at AUC **0.99680** on our own render of a known-text mesh (Gate B), confirmed on an
  independent checkpoint at 0.99562 (G-B-43), and our render depth is the team's own 28-slice convention. The stage we
  have never checked is the **parameterisation**: we render each `tifxyz` grid as the tracer emitted it and have never
  measured how much that grid stretches, shears or sags relative to the surface it claims to represent. `vc_flatten`
  (ABF++) exists in the toolchain and we run it only at packaging time, after the read.
- **Why it could be the whole gap, physically.** A `tifxyz` is a coarse control mesh: `scale = 0.05` means one grid node
  per **20 level-0 voxels = 187 µm** at 9.362 µm. `vc_render_tifxyz --scale 1` interpolates 20x between nodes. Two
  failure modes follow and neither has ever been measured here:
  1. **Stretch and shear.** If the grid is locally stretched or sheared, the rendered image is locally squashed and
     skewed. Letters ~2 mm tall would be smeared across the wrong number of pixels, and an ink model trained on
     low-distortion renders degrades.
  2. **Sag.** If the true sheet bends between two nodes 187 µm apart, the interpolated surface cuts the chord while the
     sheet takes the arc. A sag comparable to the papyrus thickness (~100-200 µm) walks the render off the ink face
     mid-patch — the same failure R-DEPTH tests globally, but local and invisible to any per-read statistic we keep.
- **The measurement** (`scripts/mesh_distortion.py`, pure arithmetic on grids already on disk, no inference, no render).
  At each interior node of the `x/y/z` grids, central-difference tangents `t_u`, `t_v` in level-0 voxels against the
  nominal step `1/scale = 20`:
  - **stretch** `s_u = |t_u|/20`, `s_v = |t_v|/20` (1.0 = isometric);
  - **anisotropy** `a = max(s_u,s_v)/min(s_u,s_v)` (1.0 = balanced);
  - **shear** `|cos(t_u, t_v)|` (0 = orthogonal);
  - **sag** — distance in **µm** from the node to the plane fitted through its four grid neighbours.
  Median and 90th percentile of each, over nodes where all neighbours are valid.
- **Two references, and only one of them is the bar.**
  - **Reference A, w040 control mesh** (`controls/w040/mesh`) — the known-text surface our reader scores 0.99680 on.
    Reported for scale only. It is a **flat fragment**, and a flat fragment can be parameterised isometrically while a
    curved scroll wrap provably cannot (Gauss). Quoting it as a bar for scroll segments would be unfair and it is not
    used as one.
  - **Reference B, the team's own published segments for the eligible volumes** — what the team's pipeline itself reads.
    This is the bar, because it is the like-for-like comparison: same scrolls, same curvature, same tool.
- **Bar, fixed now.** An auto-grown trace is **parameterisation-degraded** if its 90th-percentile **anisotropy** exceeds
  Reference B's pooled 90th percentile by **>= 2x**, OR its 90th-percentile **sag** exceeds Reference B's pooled 90th
  percentile by **>= 2x**.
  - **If NO read surface is degraded by that bar**, parameterisation is not the gap. G-GP closes that door, it is the
    seventh measure to close a door rather than open one, and nothing is re-flattened.
  - **If some are**, exactly those are re-flattened with `vc_flatten`, the metric re-measured on the flattened output —
    which must fall below the bar, or the flatten is recorded as INEFFECTIVE and reported as such — and only then
    re-rendered and re-read under a `+flat` ledger key. **Rule 5.5 is untouched**; no level moves.
- **Separately reported, gating nothing:** the absolute 90th-percentile sag in µm against the **449 µm wrap spacing**
  R-INTERIOR measured and the ~150 µm papyrus thickness. A sag at or above the sheet thickness is a physical statement
  about the render regardless of how it compares to the team.

### G-GP result, part 1 (measured 2026-09-18 18:05 UTC): the bar finds degraded surfaces, and our meshes are 3x rougher than the team's
- **Reference A, the w040 control mesh** (known text, our reader scores AUC 0.99680 on it): stretch median **1.000**,
  anisotropy p90 **1.034**, sag median **3.6 µm**, p90 **9.9 µm**. A near-perfect parameterisation — and a flat fragment,
  so it is quoted for scale only, exactly as declared. That the median stretch comes out at 1.000 also confirms the
  metric and the `scale = 0.05` -> 20-voxel node spacing reading are right.
- **Reference B, the team's 66 published segments** (the bar): pooled p90 anisotropy **1.327**, pooled p90 sag **27.8 µm**;
  median-of-p90 1.092 and 11.6 µm.
- **Ours, 106 auto-grown traces:** pooled p90 anisotropy **2.429** (1.83x Reference B), pooled p90 sag **60.4 µm**
  (2.18x); median-of-p90 1.621 and **33.2 µm** against the team's 11.6 µm.
- **Bar as declared** (>= 2x Reference B's pooled p90: anisotropy 2.654, sag 55.5 µm): **15 of 106 traces are
  PARAMETERISATION-DEGRADED.** 14 of the 15 are flagged by sag, 2 by anisotropy. Worst: `auto_grown_20260917225038237`
  at 82.4 µm. **G-GP part 1 finds degraded surfaces, so part 2 is owed** and runs as declared.
- **A hypothesis of mine that the data does NOT support, recorded because it was mine.** I expected the growth budget to
  explain the distortion — R-SMALL was declared on the reasoning that a large patch has more chances to go wrong. Split
  by budget: max_gen 40, n=14, median p90 sag **31.7 µm**, anisotropy 1.801; max_gen 60, n=89, median p90 sag **33.7 µm**,
  anisotropy 1.612. The two are the same within noise, and the smaller-budget group is if anything slightly WORSE in
  anisotropy. Within our traces, r(area, p90 sag) = **+0.296** — weak. **The budget does not explain mesh roughness**, and
  this is not evidence for R-SMALL. R-SMALL stands or falls on its own declared bar, untouched.
- **What the data does support, and it is like for like.** The team's median published segment is **3.89 cm²**, between our
  two budgets' 2.21 and 5.11 cm², so patch size is not the difference. At comparable size, on the same scrolls, with the
  same tracer, **our meshes carry about three times the team's sag and roughly 50 % more anisotropy.** That is a real,
  measured deficit in the one Grand Prize stage we had never checked.
- **Absolute physical scale, reported separately and gating nothing, as declared.** The worst p90 sag anywhere in our
  corpus is **82.4 µm**; **0 of 106** traces reach the ~150 µm papyrus thickness, and all are far below R-INTERIOR's
  **449 µm** wrap spacing. So the deficit is real in relative terms but does not by itself show the render walking off
  the sheet. It is a candidate contributor, not a demonstrated cause, and must not be quoted as one.
- `gates/ggp/{refA_w040,refB_team,ours_autogrown,ggp}.json`; `scripts/mesh_distortion.py`, `scripts/ggp_result.py`.

### G-GP result, part 2 (measured 2026-09-18 18:20 UTC): vc_flatten is INEFFECTIVE, and the test I declared was confounded
- **The confound, found before the result was used and recorded before the verdict.** `vc_flatten` emits a grid with a
  **different node spacing** from the one it was given: the worst degraded trace went from a 209.5 µm spacing to 28.6 µm.
  Sag shrinks with the measurement baseline for any surface, so a denser grid scores better on raw sag without being one
  micron more faithful. **Part 1 needed no such correction and is unaffected** — every one of the 173 meshes it compared
  has a 20-voxel spacing (verified: median tangent length 20.0–21.8 vx across the control, the team's 66 and our 106).
  Part 2 compares meshes of different density, so the declared test does not hold there.
- **By the LITERAL declared test the flatten would have PASSED**: the worst trace's raw p90 sag fell 82.44 → 17.77 µm and
  its anisotropy 2.417 → 1.823, both under the bar. I am recording that, because it is what my own declaration asked for
  and it would have sent 15 surfaces to re-render and re-read on an artefact.
- **At a MATCHED 187.2 µm baseline** (`mesh_distortion.py --baseline-um`, stride chosen per mesh from its own spacing),
  over the 14 of 15 that flattened: **sag p90 pooled 75.7 → 112.0 µm, median-of-p90 64.6 → 84.6 µm — WORSE.** Anisotropy
  pooled 2.630 → 2.543 (unchanged), median-of-p90 2.417 → **1.930** (better).
- **Reading, and it is what ABF++ is for:** `vc_flatten` optimises the 2D UV layout's angles, and it does so by
  rasterising a NEW surface. It regularises the parameterisation and it adds geometric noise. Sag is the quantity that
  decides whether the render walks off the sheet; anisotropy is not. **The flatten is recorded as INEFFECTIVE for the
  deficit G-GP part 1 found. No surface is re-rendered and no read changes.**
- I applied a STRICTER test than I declared, never a looser one, and the stricter test is the one that stands.
- 1 of 15 failed outright and is reported rather than dropped: `PHerc0358/auto_grown_20260917220622565` —
  "ABF++: Solver failed (Failed to solve A), falling back to LSCM only ... LSCM failed: Failed to solve AtA ...
  Regrid retry failed. Flattening failed." No output directory was produced.
- `gates/ggp/part2_{before,after}.json`.

### The team ships the measurements I have been hand-rolling, and we never built them (recorded 2026-09-18 18:25 UTC)
- `scripts/build_vc3d.sh` builds **7 of the 48 CLI apps** in `volume-cartographer/apps/src`. Among the 41 we skipped:
  - **`vc_tifxyz_selfcross`** — "Census a tifxyz surface for non-adjacent transverse self-intersections. Report-only",
    with `--fail-on-crossing` as a script gate. **A trace that steps across a wrap and returns folds back onto itself.**
    This is the team's own purpose-built detector for exactly the failure R-INTERIOR diagnosed as our blocker, and I
    instead hand-rolled R-WRAP and R-PHASE, both of which failed for a reason I then wrote down: a spiral defeats any
    scalar spread statistic. A self-intersection census is not a spread statistic, so the reason those failed does not
    apply to it.
  - **`vc_tifxyz_winding`** — per-node winding number on a tifxyz. The invariant that actually distinguishes "stayed on
    one wrap" from "crossed to the next", instead of the radial and phase proxies that failed.
  - `vc_grow_seg_from_segments` — the second growth stage that builds a large surface from grown patches. The
    Grand-Prize-shaped step we have never run.
  - `vc_fiber_trace_metric`, `vc_calc_surface_metrics` (needs a hand-placed point collection; not usable unattended),
    `vc_cut_windings`, `vc_merge_patch`, `vc_seg_add_overlap`, `vc_straighten`, `vc_tifxyz_inp_mask`.
- **This is my error, and it is the most expensive one on record in this project.** Six hand-rolled geometry measures
  were declared and failed today while the team's own instruments sat unbuilt in a source tree already checked out on
  this box. Recorded here with the same weight as any failed bar.
- Next: build them, and declare a bar for the self-intersection census on the calibration groups BEFORE it is run.

## R-CROSS  Does a trace fold back onto itself? (declared 2026-09-18 18:40 UTC, BEFORE any run, using the team's own tool)
- **Why this one is different from the six that failed.** R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE, R-WRAP and R-ROWS
  were all *statistical proxies* for "did this surface stay on one sheet", and three of them failed for a reason I wrote
  down at the time: **a scroll sheet is a spiral, so the good surface is the one that moves**, and no scalar spread
  statistic can separate it from a bad one. A transverse self-intersection is not a spread statistic. **Two parts of one
  papyrus sheet cannot occupy the same voxel.** A census of non-adjacent transverse contacts is therefore a *proof of a
  geometry error*, not a correlate of one — and the team ship the census as `vc_tifxyz_selfcross` ("Report-only: nothing
  is modified", with `--fail-on-crossing`), which I failed to build.
- **Populations, fixed now:** (a) the **w040 control mesh** — known-good, known-text, our reader scores AUC 0.99680 on
  it; (b) the **team's 66 published segments** for the eligible volumes; (c) **our 106 auto-grown traces**. Default tool
  parameters (`--exclude 1 --maxedge 60 --cell 40`), recorded with the result.
- **Statistic:** number of transverse contact sites, and that count divided by the surface's QC area (sites per cm²),
  plus the fraction of surfaces in each population with at least one contact.
- **Bar for admitting R-CROSS as a pre-render VOID gate, fixed now.** It is admitted only if the crossing rate separates
  outcomes on our OWN corpus: split our read traces at the team's pooled 90th-percentile rate; the high group must be
  VOID-or-unreadable at a rate **>= 2x** the low group's, with **>= 30 traces on each side**. If either side has fewer
  than 30, or the ratio is below 2x, R-CROSS is **recorded as a descriptive statistic and gates nothing** — it will not
  be retuned, re-split, or re-run with other parameters to find a threshold that works.
- **Whatever the outcome, nothing is retroactive.** No ledger verdict changes, rule 5.5 is untouched, and no read is
  withdrawn. A gate, if admitted, applies only to traces made after it is admitted.
- **The control result must be reported first and prominently.** If the w040 control mesh — a known-good sheet carrying
  known text — itself shows transverse contacts, then contacts are tolerable in a readable surface and the measure means
  far less than its physical argument suggests. That possibility is written here before the number is known.
- Cost: a local geometry census on grids already on disk. No inference, no render, no tracing.

### Throughput defect: the disk guard was pruning normal grids out from under a live tracer (fixed 2026-09-18 18:30 UTC)
- The guard prunes `normal_grids/<scroll>/` above a size cap. It did so **while that scroll's tracer was running**, so
  the tracer refetched the grids within the minute, the directory went straight back over the cap, and the next sweep
  pruned it again. The loop does not relieve disk pressure — it converts it into network time.
- **Measured, before the fix, on 40-generation interior traces (the R-SMALL population), from each patch's own
  `meta.json elapsed_time_s`:** the first two, run before the guard began pruning PHerc0358's grids under a live trace,
  took **269 s and 333 s**. Over all 14 at that budget the median is **1052 s** and the maximum **2358 s** — a ~4x
  slowdown, on the one experiment in this project that has produced readable interior surfaces.
- **Fix:** `prune_grids` skips any scroll with a `vc_grow_seg_from_seed` or `vc_render_tifxyz` running (read from the
  container process argv), **except** below the 3 GB hard floor, where it prunes everything with an explicit `force` —
  running out of disk is worse than a slow trace. Seven tests pin both behaviours, including that another scroll's idle
  grids are still pruned and that the hard-floor branch passes `force`.
- **The check on the fix, declared here before the traces run:** the next 10 completed 40-generation interior traces are
  compared on `elapsed_time_s` against the 14 above (median 1052 s). This is a throughput measurement and it changes no
  bar, no verdict and no reading; if the median does not fall, the diagnosis was wrong and that is what gets recorded.

### R-CROSS result (measured 2026-09-18 18:10 UTC): NOT ADMITTED at 1.87x against a 2.0x bar — and the descriptive number is the largest signal in this project
- **The control, reported first as declared.** The w040 known-text mesh is **NOT clean**: 62 transverse contacts (63
  under the other triangulation) over 218 386 triangles and 43.6 cm², i.e. **1.42 sites/cm²**. So a self-intersection is
  not by itself disqualifying, exactly as the declaration allowed for, and the physical argument is weaker than it looks
  as a boolean. **The rate, not the boolean, is the quantity.**
- **The three populations:**

  | population | n | with any contact | median sites | median sites/cm² |
  |---|---|---|---|---|
  | w040 control (known text) | 1 | 100 % | 62 | **1.42** |
  | team's published segments | 66 | **30.3 %** | **0** | **0.00** |
  | our auto-grown traces | 107 | **92.5 %** | **1246** | **262.61** |

- **The declared split: NOT ADMITTED.** Threshold = the team's pooled p90 rate, 341.58 sites/cm². HIGH group n=45,
  **86.7 %** unreadable; LOW group n=56, **46.4 %** unreadable; ratio **1.87x** against the declared **2.0x**.
  **The bar does not move.** R-CROSS gates nothing, changes no verdict, and is not retuned, re-split or re-run with
  other parameters — which is what the declaration said before the number was known. It is recorded as a descriptive
  statistic only.
- **What the descriptive statistic says, and it is the clearest quantitative statement of the blocker we have.** Two
  parts of one papyrus sheet cannot occupy the same voxel. The median trace of ours contains **1246 places where the
  surface is physically impossible**, at **185x the known-text control's rate**, while the team's median published
  segment on the same scrolls contains **none at all**. This is a far larger separation than the mesh sag deficit
  (3x, G-GP part 1), and it is not about the reader, the depth window or the parameterisation: **our tracer is producing
  surfaces that fold through themselves, and the team's is not.**
- Note the split's own honesty check: 86.7 % vs 46.4 % is a large difference in outcome, and it still misses a 2.0x
  ratio because the LOW group is already 46 % unreadable. A gate admitted on that would not have bought much.
- **Next, and it is a tracer-configuration question, not a new statistic:** compare our `vc_grow_seg_from_seed`
  parameters against the team's for the same scrolls, and find what they set that we leave at a default.
- `gates/rcross/{rcross,rcross_split}.json`, `scripts/rcross.sh`, `scripts/rcross_result.py`, `scripts/rcross_split.py`.

## G-GP part 3  The second growth stage — the step the team actually uses (declared 2026-09-18 18:35 UTC, BEFORE any run)
- **The evidence, from the team's own published files.** Every `team_z_dbg_gen_*` segment of PHerc1447 carries
  `"vc_grow_seg_from_segments_params": {"consensus_default_th": 6, "consensus_limit_th": 2, "flip_x": false,
  "global_steps_per_window": 2, "step": 6}`. Their surfaces are **consensus surfaces grown from a DIRECTORY of source
  segments**, not single greedy traces. We have run only stage 1 (`vc_grow_seg_from_seed`) for 107 traces and have never
  run stage 2, whose binary we had not built until today.
- **Why this is the direct answer to R-CROSS**, and it is mechanical rather than statistical: a point accepted only when
  six independent source patches agree cannot fold through itself the way one greedy trace can. R-CROSS measured our
  median trace at **262.61 self-intersections per cm²** against **0.00** for the team's median published segment on the
  same scrolls and **1.42** for the known-text control. Stage 2 is the difference in the pipeline, not a difference in
  the tracer's luck.
- **The run**, with the team's parameters used verbatim: `vc_grow_seg_from_segments --volume <the same surface-prediction
  zarr stage 1 uses> --src-dir patches/PHerc0826 --target-dir patches/PHerc0826_cons --params <team params>
  --seed-coord 4705,3262,4081`. That seed is the densest patch-overlap node in our PHerc0826 set — **covered by 12 of
  our 66 patch bounding boxes** — computed and written here before the run.
- **Bars, fixed now. All three are geometry; none involves ink.** SUCCESS requires all of:
  1. output area **>= 4 cm²** (the prize's own area);
  2. transverse crossing rate **<= 14.2 sites/cm²** — ten times the w040 known-text control's 1.42, against our
     single-trace median of 262.61;
  3. p90 sag **<= 55.5 µm** at the standard 20-voxel node spacing — the same bar G-GP part 1 used (2x the team's pooled
     27.8 µm).
- **On success** the surface goes through the pipeline unchanged: QC, R-CREST, render, plain read in both depth orders,
  rule 5.5, under its own ledger key. No level, area unit or adjacency requirement moves, and success here is a
  statement about geometry only — it is not a letter and not a candidate.
- **On failure** the reason is measured, not asserted: the output area, the crossing rate, and the number of source
  patches that actually contributed (not merely overlapped in bounding box).
- **The consensus threshold is NOT tuned to make this pass.** It runs at the team's published 6. If it fails for want of
  consensus, that is a finding about OUR patch density, and any run at another threshold is a separate experiment with
  its own declaration written before it.

### G-GP part 3 result (measured 2026-09-18 18:50 UTC): the run is blocked by a PRECONDITION on our patch library, measured before spending the download
- **First, a fact about the tool.** `vc_grow_seg_from_segments` opens its volume with `VcDataset(vol_path / "0")`, the
  LOCAL filesystem zarr reader (`vc_grow_seg_from_segments.cpp:1155`), while `vc_grow_seg_from_seed` uses
  `Volume::NewFromUrl` for an `s3://` path. Stage 2 therefore needs the surface-prediction store on local disk. The
  first attempt failed exactly there: `zarr: cannot detect version at s3://.../...zarr/0`. Materialising a box of it is
  possible — chunks are 192³ and ~449 KB each, so a 2112³-voxel box is ~600 MB — but that cost is only worth paying if
  the consensus can succeed at all.
- **The precondition, and it is the thing that decides.** Stage 2 accepts a point only where `consensus_default_th`
  source patches agree — the team publish **6**, the engine default is **10**. `scripts/patch_agreement.py` measures
  that directly from grids already on disk: every patch's valid points voxelised at **24 level-0 voxels = 225 µm**,
  half the 449 µm wrap spacing R-INTERIOR measured, counting DISTINCT patches per cell. The cell over-counts (two
  patches in one cell could sit on adjacent wraps where the spacing is locally tighter), so every area below is an
  **UPPER BOUND** and a negative conclusion is stronger than it looks.

  | patches agreeing | PHerc0826 (66 patches) | PHerc0358 (43 patches) |
  |---|---|---|
  | >= 2 | 45.12 cm² | 26.62 cm² |
  | >= 3 | 12.75 cm² | 10.83 cm² |
  | >= 4 | **5.44 cm²** | 4.43 cm² |
  | >= 6 (the team's value) | **1.15 cm²** | 0.09 cm² |
  | >= 10 (engine default) | 0.00 cm² | 0.00 cm² |
  | max in any single cell | **7** | **6** |

- **G-GP part 3 as declared cannot succeed and is not run.** At the team's threshold of 6 the whole PHerc0826 library
  supports at most **1.15 cm²** of consensus surface — scattered, and an upper bound — against the declared 4 cm² bar.
  At the engine default of 10 it supports none: the maximum agreement anywhere in 66 patches is 7. **The blocker is
  patch DENSITY, not the tool and not the threshold.** Recorded as a precondition failure rather than a run, because
  spending 600 MB and hours of growth to watch it stop at 1 cm² would have told us nothing this did not.
- **What this reframes, and it is the most useful thing learned today.** Our tracer is not uniquely bad. We have been
  growing ONE greedy trace per seed and reading it; the team grow MANY and take the consensus of six. That is exactly
  why R-CROSS finds 262.61 self-intersections per cm² on our median trace and 0.00 on theirs — a six-fold consensus
  cannot fold through itself. **The correction is more traces in the SAME place, not more places**, which is the
  opposite of the breadth-first coverage this project has been running for two days.

## G-GP part 4  Concentrated seeding: many traces on ONE sheet (declared 2026-09-18 18:55 UTC, BEFORE any run)
- **Why the existing seeding cannot produce consensus, arithmetically.** Seeds are placed >= 40 level-3 voxels apart,
  i.e. **320 level-0 voxels**, and the wrap spacing R-INTERIOR measured is **48 voxels (449 µm)**. Two seeds 320 voxels
  apart in an arbitrary direction are therefore up to **six wraps apart**. Traces from them can overlap in space and
  still be on different sheets — which is exactly what part 3 measured: 21 % of cells hold 2 patches, but only 0.55 %
  hold 6, and never more than 7 anywhere.
- **The correction, and it needs no new tool.** Seed the next traces **from the surface points of an existing patch**,
  so every one of them starts on the SAME physical sheet by construction, rather than from a 3D grid that ignores which
  wrap a point belongs to.
- **The source patch is chosen by a rule written before it is computed**, so it cannot be picked to suit a result. Among
  PHerc0826 patches: area **>= 4 cm²**, a non-VOID read outcome (the surface reached the reader, so it is a real sheet
  and not a cross-cut), and then the **lowest transverse self-intersection rate per cm²** from the R-CROSS census. Ties
  break on the lower p90 sag.
- **The campaign:** ~25 seeds sampled to spread evenly over that patch's valid points (a minimum separation in grid
  index, not in 3D), traced at the standard 60-generation budget with the existing parameters. Nothing about the tracer
  changes; only where the seeds come from.
- **Milestone 1, the precondition, measured with the same script and the same 24-voxel cell as part 3:**
  **>= 4 cm² of cells at agreement threshold 6**, within this campaign's patches plus the existing ones. The 4 cm² is
  the prize's own area, and the measure is the same upper bound as before.
- **Milestone 2, geometry, unchanged from part 3:** the consensus surface from `vc_grow_seg_from_segments` must have
  area **>= 4 cm²**, transverse crossing rate **<= 14.2 sites/cm²** (10x the w040 known-text control's 1.42), and p90
  sag **<= 55.5 µm**. The consensus threshold used is recorded with the result; **the geometry bars, not the threshold,
  are the test**, so running at a threshold our library supports is not tuning a bar — the bars do not move.
- **Milestone 3:** the consensus surface goes through the pipeline unchanged — QC, R-CREST, render, plain read in both
  depth orders, rule 5.5 — under its own ledger key. No level, unit or adjacency requirement moves.
- **If milestone 1 is not reached**, the recorded result is the **agreeing area at threshold 6 as a function of the
  number of traces in the campaign**. That curve says whether the approach scales or not, and it is the deliverable
  whether it passes or fails.
- **This supersedes breadth-first coverage as the primary use of the trace slot**, and that is a deliberate reversal:
  two days of breadth produced 135 reads, 0 candidates, and a patch library too sparse to support the team's own second
  stage. Existing coverage queues stay paused while the campaign runs.

### R-SMALL result (called 2026-09-18 19:00 UTC at the declared 15th outcome): FAILS its bar at 20.0 % against 30 %
- **17 traces at 40 generations, 15 with an outcome, 3 readable = 20.0 %**, against the declared bar of **>= 30 % over
  at least 15 outcomes** and the 60-generation interior baseline of 1 of 18 = 5.6 %. **R-SMALL FAILS. The reduced
  interior budget is NOT adopted as the interior standard.** The bar does not move, and 20 % being 3.6x the baseline is
  not a reason to move it — that comparison was available when the bar was written and the bar was still set at 30 %.
- The three 20-generation traces stay excluded and counted in neither direction, filtered by their own `max_gen`, as
  declared. Two traces are still pending and are counted in neither direction; the bar was called at the 15th outcome
  exactly as written, and a later outcome cannot re-open it.
- Breakdown: 8 VOID by R-CREST, 4 stopped at QC (3 FAIL, 1 UNREADABLE), 3 reached the reader — 2 BLANK and 1 NOT
  ESTABLISHED.
- **What R-SMALL nonetheless produced, stated without using it to rescue the bar.** It gave this project its only
  interior surface that looks like the known-text reference — `auto_grown_20260918144212741`, crosshatched papyrus
  fibre weave at on-sheet CT std **45.4** against the w040 reference's 43.1, read correctly and genuinely BLANK — and
  one of the corpus's only two flagged units (`auto_grown_20260918155811706`, 1 of 4 units, NOT ESTABLISHED). Those are
  ledgered results and they stand on their own. They do not make a 20 % readable fraction into a 30 % one.
- **And the budget was not the mechanism anyway.** G-GP part 1 measured mesh roughness by budget and found no
  difference (40 gen: median p90 sag 31.7 µm; 60 gen: 33.7 µm), which is recorded above as a hypothesis of mine the data
  refutes. R-SMALL failing its bar and the budget failing to explain mesh quality are the same finding twice.

### G-GP part 4: the target footprint, recorded before the campaign's traces land (2026-09-18 19:10 UTC)
- The source patch `PHerc0826 auto_grown_20260917043355441` occupies **9 903 cells = 5.00 cm²** at the 24-voxel cell
[line withheld: prize-candidate detail under review]
  about 80 % of the source patch's own footprint** — that is what 25 traces started on its surface have to achieve.
  Written here so the milestone cannot be read as easier after the fact than it is.
- The deliverable is the same either way: `patch_agreement.py --curve` gives the agreeing area at each threshold as a
  function of how many campaign traces are included, in order. That curve says whether concentrated seeding scales.
- Five tests pin the measure, including that two sheets one wrap (48 voxels) apart are NOT counted as agreeing and that
  a single dense grid cannot satisfy a consensus threshold on its own.

### How much sound canvas have we actually read? (descriptive, 2026-09-18 19:15 UTC; gates nothing, changes no verdict)
- The project's headline number has been "cm² read". R-CROSS makes a sharper one available: of the area that reached the
  ink model, how much was on a surface a papyrus sheet could physically be? Sound = at most **14.2 transverse
  self-intersections per cm²**, the G-GP part 3 geometry bar, ten times the w040 known-text control's measured 1.42.
- Over the 121 reads carrying a radial position: **39 reached the model (135.1 cm²)**, and of those only **8 reads,
  36.2 cm², were on sound geometry** — **22.9 cm² in the inner half of the radius (4 reads, all BLANK)** and 13.3 cm²
  in the outer half (3 BLANK, 1 NOT ESTABLISHED). Zero PROMISING CANDIDATE.
- **What may and may not be concluded from a corpus of 141 reads and 0 candidates.** A Herculaneum scroll unrolled is
  on the order of 10 000–30 000 cm². **We have read roughly 23 cm² of geometrically sound interior canvas** — of order
  one part in a thousand. The supportable statement is therefore *"nothing in the ~23 cm² of sound interior canvas we
  have read properly"*, and **not** "these volumes carry no ink the 9 µm model can see". Any wording that drifts toward
  the second is an overclaim and is to be corrected on sight.
- This is also the quantitative case for the strategy reversal recorded under G-GP part 4: the scarce resource is sound
  canvas, and breadth does not produce it. `scripts/good_canvas.py`, `gates/ggp/good_canvas.json`.

### A queue that ended early, and what is and is not established about why (2026-09-18 19:25 UTC)
- The G-GP part 4 dense loop logged one seed, then `dense queue done`, having traced **1 of 25**. The one trace it made
  is sound (5.01 cm² in 430 s at 60 generations).
- **The cause is NOT established, and I am not claiming one.** The likeliest explanation is mine: I started the loop by
  hand and the supervisor then started a second copy, and I killed one of them — two loops sharing a pid file, a log
  and a flock slot. A second, real hazard is that the loop fed its seed list through a **pipe into `while read`**, which
  hands the loop's stdin to every command in the body, so a queue can be eaten silently from inside. `rsmall_loop.sh`
  has the same shape and traced 17 seeds without trouble, so the pipe is not proven to be the cause here.
- **Fixed by shape rather than by symptom**, which is the same move as extracting the disk guard to its own file: the
  seed list is now read into an array before the loop, the tracer call has its stdin closed, and the loop logs how many
  seeds it took and how many patches exist after each one — so a truncated queue is visible in its own log instead of
  having to be inferred from a patch count. Four tests pin that shape.
- Recorded because a defect whose cause is unknown is more dangerous than one that is understood, and writing down
  "probably my duplicate loop" rather than the tidier "stdin bug" is the accurate version.

## G-GP part 3b  A falsifiable prediction from the precondition, and a plumbing check (declared 2026-09-18 19:40 UTC, BEFORE the run)
- Part 3 was not run because `patch_agreement.py` says our PHerc0826 library supports at most **1.15 cm²** of six-fold
  agreement. That measure is itself new and unvalidated, so it gets tested rather than trusted.
- **The prediction, written before the run:** with the team's `consensus_default_th: 6` and the existing 66 PHerc0826
  patches as `--src-dir`, `vc_grow_seg_from_segments` seeded inside the agreeing region produces a consensus surface of
  **at most about 1.15 cm²** — the agreement measure's own upper bound. If it produces substantially MORE than that,
  the agreement measure is wrong and every conclusion drawn from it (including G-GP part 4's whole rationale) is
  suspect and must be re-examined. If it produces that much or less, the measure is corroborated.
- It also serves as the **plumbing check** on the locally materialised prediction box (`scripts/fetch_pred_box.py`):
  that stage 2 loads a partial local store, reads the source directory and grows at all. Better to find a broken
  invocation now than when the part 4 campaign's traces have landed.
- **This is NOT G-GP part 3.** Part 3's declared bars (area >= 4 cm², crossing rate <= 14.2/cm², p90 sag <= 55.5 µm)
  are not applied to this output and cannot be passed by it; the precondition already says so. The output is measured
  with the same instruments and reported as what it is.
- The box fetched is the source patch's bounding box plus a 200-voxel margin, recorded in the store's own `meta.json`.
  Chunks outside it are absent and read as the fill value 0, which for a surface prediction means "not a sheet", so
  growth stops at the box edge rather than being misled — the opposite of the direction-field case recorded above,
  where a missing chunk would decode to a confident wrong direction.

### G-GP part 3b result (measured 2026-09-18 19:50 UTC): the prediction holds, and the plumbing works
- **The plumbing works.** `vc_grow_seg_from_segments` ran against the locally materialised prediction box
  (`pred_local/PHerc0826`, 1229 of 1575 requested chunks present, **295 MB**, 221 s — a fifth of the 690 MB I had
  budgeted, because a thresholded surface prediction is sparse), loaded **all 56 source patches**
  (`SurfacePatchIndex built for 56 surfaces patches=12600`), and grew from the seed. Its output even records
  `seed_source_patch: patches/PHerc0826/auto_grown_20260917043355441` — the tool identified the same source surface
  the declared rule picked.
- **The prediction holds.** The agreement measure's upper bound was **1.15 cm²**. The consensus output is
  **0.11 cm²** (`auto_trace_...`, 0.05 cm² for the `auto_grown_` companion). Well under the bound, so the measure is
  corroborated rather than contradicted, and G-GP part 4's rationale stands.
- **The log says exactly why, and it is worse than the bound suggested.** Through 184 generations the engine reports
  `best th: 0` at every candidate while dropping its inlier threshold from 20 to 2 in steps of 2, then
  `stopping growth after 5 expansions with no valid-count increase (valid=4)`. **With 56 source patches loaded, no
  candidate at the growth fringe had even TWO patches supporting it.** The library is not merely short of six-fold
  agreement; at the places growth wants to go it has none.
- Measured with the same instruments and reported as what it is, not against part 3's bars: p90 sag **3.16 µm** (better
  than the w040 control's 9.9), p90 anisotropy 8.38, 7 transverse contacts — on a **121-node** grid, which is far too
  small for those percentiles to mean much, and that is the honest caveat rather than a favourable reading.
- Also established while checking this: `normal_grid_path` IS read by the CLI tracer (`core/src/GrowPatch.cpp:3432`),
  which stage 1 uses, so the RULES note that normal grids are mandatory stands. Stage 2 grows through
  `grow_surf_from_surfs` in `GrowSurface.cpp`, which does not read that key at all — the consensus stage takes its
  orientation from the source patches themselves. I record this because I briefly believed the opposite after a grep
  that missed `GrowPatch.cpp`, and a wrong retraction would have been as damaging as a wrong claim.

## R-BEST  The candidate-grade reader on the geometrically pristine surfaces (declared 2026-09-18 19:55 UTC, population fixed BEFORE the reads)
- **Why.** The recipe screens with PLAIN inference and reserves `--tta-mirror` for candidates, because the frozen rule
  levels were validated on plain maps and TTA costs 4x. TTA is nonetheless the better reader on unlabelled text — it is
  what raised the w028 judge from 0.784 to 0.823, and it is a promotion already on record. R-CROSS now identifies, on
  geometry alone, the handful of our surfaces that are as clean as the ground-truth control. Those deserve the better
  reader.
- **Population, computed and written here before any read, from quantities that mention no ink at all:** area
  **>= 4 cm²**, a non-VOID read outcome, and a transverse crossing rate **<= 1.42 sites/cm²** — the w040 known-text
  control's OWN measured rate, so the bar is "as clean as ground truth or cleaner". It selects **3 surfaces, 14.6 cm²**:

  | scroll | patch | area | sites/cm² | p90 sag | current verdict |
  |---|---|---|---|---|---|
  | PHerc0358 | auto_grown_20260917230010114 | 4.85 cm² | 0.00 | 22.6 µm | NOT ESTABLISHED |
  | PHerc0826 | auto_grown_20260917043355441 | 4.82 cm² | 0.00 | 16.0 µm | NOT ESTABLISHED |
  | PHerc0358 | auto_grown_20260918104037671 | 4.89 cm² | 0.61 | 17.9 µm | BLANK |

- **What it is and is not.** It is the recipe's own candidate-grade reader applied to a pre-registered subset, under its
  own ledger key `ink9um_seed42+tta`, both depth orders, seed42. **Rule 5.5 is untouched — no level, unit or adjacency
  requirement moves**, and the plain reads of these three surfaces stand in the ledger exactly as recorded. There is no
  pass/fail bar here because a read is not a bar: what is declared is the POPULATION, so the result cannot be
  cherry-picked afterwards, and that any flagged unit is handled by rule 5.5 as written, including protocol 9 and a
  seed43 confirmation on a PROMISING CANDIDATE.
- **Cost is bounded by the population being fixed first:** 3 reads, 14.6 cm². If the same selection later admits more
  surfaces because new traces are cleaner, those are read too — the rule is the rule, not the list.
- `gates/ggp/rbest_population.json`.

### R-BEST correction, before any of its reads ran (2026-09-18 20:00 UTC)
- Checking the ledger before starting: **one of the three is already on record under `ink9um_seed42+tta`** —
  `PHerc0826 auto_grown_20260917043355441`, read on 2026-09-17 when TTA was still the screening recipe (plain screening
  was adopted on 2026-09-18). Its TTA verdict is **NOT ESTABLISHED** and it stands as ledgered.
- So R-BEST adds **two** reads, not three. Recorded rather than silently run, and the population is unchanged.
- **It also means the strongest thing R-BEST could have shown has already been tested on the single cleanest surface in
  the corpus and did not produce a candidate**: the geometrically most pristine 4.82 cm² we have, read by the
  candidate-grade reader, is NOT ESTABLISHED. That is a real negative and it is stated here before the other two run,
  so it cannot be quietly dropped if they come back blank.

### Two integrity fixes to the agreement measure, both STRICTER, made after the milestone was declared (2026-09-18 20:20 UTC)
- The measure is G-GP part 4's milestone, so changing it after declaring the milestone needs stating. **Both changes
  reduce what counts as independent support; neither can make the milestone easier.** That is the only direction such a
  change may go, and it is the same direction as the matched-baseline correction in part 2.
  1. **Patches are keyed by their SEED, not by their directory.** Two traces grown from the same seed are one
     observation twice. This is not hypothetical: restarting the dense loop over an in-flight trace produced two traces
     of seed `4654 2468 5244` before I stopped the orphan, and without this they would have counted as two patches
     agreeing. A zero or missing seed falls back to the directory, so the team's placeholder `seed: [0,0,0]` never
     collapses their distinct published segments.
  2. **`*_cons` consensus outputs are excluded from the source population.** They are grown FROM these patches;
     counting them would feed a surface's own derivative back in as independent support for it.
- Both are tested (8 tests on this file), including that a placeholder zero seed does not merge distinct segments.
- **Live reading after the first campaign traces landed:** PHerc0826, 64 independent sources — six-fold agreement
  **1.71 cm²**, maximum agreement anywhere **8**, against the pre-campaign **1.15 cm²** and maximum 7. The milestone is
  4 cm² at six-fold. The curve, not this snapshot, is the declared deliverable.
- The dense queue now runs as **two parts** (seed index modulo 2) over a two-slot pool. Concentrated seeding is all on
  one scroll, so a second concurrent trace costs no extra normal grids — both read the same cache — which is why
  widening the pool is safe here and was not for the breadth queues.

### How much on-sheet canvas a patch actually delivers (descriptive, 2026-09-18 20:30 UTC; gates nothing)
- Patch area is not read area. Over the 40 non-VOID reads carrying both: the on-sheet fraction of patch area has median
  **0.643** (p10 0.532, p90 0.966), and the on-sheet canvas delivered has median **3.16 cm²**, p90 4.17, max 7.88.
[line withheld: prize-candidate detail under review]
- A few fractions exceed 1.0 (up to 1.07) because on-sheet area is counted from the render's own pixels while the
  denominator is the tifxyz area estimate. Noted as a measurement quirk, not chased.
[line withheld: prize-candidate detail under review]
  insufficient, since a 4 cm² consensus surface at a 64 % on-sheet fraction delivers only ~2.6 cm² to the reader. It is
  not insufficient: the prize asks for ten legible letters **within** a 4 cm² area, not for 4 cm² of canvas, and
  2.6 cm² clears rule 5.5's three-unit minimum with room. The milestone stands unchanged.
- The R-BEST surface now reading, `PHerc0358 auto_grown_20260917230010114`, is on the low side at 1.88 cm² on-sheet from
  4.85 cm² — but by every geometric measure it is the best canvas in the corpus: **0.00 self-intersections/cm²**, p90
  sag 22.6 µm, crest ratio 1.897, and on-sheet CT std **42.9 against the w040 known-text reference's 43.1**.

### Published team canvas is exhausted (re-verified 2026-09-18 20:40 UTC by listing the bucket)
- Among the 23 eligible volumes only three publish surface segments, and we hold all of them: **PHerc1447** 37 unique
  uuids (38 local dirs, the extra being an `_inp_hr` variant), **PHerc1203** 22, **PHerc0800** 6. Every one is read or
  sitting in the R-CREST-POWER queue.
- So there is no remaining free, team-grade canvas to read — which matters because R-CROSS showed the team's segments
  are the geometrically clean ones (median 0.00 self-intersections/cm² against our 262.61). Any further sound canvas has
  to be built, not fetched. That is the concentrated-seeding campaign, and it is the correct place for the compute.

### `vc_tifxyz_winding` is built and is deliberately NOT being declared as a measure (2026-09-18 20:45 UTC)
- It writes a per-node `winding.tif`, a visualisation, and `wind_err.tif` (the deviation of the winding gradient from 1)
  into the current directory. A winding-span statistic would fail for the same reason R-WRAP did: a real sheet followed
  across a 2 cm patch on a ~5 cm-radius scroll legitimately advances its winding, so span does not separate good from
  bad. `wind_err` is a local consistency measure and would be a better version — but it would be measuring the same
  thing R-CROSS already measured with a cleaner argument (a self-intersection is physically impossible; a gradient
  deviation is a threshold).
- **So no eighth geometry measure is declared.** Seven have been declared today, six failed, and the seventh answered
  the question. Building the tool was right; declaring another statistic because the tool exists would not be. Recorded
  as a decision rather than left as silence.

### A disk cleanup silently corrupted a result file (found and fixed 2026-09-18 21:00 UTC)
- The self-intersection reports had grown to **533 MB** and the box was at 4.9 GB free, below its own render floor. I
  gzipped every report over 100 KB, reclaiming 533 MB -> 57 MB. **`rcross_result.py` then skipped every compressed
  report**, silently shrinking the populations from 66 and 107 to **55 and 17**, and **overwrote `rcross.json` with
  that partial result.**
- It was caught for one reason only: I re-ran the scorer after the cleanup and read its output. Nothing else would have
  noticed — the file is machine-written, the numbers were plausible, and RULES already held the correct figures in
  prose, so the two would have disagreed silently.
- **Fixed and verified.** The scorer now reads `.json` and `.json.gz` alike, and the patch key is taken before the
  extension so `.gz` cannot leak into it. Regenerated, the numbers are **identical to those recorded before the
  cleanup**: control 62 sites; team n=66, median 0.00/cm²; ours n=107, median 262.61/cm²; and the declared split
  reproduces exactly — HIGH n=45 at 86.7 % unreadable, LOW n=56 at 46.4 %, ratio **1.87x**, NOT ADMITTED. Three tests
  pin the compressed path.
- **Standing practice from this, and it costs seconds:** after any cleanup that touches a directory a scorer reads,
  re-run that scorer and compare its output against the numbers recorded in RULES. A cleanup is an edit to the data,
  and an edit to the data is an edit to the result.

### Duplicate traces of one seed, twice in one evening (fixed at source 2026-09-18 21:15 UTC)
- The supervisor restarts any loop holding a stale `HTTPS_PROXY`. That **kills the loop but not its in-flight docker
  trace**, which is then orphaned: it will never write its `.done` marker, and the flock slot it held is released with
  it. The restarted loop takes the freed slot and traces the **same seed again**. It happened twice this evening — once
  when I restarted the loop by hand, once when the supervisor did it after a worker restart — producing two live traces
  of seed `4654 2468 5244` and two of `4691 2284 3125`.
- **Why it matters beyond wasted CPU:** two traces of one seed are the same observation twice, and G-GP part 4's
  milestone is a count of how many patches agree. `patch_agreement.py` already refuses to count them twice (it keys
  patches by seed), but a measure defending itself against bad inputs is the second line, not the first.
- **Fixed at source:** before taking a seed, the dense loop scans the running tracer argv for a trace of that same seed
  into the same target directory and **waits for it** rather than starting a duplicate; it then re-checks the `.done`
  marker and releases its slot if the orphan finished the work. Six tests on this file.
- The four live duplicates were resolved by killing the two orphans (13–14 minutes of trace work each) and keeping the
  traces whose loops are intact, because clean state is worth more than the sunk time.

### The stale-proxy restart destroyed 77 minutes of R-DEPTH (fixed 2026-09-18 21:20 UTC)
- A worker restart moves this box's egress proxy, so the supervisor restarts any loop still holding the old
  `HTTPS_PROXY`. That is right for anything that fetches. **R-DEPTH fetches nothing** — it reads a local render, a local
  checkpoint and local labels — and the restart threw away **77 minutes** of a 2048x2048 inference that was most of the
  way through its first window. R-BEST does render, so it keeps the check and its own restart was justified.
- Fixed: R-DEPTH is exempt from the stale-proxy restart in the supervisor's experiment block, with two tests pinning
  both halves (R-DEPTH exempt, the check still present for R-BEST).
- **Both experiments are now supervised**, which they were not before: a genuine container reclaim would have lost them
  silently. Each is idempotent — R-DEPTH skips a window whose `.infer_complete` marker exists, R-BEST skips a surface
  that already has its `read_stats.json` — so resuming costs nothing and losing them costs hours.
- Same evening, same class: `rbest.sh` had treated the EXISTENCE of a read directory as a finished read, so when its
  queued instance was killed the loop silently skipped the surface it had been interrupted on. A directory means
  started, not done; the completion test is `read_stats.json`. That is the third instance today of a
  started-marker being read as a done-marker, after the stale render markers and the render sweeper.

## R-BEST-2  The better reader over ALL sound canvas (declared 2026-09-18 21:30 UTC, population fixed BEFORE the reads)
- R-BEST took the three surfaces as clean as the ground-truth control (<= 1.42 sites/cm²). This widens the selection to
  the **G-GP part 3 geometry bar already on record, <= 14.2 sites/cm² — ten times the w040 control's own rate** — which
  is the same number, declared earlier and for another purpose, so it is not a threshold chosen to suit a population.
- **Population, computed and written here before any read, from geometry and read outcome only, no ink statistic:**
  crossing rate <= 14.2/cm², a non-VOID read outcome, and **no TTA read already on record**. It selects **10 surfaces,
  42.6 cm²** across PHerc1447 (4), PHerc0358 (3), PHerc0826_small (3), PHerc1203 (1):

  | scroll | patch | area | sites/cm² | current verdict |
  |---|---|---|---|---|
  | PHerc1447 | team_20250703025628283 | 6.57 | 0.00 | BLANK |
  | PHerc0358 | auto_grown_20260917230010114 | 4.85 | 0.00 | NOT ESTABLISHED |
  | PHerc1447 | team_20250702235910292 | 3.95 | 0.00 | BLANK |
  | PHerc1203 | team_20250923163331524 | 3.89 | 0.00 | BLANK |
  | PHerc0826_small | auto_grown_20260918144212741 | 2.11 | 0.00 | BLANK (the fibre-weave interior surface) |
  | PHerc0826_small | auto_grown_20260918152701336 | 2.09 | 0.00 | BLANK |
  | PHerc0826_small | auto_grown_20260918155811706 | 2.09 | 0.00 | NOT ESTABLISHED (1 flagged unit) |
  | PHerc1447 | team_20250703034159599 | 7.40 | 0.41 | BLANK |
  | PHerc0358 | auto_grown_20260918104037671 | 4.89 | 0.61 | BLANK |
  | PHerc0358 | auto_grown_20260918123053821 | 4.78 | 3.97 | BLANK |

- Same terms as R-BEST: `ink9um_seed42+tta`, both depth orders, seed42, its own ledger key. **Rule 5.5 untouched** — no
  level, unit or adjacency requirement moves, every existing plain verdict stands as ledgered, and a flagged unit is
  handled exactly as the frozen rule says, including protocol 9 and a seed43 confirmation on a PROMISING CANDIDATE.
- There is no pass/fail bar because a read is not a bar. What is declared is the POPULATION, so no result can be
  cherry-picked after the fact.
- `gates/ggp/rbest2_population.json`.

### R-CREST-POWER's PHerc1203 read stopped to give the box to the candidate path (2026-09-18 21:40 UTC)
- **Measured, not assumed.** Instantaneous CPU over 5 s on this 4-core box: R-CREST-POWER PHerc1447 **119 %**,
  R-BEST **117 %**, R-CREST-POWER PHerc1203 **103 %**, dense trace 14 %, R-DEPTH 13 %. Nice values were not producing
  the split I had assumed — a nice-19 job was taking MORE of the box than the nice-4 one, because these are
  multi-threaded and the weighting is per thread group, not per job.
- Two leftovers of already-paused work were killed first: the dense campaign's in-flight READ (64 %, which contributes
  nothing to the agreement milestone, that being a count of traces) and the trace belonging to the part-1 loop I had
  already stopped (44 %). That alone took R-BEST from **61 % to 117 %**.
- **Then the PHerc1203 R-CREST-POWER read was stopped, discarding 3 hours of compute.** R-CREST-POWER asks a
  methodological question — whether the crest veto discards readable canvas — on surfaces R-CREST vetoed and R-EYES
  showed to be cross-cuts and crumpled laminae. It cannot produce a prize candidate. R-BEST-2's ten sound-geometry
  surfaces can. The PHerc1447 read keeps running because it is nearer completion (4.6 h, forward map already written).
- **No bar and no verdict changes.** R-CREST-POWER is paused by a marker, not withdrawn; its declaration and ledger keys
  stand untouched and it resumes when the candidate path is clear. Recorded because discarding three hours of a
  declared experiment is a decision, not housekeeping.

### R-CREST-POWER phase 1 also paused; the box is now entirely candidate work (2026-09-18 21:55 UTC)
- The PHerc1447 `z_dbg_gen_00701` read was stopped after **4.8 hours**, its forward map written and its reverse pass
  incomplete, so the read cannot be scored and the time is lost. Same reasoning as the PHerc1203 member: R-CREST-POWER
  tests whether the crest veto discards readable canvas, on a surface R-EYES showed to be laminar strata seen edge-on
  with no fibre weave anywhere. It is a methodological result and cannot produce a prize candidate.
- **Both R-CREST-POWER queues are paused by marker, not withdrawn.** Their declaration, population and ledger keys are
  untouched and they resume by deleting `logs/rcrest_power_paused` and `logs/rcrest_power_1203_paused`. Total discarded:
  **7.8 hours** of a declared experiment, recorded here as a decision under an explicit deadline rather than left
  implicit in a process table.
- Measured afterwards: the box runs at **388 % of 400 %**, all of it R-BEST, R-BEST-2 and one dense trace. There is no
  spare capacity left to add a third read stream to — adding one would divide the same cycles, not create more.

### The submission path is verified working, before a candidate exists (2026-09-18 22:05 UTC)
- Re-ran the packager's verifier on the P-DRY package after a day of changes to the surrounding scripts:
  **21 checks, exactly 2 FAIL — "not eligible (section 1 list)" and "fewer than 10 letters"** — which is precisely what
  P-DRY declared the dry run must fail on and nothing else. The 1 cm scale bar measures 1068 px against the expected
  `round(10000/um) = 1068`, in a footer margin outside the map area; every PNG's map pixels are byte-identical to the
  window TIFFs; the checkpoint, exact call and Docker image are recorded.
- Checked now rather than at the moment a candidate appears, because a packager that breaks at 23:00 costs the night.

### Gate A's control stack removed for disk, and the standing practice applied (2026-09-18 22:20 UTC)
- `controls/w040/stack.zarr` (1.21 GB) is the team's native w040 surface volume, Gate A's input. Gate A is complete and
  its numbers are stored; the stack is re-fetchable from `fetch_stack.sh` and `chunk_urls.txt`, both kept. Removed to
  hold the box above its 5 GB render floor with five R-BEST-2 renders still to make. Free disk 5.3 GB -> **7.4 GB**.
- **Per the practice written after the R-CROSS incident, every result that reads w040 was checked afterwards**, and all
  are unchanged: Gate A 0.99659 forward / 0.49633 reverse (stored); R-DEPTH's centre window still 0.46808 from the Gate
  B render, which is a different file; G-GP Reference A still measures stretch 1.000, anisotropy p90 1.034, p90 sag
  9.93 µm from `controls/w040/mesh`, which was kept.
- Also checked before it could bite: **five of the ten R-BEST-2 surfaces carry a stale `render.zarr.complete` marker
  with no render**, from earlier `--delete-renders` reads. `run_patch_dir.py` already drops both markers when the render
  directory is absent, so they re-render rather than reporting "complete" and reading nothing — the defect recorded
  earlier today is genuinely fixed, and none of the five carries a `render_source.json`, so no team-provenance render
  will be silently replaced by one of ours.

### G-GP part 4, the declared curve as it stands (2026-09-18 22:35 UTC)
- Six-fold agreement on PHerc0826, measured with the same script and the same 24-voxel cell throughout, as campaign
  traces land: **0 traces 1.15 cm² (max agreement 7) -> 1 trace 1.71 cm² (max 8) -> 3 traces 2.13 cm² (max 9)**.
  Milestone 1 is 4 cm². The two counting fixes (key by seed, exclude `*_cons`) were in force from the second reading on
  and both reduce what counts, so the rise is not an artefact of loosening the measure.
- At roughly +0.3 to +0.5 cm² per trace the milestone is about four more traces away, which at the current one-slot
  rate is one to two hours. **Concentrated seeding is doing what the arithmetic said it would**, and the curve — not
  any single reading — is the declared deliverable.

### G-GP part 4 curve, four traces in (2026-09-18 23:05 UTC)
- Six-fold agreement on PHerc0826, same script and same 24-voxel cell throughout, both counting fixes in force:
  **0 traces 1.15 cm² (max 7) -> 1 trace 1.71 (max 8) -> 3 traces 2.13 (max 9) -> 4 traces 2.43 cm².**
  Steady at about **+0.30 cm² per trace**, so the 4 cm² milestone is roughly five more traces away. The campaign runs
  on one slot while the two TTA reads have the box, at 15-25 minutes per trace.
- Recorded now rather than at the end: the curve is the declared deliverable whether or not the milestone is reached,
  and an interrupted session should not lose it.

### G-GP part 4: the curve DECELERATES, my projection was wrong, and the declaration already says what to do (2026-09-18 23:25 UTC)
- **The projection I gave was contradicted by the next two points and I am correcting it, not restating it.** Six-fold
  agreement by campaign trace: 1.15 -> 1.71 (+0.56) -> 2.13 over two traces (+0.21 each) -> 2.43 (+0.30) -> **2.49
  (+0.06)**. I had said "+0.30 cm² per trace, about five more traces". At +0.06 the 4 cm² milestone would need roughly
  twenty-five more, and the campaign has twenty seeds left. **Milestone 1 is unlikely to be met by this campaign.**
- The traces themselves are fine — five landed at 5.01, 5.17, 5.05, 5.42 and 4.84 cm². They overlap the source patch's
  core, where agreement is now deep (**max agreement anywhere 11, up from 7 before the campaign**), and spread outward
  where it is not. Six-fold agreement saturates on the shared core rather than growing with it.
- **What the full threshold profile says**, measured now: >= 2 patches **44.07 cm²**, >= 4 **7.14 cm²**, >= 6 2.49 cm²,
  >= 8 0.95 cm². **At threshold 4 the library already supports 7.14 cm², well past the 4 cm² the milestone asks for.**
- **The declaration written before the campaign covers this case verbatim:** "The consensus threshold used is recorded
  with the result; **the geometry bars, not the threshold, are the test**, so running at a threshold our library
  supports is not tuning a bar — the bars do not move." So stage 2 now runs at **`consensus_default_th: 4`**, recorded
  here before the run, with milestone 2's bars completely unchanged: output area **>= 4 cm²**, transverse crossing rate
  **<= 14.2 sites/cm²**, p90 sag **<= 55.5 µm**. A surface that fails any of the three fails, whatever its threshold.
- Four-fold consensus is weaker than the team's six-fold and that is stated plainly rather than buried: it is a weaker
  guarantee against a trace folding through itself, which is exactly why the self-intersection bar is applied to the
  output and is the thing that decides.

### G-GP part 4, milestone 2 result at threshold 4 (measured 2026-09-18 23:35 UTC): FAILS on area, PASSES both geometry bars
- `vc_grow_seg_from_segments` at `consensus_default_th: 4`, six source surfaces (the seed patch plus five campaign
  traces), seeded at 3590 2095 4179, against the local prediction box. Scored against milestone 2's three declared bars:

  | bar | required | measured | |
  |---|---|---|---|
  | output area | >= 4 cm² | **2.045 cm²** | **FAIL** |
  | transverse crossings | <= 14.2 /cm² | **0 sites, both triangulations** | PASS |
  | p90 sag | <= 55.5 µm | **4.64 µm** | PASS |

- **Milestone 2 FAILS.** It required all three and the area bar is missed by half. Recorded as a failure; nothing is
  retuned and no bar moves.
- **What passed is worth stating precisely.** The consensus surface has **zero self-intersections** — cleaner than the
  w040 known-text control itself, which carries 62 sites at 1.42/cm² — and a p90 sag of **4.64 µm** against that
  control's 9.93 µm, on the same 20-voxel node spacing so the comparison is direct. Our single traces sit at a median
  262.61 crossings/cm² and 33.2 µm sag. **The consensus stage does exactly what R-CROSS predicted it would: it produces
  geometrically pristine surfaces out of traces that individually fold through themselves. The limit is size, not
  quality.**
- The growth log says why it stopped: `best th: 0` at the fringe through 950 generations, then five expansions with no
  valid-count increase. Even at four-fold, support runs out at the edge of the shared core — the same finding as part
  3b, one threshold down.
- **The surface is read like any other surface**, under its own ledger key, with rule 5.5 untouched. 2.045 cm² clears
  the frozen rule's own 1.5 cm² minimum for a three-unit cluster, so a candidate is not arithmetically excluded. The
  read is not owed by milestone 2 — that failed — and its verdict is ledgered on the same terms as every other read.
- Defect fixed on the first attempt: the source directory gathered its surfaces as ABSOLUTE symlinks, which do not
  resolve inside the container (it mounts the data root at `/data`), so the tool reported "no source surfaces found".
  They are relative now, and the runner proves every link resolves to an `x.tif` before spending any growth.

### R-BEST result on the corpus's best canvas (2026-09-18 23:50 UTC): NOT ESTABLISHED, and it is a clean negative
- `PHerc0358 auto_grown_20260917230010114`, read with `--tta-mirror`, seed42, both depth orders, under
  `ink9um_seed42+tta`. This is the surface every geometric instrument picks out: **0.00 transverse
  self-intersections per cm²** (the w040 known-text control itself has 1.42), p90 sag 22.6 µm, crest ratio **1.90**,
  and on-sheet CT texture **42.9 against the known-text reference's 43.1**.
- **Verdict NOT ESTABLISHED: 0 flagged units of 2 valid.** The two valid 0.5 cm² units have forward-minus-reverse
  margins of **−0.0082** and **−0.0244** — negative, i.e. the reverse depth order reads marginally higher than the
  forward one. The depth-swap tripwire is clear. It is NOT ESTABLISHED rather than BLANK only because 2 valid units is
  1.0 cm², under the frozen rule's own 1.5 cm² minimum for a blank call; on-sheet area was 1.88 cm² of a 4.85 cm² patch.
- **What this removes.** Geometry was the live explanation for a blank corpus, and on this surface geometry is as good
  as ground truth by every measure we have. The better reader on the best canvas finds **no forward signal at all**,
  not a weak one. That is worth more than another ambiguous read: it says the blankness here is not a geometry artefact.
- It does not generalise beyond the ~23 cm² of sound interior canvas already recorded. One clean negative on 1.88 cm²
  is one clean negative, and the corpus limit written earlier stands unchanged.

### Both R-BEST loops were duplicating an in-flight read (found and fixed 2026-09-19 00:00 UTC)
- `rbest.sh` and `rbest2.sh` retry every 300 s and skip a surface that has a `read_stats.json`. **A read IN PROGRESS
  has no `read_stats.json` either**, so pass 2 started a second inference on the same render: two `infer` processes
  writing one output directory, one of them 4595 s in and the other 98 s. Caught by looking at the process table, not
  by any check in the code.
- This is the same class as the three earlier today — a started-marker read as a done-marker — but worse, because the
  duplicate does not merely waste a core, it races the first process on the same output files. The maps that decide a
  verdict were being written twice concurrently.
- **Fixed in both loops:** before starting, each checks the process table for an `infer` already running on exactly
  that surface's `render.zarr` and skips it, leaving it counted as outstanding so the next pass retries. The older
  process (most progress) was kept and the 98-second duplicate killed. Nine tests on this file now, including that the
  match is made on the exact render path rather than a loose pattern.
- No verdict is affected: the duplicate was killed before either process reached the reader, and the surviving read is
  the one that had been running for over an hour.

### And the deceleration was my sampling error, not the curve (corrected 2026-09-19 00:10 UTC)
- Half an hour ago I recorded that the six-fold agreement curve had decelerated to **+0.06 cm²** per trace and that
  milestone 1 was "unlikely to be met by this campaign". **That reading was taken while the fifth trace was still
  growing.** Sampled at completed traces the curve is:
  **1.15 -> 1.71 -> 2.13 -> 2.43 -> 2.71 -> 3.15 cm²** over 0, 1, 3, 4, 5, 6 traces, with max agreement anywhere going
  **7 -> 13**. That is about **+0.4 cm² per completed trace**, not +0.06, and the milestone is roughly two traces away.
- **Both of my projections were therefore wrong in opposite directions within an hour** — first too optimistic on a
  linear fit through four points, then too pessimistic on a single mid-trace sample. Recorded because the discipline
  that matters here is not making the projection at all: the curve is the deliverable, and it is measured at completed
  traces from now on.
- Nothing follows for the threshold-4 run already recorded. Milestone 2 failed on area at 2.045 cm² and that stands;
  it was run under the clause that says the geometry bars, not the threshold, are the test, and that clause does not
  depend on whether milestone 1 is eventually met.
- Current profile: >= 4 patches **7.45 cm²**, >= 6 **3.15 cm²**, >= 8 **1.44 cm²**.

## G-GP part 4, MILESTONE 1 MET (measured 2026-09-19 00:35 UTC)
- Declared bar, quoted exactly from above: "**>= 4 cm² of cells at agreement threshold 6**, within this campaign's
  patches plus the existing ones", on the same script and the same 24-voxel cell as part 3.
- **Measured: 4.05 cm² at threshold 6, over 10 campaign traces.** 8 017 cells of 447 000, max agreement anywhere 13.
  The declaration carries no connected-component clause — that phrasing appeared only in my task list, and RULES is the
  record — so the bar is met as written and not on a looser reading.
- Curve at completed traces: **1.15 -> 1.71 -> 2.13 -> 2.43 -> 2.71 -> 3.15 -> 3.29 -> 3.55 -> 3.71 -> 4.05 cm²**
  over 0, 1, 3, 4, 5, 6, 7, 8, 9, 10 traces, max agreement 7 -> 13. Both counting fixes (key by seed, exclude `*_cons`)
  were in force throughout and both reduce what counts.
- **Concentrated seeding worked.** Seeds 320 voxels apart across a 48-voxel wrap spacing could be six wraps apart; seeds
  taken from one patch's own surface points cannot be. That was the whole argument, written before the campaign, and
  the measurement follows it.
- Milestone 2 now runs at the team's own published `consensus_default_th: 6`, with its three bars unchanged: output
  area >= 4 cm², transverse crossings <= 14.2/cm², p90 sag <= 55.5 µm. The earlier threshold-4 run stands as recorded
  (FAILED on area at 2.045 cm², passed both geometry bars).

### G-GP part 4, milestone 2 at the team's threshold 6 (measured 2026-09-19 00:40 UTC): FAILS on area at 3.648 cm², passes both geometry bars

  | bar | required | measured | |
  |---|---|---|---|
  | output area | >= 4 cm² | **3.648 cm²** | **FAIL** |
  | transverse crossings | <= 14.2 /cm² | **0 sites, both triangulations** | PASS |
  | p90 sag | <= 55.5 µm | **4.94 µm** | PASS |

- **Milestone 2 FAILS.** It requires all three and the area bar is missed by **0.35 cm²**. Recorded as a failure. The
  bar does not move, and "close" is not a pass.
- Against the threshold-4 run two hours earlier the output nearly doubled — **2.045 -> 3.648 cm²** — on 11 source
  surfaces instead of 6, at the STRICTER six-fold threshold. Both runs returned **zero self-intersections** and a p90
  sag near 4.9 µm, half the w040 known-text control's 9.93 µm on identical node spacing.
- The growth log again ends with five expansions and no valid-count increase: support runs out at the fringe of the
  shared core, and the core grows as traces are added. Ten campaign traces are in; **fifteen seeds remain**, so the
  measurement to make is simply whether more traces carry the consensus past 4 cm². No projection is offered — the last
  two I made were wrong in opposite directions inside an hour.
- **3.648 cm² is the largest geometrically sound surface this project has produced**, and it is read on the same terms
  as every other surface, under its own ledger key, with rule 5.5 untouched.

## G-GP part 4, MILESTONE 2 MET (measured 2026-09-19 01:25 UTC)
- `vc_grow_seg_from_segments` at the team's own published **`consensus_default_th: 6`**, 13 source surfaces (the seed
  patch plus twelve campaign traces), seeded at 3590 2095 4179, against the locally materialised prediction box.

  | bar (declared before the campaign, never moved) | required | measured | |
  |---|---|---|---|
  | output area | >= 4 cm² | **4.077 cm²** | **PASS** |
  | transverse crossings | <= 14.2 /cm² | **0 sites, both triangulations, `clean=True`** | **PASS** |
  | p90 sag | <= 55.5 µm | **4.91 µm** | **PASS** |

- **All three bars pass. Milestone 2 is MET.** The two earlier attempts are on record as failures and stay there:
  threshold 4 with 6 sources gave 2.045 cm², threshold 6 with 11 sources gave 3.648 cm². The difference is the number
  of agreeing source traces, nothing else — same tool, same parameters, same seed, same bars.
- **What this surface is.** 4.077 cm² of consensus geometry with **zero self-intersections** — the w040 known-text
  control itself carries 62 — and a p90 sag of **4.91 µm** against that control's 9.93 µm on identical 20-voxel node
  spacing. Our individual traces sit at a median 262.61 crossings per cm² and 33.2 µm sag. This is the first surface
  this project has produced that matches the Grand Prize input in kind: large, clean and physically possible.
- Six-fold agreement stood at **4.91 cm²** over twelve campaign traces when this ran.
- **It is a geometry result and nothing more.** It is not a candidate, not a letter, and not a submission. It goes
  through the unchanged pipeline — QC, R-CREST, render, both depth orders, rule 5.5 — under its own ledger key, and
  whatever the reader says is what gets ledgered.

### The reader was silently skipping every consensus surface (found and fixed 2026-09-19 01:35 UTC)
- `run_patch_dir.py` enumerated only `auto_grown_*` and `team_*` children. **`vc_grow_seg_from_segments` names its
  result `auto_trace_<stamp>_seed_...`**, with a smaller `auto_grown_` companion beside it. So every consensus surface
  stage 2 produced was skipped — including the **4.077 cm² surface that met milestone 2**. The run printed its header
  and exited with nothing to do, and I reported it as "in the reader" for half an hour on the strength of that header.
  The read that was actually running was the 1.96 cm² threshold-4 companion.
- Two fixes, both tested: `auto_trace_*` is enumerated, and **a `--only` that names a patch the directory does not
  contain now exits with an error naming it** instead of quietly reading zero patches. The second is the general
  lesson — this is the fifth started-vs-done or silent-skip defect today, and the pattern is always that an absence
  reads as a success.
- **The threshold-4 consensus surface's verdict, now that it has one:** `auto_grown_20260918202108819`, 1.28 cm²
  on-sheet, crest 3.28, CT texture 35.6 — **NOT ESTABLISHED, 0 flagged units of 1 valid, margin −0.0021**, tripwire
[line withheld: prize-candidate detail under review]
  minimum. A second clean negative on pristine consensus geometry.

## G-GP part 4 complete: 25 traces, and the largest clean surface yet (2026-09-19 01:25 UTC)
- **The campaign finished all 25 seeds.** Final agreement profile on PHerc0826, 91 independent source patches, same
  script and same 24-voxel cell throughout: **>= 4 patches 13.10 cm², >= 6 7.65 cm², >= 8 5.29 cm², >= 10 3.69 cm²,
  maximum agreement anywhere 30** (it was 7 before the campaign began).
- Six-fold agreement by completed campaign trace: 1.15 -> 1.71 -> 2.13 -> 2.43 -> 2.71 -> 3.15 -> 3.29 -> 3.55 -> 3.71
  -> 4.05 -> 4.91 -> 5.31 -> 5.37 -> 5.43 -> 5.54 -> 5.90 -> 6.71 -> **7.65 cm²**. Milestone 1 was crossed at ten traces
  and the curve kept climbing to the end of the seed list.
- **Final consensus surface at the team's own `consensus_default_th: 6`, 26 sources: area 5.162 cm², p90 sag 5.11 µm,
  and the self-intersection census reports it clean.** Against milestone 2's unchanged bars (>= 4 cm², <= 14.2
  crossings/cm², <= 55.5 µm sag) that is a pass on all three, and it is **26 % larger than the 4.077 cm² surface that
  first met them**.
- Progression of the consensus stage as sources were added, all at the same seed and the same parameters:
  **2.045 cm² (6 sources, th 4) -> 3.648 (11, th 6) -> 4.077 (13, th 6) -> 5.162 (26, th 6)**, every one of them with
  **zero transverse self-intersections** and a p90 sag between 4.6 and 5.1 µm — about half the w040 known-text
  control's 9.93 µm on identical node spacing.
- The geometry problem this project started the day with is solved and measured. What the reader makes of the canvas
  is a separate question, and the answer so far is three clean negatives.

### The milestone-2 consensus surface has been read (2026-09-19 01:30 UTC): NOT ESTABLISHED, 0 flagged of 2 valid
- `PHerc0826_cons_part4 auto_trace_20260918212225942...` — the 4.077 cm² surface that met all three geometry bars,
  read with `--tta-mirror`, seed42, both depth orders. **2.71 cm² on-sheet, crest 2.96, CT texture 28.8, tripwire
  clear.** Two valid 0.5 cm² units, margins **+0.0331** and **+0.0029**, neither reaching the frozen rule's 0.08.
  **0 flagged units.** NOT ESTABLISHED rather than BLANK because 1.0 cm² of valid units is under the 1.5 cm² minimum.
- +0.0331 is the largest forward-minus-reverse margin among tonight's consensus reads and it is still less than half
  the bar. It is recorded as a number, not as a hint; a margin under the bar is not a weak detection, it is no
  detection, and the bar does not move.
- **Four clean negatives now, all on canvas at or better than ground-truth geometry:** the corpus's cleanest traced
  surface (0 of 2, margins −0.008/−0.024), the threshold-4 consensus (0 of 1, −0.002), `auto_grown_20260918104037671`
  (BLANK, 0 of 3, +0.014/−0.005/−0.012), and this one (0 of 2, +0.033/+0.003).
- The 5.162 cm² consensus surface is next.

### Container reclaimed at 2026-09-19 01:35 UTC; what was lost and what survived
- Uptime reset to 1 minute: the container was reclaimed and every running job killed. Lost: the PHerc1447
  `team_20250703025628283` TTA read at **4 h 10 m** (its forward map was written but the reverse was not, so the read
  cannot be scored and the time is gone), and the just-started read of the 5.162 cm² consensus surface.
- **Survived, because it had finished and been ledgered:** the milestone-2 4.077 cm² consensus read (NOT ESTABLISHED,
  0 flagged of 2 valid), `auto_grown_20260918104037671` (BLANK, 0 of 3), and every result recorded above. The ledger
  is at 171 lines and the working tree was clean at the moment of the reclaim, so nothing written is missing.
- The supervisor restored the loops on its first run. The dense campaign needs nothing — all 25 seeds are traced. The
  consensus read is restarted by hand; it is not in the supervisor's experiment block, which is a gap worth closing if
  another long consensus read is queued.

### Reclaims are shorter than the reads; switching the consensus surface to the PLAIN recipe (2026-09-19 00:40 UTC)
- Third container reclaim in about an hour (uptime 1 min again). A TTA read of a 5 cm² surface takes ~80 minutes on
  this box and has now been killed three times before finishing; the PHerc1447 `team_20250703025628283` TTA read has
  been killed three times as well, at 4 h 10 m, 45 m and 45 m.
- **The fix is the recipe, not a longer wait.** METHOD's screening recipe is PLAIN inference — TTA is reserved for
  candidates, costs 4x, and was never required for a surface that is not in the R-BEST or R-BEST-2 populations. The
  consensus surface is read the standard way: `ink9um_seed42+plain`, both depth orders, rule 5.5 unchanged. That is
  ~20 minutes and fits inside the reclaim interval. If any unit flags, the TTA and seed43 confirmation follow under
  protocol 9, which is what TTA is for.
- R-BEST-2's PHerc1447 entry is paused for the same reason: a 6.57 cm² TTA read cannot complete between reclaims, and
  it was consuming a core on every restart. It stays in the declared population and resumes when the box is stable.

## The 5.162 cm² consensus surface, read (recorded 2026-09-19 01:55 UTC; no bar changes)

- `PHerc0826_cons_part4/auto_trace_20260918232203445_seed_3590p000_2095p000_4179p000` — 26 sources at the team's own
  six-fold consensus threshold, zero transverse self-intersections, p90 sag 5.11 µm — read plain, seed42, both depth
  orders, ledger key `PHerc0826|auto_trace_20260918232203445_seed_3590p000_2095p000_4179p000|0|ink9um_seed42+plain|both`.
- **Result: NOT ESTABLISHED.** 3.2194 cm² on-sheet, crest ratio 2.964 (passes), 2 valid 0.5 cm² units of 8, **0 flagged**.
  Unit (1,2) forward 0.4391 margin **+0.0053**; unit (1,3) forward 0.4508 margin **+0.0014**. Depth-swapped order gives
  the mirror image (−0.0053, −0.0014), as it must. Whole-map forward mean 0.3906, reverse 0.3939.
- This is the fifth consecutive clean negative on geometry that meets every G-GP bar. It is the largest and cleanest
  canvas the project has built, and it contains no ink signal this reader can see.
- **The number that matters is not the verdict but the pair.** Forward 0.4391/0.4508 sits *at or above* the level of the
  known-TEXT w028 units that calibrated rule 5.5 (forward 0.4392, R-5.5 self-test on record at line 110) — while their
  margin was **+0.1567** and ours is **+0.0053**. Our surfaces return a text-level forward value with no depth
  asymmetry at all. That is the anomaly R-SYM below is declared to measure.

## R-SYM  Is the reverse map a copy of the forward map? (declared 2026-09-19 01:58 UTC, BEFORE any number is seen)

- **The question.** Rule 5.5 compares the *means* of the forward and reverse maps. Two very different situations give
  the same near-zero margin: (a) the model returns one depth-indifferent answer, the reverse map being a near-copy of
  the forward map — a response to structure that does not care which way the stack runs; or (b) the model returns two
  genuinely different answers that happen to share a mean, in which case a mean-margin test can hide a localised
  signal. On the w040 known-text control the reverse pass collapses to a flat, label-blind map (Gate A AUC 0.4963,
  mean_on_ink 0.3041 against mean_on_blank 0.3036) while the forward pass separates ink at 0.7579 against 0.2517. Which
  of (a) or (b) describes our corpus has never been measured.
- **The statistic.** Pearson correlation `r(forward, reverse)` computed pixel-wise over the pixels of the **rule 5.5
  valid 0.5 cm² units** — a region that is ≥ 90 % on-sheet by construction and whose boxes are already recorded in every
  `read_stats.json`. The same definition is applied to the control and to every corpus read, with no exception. Reads
  with no valid unit, or whose forward/reverse maps are no longer on disk, are excluded and counted as excluded.
- **The control anchor, and the condition for R-SYM to mean anything at all.** On the Gate B render — our own
  `vc_render_tifxyz` render of the w040 known-text mesh crop, plain seed42, both orders, the same maps Gate B scored —
  `r_control` must be **≤ 0.30**. Reverse carries no label information there (AUC 0.4963), so if it still correlates
  with forward above 0.30 the statistic does not separate a known-text read from anything, and **R-SYM is recorded as
  an unusable indicator and nothing follows from it** — exactly as R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE, R-WRAP and
  R-ROWS were recorded. The control result is reported first and prominently either way.
- **Given the anchor holds**, a corpus read is **DEPTH-SYMMETRIC** if `r ≥ 0.70` over its valid units (≥ 49 % shared
  variance).
  - **Outcome DS-ALL** — ≥ 90 % of eligible corpus reads are DEPTH-SYMMETRIC: the finding on record is that our renders
    draw one depth-indifferent response out of this model, that rule 5.5's mean-margin bar is measuring exactly what it
    was built to measure, and that no read on record hides a localised signal behind a cancelled mean. Nothing changes.
  - **Outcome DS-SPLIT** — any read with `r < 0.30`, i.e. control-like: it is **named**, read again under the
    confirmatory recipe (seed43, TTA) and put through the geometry half of protocol 9. **Nomination is not flagging.**
    Rule 5.5 is unchanged and remains the only thing that can produce a PROMISING CANDIDATE.
- **R-SYM changes no bar, no verdict already on record, and no map.** It is descriptive. It can only nominate a surface
  for a second look under recipes already on record.

- **R-SYM RESULT (2026-09-19 02:05 UTC). The control anchor HOLDS and the outcome is DS-SPLIT.**
  - **Control first, as declared.** Gate B, our own render of the w040 known-text mesh crop, plain seed42, both orders:
    over its 4 valid 0.5 cm² units (2 280 100 px) `r(forward, reverse) = **−0.0088**`; over the whole on-sheet area
    (4 194 203 px) `r = −0.0122`. Well inside the ≤ 0.30 anchor. **R-SYM is a usable indicator.**
  - **Corpus: 9 reads measured, 133 excluded** — 92 have no 0.5 cm² table at all (VOID/UNREADABLE: the crest check
    stopped them before rule 5.5 was applied) and 41 have a table but no valid unit. The accounting is complete
    (9 + 92 + 41 = 142 `read_stats.json` on disk).
  - `r` runs **0.1153 to 0.5779, median 0.3043**. **DEPTH-SYMMETRIC (r ≥ 0.70): 0 of 9 — zero per cent.**
  - Four reads are control-like (`r < 0.30`) and are therefore **nominated**, as declared: PHerc0826
    `auto_grown_20260918144212741` (r 0.1153), `auto_grown_20260918152701336` (0.1804),
    `auto_grown_20260918155811706` (0.1855), `auto_trace_20260918232203445_seed_3590p000_2095p000_4179p000` (0.2464).
    Nomination is not flagging. No verdict changes. Rule 5.5 is untouched.
  - **What this refutes.** The hypothesis I was about to act on — that our renders draw one depth-indifferent response
    out of the model, so that the forward and reverse maps are near-copies whose means must cancel — is **false**.
    Not one read is depth-symmetric. The model returns two genuinely different answers on our surfaces, and those two
    answers happen to share a mean.
  - **What this opens.** Rule 5.5 compares the *means* of two maps that R-SYM has just shown to be largely independent.
    A mean over a 0.5 cm² unit (7.07 × 7.07 mm at 9.362 µm) can therefore cancel a *localised* forward-only signal:
    Herculaneum capitals are 2-4 mm, so a unit holding a few letters is mostly blank papyrus. Whether rule 5.5 as
    frozen is sensitive to text at realistic ink coverage has never been measured. It is measured next, on the control,
    as R-SENS — and R-SENS measures our own screen; it does not touch it.

## R-SENS  The ink-coverage floor of rule 5.5, measured on the control (declared 2026-09-19 02:10 UTC, BEFORE any number is seen)

- **The question R-SYM forced.** Rule 5.5 flags a 0.5 cm² unit when `forward mean >= 0.36` AND
  `(forward − reverse) mean >= 0.08`. Both are **means over a 7.07 × 7.07 mm square**. A Herculaneum capital is
  2-4 mm tall, and lines and columns are separated by blank papyrus, so a unit that holds real text is mostly blank.
  How much of a unit must actually be inked before the frozen levels fire? This has never been measured. It is a fact
  about **our own instrument**, not about the scrolls.
- **Two arms, both on the Gate B control** — our own `vc_render_tifxyz` render of the w040 known-text mesh crop, plain
  seed42, both depth orders, with the published `w040_inklabels.zarr` and `w040_supervision_mask.zarr` at slice 14,
  crop `1152 2048 2048 2048`: the same render, checkpoint, labels, slice and crop as Gate B and Gate A.
  1. **Analytic arm.** From Gate A's measured per-class levels on this control (forward mean_on_ink 0.7579,
     mean_on_blank 0.2517; reverse mean_on_ink 0.3041, mean_on_blank 0.3036), a unit whose ink area fraction is φ has
     `fwd(φ) = 0.7579φ + 0.2517(1−φ)` and `rev(φ) = 0.3041φ + 0.3036(1−φ)`. Solve both frozen levels for φ and report
     the two floors and the binding one.
  2. **Empirical arm.** Tile the control's valid area with 0.5 cm² windows at a **half-unit stride** (stride is an
     implementation choice and changes no threshold), keep windows that are ≥ 90 % on-sheet and ≥ 90 % inside the
     supervision mask, and for each report its true ink area fraction φ, its forward mean, its margin and whether the
     frozen levels fire. Report the smallest φ among firing windows and the largest φ among non-firing windows. Repeat
     at 1 cm² for the record.
- **R-SENS has no pass/fail bar because it tests nothing about the scrolls.** It is descriptive, like `good_canvas.py`.
  What follows from it is declared here, before the numbers:
  - If every control window with φ ≥ 0.05 fires, rule 5.5 is sensitive down to 5 % ink coverage, the screen is not
    hiding text at realistic coverage, and **every corpus negative on record stands exactly as read**.
  - If windows fail to fire up to some φ_max, then **rule 5.5 as frozen is blind below φ_max ink coverage on a
    control-contrast sheet**, and that number goes on the record as a measured limitation of the screen. It still does
    **not** move the bar: rule 5.5 is frozen and stays frozen, and every verdict already recorded stands as recorded.
    What follows instead is that a second indicator, **localised rather than averaged**, is needed so that real text is
    not forfeited by an averaging artefact — and that indicator (R-MARK) will be declared with its own control anchor,
    in writing, before it is run, and will nominate surfaces for a human look rather than flag them.
- **R-SENS alters no map, no verdict, no bar, and creates no candidate.**

- **R-SENS RESULT (2026-09-19 02:25 UTC). Arm 2 as declared cannot be run; arm 1 and a label-geometry measurement
  follow. No bar moves.**
  - **Arm 2 is empty, and why.** The declared window test needs a 0.5 cm² window that is ≥ 90 % inside the supervision
    mask. The w040 supervision mask covers **3.19 %** of its 6400 × 7980 canvas (**13.9 %** of the Gate B crop) and the
    w028 mask **1.19 %** of its 9355 × 7585 canvas: they are thin bands hugging the labelled text. **Not one 0.5 cm²
    window anywhere on either control is 90 % supervised**, so arm 2 returns zero eligible windows at 0.5 cm² and at
    1 cm². Recorded as an empty arm, not as a result.
  - **Arm 1, from Gate A's own measured per-class levels on this control.** forward ink **0.7579** / blank **0.2517**;
    reverse ink **0.3041** / blank **0.3036**. Under the area-mixture model `fwd(φ)=0.7579φ+0.2517(1−φ)`,
    `rev(φ)=0.3041φ+0.3036(1−φ)`: the forward level 0.36 needs **φ ≥ 0.2139**, the margin 0.08 needs **φ ≥ 0.2608**.
    **Binding floor φ ≥ 0.2608 — 26.1 % of a 0.5 cm² unit must be inked.**
  - **What real Herculaneum text actually supplies, measured on the same control's labels** (exact box sums over every
    window position by integral image; 40 797 996 positions at 0.5 cm²): the largest ink area fraction reached by ANY
    0.5 cm² window anywhere on the w040 known-text sheet is **0.1979**; p99.9 0.1687, p99 0.1396, p90 0.0758, median
    over windows containing any ink 0.0513. At 1 cm² the maximum is **0.1292**; at 4 cm² — the prize's own area —
    **0.0622**. **Zero window positions of 40.8 million reach the 0.2608 floor, and zero reach even the 0.2139
    forward-level floor.**
  - Letter geometry on the same labels, as a physical check that these are real letters: component height median
    **2.60 mm** (p10 2.22, p90 3.81), width median **2.69 mm** — the Herculaneum capital prior, 2-4 mm, confirmed.
  - **The caveat that keeps arm 1 from being the whole story.** The mixture model treats the model's response as a
    per-pixel function of the label. It is not: a convolutional reader raises its output in a *halo* around ink, so a
    unit's forward mean rises faster with φ than the mixture predicts. That is exactly why the w028 self-test could
    flag text units at forward 0.4328: the mixture model cannot reproduce that number at any φ ≤ 1 from w028's own
    blank level, so the halo (and, on w028, memorisation — Gate C records its AUC as memorisation) is doing the work.
    **Arm 1 therefore bounds nothing on its own.** The question it raises has to be settled on the maps, not on a
    model of the maps, and that is R-CTRL55 below.

## R-CTRL55  Does rule 5.5, exactly as frozen, flag the known-text control? (declared 2026-09-19 02:28 UTC, BEFORE the run)

- **The question.** Every "BLANK" and "NOT ESTABLISHED" on record is a statement that rule 5.5 did not fire. That is
  informative about ink only if rule 5.5 fires on real Herculaneum text at real coverage, on a sheet the model was not
  trained on. The one place that has ever been tested is w028 — and Gate C records w028's label AUC as **memorisation**,
  so it cannot answer the generalisation question. w040 can: Gate A scores it at AUC 0.9966 forward and 0.4963 reverse,
  it is a real sheet with human ink labels, and we hold the full-canvas forward and reverse maps (`gates/gateA/
  w040_full_plain{,_reverse}.tif`, 6400 × 7980, plain seed42, both orders — Gate A's own maps, unmodified).
- **The run.** `rule55.evaluate` — the frozen code, no argument changed — on those two maps at 9.362 µm, with the
  on-sheet mask taken as the maps' own valid footprint, and the grid origin chosen by the frozen `best_origin`, which
  depends on the mask only and never on the maps. Reported: valid units, flagged units, cluster sizes, and the full
  per-unit table with each unit's true ink area fraction φ from the labels beside its forward mean and margin.
- **What I already know going in, stated so the bar is honestly blind:** the maximum φ available anywhere on this sheet
  at 0.5 cm² is 0.1979, and the area-mixture floor is 0.2608. I do **not** know what the maps do, because the halo
  effect above breaks the mixture model, and the maps are the thing being tested.
- **Bars, fixed now.**
  - **CTRL55-PASS** — rule 5.5 flags **≥ 1** valid unit on this control: the screen can see real text on a sheet the
    model did not memorise, and every corpus negative on record stands exactly as read.
  - **CTRL55-STRONG** — it additionally produces a cluster of **≥ 3** adjacent flagged units, i.e. a PROMISING
    CANDIDATE on the control: the screen is fully capable at the prize's own scale, and the corpus negatives stand with
    full force.
  - **CTRL55-BLIND** — it flags **zero** valid units: then rule 5.5, as frozen, **cannot flag known Herculaneum text at
    real ink coverage on an unmemorised sheet**, and every corpus BLANK / NOT ESTABLISHED verdict is uninformative
    about the presence of ink. **Rule 5.5 still does not move** — it is frozen, and every verdict already recorded
    stands exactly as recorded. What follows instead is that a second indicator, localised rather than averaged and
    anchored on **this** control, is required before any further reading has meaning; it will be declared in writing,
    with its bars, before it is run.
- R-CTRL55 alters no map, no verdict and no bar. It tests our instrument against known text.

- **R-CTRL55 RESULT (2026-09-19 02:35 UTC). OUTCOME: CTRL55-STRONG. The frozen screen fires on known text, and it
  produces a PROMISING CANDIDATE on the control. No bar moves.**
  - The frozen `rule55.evaluate`, no argument changed, on Gate A's own full-canvas w040 maps (6400 × 7980, plain
    seed42, both orders). On-sheet footprint 46 322 688 px = **40.60 cm²**, 90.7 % of the canvas. Frozen `best_origin`,
    which sees the mask and never the maps, chose (94, 188) → 71 units, **67 valid**.
  - **FLAGGED 6 of 67. Cluster sizes [3, 1, 1, 1] — largest cluster 3.** Three adjacent flagged 0.5 cm² units is
    exactly rule 5.5's PROMISING CANDIDATE. **The whole chain — render → reader → rule 5.5 → candidate — fires
    end-to-end on real Herculaneum text, on a sheet the model did not memorise.**
  - The units that fired are genuinely inked: (3,3) φ **0.1109** forward 0.3690 margin **+0.0909**; (1,3) φ **0.1087**
    forward 0.4043 margin **+0.0919**. The area-mixture floor of 0.2608 from R-SENS arm 1 is therefore **wrong as a
    bound**, exactly as the halo caveat said it would be: the reader responds around ink, not only on it, and a unit
    fires at less than half the mixture model's φ.
  - **The honest sensitivity, which is the number that matters for every negative we hold.** Of the 17 valid units
    with φ ≥ 0.02 — the genuinely text-bearing ones — **3 flagged**. Their forward mean is 0.3669 and their margin mean
    **+0.0570**, best **+0.0935**. Firing begins around **φ ≈ 0.11** and is absent below **φ ≈ 0.09**; even at
    φ = 0.1253 one unit missed, on the forward level (0.3378 < 0.36), not on the margin. The screen needs a unit that
    is roughly a tenth ink — a dense text column, not a line or two in a margin.
  - **What this settles.** Every BLANK and NOT ESTABLISHED on record **is** informative about ink: the instrument that
    produced them demonstrably fires on real text at real coverage. The corpus negatives stand, with their force
    quantified — they exclude text at ≳ 10 % unit coverage, not text at any coverage.
  - **What this costs us, quantified.** On a known text-bearing sheet, 40.60 cm² of canvas yielded **one** PROMISING
    CANDIDATE and 6 flagged units of 67. Our whole corpus has read of order **23 cm² of geometrically sound interior
    canvas**. **The binding constraint is canvas area on sound geometry, and we are at roughly half of one expected
    candidate's worth of it.** Not the reader, not the render path, not the depth test, not the geometry quality —
    area. That is where the remaining effort goes.
  - Records: `gates/rctrl55/rctrl55.json`, `gates/rsym/rsym.json`, `gates/rsens/rsens.json`, `scripts/rctrl55.py`,
    `scripts/rsym.py`, `scripts/rsens.py`.

## G-GP part 5  Second-generation concentrated seeding from the consensus surface (declared 2026-09-19 02:45 UTC, BEFORE the run)

- **Why, from the numbers just measured.** R-CTRL55 prices one PROMISING CANDIDATE at about **40 cm² of text-bearing
  sheet**; the project has ever read about **23 cm² of geometrically sound interior canvas**, and only a third of each
  surface survives rule 5.5's 90 % on-sheet validity test (the 5.162 cm² consensus rendered 3.22 cm² on-sheet and gave
  **1.00 cm² in valid units**, against the w040 control's 67 valid units over 40.60 cm²). Canvas area on sound,
  *contiguous* geometry is the binding constraint. Part 4's seed pool is exhausted at 26 sources.
- **The run.** `sheet_seeds.py` — unchanged — sampling **60 seeds by farthest-point spread in grid index** from the
  5.162 cm² consensus surface's own valid grid points, so every seed is a point that surface passes through and the
  reachable area extends to that surface's extent rather than the original patch's. Same volume, same tracer, same
  parameters, same growth budget as part 4; only the seed source differs. Output joins `patches/PHerc0826_dense/`.
- **Bar G-GP-5, fixed now.** A consensus surface built by `vc_grow_seg_from_segments` from the union of all part-4 and
  part-5 sources, at the team's own published parameters (`consensus_default_th: 6`, `consensus_limit_th: 2`,
  `flip_x: false`, `global_steps_per_window: 2`, `step: 6`), must reach
  1. **≥ 10 cm²** rendered on-sheet area, **and**
  2. **≤ 1.42 transverse self-intersections per cm²** — the w040 known-text control's own measured rate, **and**
  3. **p90 sag ≤ 9.93 µm** — the w040 control's own, at matched baseline.
  If it reaches the area and misses either geometry bar, that is recorded as **area bought at the cost of geometry**
  and the surface is not treated as sound. Valid-unit area under rule 5.5 is reported alongside on-sheet area, because
  valid-unit area is what the rule actually sees.
- Part 5 changes no bar, no verdict and no map. It buys canvas.

- **R-CTRL55, correction and completion (2026-09-19 02:55 UTC). I withdraw the sensitivity curve I wrote above; the
  outcome CTRL55-STRONG stands and is now shown to be genuine text.**
  - **My error.** I read each unit's ink area fraction φ off the label slice over the *whole* unit and binned the units
    by it. The w040 supervision mask covers **3.19 %** of the canvas: over the 67 valid units its **median coverage is
    0.0000** and its maximum is 0.3118, with only 18 units above 5 % and 3 above 20 %. A unit outside the labelled band
    scores φ = 0 because nobody looked, not because it is blank. **The bins, the "17 text-bearing units", the
    "3 flagged of 17" sensitivity and the "firing begins at φ ≈ 0.11, absent below 0.09" curve are therefore not
    supportable, and I withdraw them.** They are left above as written, per the append-only rule.
  - **What the labels do support**, recomputed over each unit's *supervised* pixels only (φ|sup = ink / examined):
    every one of the 6 flagged units that has any supervision at all is heavily inked where the labeller looked —
    (1,2) φ|sup **0.9108**, (1,3) **0.6728**, (3,3) **0.4811**, (4,2) **0.4132**, (4,5) **0.5652**. The sixth, (1,1),
    has **zero** supervised pixels, so it can be called neither ink nor blank from these labels.
  - **The PROMISING CANDIDATE on the control is real text.** The cluster is [(1,1), (1,2), (1,3)] — three units in a
    row, margins +0.0857, +0.0954, +0.0919, forward 0.4036, 0.4158, 0.4043 — and two of its three members are 67 % and
    91 % ink where examined. (1,1) is the unlabelled continuation immediately beside them. **Not one flagged unit is
    demonstrably blank.**
  - **What therefore stands, unchanged:** the frozen chain fires end-to-end on real Herculaneum text on a sheet the
    model did not memorise; every corpus BLANK / NOT ESTABLISHED on record is informative about ink; and the pricing —
    **6 flagged units and one PROMISING CANDIDATE per 40.60 cm² of a text-bearing sheet**, against the ~23 cm² of
    sound interior canvas the project has ever read — stands as the reason canvas area is the binding constraint.
  - What is **not** established, and must not be claimed: the coverage at which the screen stops firing. These labels
    cannot measure it. It would take a control whose supervision mask covers whole 0.5 cm² units, and we hold none.

- **DEFECT, found and fixed 2026-09-19 03:05 UTC, and the authoritative R-CTRL55 numbers that replace the first run's.**
  - **The defect.** `rule55.evaluate(..., unit_origin=...)` takes the **string** `"auto"` or `"fixed"`. The first version
    of `scripts/rctrl55.py` passed the `best_origin` **tuple** `(94, 188)`, which fell into the `else` branch and
    silently tiled the grid from **(0, 0)** — while the script's own log line printed "frozen best_origin (mask only):
    (94, 188)". The run was correct and self-consistent *for the (0, 0) grid* (the φ values were read from the table's
    own boxes), but it was **not the grid every corpus read uses**: `read_chart.py` defaults to `--unit-origin auto`.
    Caught by comparing against an independent path — `read_chart.py --maps-only` on the same two maps reported 7 of 71
    where the script had reported 6 of 67. Fixed by passing `"auto"` and asserting the returned grid origin equals
    `best_origin`'s. Logged here as required by the standing practice: **whenever two paths over the same data
    disagree, neither number is used until the disagreement is explained.**
  - **Authoritative result, frozen rule on the frozen `auto` grid, origin (94, 188), side 755 px.** 80 units,
    **71 valid**, **FLAGGED 7**, cluster sizes **[4, 2, 1]**, largest cluster **4**. Verdict **PROMISING CANDIDATE**.
    Two independent code paths (`rctrl55.py` and `read_chart.py --maps-only`) now agree exactly on all four numbers.
  - **Every flagged unit that the labeller examined is heavily inked** (φ|sup = ink / examined pixels):
    (1,2) **0.7045**, (2,2) **0.5199**, (4,2) **0.5090**, (4,5) **0.5543**, (2,3) **0.3596**. The remaining two,
    (1,1) and (4,3), have essentially **no** supervised pixels, so the labels call them neither ink nor blank.
    **Not one flagged unit is demonstrably blank.**
  - **The candidate cluster is [(1,1), (1,2), (2,2), (2,3)]** — four adjacent units, margins +0.1108, +0.1131, +0.0971,
    +0.0825, forward 0.4264, 0.4200, 0.4109, 0.3689 — with (1,2) at 70 % ink and (2,2) at 52 % where examined. A second
    pair, [(4,2), (4,3)], carries the single strongest unit on the sheet: margin **+0.1349** at forward 0.4285, 51 % ink.
  - **The pricing is unchanged and now firmer: 7 flagged units and one 4-unit PROMISING CANDIDATE per 40.60 cm² of a
    text-bearing sheet.** Our corpus has read of order 23 cm² of sound interior canvas. Canvas area remains the binding
    constraint.
  - The control's own review sheet, produced by the ordinary pipeline with no special handling, is
    `gates/rctrl55/sheet/contact_sheet.png` — the visual standard a real candidate has to look like.

## R-POP  Do our surfaces read like the control's papyrus, or like something else? (declared 2026-09-19 03:15 UTC, BEFORE the run)

- **The question.** R-CTRL55 gives us, for the first time, a positive control that passes through the *same* code path
  as a corpus read: 71 valid 0.5 cm² units on a real Herculaneum sheet at 9.362 µm, 7 of them flagged. So the control's
  **unflagged** units are the reference population for "this reader, on a real sheet, where there is no strong text".
  Our corpus units can now be compared against it directly. One number already looks wrong: the control's *flagged*
  text units sit at forward 0.3689-0.4285, while our best corpus units sit at forward 0.4391-0.4508 — **higher than
  the control's text** — with margins near zero. If our renders sit on a raised floor with a compressed spread, a real
  signal could be squeezed below the +0.08 bar. That is the last untested way we could walk past text.
- **The populations.** Control: the 71 valid units of the R-CTRL55 run, split flagged (7) / unflagged (64). Corpus:
  every valid 0.5 cm² unit in every `read_stats.json` on disk that carries a rule 5.5 table, plain and TTA reported
  separately because TTA changes map levels (Gate C: judge reference 0.784 plain vs 0.823 TTA).
- **The statistics.** Per-unit forward mean and margin: median, IQR and range for each population.
- **Bars, fixed now**, comparing the corpus **plain** units against the control's **unflagged** units:
  - **POP-MATCH** — the corpus median margin is within **±0.02** of the control unflagged median **and** the corpus
    margin IQR is between **0.5×** and **2×** the control's: our surfaces read like ordinary control papyrus, nothing
    about the render path differs, and the only thing missing from our reads is text.
  - **POP-NARROW** — the corpus margin IQR is **below 0.5×** the control's: our renders produce systematically less
    depth contrast than the control's, a signal could be compressed below the +0.08 bar, and that becomes the next
    declared experiment (with its own bars, before it is run).
  - **POP-SHIFT** — the corpus median margin lies **outside ±0.02** of the control's: our surfaces sit at a different
    operating point, reported with its sign and size.
  - POP-NARROW and POP-SHIFT are not exclusive; both are reported if both hold.
- **R-POP is descriptive. It changes no bar, no verdict and no map**, and it cannot create a candidate.

- **R-POP RESULT (2026-09-19 03:30 UTC). Outcome POP-SHIFT (−0.0210); POP-NARROW ruled out. No bar moves.**
  - **A defect found and worked around first, because it invalidated the first run.** 41 of the 50 reads that carry a
    rule 5.5 table have a correct `n_valid` but an **empty `valid_units` list in the forward table**, while their
    `rule55_depth_swapped` table carries the full list (those reads also carry a `flagged_any_grid` key, so a later
    summarisation path wrote them). My first R-POP therefore drew its corpus population from **9 reads and 24 units** —
    a biased subsample — and reported POP-SHIFT (−0.0389). The swapped table is the **exact mirror** (margin negated,
    forward and reverse means exchanged), verified unit by unit on the reads where both lists are populated, so the
    forward population is reconstructed from it exactly. **No verdict was ever affected**: `n_valid`, `n_flagged`,
    `flagged` and the cluster sizes are computed from the arrays, not from this list. Corrected population: **106 plain
    units over 29 reads** (9 direct + 37 mirrored), 54 TTA units over 17 reads. This is the third defect tonight caught
    by running two paths over the same data; the practice is paying for itself.
  - **The corrected numbers.** Control ALL 71 valid units: forward median 0.3368, margin median **+0.0277**.
    Control FLAGGED (7, text): forward 0.4109, margin **+0.0989** (range +0.0825 to +0.1349).
    Control UNFLAGGED (64): forward 0.3344, margin **+0.0224**, IQR 0.0382.
    **Corpus plain (106): forward median 0.4081, margin median +0.0014, IQR 0.0370, range −0.0714 to +0.0814.**
    Corpus TTA (54): forward 0.4293, margin +0.0079, IQR 0.0433, max +0.0873.
  - **Bars: margin median difference −0.0210 → POP-SHIFT** (it misses POP-MATCH by 0.001). **IQR ratio 0.967 →
    POP-NARROW is ruled out.** Our maps are not compressed; a real signal would not be squeezed below the bar by a
    narrowed spread. That was the last untested way we could have walked past text, and it is closed.
  - **Why the shift, measured rather than guessed.** The control's "unflagged" units are **not blank papyrus** — w040 is
    a text-bearing sheet whose labels cover 3.19 % of the canvas, so most unflagged units hold unlabelled, sub-threshold
    text. Splitting the 64 unflagged units by how much the labeller examined gives a clean monotone gradient:
    | control unflagged units | n | margin median |
    |---|---|---|
    | no supervised pixel at all (furthest from labelled text) | 43 | **+0.0131** |
    | supervision < 5 % | 9 | **+0.0220** |
    | supervision ≥ 5 % (text in or beside the unit) | 12 | **+0.0398** |
    | flagged (text) | 7 | **+0.0989** |
    **The margin is a monotone function of how much ink is in the unit**, from +0.013 through +0.040 to +0.099 — which
    is exactly what the statistic is supposed to do, demonstrated on real text for the first time. Our corpus sits at
    **+0.0014**, below even the blankest units of a text-covered control sheet.
  - **What follows.** The POP-SHIFT is fully accounted for by the control being text-bearing throughout, not by any
    difference in our render path. Our surfaces read like papyrus with no text on it. Combined with R-CTRL55 — the same
    frozen chain produces a four-unit PROMISING CANDIDATE on real text — the instrument is validated at both ends:
    **it fires on text and it sits at zero on our surfaces.** Nothing about the reader, the render path, the depth
    order or the map scale is standing between us and a prize. **Canvas area on sound geometry is.**
  - One honest caveat on headroom: the control's text units clear their own no-text baseline by +0.0765 (0.0989 −
    0.0224). Starting from our +0.0014, an identical contrast would land at **+0.0779**, a hair under the frozen +0.08.
    The bar does not move. The corpus has cleared it once in 106 plain units (+0.0814, the single flagged unit on
    `auto_grown_20260917090724211`), and the control's own text units reach +0.1349, so a genuinely inked unit has room.
  - Records: `gates/rpop/rpop.json`, `scripts/rpop.py`.

- **R-DEPTH RESULT (2026-09-19 03:45 UTC). VERDICT: ADMITTED, by the gain bar. The corpus has been reading the wrong
  depth.**
  | window | centre slice | offset | M = mean_fwd_on_ink − mean_rev_on_ink | AUC fwd | fwd on ink | fwd on blank | separation |
  |---|---|---|---|---|---|---|---|
  | LOW | 8 | −6 slices = −56.2 µm | 0.30980 | 0.93444 | 0.60252 | 0.28660 | 0.31591 |
  | CENTRE | 14 | 0 | **0.46808** | 0.99680 | 0.75606 | 0.25270 | 0.50336 |
  | HIGH | 19 | **+5 slices = +46.8 µm** | **0.60594** | 0.98462 | 0.71815 | 0.27305 | 0.44509 |
  - **`max(M) − M(CENTRE) = +0.13786`, against the declared bar of +0.05. ADMITTED.** The +5-slice window reads ink
    **29 % better** than the window every one of the 171 reads on record used. `retained_ratio` is 0.6619, so the
    selectivity bar (≤ 0.50) is not met and admission rests entirely on the gain, exactly as declared.
  - **Where the gain comes from.** At HIGH the *reverse* pass collapses much further on ink: `rev_on_ink` is
    0.71815 − 0.60594 = **0.1122**, against **0.2880** at the centre. The forward response is slightly weaker
    (0.71815 vs 0.75606) but the depth asymmetry — the thing rule 5.5 actually measures — is far stronger.
  - **Reported against the declaration, because it cuts the other way:** AUC (0.98462 vs 0.99680) and the
    forward ink-minus-blank separation (0.44509 vs 0.50336) both still prefer the centre. The declaration fixed the
    statistic as the margin on ink and said in advance that AUC and separation "decide nothing". They decide nothing.
  - **Why this matters more than the number looks.** R-POP measured our corpus margin baseline at **+0.0014** against a
    frozen bar of **+0.08**, and the control's text clears its own baseline by +0.0765 — leaving us about 0.001 of
    headroom if our text matched the control's contrast. A window that raises the ink margin by 29 % is the one lever
    on record that widens that gap **without touching a single threshold**.
  - **Part 2 is now owed, and its set was fixed before any of this was seen:** re-read at both off-centre windows under
    ledger keys `|-6|` and `|+5|` — (a) the two flagged-unit surfaces `PHerc0826|auto_grown_20260918155811706` and
    `PHerc0826|auto_grown_20260917090724211`, then (b) every read with `onsheet_ct_std >= 35`, in ledger order.
    **Rule 5.5 is untouched**: a unit flagged at a nonzero offset is a flagged unit exactly as at 0, and no level moves.
  - **The stated limitation stands and is repeated because it will be tempting to forget it:** ±6 slices is ±56 µm, a
    fraction of one sheet and an eighth of the 449 µm wrap spacing. R-DEPTH tests **mis-centring within a sheet**. It
    says nothing about a trace that landed on the wrong wrap, and this admission may not be quoted as if it did.

## R-CTRL55-W  Does the admitted window also flag more known text under the frozen rule? (declared 2026-09-19 04:00 UTC, BEFORE the run)

- **Why.** R-DEPTH admitted the +5 window on *its* statistic (mean forward minus reverse on labelled ink). Rule 5.5 is
  a different statistic — unit means over a 0.5 cm² square with two frozen levels — and a window that helps one need
  not help the other. Before any screening practice changes, the frozen rule itself is run at all three windows.
- **The run.** The **Gate B render** (our own `vc_render_tifxyz` render of the w040 known-text mesh crop, 2048 × 2048 ×
  28), its CT-mid on-sheet mask, and the frozen `rule55.evaluate(..., unit_origin="auto")` — nothing tuned — on the map
  pairs already on disk: CENTRE `gates/gateB/render_plain{,_reverse}.tif`, LOW `gates/rdepth/low{,_reverse}.tif`,
  HIGH `gates/rdepth/high{,_reverse}.tif`. Same render, same mask, same grid search; only the slice window differs.
- **Stated in advance: the crop is small.** 2048² at 9.362 µm is 3.68 cm², so it holds only a handful of valid 0.5 cm²
  units. A difference of one flagged unit here is weak evidence and will be reported as such, with the counts.
- **Bars, fixed now:**
  - **HIGH-BETTER** — `flagged(HIGH) > flagged(CENTRE)` **and** `largest_cluster(HIGH) >= largest_cluster(CENTRE)`.
  - **HIGH-WORSE** — `flagged(HIGH) < flagged(CENTRE)`.
  - **TIE** — anything else.
- **Consequence, declared now so it cannot be chosen after the fact.** On **HIGH-BETTER**, every new screening read is
  *additionally* read at the +5 window under ledger key `|+5|`. That is a change of **practice**, recorded as such;
  **no bar moves, no level moves and no verdict already on record changes.** On **HIGH-WORSE** or **TIE**, screening
  practice stays at offset 0. Either way **R-DEPTH part 2 still completes as owed** — its set and its obligation were
  fixed by the ADMITTED verdict and do not depend on this result.

### THE R-DEPTH "ADMITTED" VERDICT IS WITHDRAWN. It rested on a truncated map. (2026-09-19 04:20 UTC)

- **What happened.** `gates/rdepth/high_reverse.tif` is **25.00 % non-zero — exactly one quadrant** — while its own
  forward map `high.tif` is 100 % non-zero. The inference **exited 0** having written a quarter of the reverse map, so
  `.infer_complete_high` was touched and `score_auc.py` scored the file as if it were complete. The three quarters the
  writer never reached were averaged in as if the model had answered **zero** there.
- **Therefore every HIGH number I recorded at 03:45 UTC is an artefact:** `mean_on_ink 0.11221` for the reverse pass,
  `M(HIGH) = 0.60594`, the gain `+0.13786`, and the verdict **ADMITTED**. None of them stand. **R-DEPTH is back to
  PENDING on its HIGH window.** The LOW window is sound — `low.tif` and `low_reverse.tif` are both 100 % non-zero — and
  `M(LOW) = 0.30980` stands, as does `M(CENTRE) = 0.46808`, which was recorded before the bar existed.
- **Everything the withdrawn verdict caused has been undone:** R-DEPTH part 2 is **paused by marker and its running read
  killed** (it had re-rendered `PHerc0826/auto_grown_20260917090724211` and reached inference; no read was written and
  no ledger line exists). **R-CTRL55-W is void on its HIGH arm** and is reported below as inconclusive.
- **I published the wrong result and I am correcting it 35 minutes later.** It was caught only because R-CTRL55-W ran
  the frozen rule on the same maps and every unit came back with `rev 0.0000` — a number no real map produces. Had I
  not run that second test on the same data, the corpus would now be spending hours re-reading 27 surfaces at a window
  admitted by an averaging artefact.
- **What the corpus looks like after a full audit.** `scripts/map_integrity.py` checks every forward/reverse pair on
  disk with two **relative** tests: the pair's non-zero footprints must agree to within 0.02 (the two maps come from
  one tiling over one render), and, where the render survives, each map must cover ≥ 99 % of the on-sheet mask.
  **55 pairs checked; 54 sound; exactly one suspect — `gates/rdepth/high`.** No corpus read, no verdict and no gate on
  record is contaminated.
  - **My first version of that checker was wrong and is recorded so it is not repeated.** It put an absolute bar on the
    non-zero fraction and flagged **19 perfectly good corpus maps**: our surface renders are auto-cropped around an
    irregular surface, so tiles holding no surface are never written and a non-zero fraction of 0.60-0.84 is normal.
    Only full-rectangle control renders sit at 1.00. The bar has to be relative to what that read's own render covers.
- **The guard is now in the reader itself**, not in a separate script that has to be remembered: `read_chart.py`
  refuses a read whose two maps' footprints differ by more than 0.02 or whose on-sheet coverage is below 0.99, with a
  message naming the fix. There is no flag to switch it off. Two tests pin it, including one that proves an
  auto-cropped surface with a partly non-zero map is **not** refused.
- **Next:** delete the truncated HIGH maps, their marker and their AUC records, re-run the HIGH window to completion
  under the same declaration, verify the pair with `map_integrity.py` **before** scoring, and re-decide R-DEPTH on the
  bars exactly as they were written on 2026-09-18 17:45 UTC. Nothing about those bars changes.

- **R-CTRL55-W RESULT (2026-09-19 04:20 UTC): INCONCLUSIVE — the HIGH arm used the truncated map.**
  On the Gate B crop (3.68 cm², 4 units, all 4 valid — a small sample, as declared in advance):
  | window | flagged | clusters | verdict | the φ = 0.1225 unit |
  |---|---|---|---|---|
  | CENTRE | **1** | [1] | NOT ESTABLISHED | fwd 0.3889 rev 0.3083 margin **+0.0806** FLAG |
  | LOW | **0** | [] | BLANK | fwd 0.3651 rev 0.3290 margin +0.0361 |
  | HIGH | *(2)* | *(void)* | *(void)* | every unit read `rev 0.0000` — the truncated map |
  The CENTRE and LOW arms stand and are worth keeping: on this crop the frozen rule flags the most-inked unit at the
  centre window and flags nothing at LOW, which is consistent with `M(LOW) < M(CENTRE)`. **The HIGH comparison, and
  therefore the outcome, is void.** No practice changes. R-CTRL55-W will be re-run when a sound HIGH map exists.

- **No free canvas remains anywhere in the 23 eligible volumes (checked 2026-09-19 04:40 UTC).** `fetch_team_segments.py
  --dry-run` against the open-data bucket: PHerc1203 **0** unfetched, PHerc0800 **0**, PHerc1447 **1** — the flattened
  mesh variant of `z_dbg_gen_00320`, now fetched (`team_20251105093211-z_dbg_gen_00320`, `source.json` records the
  exact bucket prefix). No other eligible volume publishes segments at all. **Every published team surface is held.**
  From here, more canvas costs tracing.
- **That last surface measured before spending a read on it, as the G-GP order requires.** p90 sag **7.96 µm**, p90
  anisotropy **1.573**, 25 077 nodes at 171.2 µm spacing (≈ 7.3 cm²) — **better than the w040 known-text control's own
  9.93 µm**. It is a genuine Grand-Prize-quality parameterisation. Its raw twin of the same uuid,
  `team_z_dbg_gen_00320`, which we already hold and already read, measures p90 sag 8.79 µm and read **0 flagged of 7
  valid units**. The flattened variant is therefore a re-parameterised read of a sheet already read as a clean
  negative; it is queued behind the R-DEPTH decision, not ahead of it.
- **PHerc0826 is the right volume to concentrate on**, by our own pre-registered survey metric: it ranks **first of the
  23** on layer contrast (`records/survey_2026-09-16.json`, metric declared before the first run). The concentrated
  campaign is where it should be.

- **G-GP part 5 interim, at 29 of 60 traces (2026-09-19 04:55 UTC).** Six-fold agreement over the dense source set,
  `patch_agreement.py` at 24-voxel cells — the same instrument, unchanged, that measured the precondition before
  part 4: **5.62 cm²** at 29 sources, up from 5.11 cm² at 26. Max agreeing in one cell 23. Lower thresholds for the
  record: ≥ 2 patches 24.25 cm², ≥ 3 13.61, ≥ 4 9.26, ≥ 10 1.93.
- **The instrument is a tight predictor here, which is why it is worth quoting:** at 26 sources it gave 5.11 cm² and
  the consensus surface actually built from those 26 rendered **5.162 cm²**. It is an upper bound in principle and has
  behaved as an estimate in practice on this sheet.
- **Projection, labelled as a projection, with the rate it rests on.** Over sources 18 → 29 the six-fold area grew
  2.42 → 5.62 cm², about **+0.29 cm² per trace**; over the last three traces **+0.17**. At 31 more traces that is
[line withheld: prize-candidate detail under review]
  result** — the standing lesson from 2026-09-18 is to sample at completed traces and not to project, and the number
  that will go on the record is the one measured when the queue finishes.
- **An observation while the HIGH window re-runs, recorded because it is suggestive and not proof.** `dmesg` shows four
  failed allocations of ≈ 67.8 TB by a python process at **02:05:22 UTC**, inside the window in which the truncated
  HIGH reverse pass ran (02:00-02:29). `select_layer_indices` itself is sound on inspection — LOW, CENTRE and HIGH all
  yield exactly 17 in-range indices — so nothing is concluded from this. If the re-run truncates again the failure is
  deterministic and the HIGH window cannot be evaluated through `--layer-start/--layer-end` as it stands; if it
  completes, the first run met a transient. The guard decides either way before anything is scored.

- **Where the concentrated campaign has actually taken us, radially (measured 2026-09-19 05:05 UTC, same instrument as
  R-RADIAL: published umbilicus axis, level-4 CT mask 99th-percentile radius).**
  | surface | r/R p05 | r/R median | r/R p95 |
  |---|---|---|---|
  | the 5.162 cm² consensus surface (part 5's seed source) | 0.469 | **0.606** | 1.060 |
  | the part-4 source patch its seeds came from | 0.539 | 0.742 | 1.045 |
  | corpus readable population (R-RADIAL, BLANK + NOT ESTABLISHED, n = 18) | – | **0.83-0.86** | – |
  | corpus VOID population (R-RADIAL, n = 16) | – | **0.384** (0.201-0.569) | – |
  - **The campaign has moved our canvas inward from r/R 0.83 to 0.61** — a third of the way from the readable outer
    band toward the interior where every previous trace went VOID at the geometry stage, and it is the only method that
    has done so. The part-5 seeds are sampled from this surface, so the next generation stays there.
  - **This sharpens what "canvas is the constraint" means.** R-RADIAL already showed the corpus had only ever *read*
    the outer band (all 18 readable surfaces at r/R 0.49-0.96) while everything at r/R < 0.57 was VOID. The outermost
    wraps of a Herculaneum scroll are the most abraded and the least likely to carry legible text, so area bought out
    there is worth less per cm² than area bought inward. **We are now working at r/R ≈ 0.6, exactly the boundary where
    single-patch geometry starts to fail and where the consensus method's advantage is largest.**
  - Recorded as a measurement, not a bar. It gates nothing and changes no verdict.

- **Protocol 9 rehearsed before it is needed, and a real bug found in it (2026-09-19 05:15 UTC).** `protocol9.sh` now
  has a `P9_DRY=1` mode that runs nothing, checks every input it depends on, and prints every command it would run.
  Exercised against the 5.162 cm² consensus surface: **all 15 inputs present, every step printed.**
  - **The bug it found:** step 6, the seed43 confirmatory read, looked for the candidate in `patches/<scroll>`. Every
    surface the concentrated campaign produces lives in `patches/<scroll>_cons_partN`, `_small`, `_src` or `_dense`,
    so protocol 9 would have failed at its confirmatory step **on any candidate we are actually likely to find**, and
    it would have failed at 3 a.m. with a candidate on the table. It now uses the candidate's own parent directory.
  - Four tests pin it, including one that proves the dry run exits non-zero and prints MISSING when an input is absent.

- **An attempt to calibrate the prize bar on the control, and why it fails (2026-09-19 05:20 UTC).** The densest 4.00 cm²
  window of the w040 labels (side 2136 px = 20.00 mm, at (1900, 1007), ink area fraction 0.0622) holds **7 connected ink
  components, 5 of them 2-4 mm tall** — fewer than the ten legible letters the prize requires. **This does not mean the
  control's best window holds fewer than ten letters, and it must not be quoted that way.** The w040 supervision mask
  covers 3.19 % of the canvas, so those are the *labelled* components in that window, not the letters present in it.
  Every ink-area fraction in this file derived from these labels is a **lower bound** for the same reason.
  - What it does confirm, for a third time and independently: the labelled components there are **2.30-3.64 mm tall,
    median 2.38 mm** — the Herculaneum capital prior, 2-4 mm.

### Three corrections recorded together (container clock 2026-09-19 03:05 UTC)

- **1. My timestamps in the entries above are wrong by about two hours, and I am not editing them.** I took the time
  from the scheduled-trigger notifications and my own running estimate instead of from `date -u` on the box. The
  container clock read **03:00:31 UTC** when the entries above said 05:20. Every entry from "R-SYM declared" onward
  carries a wall-clock label that is roughly two hours fast; **the order of the entries and every measured number in
  them are unaffected**, and the append-only rule forbids editing them. From here the timestamps come from `date -u`.
- **2. A SECOND truncated reverse map, caught by the new guard before it was scored.** The PHerc1203
  `team_20250923163331524` TTA read finished at 02:58 with a reverse map covering **0.9404** of the on-sheet mask
  against the forward map's **1.0000** — footprints 0.0486 apart. **No `read_stats.json`, no contact sheet, no ledger
  line exists for it**; the guard held. A fresh audit of all 55 pairs finds that one and nothing else.
  - **Both truncations are on the REVERSE pass, and that direction is the dangerous one.** Rule 5.5 flags on
    `forward − reverse`. Pixels the reverse pass never wrote read as **zero**, which *lowers* the reverse mean and
    therefore **inflates the margin**. A truncated reverse map pushes a unit toward being FLAGGED, not away. The first
    one manufactured an ADMITTED verdict; a second could manufacture a PROMISING CANDIDATE. **This is now the failure
    mode the project guards hardest against**, and the guard sits in `read_chart.py` where every read must pass it.
  - The truncated pair and its inference marker are deleted so the read re-runs from scratch.
- **3. `rbest2.sh` was crashing on every `PHerc0826_small` member of its declared population.** It passed the patches
  **directory** name as `--scroll`, and `volume_info` raised `KeyError: 'PHerc0826_small'` against the catalogue.
  `PHerc0826`, `_small`, `_src`, `_cons_part4` and `_dense` are one scroll and one volume; only the directory differs.
  Fixed in `rbest2.sh` and, before it could bite, in `rdepth_part2.sh`: `--scroll` takes the base scroll, the patches
  path keeps the directory. Two tests pin both halves. **The declared population is unchanged** — the members that
  crashed were never read and are still owed.

- **The systemic cause of both truncations, found and capped (container clock 2026-09-19 03:10 UTC).** Seven scripts
  pass **seven different `HERCULES_INFER_LOCK` paths** — `infer.lock`, `infer_prod`, `infer_p9`, `infer_rbest`,
  `infer_rbest2`, `infer_1203`, `infer_small`, `infer_cons`. Each lock serialises its own caller and **none of them
  serialises against the others**, so by design up to eight 9 µm inferences could share four cores and 15 GB. Load
  average on this box has been 10-14 all night. Both reverse-pass truncations happened under that load.
- **`run_patch_dir.py` now holds a GLOBAL slot before its named lock**: `HERCULES_INFER_SLOTS` (default **2**)
  exclusive flocks in `logs/infer_slots/`, acquired before the per-caller lock and released even when the command
  fails. Any caller, any script, any experiment counts against the same two slots.
- **This is an engineering limit on this box, not a scientific threshold.** It changes no bar, no level, no verdict and
  no map; it only decides how many inferences run at once. Three tests pin it, including one that proves a third
  inference blocks while two slots are held and proceeds the moment one is released.
- Cause of the truncation itself remains **unproven** — `dmesg` shows failed huge virtual allocations during the first
  one, which is suggestive and nothing more. Detection, a bounded blast radius and a lower load are what we have; the
  reader refuses a truncated pair either way.

- **Is R-CREST hiding recoverable canvas? No. (measured, container clock 2026-09-19 03:20 UTC; descriptive, no bar
  changes.)** The tempting idea: 93 reads totalling **469.7 cm²** — four times all the sound canvas the project has —
  were stopped by the crest check before rule 5.5 ran. If their sheets were *present but off-centre* in the 28-slice
  window, a shifted render would recover them at no tracing cost. Split by which half of the check they failed:
  | how the crest check failed | reads | area |
  |---|---|---|
  | ratio ≥ 1.2 but the crest lies outside the central band — a sheet present but off-centre | **2** | **6.0 cm²** |
  | ratio < 1.2 — the per-slice CT profile is flat, no sheet anywhere in the window | **91** | **463.6 cm²** |
  - The failing ratios cluster at **1.00-1.11**: essentially flat profiles, not displaced peaks. **Shifting a window
    along a flat profile gives another flat profile**, so no depth offset recovers them. And the two that do have a
    real peak have it at **slice 0**, the render's outer edge — grazing material at the boundary, not a sheet sitting
    a few slices off centre.
  - **R-CREST discards nothing this reader could read**, on the evidence of the reads' own stored profiles. The 463.6
    cm² is traces that cut across wraps, which is what R-INTERIOR, R-NORMAL and G-GP part 3 all said independently.
  - It also bounds what R-DEPTH can ever be worth: R-DEPTH tests **mis-centring within a sheet**, ±56 µm, and this
    shows there is no population of near-miss surfaces waiting for it. Its declaration said exactly that; this is the
    measurement behind it.

## G-GP part 5b  Buy area with a lower consensus threshold ONLY if the geometry bars still hold (declared container clock 2026-09-19 03:25 UTC, BEFORE the run)

- **Why.** At the team's published `consensus_default_th: 6` the current 29 dense sources reach **5.62 cm²** of
  six-fold agreement; at threshold **4** the same sources reach **9.26 cm²** — 65 % more. Area is the binding
  constraint (R-CTRL55 prices one candidate at 40.60 cm² of text-bearing sheet). But a lower threshold means fewer
  independent traces had to agree on where the sheet is, so it can buy area with geometry, which is exactly the trade
  the G-GP bars exist to police. One threshold-4 consensus was built earlier in part 4 and read NOT ESTABLISHED
  (0 flagged of 1 valid unit, margin −0.0021); its geometry was never put against the control's own rates.
- **The run, when the part-5 queue finishes.** From the **identical** source set, identical seed, identical
  parameters in every other respect, build **two** consensus surfaces: `consensus_default_th` **6** (part 5, already
  declared) and **4** (part 5b). Measure both with `rcross.sh` and `mesh_distortion.py --baseline-um 187.2`.
- **Bar, fixed now.** The threshold-4 surface is **admitted for reading only if it meets the same two geometry bars as
  part 5's**: transverse self-intersections **≤ 1.42 per cm²** and p90 sag **≤ 9.93 µm**, both the w040 known-text
  control's own measured values. If it meets them, the area is **earned** and it is read under its own ledger key on
  the ordinary plain screening recipe. If it misses either, it is recorded as **area bought at the cost of geometry**
  and **it is not read** — the number goes on the record and nothing follows from it.
- Both areas, both crossing rates, both sags and both valid-unit areas are reported whatever the outcome.
- **Rule 5.5 is untouched.** A read of the threshold-4 surface is an ordinary read; no level, no cluster rule and no
  verdict definition changes. Part 5b cannot admit a candidate that part 5's own bars would not admit.

- **The truncation mechanism, captured in a log (container clock 2026-09-19 03:12 UTC).** A dense-loop inference on
  `PHerc0826_dense/auto_grown_20260918181659182` selected 1139 patches and then died with
  **"resource_tracker: There appear to be 18 leaked semaphore objects to clean up at shutdown"** — the signature of a
  multiprocessing worker pool being torn down abruptly, i.e. **workers killed under pressure**. That run exited
  non-zero and `run_patch_dir` reported `ERROR: inference failed`; the R-DEPTH HIGH run exited **zero** with a quarter
  of its reverse map written. Same mechanism, two different exit codes, which is why the guard is on the FILES.
- **Two contained mitigations, neither of which touches a result.** The global slot cap (2 concurrent inferences,
  above), and `HERCULES_INFER_WORKERS` **lowered from 3 to 2**: two inferences at three workers each is six loader
  processes on four cores on top of the tracers. Worker count affects throughput only — the maps are identical at any
  value — and it is now configurable with a test pinning the default.

- **LEDGER integrity audited (container clock 2026-09-19 03:20 UTC): the record is complete.** `scripts/ledger_audit.py`
  — **162 ledger keys, 141 `read_stats.json` on disk, 0 reads on disk with no ledger line**, 21 ledgered reads whose
  stats were pruned (normal and expected). A read that happened but was never ledgered is the one gap that cannot be
  reconstructed once its maps are gone; there are none.
  - **The audit's own first version was wrong and is recorded.** Ledger keys contain pipes, escaped `\|` so the
    markdown table keeps its columns; splitting a row on a plain `|` shredded every key and reported **all 141 reads
    as unledgered**. Rows are now split on unescaped pipes only, and a test pins that, a second pins that daily
    summary rows are not mistaken for keys.

### R-SMALL RESULT (container clock 2026-09-19 03:25 UTC): the reduced budget nearly TRIPLES the readable fraction and still FAILS its bar. The budget goes back to 60, as declared.

- **The population is complete**: 19 traces at `generations: 40` across `PHerc0826_small` and `PHerc0358_small`, every
  one resolved (the three 20-generation traces stay excluded, as declared, and `max_gen` in each `meta.json` makes the
  split checkable). Outcomes: **VOID 11, QC FAIL 4, QC UNREADABLE 1, BLANK 2, NOT ESTABLISHED 1**.
- **Both denominators are reported so there is no suspicion of picking one**, and the outcome is the same either way:
  | denominator | readable | fraction | bar |
  |---|---|---|---|
  | all 19 interior traces at 40 generations | 3 | **15.8 %** | ≥ 30 % |
  | the 14 that got past QC to a read | 3 | **21.4 %** | ≥ 30 % |
  The 60-generation baseline on record is **5.6 % (1 readable of 18)**.
- **VERDICT: R-SMALL FAILS.** Its declaration says in terms: "Below that it is recorded as no improvement and the
  budget goes back to 60." **The budget goes back to 60.**
- **What is true and must be said alongside the failure:** 15.8 % against 5.6 % is a **2.8-fold** gain, and 21.4 % is
  3.8-fold. The bar was set at 30 % before any trace precisely so that a gain of this size would not carry it, and it
  does not. The gain is recorded; the bar is not moved to meet it. Even a further readable trace would give 4 of 15 =
  26.7 %, still short, so the outcome is not one trace away from flipping.
- **The pre-written next step applies, and it was written on 2026-09-18 15:35 UTC, before any of these numbers:**
  whether the density gate — calibrated on 60-generation traces at density ≤ 0.20 — is the wrong gate for a
  40-generation patch, since a smaller patch has proportionally fewer chances to cross a wrap. That is declared below
  as R-SMALL-2, with its bar, before any such seed is traced.
- The caveat already on record stands: these interior seeds came from the existing density-gated files, so R-SMALL
  tested the BUDGET on the **sparse** interior, not the interior as a whole. R-WRAP, which was meant to remove the
  confound in "readable", failed its own calibration, so R-SMALL is judged on its declared bar alone — as its
  declaration said it would be.

## R-SMALL-2  Is the density gate the wrong gate for a smaller patch? (declared container clock 2026-09-19 03:30 UTC, BEFORE any such seed is traced)

- **This is the follow-up written on 2026-09-18 15:35 UTC, before R-SMALL's numbers existed**, and it is run because
  R-SMALL failed. Quoting that note: "whether the density gate, calibrated at 60 generations, is the wrong gate for a
  40-generation patch. A smaller patch has proportionally fewer chances to cross a wrap, so a denser neighbourhood may
  be acceptable for it." Nothing about it is invented now.
- **The evidence it rests on**, already on record: of the 53 traced seeds with an outcome, every one of the 15 that
  produced a read sat at level-3 prediction density **≤ 0.20** (median 0.105), while 16 of the 23 VOID traces sat
  **above** 0.20 (median 0.224, up to 0.36) — measured at **60** generations, which is the only budget that
  calibration ever saw.
- **The run.** Regenerate PHerc0826 and PHerc0358 interior seeds (r/R in [0.20, 0.55] by the R-RADIAL measure) with
  `--max-density 0.30` instead of 0.20, the same `--density-window`, the same prediction volume and everything else
  identical. **The population is exactly the newly admitted band** — seeds excluded at 0.20 and admitted at 0.30 — so
  the test is about the seeds the old gate threw away, not a re-run of the ones it kept. Traced at `generations: 40`,
  the same budget R-SMALL used, through the same QC, the same R-CREST, the same reader and the same frozen rule 5.5.
- **Bar, the same form and the same level as R-SMALL's, against the same baseline, fixed now.** Over **at least 15**
  such traces, the readable fraction must reach **≥ 30 %**, against the 60-generation baseline of **5.6 %** (1 of 18).
  Both denominators are reported — all traces, and only those reaching a read — and **the bar must be met on the
  all-traces denominator**, the stricter of the two, exactly as R-SMALL was finally judged.
- **If fewer than 15 seeds exist in the newly admitted band**, the test cannot be run as declared and that is recorded
  as such; no smaller population is substituted.
- **If R-SMALL-2 fails**, the pre-written conclusion stands and is recorded as the finding: *interior geometry is not
  recoverable on this box with the published tooling and priors* — the same way R-NORMAL, R-NORMMAG, R-INTERIOR,
  R-PHASE and R-WRAP were recorded.
- It changes where we TRACE and nothing else: no verdict rule, no rule 5.5 threshold, no R-CREST bar, no reading
  recipe. It starts only when the G-GP part 5 queue releases a trace slot, so it delays no declared work.

### A cache collision that silently gave one scroll another scroll's seeds (found and fixed, container clock 2026-09-19 03:35 UTC, before any R-SMALL-2 trace)

- Regenerating R-SMALL-2's seeds at `--max-density 0.30` for PHerc0826 and then PHerc0358, **sharing one `--cache`
  directory**, produced **90 seeds identical between the two scrolls** — with PHerc0826's level-3 shape
  `[2115, 1022, 1022]` and every one of PHerc0826's per-slice `n_pred` values, under **PHerc0358's own prediction URL
  in the file header**. The cache names its files after the chunk key alone (`3_.zarray`, `3_2_0_0`), so the second
  run read the first run's chunks.
- **It was caught because two different scrolls cannot produce identical numbers.** Nothing else would have shown it:
  the header, the URL and the volume id were all correct.
- **The historical record is clean, and that was checked rather than assumed.** `seeds/PHerc0826.json` and
  `seeds/PHerc0358.json` have **zero overlap** in 90 seeds, different bands (3730/7960/12190 against
  3186/6872/10558), different per-slice counts and different level-3 shapes. **No trace on record was seeded from the
  wrong volume.**
- **Fixed in `seeds.py`:** cache files now live under a namespace derived from the source URL
  (`sha1(base)[:12]`), so two sources cannot collide whatever `--cache` they are given. Three tests pin it, including
  one proving a second source with the same chunk key fetches rather than reusing the first's file.
- The two bad seed files were deleted. R-SMALL-2's seeds will be regenerated with the fixed seeder, and its bar is
  untouched — it was declared before any of this and none of it is a result about the scrolls.

- **R-SMALL-2's population exists and the precondition is met (container clock 2026-09-19 03:40 UTC, before any trace).**
  With the fixed seeder, PHerc0826 and PHerc0358 at `--max-density 0.30` give **zero overlapping seeds** and their own
  level-3 shapes (`[2115, 1022, 1022]` and `[1843, 973, 973]`), so the cache collision is gone.
  | scroll | newly admitted by the 0.20 → 0.30 change | of those, interior (r/R 0.20-0.55) | r/R median |
  |---|---|---|---|
  | PHerc0826 | 54 | **38** | 0.339 |
  | PHerc0358 | 50 | **42** | 0.389 |
  **80 interior seeds in the newly admitted band**, against the ≥ 15 the bar needs. Written to
  `seeds/PHerc0826_rsmall2.json` and `seeds/PHerc0358_rsmall2.json`, each carrying its per-seed r/R so the population
  is checkable rather than asserted. Their r/R medians (0.34, 0.39) sit squarely in the band where every 60-generation
  trace on record went VOID — which is the point of the test.

- **The model's strongest responses come from the renders with the LEAST texture (measured, container clock
  2026-09-19 03:35 UTC; descriptive, no bar changes).** Over the 50 reads that carry both numbers, the correlation
  between a render's on-sheet CT standard deviation and the fraction of its forward map above 0.75 is
  **r = −0.4960** — less texture, stronger response. Split at a CT std of 25 (the corpus median is 35.5, the w040
  control 43.1):
  | reads | n | median frac > 0.75 | median forward |
  |---|---|---|---|
  | on-sheet CT std < 25 | 3 | **0.0501** | **0.4979** |
  | on-sheet CT std ≥ 25 | 47 | **0.0036** | 0.3949 |
  **A fourteenfold difference in the strong-response fraction**, in the direction that says the response is an
  artefact of villa's robust-MAD normalisation stretching noise on a near-uniform render — the third candidate
  explanation written down on 2026-09-18 and never before tested against the corpus.
- **This bears directly on the two surfaces at the top of the review index**, and it is recorded now, before either is
  re-read, so it cannot look like an excuse afterwards:
  - `PHerc0826_small/auto_grown_20260918155811706` — **CT std 10.05**, the lowest in the corpus, forward 0.4980,
    frac > 0.75 **0.0552**, the highest in the corpus, margin +0.0320. It is the **first** of R-DEPTH part 2's two
    declared priority surfaces.
  - `PHerc0826_small/auto_grown_20260918152701336` — CT std **8.63**, forward 0.4436, frac > 0.75 0.0348, margin
    −0.0119.
  Both are R-SMALL 40-generation interior traces, and both sit at a quarter of the control's texture. Their elevated
  responses are most simply explained by the render having almost nothing in it.
- **Nothing is vetoed by this.** Rule 5.5's frozen levels and the 5.10 assertion floor (on-sheet CT std ≥ 5.0) stand
  exactly as written, and neither surface is flagged today. It is recorded so that an elevated forward value on a
  textureless render is read as what the corpus says it usually is.

### The submission package was not verifiable after its render was pruned (found and fixed, container clock 2026-09-19 03:40 UTC)

- **Found by re-running P-DRY's verifier** after a night of changes, as the standing practice requires. It reported
  **3 FAIL** where P-DRY declares exactly **2**. The third: `ct_window.png map pixels equal the render slice crop:
  render zarr missing`. The verifier proved that image unaltered by re-opening the **source render zarr** — an
  external path recorded in the manifest, which our own disk guard prunes routinely and which `--delete-renders`
  removes on purpose. **A submission package stopped being verifiable the moment its render was cleaned up.** For a
  package that has to stand up to a prize committee weeks later, that is a real defect and not a cosmetic one.
- **Fixed so the strong check is kept when possible and a real check survives when it is not.** `package_submission.py`
  now writes the raw CT crop it used into the package as `ct_window_source.tif` and records its **sha256** in the
  manifest. `verify_package.py` checks, in order: the crop matches its manifest sha256; `ct_window.png`'s map pixels
  equal that crop; and — **when the render is still on disk** — that both equal the live render slice.
- **A check that cannot be run is now reported as `N/A`, never as a pass and never as a failure of the package.** The
  tally prints `N checks, F FAIL, A N/A`. That state exists only for a check whose *input* is gone; a check that
  genuinely failed still fails.
- **P-DRY's own package predates the fix and now fails four checks**, two of them because it carries no
  `ct_window_source.tif`. **That is the verifier behaving correctly** — an old package is not fully verifiable and it
  says so and names the remedy. Regenerating it needs a 4 cm² CT crop from the 6400 × 7980 w040 canvas whose stack
  (1.21 GB, 3150 chunks) was pruned; it is not regenerated tonight, and P-DRY's declared two failures are unchanged
  in kind.
- **Three tests pin the property instead**, which is a stronger guarantee than the dry run: a package verifies clean
  with the render present and with **zero N/A**; after the render is deleted exactly the live check goes N/A and
  **nothing fails**; a tampered packaged crop is caught by its sha256; and a package with no crop is **refused, not
  skipped**. A fourth was updated: tampering with `ct_window.png` must now fail **both** CT checks, not one.

- **Disk: `external/villa/.git` removed to keep the tracer fed (container clock 2026-09-19 03:45 UTC).** Free space had
  fallen to 5.4 GB against a 5.0 GB render floor, and the disk guard was pruning normal grids under two live tracers
  every minute — the ~4x throughput tax already on record. The villa checkout's **git history was 892 MB** and nothing
  in this project reads it: the venv installs from the working tree, and the exact commit was already recorded.
  Removed, with the provenance written here so nothing is lost:
  **`external/villa` = commit `5ab585ffee54331a3362b9ce6b2929b20dcde2c6`, committed 2026-09-16T17:51:11+00:00**,
  public at `github.com/scrollprize/villa`. The working tree is untouched and `external/` was never tracked by this
  repository.

- **Disk: `controls/w028/pooled21.zarr` (954 MB) removed (container clock 2026-09-19 03:45 UTC).** Free space was back
  at 5.5 GB against the 5.0 GB render floor with two tracers writing normal grids. Everything that reads it is
  **complete and recorded**: Gate C (its label AUC, which RULES records as measuring memorisation), the w028 unlabelled
  judge, and the R-5.5 self-test that validated the frozen 0.36 / +0.08 levels (results at RULES line 110, and in
  `gates/gateC/rule55_selftest_{plain,tta}.json`, which are kept). Nothing declared and unfinished reads it.
  **Provenance:** the team's public pooled w028 surface volume, fetched on day 0 per MASTER_PROMPT_v4 section 4;
  re-fetchable. `controls/w028/team_2um_prediction.tif` (117 MB) is **kept**, because CONTROL-2UM is still open and
  B-2UM's calibration refers to it. The stored Gate C and self-test JSONs are the record, not the stack.

- **HAZARD, recorded before the result it could affect arrives: `rdepth.sh` was edited WHILE IT WAS RUNNING**
  (container clock 2026-09-19 ~03:05 UTC, to add the `infer_slot.sh` global-slot wrapper). Bash reads a script lazily
  by byte offset, and a function is fixed in memory when it is defined, so the running process is executing the
  **pre-edit** `run_window`: it will **not** run the map-integrity audit after its inference, and it will touch
  `.infer_complete_high` whatever the maps look like. An insertion can also shift the outer script's byte offset.
  - **Therefore the HIGH result is not believed until its maps are audited by hand.** When the run finishes I run
    `map_integrity.py` on the pair myself; if the pair is suspect, the maps, the marker and any `rdepth.json` written
    from them are deleted and the window is re-run under the patched script. The bars are untouched either way.
  - **Standing practice added: never edit a script that is running.** Copy it, edit the copy, and swap it in between
    runs — or stop the job first. The guard I was adding is worthless in the very run it was meant to protect.

### R-DEPTH RE-RUN, FINAL: FAILED. Depth offset is CLOSED. (container clock 2026-09-19 03:47 UTC)

- **The hazard I recorded in advance materialised exactly.** The running `rdepth.sh`, edited mid-run, died on a shifted
  byte offset — `line 38: f.tif: command not found`, `line 40: syntax error near unexpected token 'done'` — *after*
  writing both maps, running the integrity audit and scoring them, and *before* reaching `rdepth_result.py`. No
  verdict was written by the crashed script. I audited the pair by hand as promised and then ran the scorer myself.
- **The HIGH pair is sound this time**: `high.tif` and `high_reverse.tif` are each **100 % non-zero** with **100 %
  on-sheet coverage**, no problems. A fresh corpus audit reports **55 pairs, 55 sound, 0 suspect**. **The first
  truncation was transient, not deterministic**, which the re-run was the only way to establish.
  | window | offset | M = mean_fwd_on_ink − mean_rev_on_ink | AUC fwd | AUC rev |
  |---|---|---|---|---|
  | LOW | −6 slices | 0.30980 | 0.93444 | 0.52627 |
  | **CENTRE** | 0 | **0.46808** | 0.99680 | 0.50265 |
  | HIGH | +5 slices | **0.39948** | 0.98462 | 0.59181 |
  - best off-centre minus centre = **−0.06860** against the +0.05 bar → does not admit.
  - worst off-centre / centre = **0.6619** against the ≤ 0.50 bar → does not admit.
  - **VERDICT: FAILED.** Per the declaration of 2026-09-18 17:45 UTC: *"depth offset is closed permanently... the
    response is both centred and broad, a ±5-slice mesh error costs little, and the 135 reads at offset 0 lose nothing
    to it. No re-read would be owed and none would be run."* **R-DEPTH part 2 is therefore not owed and will not be
    run**; its pause marker stays and its set is closed.
- **The truncated map inverted the verdict, and that is the clearest possible case for the guard.** With one quadrant
  of the reverse map written, M(HIGH) read **0.60594** and R-DEPTH was **ADMITTED**. With the map complete it reads
  **0.39948** and R-DEPTH **FAILS**. The difference is entirely the 75 % of reverse pixels that were never written and
  were averaged in as zeros. Had the guard not existed, the project would have spent the night re-reading 27 surfaces
  at a window that is measurably **worse** than the one it already uses.
- The limitation stands, unchanged and repeated: ±6 slices is ±56 µm. R-DEPTH tested **mis-centring within a sheet**
  and says nothing about a trace that landed on the wrong wrap.

- **R-CTRL55-W RESULT, completed with the sound HIGH maps: OUTCOME HIGH-WORSE.** The frozen rule 5.5 on the Gate B
  crop (4 units, all valid — a small sample, as declared in advance):
  | window | flagged | clusters | verdict | the φ = 0.1225 unit's margin |
  |---|---|---|---|---|
  | CENTRE | **1** | [1] | NOT ESTABLISHED | **+0.0806** FLAG |
  | LOW | 0 | [] | BLANK | +0.0361 |
  | HIGH | **0** | [] | BLANK | +0.0756 |
  `flagged(HIGH) < flagged(CENTRE)` → **HIGH-WORSE**. Per the consequence declared before the run: **screening practice
  stays at offset 0.** The two instruments agree — R-DEPTH's own statistic and rule 5.5's — and the earlier
  "HIGH-BETTER" reading is void, having been computed on the truncated map where every unit returned `rev 0.0000`.

- **The last free canvas is being read (container clock 2026-09-19 03:50 UTC).** `PHerc1447/team_20251105093211-
  z_dbg_gen_00320` — the flattened team mesh, p90 sag **7.96 µm** against the w040 control's 9.93, ~7.3 cm², its
  published surface volume already on disk — had not been read because **PHerc1447's read loop is held down by a
  `read_paused` marker**, set earlier on purpose to give the inference lock to declared experiment queues. With
  R-DEPTH finished and a slot free, it is read directly under the ordinary plain screening recipe and its own ledger
  key. The marker stays: the loop is not resumed, one surface is.
- **R-DEPTH part 2 is cancelled, and both mechanisms that would have started it are closed**: its `part2_paused`
  marker is in place, and the supervisor only starts it when `rdepth.json` reads `ADMITTED`, which it now does not.

- **The last manual step before a submission is now automated (container clock 2026-09-19 04:00 UTC).**
  `scripts/protocol9_for.sh <read_stats.json> [--go]` derives everything from the record: the patch directory
  (which may be `_cons_partN`, `_small`, `_src` or `_dense` — all the same scroll), the voxel size from the read's own
  stats, and **the volume id from the supervisor's COVERAGE string, never from memory** — the mistake that has already
  cost one wrong read and was caught before a second. It prints the read's verdict and flagged-unit count, **always
  runs the dry run first**, refuses to go on if any of the 15 inputs is missing, and needs an explicit `--go`.
  Exercised end to end on the 5.162 cm² consensus read: clean. Three tests, including one proving a scroll with no
  COVERAGE entry is refused rather than guessed.

- **A derived status table for every declared bar lives in `STATE.md`** ("Where every declared bar stands"), kept
  current there because STATE is a living document and this file is append-only. It governs nothing: where the table
  and the prose above disagree, **the prose above is right**. It exists because this record is now 2000 lines and one
  bar — R-DEPTH — was admitted, withdrawn and then failed, in three separate sections.

- **The flattened PHerc1447 mesh renders thinly, recorded before its verdict (container clock 2026-09-19 04:20 UTC).**
  `team_20251105093211-z_dbg_gen_00320` renders to **13640 × 8220 px at 8.64 µm** — an 86 cm² bounding box — with
  **occupancy 8.53 %**, i.e. its ~7.3 cm² of surface is spread thinly across it (2951 inference patches, three times
  the Gate B control's 961, which is why its forward pass takes about an hour). Rule 5.5 needs a 0.5 cm² square that
  is **≥ 90 % on-sheet**, so a thin spread can leave few or no valid units however good the geometry is. This is
  written down **before** the read returns so the verdict is interpretable either way: a BLANK or NOT ESTABLISHED
  there may say more about the parameterisation's footprint than about the sheet.

- **The live-tracer grid exemption now has two tiers, like the prune target already did (container clock
  2026-09-19 04:55 UTC).** The guard was pruning PHerc0826's grids from ~2860 MB down to 900 MB every eight minutes
  under two live tracers, because the single `ACTIVE_CAP` of 1500 MB was exceeded and the exemption voided — the
  ~4x refetch tax already on record (269/333 s before, median 1052 s over the 14 traces after). Now
  `ACTIVE_CAP_ROOMY=3000` applies when free space is above the 5.5 GB tier and `ACTIVE_CAP_TIGHT=1500` below it, so
  the exemption relaxes and tightens together with the prune target it sits beside. **Self-limiting**: if the grids
  grow into the headroom and free space falls below 5.5 GB, both tiers tighten in the same pass.
  - **Changed with the guard STOPPED and restarted by the supervisor**, per the practice written after `rdepth.sh`
    was corrupted by an edit mid-run. A test pins both tiers.

- **R-BEST-2 population member read (container clock 2026-09-19 05:20 UTC): `PHerc1203|team_20250923163331524`
  under the confirmatory TTA recipe — BLANK, 0 flagged of 5 valid units.** 3.76 cm² on-sheet, on-sheet CT std 33.33,
  forward mean 0.4394, reverse 0.4242, margin **+0.0152**, best single unit **+0.0261** against the frozen +0.08 bar.
  `fwd_frac_gt_0p75` is **0.00046** — three orders below the low-texture surfaces flagged earlier tonight, i.e. this
  is a genuinely quiet read, not a suppressed one. **Its map pair was re-checked by hand and is sound** (both maps
  0.5976 non-zero, identical footprints) — this is the read whose first attempt truncated at 94 % coverage and was
  deleted before it could be scored, so it is the first surface in the project read twice with the guard in between.
  The plain read of the same surface on 2026-09-18 was also BLANK at margin +0.0114; the two recipes agree.

- **The `rbest2.sh` fix did nothing until the loop was restarted (container clock 2026-09-19 05:24 UTC).** The
  scroll-vs-directory fix was committed at ~03:05, but the loop running since before then kept raising
  `KeyError: 'PHerc0826_small'` on every pass — a long-running shell loop holds the behaviour it started with. Killed
  and restarted through the supervisor; the new run resolves correctly (`PHerc0826 20250821151701: 9.362 um/px`) and
  is now reading the three `PHerc0826_small` members its declared population still owes.
  - **This is the second time tonight the same shape bit** — the first was `rdepth.sh`, where an edit mid-run
    corrupted the script itself. **Standing practice, extended: a fix to a script is not in effect until every loop
    running that script has been restarted, and the restart is part of the fix, not a follow-up.** Committing is not
    deploying.
  - The three members are the low-texture surfaces (on-sheet CT std 10.05, 8.63 and one other) whose likely-artefact
    caveat is already on record above, written before these reads were started.

- **My own progress counter was wrong, and I reported the wrong number twice (container clock 2026-09-19 05:45 UTC).**
  The monitor counted `x.tif` files in `patches/PHerc0826_dense`, which holds **part 4's 25 patches as well as part
  5's**, and printed that total against a `/60` denominator that means *part-5 seeds*. It read "59/60" and then
  "60/60" while the authoritative counter — the one `ggp5_when_ready.sh` gates the consensus build on, a `.done`
  marker per declared part-5 seed — stood at **34 and then 36 of 60**. I told the owner twice that the queue was
  finishing. It was not, and the build gate was never going to fire on that reading.
  - Nothing measured is affected: the gate always used the right counter, so no build could have started early.
  - The monitor now reports the **same number the gate uses**. The lesson is the plain one: a progress display that
    counts a different thing from the gate it claims to track will be believed, and a directory shared by two
    campaigns is not a campaign's progress.

- **R-BEST-2: `PHerc0826_small|auto_grown_20260918144212741` under TTA — BLANK, 0 flagged of 4 valid units
  (container clock 2026-09-19 06:35 UTC).** 2.02 cm² on-sheet, **on-sheet CT std 45.44 — the highest in the corpus,
  above the w040 control's 43.1** — forward 0.2991, reverse 0.3254, margin **−0.0263**, best single unit **−0.0220**,
  and `fwd_frac_gt_0p75` **exactly 0.00000**. Map pair re-checked by hand: sound, both 1.0000 non-zero.
  - **This is the most informative negative of the R-SMALL population**, because it is the one member with no texture
    caveat: the two others owed (CT std 8.63 and 10.05) sit at a quarter of the control's texture and their elevated
    responses are the artefact this file already documents. On a surface with *more* papyrus texture than the
    known-text control, the reader returns a **negative margin and not one pixel above 0.75**. Its plain read agreed
    at margin −0.0272.
  - It is a 40-generation interior trace at 2.02 cm², so it is small; the verdict bears on this sheet, not on
    interiors in general.

### The last free canvas in the project has been read (container clock 2026-09-19 07:30 UTC): BLANK, 0 flagged of 7 valid units

- `PHerc1447|team_20251105093211-z_dbg_gen_00320` — the flattened team mesh, the best-parameterised surface we hold
  (**p90 sag 7.96 µm against the w040 known-text control's 9.93**) — read plain, seed42, both depth orders, after
  **3 h 40 m** of inference over 2951 patches.
- **Result: BLANK. 7.08 cm² on-sheet, 7 valid 0.5 cm² units (3.50 cm² of valid area), 0 flagged.** Crest ratio 1.243
  (passes, slice 13 of 31). Forward mean 0.3118, reverse 0.3194, whole-map margin **−0.0077**; the best single unit
  reaches forward 0.3352 and margin **+0.0100**, an eighth of the frozen +0.08 bar. `fwd_frac_gt_0p75` **0.0008**,
  and the largest region above 0.5 is **2.44 mm²** — smaller than a single Herculaneum capital's footprint.
  On-sheet CT std 29.08. **Map pair re-checked by hand: sound**, both 0.1184 non-zero with identical footprints.
- **The thin-footprint caveat recorded in advance held, and is smaller than feared**: 7 of 144 grid units were valid,
  so 3.50 cm² of the 7.08 cm² on-sheet area reached rule 5.5 — half, not nothing. The verdict is a real negative on
  half the surface, not an artefact of the parameterisation's footprint.
- **With this read, every published team segment across all 23 eligible volumes has been read.** There is no free
  canvas anywhere. Every further cm² costs tracing.

- **R-BEST-2: `PHerc0826_small|auto_grown_20260918152701336` under TTA — BLANK, 0 flagged of 4 valid units
  (container clock 2026-09-19 07:40 UTC).** On-sheet CT std **8.63, the lowest in the corpus**, forward mean
  **0.4522**, margin **+0.0003**, best single unit **+0.0194**, `fwd_frac_gt_0p75` **0.0049**. Pair sound.
  - **This is the texture prediction meeting its test.** The caveat written before these reads said an elevated
    forward level on a near-textureless render is most simply explained by normalisation stretching noise, and that
    it should not be read as ink. Here the forward level is **0.4522 — above the w040 control's own known-TEXT units
    (0.4109 median)** — while the margin is **+0.0003**, i.e. the reverse pass answers the same. A response with no
    depth asymmetry at all is exactly what noise amplification looks like, and exactly what ink does not look like.
  - Set against its high-texture sibling read an hour earlier (CT std 45.44, forward 0.2991, margin −0.0263,
    `frac>0.75` 0.00000), the pair makes the point on one scroll, one budget, one recipe: **the forward level tracks
    how little texture the render has, and the margin — the thing rule 5.5 actually decides on — stays at zero in
    both.**
  - One member of the declared population remains: `auto_grown_20260918155811706` (CT std 10.05).

- **The part-5 consensus build nearly did not start, because a process check matched its own launcher (fixed,
  container clock 2026-09-19 07:44 UTC).** `ggp5_when_ready.sh` guarded the build with
  `pgrep -fc "dense_loop.sh $sc"`, which matches **any** process whose command line contains that string — including
  the shell that launched the script. With both dense queues already finished and logged ("part 1 dense queue done
  (84 patches)", "part 0 dense queue done (85 patches)") it refused with "a dense loop is still running". Fixed to
  check the loops' **own pid files** (`dense_loop_*.pid`, `kill -0`), both confirmed dead. This is the same
  self-matching family as the `pkill -f` hazard already on record.
- **G-GP part 5 build started**: **86 sources** (1 seed patch + 85 campaign traces) against the 26 that produced the
  5.162 cm² surface, at the team's own `consensus_default_th: 6`, same seed `3590 2095 4179`, everything else
  identical. Part 5b (threshold 4) follows from the identical source set, and the geometry gate decides whether its
  extra area is earned.

### G-GP part 5 RESULT (container clock 2026-09-19 07:46 UTC): 9.52 cm², both geometry bars met, the AREA bar MISSED by 0.48 cm²

- **86 sources** (1 seed patch + 85 campaign traces) at the team's own `consensus_default_th: 6`, seed `3590 2095
  4179`, everything else identical to part 4.
  | | part 4 (26 sources) | **part 5 (86 sources)** | bar G-GP-5 |
  |---|---|---|---|
  | consensus surface area | 5.162 cm² | **9.52 cm²** | ≥ 10 cm² |
  | transverse self-intersections | 0.00 /cm² | **0.00 /cm²** | ≤ 1.42 /cm² |
  | p90 sag (matched baseline) | 5.11 µm | **4.85 µm** | ≤ 9.93 µm |
  | p90 anisotropy | – | **1.21** | – |
  | nodes | – | 20 692 | – |
- **VERDICT on bar G-GP-5: the two geometry bars are MET and the area bar is MISSED.** 9.52 cm² against 10 cm² — short
  by **0.48 cm², 4.8 %**. The bar was written before the run and is not moved to meet the number. **The approach
  scaled almost exactly as projected** (the interim projection at 29 traces was 10.9-13.4 cm², labelled a projection),
  and it did so *while improving* geometry: sag fell from 5.11 to 4.85 µm and crossings stayed at zero as the surface
  nearly doubled. The declaration does not gate reading on the area bar, so the surface is read.
- **G-GP part 5b: its premise is refuted by measurement.** At `consensus_default_th: 4`, from the **identical** source
  set, the consensus came out at **3.98 cm² — smaller than part 5's 9.52**, not larger. It passed the geometry gate
  (0.00 crossings/cm², p90 sag 5.05 µm) and was admitted for reading on those bars, but the area it was declared to
  buy does not exist. **A lower agreement threshold admits more weakly-supported points, and the growth wanders and
  terminates earlier rather than spreading further.** The `patch_agreement` upper bound (9.26 cm² at threshold 4
  against 5.62 at threshold 6, measured at 29 sources) does **not** predict what the grower actually produces — that
  instrument bounds where six patches agree, not where a consensus surface can hold together.
- Both surfaces are being read now on the plain screening recipe, each under its own ledger key.

- **Disk: two completed gates' bulk artefacts removed (container clock 2026-09-19 07:58 UTC).** Free space was back at
  5.3 GB with R-SMALL-2's two tracers writing normal grids, and the part-5 consensus still has to render.
  - `gates/w028_judge_ref` (**341 MB**: `reference_u8.npy`, the three mask arrays, the preview) — Gate C and the w028
    unlabelled judge are complete, their reference numbers (0.784 plain / 0.823 TTA) are on record, and the
    **scored JSONs are kept**. The reference is rebuildable from the team's public w028 data.
  - `gates/gateA_crop` (**121 MB**: the four `crop2048_*.tif` prediction maps) — Gate A's crop arm is complete and its
    **four `auc_crop2048_*.json` scorings are kept**, which are the result; the maps were the intermediate.
  - Nothing declared and unfinished reads either. Every gate JSON, every ledger line and every RULES number stands.

### R-BEST-2 COMPLETE: the confirmatory reader UN-FLAGS the corpus's second flagged unit (container clock 2026-09-19 08:10 UTC)

- `PHerc0826_small|auto_grown_20260918155811706` under TTA — **BLANK, 0 flagged of 4 valid units**. On-sheet CT std
  **10.05**, forward **0.4951**, margin **+0.0192**, best single unit **+0.0586**, `fwd_frac_gt_0p75` 0.0091. Pair sound.
- **Its PLAIN read was NOT ESTABLISHED with 1 flagged unit** (forward 0.4980, margin +0.0320). The confirmatory
  recipe reads the same surface and **flags nothing**. G-B-43 admitted seed43 as a FILTER that "never flags and never
  un-flags"; TTA is not that filter — it is a different recipe under its own ledger key — so this is **two recipes
  disagreeing on one unit**, recorded as such. The plain verdict stands as recorded; the TTA verdict stands as
  recorded; neither is edited.
- **The disagreement is exactly where the texture finding predicts it.** This is the second-lowest-texture render in
  the corpus (CT std 10.05 against a corpus median of 35.5 and the control's 43.1), and the unit that flagged plain
  sat at margin +0.0320 whole-map — a third of the bar — on a render with almost nothing in it. The one flagged unit
  the corpus had on this surface does not survive a second recipe.
- **With this read the declared R-BEST-2 population is complete.** Every member read; **not one flagged cluster
  anywhere**; the only two flagged units the project has ever produced are the single unit on
  `PHerc0826|auto_grown_20260917090724211` (which stands, 1 of 4, margin +0.0873) and this one, which does not.

## R-DEFICIT  What 113 screened units actually say (measured 2026-09-19 08:30 container clock; a measurement, not a bar)

- **The question this answers.** The project has read a lot of canvas and produced no candidate. "No candidate yet"
  is not by itself evidence of anything — the frozen screen is a *screen*, and the honest way to ask whether our
  negatives mean anything is to compare the **unit-level flag rate** against the one canvas where the answer is known.
- **Population, fixed by the recipe and not by the result.** Every unique surface ever read on the **plain screening
  recipe at the centre window** (the declared screening call), one row per surface, taking `n_valid` and `n_flagged`
  from the recorded rule 5.5 table. Confirmatory recipes (TTA, seed43) and off-centre windows are excluded because
  they are different recipes under their own ledger keys, not extra canvas. That is **30 surfaces, 113 valid units,
  56.50 cm²**.
- **Control**: the w040 known-text full canvas scored by R-CTRL55 — **71 valid units, 35.47 cm², 7 flagged, clusters
  4/2/1**, i.e. one qualifying (≥ 3 adjacent) cluster.

  | | control w040 (known text) | corpus screening |
  |---|---|---|
  | valid 0.5 cm² units | 71 | **113** |
  | valid area | 35.47 cm² | **56.50 cm²** |
  | flagged units | 7 (**9.86 %**) | **1 (0.88 %)** |
  | qualifying clusters | 1 | **0** |

- **Fisher exact, one-sided, 1/113 against 7/71: p = 0.0058.** (Treating the control rate as known gives a binomial
  P(X ≤ 1) = 1.1 × 10⁻⁴; Fisher is quoted because it carries the control's own sampling uncertainty and is the weaker,
  honest number.) **Expected flagged units at the control rate: 11.1. Observed: 1.**
- **The cluster count carries almost none of this information, and saying so matters.** At the control's cluster
  density the 113 units predict **1.59** qualifying clusters, and P(0) = **0.20**. *Our zero candidates would be an
  unremarkable outcome on genuinely text-bearing canvas.* Anyone reading "0 candidates in 56 cm²" as proof of absence
  is over-reading it by a factor of five. **It is the flag rate, not the candidate count, that separates our canvas
  from the control.**
- **What follows for strategy, stated as a prediction and not as a result.** More canvas of the kind already
  screened — the outer band, r/R ≳ 0.6, where R-RADIAL shows essentially all readable area sits — is predicted to
  keep returning the measured 0.88 % rate, at which adjacent triples do not form. The two live paths are the ones
  already declared: **inner canvas** (R-SMALL-2) and **concentrated consensus canvas** (G-GP part 5).
- **What this does NOT establish, and the distinction is the whole point.** A low flag rate has two explanations that
  this measurement cannot separate: (a) the canvas carries no ink, or (b) the detector does not transfer from the
  control volume to the 2025-scan volumes. **R-BLANK, declared below before it is run, is the test that separates
  them.** No bar, threshold or verdict changes here.

## R-BLANK  Is the corpus's margin what this detector returns on BLANK papyrus, or below it? (declared 2026-09-19 08:35 container clock, BEFORE the measurement; interpretation fixed here, before the numbers)

- **Why.** R-POP put the corpus at a whole-map margin of **+0.0014** while the control's *least-inked* bin sits at
  **+0.0131** — nine times higher. If +0.0131 is simply what blank papyrus reads on control data, then our numbers
  are below the detector's own floor, and ink-absence is not a sufficient explanation. That is a question about the
  detector, answerable from files already on disk, at zero inference cost.
- **Method, fixed now.** Control maps: the same `gates/gateA/w040_full_plain.tif` and `..._reverse.tif`
  (6400 × 7980 at 9.362 µm/px) that R-CTRL55 scored. Labels: the published `labels/w040/w040_inklabels.zarr`
  level 0 (28 × 6400 × 7980 uint8), projected to 2D by **any over z**. Grid: **the grid R-CTRL55 recorded** —
  side 755 px, origin (94, 188), validity ≥ 90 % on-sheet — not a new one. For each valid unit: labelled ink
  fraction, forward mean, reverse mean, margin.
- **Statistic.** The control's **blank baseline** = the *median margin of valid units whose labelled ink fraction is
  exactly 0.000*. **If fewer than 5 such units exist the result is reported UNDERPOWERED and no conclusion is drawn.**
- **Interpretation, fixed before the numbers.**
  - **Blank baseline ≤ +0.0042** (≤ 3× the corpus's +0.0014): the corpus numbers are what this detector returns on
    papyrus without ink. Our negatives mean *no ink on this canvas*, the strategy is unchanged, and the search moves
    inward.
  - **Blank baseline > +0.0042**: the detector returns more depth asymmetry on *labelled-blank control papyrus* than
    on our entire corpus. Ink-absence alone does not explain that, and a **domain gap between the control volume and
    the 2025-scan volumes becomes a live alternative explanation of every corpus negative** — which would have to be
    stated beside every one of them.
- **Caveat recorded in advance, because it cuts one way only.** The w040 labels mark ink a human could see *after*
  the text was recovered. "Unlabelled" is not "ink-free"; a zero-fraction unit may hold faint ink. That biases the
  blank baseline **upward**, which makes the second outcome *easier* to reach. So the second outcome is the weaker
  claim and must be quoted with this caveat attached; the first is the stronger.
- **This changes no bar, no threshold and no verdict.** It changes what our negatives are allowed to be said to mean.

### R-BLANK RESULT (measured 2026-09-19 08:34 UTC, `scripts/rblank.py`, `gates/rblank/rblank.json`): DETECTOR-FLOOR-ABOVE-CORPUS

| set (w040 control, 71 valid units, frozen grid side 755 px origin (94, 188)) | n | median margin | p10 | p90 | median fwd | median φ | flagged |
|---|---|---|---|---|---|---|---|
| labelled-BLANK (φ = 0.0000) | **44** | **+0.0134** | −0.0088 | +0.0590 | 0.3294 | 0.0000 | 1 |
| labelled-INKED (φ > 0) | 27 | +0.0438 | +0.0035 | +0.0978 | 0.3506 | 0.0322 | 6 |
| all valid | 71 | +0.0277 | −0.0078 | +0.0796 | 0.3368 | 0.0000 | 7 |

- **Blank baseline +0.0134 against the declared bar +0.0042: the second outcome, as written before the numbers.**
  Labelled ink covers 1.46 % of the control canvas (any over z); 44 of 71 valid units contain not one labelled pixel.
- **The comparison is like-for-like, and that was checked rather than assumed.** The declared comparator (+0.0014) is a
  *whole-map* margin while the statistic here is a *median over units*, so the two could have been different animals.
  On the control they are not: whole-map on-sheet margin **+0.0255** (fwd 0.3354, rev 0.3099, 46.3 Mpx) against a
  median-over-valid-units of **+0.0277** — an 8 % difference. The corpus's +0.0014 sits **18×** below the control's
  whole-map margin and **10×** below its labelled-blank median.
- **The corpus's own per-unit medians could not be recomputed**: all 30 plain screening reads had their maps pruned
  (`--delete-renders` plus the disk guard). The running G-GP part-5 reads keep theirs, so the like-for-like per-unit
  figure will be measured on those and reported with them.
- **What this does and does not license.** Ink-absence alone does not explain a corpus margin ten times below what
  this detector returns on control papyrus carrying no labelled ink. A **domain gap between the control volume and
  the 2025-scan volumes is now a live alternative explanation of every corpus negative**, and is stated beside them.
  It is not established: the caveat recorded in the declaration cuts exactly here, and is why part 2 below exists.
- No bar, threshold or verdict changes. **Every corpus verdict stands exactly as recorded.**

### R-BLANK part 2 — is the +0.0134 floor unlabelled ink, or the detector? (declared 2026-09-19 08:34 UTC, BEFORE the measurement)

- **Why this is not a test hunted until one passes.** The R-BLANK declaration recorded, in advance, that "unlabelled"
  is not "ink-free" and that the bias runs *upward*, making the domain-gap outcome easier to reach. Part 2 converts
  that pre-recorded caveat into a measurement. It can only **weaken or confirm a caveat on our own claim**; it cannot
  flag a unit, create a candidate, or change any verdict, and no third variant will be declared after it.
- **Method, fixed now.** Same maps, same labels, same frozen grid. Take the 2D label mask (any over z), max-pool it
  8× to 800 × 998, distance-transform the complement, and give every valid unit the **minimum distance from any of its
  pixels to the nearest labelled ink pixel** (in µm; the 8× pooling makes the distance conservative — it can only
  shrink). Report the median margin of valid units in distance bands **0 (touching ink), >0–1 mm, 1–2 mm, 2–4 mm,
  ≥ 4 mm**, each band's n stated.
- **Interpretation, fixed before the numbers.**
  - **The median margin falls to ≤ +0.0042 in the outermost band that has ≥ 5 units** → unlabelled ink explains the
    +0.0134 floor, the detector's true blank-papyrus floor is at the corpus level, and **R-BLANK's domain-gap reading
    is WITHDRAWN**: the corpus negatives mean no ink on that canvas.
  - **The median margin stays above +0.0042 in every band with ≥ 5 units** → the floor is not explained by proximity
    to text, and the domain-gap reading **STANDS** as a live alternative.
  - **No band beyond "touching ink" has ≥ 5 units** → UNDERPOWERED, and the domain-gap reading stands *unresolved*,
    which is weaker than standing.
- Row pitch on this control is 2–4 mm (the frozen rule's own band), so the 2–4 mm and ≥ 4 mm bands are "at least one
  line of text away" and "at least a column away". That is why those cut points and not others.

### R-BLANK part 2 RESULT (2026-09-19 08:45 UTC, `scripts/rblank2.py`, `gates/rblank/rblank2.json`): FLOOR-NOT-EXPLAINED-BY-PROXIMITY

| band (distance from the unit's nearest pixel to the nearest labelled ink pixel) | n | median margin | median fwd | flagged |
|---|---|---|---|---|
| touching ink | 28 | **+0.0409** | 0.3503 | 6 |
| > 0–1 mm | 4 | +0.0302 | 0.3539 | 0 |
| 1–2 mm | 2 | +0.0102 | 0.3199 | 0 |
| 2–4 mm | 8 | +0.0119 | 0.3301 | 0 |
| **≥ 4 mm** | **29** | **+0.0131** | 0.3229 | 1 |

- The margin falls steeply off the text — **+0.0409 → ~+0.0120** — and then **plateaus**. Twenty-nine valid units, the
  largest band of the five, sit at least one full line of text away from any labelled pixel and still read **+0.0131**,
  three times the declared bar. **The declared outcome is the second one: the floor is not explained by proximity to
  text, and R-BLANK's domain-gap reading STANDS as a live alternative.**
- A **defect found by its own test before the run**: the first implementation took the distance between max-pooled
  cell *centres* and called it conservative. It is not — a pixel sits up to (pool/2)·√2 from its cell centre at either
  end, so centre-to-centre can *over*state the true pixel distance by up to 106 µm, which is the wrong direction for a
  declaration that promised the distance "can only shrink". Fixed to `max(0, D − √2) · pool · µm`, which is a provable
  lower bound on the pixel distance, and pinned by a randomised property test over twelve ink layouts. The declaration
  was honoured by fixing the code, not by loosening the wording.

### The domain-gap reading is then NARROWED to almost nothing by provenance (2026-09-19 08:45 UTC)

- **The w040 control is PHerc0139, volume `20250728140407-9.362um-1.2m-113keV-masked.zarr`** (docs/MASTER_PROMPT_v4.md,
  confirmed against the live S3 listing). PHerc0826, PHerc0358 and PHerc1203 are
  `…-9.362um-1.2m-113keV-masked.zarr`. **Same beamline configuration, same energy, same voxel size, same 2025
  campaign, same masking.** PHerc1447 is 8.640 µm / 116 keV, the one real instrument difference in the corpus.
- The renderer is byte-identical to the team's on this very control (G-B), the model and recipe are the same, and the
  **crest centring matches**: corpus crest slice 11–16, valid-unit-weighted mean **13.19** of 28, against the control's
  12. Sheets are as well centred in our renders as in the team's, so a mis-centred reading window is not the
  explanation either. *A scanner-level domain gap between control and corpus is therefore not available as a general
  excuse; whatever separates them is downstream of the scan.*

### R-ORIENT — the confound R-DEFICIT had to survive, tested and survived (2026-09-19 08:45 UTC)

- **The confound.** Rule 5.5 flags on a **signed** margin (fwd − rev ≥ 0.08). On the team's meshes `--flip-normals`
  gives the trained orientation; **on our own traces the sheet orientation is unknown**, so "forward" is a coin flip
  per surface. A signed rule cannot flag a surface read backwards, and comparing our signed flag rate against a
  control whose orientation is known would then be unfair by construction.
- **Measured, from files already on disk.** `rule55_depth_swapped` stores the per-unit table with the depth order
  reversed, so the forward margin of every unit is recoverable as its negation. Over the plain screening recipe:
  **118 units on 31 surfaces**, median **+0.0007**, mean **−0.0002**, p10 **−0.0352**, p90 **+0.0357**, **50.8 % positive**,
  and **15 of 31 surfaces have a negative mean**. The signed distribution is symmetric about zero — exactly what a
  per-surface orientation coin flip looks like.
- **And it costs us nothing.** Over all 52 reads carrying the field, the **depth-swap tripwire has never fired**.
  Across all 189 reconstructed unit margins the extremes are **−0.0714 and +0.0873**: two units reach the +0.08 bar
  forwards, **none reaches it backwards**, and the most negative unit in the project is 0.009 short of the bar.
  **Orientation correction adds zero flagged units, so R-DEFICIT's conclusion stands unchanged** — the confound was
  real, was tested rather than waved away, and does not explain the deficit.
- **What the orientation-free statistic says instead, and this is the sharpest number in the file.** Take the
  magnitude, which orientation cannot touch: the corpus's **median |per-surface mean margin| is +0.0122**. The control's
  **labelled-blank** units sit at **+0.0134** and its **labelled-inked** units at **+0.0438**.

  > **Our canvas does not read like a detector that has stopped working. It reads, to within 9 %, like control papyrus
  > with no ink on it — and nothing like control papyrus with ink on it.**

- That leaves exactly two live explanations, and they are the two this project can still act on: **the canvas we can
  reach genuinely carries no ink**, or **our own geometry degrades text to blank-level signal**. Nothing measured so
  far separates them. No bar, threshold or verdict changes.

## G-OWN  The one link in the chain that was never gated against known text (declared 2026-09-19 08:46 UTC, BEFORE the trace is started; bars and interpretation fixed here, before any data)

- **The gap, named plainly.** Gate A validated the **model** on known text. Gate B validated the **renderer** on known
  text, byte-identically. Gate C and the w028 judge validated the **calibration**. R-CTRL55 validated the **frozen
  rule** on known text, and R-SYM/R-SENS/R-POP validated its behaviour. **Every component has a positive control on
  known text except the one this project built itself: `vc_grow_seg_from_seed` growing our own surface.** Every
  control to date was run on the *team's* w040 mesh. Our own traced geometry has never once been asked to reproduce
  known text, and it sits exactly where R-ORIENT says the signal is being lost.
- **Why it is now runnable, where it was not before.** PHerc0139 — the control scroll — publishes the **same**
  surface-prediction volume our tracer consumes on the corpus:
  `PHerc0139/representations/predictions/surfaces/20250728140407-surface-20260413222639-surface-m7-L0-th0.2.zarr`,
  the same `20260413222639-surface-m7-L0-th0.2` model as PHerc0826's, with its normal grids. The control is the same
  9.362 µm / 1.2 m / 113 keV configuration as the corpus. So our tracer can be run **on known text, under the corpus
  recipe, changing nothing**.
[line withheld: prize-candidate detail under review]
  whose surrounding 0.5 cm² footprint carries the **most labelled ink of any fully-valid neighbourhood on the sheet
  (19.65 %, against a canvas mean of 1.46 %)** — grid cell (181, 104), canvas pixel (3620, 2080), **level-0 voxel
  (4192.9, 3111.1, 5910.0)**. Seeding from a point *on the team mesh* means any divergence is the tracer's doing and
  nothing else's.
- **Run**: `vc_grow_seg_from_seed` on that seed with the corpus `params.json` — `generations: 60`, `min_area_cm: 0.2`,
  `voxelsize: 9.362`, published normal grids — then the same QC (5.8), the same renderer, the same plain seed42 call
  at `--direction both`, the same rule 5.5. Nothing is tuned for this run.
- **Admissibility gate (not a result; a run that fails it is re-seeded, never reinterpreted).** The trace must land on
  the known-text sheet: **≥ 50 % of its valid grid points within 449 µm (one measured wrap spacing) of the w040 team
  mesh surface**. Below that the run is **VOID-OFF-SHEET** and says nothing about anything.
- **Primary statistic: the whole-map on-sheet depth margin**, mean(forward) − mean(reverse) over on-sheet pixels —
  the same number measured at **+0.0255** on the team's mesh of this very region and at **+0.0014** across our corpus.
  It is chosen over a unit count because a single trace yields only a handful of units, and this statistic rests on
  millions of pixels. Because our trace's orientation is unknown (R-ORIENT), the statistic is **|margin|**, and the
  sign is reported separately.
- **Bars, fixed now.**
  - **PASS — |margin| ≥ +0.0128** (half the team mesh's +0.0255 on the same text). Our tracer's geometry preserves the
    depth-asymmetric ink signal. The corpus negatives are then about the corpus, and the binding constraint stays
    canvas: more area, further inward.
  - **COLLAPSE — |margin| ≤ +0.0042** (the R-BLANK bar; indistinguishable from our corpus's +0.0014 and from control
    *blank* papyrus). **Our own geometry destroys the ink signal on a sheet we know carries text.** Every corpus
    negative is then confounded by it, the binding constraint is geometry quality rather than canvas area, and the
    fix is upstream of everything this project has been doing for two days.
  - **PARTIAL — between the two.** The geometry costs a measurable fraction of the signal; that fraction is quoted,
    and both readings stay live.
- **Reported alongside, as description and not as bars** (the unit count is too small to carry a bar): rule 5.5 on the
  trace — valid units, flagged, clusters, and the per-unit margins; the trace's area, p90 sag and transverse crossing
  rate against the team mesh's 9.93 µm and 1.42/cm²; and its labelled-ink fraction, so the comparison is like for like.
- **This cannot produce a submission and is not meant to.** PHerc0139 is a control, not one of the 23 eligible
  volumes, and nothing measured here flags, un-flags or alters any corpus verdict. It decides what our negatives are
  allowed to mean, and where the remaining hours go.

### G-GP part 5, first verdict (2026-09-19 08:48 UTC): the 9.48 cm² consensus companion reads BLANK, 0 flagged of 5 valid units

- `PHerc0826_cons_part5|auto_grown_20260919074515012` (9.48 cm² surface), plain seed42, both depth orders:
  **BLANK.** onsheet 5.74 ctstd 35.374206542577504 crest {'ratio': 2.774, 'crest_slice': 15, 'central_bounds': [6, 21], 'min_ratio': 1.2, 'passed': True, 'reason': None} slice 15 valid 5 flagged 0 mean_margin -0.0113 best +0.0301
- **Map pair verified by hand before the verdict was accepted**: `map_integrity.py` over all 61 pairs in the project —
  **61 sound, 0 SUSPECT**. This is the check that caught and reversed R-DEPTH's ADMITTED verdict; it is run on every
  read now, not on suspicion.
- The surface is the best-conditioned canvas the project has built — 86 sources, 0.00 transverse crossings/cm², p90
  sag 4.85 µm against the control's 9.93 — and it reads at a **mean unit margin of −0.0113**, magnitude 0.0113,
  which is R-ORIENT's corpus level (|0.0122|) and the control's *blank* level (+0.0134), not its inked level (+0.0438).
  **Better geometry, by every geometric measure we have, did not move the ink statistic.** That is the observation
  G-OWN was declared to explain, and it was recorded before G-OWN returns anything.
- Its 9.52 cm² sibling `auto_trace_20260919074515229_seed_3590p000_2095p000_4179p000` is in inference now; the two
  part-5b surfaces follow.

- **Disk: 748 MB of the vendored villa checkout removed (2026-09-19 09:03 UTC).** `external/villa/scrollprize.org` (617 MB, the public
  website's source and image assets) and `external/villa/deprecated` (131 MB). Neither is imported, referenced by any
  script, gate, record or RULES entry — checked by grep before removal — and `import vesuvius` plus the inference
  module were verified to still resolve out of `external/villa/vesuvius` afterwards. The checkout is `.gitignore`d and
  re-clonable. Free space went 5.3 → 6.6 GB, which keeps the disk guard in its ROOMY tier: pruning a live tracer's
  normal grids is measured at a ~4× slowdown, and the G-OWN trace is the job that must not be slowed right now.

- **G-OWN will also be reported against an AREA-MATCHED control, declared here before it is computed (2026-09-19 09:03 UTC).** The
  declared bars compare our trace to the team mesh's **+0.0255 over its whole 40.6 cm² canvas**; our trace will cover
  a few cm² of it. So the same statistic will additionally be computed on the **team's own maps restricted to the
  canvas region our trace covers** (each trace point → its nearest w040 mesh node → that node's canvas pixel block),
  giving a like-for-like ratio "signal our geometry keeps / signal the team's mesh gets on the same papyrus". **This is
  descriptive and cannot move the verdict**, which stays on the declared bar against +0.0255; it is reported so the
  cost of our geometry is quoted as a fraction of what that exact patch of sheet is known to yield.

## R-SHAPE  Our canvas cannot form a candidate even if it were pure text — and this CORRECTS my own figure (2026-09-19 09:06 UTC, `scripts/cluster_power.py`, `gates/cluster_power.json`)

- **The correction first.** R-DEFICIT, recorded earlier today, put the expected number of qualifying clusters from our
  canvas at **1.59** by scaling the control's cluster *density* (one per 71 valid units). **That figure silently
  assumed our units are laid out as the control's are — one large contiguous 71-unit grid. They are not, and the
  assumption was mine, unstated.** Computing it from the **actual recorded per-surface layouts** instead:

  > **Expected candidates from everything we have ever screened, if every unit of it were as inked as the known-text
  > control: 0.079.** Twenty times lower than the number I recorded.

- **Method** (nothing to pre-register: no threshold is chosen). Reconstruct each surface's valid-unit occupancy grid
  from its recorded rule 5.5 table (using the swapped table's rows where the forward list is empty, per R-ORIENT),
  flag each valid unit independently at the control's **own measured rate 7/71 = 0.0986**, and count 4-connected
  triples. Monte Carlo, 20 000 trials, fixed seed 20260919. Six tests pin the behaviour, including that three
  diagonally-touching units are *not* a candidate and that one contiguous grid beats three islands of the same total.
- **Why it is so low. Rule 5.5 needs three 4-connected units, and our surfaces are too small and too ragged to hold
  three.** corpus: on-sheet 110.94 cm2 -> valid 59.00 cm2 = 53.2% unit validity over 31 surfaces
control w040: on-sheet 40.60 cm2 -> valid 35.47 cm2 = 87.4%% unit validity, 71 units on ONE surface
median valid units per corpus surface: 4.0 ; max 9
  - **10 of 31 surfaces have fewer than 3 valid units and therefore cannot produce a candidate at any flag rate.**
  - The best surface in the whole project is `PHerc1447|team_20250703034159599` at 9 valid units, P(triple) = 0.0122.
  - Our unit **validity** — the fraction of on-sheet area that lands in a ≥ 90 %-on-sheet unit — runs at about
    **half the control's**, because our rendered footprints are ragged where the control's is a clean rectangle.
- **What survives and what does not.**
  - **R-DEFICIT's unit-level test is untouched**: 1 flagged of 113 against 7 of 71 is a comparison of *rates*, which
    no layout assumption enters. Fisher exact one-sided **p = 0.0058** stands.
  - **R-DEFICIT's cluster arithmetic is superseded by this entry.** The earlier text already said the cluster count
    carried almost no information; it carries even less than that — **our zero candidates are the expected outcome
    even on perfect text.** Neither entry is edited; this one corrects the other, as the record requires.
- **This renames the binding constraint, for the third and most precise time.** It was called "area and breadth",
  corrected by R-RADIAL to "interior geometry", and is now, measurably: **contiguous, fully-on-sheet canvas per
  surface.** Total area does not buy candidates; three adjacent valid units do. A single clean 20-unit surface is
  worth more than the entire 59 cm² we have screened. **That, and not more cm², is what the remaining effort must
  produce** — and it is what G-GP part 5 was reaching for when it returned 9.48 cm² of surface that yielded only
  5.74 cm² on-sheet and **5 valid units**.

### R-SHAPE, checked against its own weakest assumption (2026-09-19 09:08 UTC) — and the assumption fails in MY favour, so it is stated

- R-SHAPE flags each unit **independently**. Real ink is not independent: a column of text inks adjacent units
  together. Tested on the control's own outcome — 7 flagged of 71 on a contiguous grid, 40 000 draws:

  | | independent flagging | observed on the control |
  |---|---|---|
  | P(largest cluster ≥ 3) | **0.1606** | — |
  | P(largest cluster ≥ 4) | **0.0257** | **largest = 4** (sizes 4, 2, 1) |
  | mean largest cluster | 1.87 | 4 |

- **The control's 4-unit cluster is a 1-in-39 event under independence.** Real ink therefore clusters far more than
  the model assumes, and **R-SHAPE's 0.079 is a LOWER bound, not an estimate.** Scaling by the control's own measured
  excess (1 qualifying cluster observed where independence gives 0.16) puts the corrected figure near **0.5** — still
  below one, and quoted as the rough factor it is, not as a computed number.
- **I am recording this because it weakens my own conclusion.** The strong form — "our canvas cannot form a candidate"
  — is not supported. The supported form is: **zero candidates is the expected outcome from canvas of this size and
  shape, whether the true expectation is 0.08 or 0.5.** The strategic consequence does not move: **contiguous
  fully-on-sheet units per surface is the quantity to maximise**, and nothing we have built comes close.
- **And the scale of what "close" means, measured the same way** (contiguous square grids, control flag rate,
  6 000 draws each):

  | clean contiguous valid units | valid cm² | P(a qualifying candidate) |
  |---|---|---|
  | 9 | 4.5 | 0.017 |
  | 25 | 12.5 | 0.066 |
  | 49 | 24.5 | 0.138 |
  | 71 (the control's own canvas) | 35.5 | ≈ 0.18 |
  | 100 | 50.0 | 0.274 |

  > **Rule 5.5's PROMISING CANDIDATE is roughly a one-in-five event per 35 cm² of clean, contiguous, KNOWN-TEXT
  > canvas.** The control fired once on exactly such a canvas. Our best single surface holds **9** valid units.
  > This is the honest scale of the gap, and no amount of small surfaces closes it.

## R-COVER9  Our surfaces are HALF OFF THE PAPYRUS, and the bigger they get the worse it is (2026-09-19 09:10 UTC; a measurement, not a bar)

- **A false alarm of my own, resolved first.** Recomputing part 5's unit table from the model maps' own footprint
  `(fwd>0)|(rev>0)` gave 13 valid units where the read recorded 5, which looked like a defect. It is not.
  `read_chart.py` line 212 masks on the **CT render's middle slice > 0** — where the render actually sampled
  material — not on where the model happened to emit a probability. That is the correct, physical definition: the
  model returns a number for air too. **The recorded 5 stands and the reader is right.** But the 3.17 cm² between
  the two masks is not nothing: it is surface that carries model output and **no papyrus**.
- **Measured across all 31 screening reads** as papyrus coverage = on-sheet area / render canvas area:

  | | papyrus coverage |
  |---|---|
  | control w040 team mesh | **0.907** (R-COVER scores the same mesh 0.997 on its own per-layer measure) |
  | corpus median | **0.584** |
  | corpus p10 / p90 | 0.427 / 0.853 |
  | reads at or above the control | **3 of 31** |

- **This is the first geometric measure on which our surfaces are clearly WORSE than the control's**, and the others
  were not close calls in our favour: p90 sag 4.85 µm against 9.93, transverse crossings 0.00/cm² against 1.42.
  Our traces are smooth, non-self-intersecting, correctly centred — and **spend two fifths of their area off the
  papyrus altogether.**
- **The tension that names the target, and it is exactly backwards from how we have been buying canvas:**
  - the three best-covered surfaces in the project (0.942–0.948, *above* the control) are the **40-generation R-SMALL
    interior traces**, and each holds only **4 valid units**;
  - the **consensus surfaces — our whole route to large canvas — have among the worst coverage**: part 5 at **0.412**
    (5 valid of 18 units), part 4 at **0.427** (2 of 8).
  - Coverage and unit validity correlate at **r = 0.484** across the corpus.
  - **Growing bigger has been costing coverage.** A longer trace travels further along the spiral into sheet that is
    delaminated, crushed or absent, and the render finds nothing there. The small budget stops while still on
    intact papyrus.
- **So R-SHAPE's "contiguous fully-on-sheet units per surface" decomposes into two factors we can now measure
  separately: canvas size, which the consensus buys, and papyrus coverage, which it destroys.** Nothing we have built
  has both. No bar, threshold or verdict changes.

### R-COVER9 CORRECTED (2026-09-19 09:13 UTC): the measure is real, my reading of it was wrong

- **R-COVER9, recorded above, says "our surfaces are HALF OFF THE PAPYRUS". That reading is WRONG and is withdrawn
  here.** The numbers in it are correct; what they mean is not what I wrote. I found the error by testing two
  explanations of it, and both failed in a way that exposed the mistake.
- **Failed explanation 1 — a CT proxy for coverage** (`scripts/coverage_proxy.py`, written with the commitment, in its
  own docstring before it ran, that "the proxy is used for nothing unless it predicts"). Sampling the level-4 CT at
  each trace's grid points and scoring the fraction above the air level (R-COVER's 40 on the 8-bit scale):

  | surface | CT frac above air | rendered "coverage" |
  |---|---|---|
  | `PHerc0826_small` traces (×3) | **1.000** | 0.942–0.948 |
  | **cons part 4** | **0.857** | **0.427** |
  | **cons part 5** | **0.823** | **0.412** |

  Pearson r 0.43–0.63 over 9 surfaces, carried entirely by the small traces. **The proxy calls both consensus
  surfaces firmly on papyrus — which is the one case it had to catch. It is not usable and is used for nothing.**
- **Failed explanation 2 — nodes stretched across wrap gaps.** Median 3D distance between adjacent valid nodes, against
  the nominal 20 level-0 voxels: small traces **20.0–20.1**, consensus **20.0–20.1**, control **20.0**; fraction of
  edges beyond twice nominal **0.0000 on both consensus surfaces**, 0.0004 on the control. The consensus geometry is
  as regularly spaced as the control's. Not this either.
- **What it actually is.** The measure divides on-sheet area by the render's **bounding rectangle**, and for five of
  the seven surfaces tested it tracks the **grid fill fraction** — valid nodes over the tifxyz's rectangular node
  array — to within 5–17 %:

  | | grid | valid nodes | **grid fill** | rendered "coverage" | ratio |
  |---|---|---|---|---|---|
  | small traces | 82×82 | 6 084 | **0.905** | 0.942–0.948 | 1.04–1.05 |
  | **cons part 4** | 126×198 | 11 874 | **0.476** | 0.427 | 0.90 |
  | **cons part 5** | 174×258 | 22 228 | **0.495** | 0.412 | 0.83 |
  | control w040 | 320×399 | 110 046 | **0.862** | 0.907 | 1.05 |

- **The corrected statement.** Our consensus surfaces are not off the papyrus — their nodes sit on it and their
  spacing is clean. **They are RAGGED: they fill barely half of their own bounding grid** (0.476, 0.495) where the
  control fills 0.862 and a small single trace fills 0.905. A union of many overlapping traces is an irregular blob
  inscribed in a rectangle, and rule 5.5 needs 755 × 755 px blocks that are ≥ 90 % covered. Two of the seven surfaces
  (ratio 0.79 and 0.63) do lose area beyond grid fill, so some genuinely off-sheet rendering exists — it is simply not
  the dominant effect and not what distinguishes the consensus surfaces.
- **The strategic conclusion survives in corrected form, and is sharper for it.** R-SHAPE's target is not raw cm² and
  not "stay on the papyrus": it is **a compact, densely filled surface** — one whose outline is close to convex and
  whose grid is populated like the control's 0.862. The consensus method buys size and pays for it in raggedness, and
  that trade, not void contact, is what has kept every surface below three adjacent valid units.

## G-GP part 6  Optimise DENSITY, not area (declared 2026-09-19 09:15 UTC, BEFORE the build; bars fixed here, before the data)

- **Why, and what changed.** Part 5's declared bar was **area** (≥ 10 cm²). It got 9.52 cm² — and that surface reads
  **5 valid units** from a grid filled to **0.495**. R-SHAPE showed valid units are what a candidate is made of and
  area is not; R-COVER9-corrected showed the consensus buys area by becoming ragged. **Part 6 therefore optimises the
  quantity that matters and accepts less area for it.**
- **Run.** The **identical** 86-source set, the **identical** seed `3590 2095 4179`, everything else identical to
  part 5 — only `consensus_default_th` changes, from the team's 6 to **8 (part 6)** and **10 (part 6b)**. The knob is
  the one `vc_consensus.sh` already documents as existing "only so a LATER, separately declared experiment can vary
  it". Part 5b has already measured threshold 4, so the sweep will read 4, 6, 8, 10 on one source set.
- **Reported for every threshold**, whatever the outcome: surface area, grid shape, **grid fill fraction** (valid
  nodes ÷ array, the number R-COVER9-corrected identified), p90 sag and transverse crossings/cm² against the existing
  geometry gate (≤ 9.93 µm, ≤ 1.42/cm²), and — for any surface that passes that gate — the rule 5.5 table.
- **Bar, fixed now: part 6 is ADMITTED as an improvement over part 5 only if it yields MORE THAN 5 valid units** in
  its rule 5.5 table on the plain screening recipe. **Area is explicitly not a criterion here**; part 5's area bar is
  not re-used, not re-fought, and not moved.
- **Prediction recorded before the run, so that it can be wrong on the record:** grid fill rises with the threshold
  and area falls. **Whether valid units rise is genuinely open** — part 5b at threshold 4 gave *less* area *and* is
  the opposite end of the same knob, so the relation need not be monotone in the direction I expect.
- Part 6 creates no candidate by itself. Any flagged cluster it produces goes through protocol 9 exactly as any other
  read. It is queued **behind G-OWN**: if our tracer's geometry turns out to destroy the ink signal, a denser surface
  built the same way is not worth the compute, and that ordering is deliberate.

- **Disk: 1.1 GB freed without touching anything a declared run needs (2026-09-19 09:16 UTC).** Free space had fallen to **4.6 GB**,
  below the 5 GB floor, which would have put the guard into its tight tier and pruned the **G-OWN trace's** normal
  grids — a measured ~4× slowdown on the one job that must not be slowed. Removed: `pred_cache` (654 MB) and
  `pred_l0_cache` (16 KB), both **unreferenced by any script or doc** (checked by grep across `scripts/` and `docs/`
  before deleting), and four **orphan `render.zarr`** directories whose reads were stopped and never completed
  (207 MB). **Explicitly kept**: `pred_local` (G-GP part 6's `VC_VOLUME` reads it), `pred_l3_cache` (a test reads it),
  `w028_2um` (the supervisor references it), `ct_l4_cache` (every new trace's QC), and the **in-flight** part-5
  `auto_trace` render, whose inference is still running. Free space 4.6 → 6.9 GB; all three inferences survived.

### A DEFECT that would have made R-SMALL-2 unanswerable however long it ran (found and fixed 2026-09-19 09:21 UTC)

- **R-SMALL-2's bar is a READABLE FRACTION** — "over at least 15 such traces, the readable fraction must reach ≥ 30 %".
  Its traces land in `patches/<scroll>_rs2`. **The supervisor's reduced-budget read loop was hard-coded to
  `patches/<scroll>_small`.** So `_rs2` had a tracer and **no reader**: 15 traces had been grown and **not one had
  been QC'd or read**. Checked directly before the fix — 15 trace directories, 15 with no `patch_qc.json` and no
  `read_*` directory, readable fraction 0/15 **not because the geometry failed but because nothing ever looked at it**.
- **This is the "committing is not deploying" family again, one step earlier**: R-SMALL-2 was declared to "reuse this
  loop rather than copying it, so its hard-won guards apply unchanged" — and the *tracing* loop was indeed reused.
  The *reading* half lives in the supervisor and was not, and nobody noticed because the tracer's progress counter
  kept going up. **A campaign that produces traces nothing reads looks exactly like a campaign that is working.**
- **Fixed by making the suffix a loop variable** (`RSMALL_SUFFIXES:-_small _rs2`) rather than a literal, with the pid
  file and log name carrying the suffix so two loops cannot collide. A future campaign that adds a suffix gets its
  reader with it instead of silently getting none. Three tests pin it, including that the literal `_small` log name
  is gone. The supervisor was **not running** when it was edited — checked first, per the `rdepth.sh` corruption
  already on record.
- **Both `_rs2` read loops are now running** and the first read is in flight. **No R-SMALL-2 verdict has been reached
  and none is claimed**; the bar stands exactly as declared, and the clock on it starts now.

### G-OWN admissibility gate: PASSED, and decisively (2026-09-19 09:24 UTC, `gates/gown/gown_gate.json`)

- The trace finished at **4.845 cm²** (`PHerc0139_gown/auto_grown_20260919084719395`, 13 924 valid grid nodes,
  60 generations, corpus params unchanged).
- **On-sheet fraction 0.9889 against the declared gate of 0.50.** Distance from each trace point to the w040
  known-text mesh: **median 85 µm**, p90 160 µm, max 915 µm, against one wrap spacing of 449 µm. **13 770 of 13 924
  points sit on the known-text sheet.** Our tracer, seeded on that mesh, stayed on it.
- **The area-matched control is therefore available and is already measured**: over the **4.32 cm²** of the control
  canvas our trace covers (12 308 mesh nodes, 4.92 Mpx), **the team's own maps give forward 0.3556, reverse 0.3140,
  margin +0.0416** — essentially the control's labelled-INKED level (+0.0438), because the seed was placed in the
  most-inked neighbourhood on the sheet. **This is the number our trace has to reproduce**, and the declared verdict
  still stands on the declared bar (+0.0128 against the whole-canvas +0.0255), exactly as declared.
- Verdict **PENDING**: admissible, read in flight. Nothing is claimed until the map pair exists.

### G-GP part 6 RESULT (2026-09-19 09:24 UTC): my pre-registered prediction is REFUTED — the team's own threshold is optimal on both axes

- The prediction recorded before the build was: *"grid fill rises with the threshold and area falls."* Measured over
  the identical 86-source set and seed, sweeping `consensus_default_th` across **4, 6, 8, 10**:

  | `consensus_default_th` | part | grid | valid nodes | **grid fill** | area |
  |---|---|---|---|---|---|
  | 4 | 5b | 120×162 | 8 929 | 0.459 | 3.98 cm² |
  | **6 (the team's default)** | **5** | **174×258** | **22 228** | **0.495** | **9.52 cm²** |
  | 8 | 6 | 114×162 | 8 677 | 0.470 | 3.71 cm² |
  | 10 | 6b | 120×162 | 8 803 | 0.453 | 3.91 cm² |

- **Fill does not rise with the threshold. It peaks at 6 and falls on both sides, and so does area — by a factor of
  2.4.** My prediction was wrong in exactly the direction the declaration said it might be. Thresholds 4 and 10, the
  two extremes, converge to almost the same surface (120×162, ~3.9 cm², fill 0.453–0.459).
- **The team's published `consensus_default_th: 6` is optimal on both axes among the four tested, and the threshold
  knob is now CLOSED.** Part 5b's premise was refuted by measurement and so is part 6's; neither bar is moved. The
  raggedness R-COVER9-corrected identified — fill ≈ 0.48 against the control's 0.862 — **is not a tuning problem, it
  is what this growth method produces**, and it is stable across a 2.5× range of its main parameter.
- Part 6's declared bar (> 5 valid units on the read) is not yet decided: its surfaces go through the geometry gate
  and, if they pass, are read like any other. At 3.7 cm² and fill 0.470 they are smaller than part 5's, so the bar is
  unlikely to be met — but it is decided by the read, not by that expectation.

- **G-OWN's like-for-like context, measured before its read returns (2026-09-19 09:28 UTC).** The 4.32 cm² of control canvas our trace
  covers carries a **labelled-ink fraction of 0.0334 — 2.1× the whole canvas's 0.0161**, and the team's own mesh reads
  **+0.0416** there, essentially their labelled-INKED unit level (+0.0438). Our trace's QC **PASSED** (mean |n_z|
  0.2324 against the ≤ 0.50 bar, area 4.86 cm², 60 generations, corpus params unchanged) and its render is complete.
  **So the question G-OWN asks is now exact: on 4.3 cm² of papyrus carrying twice the average density of KNOWN TEXT,
  where the team's geometry returns +0.0416, what does ours return?** Corpus level is |0.0122|. The declared bars are
  unchanged: PASS ≥ +0.0128, COLLAPSE ≤ +0.0042.
  - Its inference is correctly queued behind the part-5 `auto_trace` read on the production lock. That lock exists
    because two large inferences oversubscribe four cores; it is not overridden for this experiment, and the 42
    minutes already spent on the part-5 read are not discarded to jump the queue.

### G-GP part 5 COMPLETE (2026-09-19 09:29 UTC): both outputs BLANK, 0 flagged of 5 valid units — and they are ONE surface, not two

- `auto_trace_20260919074515229_seed_3590p000_2095p000_4179p000` (9.52 cm²), plain seed42, both depth orders:
  **BLANK. 5.74 cm² on-sheet, 5 valid units, 0 flagged**, on-sheet CT std 35.4, crest ratio 2.774 (slice 15),
  mean unit margin **−0.0113**, best unit **+0.0301**. Map pair verified: **62 of 62 pairs in the project sound.**
- **Its statistics are identical to its 9.48 cm² companion's, to every digit reported** — same on-sheet area, same
  5 valid units, same mean margin −0.0113, same best +0.0301. They are the `auto_grown` and `auto_trace` outputs of
  **one consensus build**: same grid 174×258, same **22 228** valid nodes. **They are one surface written twice, and
  must not be counted as 19 cm² of canvas.** Recorded so that no later tally inflates our coverage by double-counting
  a build's two outputs; the same applies to every `cons_part*` pair on record (parts 4, 5, 5b, 6, 6b all have them).
- **G-GP part 5's verdict, whole:** the area bar was missed at 9.52 of 10 cm² and not moved; the geometry bars were
  met with room (0.00 transverse/cm², p90 sag 4.85 µm against the control's 9.93); and the surface **reads blank at a
  margin magnitude of 0.0113 — R-ORIENT's corpus level, and the control's BLANK level.** The best-conditioned canvas
  this project has ever built returns exactly what every other surface returns.

- **Checked, not asserted: neither R-DEFICIT nor R-SHAPE was inflated by that duplication (2026-09-19 09:30 UTC).** Both were computed
  **before** the part-5 `auto_trace` read landed — R-DEFICIT at 30 surfaces / 113 valid units, R-SHAPE at 31 / 118,
  with exactly one output per consensus build in each. The tally is now 32 / 123 and **the next naive count would have
  double-counted**, so the dedup is now automatic in `cluster_power.py` rather than a note: within a `*_cons_part*`
  directory, two reads with an identical valid-unit layout are one build and are counted once. It collapses nothing
  across parts and nothing among ordinary traces, which four tests pin. **Re-running R-SHAPE with the fix reproduces
  0.079 exactly**, so the published figure stands unchanged.

## R-EYE  What a true positive LOOKS like in this pipeline, established on the control before looking at anything of ours (2026-09-19 09:33 UTC)

- **Why this is recorded.** R-CTRL55 calibrated the *screen*; nothing had calibrated the *eye*. The prize is judged on
  legible letters, not on our margin statistic, and the control says our screen fires on only 7 of 71 known-text
  units — so "look at the renders too" is a reasonable instinct. It is also the shortest road to seeing what one
  wants to see. The order therefore matters: **the control is looked at first, and it sets the standard.**
- **The raw CT render of known text shows NO letters.** `review_sheets/reference/REFERENCE_w040_known_text_4cm2_9.362um.png`
  — 4 cm² of the w040 control at 9.362 µm/px, a sheet whose labels carry ink over 3.3 % of this region — shows
  papyrus fibre weave, horizontal and vertical bundles, surface damage, and **not one legible character**. At 9 µm
  carbonised ink is not visible to the eye in the CT; that is the entire reason the ink model exists.
  **Consequence, and it is a standing rule of reading: any "letterform" seen in a raw CT render of one of our
  surfaces is pareidolia in fibre texture and is never evidence of anything.**
- **The ink model's FORWARD map of known text shows letters that cannot be missed.**
  `review_sheets/reference/CONTROL_w040_rule55_PROMISING_CANDIDATE_cluster.png`, the four-unit PROMISING CANDIDATE
  cluster, stored with no enhancement: a large **Φ** at centre — vertical stroke through a closed bowl — further
  characters along the lower edge and a **Λ**-like form at lower left. Bright, sharp, continuous strokes of uniform
  width standing well clear of a mottled background. **The REVERSE map of the same region shows none of them.**
- **The standard this sets, written down before any of our own maps are viewed:**
  1. A recoverable letter in this pipeline is **unmistakable** — a stroke, not a suggestion. If a mark needs
     argument, contrast adjustment, or a second look to be called a letter, **it is not one**.
  2. It appears in the **forward map and not the reverse**. A mark present in both is texture or geometry, not ink.
  3. It has **stroke morphology**: continuous, roughly uniform width, comparable to its neighbours, sitting on a row.
- **This changes no bar and no verdict.** Rule 5.5 still decides PROMISING CANDIDATE and protocol 9 still decides
  anything beyond it. R-EYE only fixes, in advance and against ground truth, what the eye is allowed to call a letter.

### R-EYE applied to the project's single strongest surface (2026-09-19 09:34 UTC): nothing a reader can call a letter

- Looked at: `PHerc0826|auto_grown_20260917090724211` — **the surface carrying the only flagged unit still standing
  anywhere in the project** (plain read, margin +0.0873, the highest in 189 units on record). The review sheet shown
  is its seed42+TTA read: fwd 0.419, rev 0.372, **1 of 4 valid units flagged, largest 4-connected cluster 1 < 3.**
- **Against the three criteria R-EYE fixed on the control before this was viewed:**
  1. *Unmistakable stroke?* **No.** The forward map is fine-grained mottle throughout — no continuous mark, no
     uniform-width stroke, nothing with the morphology of the control's Φ.
  2. *Forward-only?* **No, and this is the decisive one.** The forward and reverse maps are **visually
     indistinguishable** — the same mottle in the same places. On the control the forward drew letters and the
     reverse of the same region drew none. Here the two panels could be swapped without a reader noticing.
  3. *Stroke morphology?* **No.** Nothing sits on a row; nothing has consistent width.
- **So the eye agrees with the arithmetic, independently.** R-ORIENT put this corpus at |margin| 0.0122 — the
  control's *blank* level — and R-SYM found forward and reverse are genuinely independent answers rather than copies.
  The picture shows exactly that: two independent answers that agree there is nothing there.
- **The "we should also just look at the renders" line is therefore closed, and closed honestly rather than by
  refusing to look.** It was a fair instinct — the screen fires on only 7 of 71 known-text units, so it misses most
  text — but the strongest surface we have shows no letter under a standard fixed against ground truth beforehand.
  **No claim is made, none is withdrawn, and no bar moves.** If a surface ever does show the control's kind of mark,
  it will be obvious, it will be forward-only, and rule 5.5 and protocol 9 will still be what decide it.

- **G-GP part 5b RESULT (2026-09-19 09:34 UTC): VOID.** Both outputs of the threshold-4 build render **not centred on a sheet**
  (1.69 cm² on-sheet each) and are vetoed by R-CREST before the model runs. Part 5b is therefore settled on every
  count: its declared premise — that a lower agreement threshold buys area — was refuted at the build (3.98 cm²
  against threshold 6's 9.52), and its surface does not survive the geometry veto at the read.

- **G-OWN's follow-up is named BEFORE its number is known (2026-09-19 09:51 UTC), so the diagnosis cannot be chosen to fit the
  result.** If G-OWN returns COLLAPSE or PARTIAL, the **first** thing tested will be **flattening**, for a stated
  reason: the control surface we render is the team's *flattened* segment mesh, while every trace of ours is a raw
  tifxyz control grid rendered directly. `vc_tools.sh flatten` (ABF++) already exists and `flat/` already holds 29
  flattened copies, so the test is cheap — flatten the G-OWN trace, render and read it under its own ledger key, and
  compare against the same bars. **My prior, recorded so it can be wrong:** flattening changes the *in-plane*
  parameterisation, not the surface or its normals, so it should NOT move a depth-asymmetry statistic; if it does,
  that is a genuine surprise about the renderer and not a tuning win. Second on the list, if flattening does nothing,
  is node spacing and interpolation between the 20-voxel grid nodes.
  - If G-OWN returns **PASS**, no diagnosis is needed and none will be invented: the corpus negatives are then real,
    the constraint stays R-SHAPE's contiguous canvas, and the honest consequence — that a candidate is a ~1-in-5
    event per 35 cm² of clean known-text canvas while our best surface holds 9 valid units — is a scaling problem,
    not an insight problem, and will be reported as such.

- **R-SMALL-2 interim, recorded because its declared MINIMUM is now met and I do not want the number to appear only
  once it is final (2026-09-19 10:04 UTC).** 23 traces grown, **16 resolved, 1 readable** — `PHerc0826_rs2|auto_grown_20260919083016392`,
  **BLANK, 0 flagged of 4 valid units**. The other 15 are 14 VOID by R-CREST (crest ratios 1.01–1.29; one of them at
  ratio 1.29, which passes, vetoed instead on crest **slice 0**, the render's edge) and 1 QC FAIL.
  - Readable fraction **1/23 = 4.3 % on the all-traces denominator** (the one the bar is judged on) and **1/16 = 6.2 %
    on resolved**, against a **≥ 30 %** bar and the 60-generation baseline of **5.6 %**. On the denominator that
    decides, it is currently **below the baseline it was meant to beat**.
  - **No verdict is called yet.** R-SMALL was judged only when all 19 of its traces had resolved, and R-SMALL-2 gets
    the same treatment: PHerc0358_rs2 is still tracing its declared 20. The bar is not moved, the interim is not a
    result, and the pre-written conclusion for a failure — *interior geometry is not recoverable on this box with the
    published tooling and priors* — is quoted here unchanged from where it was written before any of this ran.

## G-OWN RESULT (2026-09-19 10:13 UTC): **PASS** — our own tracer's geometry finds ink on known text at 142.7 % of the team mesh's signal

`PHerc0139_gown/auto_grown_20260919084719395`, 4.845 cm², 60 generations, corpus params unchanged, plain seed42,
both depth orders, frozen rule 5.5. **PHerc0139 is a CONTROL, not one of the 23 eligible volumes: nothing here is or
can become a submission.**

| | value | bar / reference |
|---|---|---|
| on-sheet fraction vs the w040 known-text mesh | **0.9889** | gate ≥ 0.50 |
| whole-map on-sheet margin | **−0.0594** (`maps`: −0.0609 over 5.38 Mpx) | — |
| **|margin|, the declared statistic** | **0.0594** | **PASS ≥ 0.0128**, COLLAPSE ≤ 0.0042 |
| area-matched: the team's own maps over the same 4.32 cm² | +0.0416 | **our geometry keeps 142.7 % of it** |
| control labelled-INKED units / labelled-BLANK units | +0.0438 / +0.0134 | our |margin| is **4.4×** the blank floor |
| rule 5.5, forward table | 9 units, 9 valid, **0 flagged** → **BLANK** | — |
| rule 5.5, **swapped** table | 9 valid, **2 flagged**, margins **+0.1150** and **+0.1048**, clusters **[1, 1]** | bar +0.08 |

- **Our tracer's geometry is not the problem, and this is the first evidence that could have said otherwise.** On a
  sheet we know carries text, our own auto-grown surface returns a depth asymmetry **larger than the team's own mesh
  gets on the identical papyrus**. Every component of the chain — model, renderer, calibration, frozen rule, and now
  the tracer — has a positive control on known text. **The corpus negatives are therefore real negatives**, and
  R-DEFICIT, R-BLANK and R-ORIENT all stand with a same-geometry positive control behind them.
- **The depth-swap tripwire FIRED, for the first time in this project, and it fired where it should.** The sign is
  **negative**: our trace's sheet orientation is the mirror of the team's mesh, which is rendered with
  `--flip-normals` to reach the trained orientation while ours is not. **R-ORIENT's confound is therefore not
  hypothetical — it is exactly what happens**, demonstrated on known text: a reversed trace reads **BLANK** under the
  signed rule while carrying two units over the bar in the correct orientation.
  - **The obligation the tripwire carries is discharged by measurement, not skipped.** RULES requires the surface's
    orientation be checked and, if genuinely mirrored, re-read under a `+flip` tag. It is genuinely mirrored, and the
    `+flip` read **already exists**: `--direction both` writes the reverse map as *the same stack with the slice order
    flipped*, and `--flip-normals` at render time flips the sampling direction along the normal, which reverses that
    same slice order. **The swapped table IS the flipped read**, exactly, so re-rendering would spend ~45 minutes
    reproducing numbers already on record. That equivalence is stated so it can be checked and contradicted.
  - **And R-ORIENT's corpus check now carries much more weight than when it was made.** It found the tripwire had
    never fired across 52 corpus reads and nothing reached the bar backwards (extremes −0.0714, +0.0873). That was
    the right check for a mechanism now proven real — **no corpus candidate is hidden behind a flipped trace.**
- **R-SHAPE is demonstrated directly, on inked canvas, with our own geometry — and this is the sharpest thing in the
  result.** Two of nine valid units flag: a **22 % unit flag rate, more than twice the control's 9.86 %.** And still
  **no candidate**, because the two flagged units sit at (1,1) and (2,2) — **diagonal, 8-connected, not 4-connected**
  — so the largest cluster is 1 < 3. *Enough signal, too few units.* The frozen rule behaves correctly; the canvas is
  simply too small to hold an adjacent triple. This is exactly what R-SHAPE computed from layouts alone, now observed.
- **What this closes and what it leaves.** Closed: the geometry hypothesis, the orientation hypothesis, the domain-gap
  hypothesis, and any remaining doubt that our chain can recover ink. Left: **contiguous valid units on canvas that
  carries ink** — the one constraint every measurement today converges on. No bar, threshold or verdict changes.

### G-GP part 6 FINAL (2026-09-19 10:15 UTC): the bar is MISSED, and the threshold sweep closes on a third axis nobody was watching

- **Part 6's declared bar was "> 5 valid units on the read". It is missed: both threshold-8 surfaces and both
  threshold-10 surfaces read VOID, vetoed by R-CREST before the model ran, so they produce no valid units at all.**
  The bar is not moved and the premise is recorded as refuted, exactly as part 5b's was.
- **But the failure mode is the informative part, and it is not low contrast.** The full sweep, one source set, one
  seed, only `consensus_default_th` changing:

  | `th` | part | verdict | on-sheet | crest **ratio** | crest **slice** (of 28) | grid fill | area |
  |---|---|---|---|---|---|---|---|
  | 4 | 5b | VOID | 1.69 cm² | **4.434** | **27** | 0.459 | 3.98 cm² |
  | **6** | **5** | **BLANK (read)** | **5.74 cm²** | **2.774** | **15** | **0.495** | **9.52 cm²** |
  | 8 | 6 | VOID | 1.62 cm² | **4.388** | **27** | 0.470 | 3.71 cm² |
  | 10 | 6b | VOID | 1.67 cm² | **4.492** | **27** | 0.453 | 3.91 cm² |

- **Every off-default threshold produces a surface with a STRONGER crest than the default — ratio 4.39–4.49 against
  6's 2.774, three to four times the 1.20 bar — sitting at slice 27 of 28, the render's far edge.** These are not
  weak or ambiguous surfaces. They are surfaces that have found a real sheet and are **offset from its mid-plane by
  roughly half the 28-slice window — about 122 µm, a quarter of the 449 µm wrap spacing.** The veto is doing exactly
  its job: the reading window is not on the sheet, so the ink window would be meaningless.
- **So the team's `consensus_default_th: 6` is optimal on three independent axes, not two**: area (9.52 cm² against
  3.7–4.0), grid fill (0.495, the peak), and **whether the consensus lands on the sheet's mid-plane at all** (slice
  15 of 28 against slice 27 for every other value tested). The third was not something I was looking for and is the
  strongest of the three. **The threshold knob is closed, and closed harder than this morning's entry said.**
- G-GP part 6 is complete. No bar, threshold or verdict changes.

## R-YIELD  The consensus programme bought area and LOST the thing a candidate is made of (2026-09-19 10:21 UTC; a measurement, and an assessment of my own day's work)

- Valid 0.5 cm² units per surface, by how the surface was made, over the 34 plain screening reads:

  | surface kind | n | median **valid units** | median unit validity | median grid units | **best in class** |
  |---|---|---|---|---|---|
  | **consensus** (G-GP parts 4–6) | 3 | **5.0** | **44 %** | **18.0** | **5** |
  | single trace | 23 | 4.0 | 60 % | 9.0 | **9** |
  | team mesh | 8 | 6.0 | 57 % | 14.0 | **9** |
  | *G-OWN, single trace on KNOWN TEXT* | 1 | **9** | **95 %** | 9 | 9 |

- **The consensus surfaces carry the MOST grid units and the FEWEST valid ones.** Eighteen units per surface, five of
  them usable. They are the worst of the three kinds on the only quantity that can produce a candidate, and they are
  what four of the day's six G-GP parts were built to make. **G-GP was aimed at area, and R-SHAPE showed area is not
  the constraint; this entry states plainly that the programme optimised the wrong quantity.** Its geometry results
  stand (0.00 crossings/cm², sag 4.85 µm, the threshold sweep) and are worth having — the *canvas* it bought was not.
- **The ceiling is now measured, not guessed. Nine valid units is the best any surface in this project has ever
  produced** — a single trace, a team mesh and G-OWN's known-text trace all reach exactly 9, and nothing reaches 10.
  At the control's own flag rate a 9-unit surface yields a candidate with probability **0.017**. That is the ceiling
  per surface, and 31 surfaces of it is R-SHAPE's 0.079.
- **G-OWN's 95 % validity against the corpus single-trace median of 60 % is itself informative**: the difference is
  not method, it is the sheet. An intact control sheet renders a full clean 3×3; a damaged outer wrap renders holes.
- **What would actually change the arithmetic, stated so it can be judged rather than pursued blindly:**
  1. **A surface with ~50 valid units on an eligible volume.** The w040 control has 71 and yields ~0.18. Nothing
     available to us on any eligible volume comes close — the best published team mesh on one gives 9, and one
     PHerc1447 mesh has 144 grid units with **7** valid (5 % validity).
  2. **Canvas that carries ink**, i.e. inner wraps — blocked by R-SMALL (failed) and R-SMALL-2 (running, 1 readable
     of 26).
  3. **Higher resolution**, the 2.4 µm rescans, which is the only untried lever and is what the remaining assessment
     looks at.
- No bar, threshold or verdict changes.

### R-CREST-POWER phase 1 RESUMED (2026-09-19 10:23 UTC): its pause condition has lifted, and G-OWN makes it much sharper

- The marker said, verbatim: *"paused 2026-09-18 21:55 UTC so the candidate path has the box; resume by deleting this
  file."* **That path is finished** — G-GP part 5 read out, part 6 closed, G-OWN complete — and the box is idle
  (load 1.67, zero inferences). The pause was a resource decision and the resource is back, so the queue is resumed
  with nothing about its declaration, population or decision rule touched. **0 of 12 members had ever completed**;
  two earlier attempts were killed for the box, which is why this experiment has no data at all.
- **G-OWN changes what a positive here would mean.** Before it, a flagged unit on a crest-vetoed surface could have
  been our geometry misbehaving. Now every component including our tracer has a positive control on known text, so
  **a flagged unit on a VOID surface would be real ink on canvas the veto is discarding** — and the populations at
  stake are large: PHerc1203 **21 of 22** surfaces VOID, PHerc1447 **28 of 32**, most of them the team's own curated
  and published reading surfaces.
- **And R-YIELD names why that matters more than it did this morning.** The ceiling on anything we build is 9 valid
  units. The team's curated surfaces are far larger — one PHerc1447 mesh carries **144** grid units — so if the veto
  is wrong on low-contrast volumes, what it unlocks is not another 5 cm² trace but the only canvas in this project
  that could ever hold an adjacent triple with room to spare.
- Nothing is pre-judged: the decision rule fixed on 2026-09-18 stands unchanged, including that a PROMISING CANDIDATE
  starts protocol 9 immediately and that no rule 5.5 threshold moves either way.

## R-2UM-SCOPE  What the 2.4 µm lever actually consists of, measured against the eligible list (2026-09-19 10:26 UTC; an assessment, not a declaration — nothing is started here)

- **Queried all 23 eligible volumes' `volumes/` prefixes on S3. Exactly TWO have a high-resolution rescan:**
  **PHerc0846A** (`20260319102732-2.403um-0.2m-77keV`) and **PHerc1203** (`20260319130212-2.403um-0.2m-77keV`).
  The other 21 have only the 9.362 µm or 8.640 µm survey scan. **So "go to higher resolution" is not a strategy for
  the corpus; it is a strategy for two scrolls.**
- **PHerc0846A is the one already tried and it is the one already blocked.** CONTROL-2UM traced it, the traces were
  not sheet-following, and its best 1 cm² window scored **28.6 %** papyrus coverage against R-COVER's declared 0.80
  bar — **VOID-COVER**, recorded 2026-09-17, no 2.4 µm inference ever run on it.
- **PHerc1203 is untried, and it is the better target of the two for three independent reasons.**
  1. Its rescan publishes the **full apparatus our pipeline needs**:
     `20260319130212-surface-20260413222639-surface-m7-L2-th0.2.zarr` **plus its normal-grids** — the same
     `20260413222639-surface-m7` model we trace every other scroll with, at level 2 of the 2.4 µm volume.
  2. **The tooling already anticipates exactly this route** and was written for it before today: `vc_tools.sh` takes
     `SURF_SUFFIX` and documents `VC_CACHE_SUFFIX=_L2` as "keeps the VC volume cache of another prediction/volume of
     the same scroll apart", and `patch_qc.py --coord-scale` documents "4 for L2-traced 2.4 µm meshes".
  3. **It is the volume where R-CREST vetoes 21 of 22 team surfaces at 9 µm** — the compressed-wrap, no-air-gap case
     where density contrast is absent. That is precisely the failure higher resolution would address, and PHerc1203
     is the only eligible volume that is both that case and rescanned.
- **Sequencing, and the reason for it.** The box is committed to **R-CREST-POWER phase 1**, which asks a cheaper
  question about the same volume — whether the ink model finds anything on those 21 vetoed surfaces *at 9 µm*, using
  geometry that already exists. If it finds something, no rescan is needed. If it finds nothing, the 2.4 µm route on
  PHerc1203 is the remaining lever and would be **declared with its own bars before any of it is run**, R-COVER's
  0.80 papyrus-coverage bar included, exactly as PHerc0846A's was.
- Nothing here changes a bar, a verdict, or what is running.

### A STALE-PAIR check added, found WRONG by its own first run, and replaced with a relative one (2026-09-19 10:34 UTC)

- **Why it was added.** Resuming R-CREST-POWER put a fresh read into a directory that still held a forward map from
  the previous day's **killed** attempt. The existing guards cover the dangerous version of that (a *partial*
  leftover fails PAIR or COVERAGE and `read_chart.py` refuses it), but nothing named the situation.
- **The first version was wrong, and it is the SAME mistake `map_integrity.py`'s own docstring already warns about**
  — an absolute bar where the quantity is relative. It flagged a pair whose two maps were written more than an hour
  apart, on the assumption that `--direction both` writes them together. **It does not: it runs forward, then
  reverse.** The bar flagged **4 sound pairs** on its first run.
- **The explanation was tested against recorded data rather than asserted**, which is the only reason it is in this
  entry as a fact:

  | read | recorded `s_infer` | measured skew | ratio |
  |---|---|---|---|
  | `PHerc0358|auto_grown_20260918104037671` TTA | 9 222 s | 4 620 s | **0.50** |
  | `PHerc0826|auto_grown_20260917182826749` TTA | 7 985 s | 3 705 s | **0.46** |
  | `PHerc1203|team_20250923163331524` TTA | 8 141 s | 4 209 s | **0.52** |
  | `PHerc1447|team_…z_dbg_gen_00320` plain | 13 108 s | 6 806 s | **0.52** |

  **Exactly half, in every case** — which is what sequential forward-then-reverse writing means. All four sound.
- **Replaced with a relative test, calibrated by construction rather than fitted to those four numbers:** the skew
  may not exceed **that read's own total inference time** (`throughput.jsonl`, `s_infer`, matched by ledger key),
  since two maps produced by one call cannot be further apart than the call took. Slack 600 s. **A read with no
  throughput record is SKIPPED, not guessed.** Five tests pin it, including the four false positives as regressions
  and one asserting the withdrawn constant is gone.
- **Live audit after the fix: 64 pairs, 64 sound, 0 SUSPECT.** It remains an audit flag and never a refusal —
  `read_chart.py` is untouched, because a *complete* leftover is genuinely equivalent to a fresh map and refusing it
  would discard sound work. A test asserts `read_chart.py` contains no mtime logic.

### A DEFECT I CAUSED resuming R-CREST-POWER: two queues writing one read directory (2026-09-19 10:38 UTC, caught and fixed within 15 minutes)

- **What I did.** Resuming the experiment, I deleted **both** pause markers — `rcrest_power_paused` and
  `rcrest_power_1203_paused` — without checking what the second one gated. It gates `rcrest_power_1203.sh`, the
  supervisor's **PHerc1203-only subset** queue, whose three members are **already inside** the full 12-member phase-1
  list that `rcrest_power.sh` runs. The next supervisor check-in duly started it.
- **What that produced.** Two `run_patch_dir.py --only team_20251005230830031` processes in flight at once, both
  writing `read_ink9um_seed42_plain_nocrest/`. **Two writers, one output directory — the R-DEPTH shape**, and the
  artefact that cost this project a reversed verdict came from trusting a map that a killed writer had left behind.
- **What I did about it, in order:** restored the 1203 marker with the reason written in it; stopped both queues and
  both readers and both inferences **by explicit pid** (never `pkill -f`, which has matched my own shell three times
  in this session's history); **deleted the contested read directory outright** rather than trusting a directory two
  processes had been writing; restarted the single declared queue. The directory held only yesterday's stale forward
  map, so **nothing from today was lost** — that was checked, not assumed.
- **The durable fix is the invariant, not the marker.** A marker can be cleared, which is exactly how this happened.
  The supervisor's subset queue now stands down whenever the full queue's pid is alive, marker or no marker, and two
  tests pin it — including that the guard precedes the launch. **One queue per population is the rule; the marker is
  only a convenience.**
- Nothing measured is affected: no read completed under the race, no verdict, ledger line or gate result exists from
  it, and the post-fix audit is **64 pairs, 64 sound, 0 SUSPECT**.

## R-SMALL-2 RESULT (2026-09-19 10:40 UTC): **FAILED**, and the failure is arithmetically decided, not called early

- **Tally: 30 traces, 29 resolved, 1 readable.** 24 VOID by R-CREST (crest ratios 1.01–1.29), 3 QC FAIL,
  1 QC UNREADABLE, **1 BLANK** (`PHerc0826_rs2|auto_grown_20260919083016392`, 0 flagged of 4 valid units).
  **3.3 % on the all-traces denominator the bar is judged on**, 3.4 % on resolved, against a **≥ 30 %** bar and the
  60-generation baseline of **5.6 %**. It is below the baseline it was declared to beat.
- **Why this is decided now rather than at population completion.** PHerc0826_rs2 has reached its declared cap of 20;
  PHerc0358_rs2 stands at 10 of 20; the declared maximum population is **40**. One trace is readable and **10 can
  still be grown**, so the best attainable final figure — *every remaining trace readable* — is **11/40 = 27.5 %**
  against a bar of **12/40 = 30 %**. **The bar cannot be reached even in the best case, by one trace.** That is an
  arithmetic fact about the declared population and cap, not a judgement about the trend, and it is the only reason
  the verdict is recorded before the last ten traces finish. They are left running and the final tally will be
  appended; it can only move the percentage down.
- **The pre-written conclusion therefore stands, quoted unchanged from where it was written on 2026-09-19 03:30 UTC,
  before a single one of these seeds was traced:** *interior geometry is not recoverable on this box with the
  published tooling and priors.*
- **What failed, precisely, and what did not.** The hypothesis was that the density gate — calibrated at 60
  generations — was the wrong gate for a 40-generation patch, so seeds it rejected at density 0.20–0.30 would trace
  acceptably at the smaller budget. They do not: **24 of 30 die at the geometry stage before the ink model is ever
  invoked**, on flat renders with no crest. The reader is not the problem and was never reached. **This is the third
  independent line to land on the same wall** — R-SMALL (15.8 %), R-RADIAL (89 % of inner-half reads VOID), and now
  R-SMALL-2 (3.3 %).
- **No bar is moved, no threshold changes, and no successor experiment is declared off the back of this.** R-SMALL
  was allowed one pre-written successor because that successor was written before R-SMALL's numbers existed. There
  is no such pre-written successor here, and inventing one now would be the "declare variants until one passes"
  failure this file has refused five times already.

- **A sweep for killed reads' leftovers, made structural (2026-09-19 11:02 UTC, `scripts/sweep_partial_reads.py`).** The R-CREST-POWER
  leftover was not unique: sweeping the whole tree found **three** read directories holding a forward map with **no
  reverse, no `read_stats.json` and no `.read_complete`** — `PHerc0826_cons_part4/…/read_…_tta` (10.6 h old),
  `PHerc1447/team_20250703025628283/read_…_tta` (13.7 h), and `PHerc1447/team_z_dbg_gen_00701/read_…_nocrest`
  (19.2 h, **a member this very queue was about to reach**). None had ever been scored, so **no verdict, ledger line
  or gate result is affected** — but each was a stale forward waiting for a fresh reverse.
  - **The predicate is conservative by construction, because deleting a live read is far worse than leaving a dead
    one:** no `.read_complete`, at least one `.tif`, and **untouched for 6 h** — against a longest-observed
    single-direction write of **1.9 h**, measured from the same skew data that corrected the STALE check an hour ago.
    `--dry-run` is the default and deleting needs `--go`. Six tests pin it, including that a 1.9 h-old live read and
    a finished read of any age are both left alone.
  - Wired into every supervisor check-in, **after** the ledger audit and as a standalone statement — the first
    attempt inserted it inside the map-integrity `case` block and broke `bash -n`, caught immediately and reverted.
  - **The one-queue guard also fired correctly on its first real check-in:** *"rcrest_power.sh (full phase-1 queue) is
    running; the PHerc1203 subset queue stands down."*

- **R-SMALL-2's READ loops paused so R-CREST-POWER has the box; its TRACING is deliberately left running (2026-09-19 11:04 UTC).**
  Three inferences were sharing four cores at load 11. R-SMALL-2's bar is already decided and **its remaining reads
  cannot change the verdict** — that was recorded before this decision, not after it. R-CREST-POWER phase 1 is the
  only live experiment that can unlock canvas and its members are the team's large curated surfaces, so it is worth
  more per core-hour than a 2 cm² interior read with four units.
  - **The reads are paused, not cancelled, and tracing continues**, so the declared 40-trace population still
    completes and the final tally will be appended as promised. The markers state the reason and how to resume.
  - **Stated against myself:** an rs2 read could in principle return a flagged unit regardless of the bar, and
    pausing them forgoes that. The trade is taken with the numbers in view — 24 of 30 of those traces never reach the
    reader at all, and R-SHAPE prices a 4-unit surface's chance of a candidate at essentially nil — not because the
    experiment is over.

### R-SMALL-2 population COMPLETE (2026-09-19 11:30 UTC): 40 traces, and the verdict is unchanged at both bounds

- **The declared population is finished**: PHerc0826_rs2 **20**, PHerc0358_rs2 **20**, both loops exited at their cap.
  **40 traces, 30 resolved, 1 readable** — 25 VOID by R-CREST, 3 QC FAIL, 1 QC UNREADABLE, 1 BLANK.
- **Ten traces are UNRESOLVED, and the reason is my own resource decision, not the experiment.** I paused the rs2
  read loops at 11:05 UTC to give R-CREST-POWER the box, having already recorded that R-SMALL-2's bar was decided.
  So the final figure must be quoted as a range, not as a point:
  - if none of the ten is readable: **1/40 = 2.5 %**
  - if **all** ten are readable: **11/40 = 27.5 %**
  - **both bounds are below the 30 % bar**, which is the same arithmetic that decided the verdict an hour ago, now
    with the population actually complete rather than projected.
- **The verdict recorded at 10:47 UTC stands unchanged: R-SMALL-2 FAILED**, and its pre-written conclusion with it —
  *interior geometry is not recoverable on this box with the published tooling and priors.*
- **2.5 % is the lower bound and must not be quoted as the result**; the honest single number for the resolved
  population is **1/30 = 3.3 %**, still below the 60-generation baseline of 5.6 %. The ten unread traces remain on
  disk and can be read whenever the box is free; doing so can only move the figure between the two bounds above.

## R-CREST-POWER phase 1, member 1 of 12 (2026-09-19 11:51 UTC): 0 flagged of **28 valid units** — and it breaks R-YIELD's ceiling

- `PHerc1203|team_20251005230830031`, read with the crest veto off (`+plain+nocrest`, its own ledger key):
  **14.58 cm² on-sheet, 36 grid units, 28 VALID, 0 flagged — forward AND swapped, tripwire False.**
  Whole-map forward 0.3499, reverse 0.3463, **margin +0.0036**; `frac > 0.75` **0.00117**; largest region above 0.5
  only **3.13 mm²**. Per-unit margins: median **+0.0022**, range **−0.0304 to +0.0323**, none within a factor of two
  of the +0.08 bar. On-sheet CT std 34.55. Crest ratio 1.036 at slice 27 — the flat, edge-peaked profile the veto
  was rejecting.
- **Against the decision rule fixed on 2026-09-18, before any of these reads:** no flagged unit, and the margin
  distribution sits inside the BLANK population already on record. **Member 1 supports the branch in which R-CREST
  discards nothing this reader could read.** Eleven members remain and the rule is judged on all of them; nothing is
  concluded from one.
- **R-YIELD's ceiling is superseded, and by a large margin.** Two hours ago I recorded that *"nine valid units is the
  best any surface in this project has ever produced … and nothing reaches 10."* **This surface yields 28, at 96 %
  unit validity** — three times the old best, and 40 % of the w040 control's 71. It reaches that only because the
  veto was lifted; at 9 µm with the veto on it was one of the 21 of 22 PHerc1203 surfaces discarded before the model
  ever ran. **R-YIELD's lever #1 — "a surface with ~50 valid units on an eligible volume" — is no longer unavailable;
  it is a third of the way to hand, on the first member read.** At the control's own flag rate a 28-unit surface
  carries P(candidate) ≈ 0.07, against 0.017 for a 9-unit one.
- **A reporting detail, so the ledger line is not misread:** the recorded `verdict` is still **VOID**, because
  `read_chart.py` reports the crest statistic in that field regardless of `--ignore-crest`. The inference **did** run
  and rule 5.5 **was** evaluated — that is the whole experiment. R-CREST-POWER is judged on flagged units, not on
  that label, so nothing here is affected; but a reader scanning the ledger would otherwise see "VOID" and assume no
  model output exists.
- Also landed: `PHerc0358|auto_grown_20260919103859907` — **NOT ESTABLISHED, 0 flagged of 2 valid units**, the
  **second** readable R-SMALL-2 trace. The final tally will be recomputed when the remaining eight resolve.

### R-SMALL-2 FINAL (2026-09-19 12:01 UTC): 2 readable of 40, **5.0 %**, every trace resolved

- **40 traces, 40 resolved, 0 unresolved. 2 readable. 5.0 % on both denominators** (they coincide now that nothing is
  unread), against a **≥ 30 %** bar and the 60-generation baseline of **5.6 %**.
  - 33 VOID by R-CREST, 4 QC FAIL, 1 QC UNREADABLE, 1 BLANK, 1 NOT ESTABLISHED.
  - The two readable members, both with **0 flagged units**:
    `PHerc0826_rs2|auto_grown_20260919083016392` BLANK (4 valid) and
    `PHerc0358_rs2|auto_grown_20260919103859907` NOT ESTABLISHED (2 valid).
- **This supersedes the range recorded at 11:30 UTC (2.5 %–27.5 %) with the measured value, and the earlier 2.5 %
  lower bound is NOT the result** — it was a lower bound taken while ten traces were unread because I had paused the
  read loops. Resuming them on spare capacity closed the gap, which is why the figure is now a single number.
- **The verdict recorded at 10:47 UTC is unchanged and is now final: R-SMALL-2 FAILED**, at **5.0 % against a 30 %
  bar**, and — the sharpest way to put it — **it did not even beat the 5.6 % baseline it was designed to improve on.**
  Raising the density cap from 0.20 to 0.30 admitted 104 seeds the old gate rejected, and they trace no better.
- **The pre-written conclusion stands, unchanged from 2026-09-19 03:30 UTC, before any of these seeds was traced:**
  *interior geometry is not recoverable on this box with the published tooling and priors.*
- **Every declared experiment on interior geometry is now closed**: R-INTERIOR, R-PHASE, R-WRAP, R-SMALL and
  R-SMALL-2, plus R-RADIAL's measurement that 89 % of inner-half reads are VOID. **No successor is declared.**

## R-CREST-POWER: the PHerc1203 half is COMPLETE (2026-09-19 12:32 UTC) — the first CONTROL-SCALE canvas on an eligible volume, and it is blank

- All **3 of 3** PHerc1203 members read with the veto off. RULES called this "the informative half"; here it is:

  | surface | on-sheet | valid | flagged | swapped | whole-map margin | median unit | max unit | `f>0.75` | tripwire |
  |---|---|---|---|---|---|---|---|---|---|
  | `team_20251005221856743` | 10.61 cm² | 18 | 0 | 0 | +0.0059 | +0.0057 | +0.0597 | 0.00273 | False |
  | `team_20251005230830031` | 14.58 cm² | 28 | 0 | 0 | +0.0036 | +0.0022 | +0.0323 | 0.00117 | False |
  | `team_20251005231446965` | 11.35 cm² | 18 | 0 | 0 | −0.0002 | −0.0013 | +0.0174 | 0.00093 | False |
  | **total** | **36.54 cm²** | **64** | **0** | **0** | — | **+0.0022** | **+0.0597** | — | never fired |

- **This is the milestone R-YIELD said we needed and could not reach.** 64 valid units over 36.54 cm² stands directly
  against the **w040 known-text control's 71 valid units over 40.60 cm²** — the same scale, on an ELIGIBLE volume,
  for the first time in this project. It exists only because the crest veto was lifted; at 9 µm with the veto on,
  all three were among the 21 of 22 PHerc1203 surfaces discarded before the model ever ran.
- **And it is blank, decisively.** The control gives **7 flagged of 71**; this canvas gives **0 of 64** where the
  control's rate predicts **6.31**. Binomial **P(X = 0) = 0.0013**; **Fisher exact one-sided p = 0.0096**. Across all
  64 units the margins run **−0.0305 to +0.0597** with a median of **+0.0022** — below even the control's
  *labelled-blank* level of +0.0134 — and **not one unit reaches the +0.08 bar in either depth order.** The single
  highest, +0.0597, is three quarters of the bar and stands alone on an 18-unit surface.
- **Against the decision rule fixed on 2026-09-18, this half lands squarely on the first branch**: no flagged unit,
  and the margin distribution inside the BLANK population on record. Nine PHerc1447 members remain and the rule is
  judged on the whole phase-1 population, so **no verdict is called yet** — but the half chosen in advance as the
  informative one has now spoken, and it says **R-CREST is discarding nothing this reader could read on PHerc1203.**
- **What that costs and what it buys.** It closes the hope that the veto was hiding recoverable canvas on this
  volume — the single largest remaining hope after R-SMALL-2 failed. It also removes the last confound between us and
  a plain statement: **on 36.54 cm² of the team's own curated PHerc1203 surfaces, read at control scale with every
  gate open, there is no ink this detector can find.**

- **R-CREST-POWER interim, 4 of 12 (2026-09-19 13:32 UTC): the veto-off canvas has now PASSED the control's size, and is still empty.**
  Member 4, `PHerc1447|team_z_dbg_gen_00701`, 23.59 cm² on-sheet: **85 grid units, 19 valid, 0 flagged**, whole-map
  margin **−0.0149**, median unit −0.0138. Its 22 % unit validity is the PHerc1447 flattened-mesh raggedness
  R-COVER9-corrected already identified, on the largest surface in the population.
  - **Phase 1 so far: 60.13 cm² on-sheet, 83 valid units, 0 flagged, tripwire never fired.** 83 units is **more than
    the w040 known-text control's 71**, so the project has now read more control-scale canvas with every gate open
    than the control itself contains — and found nothing. Expected flagged at the control's rate **8.18**; binomial
    **P(0) = 0.0002**; Fisher exact one-sided **p = 0.0023**.
  - All 83 unit margins: median **+0.0007**, range **−0.0485 to +0.0597**, none at the +0.08 bar in either order.
  - Eight members remain and **the decision rule is judged on the full population, not here.**

- **CORRECTION to the line immediately above (2026-09-19 13:32 UTC): the Fisher value is p = 0.00375, not 0.0023.** I wrote the number
  into the entry in the same command that computed it, so the text was composed before the result existed — the
  binomial P(0) = 0.000181 rounded correctly to 0.0002, but the Fisher figure was a guess and it was wrong by a
  factor of 1.6. **The corrected pair for 0 flagged of 83 against the control's 7 of 71 is: expected 8.18, binomial
  P(0) = 1.81 × 10⁻⁴, Fisher exact one-sided p = 0.00375.** The conclusion is unchanged and was never close to the
  0.05 line, but a number in this file must be one that was computed, not one that was anticipated.
  - **Practice, since this is the third time today a message or number was composed before its input was read**
    (two commit subjects, now one statistic): a figure goes into RULES only after its computation has printed. The
    two earlier cases were commit-message labels and cost nothing; this one was a p-value in the scientific record.

- **Session container restarted (2026-09-19 13:38 UTC) — the workloads SURVIVED, and the distinction matters.** The harness reported
  "the container was restarted" and killed this session's background watchers. **The machine did not reboot**: system
  uptime read **12:57**, continuous. What actually broke was narrower and more interesting — several long-lived loops
  came back holding a **stale `HTTPS_PROXY`**, and the supervisor detected exactly that and restarted only those
  (`rcrest_power`, and the PHerc1447 and PHerc0800 surface-volume fetch loops). That `stale_proxy` check was written
  for this case and is the reason recovery was a no-op rather than a morning's work.
  - **My first reading was wrong and is corrected here**: I said "every job is gone". They were not. Losing the
    session's watchers is not the same event as losing the work, and conflating them would have had me restarting
    queues that were already running — the duplicate-queue defect from 10:38 UTC, repeated.
  - **Cost of the restart: one member's render.** `PHerc1447|team_z_dbg_gen_00357` was mid-render; its read directory
    held **0 tif files**, so there was nothing partial to pair with anything and nothing to clean. It restarted from
    scratch at 13:37. The four completed members are intact with both maps and their completion markers, and the
    audit reads **69 pairs, 69 sound**.
  - Verified single queue afterwards (pid 13503, started 13:37:08). The second pid my check reported was **my own
    `grep` subshell matching its own command line** — the self-match hazard already on record for `pkill -f`, which
    bites any `ps`/`/proc` scan written the same careless way. Confirmed with `ps -eo pid,ppid,lstart,args`.

- **R-CREST-POWER interim, 5 of 12 (2026-09-19 14:14 UTC).** Member 5, `PHerc1447|team_z_dbg_gen_00357`, 17.01 cm² on-sheet,
  **0 flagged of 14 valid units**. This one was re-run from scratch after the session-container restart killed its
  render; its read directory had held zero tifs, so nothing from the interrupted attempt entered it.
  - **Phase 1 so far: 77.13 cm² on-sheet, 97 valid units, 0 flagged, tripwire never fired.** 97 units is **37 % more
    than the w040 known-text control's 71**. Expected flagged at the control's rate **9.56**; binomial
    **P(0) = 4.24 × 10⁻⁵**; Fisher exact one-sided **p = 0.00201**. All 97 margins: median **−0.0015**, range
    **−0.0485 to +0.0597**, none at the +0.08 bar in either depth order.
  - Every figure above was printed by its computation before this entry was written, per the correction at 13:31 UTC.
  - Seven members remain; the decision rule is judged on the full population, not here.

- **R-CREST-POWER at the HALFWAY mark, 6 of 12 (2026-09-19 14:49 UTC).** Member 6, `PHerc1447|team_z_dbg_gen_00329`, 15.49 cm²,
  **0 flagged of 17 valid units**. Running total: **92.62 cm² on-sheet, 114 valid units, 0 flagged** forward or
  swapped, tripwire never fired. Expected at the control's 7/71 rate **11.24**; binomial **P(0) = 7.26 × 10⁻⁶**;
  Fisher exact one-sided **p = 0.00101**. All 114 margins: median **−0.0022**, range **−0.0485 to +0.0597**.
  Figures printed by their computation before this entry was written.
- **No further per-member interim will be recorded.** Six members is enough to establish the shape and the remaining
  six are judged together at completion; logging each one separately would pad the record without adding evidence.
  The next R-CREST-POWER entry is the phase-1 verdict against the decision rule fixed on 2026-09-18.

## R-REPRO  Fresh-container reproduction of the known-text control from public data (declared 2026-10-15 05:30 UTC, BEFORE any output exists)

- **Why.** The release rests on two September results on the w040 known-text control: Gate A (forward AUC 0.99659,
  reverse 0.49633 on 1,629,734 supervised px) and R-CTRL55 (71 valid units, 7 flagged, clusters [4, 2, 1], origin
  (94, 188)). The September data root no longer exists. This re-creates both in a NEW container, from nothing but the
  public bucket, the public model and the code in this repository. It is the same test a judge would run.
- **Inputs, verified before the run.** w040 native stack level 0 + mesh fetched anonymously from
  `s3://vesuvius-challenge-open-data/PHerc0139/segments/20250831000000-w040_2025083102/` (2776 files, manifest digest
  `cf8b283adee7af62bba3a8e11d19c0682dce2723a0a153134ae5a1d210258d84`); mesh x/y/z.tif sha256 identical to the
  September package record; slice 14 of the stack, crop [1500:3636, 2000:4136], has pixel sha256 `7d62c816...`,
  identical to the September `ct_window.png`. Checkpoint `hybrid_3d2d-seed42/step-075000.pth` sha256 `e635558a...`,
  equal to the Hugging Face LFS record (repo revision 7109667e). Labels from `hf://buckets/scrollprize/datasets/ink_9um`
  (8496 files, manifest digest `dfb49aa7...`), 1,629,734 supervised px on slice 14, the September count.
- **Software.** villa `5ab585ffee54331a3362b9ce6b2929b20dcde2c6` (the September commit) installed editable; Python 3.14.6;
  torch 2.14.0+cpu, torchvision 0.29.0+cpu (the September torch version). Call:
  `python -m vesuvius.ink_detection.inference.infer <stack> <ckpt> <out.tif> --direction both --batch-size 4 --no-compile --num-workers 3`.
  Started 2026-10-15 05:01:22 UTC; 11,076 patches per direction, the September count.
- **Bars, fixed now.**
  - **REPRO-GATE-A:** forward AUC within **0.01** of 0.99659 AND reverse AUC < 0.70 (the Gate A rule itself).
  - **REPRO-CTRL55:** the frozen rule on the fresh maps gives **exactly** 71 valid, 7 flagged, clusters [4, 2, 1] at
    origin (94, 188), from BOTH code paths (`rctrl55.py` and `read_chart.py --maps-only`).
  - **Reported, not a bar:** whether the window [1500:3636, 2000:4136] of each map is bit-identical to the September
    pixel sha256 (`4eced8f4...` forward, `2522e682...` reverse). CPU float summation order can differ between runs, so
    a difference is not a failure; if they differ, the max |difference| is reported, and the two bars above decide.
  - If either bar fails, every release claim that rests on the September control numbers is marked NOT REPRODUCED
    and the release says so on its first page.

## R-HELDOUT  Does the reader fire on known text the model has NEVER seen? (declared 2026-10-15 05:40 UTC, BEFORE any of its data is downloaded or looked at)

- **Why this test exists: a premise of R-CTRL55 is false, and it was found while writing the release.** R-CTRL55 (and
  STATE.md, and G-OWN's reading) call w040 "a sheet the model did not memorise". It is not. villa's training config
  for this checkpoint, `vesuvius/src/vesuvius/ink_detection/configs/aligned21_hybrid_3d2d.json` at `5ab585f`, lists
  `w040` among its five native-9.362 µm training segments (`native9-scrollprizeorg-21slices`: w035, w039, w040, w041,
  w044) and `pherc0139-w040` among its aligned ones; the model card (huggingface.co/scrollprize/ink_9um, read
  2026-10-15) says "plus 5 native 9.362 µm segments from PHerc. 0139"; and no `w040_validation_mask.zarr` exists in
  the label bucket, so nothing of w040 was held out. **Gate A's AUC on w040 and R-CTRL55's 7/71 are therefore
  measurements on a TRAINING-SET sheet: a best case for the detector, not a held-out validation.** MASTER_PROMPT_v4
  5.4 already said "w028 and w040 are in its training corpus"; RULES applied that caveat to w028 (Gate C) and not to
  w040. Every claim resting on "unmemorised" is corrected in docs/SUPERSEDED_CLAIMS.md; no earlier entry is edited.
- **The held-out data.** Every labelled segment in the `ink_9um` label bucket is in the training config. The open
  bucket holds labels for scrolls outside it: **PHerc0841**, three segments, each with `inklabels.zarr`,
  `supervision.zarr` and `validation.zarr` (OME-Zarr 0.5, 2.403 µm, labels dated 2026-09-18): `20260220213127-w00`,
  `20260220214732-auto_grown_20260220144552896`, `20260221022814-auto_grown_20260220174252405`. PHerc0841 is not in
  the config's four training scrolls (0139, 1667, Paris4, 0814) nor in the model card's list. **The population is
  all three segments, fixed now.**
- **The run, fixed now.** Input = each segment's `2.403um-0.22m-77keV-volume-20260319124803.zarr` level 2, pooled to
  21 slices by `python -m vesuvius.ink_detection.preprocessing.prepare_9um_isotropic_input <url> <out> --level 2`
  (villa 5ab585f; the model card's documented route to the model's ~9.6 µm training representation; Gate C used it).
  µm/px = 2.403 × 4 = **9.612**. Model: the same checkpoint, plain, `--direction both`, the same call as R-REPRO.
  Labels: level 2 of `inklabels.zarr` (> 0 = ink) and `supervision.zarr` (> 0 = supervised), which share the pooled
  canvas. On-sheet = pooled CT middle slice > 0 (the reader's standard mask). Unit side round(sqrt(0.5)·10000/9.612).
- **Measures.** (1) Pixel ROC AUC of each map against the labels on supervised pixels, per segment and pooled.
  (2) The FROZEN rule 5.5 (`rule55.evaluate`, `unit_origin="auto"`) on each segment: valid units, flagged units,
  cluster sizes, both depth orders; plus `read_chart.py --maps-only` as the second code path. (3) Every valid unit's
  labelled ink fraction φ, so the flag rate on text-bearing units (φ ≥ 0.02) and on supervised blank units (φ = 0
  with ≥ 50 % supervised) is reported with an exact interval. The crest check is reported, never gates this test.
- **Bars, fixed now.**
  - **HELDOUT-AUC:** TRANSFERS if pooled forward AUC ≥ 0.75 AND reverse AUC ≤ 0.60; NO TRANSFER if forward AUC < 0.60;
    PARTIAL otherwise.
  - **HELDOUT-RULE:** STRONG if any segment yields a ≥ 3 four-connected flagged cluster (a PROMISING CANDIDATE on unseen
    known text); PASS if ≥ 1 valid unit is flagged across the three; BLIND if none is.
- **What follows from each outcome, written now.** BLIND or NO TRANSFER: the release states on its first page that
  this reader, with this checkpoint and frozen rule, has NOT been shown to fire on known text from an unseen scroll,
  and that the eligible-scroll negatives (1/113, 0/190) are therefore not evidence of absent ink. PASS or STRONG: the
  held-out flag rate on text-bearing units replaces w040's 7/71 as the reference rate for unseen text, and the
  release reports both. Either way the result is published; the release does not depend on which outcome occurs.

### R-REPRO RESULT (2026-10-15 07:05 UTC): **BOTH BARS PASS, and the maps are byte-identical to September's**

- **REPRO-GATE-A: PASS.** Forward AUC **0.99659** (record 0.99659), reverse **0.49633** (record 0.49633), on
  **1,629,734** supervised px (record 1,629,734); mean on ink 0.758 / blank 0.252 forward, 0.304 / 0.304 reverse.
- **REPRO-CTRL55: PASS, both code paths.** `rctrl55.py`: on-sheet 46,322,688 px = 40.60 cm² (90.7 % of the canvas),
  frozen `best_origin` (94, 188), **71 valid, 7 flagged, clusters [4, 2, 1]**, outcome CTRL55-STRONG.
  `read_chart.py --maps-only` on the same maps: **7/71, largest cluster 4, PROMISING CANDIDATE**.
- **Bit-identity (reported, not a bar): identical.** The window [1500:3636, 2000:4136] of each map hashes to
  `4eced8f4...` / `2522e682...`, the September pixel record. Beyond that, the WHOLE output files hash to
  `31f001f4f90d42b679d8f57a363ce0b90c4926ec0737dc436db4d7c376d671dc` (forward) and
  `a5425879eb1a1999c15c6c4fde18cdf3aa3e8f2cf5c3e561c1470a06da51b2af` (reverse), exactly the `forward_tif_sha256` /
  `reverse_tif_sha256` that `packages/DRYRUN_PHerc0139_w040/package.json` recorded on 2026-09-17. Same code, same
  versions, same inputs, a different container a month later: **the prediction maps are bit-for-bit the same files.**
- **Cost.** Inference 05:01:22 -> 06:40:40 UTC = **5958 s** for both orders on 4 cores (forward 52 min, reverse 47 min;
  September recorded "~1.9 h per direction under contention"). Scoring, both rule paths and checksums: 3 min 5 s.
- **A gap the run exposed, fixed before this entry.** The first attempt of step 3 stopped at the integrity check with
  "unreadable: COMPRESSION.LZW requires the 'imagecodecs' package": the inference writes LZW TIFFs and the release's
  new `requirements.txt` omitted the decoder. `map_integrity.py` refused the unreadable pair, as designed; the pin
  `imagecodecs==2026.10.10` was added and the run repeated. No number came from the failed attempt.
- **What this does and does not establish.** It establishes that the September control numbers are exactly
  reproducible from public data with the committed code. It does NOT change what they measure: w040 is a
  training-set sheet (R-HELDOUT, above), so this is a reproduced best case, not a held-out validation.
- Records: `records/release/repro_2026-10-15/` (Gate A JSONs, `rctrl55.json`, the reader's stats, input and label
  manifests, output checksums, inference log, the full console of `scripts/reproduce_control.sh`).

### R-HELDOUT RESULT (2026-10-15 08:26 UTC): **HELDOUT-AUC TRANSFERS, HELDOUT-RULE PASS (not STRONG). The model's pixel signal transfers to an unseen scroll; the frozen unit screen almost never fires on that text.**

- **Run as declared.** Three PHerc0841 segments, 2.403 µm level 2 pooled to 21 slices (9.612 µm/px), the same
  checkpoint and call as R-REPRO, both orders. Inference 1825 s, 2274 s and 1940 s (06:40:44 -> 08:21:23 UTC). Every
  pair `map_integrity.py --pair` SOUND. Analysis by `scripts/rheldout.py`, committed (d8c39a3) before any output existed.
- **HELDOUT-AUC: TRANSFERS.** Pooled over 3,669,681 supervised px (914,943 ink): forward AUC **0.8393** (bar ≥ 0.75),
  reverse **0.5486** (bar ≤ 0.60). Per segment forward / reverse: w00 0.8531 / 0.5324; auto_grown_20260220144552896
  0.8176 / 0.5938; auto_grown_20260220174252405 0.8294 / 0.5363. Forward mean on labelled ink 0.534 / 0.543 / 0.522
  against 0.307 / 0.344 / 0.307 on labelled blank; reverse 0.307 / 0.325 / 0.353 on ink against 0.299 / 0.298 / 0.349.
  The depth asymmetry the reader rests on is present on text the model never saw.
- **HELDOUT-RULE: PASS.** Frozen rule 5.5, auto grid: 60 valid units (20 per segment; 12.53, 12.56 and 12.00 cm²
  on-sheet), **1 flagged** (auto_grown_20260220144552896 unit (3,3), φ 0.0935, forward 0.3864, margin +0.0864), no
  cluster, so not STRONG. Swapped order: 0 flagged on all three; tripwire silent. Text-bearing units (φ ≥ 0.02):
  **1 of 15 flagged** (exact 95 % CI 0.0017-0.3195). Supervised blank units (φ = 0, ≥ 50 % supervised): none exist on
  these segments (0 of 0), so the blank arm is empty, not passed.
- **Second code path, `read_chart.py --maps-only` (both grids, the ordinary reader):** verdicts **NOT ESTABLISHED,
  NOT ESTABLISHED, BLANK**. It agrees with `rheldout.py` on the auto grid (0, 1, 0 flagged); the (0, 0) grid adds 1
  and 2 flagged units on the first two segments; no ≥ 3 cluster on either grid, so PASS under both paths.
- **The units with the most labelled ink do not fire.** The seven units with φ ≥ 0.10 (max **0.2347**, more labelled
  ink than any 0.5 cm² unit on w040, whose max on the auto grid is 0.1513) give margins +0.0360 to +0.0663 and forward
  0.3432-0.3729; **0 of 7 flagged**. On w040, a training-set sheet, the comparable figures on the same grid (from
  `records/release/repro_2026-10-15/rctrl55.json`) are **5 of 16** text-bearing units flagged and 2 of 2 at φ ≥ 0.10.
- **What follows, as declared:** PASS, so the held-out rate is reported beside 7/71 as the reference for unseen text:
  **1 of 60 valid units (1.67 %, exact 95 % CI 0.0004-0.0894); 1 of 15 text-bearing units.**
- **EXPLORATORY, computed after the result by `scripts/release_stats.py`:** against the held-out rate, the eligible
  counts are not distinguishable from known text on an unseen scroll: R-DEFICIT 1/113 vs 1/60, Fisher one-sided
  p = 0.575; R-CREST-POWER 11 of 12, 0/190 vs 1/60, p = 0.24 (expected 3.17); PHerc1203 half 0/64, p = 0.484. The
  held-out rate against the training-set control 7/71: p = 0.0523.
- **Reading (INFERENCE).** The eligible-scroll negatives on record (1 flagged of 113 screened units; 0 of 190 at
  R-CREST-POWER) are what this screen returns on REAL text from a scroll outside the training set. They are not
  evidence that the eligible canvas carries no ink. The bottleneck this exposes is the unit screen's sensitivity on
  unseen text (margins diluted to +0.04-0.07 by 0.5 cm² averaging, against a +0.08 bar calibrated on training-set
  text), not the model's pixel-level transfer. Every claim that the corpus negatives are "real negatives" or that
  "there is no ink this detector can find" means only the second half: this detector, at this unit size and bar,
  finds none — as it found almost none on held-out known text. Rule 5.5 does not move: it is frozen. Corrections are
  listed in docs/SUPERSEDED_CLAIMS.md.
- Records: `records/release/heldout_2026-10-15/` (`rheldout.json`, the three readers' stats, checksums of every map,
  pooled input and label set, timings, and the exact preparation, fetch and inference scripts used).
- **CORRECTION to the entry above (2026-10-15 08:40 UTC), found by re-deriving its numbers from `rheldout.json`
  before propagating them:** the seven units with φ ≥ 0.10 have forward means **0.3388-0.3729**, not 0.3432-0.3729
  (unit (3,1) of auto_grown_20260220144552896, φ 0.1003, forward 0.3388, was missed). The margin range +0.0360 to
  +0.0663, the 0 of 7 flagged and the max φ 0.2347 stand. The on-sheet areas, rounded above to 12.53, 12.56 and
  12.00 cm², are exactly **12.5338, 12.5625 and 11.9985 cm²** (the last was rounded up). No verdict, bar or
  conclusion changes. Same practice as the 13:32 UTC correction of 2026-09-19: a number goes in only as computed.

### R-REPRO ADDENDUM (container clock 2026-10-15 12:02 UTC): `scripts/reproduce_control.sh` run end to end from an empty directory; every output identical

- **Why.** The R-REPRO run above fetched its inputs with an earlier, uncommitted helper and ran the inference with the
  identical call before the script existed; the script then ran steps 3-7 in resume mode. Its fetch and inference
  steps had therefore never run as committed. This run started the committed script on an empty work directory
  (`/home/user/hdata/e2e/work`, created 10:12 UTC) in the release container.
- **Step 1 (fetch).** `scripts/fetch_control_w040.py` wrote an inputs `MANIFEST.sha256` byte-identical to the R-REPRO
  record (2776 files, digest `cf8b283a...`); the labels fetched with `hf buckets sync` give a manifest byte-identical
  to the record (8496 files, digest `dfb49aa7...`); the checkpoint sha256 is `e635558a...`, equal to the Hugging Face
  LFS record.
- **Step 2 (inference).** The first attempt (started 10:15:31 UTC) was killed by a container restart at about 10:21
  UTC, before either map was written; the same script was relaunched at 10:25:30 UTC and resumed at step 2. Both
  attempts are in the console. Inference wall time **5526 s** for both orders on 4 cores. The box also ran
  documentation checks, short test runs, two local clones and a figure regeneration during it, so this is not a clean
  timing.
- **Steps 3-7.** Integrity SOUND (both maps 0.907008 non-zero). Gate A forward **0.99659**, reverse **0.49633** on
  **1,629,734** supervised px. R-CTRL55: 71 valid, **7 flagged, clusters [4, 2, 1]**, origin (94, 188). The reader on
  the same maps: 7/71, largest cluster 4, PROMISING CANDIDATE. Window sha256 IDENTICAL to the 2026-09-17 record.
  Whole-file sha256 `31f001f4f90d42b679d8f57a363ce0b90c4926ec0737dc436db4d7c376d671dc` (forward) and
  `a5425879eb1a1999c15c6c4fde18cdf3aa3e8f2cf5c3e561c1470a06da51b2af` (reverse): **the same files as R-REPRO and as
  the 2026-09-17 package**.
- Both Gate A JSONs, `rctrl55.json` and the reader's `read_stats.json` are identical to the R-REPRO records except for
  file paths.
- **What this establishes.** The committed script reproduces the control from public data with no uncommitted step.
  It changes nothing about what the control measures: w040 is a training-set sheet (R-HELDOUT).
- Records: `records/release/e2e_2026-10-15/`.

### R-REPRO ADDENDUM, precision notes (container clock 2026-10-15 12:36 UTC), found by the release's fourth adversarial check

- **"Every output identical"** in the addendum's heading means: both maps byte-identical, every score and verdict
  identical, and the four JSON files identical except for file paths. Run-dependent values differ, as they should:
  inference time (5526 s against 5958 s) and the integrity check's mtime skew (2789.8 s against 2796.8 s).
- **"Resumed at step 2"** means the relaunch re-entered step 1 at 10:25:30 UTC, where every fetch was skipped and the
  checkpoint re-hashed, then ran step 2's inference for both orders from the start (10:25:42 UTC). 5526 s is that
  complete run; the killed attempt's ~5.5 min is not included. The restart time "about 10:21" is the operator's NOTE
  line in the console, not script output.
- **"Before either map was written"** is INFERENCE: villa's infer.py writes each map only after all of that order's
  patches, and the relaunch's forward order took 10:25:54 to 11:11:16 UTC. The first attempt's inference log was
  overwritten by the relaunch; what was seen after the restart is in `records/release/e2e_2026-10-15/first_attempt_note.md`.
- **The labels manifest** named in Step 1 is not printed by the script. It was written by
  `scripts/fetch_control_w040.py <work>/labels/w040 --manifest-only` during the relaunch; its comparison with the R-REPRO
  copy, and the inputs manifest's, are in `records/release/e2e_2026-10-15/manifest_check.txt`.
- **"0.907008 non-zero"** was rounded up by map_integrity.py's six-place rounding. Each map is non-zero on 46,322,688
  of 51,072,000 px = **0.9070075**. The Gate A AUCs quoted at five decimals are rounded to nearest from the JSONs'
  0.9965859995 and 0.4963278136, the convention used since September. No result changes.

### R-REPRO ADDENDUM, correction to the precision notes (container clock 2026-10-15 13:04 UTC), found by the fifth check

- **"The first attempt's inference log was overwritten by the relaunch"** (precision notes, third bullet) is wrong.
  Both of the first attempt's logs (`out/infer.log`, `out/infer.err`) were deleted before the relaunch
  (`rm -f`, recorded in `records/release/e2e_2026-10-15/first_attempt_note.md`); the relaunch then wrote new files
  under the same names. No copy of either survives.
- **"the JSONs' 0.9965859995 and 0.4963278136"** (fifth bullet): the reverse JSON holds 0.4963278135827075, so at ten
  decimals, truncated, it is 0.4963278135. No result changes.
