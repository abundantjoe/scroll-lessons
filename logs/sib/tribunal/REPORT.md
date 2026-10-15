Provenance: Project HERCULES | owner the owner | [id removed]


STATUS: DONE for rounds 1-3 (REAL-TRIB-2 complete, 2026-09-26). Clearance part B with w028 is complete: no change. w028 lies >= 17.3 vox from w024, >= 150 vox from w047/w053, and >= 173 vox from both D1 blanks, with 0 points within 3 vox. The previous part B is kept under part_b_superseded.

REAL-TRIB-2 verdicts:
- (i) done.
- (ii) null dry run INSUFFICIENT.
- (iii) 2.4 um: clean 12/12 and faults 60/60, but margins are NOT >= 3x (min 1.15x), and the 9 um-derived slice threshold gives a clean false alarm.
- (iv) Paris 4 tile checks PASS.

> Round 1 (below the round-2 section) was written when the package lived at
> `tools/sib/tribunal/tribunal/` and the tests were `tests/sib_tribunal_*.py`. Per the orchestrator's
> decision of 19:04Z, both have moved to `src/hercules/tribunal/` and `tests/test_tribunal_*.py`.
> The code is unchanged apart from `manifest.py` and the additions to `validity.py`/`wiring.py` listed
> below. The runner is now invoked as `python -m hercules.tribunal.runner`.

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
  list). Adding it did not change the example manifest or any clearance result: 0 points of any bank segment
  or blank lie within 3 vox of w028 (nearest w024 at 17.3 vox; `recheck_add_base.py`).
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

---

## Round 2: orchestrator decisions of 2026-09-25 19:04Z

### Summary

| Decision | Status | Output |
|---|---|---|
| 1 re-trace rule (vertex OR surface) | kept in code | `src/hercules/tribunal/preread.py` |
| 2 batch-validity defaults | kept in code | `src/hercules/tribunal/validity.py` |
| 3 REAL-TRIB-1 | **PASS**, thresholds PROPOSED, not declared | `real_trib1.json`, `real_trib1_raw.json` |
| 4 HARNESS-HOOK patch | done, not for merge before D3-VERDICT | `proposals/HARNESS-HOOK.md` |
| 5 mirror answer field | proposal only; briefs and schema not edited | `proposals/MIRROR-ADDENDUM.md` |
| 6 manifest-driven builders | done; example from clean 0139 | `src/hercules/tribunal/manifest.py`, `controls_manifest_example.json` |
| 7 clearance re-check | done; nothing below a margin by more than 0.001 vox | `recheck_clearances.json` |

