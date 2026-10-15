
## Round 3: REAL-TRIB-2 (orchestrator, 2026-09-26 00:39Z)

Pre-registered in `real_trib2/PREREG.md` (commit 817a237, sha256 40d63bee...) before any analysis.
Coordinates, geometry, CT renders and numbers only. No ink map, tile PNG or image was opened.

### (i) Preread: no rounding, no short-circuit (`real_trib2/retrib1_unrounded.json`)

- Thresholds can now be passed in (`thresholds=`; the defaults are unchanged).
- Every check evaluates all of its conditions and lists every failing reason (`details.reasons`).
  Nothing is rounded.
- Tests: 43 preread tests, including new ones for multi-reason reporting, injected thresholds and 1e-12
  threshold edges.

The pre-registered rule, re-applied **unrounded** to the REAL-TRIB-1 rows:
- MIN_REF_NCC = 0.999777163, MIRROR 0.181402, DEPTH 0.284129,
  SLICE 0.042175.
- Clean: 12/12. The margin is thin: the minimum clean NCC is 0.999944 against the
  threshold 0.999777.
- Every fault is caught by its own check. Offset, swap, mirror and voxel faults each fire their own check
  only (12/12).
- **Off-by-one faults (NCC 0.74-0.85) also read "unverifiable"**, so all four data checks fire and the
  fault is no longer attributed to the slice check (0/12 by the slice check alone).

### (ii) Empirical-null dry run on clean PHerc0139: **INSUFFICIENT** (`real_trib2/null_dryrun/`)

- Mock R (first window meeting the pre-registered rule): 20260215000000-w024_2026021572 y3204 x1068.
  - It is >= 95 % valid and clear of base training (w028 included) + 64 px.
  - It is canvas-disjoint from 42 used, DEV and D1 windows, and >= 192 vox from the
    5 DEV windows.
- Pitch measured from m7 along the normals: **20.875 vox** (p10 11.38,
  p90 33.62).
  - 721 of 841 vertices used; 730
    had their own m7 sheet confirmed.
  - m7 was fetched only in the chunks the normal lines touch.
  - The two off-sheet meshes (+-10.44 vox) were written outside the repo, because
    the pre-commit hook rejects TIFF tags. Their sha256 are listed.
- Band tiles: **0 of the 89 candidates**. 77 were
  outside the +-10 % band (R radius 674 vox, band +-67.4)
  and 12 were within 192 vox of R.
  - Result: 4 tiles, not >= 40 → INSUFFICIENT, per the pre-registered criterion.
- Diagnostics (`segment_radii.json`):
  - The geometry-only centre curve fits poorly: the median normal-line miss distance is
    326 vox.
  - Segment radii are monotone w030 -> w059, but each segment spans about 500 vox of radius (p10-p90).
  - So either the scroll cross-section is far from circular, or the centre estimate is off. In either
    case a single "radius band" is poorly defined here.
- **Needs a declaration (not adjusted post hoc):** the band definition, the centre source (for example the
  official 2.399 um umbilicus mapped to the 9.362 um volume), or R placement, before a null set can be
  built for R candidates in this region.

### (iii) Gate calibration on the 2.399 um protocol (`real_trib2/gate_2p4um.json`)

- Volume: PHerc0139 20260102150214, 2.399 um from metadata.json.
- 12 windows on w040/w044, each with its organizer 2.399 um mesh.
- The window-selection code was replaced by an exact fast equivalent. It reproduces REAL-TRIB-1's 12 windows
  identically (`pick_windows_equivalence.json`).
- The official renderer was used, byte-identical to the D3 binary. Slices [1:32] of the -n 33 render equal
  the -n 31 render on all 12 windows.

| Threshold set | (a) clean pass | (b) faults caught by own check | (c) every margin >= 3 x threshold | min ratio |
|---|---|---|---|---|
| current (0.5/0.05/0.02/0.02) | 12/12 | 60/60, each by its own check only | **no** | 1.147 (slice) |
| REAL-TRIB-1 proposed (0.5/0.181/0.284/0.042) | **11/12** (one clean false alarm) | 60/60 | **no** | 0.546 |

- Clean margins at 2.4 um (n = 12):
  - slice 0.0229-0.0682 (median 0.0585);
  - mirror 0.544-0.860;
  - depth 0.467-1.002;
  - reference NCC >= 0.99991.
- **Answer: no, not every clean margin is >= 3 x the thresholds on this protocol.** The slice-lag margin
  scales with voxel size: at 2.4 um, adjacent slices are about 4 x closer physically and far more alike
  (the 9.362 um margins were 0.126-0.217).
