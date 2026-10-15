Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-a: 20260701183124-w010-027 tiles (DECL-P4-2 M1, item 2)

Builder report. No tile, map or CT pixel was opened, viewed or described. The checks below use numbers, shapes and hashes only.

## Inputs (official bucket, anonymous; sha256 in downloads.jsonl)
- Prediction: `PHercParis4/segments/20260701183124-w010-027/ink-detection/PHercParis4-20260701183124-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif`
  - 1,070,196,417 B, sha256 in manifest.json.
  - uint8, 69760 x 170000, 1024^2 deflate tiles.
- Mesh: `mesh/20260701183124-on-20260411134726-2.4um.tifxyz` (x/y/z.tif, 118,592,134 B each, plus meta.json).
  - Grid 3488 x 8500, meta scale 0.05.
- Voxel size: 0.0024 mm, from volume metadata.json `scan.tomo.acquisition.detector.samplePixelSize`. This matches the volume name (2.400um).

## Geometry (grid.json)
- Canvas / grid = 20.0 exactly on both axes.
- Mesh-valid vertices: 28,221,728 of 29,648,000 (95.19 %). The -1 vertices are identical on x, y and z. There are no non-finite vertices.
- Median 3-D edge length is 19.978 vox over 56.4 M edges (P1-P99: 17.21-21.26). Along cols it is 19.987; along rows, 19.969.
- px_per_mm = 20 / (19.978 x 0.0024) = **417.131**.
  - Per axis: 416.94 (cols) and 417.32 (rows).
  - The nominal 1 px/voxel value would be 416.67.
- **T = round(20 x 417.131) = 8343 canvas px.** The tile grid is 9 rows x 21 cols = 189 tiles.
- Area cross-check:
  - Valid area summed over all tiles: 648.78 cm^2.
  - Mesh meta area_vx2: 641.42 cm^2, the official figure.
  - The difference is +1.1 %. It comes from the median edge versus the true per-quad area.

## Tiles
- 160 of 189 tiles are read-eligible (valid fraction >= 0.5). The 29 ineligible tiles all have valid fraction <= 0.326.
- Eligible tiles cover 623.27 cm^2 of mesh-valid canvas.
- Every eligible tile was checked:
  - PNG 1068 x 1068, 8-bit grey (IHDR); chunks only IHDR/IDAT/IEND.
  - The sha256 recomputed from the file matches the census.
  - Total 42.4 MB; the largest file is 339 KB.
- Consistency: the raw prediction has 0 nonzero pixels outside the mesh-valid mask in every eligible tile. The official product is already masked, so masking changes nothing.
- tile_points.npz: 160 keys, each (4096, 3) float32 x,y,z in 20260411134726 voxels, seeded subsample (rng seed [20260926, r, c]).
- Files:
  - manifest.json: per-tile r, c, valid fraction, PNG sha256, mean/std/frac>=150 of raw valid pixels.
  - tile_census.jsonl: all 189 tiles.
  - tiles/w010-027_r<r>_c<c>.png

## Timings and failures
- Fetch: 38 s for 7 files, including 28 s for the 1.07 GB prediction.
- Geometry: 10 s. Tiling: 216 s total, 0.7-2.1 s per tile, single process.
- Failures: no data request was refused.
  - The final commit and push were blocked once by a session permission check. They were completed afterwards, on the owner's instruction.
- Region reader self-check: an overlapping crop is identical, and pixels beyond the canvas are 0.
- The first 40 tiles were pushed in commit 98d5456; this commit adds the remaining 120.

## Notes for the orchestrator
- The file names carry segment, row and column. DECL-P4-2 item 2 requires uuid4 names and a key held in /srv/scorer, so renaming and keying must happen before any reader sees these files.
