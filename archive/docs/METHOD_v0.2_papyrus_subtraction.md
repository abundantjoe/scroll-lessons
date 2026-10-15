# METHOD.md — papyrus-subtraction residual (route B). Version v0.2 (v0.1 = without the inpainting term).

Status 2026-09-16: parameters below are the calibration values in force; they will be FROZEN after GATE-T1/T2/F and
before any eligible scroll is read. Changes after that are only allowed as a new method version re-calibrated from scratch.

## Inputs
- Thick render I(u,v,k), uint8, k along the local normal, 96 slices at 2.4 µm (±48) or all available slices of a published surface volume.
- Pitch from the store's own metadata (`.zattrs` coordinateTransformations level 0); 1 cm bar = 10000/pitch px.

## 5.3 Faces (scripts/topo_faces.py)
- Gaussian smoothing σ = 1 slice (k) and 1 px (u,v) before the profile search.
- Per pixel: crest k* = argmax, peak; the bright band = the contiguous run around k* where the profile ≥ 50 % of peak;
  k_top / k_bot = its ends with linear sub-slice interpolation. Implementation choice (recorded before any run): the band is the one
  CONTAINING the crest, not the first 50 % crossing from the stack top, so a neighbouring winding inside the stack does not steal the face.
- valid = band not clipped by the stack ends, peak ≥ 24 (uint8), CT(mesh slice) > 0.
- Face intensities (k increases from the top face to the bottom face; outside the top face is smaller k):
  S_top = I(k_top − 1), D_top = I(k_top + 2), S_bot = I(k_bot + 1), D_bot = I(k_bot − 2) (linear interpolation in k).
- On-sheet = valid AND 30 µm ≤ t ≤ 380 µm (= the brief's 4–40 voxels at 9.362 µm, expressed in µm so the same physical bound holds at 2.4 µm) AND CT > 0.

## 5.4 Residuals (scripts/residual.py, scripts/inpaint_net.py)
- Relief r = sign·(h − G_{0.6 mm}(h)), normalised convolution over the on-sheet mask; sign = −1 for the top face, +1 for the bottom, so proud-of-sheet is positive on both faces.
- Fibre model: structure tensor of G_1(S) with σ = 6 px; fibre direction ⟂ dominant gradient; 12 orientation bins; oriented background =
  S smoothed along the fibre direction (σ_along = 1.0 mm, σ_across = 1.5 px, normalised convolution, rotate–filter–rotate back); e = S − background.
- Inpainting net: U-Net (2 input channels: masked S and hole mask; channels 16/32/64; 2 down-samplings; 110 k parameters), 64×64 crops,
  24×24 holes, MSE inside the hole, Adam 1e-3, batch 64, 6000 steps, seed 0; trained on the standardised S maps (both faces) of the target
  scroll's own charts only (never the submission window; no labels). a = |S − Ŝ| with Ŝ from a 4-phase 24×24 hole grid.
- Standardisation per chart: z = (x − median)/(1.4826·MAD) over on-sheet pixels.

## 5.5 Combination
- s = 0.5·z(r) + 0.3·z(e) + 0.2·z(a)  (v0.1: 0.625·z(r) + 0.375·z(e)).
- Damage mask (decided 2026-09-16 on text1's thickness maps BEFORE any AUC was computed; the brief's "|∇t| large" at pixel scale removed
  57 % of the sheet at 2.4 µm because it is fibre texture): tear/step = |∇(G_{0.1 mm}(t))| > 0.3 voxel/px, plus t < 30 µm, invalid, CT == 0;
  dilated by 0.4 mm. Grains: S > 99.9th percentile, component ≤ (0.1 mm)² → dilated 0.3 mm.
- Band-pass: DoG σ = 0.15 mm and 1.2 mm (normalised convolution over the mask); zero outside the mask.
- Outputs s_top, s_bot as float32 and uint8 = 255·clip(0.5 + s/8, 0, 1). Unaltered downstream.

## 5.6 Row test and units (scripts/gate_eval.py)
- Row profile = mean of s over masked pixels per image row (rows run across the writing lines), smoothed 0.1 mm; autocorrelation; first local
  maximum in the 2–4 mm lag band; positive if ≥ 0.25 on the writing face and < 0.15 on the other face and the CT mid-slice row profile's
  autocorrelation at the same lag < 0.25.
- Units: 0.5 / 1 / 2 cm² squares with ≥ 50 % masked-valid pixels; class text if ≥ 30 % of valid pixels are reference-text, blank if ≤ 5 % text
  and ≥ 50 % reference-blank.

## Deviations from the brief forced by this environment (recorded, not hidden)
- No renderer/tracer (no Docker daemon at start, no GPU): calibration uses the published surface volumes of w028 (2.399 µm, 109 slices) and
  w040 (9.362 µm, 28 slices) instead of own `vc_render_tifxyz` renders. Eligible-scroll charts cannot be produced here.
- No GPU: the public-model comparators (6.6) are deferred.

## Retired changes
- none yet
