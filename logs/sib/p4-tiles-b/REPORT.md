Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-b report: segment 20260701183125-w028-037 (DECL-P4-2, material M1)

Builder role only. No tile, map, mesh image or CT pixel was opened, viewed, displayed or described. Only numbers, shapes and hashes were computed. The PNG bytes were hashed before they were written, and no PNG was read back.

## Inputs (official bucket, anonymous HTTPS; fetched 2026-09-26T00:27Z)
| file | bytes | sha256 |
|---|---|---|
| ink-detection/...-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif | 1207687349 | 698795e1b993bde4d8f65e6f3b3e84bef6b8017d4494deedce91897a7b2c8034 |
| mesh/20260701183125-on-20260411134726-2.4um.tifxyz/x.tif | 125042374 | 5cfb0dd25c39bcd6b94c314b9e06e9a1acfb4cd610f10338cb7b2b2d9354d606 |
| .../y.tif | 125042374 | cd631abe22a4205da70afa22eab11d91a59662c3f8788283261ad4c0a1037c05 |
| .../z.tif | 125042374 | 6e2681f9298a5311f081ae9afbd16d8a333c8991d57d2c8ddbb761dc565bb86b |
| .../meta.json | 410 | da81ed99c6df18e0e42887c818526e238073eae12961b5338eda926ffb5df241 |
| volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/metadata.json | 8453 | 881bf77fc0f02a91040755da25d54ad958e290a528ec61489e411937112fba4d |

Full keys are in manifest.json and grid.json. The large downloads were deleted after use.

## Geometry (grid.json)
- Voxel size (I9): 0.0024 mm, taken from metadata.json `scan.tomo.acquisition.detector.samplePixelSize`.
- Prediction canvas: 71600 x 174640 uint8, deflate-compressed (32946) with no predictor, in 1024 x 1024 TIFF tiles.
  - The canvas was decoded region by region with zlib.
  - On 3 TIFF tiles this decode matched tifffile's own decoder exactly.
- tifxyz grid: 3580 x 8732 (mesh scale 0.05). Canvas/grid = 20.0 exactly on both axes.
- Mesh-valid vertices: 29,371,664 of 31,260,560 (93.96 %).
  - 1,888,896 vertices are -1, and x, y and z agree on every one.
  - There are 0 non-finite values.
- Median 3-D edge length of valid grid edges:
  - 20.078 vx overall (58.7 M edges);
  - 20.212 vx along columns;
  - 19.962 vx along rows.
- px_per_mm = 20 / (20.078 x 0.0024) = **415.04**.
  - Axis-only values: 412.29 (columns) and 417.47 (rows).
  - Nominal (1 px per voxel): 416.67.
- T = round(20 x 415.04) = **8301 px**. The display scale is 1068/8301 = 0.12866, i.e. 53.4 px/mm.
[line withheld: prize-candidate detail under review]

## Tiles
- Tile grid: 9 x 22 = 198 tiles from origin (0, 0).
  - Tiles that run past the canvas are zero-padded to T x T. The padded pixels count as not mesh-valid, in a T^2 denominator.
  - The last column is only 319 px wide, and the last row 5192 px.
- **171 tiles are read-eligible** (>= 50 % mesh-valid). 27 are not, and 7 of those are 0 % valid.
  - Valid fraction: minimum 0.502, median 1.0. 133 tiles are >= 99.9 % valid.
  - For every tile, the valid fraction from the grid formula equals the per-pixel count (maximum difference 0).
- PNGs: tiles/w028-037_r<r>_c<c>.png, each 1068 x 1068, with chunks IHDR/IDAT/IEND only (checked on every file).
  - All 171 sha256 values are distinct.
  - Total size 47.2 MB; the largest file is 0.35 MB.
- Numeric stats over the valid raw full-resolution pixels (manifest.json, per tile):
  - mean: 39.1 to 80.5 (median 66.5);
  - fraction >= 150: 0.020 to 0.217 (median 0.144).
- tile_points.npz: 171 keys r<r>_c<c>. Each holds 4096 x 3 float32 xyz in volume 20260411134726 voxels.
  - These are the valid vertices whose canvas position lies in the tile.
  - Every tile had more than 4096 such vertices. The subsample was drawn by default_rng(20260926 + 1000 r + c).

## Timings
- Download: about 20 s for 1.58 GB.
- Grid geometry, tiling, PNGs and points: 71.1 s in total with 4 workers, about 1.1 s per tile.

## Pushes
- 7881a6e: grid.json, tools and the first 40 tiles.
- 380672d: the remaining 131 tiles, manifest.json, tiles.jsonl and tile_points.npz.
  - This commit also removed local scratch paths from grid.json fetch records.

## Notes and failures
- There were no failures, refusals or retries.
- Anisotropy: the median grid step is 1.25 % longer along columns than along rows.
  - Each tile is therefore about 20.13 mm wide by 19.88 mm tall on the surface (T at the pooled median).
  - This is recorded, not corrected.
- Naming: the files use the w028-037_r<r>_c<c>.png names given in the task brief. DECL-P4-2 item 2 asks for flat uuid4 names and a /srv/scorer key; that renaming and keying is the orchestrator's step and was not done here.
- The labelled-adjacent flag (the 1.2 mm distance check) is not computed here. The sibling p4-excl computes it from tile_points.npz.
