Provenance: Project HERCULES | owner the owner | [id removed]

# Pre-registration: PHerc0500P2 9.362 um <-> 2.215 um registration (task ktlb4p-prep, step 3)

Committed and pushed BEFORE any level-0 block is read. Only 9 um level 3 and 2.215 um level 5 CT have been read so far (coarse_check.json, patch_plan.json). No ink model, no ink map, no image viewed.

Patch plan: `logs/sib/ktlb4p-prep/reg/patch_plan.json`, sha256 `31b0b84b74d4a5f9e65e8491911d9639c46bfdb834706a63fa45319d118b3be9`. It has 40 sites: 24 fit and 16 held-out (NEW for this scroll), each a 48 x 256 x 256 block of 9 um level-0 voxels.

## Held-out patches (16)

| id | centre (x, y, z), 9 um level-0 vox |
|---|---|
| P01 | [1920.0, 1408.0, 1648.0] |
| P02 | [2688.0, 1920.0, 3808.0] |
| P03 | [1408.0, 1408.0, 2752.0] |
| P04 | [2816.0, 2048.0, 4912.0] |
| P06 | [768.0, 1536.0, 4384.0] |
| P08 | [640.0, 1408.0, 5200.0] |
| P10 | [2176.0, 1664.0, 2224.0] |
| P11 | [2688.0, 2048.0, 4336.0] |
| P15 | [2176.0, 1920.0, 5296.0] |
| P16 | [2176.0, 2048.0, 5968.0] |
| P19 | [2560.0, 1792.0, 2896.0] |
| P26 | [2048.0, 2048.0, 5680.0] |
| P31 | [3200.0, 2048.0, 5248.0] |
| P33 | [1664.0, 1792.0, 3760.0] |
| P35 | [1024.0, 1280.0, 3616.0] |
| P37 | [768.0, 1536.0, 4144.0] |

## Measurement (frozen)

**Model form.** q2 = A p9 + c. Level-0 voxels, (x, y, z). The 2.215 um volume is read at pyramid level 1 (4.430 um, an exact 2x2x2 mean). Level-1 index = (q0 - 0.5) / 2.

**Prefilter (the C6 sigma).** C6 specifies a prefilter of F0/2 level-0 vox, with F0 = 9.362 / 2.215 = 4.2266. Here that becomes sqrt((F0/4)^2 - 0.25) = 0.93 level-1 vox, plus the 2x2x2 mean. This is a disclosed deviation: level 1 is used instead of level 0 to fit the disk allowance.

**Correspondence per patch** (reg0841 `reg_core`):
- Iterate a 3-D phase correlation of the 9 um block against the prefiltered rescan, resampled (trilinear) through the model, until the step is below 0.02 vox. Hann window, parabolic sub-voxel peak.
- Residual d9 = the converged shift, in 9 um vox.
- r = NCC of the raw 9 um block and the resampled rescan at ZERO shift under the model.
- Control: r_ctrl at a shift of half the local sheet pitch along the sheet normal (structure tensor plus autocorrelation), reported as a drop r - r_ctrl.

## Model selection: on the 24 FIT patches only, frozen before any held-out block is read

1. Affine, 2 passes, starting from the organizer affine 20250820143440 -> 20250526151718.
2. If the affine's leave-one-out RMS on the fit patches is <= 1.5 vox (9 um), the final model is the affine.
3. Otherwise, try affine + quadratic field (21 parameters: x^2, xy, y^2, xz, yz, z^2 terms are NOT all used; exactly the reg0841na form: affine plus x^2, xy, y^2 in all 3 components). Select it only if its leave-one-out RMS is lower than the affine's. Otherwise keep the affine.
4. The selected model is written to `model_final.json`, committed and pushed. Only then are the held-out blocks read.

## Bars (16 held-out patches, final model, evaluated ONCE)

| Bar | Threshold |
|---|---|
| median r | >= 0.85 |
| RMS of abs(d9) | <= 1.5 vox (9 um) |
| control, reported and required | median drop >= 0.30, and >= 14 of 16 with r_ctrl < r - 0.15 |

- PASS requires all three.
- If any bar fails: FAIL is reported. No bar and no patch is changed. Any second attempt needs 16 NEW patches, pre-registered anew.

