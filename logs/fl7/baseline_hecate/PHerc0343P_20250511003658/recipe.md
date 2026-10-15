# Hecate 9.6 um on the held-out scroll PHerc0343P (DECL-FL-7 item 3(ii), public-model comparison)

## What was run
- Model: Hugging Face `scrollprize/hecate`, revision 9cb86e500e944b11a06a7020403cde5dffb5bcb2 (MIT), file `hecate_9.6um.pth`,
  sha256 809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d (matches the HF LFS record). 130.4 M parameters
  (ResNet-152 3-D encoder, 3-D U-Net decoder, learned depth attention -> 2-D logits). Runtime: the released `hecate.py`
  (sha256 c232c18a..., vendored unmodified in tools/master/hecate/).
- Recipe per the model card: input = unnormalised uint8 Z,Y,X surface-conditioned render sampled at 9.6 um on all three axes;
  patch 16 x 64 x 64; CT / 255, no clipping; the central 16 planes of the render; XY tiling at half-patch stride (32) with a
  floored Hann blend; empty CT columns zeroed; output uint8 = round(255 p), no min-max scaling; `--reverse` flips the full
  depth before selecting the central planes. fp32, CPU. Batch size changes throughput only (eval-mode BN/GN).
- Segment: PHerc0343P 20250511003658-tifxyz, organizer surface volume 8.64um-1.2m-116keV-volume-20250521134555.zarr,
  level 0, 31 x 3440 x 2060 (manifest entry 18).
- Pseudo-labels: the organizers' 2026 prediction (new_canon_autoresearch_recipe, 2.215 um scan) rescaled onto the 8.64 um
  canvas by tools/master/build_data.py; shard /dev/shm/shards/PHerc0343P_20250511003658.npz (--stride 48 --max 600; 600 crops
  of 64 x 64, 299 with ink (49.8 %); sha256 e680c6ba...; identical rebuild after the container restart).
- Scoring: tools/master/baseline_eval.py at the shard's crop positions (pixel AUC, pixel AP, tile AUC of the crop p95 vs
  crop-contains-ink), the same metrics as the ink_9um baseline lane.

## Mismatches between the model's expected input and this surface volume
1. Voxel size: the model requires 9.6 um isotropic; the volume is 8.64 um isotropic (ratio 0.9, a 10 % scale error, which
   hecate.py refuses on the CLI: it allows 2 %). Handled by resampling the whole render by 0.9 on all three axes
   (scipy.ndimage.zoom, trilinear, grid_mode so the output pitch is exactly 9.6 um): 31 x 3440 x 2060 -> 28 x 3096 x 1854
   (resample.json). The 2-D map is mapped back to the 8.64 um canvas by bilinear upsampling for scoring.
2. Depth: the model reads 16 planes = 153.6 um at 9.6 um. The 8.64 um render has 31 planes = 268 um; after resampling 28
   planes = 269 um, of which the central 16 (planes 6..21) are read; the outer 6 planes on each side are ignored. At native
   spacing 16 planes would be only 138 um, i.e. a 10 % thinner slab than the model was trained on.
3. Depth orientation: unknown for the organizer renders versus Hecate's training convention; both directions are run and
   reported (forward, reverse, and their mean as in the ink_9um lane).
4. Scan: PHerc0343P 8.64 um / 116 keV / 1.2 m is an ESRF native coarse scan; the model card says native coarse renders were
   introduced during training alongside downsampled fine CT, with blur/contrast augmentation. Whether this scan setting was in
   its training mix is not stated.
5. The vesuvius package entry point rejects the checkpoint (`Unsupported model_type 'multiteacher_3d_projection'`,
   vesuvius_infer_rejects_hecate.log), so the released standalone runtime is the inference path.
6. Compute: ~1.8 s per 16x64x64 patch at fp32 on 4 CPUs (AMX bf16 would be 2.5x faster but is not the published CPU recipe).
   The container was restarted twice during the run; tools/master/hecate_tiled.py re-implements hecate.predict() with atomic
   checkpoints (byte-identical to hecate.py on a real sub-volume in both directions and across a kill/resume, tiled_identity.json).

## Scores (pixel AUC / pixel AP / tile AUC; 600 crops; bar (i) is AUC >= 0.90 and AP >= 0.50 for OUR model, recorded here for comparison only)
| run | pixel AUC | pixel AP | tile AUC (p95) |
|---|---|---|---|
| Hecate 9.6 um, 9.6 um resample, forward (model recipe) | 0.731 | 0.390 | 0.652 |
| Hecate 9.6 um, 9.6 um resample, reverse (model recipe) | 0.551 | 0.153 | 0.520 |
| mean of forward and reverse | 0.709 | 0.323 | 0.636 |
| Hecate 9.6 um, NATIVE 8.64 um crops fed as 9.6 um, forward (mismatch experiment, one patch per crop) | 0.724 | 0.379 | 0.675 |
| same, reverse | 0.594 | 0.172 | 0.531 |
| (context) HERCULES master global_r1, same shard (DECL-FL-7-A1) | 0.579 | 0.167 | 0.575 |
| DECL-FL-7 bars (i)/(iii) for OUR model | >= 0.90 | >= 0.50 | >= 0.85 |

Whole-segment control (1.5 M valid pixels, label base rate 0.076): forward AUC 0.758 / AP 0.280; reverse 0.576 / 0.088; mean 0.734 / 0.219.

## Reading
- Depth orientation: forward is the informative direction for the organizer renders (AUC 0.73 vs 0.55 reverse; the reverse
  map carries almost none of the pseudo-label structure, see hecate_rev_q4.png); averaging the two only dilutes the forward map.
- The 10 % spacing mismatch is NOT what limits the model here: native 8.64 um crops fed as 9.6 um score within 0.01 AUC /
  0.01 AP of the faithful 9.6 um resample (0.724/0.379 vs 0.731/0.390; the tile AUC is even slightly higher without blending).
- Against the organizers' 2026 pseudo-labels on this held-out scroll, Hecate 9.6 um reaches pixel AUC 0.73, AP 0.39, tile
  AUC 0.65-0.67: clearly above our master model (0.58 / 0.17 / 0.58, DECL-FL-7-A1) and clearly below the DECL-FL-7 bars
  (0.90 / 0.50 / 0.85). A public model trained at this resolution does not reach the bars on this scan either; the bars stand.
- Caveats on the comparison: the pseudo-label is itself a model output on a different scan of the same segment (2.215 um,
  111 keV) and is visibly noisy (pseudolabel_q4.png), so the ceiling of any 8.64 um model on this metric is < 1; the whole-
  segment control (AUC 0.76 on all valid pixels) shows the crop-based numbers are not a sampling artefact. The quarter-size
  maps are published for the owner's eyes; no letters are claimed from them.
- The ink_9um (hybrid_3d2d seed42) comparison of item 3(ii) is a separate lane (lane_baseline.sh); its result is not in this record.
