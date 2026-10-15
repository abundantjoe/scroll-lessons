Provenance: Project HERCULES | owner the owner | [id removed]

# P4-O model-input stacks for the Paris 4 title strip (DECL-P4-14 item 2): chain2um support

Numbers only. No image was written, opened or displayed, and no model was run on Paris 4 by this task. PHercParis4 is not an eligible scroll (data/catalogue/eligible_products.json lists it only as non-eligible), and nothing here touches PHerc0841.

## What the eligible checkpoints need
- At dispatch (2026-09-26 ~18:45Z), only ckpt-screen-b lists eligible checkpoints: scrollprize/PHerc.1667-iteration-0..5, a ResNet3D-50 family.
- ckpt-screen-a (ink_9um seed43, hecate_9.6um, ink_3d_dino_guided) and ckpt-screen-c (5 checkpoints) list none: each one's documentation states Paris 4 training data.
- The ruled geometry of the 1667 family (ckpt-screen-b STATUS.md, orchestrator ruling 2026-09-26 05:59Z) is 2.399-um class, 62 layers centred on the surface, 256 x 256 tiles, clip(0, 200)/255. So the input is the native 2.4 um organizer surface volume and **no resampling is needed**.
- The dispatch's "typically 7.9-9.6 um" does not apply to any currently eligible checkpoint. A 9.6 um option (organizer XY pyramid level 2, optional 4x z mean) is provided and verified in case a later checkpoint needs it.

## Source and grid
- Surface volume: s3://vesuvius-challenge-open-data/PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
  - zarr v2, level 0 (109, 69760, 170000) uint8, chunks (109, 128, 128), uncompressed.
  - Voxel 2.400 um, from the volume metadata.json (samplePixelSize 0.0024 mm).
- The SV canvas is the strip-a canvas (p4-tiles-a grid.json: 69760 x 170000, T = 8343, tile (r, c) = rows [r*T, (r+1)*T), cols [c*T, (c+1)*T) from (0, 0), c0 = outer end).
- Size: one full 62-layer tile slab is 8343^2 x 62 = 4.3 GB uint8. The 108 tiles r0-r5 x c0-c17 cover 459,162 chunk objects (of 472,827 grid positions; missing = fill 0) = 820 GB of raw chunks. Compressed per-tile npz in git is therefore impossible (limit 95 MB per file). The deliverable is a **reproducible streaming reader plus hashes**.

## Reader
`tools/sib/chain2um/p4o/p4o_stack.py` (sha256 in manifest.json):
- `read_stack(y0, y1, x0, x1, z0=23, nz=62, level=0, zpool=1)` returns (H, W, nz) uint8 in SV order.
- `tile_bounds(r, c)` gives a tile's canvas bounds.
- CLI: `python p4o_stack.py --tile R C [--roi y0 y1 x0 x1] --out f.npz`.
- Anonymous HTTPS; missing chunks = 0; optional local chunk cache via P4O_CHUNK_CACHE.
- A consumer tiles its own 256 px model patches inside a tile, and mesh-valid masking uses the mesh (grid = canvas // 20).
- Streaming cost: each 128 x 128 column fetches all 109 slices (1.78 MB), i.e. about 7.6 GB per full tile. At the measured throughput (about 50 MB/s single stream; 108 tiles x 16 chunks in 3.5 min with 16 threads) a full tile is a few minutes of I/O, small next to about 394 CPU-min of inference per 2 x 2 cm per order.

## Conventions, verified on this segment (not assumed from 0139)
1. The SV slice order equals the official renderer with --flip-normals, with the surface at slice 54 = (109-1)/2.
   - Setup: our vc_render_tifxyz (villa 41701aa build) `-n 109 --slice-step 1 --voxel-size 2.4 --flip-normals` on the official 2.4 um mesh, over 3 regions of 256 x 256 px at tile centres. The regions are r5_c10, r5_c11 and r5_c6, drawn by seed 20260926 among the 104 r0-5 c0-17 tiles with >= 95 % mesh-valid.
   - Pooled Pearson at offset 0 = 0.9999974 / 0.9999981 / 0.9999976.
   - Per-slice min >= 0.99995; 99.2-99.4 % of voxels are bit-identical.
   - The reversed stack gives r = -0.14 / -0.18 / +0.15.
   - `verify_render.json`.
2. The default slab [23, 85) is bit-identical to render slices 23..84 in all 3 regions. That is the same window as the chain2um-validated 2.4 um chain, which reproduced the organizer canonical map at r = 0.99999 on PHerc0139 w043 (logs/sib/chain2um/REPORT.md).
3. Level 2 (9.6 um XY option) vs our 4 x 4 XY mean of level 0: Pearson 0.99997, max abs diff 1 grey level (rounding), 74.8 % exact (`verify_level2.json`).
4. Determinism: re-reading r0_c0's check ROI reproduces its manifest sha256 (946f6c23...).

Text order for the 1667 family is not documented relative to this frame. Per the orchestrator ruling, both orders are mapped: forward = as returned, reverse = `[..., ::-1]`. Our 2.4 um canonical-model finding (text order = official FORWARD on a --flip-normals render) applies to ink_canonical_2um only, and is not transferred to the 1667 family.

## manifest.json
For each tile r0-r5 x c0-c17 (108), manifest.json records:
- canvas bounds;
- mesh-valid fraction (min 0.772; all >= 0.5);
- chunk ranges, and chunks present;
- a sha256 digest of the tile's S3 listing lines ("key etag size", sorted), which detects any upstream change without downloading;
- the content sha256 of the default slab (z [23, 85), SV order, C-order (H, W, 62) uint8) over the 512 x 512 px ROI at the 128-aligned tile centre, so a consumer can check its read with `read_stack(*center_roi_canvas_yx)`.

## Commands (all rows in ../runs.jsonl)
- `python tools/sib/chain2um/p4o/verify_render.py logs/sib/chain2um/p4o/verify_render.json`
- `python tools/sib/chain2um/p4o/build_manifest.py /work/p4o/tiles_manifest.json` (3.5 min)
- `python tools/sib/chain2um/p4o/verify_level2.py logs/sib/chain2um/p4o/verify_level2.json`
- The mesh (x/y/z.tif, meta.json) was downloaded from the official bucket; sha256s are in manifest.json.

## Events
- The docker daemon was down again after an earlier container restart. It was restarted as in setup_env.sh; the renders used for verification ran after that.
- No other failure.

Integrity: no issues.
