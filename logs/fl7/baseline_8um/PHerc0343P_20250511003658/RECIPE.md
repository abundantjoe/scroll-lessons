# DECL-FL-7 item 3(ii): public ink-8um-v8in on the held-out scroll (PHerc0343P, manifest entry 18)

Provenance: Project HERCULES | [id removed]. Sibling base-8um. No letters are claimed; these are detector scores against organizer pseudo-labels.

## What was run
- Model: Hugging Face `YoussefMoNader/ink-8um-v8in`, revision `d89166b41a3f5fad7749b3d7c0fdd1bd3695d844` (2026-09-28), MIT.
  `model.safetensors` sha256 `3b94548d7f9ba9f99bc4b0ad8cafcec6d42585c06304e1bd11e47b5d0f88c4cd` (also in every run record as
  `weights_sha256`); config in `v8in_config.json` (tile 64, in_depth 24, stride 21, clip_max 200, resample 96x256x256,
  reverse_layers false). 83,317,827 parameters, loaded `strict=True`.
- Code: the repository's own `predict.py` / `ink8um/` could not be downloaded into this container (external code refused by the
  session's permission policy), so `tools/master/v8in_infer.py` re-implements the network and the released full-surface recipe
  from the public model card, `config.json`, `ink8um/modeling.py` and `ink8um/inference.py` (read, not executed). Any divergence
  from the public code is ours; the strict parameter-name match and the recipe constants were checked line by line.
- Input: organizer surface volume `PHerc0343P/segments/20250511003658-tifxyz/surface-volumes/8.64um-1.2m-116keV-volume-20250521134555.zarr`,
  level 0, shape (31, 3440, 2060) uint8. The model takes 24 layers: the centred 24 (layers 3..26 of 0..30) as the public
  `read_stack` does for a deeper stack. Intensities clipped to [0, 200] and scaled by 1/255. Depth order is unknown for this
  render, so both orders were run (`fwd` = organizer order, `rev` = `--reverse`), as the model card advises.
- Labels: pseudo-labels of the shard built by `tools/master/build_data.py PHerc0343P 20250511003658-tifxyz <sv> <out> --stride 48 --max 600`
  (organizers' 2.215 um new_canon_autoresearch_recipe prediction rescaled onto the 8.64 um canvas; 600 crops, 485 of 1751
  candidates contain ink, 49.8 % of the selected crops contain ink, label mean 0.246). Scored with `tools/master/baseline_eval.py`.
- Compute: 4 CPU cores, fp32 (the release used fp16 autocast on CUDA; CPU bf16 was measured at mean |dp| 4e-4 / max 2.5e-3
  against fp32 under autocast and gave no speed-up, so fp32 was kept). About 7 s per 64x64x24 tile.

## Two scorings
1. `per_crop` (exact alignment): the model is applied to the shard's own 600 crops (one tile each, no stitching) and scored crop
   by crop (`baseline_eval.py` on a `.npy` stack). This is the model's raw tile output at the scored positions.
2. `full_surface` (released recipe): coverage mask (max over depth > 0, 7x7 ellipse closing), 64 px tiles at stride 21 fully
   inside the mask (8,924 tiles), sigmoid, Gaussian-weighted sum divided by the per-pixel tile count, clipped to [0, 1]; the
   resulting canvas map is scored at the crop positions exactly like the ink_9um baseline (`logs/fl7/baseline/`).
   At ~7 s per tile this is ~17 h per direction on this container, so it is run for the direction that scores better in (1)
   with a resumable checkpoint; the other direction's full map is not produced here.

## Input mismatch (reported, not corrected)
- Voxel size: the v8 patch pack is rendered at ~8 um (Scroll 1 / 5, PHerc1667, 0139, 0814, 0500P2, one fragment); this volume
  is 8.64 um (ESRF 116 keV, 1.2 m), i.e. the 24-layer window spans 207 um here versus ~190 um in training.
- Window: the organizer render has 31 layers; the model sees the central 24 (3 unused on one side, 4 on the other).
- Intensities: non-zero voxels of the 24 used layers have mean 78, p50 60, p95 142, p99 160; only 0.07 % exceed the clip of
  200 (6.7e-5 are 255). The clip therefore does almost nothing here, whereas the training renders were clipped meaningfully.
- Depth order: unknown; both orders are run and reported, neither is assumed.
- The pseudo-labels come from the organizers' 2.2 um model on the same mesh; they are not human marks (DECL-FL-7 item 2).

## Files
- `v8in_crops_fwd.json`, `v8in_crops_rev.json`: per-crop scores (pixel AUC, pixel AP, tile AUC p95, n_crops).
- `v8in_crops_<dir>.recipe.json`: run record (weights sha256, config, layer window, seconds, crop positions).
- `v8in_full_<dir>.json` + `v8in_full_<dir>.recipe.json` + `v8in_full_<dir>_q4.png`: full-surface recipe map scores, run record
  and quarter-size PNG (the float32 map itself stays outside git: /work/v8in/out/full_<dir>.tif, sha256 in the record).
- `pipeline.log`: timestamps. The container restarted at ~23:15Z on 2026-10-09; the first per-crop pass (started 21:54Z in
  /dev/shm) and this file's first entry were lost and the chain was restarted from /work with checkpoints (`/work/v8in/chain.sh`).

## Results so far (per-crop, 600 crops, fp32; full-surface pending)
| run | pixel AUC | pixel AP | tile AUC (p95) | DECL-FL-7 bar |
|---|---|---|---|---|
| v8in per-crop, organizer depth order (`fwd`) | 0.750 | 0.357 | 0.697 | 0.90 / 0.50 / 0.85 |
| v8in per-crop, reversed depth (`rev`) | 0.536 | 0.168 | 0.482 | |
- The reversed order scores at chance, so the organizer order is the one the model expects on this render; `fwd` is the
  direction carried into the full-surface recipe (started 2026-10-10 02:03Z, 8,924 tiles, ~17 h).
- The public model does not reach the DECL-FL-7 bars on this held-out shard in per-crop mode. These are detector scores
  against organizer pseudo-labels; no reading is implied.
