# CHANGELOG.md (append-only)

- 2026-09-16 Session 1 (rebuild from MASTER_PROMPT_v4). Environment surveyed: no GPU, 4 cores, 15 GB RAM, ~30 GB disk; Docker daemon started manually; VC3D edge image pulled; villa cloned (5ab585f); catalogue fetched; checkpoints, w040 mesh, w028 team TIFF downloaded; w040 stack + labels syncing. RULES.md written with all bars before any run. Repository skeleton created.
- 2026-09-17 Session 1 continued (two container restarts survived via scripts/supervisor.sh; hourly self check-in Routine created). Published VC3D image found stale (2026-05-13); tools rebuilt from villa 5ab585f. Gate A PASS (0.99659/0.49633), Gate B PASS (renderer Pearson 0.999999; model 0.99680 plain, 0.99024 TTA), P-DRY PASS. Pipeline scripts delivered by a 20-agent build/review/fix workflow (86 tests). Level-4 survey of the 23 volumes: new order 0826, 1447, 0175A, 0343, 0358, 0800, 0813, 0191, 1203, 0306B, ... Seeds for PHerc0826 (90); tracer loop + read loop running; first patch traced (5.18 cm², 11 min) and failed QC (frac |n_z|>0.7 = 0.268). 2 µm model timed on CPU: ~9 s per tile, ~14 h per depth order per 5 cm² patch (T-2UM). PHerc0846A rescan control patch being traced on the L2 prediction.
- 2026-09-17 (cont.) Gate C PASS (0.99982 / 0.53058), plain judge 0.7842 / 0.4902, R-5.5 self-test 5/5 text, 0/8 blank. R-CREST declared (VOID for flat-profile renders; pre-check before inference). Rule 5.5 grid origin chosen from the mask, verdict = conservative combination of both tilings; read 2 corrected to VOID and read 4 to NOT ESTABLISHED (one (0,0)-grid unit fwd 0.50). PHerc0826: 5 on-sheet reads (2 NOT ESTABLISHED, 2 BLANK, 1 NOT ESTABLISHED by combination), 8 VOID renders (middle/inner seeds), seeds reordered outer-first. Disk guard caps the VC3D chunk cache; 4 Routines keep the session alive.

## 2026-09-17 18:15 UTC — egress proxy moved after a worker restart; loops restarted
- At 17:02 UTC the session worker restarted and the local egress proxy moved from port 34301 to 37007. The tracer loop,
  the read loop and the review loop kept the old `HTTPS_PROXY`, so from then on every S3 fetch they made failed
  (QC of `auto_grown_20260917164151289` and `auto_grown_20260917165251284`: `ProxyError ... Connection refused`;
  tracer of seed 7336 4488 12520: 15,147 normal-grid fetches returned HTTP 0; tracer of seed 1440 3648 12688 aborted
  on `.zgroup`).
