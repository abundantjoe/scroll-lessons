# PHerc0268 ink-detection plan (CPU-only, 8×4-core / 15 GB / 2 GB disk)

## 0. Ground truth about our regime

PHerc0268 is 8.64 µm / 116 keV / 1.2 m. Evidence for that regime:

- **Positive:** PHerc0343 (same 8.64 µm/116 keV/1.2 m, vol 20250521140437) was read on 8 Oct 2026 by z-score-averaging four 9 µm models (ink_9um s42+s43 step-75k, Hecate 9.6 µm, Nieuwlaar dense_native). PHerc1447 (8.64/116) also has letters (Bullo27 w058/w060 labels; v8in AUC 0.86/0.81, ink_9um 0.74/0.65).
- **Negative:** ink_9um alone gives speckle on PHerc0800/1203/0268 and most eligible scrolls; two naive 116 keV fine-tunes collapsed to chance; 2.4 µm-pooled renders do not behave like native coarse scans (canonical-model agreement r 0.93→0.32).
- **Lesson:** single models trained on pooled 2.4 µm data under-transfer; ensembles plus native-coarse training data are what worked. Our plan therefore (a) trains only on native 8–9.4 µm / 113–116 keV renders, (b) proves sensitivity on PHerc0343/1447 before touching 0268, (c) treats the 4-model ensemble as the baseline we must beat, not replace.

## 1. Data and labels (all public)

| Use | Scroll / asset | Voxel / keV | Labels |
|---|---|---|---|
| Train (same regime) | PHerc1447 w058/w060 | 8.64 / 116 | Bullo27 human-traced labels |
| Train | PHerc0343P fragment, PHerc0009B fragments | 8.64 / 116 | canonical-2 µm predictions (TAUIL, Jashann) — pseudo-labels, weight 0.5 |
| Train (near regime) | PHerc0139 native 13 renders | 9.362 / 113 | ink_9um manual labels + Nieuwlaar dense_native pseudo-labels (HF Nieuwlaar/ink9um-dense-native) |
| Train | PHerc0500P2 fragments | 9.362 / 113 | canonical predictions |
| **Held-out bar A** | PHerc0343 w047+w048, z 9500–11000 | 8.64 / 116 | Nieuwlaar meshes (CC BY-NC) + his published letter region; trace 8 letters by hand from his map |
| **Held-out bar B** | PHerc0841 segment 252405 | 9.366 / 113 | human labels (SirColton/liliandevarieux) |

Excluded: Paris 4 / 1667 pooled 2.4 µm renders (regime mismatch), Scroll 1 7.91 µm/54 keV, Scroll 5 53 keV. Everything is resampled to 8.64 µm isotropic in-plane and depth (9.362 → 8.64 is a 1.08× zoom; acceptable). Surfaces are rendered as 64-layer slabs (±32) so a one-layer mesh jump still keeps the sheet inside the slab.

Disk: 2 GB forbids local volumes. Each container streams 64³ crops from the ash2txt zarr via fsspec with a 600 MB LRU crop cache; labelled training crops are pre-cut once into a ~900 MB uint8 patch pack (≈3,500 crops of 5-ch 64×128×128 at 8-bit) and shared to the fleet. The v8 patch pack (≈50 GB) is only subsampled (~8k patches) for an ablation.

## 2. Model (owner's three strategies, scaled to CPU)

**fp16 caveat:** CPU autocast fp16 is slower than fp32 in PyTorch; bf16 autocast helps only on AVX512-BF16 hosts. We detect at start-up and use bf16 where available, else fp32. "fp16" is kept for the exported inference weights only.

**(3) Gradient/crackle channels (cheap, deterministic):** input = 5 channels: raw CT (÷255, clipped like Hecate 9.6), 3D Sobel x/y/z, 3D Laplacian (σ=1 LoG) which isolates phase-contrast edge halos, plus a crackle channel = local std of the top-hat residual in a 5³ window. Precomputed on the fly with scipy; <5 % of step time.

