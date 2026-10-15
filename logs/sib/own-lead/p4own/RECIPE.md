Provenance: Project HERCULES | owner the owner | [id removed]

# P4-OWN RECIPE (DECL-P4-23 item 4). FROZEN.
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

## 8. Frozen build numbers (recipe_final.json, sha256 7b484b80185c4e10ca39f7678d4a4d0feef4acdc1c1b0f17b51099ea7d64c993)
- Feasibility: 45262 ink 64-px cells (labelled 143474); bar 2000; feasible=True.
- Patches: 4000 kept (qualifying count not recorded: the manifest step was re-run with --manifest-only after a crash; the kept list is deterministic and every worker rebuild verifies it); ink patches 4000; 17.04 GB (workers rebuild and verify).
- build_manifest.json sha256 c567393deaddaa5734f600fa554d6c97703ba9826e9a73632211337275233379; patches.json sha256 c97a11fd6b3885373e85ff32f33f29e1e553ef10fc577473cffff685b14feb7c.
- NULL derangement: n 4000, sha256 70cad01901b990b2aa5fdf4429c0364339571aaa55593f46f63f960d9ee96e67, fixed points 0.
- Training patches per arm: {'S': 4000, 'F1': 3365, 'F2': 1230, 'F3': 3359}.
- F1 held-out tiles (24): w028-037:4,1; w028-037:3,0; w028-037:1,1; w028-037:0,3; w028-037:1,3; w028-037:1,0; w028-037:0,1; w028-037:5,0; w028-037:1,2; w028-037:5,1; w010-027:2,0; w028-037:0,4; w028-037:4,2; w010-027:2,1; w028-037:5,3; w028-037:4,3; w028-037:3,1; w028-037:0,2; w010-027:4,4; w028-037:2,2; w028-037:3,2; w028-037:4,0; w010-027:5,3; w028-037:2,1
- F2 held-out tiles (24): w028-037:1,10; w028-037:2,9; w028-037:1,11; w028-037:2,8; w028-037:1,12; w028-037:5,8; w028-037:1,9; w028-037:3,6; w028-037:3,12; w028-037:4,8; w028-037:0,5; w028-037:2,10; w028-037:3,5; w028-037:5,6; w028-037:2,5; w028-037:1,5; w028-037:0,6; w028-037:0,10; w028-037:4,12; w028-037:5,5; w028-037:4,6; w028-037:1,6; w028-037:5,9; w028-037:1,8
- F3 held-out tiles (24): w028-037:3,14; w028-037:1,13; w028-037:1,14; w028-037:5,14; w028-037:3,13; w028-037:1,15; w028-037:4,13; w028-037:3,19; w028-037:3,15; w028-037:2,20; w028-037:5,20; w028-037:5,13; w028-037:3,20; w028-037:4,20; w028-037:3,16; w028-037:1,16; w028-037:2,16; w028-037:3,18; w028-037:5,12; w028-037:2,18; w028-037:5,16; w028-037:4,16; w028-037:5,15; w028-037:4,14
- Code sha256: own_common.py 96ce5aae47a410de315389753bcf32dc2cc0331e62b862e7aa10440e12227d4b, build_patches.py 2ce23be8c0890838468ce1818b4e6e1e357f09e6d0ea73f2787d812e1b614829, train.py 2943cac435c2a9b425eae794708bf18dbec2abc033da5a2fd283fc991052a0f3, infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e, auc.py 927f937c68aa7833f66e79fa74cb415c2bfb1cc6b7e8856aab8f26f5965494d2, test_own.py a73b4711040211f28c97e5c7a1811e6b2447ce3a65de67d5c1c2521d58ce738a, finalize_recipe.py d273bb1a8b1d20ad950e30d6026cf62e99127655b47574299e625413fc53adce
- recipe.json sha256 25de8da77e1e1bad539181dafcb9a95af73213af3557a1d216c9fe84b962bdad

## 9. Disclosures (fixed at freeze)
- The cap binds on ink patches alone: all 4000 kept patches have core ink >= 2 %.
  - Consequence: the non-ink sampler pool is empty, so every batch is drawn from the ink pool (train.schedule single-pool branch).
  - Non-ink pixels still dominate within the patches.
- F2 holds out the densest group (G2), so it trains on only 1230 patches (~33 passes over 2500 x 16 samples); F1 has 3365, F3 3359.
  - Reported as is; no bar depends on it.
- No spatial buffer separates the fold groups beyond the whole-window rule (input windows touching two groups are excluded). Adjacent windings may make the F AUCs optimistic.
- min_dist_to_X_mm = 1.2 is the certified lower bound from p4-excl (per-cell rule, independent check all pass), not a measured minimum.
- Workers rebuild the 17.04 GB patch set from S3 (about 1 h) and verify every shard sha256; keep >= 5 GB free.
- Arm training uses these files at the RECIPE commit: tools/sib/own-lead/{own_common,build_patches,train,infer,auc}.py and logs/sib/own-lead/p4own/recipe.json.
