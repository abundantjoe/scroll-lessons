Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-a: P4-D M2a, 20260623141924-w010-027 tiles (DECL-P4-4)

Builder report. No tile, map or CT pixel was opened, viewed or described. The checks below use numbers, shapes and hashes only. The earlier w010-027 (M1) outputs in `logs/sib/p4-tiles-a/` are unchanged; everything here is in `m2a/`.

## Inputs (official bucket, anonymous; sha256 in downloads.jsonl and manifest.json)
- Prediction: `PHercParis4/segments/20260623141924-w010-027/ink-detection/PHercParis4-20260623141924-1.129um-0.23m-78keV-volume-20260608103018-L1-20260709123958-mrg20736-1um-s1z2-tile256-stride128.tif`
  - 1,177,580,667 B, sha256 `1cc20035dc5dfc53c2d22ea974406cb533c742b9a03cb61fdda1da7270f75852`.
  - uint8, 47750 x 180700, 1024^2 tiles.
- Native mesh: `mesh/20260623141924-on-20260608103018-1.129um.tifxyz` (x/y/z.tif, 345,137,134 B each). Grid 4775 x 18070, meta scale 0.05.
- 2.4 um mesh: `mesh/20260623141924-on-20260411134726-2.4um.tifxyz` (76,504,070 B each). Grid 2248 x 8508.
- Volume files: 20260608103018 metadata.json, .zattrs and transform.json; 20260411134726 metadata.json and transform.json.
- Voxel size: 0.001129 mm, from 20260608103018 metadata.json `samplePixelSize`. All 20 entries are equal, and the value matches the volume name (1.129um).

## Geometry (grid.json)
- Canvas / grid = 10.0 exactly on both axes. This matches an L1 render: grid step 20 native voxels = 10 canvas px.
- Mesh-valid vertices: 82,137,796 of 86,284,250 (95.19 %).
- Median 3-D edge length is 19.966 native voxels over 164.2 M edges (P1-P99: 18.27-21.02). Along cols it is 19.963; along rows, 19.970.
- px_per_mm = 10 / (19.966 x 0.001129) = **443.622**.
  - Per axis: 443.70 (cols) and 443.54 (rows).
  - The nominal L1 value would be 442.87.
- **T = round(20 x 443.622) = 8872 canvas px.** The tile grid is 6 rows x 21 cols = 126 tiles.
- Area cross-check:
  - Valid area summed over all tiles: 417.37 cm^2.
  - Mesh meta area_vx2: 415.11 cm^2; recon lists 415.32 cm^2.
  - The difference is +0.5 %. It comes from the median edge versus the true per-quad area.

## 2.4 um frame (20260411134726)
- Same-UV check, with its rule fixed in the script before the run. 20,000 native vertices (seed 20260926) were mapped through the affine and compared with the 2.4 um tifxyz read bilinearly at the corresponding UV:
  - scaled index: median 7.47 vox, p95 7.68 vox;
  - scaled corner: median 4.11 vox, p95 6.14 vox.
- Rule: median <= 2 and p95 <= 5 vox. It failed, so the grids are treated as not corresponding.
- Used: the published affine 20260608103018 -> 20260411134726 (volume transform.json).
- For scale: the residual is about 10 um (4.1 vox x 2.4 um), about 1 % of the 1.2 mm labelled-adjacency threshold.
- Sanity check: the native mesh bbox passed through the affine lands within about 0.25 mm of the 2.4 um mesh bbox on every corner coordinate.

## Tiles
- 100 of 126 tiles are read-eligible (valid fraction >= 0.5). The 26 ineligible tiles all have valid fraction <= 0.331.
- Eligible tiles cover 387.50 cm^2 of mesh-valid canvas.
- Every eligible tile was checked:
  - PNG 1068 x 1068, 8-bit grey (IHDR); chunks only IHDR/IDAT/IEND.
  - The sha256 recomputed from the file matches the census.
  - Total 25.6 MB; the largest file is 474 KB.
