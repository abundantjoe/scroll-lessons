Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814b: P4-E material E2 (RULES.md DECL-P4-5)

STATUS: DONE (2026-09-26T11:08Z)

This is a builder report. No tile, slice or map was opened, viewed or described; everything below is numbers, shapes
and hashes. There are 160 read-eligible tiles, the same set as P4-B strip a, and each has a uint8 PNG of
1068 x 1068 at tiles/20260701183124-w010-027_r{r}_c{c}.png. The files are named by segment, row and column, as
instructed. As with strip a, renaming to uuids and keying happen on the orchestrator side before any reader sees
them.

## Material and inputs (sha256 in downloads.jsonl and manifest.json input_sha256)

* Surface volume: s3://vesuvius-challenge-open-data/PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
  * .zattrs a4d12973..., .zgroup 2b31f1f5...
  * .zarray: level 0 8ffed5fa..., level 1 8702d79b..., level 2 a988c2d1..., levels 3-5 recorded.
  * The .zattrs say: downsampling_method mean; scales (z, y, x) are 2.4 / 2.4·2^L / 2.4·2^L um for L = 0..5;
    num_slices 109; canvas_size [170000, 69760] (W, H).
  * Chunks are (109, 128, 128) u8, uncompressed, C order, fill 0.
* Chunk manifest: chunks.jsonl has one row per chunk read.
  * Each row gives the key, the byte range and the sha256 of the bytes read.
  * 46,714 range reads returned 206. 896 chunks were absent (404), and those are fill 0 per .zarray.
* Mesh: the official tifxyz of 20260701183124-on-20260411134726-2.4um (meta, x, y and z.tif). These match strip a's
  hashes (8a61b3e6..., c304cdfd..., 9a4eefda..., a06716af...).
* Voxel size: 0.0024 mm, from the volume metadata.json samplePixelSize. That file's sha256 is 881bf77f..., the same
  as strip a's.

## Grid and mapping (grid.json)

* The grid is identical to P4-B strip a: grid.json and manifest.json at e25635c, whose sha256 values are recorded.
  * T = 8343 canvas px (20 mm at 417.13 px/mm), origin (0, 0), 9 x 21 tiles.
  * Mesh-valid uses strip a's canvas_mask rule (canvas px -> grid i // 20, j // 20), and a tile is eligible at
    >= 50 % valid.
* Canvas to surface volume: level-0 in-plane shape (69760, 170000) equals the render canvas, so canvas px (i, j) is
  level-0 (row i, col j).
* Level used: **2** (in-plane 9.6 um, which is <= 18.7 um). It is the mean of 4 x 4 level-0 px, so canvas px (i, j)
  lies in level-2 px (i // 4, j // 4). Each canvas pixel takes its parent's value, with no interpolation.
* Depth is not downsampled at any level (z scale is 2.4 um everywhere). The centre slice is 54, the mesh surface.
  The slab is slices 32..76: 45 slices, +-22 slices, +-52.8 um. Each chunk is read by one HTTP range request of
  those 45 contiguous slices, and the per-pixel value is the float mean over them.

## Display (fixed by DECL-P4-5 item 2; one projection, nothing else tried)

For each tile:
1. A linear 1-99 % stretch over the tile's mesh-valid canvas px (hercules.display.builder.linear_window_ct, the
   project display builder).
2. 0 outside mesh-valid.
3. cv2.INTER_AREA 8343 -> 1068.
4. A uint8 grey PNG (builder.png_bytes).

## Validation

* **Grid and mask match strip a exactly.**
  * 189 census rows and 160 eligible tiles; the eligible set equals strip a's.
  * valid_fraction and valid_px are equal to strip a's for every tile (exact float and int equality).
* **PNG files.** Every PNG was parsed chunk by chunk, with CRC checked. All 160 contain only IHDR, IDAT and IEND,
  are 1068 x 1068, 8-bit grey, and their sha256 recomputed from the file matches the manifest. The total is 125.3 MB
  and the largest file is 839 KB.
* **Determinism.** Tile r0 c0 from the main run has PNG sha256 9b9eb491..., the same as an earlier independent test
  run in a separate directory.
* **Level-1 cross-check (r0 c0).** The same tile rebuilt from level 1 (4.8 um) gives:
  * PNG sha256 0d939a03...;
  * mean |diff| 1.28 u8, p99 |diff| 6 u8, Pearson r 0.99936, over px nonzero in either image.
  * So level 2 does not change the 18.7 um display beyond rounding-level differences.
* **Surface-volume coverage inside the mask.**
  * Fraction of mesh-valid canvas px where the slab mean is 0: median 0.0, max 0.0032 (0.32 %, tile r0 c0).
  * Nonzero surface-volume px outside mesh-valid: 0 in every tile. The surface volume is masked to the mesh.
* **Slab-mean statistics** over mesh-valid px, before the stretch, across the 160 tiles:

  | Statistic | min | median | max |
  |---|---|---|---|
  | mean | 68.6 | 82.2 | 98.2 |
  | std | 16.5 | 18.3 | 21.3 |
  | stretch p1 | 39.7 | 43.5 | 49.0 |
  | stretch p99 | 112.0 | 122.5 | 134.1 |

## Time and resources

* The tiles took 1728 s of compute in total: median 10.7 s per tile (read 4.0 s, compute 6.7 s), max 18.9 s.
  32 range-request threads, 1 process.
* Machine: 4 vCPU Xeon @ 2.10 GHz, 15 GB RAM, no GPU. The same container ran pairs0814b.

## Incidents (logged in ../runs.jsonl)

1. **Driver bug.** In e2_run.sh, the retry loop in push() used the global variable i. Because of that, after
   batch 1 the batch index reset on every successful push.
   * The driver re-ran an already finished batch 296 times. Each run was a no-op: one runs.jsonl line and one
     commit ("tiles batch 2 (80 tiles)"), with no tile data changed.
   * One tile (list index 40) was skipped in that pass.
   * History was not rewritten.
2. **Container restart.** The restart stopped the looping driver at 10:50Z. The fix is `local i` (commit 84113b9).
   The run resumed from the census: the done tiles were skipped, and the skipped tile and the remaining 80 were
   built. The final checks cover all 160.

## Files

* tiles/: 160 PNGs.
* manifest.json: per-tile file, r, c, png_sha256, png_bytes, valid_fraction, canvas box, stats and chunk counts;
  plus input_sha256, checks, the ineligible list and the level-1 cross-check.
* grid.json: the strip-a grid plus the surface-volume mapping.
* census.jsonl: all 189 tiles.
* chunks.jsonl: the chunk manifest.
* downloads.jsonl: input hashes.
* Code in tools/sib/pairs0814b/:

  | File | sha256 |
  |---|---|
  | e2_tiles.py | 6cdf8c3d8abd25ab58e458e7a4b17641f34260ddb3f2612b69864ef586bc26ad |
  | e2_finalize.py | 54500db37142b40a80acc9a22d0e7913cab26775a49bdc773a09fa8650549feb |
  | e2_run.sh | ddd60e90b1b65f1701893f44e006eaa344cfe6061ef85de44fcbf077f7d70fb4 |

* manifest.json sha256 462909e1310369194e6321513aef3010f922dcea1d33c29afe627c48a8850210; grid.json sha256
  9703b4e26d39e9c25ae9cc0736f90a000cbce7bfaccf271ef7d7322ef8aacb96.
