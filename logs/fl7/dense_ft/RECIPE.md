# DECL-FL-7-A1: dense_native fine-tune on PHerc0009B at 8.64 um (RECIPE and RESULT)

**Result: no fine-tuned step improved the held-out AUC; the kept checkpoint `master_dn_ft.pt` is the base weights (step 0).** Held-out pixel AUC fell from 0.698 (step 0) to 0.63-0.68 at every evaluation from step 250 to 2000 while the training loss stayed flat (Dice ~0.65-0.88). This matches the model card's own negative result for fine-tuning this family on sparse single-scroll labels. The bars (AUC >= 0.90, AP >= 0.50, tile AUC >= 0.85) are not met by any checkpoint. No letters are claimed.

## Base weights
- Nieuwlaar/ink9um-dense-native @ b894a0493ab2291cc8dc3247020c0d7cb0967a58, `weights/dense_native_016000.safetensors`, sha256 `d3d95dc41dcb24ed76b84b5e12ca5dae25d7fb34edf1dfbb93e0186f91e6fc6d`
- .pth payload (model + training/configs/train_dense_native.json + step 16000): sha256 `301caa0b02e2aa2d6071573ebb4a282ec72bdf9dc864c6dd11bc45b435ed457e` (logs/fl7/baseline_dense/.../recipe.json)
- Architecture: vesuvius_unet_3d_stem_2d (depth_fusion 3-D stem -> 2-D UNet, 6 stages, InstanceNorm, 128 px training patches, must be divisible by 32; 64 px crops are)

## Training (tools/master/ft_dense.py, commit in this branch)
- Trainable: `network.shared_decoder.*` + `network.task_heads.*` = 4,322,465 params; frozen: `network.shared_encoder.*` + `depth_fusion.*` (the 3-D input stem is counted with the encoder) = 30,224,033 params
- AdamW lr 1e-4, weight decay 1e-2, batch 4, fp32, 4 CPU threads, seed 0, no augmentation, no LR schedule; loss = BCE-with-logits + soft Dice (batch-level, smoothing 1) on target (y > 127)
- Steps: 2000 (the declared maximum); evaluation at step 0 and every 250 steps on the held-out shard; the kept checkpoint = best held-out pixel AUC among all evaluations including step 0
- Step time: 0.2492 s mean over the first 20 steps -> 0.138 h projected for 2000 steps (limit 6.0 h; not abandoned); wall time 725.7 s including 9 evaluations
- Input adapter (identical to the baseline scoring recipe, villa 41701aa flat inference): the 31-layer crop is center-cropped to the 17 layers 7..23 (`select_layer_indices`), placed centered in a 17-deep stack (`centered short-depth placement`, a no-op at 31 layers), and robust-normalized per crop (`tifxyz_robust`: median/MAD, p1-p99 clip). Note: the shards carry 31 layers (manifest), not 16; the same adapter would zero-pad a 16-layer stack to 17.
- Training data: the 18 PHerc0009B shards below (`tools/master/build_data.py --stride 48 --max 600`, level 0, 600 balanced 64 px crops each = 10,800 crops; organizer 2026 2.4 um pseudo-labels rescaled INTER_AREA to the 8.64 um canvas). All 18 manifest entries built here (the declaration says 17; none failed). Never PHerc0343P; no parchment or vellum data.

  - PHerc0009B_20250510172639.npz
  - PHerc0009B_20250510172804.npz
  - PHerc0009B_20250511200236.npz
  - PHerc0009B_20250919064353.npz
  - PHerc0009B_20250919123506.npz
  - PHerc0009B_20250919124722.npz
  - PHerc0009B_20250919124917.npz
  - PHerc0009B_20250919125302.npz
  - PHerc0009B_20250919125605.npz
  - PHerc0009B_20250919125754.npz
  - PHerc0009B_20250919130642.npz
  - PHerc0009B_20250919131352.npz
  - PHerc0009B_20250919131642.npz
  - PHerc0009B_20250919132115.npz
  - PHerc0009B_20250919133208.npz
  - PHerc0009B_20250919135433.npz
  - PHerc0009B_20250919135915.npz
  - PHerc0009B_20250919140325.npz

## Held-out evaluation (PHerc0343P 20250511003658 shard, 600 crops, eval_master.py semantics on isolated 64 px crops)

| step | pixel AUC | pixel AP | tile AUC (mean prob) | tile AUC (p95) | train loss |
|---|---|---|---|---|---|
| 0 | 0.6977 | 0.2969 | 0.6256 | 0.6319 | - |
| 250 | 0.6762 | 0.2950 | 0.6223 | 0.6187 | 1.2418 |
| 500 | 0.6488 | 0.2850 | 0.6380 | 0.6365 | 1.3401 |
| 750 | 0.6555 | 0.2697 | 0.6022 | 0.6041 | 1.2372 |
| 1000 | 0.6389 | 0.2625 | 0.6081 | 0.6102 | 1.1071 |
| 1250 | 0.6335 | 0.2703 | 0.5946 | 0.5965 | 0.9896 |
| 1500 | 0.6460 | 0.2700 | 0.6117 | 0.6167 | 1.2755 |
| 1750 | 0.6534 | 0.2804 | 0.5963 | 0.5974 | 1.3214 |
| 2000 | 0.6509 | 0.2714 | 0.6122 | 0.6138 | 1.3198 |

Kept: step 0 (base weights), pixel AUC 0.6977, AP 0.2969, tile AUC 0.6256. `master_dn_ft.pt` sha256 `dd1788ec62d27280f09035f5188d22fca29b73bffd9fca39c2661fb35aa26b0c` (132 MB; NOT in git: GitHub rejects files over 100 MB, so the file stays at /work/ckpt/dense_ft/master_dn_ft.pt on the lane and only its sha256 is committed, as the declaration provides for an oversized checkpoint; payload {model, config, step, base, metrics, train_shards}, loadable by villa's infer CLI).

## Measurement note: per-crop evaluator vs full-map recipe
The same base weights score pixel AUC 0.7605 / AP 0.4082 under the baseline full-map recipe (128 px patches, overlap 0.5, Hann blending, scored at the same crop positions; logs/fl7/baseline_dense) but 0.6977 / 0.2969 on isolated 64 px crops here: per-crop normalization statistics and the missing 32 px context around each crop cost ~0.06 AUC. The per-crop numbers in the table are comparable with each other and with eval_master.py on the from-scratch control; the full-map number is the one that applies to pipeline use.
Round-trip check: the kept checkpoint run through the full-map recipe scores pixel AUC 0.7605 / AP 0.4082 / tile AUC p95 0.6884 (fullmap_fwd.json), reproducing the baseline 0.7605 / 0.4082 / 0.6884 exactly (identical scores).

## Reading
- Under the declared protocol the fine-tune is a recorded negative result: the decoder+head adaptation to the 8.64 um pseudo-labels does not transfer to the held-out scroll; the training loss does not fall either (the frozen encoder features plus a 1e-4 decoder update do not fit the pseudo-labels in 2000 steps at batch 4).
- The kept model equals the public base model; if used in the ink stage its measured held-out numbers (full-map AUC 0.760 / AP 0.408 / tile AUC 0.688; per-crop 0.698 / 0.297 / 0.626) go beside every output, below the bars, as item (4) requires.
- Not done (not declared): unfreezing the encoder, a learning-rate schedule, augmentation, longer runs, or evaluation of the step-2000 weights under the full-map recipe (only the best checkpoint was kept).