- Consistency: the raw prediction has 0 nonzero pixels outside the mesh-valid mask in every eligible tile.
- tile_points.npz has 400 keys; for each of the 100 tiles:
  - `r_c`: 4096 native points, float32;
  - `r_c__2p4`: the chosen 2.4 um frame, here the affine;
  - `r_c__2p4_affine`;
  - `r_c__grid_rc`: native grid indices.
  - There are no NaNs.
- All vertices per tile were not saved: about 0.8 M vertices per tile, about 1 GB in total, beyond the push limits. Every vertex can be recovered from the official native tifxyz using grid_rows/grid_cols per tile in manifest.json.
- Files:
  - manifest.json: per tile r, c, valid_fraction, file, png_sha256, mean/std/frac_ge_150 of raw valid pixels.
  - tile_census.jsonl: all 126 tiles.
  - tiles/20260623141924-w010-027_r<r>_c<c>.png

## Timings and failures
- Fetch: 52 s for 14 files. The prediction took 23 s.
- Geometry and frame check: 160 s. Tiling: 411 s total, 1.4-5.1 s per tile.
- Failures: no data request was refused.
  - A session permission check blocked shell commands for a time. The work resumed on the owner's instruction.
- Pushes:
  - 83b4407: grid.json and tiles 1-40;
  - d0d1ce7: tiles 41-80;
  - this commit: tiles 81-100, tile_points.npz, manifest.json, census and report.

## Notes for the orchestrator
- The file names carry segment, row and column. DECL-P4-2 item 2 requires uuid4 names and a key held in /srv/scorer, so renaming and keying must happen before any reader sees these files.
- DECL-P4-4 item 1 applies: this model has no public card and its training data are unknown.

## Addendum 2026-09-26 ~17:50Z: DECL-P4-4-A1 scan coverage and grid identity with p4-tiles-b E1
- Status: the M2a outputs were already on this branch at 17:40Z (83b4407, d0d1ce7, e505001). The 17:42Z order was written just before they landed, so the tiling was not rebuilt. Tiles and PNG hashes are unchanged.
- Grid identity with p4-tiles-b `logs/sib/p4-tiles-b/e1/` (manifest sha256 413f6078...a1ec):
  - canvas 47750 x 180700, grid 4775 x 18070, T 8872 and tile grid 6 x 21 are all equal;
  - px_per_mm is 443.622228 here and 443.622186 there;
  - the largest per-tile difference in valid fraction is 4.7e-7.
- A1 item 1 coverage, computed from geometry only (tools/sib/p4-tiles-a/m2a_coverage.py):
  - The volume extent is the 20260608103018 level-0 .zarray shape, zyx (59969, 36006, 32354), sha256 e5483c9c...81cf4.
  - frac_mesh_points_outside_1129_volume is taken over each tile's 4096 saved points.
  - Check against every valid vertex: no eligibility decision changes, and the largest difference is 0.018.
- Result: **60 of the 100 tiles with >= 50 % valid are read-eligible, and 40 are excluded.**
  - Of the 40 excluded tiles, 20 are fully outside and 20 are 0.6-0.8 outside. The eligible maximum is 0.147, and the closest tile is 0.057 from the 0.5 threshold.
  - This equals p4-tiles-b's E1 eligible set exactly: 100 of 100 decisions agree, and the largest difference in outside fraction is 0.013 (different 4096-point subsamples).
- The 60 read-eligible PNGs have 60 unique sha256. The 40 excluded ones have 21 unique sha256, because the fully outside tiles are byte-identical.
- Files:
  - manifest.json now has per tile frac_mesh_points_outside_1129_volume, frac_all_valid_vertices_outside_1129_volume and read_eligible_A1, plus the eligibility_A1 and grid_crosscheck_tiles_b_e1 blocks;
  - coverage_A1.jsonl and coverage_A1_summary.json.
- Sub-siblings: none were created. The whole M2a build took about 10 minutes on one process, so splitting rows would not have saved time.
- Integrity: no issues. No tile was opened or viewed. No prior output was deleted.
