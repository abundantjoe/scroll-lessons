# METHOD.md — current recipe and retired changes

Every bar and every result referenced here is in `RULES.md`, written before its run and never edited afterwards.
`LEDGER.md` carries one line per read. This file is the recipe as it stands today.

## Current recipe (rebuilt from MASTER_PROMPT_v4 section 5; each step is a script in `scripts/`)
1. **Seeds (5.6, `seeds.py`).** Level 3 of the surface-prediction zarr, threshold >= 128, 5 slices per z-band, three
   z-bands per scroll, outer/middle/inner thirds by distance from the slice centroid, >= 40 level-3 voxels apart,
   ~30 seeds per band, ordered outer -> middle -> inner. Two gates on a candidate:
   - the **CT gate** — the level-4 CT value at the seed must be > 0 (the 5.8 mask criterion), and
   - the **density gate** — `--max-density 0.20 --density-window 31`: the level-3 prediction density in a 31 px
     (~2.9 mm) window must not exceed 0.20. Measured effect on PHerc0358, the one scroll traced both ways: readable
     traces 10 % -> **59 %**, VOID 80 % -> 6 %, at the cost of QC rejections rising 10 % -> 35 % (RULES, seeds density
     gate). Note the side effect quantified later by R-RADIAL: sparse neighbourhoods sit nearer the scroll edge, so
     this gate biases coverage OUTWARD.
   - `interior_seeds.py` selects the interior subset of a seed file by radial position, for R-SMALL.
2. **Tracer (5.7, `tracer_loop.sh` -> `vc_tools.sh trace`).** `vc_grow_seg_from_seed` in the VC3D container, params
   `{"mode":"seed","min_area_cm":0.2,"generations":<TRACE_GENERATIONS, default 60>,"thread_limit":2,...}`. **Normal
   grids are mandatory** (without them traces cut across windings: mean |n_z| 0.75-0.83). A two-slot pool caps
   concurrent 9 µm traces; `TRACE_GENERATIONS=40` is the reduced interior budget under test (R-SMALL), and every
   patch's budget is recorded on its ledger line.
3. **Patch QC (5.8, `patch_qc.py`).** Per-cell normals from the tifxyz grids; PASS if mean |n_z| <= 0.50 AND
   frac(|n_z| > 0.7) <= 0.25 AND area >= 0.5 cm². Then the CT-mask check at level 4, which now has **two arms**: the
   patch proceeds when `zero_frac <= 0.50` OR the estimated in-mask area `(1 - zero_frac) * area_cm2 >= 1.5 cm²`
   (RULES, in-mask area arm — the zero-fraction bar sits inside a dense continuum, not a gap, and it gates render
   COST only). One overlay per scroll on a level-4 slice.
4. **Render (5.9).** `vc_render_tifxyz ... --num-slices 28 --slice-step 1 --scale 1 --group-idx 0
   --voxel-size <pitch> --auto-crop`; all-zero render => delete and re-render, give up after three. A render is not
   started below a 5 GB free-disk floor. Deleting a render drops BOTH its completion markers, or a re-read silently
   skips rendering. Where the team published their own surface volume, that render is fetched instead of made
   (`fetch_surface_volumes.py`) and a missing one is re-fetched, never quietly replaced by ours.
5. **Read (5.10, `run_patch_dir.py` -> `read_chart.py`).**
   - **R-CREST pre-check** on the render (crest ratio >= 1.20 with the crest in the central half) before any
     inference; VOID otherwise. `--ignore-crest` turns the veto into a recorded statistic for the declared
     R-CREST-POWER experiment only, under its own tag and ledger key.
   - **Screening inference is PLAIN**: `python -m vesuvius.ink_detection.inference.infer <stack.zarr> <ckpt>
     <out.tif> --direction both --batch-size 4 --no-compile --num-workers 3`, checkpoint `seed42 step-075000`, tag
     `ink9um_seed42+plain`. Both depth orders, always. `--tta-mirror` is for candidates, not screening (RULES,
     reading recipe): the frozen rule levels were validated on plain maps, and TTA costs 4x.
   - **Rule 5.5** at 0.5 and 1 cm², on the mask-origin grid with the fixed (0, 0) grid recorded alongside and
     combined conservatively. Every VALID unit's levels are stored, not only the flagged ones.
   - **R-FLIP tripwire**: the swapped (reverse-as-forward) evaluation is recorded on every read, because a mirrored
     surface carrying ink would put its signal in the map we call "reverse". It changes no verdict; a firing obliges
     an orientation check and, if the surface really is mirrored, a separate re-read under a `+flip` key.
   - Contact sheet, ledger line, bright-ink-in-render check.
