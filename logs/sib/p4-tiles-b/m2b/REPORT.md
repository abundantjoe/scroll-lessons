Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-b report: M2b, segment 20260623142658-w028-037 (DECL-P4-4)

Builder role only. No tile, map, mesh image or CT pixel was opened, viewed, displayed or described. Only numbers, shapes and hashes were computed. The PNG bytes were hashed before they were written, and no PNG was read back.

Outputs are in `logs/sib/p4-tiles-b/m2b/`: `tiles/`, `manifest.json`, `grid.json`, `uv_check.json`, `tile_points.npz`, `tiles.jsonl` and this report. They sit in a subdirectory so the earlier M1 outputs in `logs/sib/p4-tiles-b/` are kept unchanged; nothing was deleted.

## Inputs (official bucket, anonymous HTTPS; fetched 2026-09-26 ~06:00Z)
| key (under PHercParis4/) | bytes | sha256 |
|---|---|---|
| segments/20260623142658-w028-037/ink-detection/PHercParis4-20260623142658-1.129um-0.23m-78keV-volume-20260608103018-L1-20260709123958-mrg20736-1um-s1z2-tile256-stride128.tif | 1175621159 | 51243509489ef578eae21d83abdaca4da72f95034d3d27e4b5770ff637314650 |
| .../mesh/20260623142658-on-20260608103018-1.129um.tifxyz/x.tif | 370112646 | 169dc4d78808cad2553e5911df4dd5152705ad3e7e73c3c54ff81cb6752f1a04 |
| .../1.129um.tifxyz/y.tif | 370112646 | d127a8dcb439c9dd827ad134b555e005d4ccdda0003454b4c98acb116b2044fd |
| .../1.129um.tifxyz/z.tif | 370112646 | 26a025bbf90f7b9c2d6219ccc2919b946ee341262b07b86e9dd0a15c9a168324 |
| .../1.129um.tifxyz/meta.json | 411 | 7b60c4094de5c856fc17958c27cd50ab56e1b21fd31f965a0ed9fca62e921a20 |
| .../mesh/20260623142658-on-20260411134726-2.4um.tifxyz/x.tif | 82035334 | 170e9d58cabc8096a218ea931ff851a36c4f80491a3620d75e34072238f1c04e |
| .../2.4um.tifxyz/y.tif | 82035334 | 16d5597f4f84eb275cd6603f1257e28c7d9ea317e725b2b409378e9b2ecaf7ee |
| .../2.4um.tifxyz/z.tif | 82035334 | 7589c7e1bf557ea46b0b4cc32a4d2137d6a52cb21ea92101c61b62603a770798 |
| .../2.4um.tifxyz/meta.json | 403 | 2f6bba107a68518c1aafd64283f7a4a4bb024c8662cd6e3855a8a75aa128979f |
| volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr/metadata.json | 158775 | acd47f1093d8917b1642198e3f0f5de3bff3d86222e630600a225bb46ba715ca |
| volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr/.zattrs | 3018 | 97e968dbbf11cc856dc57648aaaa9e6cade5e6575472dcfdeac7cfa50f546dd9 |
| volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr/transform.json | 3053 | 2291a626dd3a2712984ec7eaa00bcf6f636b10936c9c36d57efc7228f649d1ad |

- **Byte-count discrepancy:** DECL-P4-4 item 1 gives the M2b prediction as 1,175,621,659 B. The bucket listing and the downloaded file are both **1,175,621,159 B**, which matches the task notice. The DECL figure looks like a one-digit typo; the file used is identified by the sha256 above.

## Geometry (grid.json)
- Voxel size (I9): 0.001129 mm, from metadata.json `tomo.acquisition.detector.samplePixelSize`.
[line withheld: prize-candidate detail under review]
- Prediction canvas: 49280 x 187760 uint8, deflate-compressed with no predictor, in 1024 x 1024 TIFF tiles.
  - On 3 TIFF tiles, my zlib decode matched tifffile's own decoder exactly.
- tifxyz grid: 4928 x 18776. **Canvas/grid = 10.0 exactly** on both axes.
  - The mesh scale 0.05 means 20 L0 voxels per grid step, which is 10 L1 px. This confirms the canvas is L1 (`.zattrs` level 1 has scale 2).
- Mesh-valid vertices: 86,593,672 of 92,528,128 (93.59 %).
  - 5,934,456 vertices are -1, and x, y and z agree on every one.
  - There are 0 non-finite values.
- Median 3-D edge length over 173.2 M valid edges: 19.973 L0 voxels (0.022550 mm).
- px_per_mm = 10 / 0.022550 = **443.47**.
  - Axis-only values: 443.70 (columns) and 443.21 (rows), so the anisotropy is 0.11 %.
  - Nominal L1 value: 442.87.
- T = round(20 x 443.47) = **8869 px**. The display scale is 1068/8869, i.e. 53.4 px/mm.

