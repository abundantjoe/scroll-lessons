# X3 gate 0 (DECL-UNR-1 item 5): existence test of a recto/verso fibre-orientation alternation, PHerc0268 level 0

Provenance: Project HERCULES | [id removed]. Tool: `tools/unr/x3_gate0.py`. Measurement only: no letters, no readings, no recto/verso naming.

## Result: gate CLOSED (both the primary and the secondary analysis)

- Data: 8 declared level-0 windows (128 y x 1024 z x 1024 x each, 134 MB, 15-21 s per fetch at 1 thread), 1.07 GB of raw CT; 265 laminae tracked.
- Primary (pre-declared bar, clean 64 x 64 tiles with >= 80 % clean columns): 1 clean sheet of 265 (bar: >= 20). Its outer quartiles are at the null (A 0.124 vs p95 0.129; A 0.032 vs p95 0.134), dtheta 8 deg.
- Secondary (masked: tiles with >= 30 % clean columns, unclean columns zeroed in data and nulls alike): 175 usable laminae, alternation on 0 of 175 (0 %). Median outer-quartile angle difference 10.9 deg (null for the median: p50 41.1, p95 45.9); 122 of 175 differ by <= 20 deg, 13 of 175 by 90 +- 20 deg. Where both outer quartiles are above the isotropised null (68 laminae) the differences are 0.1-22.8 deg: the two halves share ONE orientation. The gap controls 5 vox outside the sheet are more anisotropic than the sheet (gap A above the null on 66 % of laminae; gap A exceeds both quartiles on 70 %), so the anisotropy that exists is a pattern common to sheet, halves and gap (surface roughness of the lamina, the column mask, or residual reconstruction texture), not a fibre bilayer.
- Phase retrieval (metadata.json next to the volume's .zattrs; the .zattrs carries only axes/scales): Paganin, delta/beta 1000, unsharp coeff 4.0 sigma 1.2 (gaussian), padding edge; reconstruction GHBP, rotation axis 6071.75; 116 keV, 1200 mm. Derived Paganin length sqrt(lambda z delta/beta / 4 pi) = 31.9 um = 3.7 vox.

## What the laminae look like at 8.64 um (all 8 windows)
- Single-column FWHM of the tracked laminae: p10/50/90 = 7.5 / 8.2 / 9.2 vox (65 / 71 / 80 um). On 8 x 8-column mean profiles (tilt-broadened) the FWHM median is 10.8-15.9 vox per window; peak spacing median 29-42 vox.
- The lamina surface is rough at the 10-100 um scale: rms height step 1.5 vox at 1-vox lag rising monotonically to 9-27 vox at 64-vox lag; a smooth tracked map leaves a 4.6 vox rms residual (median over laminae). Within a tracked lamina 98 % of columns have a gap on both sides, 76 % have FWHM 5-20 vox, 85 % prominence >= 1.5 MAD, 70 % height residual <= 2 vox; the best 64 x 64 tile of a lamina has a median clean fraction 0.56 (p90 0.73). This, not the detector, is why the pre-declared clean-sheet bar is not met.
- Two outer quartiles of an 8-vox lamina are 2 vox thick and 6 vox apart: 1.6 Paganin lengths. The depth discrimination is marginal but not void (see controls).

## Controls (same pipeline, `phantom_*.json`)
- bilayer (13 vox, blur 1, contrast 0.08): alternation 10/10, median dtheta 89.1 (null p95 of the median 67.2), q0 theta ~0 (along x), q3 theta ~90 (along y), tracking error 0.15 vox, gaps at the null.
- same-angle negative: alternation 0/10, median dtheta 0.7. isotropic negative: A at the null (median 0.027 vs p95 0.052; 10-20 % of bands above p95, so the isotropised null is mildly anticonservative), dtheta scattered (median 33).
- sensitivity at the real thickness and blur (10 vox, blur sigma 2.0): contrast 0.08 -> 10/10, median dtheta 85.1; 0.04 -> 10/10, 85.7; 0.02 (texture 0.4 x the noise sigma) -> 8/10, 83.2. An 8-vox phantom is not seedable under the declared 10-18 vox seed class (its 8 x 8 profile FWHM is 8.7); real laminae were seeded because tilt broadens their mean profiles.
- The literal phase-randomised null (same |F|, random phases) reproduces the data's A and theta by construction (phantom: A 0.67 vs 0.69; real: median dtheta 7.9 vs 10.9): it tests nothing about anisotropy, which is why the isotropised surrogate is the null of record.

## Calibration record (changed after seeing lamina widths and roughness in window 1, before any spectrum was computed; in `gate0.json` under `calibration_record`)
column width class 8-20 -> 5-20 vox; column prominence 3 -> 1.5 MAD (3 MAD kept at the seed); spectral tile 128 -> 64 vox; tile clean fraction 0.9 -> 0.8; sheet needs 4 (of 32) clean tiles; seed neighbour rule = edge-to-edge gap >= 4 vox; height map = two-pass (smooth track, then a 5 x 5 median of per-column midpoints that the bands follow). The orientation statistic, annulus (wavelengths 4-32 vox = 35-277 um), nulls, quartile definition and gate rule are unchanged.

## Files
`gate0.json` (full record, per window and per lamina), `gate0_montage.png` (the one primary clean sheet), `gate0_montage_masked.png` (4 masked laminae), `gate0_run.log`, `phantom_*.json/png/log`.