6. **Confirmation.** A PROMISING CANDIDATE is additionally read with `--tta-mirror`, and with the **second
   checkpoint seed43** (admitted by G-B-43: forward AUC 0.99562, ink margin +0.45806, blank margin -0.03637 on our
   own render of the w040 mesh). seed43 is confirmatory only — it never flags or un-flags a unit.
7. Review folder (5.12), flattening before packaging (5.13), packager + verifier (5.14), protocol 9.

## What the corpus actually covers, and the standing constraint
- **R-RADIAL (2026-09-18):** the reads are overwhelmingly OUTER WRAPS. Inner half of the radius: 62 of 70 reads VOID
  (89 %), 35.8 cm² ever read; outer half: 20 of 51 VOID, 99.3 cm². On PHerc0826, 15 of 16 inner traces are VOID and
  17 of 18 outer traces readable. The seed order and the density gate both push coverage outward, and outer wraps are
  the most damaged and least likely to carry legible text.
- **R-INTERIOR (2026-09-18):** the interior is NOT unresolved — the CT's own autocorrelation shows a wrap every
  **449 µm** and the surface prediction tracks it to 27 %. So interior traces fail because a 5 cm² patch grown at 60
  generations has many chances to step across a 449 µm wrap, not because the data is a blur. **The limiting factor is
  interior geometry, not area and not breadth.** R-SMALL tests the budget.