- The trace of seed 7336 4488 12520 (`auto_grown_20260917170122001`, 4.99 cm²) grew largely without normal grids and is
  discarded (moved to `patches/PHerc0826/discarded/`, not QC'd, not read, no ledger line); its seed and seed 1440 3648
  12688 are retraced. Nothing else was affected: Gate C TTA and the 2 µm calibration read local data only.
- `scripts/supervisor.sh` now compares the `HTTPS_PROXY` of the tracer loop and the read loop (new pid file
  `read_loop.pid`) against the current one and restarts a loop that holds a stale value (killing its tracer container,
  whose seed is then retraced). Both loops were restarted under the current proxy at 18:12 UTC.
- LEDGER throughput row for 2026-09-17 filled in from the 27 charts of PHerc0826.

## 2026-09-17 18:45 UTC — CONTROL-2UM: the first rescan trace cross-cuts the sheets; CT crest pre-check declared
- Before rendering the PHerc0846A rescan trace at 2.403 µm, a 512² × 64-slice test render (22 s) came back at the
  volume's air level. Sampling the level-3 CT at the trace points along their own normals gave a flat profile
  (crest ratio 1.043; a render-verified on-sheet 9 µm trace gives 1.35, a VOID one 1.03) and a papyrus fraction at
  the points (0.63) barely above the region's base rate (0.52): the trace does not follow a sheet. The team's L2
  prediction of the rescan is clean where the layers are loose and blob-like in the compressed core where this
  "inner" seed sat.
- `scripts/ct_at_points.py` (+3 tests) implements this as R-CREST-CT, declared in RULES.md with the R-CREST numbers
  transposed (crest ≥ 1.20 in the central half over ±300 µm); calibrated on three PHerc0826 traces against their
  render verdicts (1.350 / 1.369 PASS, 1.026 VOID-CT). LEDGER line for the rescan trace: VOID-CT, no inference.
- Render wrapper: `RENDER_SLICES`, `RENDER_ARGS`, `RENDER_AUTOCROP` overrides; trace wrapper: `SURF_SUFFIX` and
  `VC_CACHE_SUFFIX` are now overridable (the first relaunch of the rescan seeds used the L0 suffix by mistake and
  died on "no metadata" within seconds; fixed and relaunched: five seeds, L2 prediction, cache `_L2`).
- The 1 cm² render/read of a rescan trace waits for a trace that passes R-CREST-CT; the w028 1 cm² calibration
  (forward pass ~14 % at 18:45) continues untouched.

## 2026-09-17 19:15 UTC — rescan seeds regenerated with the CT gate; off-CT smoke seeds dropped
- The 2 µm smoke seeds (`seeds/PHerc0846A_2um_smoke.json`) were picked without the CT gate: seeds 5544 1352 1544
  (traced: QC UNREADABLE, ct_zero 1.00, R-CREST-CT undefined, all CT samples zero), 920 5848 1664 and 2960 1520 1704
  lie outside the masked CT (their level-3 chunks are absent from the bucket). The running trace of 920 was stopped;
  the two on-CT smoke seeds (1816 5752 1544, 1416 3232 1584) are being traced.
- `scripts/seeds.py`: `--coord-scale`, `--ct-level`, `--ct-up` (L2 predictions: CT level 5 at the same pitch as
  prediction level 3), `--ct-erode` (rim inside the mask boundary) and `--max-density` (solid prediction band). New
  `seeds/PHerc0846A_2um.json`: 36 CT-gated seeds (3 bands at 25/50/75 % of z, 12 per band, 4 per radius class; the
  gate removes ~48 % of the predicted voxels, which are whole prediction chunks outside the scan mask).
- `scripts/trace_seeds_2um.sh` traces them outer → middle → inner after the smoke queue; `scripts/precheck_2um.sh`
  runs QC 5.8 and R-CREST-CT on every trace. The first PASS is rendered (1 cm², 64 slices) and read in both orders.

## 2026-09-17 19:30 UTC — R-CREST-CT tightened to the render half-depth; run_2um_patch.sh
- Smoke seed 1816 5752 1544 traced (QC PASS 5.10 cm²) but its CT profile falls monotonically from 60 at −307 µm to 1
  at +307 µm: the trace follows the outside of the outermost wrap, the material lies ≥ 150 µm inward. The ±300 µm
  "central half" rule called that PASS (crest at −8 voxels). R-CREST-CT now requires the crest within ±4 voxels =
  the half-depth of the render window (RULES, disclosed). Calibration verdicts unchanged. LEDGER lines for the two
  new rescan traces (UNREADABLE off-CT; VOID-CT).
- `scripts/run_2um_patch.sh`: window → 64-slice 2.403 µm render (explicit crop, `--scale-segmentation 4`) → R-CREST
  on the render → `run_2um.py` layers 1..63 both orders → `read_chart.py` at 2.403 µm with a ledger line.

## 2026-09-17 20:15 UTC — first sheet-following rescan trace; 2.4 µm render started
- The 2.4 µm gate is now R-CREST on a 28-slice render of the trace at its own pitch (9.612 µm, level 2), the
  established 9 µm-route check; the level-3 CT profile (R-CREST-CT) is too coarse for the thin rescan wraps and is
  kept as a diagnostic only (an x/y swap test flattened every profile, so its frame was right). Interior traces:
  flat (1.029, 1.024) → VOID. The outermost-wrap trace of seed 1816 5752 1544: ratio 3.491, crest at slice 14/28 →
  PASS; its 1 cm² window (crop 1840, 5360; 4160 px; 64 slices) is rendering at 2.403 µm, then both depth orders
  through the 2 µm model. LEDGER correction/confirmation lines; RULES R-CREST-CT amended with disclosure.
- Gate C TTA paused (SIGSTOP) and the PHerc0826 tracer loop paused while the calibration and the rescan read need
  the CPU; both resume automatically (supervisor) when the calibration completes.

## 2026-09-17 20:30 UTC — R-COVER: the outermost-wrap window is air; inference stopped before any tile
- The 2.4 µm render of the chosen window passed the crest check (1.88, slice 32/64) but is air and masked void
  with papyrus fragments: only 28.6 % of its pixels see papyrus in any layer (w040 control: 99.7 %). The 2 µm
  inference was killed at 0/1024 tiles; no map exists. New bar R-COVER (≥ 0.80 coverage) in RULES; `render_cover.py`;
  `window_2um.py` now picks the window by coverage on the level-2 check render (rendered without auto-crop and kept
  until the coverage grid is written); `run_2um_patch.sh` enforces R-COVER on the 2.4 µm render before inference;
  `precheck_2um.sh` ledger lines carry VOID-COVER. Previews of the render kept under `review_sheets/2um/`.

## 2026-09-17 22:20 UTC — PHerc0826 tracing complete; coverage moves to PHerc0358
- The tracer loop reports all active PHerc0826 seeds done (52 .done markers, 53 patch dirs; the 40 middle/inner
  seeds stay skipped as cross-cutting). The read loop still works through the last QC-PASS patches (one read per
  ~40-60 min under the current CPU load). PHerc0358 (survey rank 5; 1447, 0175A, 0343 have no usable surface
  prediction or are excluded per LEDGER) is being traced with CT-gated seeds; its first two traces were VOID by R-CREST.
- The 2 µm seed queue on the PHerc0846A rescan is paused after 14 traces with no sheet-following surface in the
  interior (all flat by R-CREST on the 9.6 µm render) and one outer-wrap surface that is air by R-COVER; it resumes when
  the w028 calibration releases the CPU. Gate C TTA stays paused until then.

## 2026-09-17 23:40 UTC — B-2UM calibration, forward: our 2.4 µm map reproduces the team's map (Pearson 0.9996)
- The 1 cm² w028 calibration (villa `optimized_inference` on CPU, layers 23..85, tile 256/stride 128) matches the
  team's published 2.4 µm prediction pixel for pixel: Pearson 0.9996, AUC 0.9999, text/blank levels within 0.002.
  The 2 µm reading recipe is therefore validated; what is missing for CONTROL-2UM is a sheet-following trace of the
  rescan (0 of 14 so far). Reverse pass running; Gate C TTA and the 2 µm seed queue resume afterwards.

## 2026-09-18 00:05 UTC — screening reads switch to plain inference (TTA on candidates only)
- The frozen rule 5.5 levels were validated on plain maps (R-5.5 self-test); TTA maps are not validated yet and cost
  4x. `run_patch_dir.py --no-tta --tag ink9um_seed42+plain` is the screening call from now on (RULES: reading
  recipe); patches already read under the TTA tag are skipped (`--reread` for a deliberate second read). The two
  TTA reads in flight (PHerc0826 182826749, PHerc0358 211236717) finish as TTA reads; the loops restart afterwards.

## 2026-09-18 01:00 UTC — seeds density gate; PHerc0358 seeds regenerated
- Prediction density at level 3 (31 px window) separates sheet-following traces (all 15 reads ≤ 0.20) from
  cross-cutting ones (16/23 VOID above 0.20). `seeds.py --max-density 0.20 --density-window 31` is now part of the
  seed gate (RULES); PHerc0358 seeds regenerated and ordered outer → middle → inner (90 seeds); tracer loop restarted.

## 2026-09-18 04:10 UTC — B-2UM calibration complete: both depth orders pass
- Reverse pass of the 1 cm² w028 calibration finished (1024 tiles, 4 h 29 min). Our reverse map sits at mean 0.188
  and 0.200 over the team's text pixels, against 0.805 forward: the depth asymmetry that ink produces, with blank
  pixels unchanged at 0.163 vs 0.167. Scored with a reverse-order bar (`--expect-weak`), since agreement with a
  forward map is not the criterion for a reverse map. The 2.4 µm reader is validated end to end on this box.
- Gate C TTA resumed automatically (supervisor) now that the calibration released the CPU; the 2 µm seed queue
  resumes with it. CONTROL-2UM remains blocked only on a sheet-following trace of the rescan.

## 2026-09-18 05:45 UTC — the team publishes 87 reading surfaces on three eligible volumes; tracing stood down
- A 28-agent sweep of all 23 eligible volumes in the open-data bucket (workflow `eligible-asset-sweep`) established
  that exactly three of them publish surface segments, and no other eligible volume publishes any:
  **PHerc1203 22 surfaces (130.2 cm² recorded), PHerc1447 53, PHerc0800 12.** Every other scroll has only
  photos/, representations/ and volumes/ — verified per scroll by explicit listings, not inferred.
- They are tifxyz in exactly the layout our renderer consumes (`x.tif y.tif z.tif meta.json`), in two variants:
  `segments/raw/<uuid>/` (grown patches, as ours) and `segments/<stamp>-<uuid>/mesh/*.tifxyz/` (flattened onto the
  volume). `scripts/fetch_team_segments.py` fetches one per uuid, flattened preferred, writing `source.json` with the
  exact bucket key so every ledger line traces to a public object. 42 MB for all 87.
- PHerc1203 is an eligible volume our ledger records as UNREAD, and it carries a 2.403 µm rescan as well.
- The pipeline now reads `team_*` directories alongside `auto_grown_*` (run_patch_dir, patch_qc, tracer_loop backlog).
  Read loops started for the three scrolls; their tracer loops are marked never-to-run, and tracing on PHerc0826 and
  PHerc0358 is paused while the 87 published surfaces are read. First QC on a PHerc1203 surface: PASS, 3.82 cm²,
  no off-CT pixels.
- Why this matters: two thirds of our own traces end VOID (the surface cuts across wraps) and each costs ~10 min of
  tracer CPU. These surfaces cost nothing and were grown by the team with direction fields and 75 generations
  (see their meta.json `vc_gsfs_params`), parameters our tracer does not use.

## 2026-09-18 06:15 UTC — published surface volumes: 21 stacks read with no rendering at all
- PHerc1447 (15) and PHerc0800 (6) publish the team's OWN renders of their curated segments:
  `<scroll>/segments/<stamp>-<uuid>/surface-volumes/<pitch>-volume-<vol>.zarr/`, 31 slices, uint8, 3.7 GB for all 21.
  `scripts/fetch_surface_volumes.py` drops them into the patch dir as `render.zarr` + `.complete`, so run_patch_dir
  skips its render stage and goes straight to R-CREST, inference and rule 5.5. Provenance in `render_source.json`.
  Using their render is sound because Gate B showed our rebuilt renderer reproduces a team stack pixel for pixel.
- The loops keep at most two unread stacks on disk and stop below 4 GB free; the read loop deletes each after reading.
- Duplicate patch dirs from the first fetch pass (stamp-prefixed names) removed: PHerc0800 12 -> 6 surfaces,
  PHerc1447 53 -> 38, PHerc1203 22 unchanged.

## 2026-09-18 06:10 UTC — the model's window covered the sheet in every on-sheet read
- The 9 µm model consumes exactly 17 slices (`patch_size [17,128,128]`), and `center_crop_layer_indices`
  (external/villa/vesuvius/src/vesuvius/ink_detection/inference/infer.py:200) crops a 28-slice render to indices
  6..22; slices 0-5 and 23-27 never reach the network.
- Measured over all 53 charts on record: the crest sits at slice 11-16 in every non-VOID read (median |crest-12| = 2,
  max 4), i.e. inside the model's window and within the trained jitter of where both controls sit. So the low
  forward-minus-reverse margins are NOT a windowing artefact, and no re-render with a depth offset is warranted.
  The VOID charts are the ones with crests at 0, 1, 4, 23, 25, 27 - the R-CREST bar already excluded them.

## 2026-09-18 07:35 UTC — PHerc1203's published surfaces are exhausted: 21 of 22 cross-cut, 1 blank
- All 22 team surfaces of PHerc1203 have been read. Twenty-one are VOID by R-CREST with crest ratios of 1.03-1.11
  and the crest dead centre: the surfaces are centred on something, but the profile across them is flat, which on a
  9.362 µm scan means tightly compressed wraps with no density contrast between sheet and gap. The one surface that
  passed (team_20250923163331524) read BLANK: forward 0.4329, reverse 0.4215, margin 0.0114, 0 of 5 units flagged.
- So the 130.2 cm² of recorded geometry on this scroll yielded 3.8 cm² of on-sheet reading surface. That is the
  honest number for PHerc1203 and it is now in the ledger's scroll table.
- PHerc1447 and PHerc0800 continue; their curated surfaces come with the team's own renders.

## 2026-09-18 08:55 UTC — Gate C TTA complete: both published judge numbers reproduced
- The TTA pass over the w028 pooled stack finished after 21 h at nice 19. Judge AUC 0.8224 forward against the
  published 0.823 (plain was 0.7842 against 0.784); labels AUC 0.99955 forward, 0.53485 reverse; rule 5.5 self-test
  5/5 text flagged and 0/8 blank, matching the plain result. The frozen rule 5.5 levels separate text from blank
  under both recipes, which is what justifies screening plain and keeping TTA for candidates.
- `score_auc.py` now records the ink threshold it used: the w028 labels are 0/1 and the script's default of 128
  silently produces a null AUC. No stored result changed.

## 2026-09-18 10:00 UTC — the seed density gate is measured, and it works
- PHerc0358 is the one scroll traced both with and without the density gate declared yesterday. Ungated: 10 traces,
  1 readable chart, 8 VOID. Gated: 17 traces, 10 readable, 1 VOID. Readable fraction 10 % -> 59 %, VOID 80 % -> 6 %,
  at the cost of the QC rejection rate rising 10 % -> 35 % (sparser neighbourhoods sit nearer the scroll edge).
- Tracing on PHerc0358 resumed on that basis; the published team surfaces keep being read in parallel.

## 2026-09-18 13:15 UTC — 112 reads, one flagged unit in the whole corpus
- Five eligible volumes now have reads on record: 75 VOID by R-CREST, 22 BLANK, 15 NOT ESTABLISHED, 0 PROMISING
  CANDIDATE, over 128.0 cm² of on-sheet surface (64.4 cm² inside valid 0.5 cm² units).
- Across all of it exactly one 0.5 cm² unit has ever met the flag bar: PHerc0826 auto_grown_20260917090724211,
  forward 0.4812, margin +0.0873, cluster size 1. The rule needs three adjacent flagged units. Nothing else on
  record comes close, which is the honest state of the evidence.
- Disk incident handled: `du` on /var/lib/docker double-counts the overlay `merged` mounts, so Docker looked like
  12 GB when it holds 4.1 GB. The real pressure was 3.6 GB of scratch CT chunk caches under /tmp plus the level-4
  CT caches of scrolls no longer under coverage; the disk guard now drops the latter below 3 GB free.

## 2026-09-18 13:45 UTC — the QC CT-mask bar gets an in-mask AREA arm (24 traces unblocked)
- The zero-fraction bar (>50 % of 100 level-4 mask samples zero → UNREADABLE) turns out to sit inside a dense
  continuum, not a gap: over all 151 QC'd patches the histogram runs 67, 1, 13, 18, 14 | 18, 5, 8, 5, 2 in 0.1 bins,
  so 14 patches pass at 0.40–0.50 and 18 are stopped at 0.50–0.60 with no physical difference between them.
- That bar gates render COST only — the read takes its on-sheet mask from the render's CT mid slice, rule 5.5 needs
  ≥ 90 % on-sheet per unit and ≥ 1.5 cm² of valid units for BLANK — so a half-off-mask surface cannot reach a verdict
  it should not reach. A second arm is added (RULES, declared before the run): a patch also proceeds when
  `(1 − zero_frac) × area_cm2 ≥ 1.5 cm²`. Strict widening; 20 of our traces and 4 published PHerc1447 surfaces
  (9.7, 5.9, 4.6, 3.7 cm² of in-mask area) become readable. Every such read says so on its ledger line.

## 2026-09-18 13:50 UTC — the corpus margin is not a pipeline artefact (Gate B, re-read)
- Across the 37 on-sheet reads the forward level is TEXT-like (median 0.394 plain) while the margin is BLANK-like
  (median +0.002). The stored Gate B numbers settle which: on OUR OWN render of the w040 mesh the plain call gives
  mean 0.7561 on ink and 0.2880 on the same pixels reversed — **margin +0.4681** — against −0.0039 on blank.
- The chain trace → our render → 5.1 → rule 5.5 therefore preserves the depth asymmetry it rests on, and the frozen
  +0.08 bar is about a sixth of a fully inked pixel's margin. The low corpus margins are a physical result about
  those surfaces. Priority moves to AREA and BREADTH.

## 2026-09-18 14:05 UTC — R-CREST-POWER: reading the surfaces the crest veto rejects
- On the two volumes the team publishes, R-CREST rejects almost everything: PHerc1203 21 of 22 at ratios 1.03–1.20,
  PHerc1447 28 of 32 at 1.00–1.02, eleven of them the team's own published 31-slice renders. The per-slice profiles
  say why: PHerc1203's team surfaces have a real, centred crest of only 4–6 % (102 → 107 → 101), and PHerc1447's sit
  at a constant 90.4 across all 28 slices. On tightly compressed wraps there is no air gap to dip into, so a correct
  reading surface has no crest at all and R-CREST has no dynamic range — it vetoes everything before the ink model
  ever sees it. (For contrast, a PHerc0826 trace runs 37 → 106 → 37.)
- Experiment declared in RULES with its population (12 largest-area VOID surfaces, map-blind) and its decision rule
  fixed before any data. `run_patch_dir.py --ignore-crest`, tag `ink9um_seed42+plain+nocrest`, own ledger keys;
  160.2 cm² — more than the whole corpus read so far. Runner `scripts/rcrest_power.sh`, resumed by the supervisor.
- Bug found and fixed on the first attempt: `--delete-renders` left TWO completion markers behind (ours and the one
  `vc_tools.sh` writes, also used by the surface-volume fetcher), so a re-read skipped the render stage and died on a
  missing `render.zarr`. Both markers now go with the render; a patch whose published render is missing stops with a
  pointer to the fetcher rather than quietly substituting one of ours under the team's provenance.

## 2026-09-18 13:49 UTC — breadth: four more eligible volumes enter coverage
- Seeds generated with the density gate for **PHerc0175A** (survey rank 3), **PHerc0343** (4), and regenerated for
  **PHerc0813** (7) and **PHerc0191** (8), which had been seeded before the gate existed — 90 seeds each,
  outer → middle → inner. All four are in the supervisor's COVERAGE list.
- PHerc0826's tracer is paused: 33 reads, 126.9 cm² and 0 candidates make it the most-covered volume in the corpus,
  and with two trace slots the second one is better spent on a volume nobody has read. Active tracers are now
  PHerc0358 and PHerc0175A; PHerc0343, PHerc0813 and PHerc0191 wait behind `tracer_paused` markers.

## 2026-09-18 14:05 UTC — disk: a render floor, and 2.3 GB reclaimed
- Free disk reached 4.1 GB with three renders in flight (one of them 861 MB). A render is the largest write in this
  pipeline and several loops can reach that stage at once, so the floor is now checked before the render starts
  (`run_patch_dir.MIN_FREE_RENDER_GB`, default 5 GB, env `HERCULES_MIN_FREE_RENDER_GB`): below it the patch is skipped
  and the loop comes back, instead of the disk guard cleaning up after a half-written stack.
- Reclaimed: `/tmp/pytest-of-root` (428 MB, now also cleared by the disk guard's low-disk branch) and
  `w028_2um/calib.zarr` (1.9 GB). B-2UM passed in BOTH depth orders, so that input stack is a finished input, not a
  result; every map, comparison and marker is kept under `calib_out/` and `records/2um/`, and `w028_2um/fetch.sh`
  refetches the stack idempotently if it is ever needed again. A note recording the removal sits beside it on disk.

## 2026-09-18 14:30 UTC — two blind spots in the record closed
- **Every valid unit's levels are now stored, not only the flagged ones** (`rule55.summarise_units` →
  `units['0.5cm2'].valid_units`). The flagged list alone cannot say whether a flagged unit is an isolated spike or the
  peak of a locally elevated region, and ink is organised into strokes and lines while noise is not. Only one read in
  the whole corpus had a per-unit table before this, because only flagged units were written. No threshold, cluster
  rule or verdict is touched.
- **R-FLIP tripwire.** Rule 5.5 flags on a SIGNED margin, and "forward" is a property of the surface's normal, which
  `vc_grow_seg_from_seed` picks by its own growth: a mirrored trace carrying ink would put its whole signal in the map
  we call "reverse" and the signed rule would never see it. Measured first: the most negative margin over the 37
  on-sheet reads is **−0.0366**, where a mirrored inked surface would sit near −0.15 (the mirror of the w028 control's
  +0.1492). Nothing on record has been missed by the sign. From now on every read records the swapped evaluation and a
  `depth_swap_tripwire` flag; a firing obliges an orientation check in the geometry and, if the surface really is
  mirrored, a separate re-read under its own ledger key, never a changed verdict.

## 2026-09-18 14:20 UTC — the team publishes a sheet-geometry field, and it has never been used here
- Found while checking whether any eligible volume publishes ink predictions (none does): 14 of the 23 publish
  `representations/predictions/lasagna/`, which is not a surface probability but a **geometry product** — `cos`, a
  winding-phase field at CT level 1; `grad_mag`; and **`nx`, `ny`, the sheet normal components at CT level 2**. Three
  volumes (PHerc0826, PHerc0211, PHerc0125) also publish an `umbilicus` polyline, the scroll axis.
- `scripts/lasagna_normal.py` reads it (blosc chunks, disk cache) and compares a trace's own normal, computed from the
  tifxyz grid, against the published one. **Decoding self-test passes**: pooled median `nx² + ny²` = 0.9093 over
  39 491 occupied voxels on 15 PHerc0826 traces, inside the declared [0.9, 1.1] band.
- **R-NORMAL fails its declared bar** and is recorded as not a discriminator: traces R-CREST calls VOID come back at
  |cos θ| = 0.9887 against 0.9981 for traces it passes, where the bar required 0.60. Nothing is retuned. The useful
  part is what it rules out: a trace driving ACROSS the wraps would sit near |cos θ| = 0, so those surfaces are
  **locally tangent to the sheets everywhere sampled**. R-PHASE (declared before this was known) tests the remaining
  explanation — a surface tangent everywhere that still steps from one wrap to the next.
- Recorded with full disclosure as an incidental, post-hoc observation: the LENGTH of the published normal, which
  behaves as the team model's own confidence in the sheet orientation, separates the two groups with no overlap
  (A 0.970–0.979, B 0.554–0.922). **R-NORMMAG** fixes its boundary at 0.95 from PHerc0826 and requires an
  out-of-sample confirmation on PHerc0358 before it may gate anything; it is running.

## 2026-09-18 14:40 UTC — the corpus has been reading the outer wraps; the limiting factor is interior geometry
- **R-RADIAL** (`scripts/radial_position.py`): for every read surface, its radial position between the scroll axis —
  the published `umbilicus` control points where they exist, otherwise the level-4 CT mask centroid — and the outer
  edge of the scanned material at the same z.
  - Inner half (r/R < 0.50): **62 of 70 reads VOID (89 %)**, only **35.8 cm²** ever read.
  - Outer half: 20 of 51 VOID, **99.3 cm²** read.
  - On PHerc0826, where the crest test demonstrably has dynamic range (1.00–3.12): **15 of 16 inner traces VOID, 17 of
    18 outer traces readable**, every readable surface but one at r/R ≥ 0.717.
  The seeds are ordered outer → middle → inner and the density gate prefers sparse neighbourhoods, which sit near the
  edge; both push coverage outward, and outer wraps are the most damaged and least likely to carry legible text. So
  "no ink in 135 cm²" is a statement about outer wraps, not about scroll interiors.
  PHerc1203/PHerc1447/PHerc0800 are a separate case — VOID at both radii, crest never above 1.42 — which is exactly
  the no-dynamic-range situation R-CREST-POWER was declared to test.
- **R-INTERIOR** (`scripts/interior_resolve.py`) then asked whether the interior is resolvable at all, and **failed its
  declared criterion**: over 36 interior rays the phase field resolves 24 wraps where the surface prediction resolves
  28 (ratio 0.857, bar 1.5), and its implied spacing is 62 % off the CT's own autocorrelation where the prediction is
  27 % off. The phase field is not the better interior product and gets no further role from this test.
- What the same measurement establishes is decisive for the plan: **the interior is not a blur.** The CT shows a wrap
  every 24 level-1 voxels = **449 µm**, and the prediction tracks it. Interior traces therefore do not fail because
  the data is unresolved — they fail because a 5 cm² patch grown at 60 generations has many chances to step across a
  449 µm wrap. Every interior patch on record used the same budget as an outer one.
- **R-SMALL** declared and started: interior seeds only (44 of 90 on PHerc0826, 40 of 90 on PHerc0358), **20
  generations instead of 60**, into `patches/<scroll>_small/`, everything downstream untouched. Baseline 1 readable of
  18 interior traces (5.6 %); the bar is ≥ 30 % over at least 15 traces. `vc_tools.sh` now takes `TRACE_GENERATIONS`.
- Scheduling: the three read loops with a backlog are paused so the R-CREST-POWER queue gets the inference lock (its
  first read had waited 48 minutes behind coverage), and the trace slots go to R-SMALL.

## 2026-09-18 14:46 UTC — G-B-43 passes; R-PHASE fails; the geometry tally closes at four failures
- **G-B-43 PASS.** seed43 on the Gate B render, scored exactly as seed42: forward AUC **0.99562** (bar 0.95), ink
  margin **+0.45806** (bar 0.30), blank margin **−0.03637** (bar 0.05). Two independently seeded networks agree to
  within 0.001 of AUC and 0.01 of ink margin on the same 582 314 supervised pixels. seed43 is admitted as a
  **confirmatory** reader — it never flags or un-flags a unit; every PROMISING CANDIDATE is now additionally read
  with it and the agreement reported with the claim.
- **R-PHASE FAIL, in the reverse direction.** Group A (on-sheet) phase IQR median 0.9402 against group B's 0.5647,
  where the bar required A at or below half of B. A scroll sheet is a spiral, so a surface that follows it *sweeps*
  phase while one that cuts across wraps samples a narrow band locally — the premise was wrong, not the field.
- That closes the tally on the published lasagna geometry product: **R-NORMAL, R-NORMMAG, R-INTERIOR and R-PHASE all
  failed bars written before their data.** No bar was moved and no fifth variant was invented. The field is real and
  readable (pooled decoding self-test 0.9093); its one durable contribution is descriptive — PHerc1203's surfaces
  agree with the published sheet normal at |cos| 0.9967 while 27 of PHerc1447's 31 fall below 0.90 (lowest 0.362).
  So R-CREST looks right on PHerc1447, and the four PHerc1203 members of R-CREST-POWER are where its information is.
- **R-SMALL running on both scrolls.** The declared 20-generation budget produced 0.49 cm² patches — below QC's own
  0.5 cm² bar — so it could not answer the question; the bar did not move and the budget was re-set to 40 from the
  area arithmetic alone (area ∝ budget²). The first 40-generation trace came out at **2.23 cm²** against the 2.2 cm²
  predicted. Both scrolls' interior queues now run, each patch's growth budget is recorded on its ledger line, and
  `scripts/rsmall_result.py` refuses to call the bar until the declared 15 outcomes exist.
- Two scheduling defects fixed: `tracer_paused` only prevented a restart (a paused loop kept tracing), and `TRACERS`
  defaulted to 1 while the slot pool allows 2, so a single trace anywhere blocked every other scroll — PHerc0175A had
  produced nothing for 50 minutes for that reason. 98 tests pass.

## 2026-09-18 16:00 UTC — R-WRAP fails, the spiral lesson, and three pieces of hygiene
- **R-WRAP FAIL, the fifth pre-registered measure of the day.** It was declared to answer a confound in R-SMALL that
  I spotted before its numbers: "readable" there means the render passed R-CREST, and R-CREST needs a
  papyrus-to-gap contrast. The first 40-generation interior trace renders as a ramp, 97 → 102 across all 28 slices —
  a window entirely inside solid material — so a trace could hold to one sheet and still render flat. R-WRAP measured
  radial spread in units of the 449 µm wrap spacing: group A (one sheet) **28.47 wraps**, group B (crest-VOID)
  **16.95**, against a bar of 1.5 and half of B. Fails both halves.
- **The lesson is physical, and it retires a family of proxies.** R-PHASE and R-WRAP both failed because a scroll
  sheet is a **spiral**: following it through one turn moves you outward by one wrap, so a surface that genuinely
  holds to a sheet *sweeps* phase and *spans* many radii — more than one that cuts across and stays put. No scalar
  spread statistic separates a good surface from a bad one here, because the good surface is the one that moves.
  **No sixth variant is declared.** R-SMALL is judged on its declared bar with the confound stated; R-CREST-POWER
  needs no geometric proxy at all.
- `METHOD.md` rewritten: it still described TTA screening, one QC arm and seed43 as retired. It now records the
  recipe as it runs, what the corpus covers, and the five failed measures.
- **Bright-ink-in-render loop closed** (page item 7): over 41 reads, 39 have no elongated marks and two have exactly
  one, both isolated, both on charts rule 5.5 called BLANK. Neither is evidence of text and neither is treated as a
  lead; the checks stay on record.
- **Disk-guard defect fixed.** Pruning the normal-grid cache to 500 MB whenever free disk was under 7 GB meant the cap
  applied almost always, so every tracer refetched its grids: 40-generation traces went from the predicted ~250 s to
  15 minutes. Two tiers now — 500 MB under 5.5 GB free, 900 MB between 5.5 and 7 GB.
- Weekly prize-page re-read: **all 23 First Letters volumes still listed, none claimed.** Recorded with a trap note —
  `scrollprize.org/firstletters` is the October 2023 PHercParis4 announcement and is a different, already-awarded prize.

## 2026-09-18 15:27 UTC — INTERIM (n = 4, the bar needs 15): the reduced budget produced a readable interior surface
- **`PHerc0826 auto_grown_20260918144212741`, 40 generations, 2.11 cm²** — the first interior trace to reach the
  reader since R-SMALL began, and only the second readable interior surface in the whole corpus. Crest **1.250** with
  the crest at slice 12, dead centre; the per-slice profile runs **86 → 101 → 81 → 90**, an actual sheet with air on
  both sides, where every 60-generation interior trace gave a flat ramp. **2.02 cm² on-sheet in 4 valid 0.5 cm² units**
  — enough for a BLANK verdict and enough for the three-unit cluster a candidate needs.
- Verdict **BLANK**: forward 0.3020, reverse 0.3292, margin −0.0272, no unit near the frozen levels, depth-swap
  tripwire clear. No ink here. What it demonstrates is that the interior is reachable at all.
- R-SMALL stands at **1 readable of 4 outcomes (25 %)** against the 5.6 % baseline. **This decides nothing**: the bar
  written before the run is ≥ 30 % over at least 15 outcomes, chosen precisely so a one- or two-trace fluctuation
  cannot carry it. Recorded here, not in RULES, because it is not yet a result.
- Worth noting for later: that interior read's forward level of **0.3020** sits at the w028 control's BLANK level
  (0.2832), while the outer-wrap reads run at a median of 0.394. If that holds up across more interior reads, the
  outer wraps have been reading high for a reason that is not ink.

## 2026-09-18 16:32 UTC — INTERIM (n = 9, the bar needs 15): R-SMALL has now produced a textbook interior sheet
- Second readable interior trace at the reduced budget: **`PHerc0826 auto_grown_20260918152701336`, 40 generations,
  2.09 cm²** — crest **3.107**, crest slice 12, per-slice profile **41 → 128 → 41**. That is a sheet with clear air
  on both sides, as strong as the best outer-wrap traces on record (which top out at 3.12), and it sits in the
  scroll interior where every full-budget trace gave a flat monotonic ramp. 2.02 cm² on-sheet in 4 valid units.
- Verdict **BLANK**: forward 0.4436, reverse 0.4555, margin −0.0119, no unit near the frozen levels, tripwire clear.
  No ink on this surface. What it establishes is that **the interior is now reachable with genuine sheet geometry**,
  which is the thing that was blocking everything.
- R-SMALL stands at **2 readable of 9 outcomes (22.2 %)** against the 5.6 % baseline. Still short of the 30 % bar and
  still short of the 15 outcomes the bar requires, so it decides nothing yet; recorded here rather than in RULES.
- Its render was deleted by `--delete-renders`, so that one 2 cm² surface is being re-rendered for the R-EYES check
  against the w040 reference — the first chance to see whether an interior surface shows the crosshatched fibre
  weave rather than laminar strata.

## 2026-09-18 19:00–20:10 UTC — the blocker is measured: patch density, not the reader, the budget or the parameterisation
Every item below has its bar in RULES.md, written before the run, and none of them moved after a result.

**Bars called.**
- **R-SMALL FAILS** at 20.0 % readable over 15 outcomes against its declared 30 % (baseline 5.6 %). The 40-generation
  interior budget is not adopted. It nonetheless produced the only interior surface matching the known-text reference
  (fibre weave, on-sheet CT std 45.4 vs 43.1) and one of the corpus's two flagged units; both are ledgered and neither
  rescues the bar.
- **R-CROSS NOT ADMITTED** at 1.87x against a 2.0x bar (HIGH group 86.7 % unreadable, LOW 46.4 %). Gates nothing.
- **G-GP part 1**: 15 of 106 traces parameterisation-degraded; our meshes carry 3x the team's sag at identical node
  spacing and comparable patch size.
- **G-GP part 2**: `vc_flatten` INEFFECTIVE. It changes node density, and the declared test compared raw sag across
  densities; at a matched 187.2 µm baseline the flatten makes 3D sag WORSE (64.6 → 84.6 µm) while improving UV
  anisotropy. The literal test would have passed it on an artefact. The stricter test stands.
- **G-GP part 3**: not run — precondition measured and failed. At the team's `consensus_default_th: 6` our 66 PHerc0826
  patches support **1.15 cm²** of six-fold agreement (upper bound), max 7 anywhere; PHerc0358's 43 support 0.09 cm².
- **G-GP part 3b**: the prediction from that precondition tested and corroborated — stage 2 ran on a locally
  materialised prediction box (295 MB) with all 56 source patches loaded and returned **0.11 cm²**, reporting
  `best th: 0` at every candidate while dropping its inlier threshold from 20 to 2.

**The finding.** `vc_tifxyz_selfcross` — the team's own census, which we had never built — puts our median trace at
**262.61 transverse self-intersections per cm²** against **1.42** for the w040 known-text control and **0.00** for the
team's median published segment on the same scrolls. The team's segments record
`vc_grow_seg_from_segments_params {consensus_default_th: 6, ...}`: they are consensus surfaces grown from a directory of
patches. A six-fold consensus cannot fold through itself. We have run only stage 1, for 141 reads.

**My own error, recorded with the weight of a failed bar:** `build_vc3d.sh` built 7 of the 48 VC3D apps. Six hand-rolled
geometry measures were declared and failed today while the team's instruments sat unbuilt in a checked-out source tree.

**Strategy reversal.** Seeds are placed 320 voxels apart and the wrap spacing is 48 voxels, so two seeds can be six
wraps apart. G-GP part 4 seeds 25 traces from ONE patch's own surface points — source chosen by a rule written first
(`PHerc0826 auto_grown_20260917043355441`: 4.82 cm², 0.00 crossings/cm², p90 sag 16.0 µm). Milestone 1 is 4 cm² at
[line withheld: prize-candidate detail under review]

**Declared and running:** R-DEPTH (all 141 reads sit at depth offset 0; the 17-slice window swept across the 28-slice
control render and scored against the published labels) and R-BEST (the TTA reader on the 3 surfaces as clean as the
ground-truth control — one of which already had its TTA read and is NOT ESTABLISHED, recorded before the others ran).

**Descriptive limit on what the corpus supports:** of 135.1 cm² that reached the ink model, **36.2 cm² was on
geometrically sound surface, 22.9 cm² of it interior**. A scroll is 10 000–30 000 cm². The supportable statement is
"nothing in the ~23 cm² of sound interior canvas we read properly", never "no ink in these volumes".

**Defects found and fixed:** the disk guard pruned normal grids under a live tracer (a ~4x tax on interior traces),
and its replacement exemption was then uncapped and took the box from 8.1 GB to 3.8 GB free — now capped at 1500 MB,
8 tests. A dense queue reported itself done after 1 of 25 seeds; cause not established (most likely a duplicate loop I
started myself), fixed by shape — the queue is materialised before the loop and the tracer's stdin is closed, 4 tests.
A near-retraction of the normal-grid claim was itself withdrawn: `normal_grid_path` IS read, at `GrowPatch.cpp:3432`,
which my grep had missed.

Tools built beyond the original seven: `vc_tifxyz_selfcross`, `vc_tifxyz_winding`, `vc_grow_seg_from_segments`.
New scripts: `mesh_distortion.py`, `ggp_result.py`, `rcross{,_result,_split}`, `patch_agreement.py`, `sheet_seeds.py`,
`dense_loop.sh`, `vc_consensus.sh`, `fetch_pred_box.py`, `good_canvas.py`, `rdepth{.sh,_result.py}`, `rbest.sh`,
`build_vc3d_extra.sh`. Test suite 128 passing.
- 2026-09-19 (02:00-03:10 UTC) **The night the instrument was validated against known text.** The 5.162 cm² consensus surface — 26 sources, zero self-intersections, p90 sag 5.11 µm — read **NOT ESTABLISHED**, 0 flagged of 2 valid units (forward 0.4391/0.4508, margins +0.0053/+0.0014). That forward level is at or above the known-TEXT units that calibrated rule 5.5, with a twentieth of their margin, which forced three declared experiments. **R-SYM** (bars fixed before the run): the pixel-wise correlation between forward and reverse maps over rule 5.5 valid units; control anchor holds at **r = −0.0088**, corpus runs 0.1153-0.5779 (median 0.3043), **0 of 9 depth-symmetric** — outcome DS-SPLIT, four reads nominated for a second look, no verdict changed. So the reverse map is *not* a copy of the forward map and a mean can, in principle, cancel a localised signal. **R-SENS**: arm 2 is empty — the w040 supervision mask covers 3.19 % of its canvas and w028's 1.19 %, so no 0.5 cm² window anywhere is 90 % supervised; arm 1's area-mixture floor of 26.1 % ink per unit is void as a bound because a convolutional reader responds in a halo. **R-CTRL55**, the decisive one: the frozen rule 5.5, unchanged, on the w040 known-text control's full 40.60 cm² canvas — **7 flagged of 71 valid, clusters [4, 2, 1], a four-unit PROMISING CANDIDATE**, and every flagged unit the labeller examined is **36-70 % ink**; not one is demonstrably blank. **The chain fires end to end on real Herculaneum text on a sheet the model did not memorise, so every corpus negative on record is a real negative.** It also prices the problem: one candidate per 40.60 cm² of text-bearing sheet against the ~23 cm² of sound interior canvas ever read — **canvas area is the binding constraint**. Two of my own errors caught and recorded: a sensitivity curve drawn from whole-unit ink fractions on a mask with median per-unit coverage of zero (withdrawn), and a `unit_origin` tuple passed where `evaluate()` wanted `"auto"`, which silently tiled from (0, 0) while the log claimed (94, 188) — fixed, and caught only because `read_chart.py` on the same maps disagreed. **G-GP part 5** declared and running: 60 second-generation seeds from the consensus surface's own grid points, bar ≥ 10 cm² at the control's own crossing rate and sag. New: `scripts/rsym.py`, `scripts/rsens.py`, `scripts/rctrl55.py`, `review_sheets/reference/CONTROL_w040_rule55_PROMISING_CANDIDATE_cluster.png`.
- 2026-09-19 (03:10-05:30 UTC) **Two of my own results withdrawn, and the instrument validated at both ends.** **R-DEPTH was ADMITTED at 03:45 and WITHDRAWN at 04:20**: its HIGH reverse map was 25.00 % written — exactly one quadrant — the inference exited 0, the completion marker was set, and the unwritten zeros were averaged in as if the model had answered zero there, producing mean_on_ink 0.11221, M(HIGH) 0.60594, a gain of +0.13786 and the verdict. Caught only because R-CTRL55-W ran the frozen rule on the same maps and every unit returned `rev 0.0000`. Everything the verdict caused was undone: part 2 paused, its running read killed, its partial output deleted, R-CTRL55-W marked void on its HIGH arm. **A full audit of all 55 forward/reverse pairs on disk (`scripts/map_integrity.py`, two relative tests: the pair's footprints must agree to 0.02, and each must cover ≥ 99 % of the on-sheet mask) finds exactly one suspect — that one.** No corpus read, verdict or gate is contaminated. The first version of that checker was itself wrong and is recorded: an absolute non-zero bar flagged 19 sound auto-cropped maps. The guard now lives in `read_chart.py` and in `rdepth.sh`, before the scorer and before the completion marker, with no flag to switch it off; eight tests pin it, including two proving an auto-cropped surface is not refused. Also withdrawn: a sensitivity curve drawn from whole-unit ink fractions on a mask whose median per-unit coverage is zero. Also fixed: `rctrl55.py` passing a `unit_origin` tuple where `evaluate()` wanted `"auto"` (it silently tiled from (0,0) while logging otherwise), a guessed PHerc0358 volume id caught before it ran (volume ids are now parsed from the supervisor's COVERAGE string, with a test forbidding literals), and **protocol 9's step 6 looking for candidates in `patches/<scroll>`** — wrong for every surface the concentrated campaign produces, so it would have failed at the confirmatory read with a candidate on the table; `P9_DRY=1` now rehearses all 15 inputs and prints every command. **R-POP** (declared before the run): the margin is monotone in ink content on the control — unflagged units read +0.0131, +0.0220, +0.0398 by how much text the labeller found in them, flagged units +0.0989 — and our corpus sits at +0.0014 with an IQR ratio of 0.967, so **POP-NARROW is ruled out** and no signal is being squeezed below the bar. Its first run was invalid (41 of 50 reads carry an empty forward `valid_units` list; the population is now reconstructed exactly from the swapped table's mirror, 106 plain units over 29 reads). **No free canvas remains**: every published team segment across all 23 eligible volumes is held, the last one fetched and measured at p90 sag 7.96 µm. **The concentrated campaign has moved our canvas to r/R 0.606**, from the 0.83-0.86 outer band that is all the corpus had ever read. **G-GP part 5** declared and running: 60 second-generation seeds from the consensus surface's own grid points, six-fold agreement at 5.62 cm² by 30 traces, the consensus build armed to fire automatically when the queue finishes. New: `scripts/map_integrity.py`, `scripts/rpop.py`, `scripts/rdepth_part2.sh`, `scripts/ggp5_when_ready.sh`, R-DEPTH windows wired through `run_patch_dir.py` with the layer arguments locked to the ledger offset.
- 2026-09-19 (05:30-03:45 UTC container clock; the earlier entries' wall-clock labels run about two hours fast, recorded in RULES and not edited) **R-SMALL resolved against us, R-CREST cleared, and four more defects found.** **R-SMALL FAILS**: 19 forty-generation interior traces, all resolved (11 VOID, 4 QC FAIL, 1 QC UNREADABLE, 2 BLANK, 1 NOT ESTABLISHED), readable 3 of 19 = **15.8 %** (3 of the 14 reaching a read = 21.4 %) against a **≥ 30 %** bar and a 5.6 % baseline; both denominators reported, both short, and **the budget goes back to 60 exactly as declared** even though the 2.8-fold gain is real. **R-SMALL-2** declared as its pre-written successor (density cap 0.20 → 0.30, newly admitted band only, same budget, same bar) with **80 interior seeds** built (r/R medians 0.339 and 0.389) and armed to start when part 5 frees a trace slot. **R-CREST is not hiding recoverable canvas**: of 469.7 cm² vetoed, 463.6 cm² fails on the crest RATIO with values at 1.00-1.11 — flat profiles, where a shifted window changes nothing — and the only 6.0 cm² with a real off-centre peak has it at slice 0, the render's edge. **The truncation mechanism was captured**: an inference died leaving "18 leaked semaphore objects", i.e. workers killed under pressure; seven scripts passed seven different inference locks so none serialised against the others, and a **global cap of 2** now applies to every caller including the scripts that call inference directly (`infer_slot.sh`), with dataloader workers 3 → 2. **A seed-cache collision** gave one scroll another scroll's 90 seeds under the correct URL; caught because two scrolls cannot give identical numbers, the historical files were then checked and have zero overlap, and cache entries are now namespaced by source URL. **`rbest2.sh` was crashing on every `PHerc0826_small` member** of its declared population by passing a patches directory as `--scroll`. **The submission package was not verifiable after its render was pruned** — `verify_package.py` re-opened an external render zarr that the disk guard removes routinely — so the packager now carries the raw CT crop and its sha256 inside the package, the verifier checks crop-vs-manifest, PNG-vs-crop and both-vs-live-render, and a check whose input is gone reports **N/A**, never a pass and never a package failure. Measured and recorded: the model's strongest responses come from the renders with the **least** texture (r = −0.4960 between on-sheet CT std and frac > 0.75; fourteenfold difference in strong-response fraction below a CT std of 25), which bears on the two surfaces at the top of the review index and is written down before either is re-read. Also: **LEDGER audited complete** (141 reads, 0 unledgered), both audits now run on every check-in, and protocol 9 rehearsed with `P9_DRY=1`. New: `scripts/map_integrity.py`, `ledger_audit.py`, `infer_slot.sh`, `ggp5b_decide.py`, `rsmall2_when_ready.sh`.
- 2026-09-19 (08:20-09:40 UTC) **The morning the binding constraint was finally named as a number — and three of my own claims were corrected.** **R-DEFICIT**: 1 flagged unit of 113 on the plain screening recipe against the w040 control's 7 of 71, **Fisher exact one-sided p = 0.0058**, 11.1 expected. The *candidate* count carries almost none of that information (0 observed, 1.59 expected under the control's cluster density, P(0) = 0.20), so "no candidate in 56 cm²" was being over-read fivefold. **R-BLANK** (declared before it ran, interpretation fixed before the numbers): on the control, the 44 valid units with **zero labelled ink** return a median margin of **+0.0134** against our corpus's +0.0014 and a declared bar of +0.0042 — and the like-for-like check was done rather than assumed (median-over-units +0.0277 vs whole-map +0.0255 on the control, an 8 % difference). **Part 2** tested the caveat the declaration itself had recorded: the margin falls off the text and then **plateaus at +0.0131 for the 29 units ≥ 4 mm from any labelled ink**, so the floor is not proximity. **The domain-gap escape was then closed by provenance**: the w040 control is PHerc0139 at `9.362 µm / 1.2 m / 113 keV` — the same scan configuration as PHerc0826, PHerc0358 and PHerc1203 — with the renderer byte-verified and crest centring matched (weighted mean slice 13.19 against 12). **R-ORIENT** tested the one confound that could have made all of this unfair: our traces' sheet orientation is unknown and rule 5.5 flags on a *signed* margin. Reconstructing all 189 per-unit margins from the swapped tables, the signed distribution is symmetric (50.8 % positive, 15 of 31 surfaces negative) — but **the depth-swap tripwire has never fired in 52 reads** and nothing reaches the bar backwards (extremes −0.0714, +0.0873), so orientation correction adds **zero** flagged units and the deficit survives. Orientation-free, the corpus sits at **|0.0122|** against the control's labelled-blank **+0.0134** and labelled-inked **+0.0438**: *our canvas reads like control papyrus with no ink on it, and nothing like control papyrus with ink.* **R-SHAPE renamed the binding constraint for the third and most precise time.** Computed from the actual recorded per-surface unit layouts instead of the control's cluster density, our entire corpus expects **0.079 candidates even if every unit of it were as inked as the control** — twenty times below the 1.59 I had recorded that morning, because that figure silently assumed our units were laid out as the control's single contiguous 71-unit grid. Ten of 31 surfaces cannot hold a 4-connected triple at any flag rate; median 4 valid units per surface, best 9. I then tested R-SHAPE's own weakest assumption and **it failed in my favour**: the control's observed 4-cluster is a 1-in-39 event under independent flagging, so real ink clusters far more and 0.079 is a **lower bound** (~0.5 after the control's measured excess) — the strong claim "our canvas cannot form a candidate" is withdrawn, the supported one ("zero candidates is the expected outcome at this size and shape") stands. Calibrated against clean contiguous known-text canvas, **a qualifying candidate is a ~1-in-5 event per 35 cm²**. **R-COVER9 and its correction**: our surfaces score 0.584 papyrus coverage against the control's 0.907 and the consensus surfaces are the worst (0.412, 0.427) — but my reading of that, "half off the papyrus", is **wrong and withdrawn**. Two explanations were tested and both failed (a level-4 CT proxy that calls both consensus surfaces firmly on papyrus; node spacing as regular as the control's, median 20.0–20.1 vx, zero edges beyond 2× nominal), and that is how the error surfaced: the measure tracks the tifxyz **grid fill fraction**, and the consensus surfaces are **ragged**, filling 0.476 and 0.495 of their own bounding grid where the control fills 0.862. **G-GP part 5 completed** — both outputs BLANK, 0 flagged of 5, mean margin −0.0113, and they are **one surface written twice** (same grid 174×258, same 22 228 nodes), now deduped automatically so no later tally inflates the canvas. **G-GP part 6** swept `consensus_default_th` over 4/6/8/10 and **refuted the prediction recorded before the build**: fill peaks at the team's own default 6 and falls on both sides, area peaks there by 2.4×, so the raggedness is what this growth method produces and the knob is **closed**. **G-OWN** — the one link in the validation chain never gated against known text, since Gate A validated the model, Gate B the renderer, Gate C the calibration and R-CTRL55 the rule, but never the tracer this project built on top of them — was declared with bars fixed before the trace, seeded on the w040 mesh cell carrying 19.65 % labelled ink, and **passed its admissibility gate decisively**: 4.845 cm², **98.9 %** of points within one wrap spacing of the known-text mesh, median distance 85 µm, QC PASS at mean |n_z| 0.2324. The team's own mesh returns **+0.0416** over the exact 4.32 cm² our trace covers, which carries 2.1× the canvas-average labelled ink; its read is running. **A defect that would have made R-SMALL-2 unanswerable**: its traces land in `patches/<scroll>_rs2` and the supervisor's reduced-budget read loop was hard-coded to `_small`, so 15 traces had been grown and **not one QC'd or read** — the bar is a readable *fraction*, so it could never have been evaluated however long the tracer ran, and the rising trace count made it look healthy. Fixed by making the suffix a loop variable; both loops now read, first results VOID at crest 1.01–1.11. Disk held above the floor throughout by removing 1.9 GB of unreferenced vendored website, caches and orphan renders, checked by grep before deletion and with `import vesuvius` verified afterwards. New: `scripts/rblank.py`, `rblank2.py`, `cluster_power.py`, `coverage_proxy.py`, `gown_result.py`, `gown_when_ready.sh`, `ggp6_when_ready.sh`, `ggp6_read_when_ready.sh`. Test suite **259 passing**.
- 2026-10-15 **Public release for the Progress Prize (October 2026 cycle).** Fresh container, September data root gone.
  **R-REPRO PASS**: the w040 known-text control re-created from public data with the committed code is byte-identical
  to September (Gate A 0.99659 / 0.49633; 7/71, [4, 2, 1]; both TIFFs' sha256 match `package.json`), and again when the committed `scripts/reproduce_control.sh` ran end to
  end from an empty directory. **w040 found to be a training-set sheet** of `ink_9um` (villa's training config). **R-HELDOUT** (declared before download) on
  three labelled PHerc0841 segments: pixel AUC 0.8393 / 0.5486 TRANSFERS; frozen rule 1 of 60 units PASS (not STRONG);
  the eligible negatives are not significantly below that rate (exploratory p = 0.575, 0.24; against the declared
  text-unit rate 1/15, p = 0.221, 0.0732). The published VC3D `:edge` image
  verified still stale. Release docs written from 1119 extracted claims (METHODS, RESULTS, LESSONS 37,
  REPRODUCE, SUPERSEDED_CLAIMS, scripts index), quick start on real known text (16 s, 10 checks), statistics
  recomputed by code (10/10 reproduce; cluster-collapsed sensitivity added), disk_guard keep-list bug fixed,
  portable paths, 1.4 GB of overlays moved out of the release tree (kept in history at 71720ce).
