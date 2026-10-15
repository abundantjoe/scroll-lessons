Provenance: Project HERCULES | owner the owner | [id removed]

# C3 regression gate: runner output

Raw outputs for RULES.md DECL-C3. This runner gives no verdict. Full numbers, paths, sha256s, commands and versions are in `c3_results.json`. Large files are under /work/c3 (not in the repo).

## Inputs

- Volume: `s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/` (voxel 9.362 um, from metadata.json samplePixelSize).
- Segment: `s3://vesuvius-challenge-open-data/PHerc0139/segments/20250831000000-w040_2025083102/` (the name exists exactly as declared).
- Unlevelled team mesh: `mesh/20250831000000-on-20250728140407-9.362um.tifxyz` (grid 320 x 399, scale 0.05).
- Team SV: `surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr`, shape [28, 6400, 7980] (28 slices), uncompressed uint8.
- Labels: `hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w040/`, shape [28, 6400, 7980], annotated only at Z=14, values 0/255. They match the S3 ink-labels/20260918 copy exactly.
- Checkpoint sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab (matches the expected hash). Metric code pixel.py sha256 a5ab7fed2b83ce005e45a683ba883f8f53073dd9f9818c375bc9ab693fc097c8 (matches the declared hash).

## Canvas

Mesh grid x 20 = 6400 x 7980. This equals the team SV and label shapes, so all three are on one canvas. The render used `--crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048` and omitted `--auto-crop`, which keeps the SV canvas origin.

## Render fidelity (crop 2048 x 2048 at x1152, y2048; all pixels valid in both)

| Pooled Pearson | Minimum per-slice Pearson (slice) | Best slice offset | Best canvas shift (dy,dx) | Voxels exactly equal |
|---|---|---|---|---|
| 0.9999990 | 0.9999987 (12) | 0 | 0,0 | 0.9971 (max diff 1) |

The render took 71 s (2026-09-24T21:58:51Z to 2026-09-24T22:00:02Z) and streamed chunks from S3 through the proxy.

At slice offset +1 or -1, r = 0.8281. With the slice order reversed, r = -0.0146. Nothing was re-aligned.

## AUC (Mann-Whitney AUC; ink = label > 127.5; blank = label == 0; valid = model-input valid mask and label canvas)

| Map | Forward | Reverse | Time for both orders |
|---|---|---|---|
| Our render crop, C2 with --tta-mirror (declared) | 0.9549 | 0.4254 | 40.7 min (2026-09-24T22:12:27Z to 2026-09-24T22:53:10Z) |
| Our render crop, no TTA | 0.9691 | 0.3987 | 8.8 min (2026-09-24T22:53:10Z to 2026-09-24T23:02:01Z) |
| Team SV, whole canvas, no TTA (archive 0.9966 / 0.4963) | 0.9807 | 0.4563 | 56.4 min (2026-09-24T23:02:01Z to 2026-09-24T23:58:27Z) |

Extra rows (not declared): inside the organizer supervision mask, crop with TTA: 0.9902 / 0.5658; team SV: 0.9966 / 0.4963. Team SV inside the label bbox: 0.9784 / 0.4532.

Order naming comes from the code (infer.py at 41701aa). `OUT.tif` is forward: source layers 6..22 in ascending order. `OUT_reverse.tif` is reverse: layers 22..6.

## Declared bars (for the decider)

Pooled render Pearson >= 0.999. Forward AUC >= 0.987 and reverse AUC < 0.60, both for C2 with --tta-mirror.

## Deviations and notes

- DEFECT (AUC valid-pixel set). The declared AUC counts every valid pixel with label == 0 as blank. Computed that way, the team-SV no-TTA check gives forward/reverse 0.9807/0.4563, which does not reproduce the archive reference 0.9966/0.4963. Restricting to the organizer supervision mask (native9 w040_supervision_mask.zarr, Z=14, value > 0) gives 0.996586/0.496328, which matches the archive to 4 decimals. So the archive valid set was most likely the supervision mask, and the declaration text omits it. The choice moves the declared C2+TTA forward AUC on the crop from 0.9549 (declared text) to 0.9902 (supervision mask). The runner reports both and does not choose.
- vc_render_tifxyz requires -v/--volume (the suggested command omitted it). The S3 volume URL was passed as -v. With --remote-url and --voxel-size given, -v is only written into the output .zattrs source_zarr (vc_render_tifxyz.cpp L1258-1266, L1475-1484).
- Flags added to the declared render command: --crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048 (the declared crop), --zarr-output (the app needs an output), and --cache-gb 4 (memory only). The output zarr uses the default blosc-lz4 compression, which is lossless. --auto-crop was omitted to keep the SV canvas.
- S3 access through the proxy worked with the s3:// form. No https fallback or local chunk mirror was needed for the render. Fetched chunks sat in the container-ephemeral /root/.VC3D/remote_cache, which was removed with the container.
- Pearson: the declared literal reading (all 2048 x 2048 crop pixels) is the primary number. Every crop pixel is valid in both the render and the team SV (any of the 28 slices is nonzero), so the jointly-valid variant is identical.
- Labels are 0/255, so the half-range threshold is 127.5 and ink = label == 255. Blank = label == 0. No other values occur. The label canvas covers the whole SV canvas, so valid pixels = the model-input valid mask. In the crop that is all 4,194,304 px.
- Team SV "whole labelled area": the whole SV canvas was run (no --mask-path; the occupancy scan kept 85.3% of level-3 cells, 11078 patches per order). The AUC uses every SV-valid pixel on the label canvas, which is the same definition as the crop. Two extra views are reported: inside the organizer supervision mask, and inside the label bounding box. The archive AUC area definition is not available to this runner.
- Inference ran on the 2048 x 2048 crop render only, as the brief states. Patches at the crop border have no context beyond it.
- Model maps are uint8 TIFFs (official output). AUC ties get average ranks (pixel.auc).
- The wrapper scripts (fidelity.py, auc_eval.py: crop, masks, binarisation) are not covered by a METRIC-HASH entry; only pixel.py is declared. Their sha256s are listed under scripts.
- The declaration VOID conditions refer to an "archive description" of the label crop, the direction naming and the SV slice alignment. This runner does not have that description. Observed facts: crop on the SV canvas at x1152, y2048 (no offset; the canvas-shift scan peaks at 0,0); OUT.tif = forward (layers 6..22 ascending), OUT_reverse.tif = reverse; team SV slice k matches render slice k (best offset 0).
- CPU contention: other project agents ran CPU jobs during the inference (load average up to about 7.9 on 4 cores). Wall times are inflated and not comparable to the TOOLING benchmark. In the TTA run the forward order took about 8.4 min and the reverse order about 32 min.
- Ledger: a 128 x 128 test render (rc 0) and one failed launch (rc 127, /usr/bin/time missing, nothing ran) are logged. The HF label download row was added by hand with the same fields, because it ran before the ledger wrapper existed.

Disk used under /work/c3: 1.75 GB.