**(2) Native 3D U-Net (the single combined model):** residual 3D U-Net, 4 stages, channels 16-32-64-128, 3×3×3 convs, InstanceNorm, ≈1.6 M params. Input 5×64×128×128. Two heads: (i) 3D sigmoid logit volume; (ii) a Hecate-style learned depth attention that pools the 3D logits into a 2D map. Loss = Dice+BCE on the 2D map against the 2D label, plus BCE on the 3D volume against the label broadcast into a ±4-layer band around the attention peak (label smoothing 0.1, not 0.5 — avoids ink_9um's compressed output). z-jitter ±3 layers, flips, 90° rotations, intensity gain/blur augmentation (native scans are blurrier than pooled).

**(1) 3D DINO-style SSL, scaled down:** a ViT at dinovol's size is not CPU-trainable (one 128³ dinovol forward ≈2.5 TFLOP ≈100 s on 4 cores; a winding would take ~20 h), and dinovol was trained at 2.4 µm (3.6× finer than ours) with a prototype probe that an independent audit found adds nothing to a decent teacher. So: the SSL encoder is the U-Net's own 3D CNN encoder (≈0.9 M params), trained DINO-style (EMA teacher 0.996, centering + sharpening, 1,024 prototypes, 2 global 64³ views + 4 local 32³ views) on **unlabelled 8.64 µm crops from PHerc0268, 0343 and 1447** (domain-matched, 5-ch input). Optionally dinovol ps8 is run once on a 256³ ROI of 0343 to compare its cosine map against ours as a sanity check, nothing more.

**Combination:** supervised U-Net initialised from the SSL encoder, fine-tuned end-to-end. This is one model with gradient channels, depth-profile 3D decoding and SSL-initialised features.

## 3. CPU budget (numbers)

Assume ~25 GFLOP/s sustained per 4-core container for 3D convs (measure in the first hour; adjust batch).

| Job | Cost/step | Steps in 12 h | Data seen |
|---|---|---|---|
| SSL encoder, batch 8 × (2×64³ + 4×32³ views) ×2 (teacher) | ≈200 GFLOP ≈ 8 s | ≈5,000 | ≈40k crops (10 GB streamed) |
| U-Net supervised, batch 6 × 64×128×128 | ≈150 GFLOP ≈ 6 s | ≈7,000 | ≈42k crops ≈ 12 epochs of the patch pack |
| Inference, 64³ tiles, 0.5 overlap, Hann | ≈0.15 s/tile | — | one 20×50 mm winding (≈3,300 tiles) ≈ 10 min |

5k SSL steps is ~1.5 % of dinovol's schedule; expect modest features. It is run as an ablation, not an assumption.

**Fleet allocation (8 containers, 2 rounds of ≤12 h):**
Round 1: C1–C2 SSL (two seeds); C3 patch-pack build + resampling; C4 baseline eval (ink_9um ×2, Hecate 9.6, dense_native, z-score ensemble) on held-out A/B; C5–C8 U-Net from scratch: raw-only, +gradients, +gradients on v8 subsample, +gradients with pseudo-label weight 1.0.
Round 2: C1–C4 U-Net +SSL init (2 seeds × 2 variants); C5–C6 continued SSL; C7 held-out scoring + blind-reader packs; C8 PHerc0268 inference only after the gate below passes.

## 4. Sensitivity gate (before any 0268 scan)

Pre-registered, written to the repo before training finishes:

1. **Pixel AUC** vs human traces on held-out A (PHerc0343 w047/48 letters) ≥ 0.80 and on held-out B (PHerc0841 252405) ≥ 0.80, computed per segment, both depth directions, best-of-two reported with the other shown.
2. **Beat the baseline:** must exceed the 4-model z-score ensemble's AUC on A by ≥ 0.02, or we ship the ensemble as primary and ours as second opinion.
3. **Legibility:** SirColton protocol — two blind readers, 8 reference letters on A, ≥ 5/8 matched (ink_9um s43 got 0/8 on 9 µm; Hecate 2.4 got 6/8).
4. **Controls:** depth-shuffled input must give < 50 % of the real-order p>0.5 mass (aviad12g found Hecate fails this on 0800/1203); forward vs reverse AUC gap ≥ 0.15 on A; elongation of connected components ≥ 15 (blobs score ~11).
5. Anything failing → iterate on data/augmentation, never on 0268.

## 5. Producing a viewable 3D ink volume on imperfect surfaces

- Render 64-layer slabs per winding; keep the per-pixel (x,y,z) scroll coordinates from the renderer.
- Run the U-Net at 0.5 overlap with Hann blending; write three outputs per winding: (a) 3D probability in slab coords (uint8 zarr), (b) attention-pooled 2D map, (c) depth-argmax map (flags mesh layer jumps as discontinuities).
- Scatter (a) back into a sparse scroll-coordinate zarr (uint8, chunk 128³, ~2–6 GB streamed to S3-compatible store, not local disk). This decouples detection from the mesh: a corrected or re-flattened surface later re-samples the saved probability instead of re-running the model, and the same voxel gets consistent votes from overlapping windings.
- Viewing: neuroglancer / VC3D with raw CT + probability overlay; the depth-argmax map guides mesh repair at cracks.
- Final letter claims use (b) at the attention depth and ±3 layers; receptive field is kept ≤ 64 voxels so nothing can invent writing from context.

## 6. Top 5 risks and mitigations

1. **No usable ink signal in PHerc0268 at 8.64 µm/116 keV.** Mitigation: gate on 0343/1447 first, so a null on 0268 is reported as "no ink recovered yet" with a measured sensitivity bound, not a blank-scroll claim. Escalate to organisers for a 2.4 µm scan request.
2. **Pseudo-label inheritance / regime mismatch** (fine-tunes scored below base on 0139 w043). Mitigation: human labels (1447, 0841, 0139 manual) weighted 1.0, canonical pseudo-labels 0.5; held-out sets are human-traced only; ablation without pseudo-labels.
3. **CPU compute too small for SSL to matter.** Mitigation: SSL is an ablation; dropped if +SSL init does not beat scratch by ≥ 0.01 AUC on A and B; budget capped at 2×12 h.
4. **Mesh layer jumps at cracks produce false edges or lose the sheet.** Mitigation: 64-layer slabs, 3D output in scroll coordinates, depth-argmax diagnostics, crack-aware masking (Laplacian magnitude > threshold over ≥ 8 layers is masked from the 2D pool).
5. **Letter-like hallucinations and confirmation bias** (organisers warn distorted geometry yields "very letter-like" output). Mitigation: pre-registered gate, shuffle and reverse controls, elongation metric, blind readers, no training ever on the 0268 candidate region, ensemble disagreement map (ours vs 4-model z-score) published with any claim.