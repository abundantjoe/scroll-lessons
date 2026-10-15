Provenance: Project HERCULES | owner the owner | [id removed]

# P4-OWN RECIPE — DRAFT (DECL-P4-23 item 4). NOT FROZEN.
This draft fixes everything that does not depend on the labels. The frozen file is RECIPE.md with RECIPE.md.sha256,
pushed after the patch build and before any full training step or map. Items marked PENDING are filled only from
numbers the build produces: counts, hashes and tile lists. No design choice is left open.

## 1. Zones and data (DECL-P4-23 items 1-3)
- X: w010-027 strip-a tiles c9-c19, all rows. It is never read for training. The loaders refuse any label or mask file of an X tile.
- T: p4-excl certification a4ea355 (T_cert.json; independent check all pass).
  - w010-027 T_px 8343; w028-037 T_px 8301.
  - Only strip px inside certified x4 mask pixels are used (>= 1.2 mm 3-D from every X mesh point).
- Input: 2.4um-0.22m-78keV-volume-20260411134726, level 0, slices 23..84, forward order, clip(0,200)/255, mesh-valid mask.
  - Reader: ckpt-screen-b p4o_tiles.py at 98cd075; its sha256 is checked at import.
  - No other normalisation statistic exists. BatchNorm statistics come from T patches only.
- Labels: organizer 20260918 ink labels, mapped onto T by p4-excl label_shards.py (x4 per-tile grid, bilinear UV, n_sub 1). No teacher labels.
- Training patch:
  - 256 x 256 px input window. Its whole window must be in certified T and never touch X.
  - Loss core: the central 192 x 192 px, placed on the 192-px grid aligned at canvas (0,0).
  - Kept if the core is >= 50 % mesh-valid and >= 25 % label-covered (sup & mesh-valid).
- Cap: 4000 patches. Ink patches (core ink >= 2 %) are kept first; the rest are drawn with default_rng(20260927).choice.
  - Geometry-only candidates: 195,139 windows (geocount.json).
- Feasibility (item 2): 64 x 64 cells, (sup & mesh-valid) >= 50 %, ink >= 2 % of covered px. INFEASIBLE if < 2000.
  - Result: PENDING.
- Data build command:
  `build_patches.py --excl <p4own dir> --out /work/own/data --patch 256 --core 192 --max-patches 4000`
  - PENDING: build_manifest.json sha256 and patch counts.
  - Workers rebuild with `--verify` against that manifest.

## 2. Architecture (timing.json sha256 8e15f9db..., cfg A)
- 3-D-to-2-D CNN, random init, 232,697 params (<= 5 M). No pretrained weights.
- 3-D encoder:
  - Conv3d 1->8, k (5,3,3), s (2,2,2)
  - Conv3d 8->16, k 3, s (2,2,2)
  - Conv3d 16->32, k 3, s (2,1,1), + residual 3x3x3 block
  - Conv3d 32->32, k 3, s (2,1,1), + residual block
  - BatchNorm and ReLU throughout.
- Depth collapse: concatenated max and mean over depth.
- 2-D head: 1x1 conv to 32 channels, 4 residual 3x3 blocks with dilation 1, 2, 4, 8, then a 1x1 conv to one logit.
- Output stride 4 (9.6 um). Receptive-field radius 151 px.

## 3. Training
- Loss: masked BCE-with-logits + soft Dice (smooth 1), weight 1:1, at stride 4.
  - Target: mean ink over each 4x4 block.
  - Mask: 4x4 blocks fully covered by (sup & mesh-valid) inside the 192-px core.
- Optimiser: AdamW, lr 1e-3, weight decay 1e-4, 100 warm-up steps then cosine to 0, grad-norm clip 1.0. fp32, 4 CPU threads.
- Batch 16, 2500 steps (timing: 2.70 s/step, about 2 h/arm).
- Sampler, drawn up front from SeedSequence(seed) child streams:
  - Each batch is 8 patches from the ink pool (ink >= 2 %) and 8 from the rest.
  - Draws are epoch-wise permutations without replacement.
- Augmentation, per sample: flip-y, flip-x, in-plane rot90 k in 0..3, gain U(0.9,1.1), offset U(-0.02,0.02). No depth jitter; the slices are fixed.
- Seeds:
  - F1, F2, F3, S1 and NULL use 20260927.
  - S2 uses 20260928; S3 uses 20260929.
  - Torch init uses torch.manual_seed(seed).
- Checkpoints every 15 min; resume after a kill is bit-identical (tested).

## 4. Arms (item 5)
- F1-F3 (3 folds):
  - The 229 certified T tiles (T_cert certified_fraction > 0), ordered by (strip, column, row), are cut by np.array_split into 3 contiguous groups (recipe.json fold_groups):
    - G1: 77 tiles, w010-027 r0c0 .. w028-037 r0c4
    - G2: 76 tiles, w028-037 r1c4 .. r4c12
    - G3: 76 tiles, w028-037 r5c12 .. r8c20
  - Fk trains on the patches whose input windows touch only tiles of the other two groups. Patches straddling two groups are excluded from every F arm.
  - Fk predicts group k's held-out tiles. PENDING: the list = held-out tiles with >= 1 labelled px, by labelled px descending, capped at 24 per fold (~2 h).
- S1-S3: all patches, 3 seeds. Each predicts the X tiles r0-r7 x c9-c19 in this order:
  1. col. -1: r0c11, r0c12, r0c13, r1c11, r1c12, r1c13;
  2. r0-r5 x c14-c17, row-major;
  3. the rest of r0-r7 x c9-c19, row-major.
- NULL: the S1 recipe with each patch's labels (ink, sup) replaced by those of patch perm[i].
  - perm = numpy default_rng(20260927).permutation(n), redrawn until it has no fixed point (D3 NULLA convention).
  - PENDING: n and the sha256 of perm.
  - NULL predicts the same X tiles as the S arms.

## 5. Inference and display (identical to P4-O)
- Window 1024 px with a 160 px halo (>= receptive field; windowed = whole-image, tested diff 0.0).
- sigmoid, then bilinear x4 upsampling to canvas px, then u8 = clip(p*255) truncated. 0 outside mesh-valid.
- cv2.INTER_AREA to 1068 px, PNG (IHDR/IDAT/IEND).
- Each record carries png_sha256, valid_fraction, stats, train_manifest_sha256, model_final_sha256, min_dist_to_X_mm (tile) and train_min_dist_to_X_mm.
- End-to-end tile timing: 4.89 min.

## 6. Validation (item 6), computed before any X tile is read
- Held-out pixel AUC (auc.py; Mann-Whitney on u8, ties 0.5): F1-F3 on their held-out tiles, and NULL on the same px.
- col. -1 arrays (npz) are pushed for p4-excl's AUC (DECL-P4-21-A1).
- Census, G1, (c) and (d) are done by the harness and the orchestrator as declared.

## 7. Code sha256 (at draft time; re-listed in the frozen RECIPE.md)
own_common.py 96ce5aae..., build_patches.py e7a6fc0f..., train.py 2943cac4..., infer.py 36a64e1a..., auc.py 927f937c...,
test_own.py 65d8cac6..., recipe.json 25de8da7... (full hashes in the frozen file).