## The pipeline stage we were missing, and the measurements that found it (2026-09-18)
- **Two stages, not one.** The team's published segments carry `vc_grow_seg_from_segments_params
  {"consensus_default_th": 6, "consensus_limit_th": 2, "global_steps_per_window": 2, "step": 6}`. Their surfaces are
  **consensus surfaces grown from a directory of stage-1 patches**; ours are single greedy traces. A point accepted only
  where six patches agree cannot fold through itself.
- **R-CROSS** (`vc_tifxyz_selfcross`, the team's own report-only census, built 2026-09-18): our median trace carries
  **262.61 transverse self-intersections per cm²** against **1.42** for the w040 known-text control and **0.00** for the
  team's median published segment on the same scrolls. Not admitted as a gate (1.87x against a 2.0x bar); decisive as a
  description. Note the spread within our own traces: 33 patches >= 4 cm² with a non-VOID read include several at
  **0.00/cm²**. Our tracer produces GP-quality surfaces some of the time, and we have been reading everything.
- **G-GP part 1**, mesh parameterisation (`mesh_distortion.py`, arithmetic on grids already on disk): stretch,
  anisotropy, shear and **sag** (distance in µm from a node to the plane of its four neighbours). Control 9.9 µm p90
  sag, team 27.8, ours 60.4. Compare meshes only at a **matched physical baseline** (`--baseline-um`) when their node
  spacing differs — sag shrinks with the baseline, which is how `vc_flatten` looked effective when it is not.
- **`patch_agreement.py`**, the precondition for stage 2: distinct patches per 24-voxel cell (half the 449 µm wrap
  spacing), an upper bound on same-sheet agreement. PHerc0826's 66 patches reach six-fold agreement over 1.15 cm²;
  the maximum anywhere is 7. Seeds 320 voxels apart across a 48-voxel wrap spacing can be six wraps apart.
- **`sheet_seeds.py`** (G-GP part 4): seeds sampled from ONE patch's own valid grid points, spread by a farthest-point
  pass in GRID INDEX rather than in 3D, so every trace starts on the same physical sheet by construction. Traces go to
  `patches/<scroll>_dense/` and are read by the same unchanged reader.
- **Tools now built** beyond the original seven: `vc_tifxyz_selfcross`, `vc_tifxyz_winding`,
  `vc_grow_seg_from_segments` (`scripts/build_vc3d_extra.sh`, which removes its build tree on exit; disk is the binding
  constraint on this box). `vc_grow_seg_from_segments` opens its volume with the LOCAL-only `VcDataset`, so it needs the
  prediction store materialised on disk — chunks are 192³ and ~449 KB, about 600 MB for a 2112³ box.

## Retired (recorded; do not retry as is)
- Pilot pseudo-label loop seeded by the public map (79k-parameter 3D CNN on 17×64×64 crops, labels from one half,
  judged on the other): 0.661 then 0.643 vs 0.784; converged on fibre texture and hole rims.
- Tracing without normal grids: 100× faster but cuts across windings (mean |n_z| 0.75–0.83): void.
- **Five pre-registered geometry measures, all failed, none retuned** (RULES has each with its numbers):
  R-NORMAL (agreement with the published sheet normal), R-NORMMAG (the normal's length), R-INTERIOR (phase field vs
  surface prediction), R-PHASE (winding-phase spread along a trace), R-WRAP (radial spread in wrap spacings).
  The last three failed for one physical reason: **a scroll sheet is a spiral**, so a surface that genuinely holds to
  a sheet sweeps phase and spans many radii — MORE than one that cuts across and stays put. No scalar spread
  statistic separates a good surface from a bad one here, because the good surface is the one that moves.
- 20-generation interior traces: 0.49 cm², below QC's own 0.5 cm² area bar, so they can never reach the reader.
- **40-generation interior traces (R-SMALL): FAILED** at 20.0 % readable against a declared 30 % bar over 15 outcomes
  (baseline 5.6 %). Not adopted; 60 generations remains the budget. The budget also does not explain mesh roughness
  (40 gen median p90 sag 31.7 µm vs 60 gen 33.7 µm), so the idea is refuted twice over.
- **`vc_flatten` before rendering**: INEFFECTIVE at a matched baseline (3D sag 64.6 → 84.6 µm while UV anisotropy
  improves). It regularises the parameterisation and adds geometric noise; sag is what decides whether the render walks
  off the sheet.
- **Breadth-first coverage as the primary use of the trace slot**: two days, 141 reads, 0 candidates, and a patch
  library too sparse to support the team's own second stage. Superseded by concentrated seeding (G-GP part 4).

## Promotions on record
- 2026-09-12 (previous session): `--tta-mirror` promoted (w028 judge 0.784 -> 0.823; w040 regression 0.990; rule
  levels unchanged). Superseded for SCREENING on 2026-09-18 (plain call, same levels, a quarter of the cost); TTA
  remains the recipe for candidates.
- 2026-09-18: **seed43 admitted as a confirmatory reader** (G-B-43). It had been retired as a screening checkpoint on
  the w028 judge (0.781 vs 0.784) and is used exactly as that note anticipated — as an agreement filter, never as a
  flagger.
- 2026-09-18: seeds density gate; QC in-mask area arm; plain screening; the R-FLIP tripwire.

## Scroll-specific coverage decisions
- PHerc0826 (2026-09-17): middle and inner radius seeds skipped after 13/13 rendered middle+inner patches were VOID
  under R-CREST. Revisited 2026-09-18 by R-RADIAL and R-SMALL: the interior is where the text is, and the budget —
  not the seed radius — is the thing now under test.
- PHerc0826 (2026-09-18): tracer paused for breadth at 34 reads and 126.9 cm² with no candidate; read loop paused so
  the declared experiment queues get the inference lock.
- PHerc1203 / PHerc1447 (2026-09-18): the published normal field splits them — PHerc1203's surfaces agree with it at
  |cos θ| 0.9967 and still render flat, while 27 of PHerc1447's 31 fall below 0.90 and genuinely cross-cut. R-CREST
  looks right on PHerc1447; PHerc1203 is what R-CREST-POWER decides.

## Decisions per scroll from CONTROL-2UM
- (pending; the 2.4 µm reader is validated in both depth orders, B-2UM; it is blocked only on a sheet-following trace
  of the PHerc0846A rescan — 0 of 14 so far. See LEDGER.md.)