## Tiles
- Tile grid: 6 x 22 = 132 tiles from origin (0, 0).
  - Tiles that run past the canvas are zero-padded to T x T. The padded pixels count as not mesh-valid, in a T² denominator.
  - The last column is 1511 px wide, and the last row 4935 px.
- **106 tiles are read-eligible** (>= 50 % mesh-valid). 26 are not, and 1 of those is 0 % valid.
  - Valid fraction: minimum 0.511, median 1.0. 78 tiles are >= 99.9 % valid.
  - For every tile, the valid fraction from the grid formula equals the per-pixel count.
- PNGs: `tiles/20260623142658-w028-037_r<r>_c<c>.png`, each 1068 x 1068 uint8, with chunks IHDR/IDAT/IEND only (asserted on every file).
  - Total size 25.2 MB; the largest file is 0.43 MB.
- Stats per tile in manifest.json, over the valid raw L1 pixels: mean, std, frac_ge_150, frac_zero_valid and frac_mesh_points_outside_1129_volume.

### Important: scan-coverage zeros (numbers only)
- **All 21 read-eligible tiles in row 0 (r0_c0 .. r0_c20) are 100 % zero** in the prediction over their mesh-valid pixels.
  - Their PNGs are byte-identical (sha256 3308991c...). They are the only duplicate group; the other 85 tiles have unique hashes.
- Row 1 tiles are 68-78 % zero, and rows 3-4 are 15-52 % zero on many columns. 69 of the 106 tiles are >= 5 % zero.
- Cause, checked numerically: the per-tile zero fraction tracks the fraction of the tile's mesh points that lie outside the 1.129 um volume's L0 extent (zyx 59969 x 36006 x 32354).
  - Pearson r = 0.998; mean absolute difference 0.016.
  - By row, the mean fraction outside the volume vs the mean zero fraction is: row 0, 1.000 vs 1.000; row 1, 0.710 vs 0.723; row 2, 0.017 vs 0.040; row 3, 0.155 vs 0.175; row 4, 0.134 vs 0.154.
  - This matches recon: the 1.129 um mosaic covers only the central region (z 67-135 mm), while this strip reaches further.
- **These zeros mean "no CT input", not "no ink".** Those regions carry no measurement. The orchestrator may want to decide, before the census, whether all-zero or mostly-zero tiles are shown to readers; they would be trivially blank and identical. I made no selection; every tile that meets the >= 50 % mesh-valid rule was written.

## Mesh points (tile_points.npz, 10.2 MB, 530 arrays)
- For each of the 106 tiles:
  - `r<r>_c<c>`: 4096 x 3 float32 xyz in 20260608103018 L0 voxels (the mesh's own frame);
  - `r<r>_c<c>__f20260411134726`: the same points in 20260411134726 voxels;
  - `__f20260411134726_src`: 0 = same-UV, 1 = affine;
  - `__grid_ij`: the 1.129 um grid row and column;
  - `__n_valid_vertices`: valid vertices in the tile before subsampling.
- Every tile had more than 4096 valid vertices. The subsample was drawn by default_rng(20260926 + 1000 r + c).
- **Frame 20260411134726: same UV, verified** (uv_check.json).
  - Grids 4928 x 18776 and 2320 x 8840 correspond under the pixel-centre map i24 = (i + 0.5) x 2320/4928 - 0.5, and j likewise.
  - Checked against the published affine (transform.json, 1.129 um L0 xyz -> 2.4 um xyz; landmark residual median 1.10 vx, max 1.88) on 2000 random vertices:
    - median distance 0.005 vx, p95 0.55 vx, max 3.36 vx (2.4 um voxels);
    - a free per-vertex refit gives the same map (slopes 0.470779 / 0.470814, offsets -0.2646).
  - Simpler maps fail: ratio without centring gives 7.5 vx, and the voxel-size ratio gives 71 vx.
  - Over all 434,176 saved points: same-UV vs affine median 0.005 vx, p99 1.10, max 9.58.
  - **242 points (0.06 %) used the affine fallback** because a bilinear corner was invalid in the 2.4 um mesh.
- All vertices were not saved. There are 86.6 M valid vertices, 1.04 GB per frame as float32 xyz, which is over the 90 MB per-file limit. p4-excl can read all vertices from the official tifxyz (sha256 above) with the same UV map.

## Timings
- Download: about 40 s for 2.6 GB.
- UV check: about 1 min.
- Tiling: 103.1 s in total with 4 workers, about 2 s per tile.
- Zero and coverage supplement: about 2 min.

## Pushes
- 040d243: tools, grid.json, uv_check.json, tile_points.npz and the first 40 tiles.
- The next commit adds the remaining 66 tiles, manifest.json, tiles.jsonl and this report.

## Notes
- Naming follows the task notice (`20260623142658-w028-037_r{r}_c{c}.png`). The flat uuid naming and the key are the orchestrator's step (DECL-P4-2 item 2).
- The model 20260709123958 has no public card, and its training data are unknown (DECL-P4-4 item 1).
- There were no failures, refusals or retries. The large downloads were deleted after use.
