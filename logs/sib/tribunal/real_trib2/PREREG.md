Provenance: Project HERCULES | owner the owner | [id removed]

# REAL-TRIB-2 pre-registration (fixed before any REAL-TRIB-2 analysis is run)

Task: orchestrator message of 2026-09-26 00:39Z. Everything below is coordinates, geometry, CT
renders and numbers only. No ink map pixel, no tile PNG and no image is opened, viewed or produced.

Materials allowed: official organizer data only (s3://vesuvius-challenge-open-data), non-eligible
PHerc0139, and the Paris 4 tile manifests (JSON and numbers only) from the p4-tiles-a/b branches. No
PHerc0841 and no eligible scroll.

Base-training trace list (correction noticed while preparing this): w028, w029, w030, w035, w039, w040,
w041, w043, w044, w045, plus the re-trace w046. This follows the devloop registry R3, which added w028
from the official ink_9um label list. The round-2 clearance re-check (part B) and the example manifest
used this list without w028. Both are re-run with w028, and any change is reported.

## (i) Preread without rounding or short-circuit

1. Thresholds become injectable (`thresholds=` argument; defaults unchanged: 0.5 / 0.05 / 0.02 / 0.02 /
   1 px). Every check evaluates ALL of its conditions and reports every failing reason: unverifiable,
   transform, lag or shift, and margin. None returns before the others are evaluated. No threshold or
   statistic is rounded anywhere in the gate or the analysis.
2. Re-analysis of the REAL-TRIB-1 rows (unchanged raw file): the pre-registered rule is applied
   UNROUNDED, MIN_REF_NCC = p1 - 3 (1 - p1), with margins = p1 / 3. Reported: clean pass count, each
   fault's catch count by its own check, and which other checks fire. Under the unrounded rule,
   off-by-one faults may also become "unverifiable". That is reported, not hidden.

## (ii) Empirical-null dry run (coordinates only)

- Volume: PHerc0139 20250728140407 (9.362 um, from metadata.json).
- m7: the official `20250728140407-surface-20260413222639-surface-m7-L0-th0.2.zarr` (surface
  prediction, not ink), read only along R's mesh normals.
- Centre curve: no official umbilicus exists for this volume. The centre is instead estimated from
  mesh geometry only. In z-bands of 200 vox, take the least-squares intersection point of the xy
  vertex-normal lines of every 0139 9.362 um official mesh, then smooth with a 3-band running median.
  The method is unit-tested on a synthetic cylinder before use.
- Mock R: the first 2136 x 2136 px window, in scan order (stride 1068), on clean segment w024, then w053,
  then w047, that meets all of:
  - >= 95 % mesh-valid;
  - no 4-vox densified vertex within 4.83 vox of any base-training trace, within window + 64 px;
  - canvas-disjoint, with a 64 px halo, from every used or sealed 0139 window (the devloop registry
    `used_windows_0139`, the registry's DEV windows and DEV blanks, and the D1 blanks and canary in
    logs/d1/d1_build_prep.json);
  - >= 192 vox (3-D, point-to-surface) from every DEV window.
- Null set: `hercules.tribunal.empnull.build_null_set` with its declared defaults: band 10 %,
  separations 192 / 144 / 64 vox, n_total >= 40, n_band >= 20.
- Band candidates: 2136 px tiles, stride 1068, on every 0139 official 9.362 um mesh except the
  base-training traces. Candidate tiles must also satisfy the used / sealed / DEV disjointness above.
- Seed 20260926. Output: coordinates and pitch statistics only.
- Pass criterion for the dry run: status OK (>= 40 tiles, >= 20 band tiles, pitch measured on
  >= 50 vertices).

## (iii) Gate calibration on the 2.399 um protocol

- Volume: PHerc0139 20260102150214 (2.399 um from metadata.json). Organizer meshes
  `-on-20260102150214-2.399um.tifxyz` of w040 and w044.
- 12 windows of 384 px, 6 per segment, chosen by the same `pick_windows` rule as REAL-TRIB-1. Official
  vc_render_tifxyz (sha256 473369f9...). CT only.
- Faults as in REAL-TRIB-1: 8 px offset, depth swap, mirror, off-by-one (-n 33), and wrong voxel. The
  wrong voxel is 9.362 (the other 0139 protocol) or the 9.362 um volume's metadata.json.
- Criteria, all evaluated under both the current thresholds (0.5 / 0.05 / 0.02 / 0.02) and the
  REAL-TRIB-1 proposed thresholds (0.5 / 0.181 / 0.284 / 0.042):
  - (a) every clean record passes;
  - (b) every fault is caught by its own check;
  - (c) every clean margin >= 3 x its threshold (mirror, depth, slice), clean |shift| = 0, and clean
    best NCC >= MIN_REF_NCC.
- The answer to "is every clean margin >= 3 x the thresholds" is given per threshold set, with the
  smallest ratio found.

## (iv) Paris 4 tile checks (P4-B, DECL-P4-2 item 2)

Manifest checks, on numbers only (grid.json, manifest.json, tiles.jsonl from both branches):
1. T == round(20 x px_per_mm) exactly.
2. px_per_mm == canvas px per grid step / (median edge vox x voxel_mm), recomputed from the recorded
   fields where present. The ratio to the nominal 1 / voxel_mm must lie in [0.97, 1.03].
3. The voxel size equals the metadata value 0.0024 mm (declared source recorded).
4. Canvas == grid_shape x 20. The tile grid dims == ceil(canvas / T).
5. Every tile's canvas_rows / cols == [r T, (r+1) T) from origin (0, 0).
6. in_canvas equals the canvas-clipped range.
7. valid_fraction == valid_px / T^2 (to 1e-12). It equals valid_fraction_check, and it equals the grid
   matrix entry (to its 6-decimal rounding).
8. Read-eligibility == (valid_fraction >= 0.5).
9. Tile count and eligible count match the grid.
10. Chunks are exactly IHDR/IDAT/IEND. Display side 1068, and display px/mm == 1068 / 20.
11. The two segments' px_per_mm formulas are compared and reported.

Pixel checks, tested on SYNTHETIC arrays only (the real tiles are never opened):
- `verify_tile(tile_u8, canvas, valid, r, c, T, expected_rotation)` recomputes the expected display tile
  from the source canvas. It then registers the delivered tile against it over the dihedral group
  and integer shifts, with a scale check.
- Faults, 200 random synthetic trials each: 8 px offset, 90-degree rotation (when 0 is expected), wrong
  px_per_mm (T off by 1-5 %), left-right mirror, and a missing rotation on an N0 tile (expected 90,
  delivered 0). The manifest checks get their own numeric faults: wrong T, wrong origin, and wrong
  valid fraction.
- Bars: 100 % caught by the intended check, and 0 false alarms on 200 clean trials.

## Output

`logs/sib/tribunal/real_trib2/`: `retrib1_unrounded.json`, `null_dryrun.json`, `gate_2p4um.json`,
`p4_tiles.json`, `REPORT.md` section. Every run is logged in runs.jsonl.