Tests on this branch: plain `PYTHONPATH=src pytest -q` gives **701 passed, 0 skipped**
(`out/pytest_all_v4.log`: the repo's 585 + the 6 renderer-dependent canvas tests + 110 tribunal tests).
The Docker daemon stopped once while the session idled, so those 6 tests skipped in `pytest_all_v3`.
It was restarted with the same setup script (`setup_render_3`). The official renderer was rebuilt with `tools/sib/tribunal/setup_render.sh`, a copy of
setup_env.sh steps 1-3 with the proxy port taken from $HTTPS_PROXY instead of the hard-coded 46883.
Its `vc_render_tifxyz` has sha256 473369f9...f9e2c, **byte-identical** to the binary recorded for D3.
The 6 canvas tests that need it now run and pass.

### REAL-TRIB-1

Material: official `vc_render_tifxyz` CT renders only, of non-eligible PHerc0139 volume 20250728140407.
Voxel size 9.362 um was read from its metadata.json (sha256 95917633ca11...).
There were 12 windows of 384 x 384 px, 6 on each of base-training segments w040 and w044, spread
over each segment by code. No ink map, no inference, no image file, no read, and nothing was viewed.

Planted faults, caught by their own check, with no other check firing:

| Fault | offset8 | swap_depth | mirror | off_by_one | wrong_voxel |
|---|---|---|---|---|---|
| Caught | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |

- **offset8:** a real re-render 8 px off, cycling through all 8 directions.
- **mirror:** alternately left-right and up-down.
- **off_by_one:** real -n 33 renders, taking slices [0:31] and [2:33].
- **wrong_voxel:** the value 9.366, or PHerc0841's metadata.json.
- Slices [1:32] of the -n 33 render equal the -n 31 render exactly on all 12 windows.

Clean records passed 12/12. Clean margin distributions, n = 12:

| Metric | Min | p1 | Median | Current threshold |
|---|---|---|---|---|
| Reference vs official NCC | 0.99994 | 0.99994 | 0.99997 | 0.5 |
| Mirror margin | 0.540 | 0.544 | 0.732 | 0.05 |
| Depth margin | 0.849 | 0.852 | 0.966 | 0.02 |
| Slice margin | 0.126 | 0.127 | 0.165 | 0.02 |
| max abs(shift) | 0 px | | | 1 px |

The independent reference render reproduces the official renderer almost exactly on real CT.

**Proposed thresholds (PROPOSED, not declared):**
- MIN_REF_NCC stays at 0.5.
- MIRROR_MARGIN 0.181, DEPTH_MARGIN 0.284, SLICE_MARGIN 0.042.
- OFFSET_TOL_PX stays at 1.

Under these, 12/12 clean records pass and 60/60 faults are still caught, each only by its own check.

**Defect in my pre-registered rule, reported and not used.** The rule MIN_REF_NCC = p1 - 3 (1 - p1)
gives 0.9998 here, which rounds to **1.000** and would fail every clean record. The proposed
MIN_REF_NCC of 0.5 is therefore POST-HOC and labelled so in the JSON. It must stay below the surface
NCC that genuine off-by-one faults produce (0.74-0.85).
Above that, those faults would read "unverifiable" instead of being attributed to the slice check.
The margins follow the pre-registered p1 / 3 rule unchanged.

**Re-trace on official 0139 meshes** (windows of about 19 x 19 grid cells at the official 20-vox step):
- Where official re-trace w023 overlaps w024, or w052 overlaps w053, the check caught **10/10**.
  The surface form caught 10/10; the literal nearest-vertex form alone caught **0/10**. This confirms
  CORR-RETRACE-RULE on real meshes.
- Negatives on the neighbouring winding, windows whose every vertex is 5.5-15.7 vox from the re-trace,
  gave **0/10 false alarms**.
- The first negative criterion (> 50 vox everywhere) produced 0 negatives: wherever it does not
  overlap, the re-trace lies one winding away. A second run carried a reporting bug (a stale distance
  field). Both are kept under `retrace_superseded` (3 entries; the buggy run is recorded twice).

### Clearance re-check (`recheck_clearances.json`)

Mesh geometry only, from official tifxyz; sha256 of every file in `meshes_fetched.json`.

**D3-FEAS / DECL-D3-A2.**
- The recorded distances were computed point-to-point on dense canvas points (1 px = 1 vox), not on
  20-vox vertices. The re-check reproduces the recorded minimum retained distance
  (w00 128.00015 vox). At that density, point minus surface distance is <= 0.0025 vox.
- I checked every PRIMARY-grid tile position: 128 px, stride 64, >= 90 % mesh-valid, outside its own
  J window. That is 927 tiles at >= 128 vox,
  a superset of the 306 PRIMARY and 288 pool tiles. Their text status was not recomputed, because
  that needs the 0841 reference ink map.
- Result: **0 tiles change status at 128 vox or at 144 vox.**
- 4 retained pixels are 0.0002-0.0008 vox below 128 by the surface form. This is below the declared
  margin but negligible, and it affects no tile.

**RCBANK-1.**
- w047 is SAME as base-training w045 under the corrected rule; the vertex form alone says NOT SAME.
  The area within 2 vox is 0.1185 cm^2 against w045 and 0.1219 cm^2 against w046. This matches the
  recorded, already-excluded ~0.12 cm^2 strip.
- w046 misses SAME only on the ratio test (c0 4964 < 2 x 2490).
- w024: nearest vertex 29.7 vox from any base-training trace.
- w053: 0.0011 cm^2 within 2 vox of w039, not SAME.

**SEAL-J-D1 blanks.**
- Their distance to J is undefined: they are on PHerc0139 w053, and J is on PHerc0841.
- Checked instead against 0139 base training. blank_w053_y256_x1536 is clean (49.9 vox).
  blank_w053_y256_x7168 contains a **0.0011 cm^2 contact sliver** with base-training w039
  (78 points within 2 vox, min 0.048 vox, about 0.03 % of the blank). It is not SAME.
- No blank-vs-training margin was declared. This matters only if the w053 blob-f180 bar is meant to be
  base-clean.

### Manifest-driven controls and the mirror addendum

- `hercules.tribunal.manifest`: `validate_manifest` and `build_from_manifest`.
  - Positives come from clean PHerc0139 only; PHerc0841 and the 23 eligible scrolls are refused for
    every source.
  - The loader's source sha256 must match; missing sigma, ceiling or hash values are refused.
- `controls_manifest_example.json` is built by code from 0139 geometry only
  (`tools/sib/tribunal/make_example_manifest.py`).
  - It holds 6 windows of 2 x 2 cm on w024/w053, chosen away from every base-training trace
    (4.83 vox conservative band plus 64 px halo) and away from both D1 blanks.
  - Its sigma, ceilings, voxel and hashes are left null, so the builder refuses it until the
    orchestrator fills them.
  - The READ-CAL/PROBE/D3 window lists are not in this container. **Remove any example window that
    lies in a sealed or used set.**
- `proposals/MIRROR-ADDENDUM.md` holds the addendum sentence, the optional `"mirrored": "Y"|"N"`
  schema field, and a scorer adapter (`validity.mirror_answers_from_panels`, tested).

### Round-2 incidents

- The first renderer build failed: `vc_build.sh` hard-codes proxy port 46883, and this container's
  port differs. I fixed a copy under `tools/sib/tribunal/`; `docker/` is untouched.
- The pre-registered MIN_REF_NCC rule was defective (see above).
- The analysis verdict at first passed vacuously with 0 re-trace cases. It now requires at least one
  positive and one negative.
- In the re-trace study, the stale-variable reporting bug and the 0-negatives criterion are both fixed
  and superseded runs are kept.
- A process waiter matched its own command line. No data was affected.

### Next for the orchestrator (round 2)

1. Declare, amend or reject the proposed thresholds (`real_trib1.json`, `thresholds_proposed`); they are
   not declared.
2. After D3-VERDICT: merge the HARNESS-HOOK patch and hash it, then add certificates to the existing
   job builders.
3. Fill `controls_manifest_example.json`: sigma, ceilings, voxel, hashes, and removal of used windows.
[line withheld: prize-candidate detail under review]
5. Declare the mirror addendum (new METRIC-HASH) before any batch uses mirror canaries.

---

# Round 1
# TRIBUNAL: anti-self-deception controls (sibling task `tribunal`)

Branch `claude/gifted-bell-gavnl5-sib-tribunal`, base 638615a. Code and tests only. Nothing was read,
viewed or rendered from real data: every volume, mesh, map and reader answer below is synthetic.
No seal, key, scorer secret or encrypted file was touched. Machine-readable results:
`logs/sib/tribunal/results.json` (code and test sha256, thresholds, suite results). Every run is in
`logs/sib/tribunal/runs.jsonl`.

## What was built (`tools/sib/tribunal/tribunal/`)

| Module | Role | Reuses |
|---|---|---|
| `preread.py` | Pre-read gate, one content check per planted fault, fail-closed; `preread_gate`, `require_clean` | `pipeline.canvas.emulate_gen` (renderer canvas/normal conventions), `pipeline.window.ncc`, `voxel_size_from_metadata`, `geometry.contamination.same_papyrus`, `tifxyz.densify/read_tifxyz` |
| `faults.py`, `runner.py` | Fault injectors; runner that injects every fault into random worlds and reports the catch rate and clean false alarms | `render_synth.cylinder_grid`, `window.render_command` |
| `synth.py` | Synthetic textured concentric-sheet CT, tifxyz, zarr. The delivered render uses an independent code path (`sample_grid` + `vertex_normals` + `render_along_normals`) | `render_synth`, `tifxyz` |
| `controls.py` | Positive canaries (declared-sigma Gaussian), baits (wrong-order, blank, NULL-arm), mirror canaries (E K R C G B N) | `display.builder` (raw / 1-99 % windows, INTER_AREA, `png_bytes`, 1068 px cap) |
| `validity.py` | Batch-validity scorer and I16 | `scorer.schema`, `scorer.display.DisplayMap/item_namings`, `scorer.matching.match_letters`, `R_PRIMARY` |
| `empnull.py` | Empirical null tile builder (section 8.2) with code-measured local m7 pitch | `tifxyz`, `pipeline.canvas`, `level_mesh.CentreCurve` |
| `wiring.py` | Certificates that bind display-image sha256s to a passed gate; `assert_images_certified` for `harness.jobs.make` | |

How each fault is caught: the delivered stack is registered against an independent reference render
of the DECLARED window, computed from the volume and mesh.

| Planted fault | Caught by | How |
|---|---|---|
| 8 px window offset | `window_offset` | Surface slice, best integer shift within +-12 px must be 0 (tolerance 1 px) |
| Mirrored render | `mirror` | Best dihedral transform must be identity, beating every other transform by >= 0.05 NCC |
| Swapped depth order | `depth_order` | Slice-by-slice NCC matrix: forward must beat reversed by >= 0.02. For ink maps, `map_order` also checks that the map's sha256 is logged for the direction its order implies |
| Off-by-one slice | `slice_index` | Winning lag in the same matrix must be 0, beating +-1..3 by >= 0.02 |
| Re-trace by a training segment | `retrace` | KD-tree on 5 x 5 densified meshes; SAME if >= 1000 points within 2 vox and c[0,1) >= 2 c[2,3), vertex OR surface distance (see finding 1) |
| Wrong voxel size | `voxel_size` | Every use (record, `--voxel-size`, display px/mm, stack attributes) equals the sha256-pinned `<volume>/metadata.json` value |

Fail-closed behaviour is tested: when the reference and delivered stacks do not correlate, or two
hypotheses tie, the check fails. It does so for a depth-invariant volume and for a stack from a
foreign volume. A missing training list fails. A hash or shape mismatch fails. A failed gate
cannot be certified.

## Measured results

Commands, run from the repository root:

```
tools/sib/tribunal/logrun.sh faultsuite_v1 env PYTHONPATH=src:tools/sib/tribunal OMP_NUM_THREADS=1 /opt/hv/bin/python -m tribunal.runner --worlds 40 --scale-trials 200 --out logs/sib/tribunal/faultsuite.json --rows logs/sib/tribunal/faultsuite_rows.jsonl
tools/sib/tribunal/logrun.sh faultsuite_stress_t2 ... --worlds 40 --scale-trials 50 --seed 31000 --texture-sigma 2.0 --noise-max 12 --out logs/sib/tribunal/faultsuite_stress_t2.json
tools/sib/tribunal/logrun.sh faultsuite_stress_t3 ... --worlds 40 --scale-trials 50 --seed 32000 --texture-sigma 3.0 --noise-max 12 --out logs/sib/tribunal/faultsuite_stress_t3.json
tools/sib/tribunal/logrun.sh pytest_tribunal env PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_tribunal_*.py
tools/sib/tribunal/logrun.sh pytest_all env PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/ ...   (repo baseline)
```

Planted-fault catch rate, where every faulted record carries consistent hashes, so only the
content check can catch it:

| Suite | offset8 | swap_depth | mirror | off_by_one | retrace | wrong_voxel | Clean false alarms | Cross-firing |
|---|---|---|---|---|---|---|---|---|
| v1 (texture 1 vox, noise <= 6) | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 0/40 | none |
| stress t2 (texture 2 vox, noise <= 12) | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 0/40 | none |
| stress t3 (texture 3 vox, noise <= 12) | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 40/40 | 0/40 | none |

That is **720/720 faults caught by their own check (100 %) and 0/120 clean false alarms**. Each
fault tripped only its own check.

The worlds varied the sheet, voxel size (9.366 / 7.91 / 2.403 / 8.64 um), n = 21 or 31 slices,
offset direction (all 8), flip axis (left-right / up-down), slice shift (+-1), and the wrong-voxel
variant: 9 wrong values including a 1e-4 relative error, plus metadata taken from another volume.

Smallest clean margins against their thresholds:

| Suite | Slice margin (thr 0.02) | Depth margin (thr 0.02) | Mirror margin (thr 0.05) | Min reference NCC (thr 0.5) |
|---|---|---|---|---|
| v1 | 0.114 | 0.773 | 0.828 | 0.991 |
| t2 | 0.085 | 0.603 | 0.716 | 0.972 |
| t3 | 0.076 | 0.597 | 0.607 | 0.973 |

Re-trace at the official 20-vox grid step. Radii 300-3000 vox, random phase, angle +-10 deg,
radial noise 0-0.5 vox, overlap 30-100 %:

| Suite | Re-traces caught | By literal vertex form alone | By surface form alone | Neighbour false alarms (gaps 3-20 vox) | Far same-sheet false alarms |
|---|---|---|---|---|---|
| v1 | 200/200 | 4/200 | 200/200 | 0/200 | 0/200 |
| t2 | 50/50 | 0/50 | 50/50 | 0/50 | 0/50 |
| t3 | 50/50 | 1/50 | 50/50 | 0/50 | 0/50 |

Unit tests: **99 passed** in `tests/sib_tribunal_{preread,controls,validity,empnull,runner,wiring}.py`.
The repository baseline is unchanged: 585 passed, 6 skipped.

- Preread (40 tests): one per fault through the full on-disk gate (all 8 offset directions, both
  flips, both slice shifts, 4 wrong voxel values, foreign metadata, a wrong value in the command
  only or the display only), clean with noise sd 8, fail-closed cases, surface distance exact on a
  plane, map-order provenance, and reference vs delivered NCC > 0.99 on every slice.
- Controls (20 tests): sigma 0 is the identity; the impulse second moment equals the declared
  sigma within 2 %; the blur round-trips through `sigma_eq` exactly; the 1-99 % window is linear
  within 0.5 grey level; INTER_AREA equals the 2x2 block mean; pixel shuffle keeps the histogram
  exactly; phase scramble keeps the amplitude spectrum (relative error < 1e-9); mirror images are
  exact left-right flips; all 7 glyphs are asymmetric; glyph height is within 5 % of declared;
  PNGs hold only IHDR/IDAT/IEND, with no cf_scan finding and UUID names.
- Validity (25 tests): recall and rows bars, including the exact boundaries; letters on the wrong
  side or of the wrong identity do not count; bait at exactly 0.5 per 4 cm^2 is valid and above it
  is void; one firm bait naming voids; mirror 10/12 is valid and 9/12 or a missing answer voids;
  schema-invalid readers are excluded; a batch without controls is void; 6 I16 sequences.
- Empnull (9 tests): pitch 12 / 18 vox within 0.5; nearest-neighbour pitch 9 in a 9/15 gap
  layout; downsampled m7 (x2) within 1.0; a mesh off the m7 sheet gives INSUFFICIENT; off-sheet
  meshes lie at R +- pitch/2 within 0.05 vox with correct outward/inward labels; every band
  selection rule holds and is seed-deterministic; the full null set has 40 tiles (2 + 2 + 36
  band); too few candidates gives INSUFFICIENT.

## Findings the orchestrator needs

1. **The literal form of the declared re-trace rule misses re-traces at the real grid step.**
   Official meshes use a 20-vox step, so 5 x 5 densification leaves 4-vox vertex spacing. The
   nearest-vertex distance of a true re-trace then lands mostly in [1,3) vox. An exact re-trace
   offset by half a dense cell gives [0, 0, 20736], which the rule calls NOT SAME.
   The literal form caught 5 of 300 re-traces. The point-to-surface form of the same bins caught
   300 of 300, with no false alarm on sheets 3-20 vox away.
   The gate uses vertex OR surface (fail closed). The same weakness would affect any FL-09 / SG 8
   certificate or bank exclusion computed with the literal form on 20-vox meshes. RCBANK-1 used a
   normal-distance variant instead, so it is not directly affected, but that is worth checking.
2. The DECL-EMPNULL batch-validity wording leaves 4 definitions open. The chosen defaults are in
   `proposals/DECL-TRIBUNAL-1.md` item 4:
   - rows found is absolute;
   - the bait rate is a mean over readers;
   - mirror answers need a new brief field;
   - I16 halts on the running fraction, so a void first batch halts the run.
3. Test discovery: `tests/sib_tribunal_*.py` is not collected by a plain `pytest -q`, because the
   default pattern is `test_*.py`. The files must be named explicitly.
4. Pre-read thresholds are synthetic-calibrated. Real 9 um CT has not been tested.

## Failures and incidents (all resolved; none changed a threshold)

- The first runner pass reported clean false alarms, 2 of 3 from `retrace`. The cause was my
  synthetic decoy, not the check: on the radius-42 sheet the window spans 213 deg of arc, so the
  "opposite side" decoy really overlapped the window's papyrus. I moved the decoy into the arc
  gap; the check was unchanged.
- Two validity test expectations were wrong. A kind+1 identity shift landed on the neighbouring
  seal letter's kind 180 px away, which is a correct match within R = 250. A bait count of
  (3,0,0) is exactly 0.5 per 4 cm^2, which is not > 0.5. I fixed the tests; the scorer was
  unchanged.
- An empnull test world was too cramped: stacked in-band segments sat less than 64 vox apart.
  The builder correctly returned INSUFFICIENT. I enlarged the test world; the builder was
  unchanged.
- The first combined pytest invocation did not collect the `sib_` files (finding 3), so they were
  re-run separately and logged.
- This fresh container had no `/opt/hv`. I rebuilt it exactly as `docker/env/setup_env.sh` step 4
  does. Docker, villa and checkpoints were not needed and not installed.

## What the orchestrator needs to declare or do next

1. Declare, amend or reject `proposals/DECL-TRIBUNAL-1.md`: thresholds, the re-trace rule form
   (finding 1), batch-validity definitions, null-set parameters (band 10 %, separations
   192 / 144 / 64 vox).
2. Run `proposals/REAL-TRIB-1.md` before the first batch that relies on the gate: clean and
   planted faults on existing official non-eligible renders (0139 C3 crops), CT only, no reads.
   Then fix thresholds from the real clean-margin distribution.
3. Adopt `proposals/HARNESS-HOOK.md`: move the package into `src/hercules/tribunal`, add one call
   in `harness.jobs.make`, and certify images at display build time.
4. Add a "mirrored/normal" answer field to the mirror-canary brief, and choose the canary
   material (fold K tiles, REF ceilings, sigma_eq of the base model) and the bait sources.
5. Re-check any existing KD-tree exclusion or clearance computed with the literal nearest-vertex
   rule on 20-vox meshes (finding 1).