- The 9 um-derived slice threshold (0.042) does not transfer. Slice thresholds must be declared per protocol.
  On this evidence even 0.02 leaves only a 1.15 x margin at 2.4 um.
- A per-protocol threshold would be clean p1 / 3 = 0.0076 here. Proposed, not declared.
  Alternatively, the slice check at 2.4 um could compare lags of +-4 slices (about one 9 um slice).
  That is a design change for the orchestrator.

### (iv) Paris 4 P4-B tile checks: **PASS** (`real_trib2/p4_tiles.json`)

Numbers only, from the p4-tiles-a/b manifests (inputs copied with sha256 to `real_trib2/p4_inputs/`). No PNG
or prediction pixel was opened. The voxel size is taken from the sha256-pinned Paris 4 metadata.json
(0.0024 mm).

- **Real grids:**
  - a (w010-027): px_per_mm 417.131, T 8343.
  - b (w028-037): px_per_mm 415.039, T 8301.
  - All grid checks pass: T rule; px_per_mm recomputed from the median edge; within 3 % of nominal;
    voxel from metadata; canvas = grid x 20; tile-grid dimensions; display 53.4 px/mm.
  - b: all 171 listed tiles pass every tile check (origin (0, 0), extent, clip, valid_fraction =
    valid_px / T^2, grid-matrix agreement, eligibility >= 0.5, chunks, file name). The counts match the
    grid (171 / 198).
  - a: no per-tile list exists yet on its branch, so only its grid could be checked.
  - The two builders compute the same px_per_mm definition with differently pooled medians. Values are
    per segment and consistent.
- **Planted manifest faults** (in copies of b's real manifest): wrong T, wrong px_per_mm (with T made
  consistent), wrong voxel, 8 px origin offset, wrong valid fraction, swapped r/c, extra PNG chunk.
  Each was caught **200/200**.
- **Planted pixel faults on synthetic arrays** (`tiles.verify_tile`: bit-exact recomputation of the
  prescribed display tile, then `diagnose`):
  - 8 px offset, 90-degree rotation, wrong px_per_mm (T off by 1-5 %), left-right mirror, and N0 tile
    missing its keyed 90-degree rotation: each caught **200/200**.
  - Clean false alarms: **0/200**.
  - The advisory diagnosis names the fault correctly in 100 % of cases, except wrong px_per_mm
    (179/200 named as a tile-size error; the rest as a rotation, mirror or shift). The catch itself is 100 %.

### Corrections in this round

- **w028** was missing from my base-training list (the devloop registry R3 adds it from the ink_9um label
  list). Adding it did not change the example manifest. Clearance part B is being re-run with w028
  (see below).
- **Example manifest vs DEV windows:** 4 of its 6 earlier windows overlapped DEV windows (w024 y256 x1792;
  w053 y256 x4864 and y3840 x4096). It has been regenerated disjoint from all used, DEV and D1 windows
  (+64 px halo): 3 windows.
- Off-sheet tifxyz meshes are kept outside the repo, because the pre-commit hook rejects the TIFF Software
  tag. Their sha256 are listed.
- The container killed background jobs and dockerd during long idle periods (twice). Every job was restarted
  from the cached renders and re-logged.

### What the orchestrator needs to declare next (REAL-TRIB-2)

1. **Per-protocol preread thresholds.** The 9 um-derived SLICE_MARGIN 0.042 gives a clean false alarm at
   2.4 um. At 2.4 um even 0.02 leaves only a 1.15 x margin. Options:
   - declare 2.4 um thresholds from the 2.4 um clean p1 / 3 (SLICE about 0.0076);
   - or change the 2.4 um slice check to compare lags of +-4 slices.
2. **MIN_REF_NCC.** The unrounded pre-registered rule (0.99978) keeps 12/12 clean at both protocols
   (minimum clean 0.999944 at 9 um and 0.999914 at 2.4 um). But off-by-one faults then also read
   "unverifiable" (attribution lost). 0.5 keeps clean attribution. Choose.
3. **Empirical null:** declare the radius-band definition or centre source (for example the official
   2.399 um umbilicus mapped to 9.362 um), or R placement. The dry run found 0 same-band tiles for a
   w024 R.
4. **Paris 4:** tiles-a should publish its per-tile list, so its tiles get the same checks as tiles-b.
   `tiles.verify_tile` can run where the prediction canvas is held (the builders' containers) before
   renaming to uuid.
