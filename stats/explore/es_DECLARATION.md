# edgeshape (es) — declared BEFORE any evaluation crop is touched (2026-09-18, exploration E1 item 4)

E1 EXPLORATION, not a gate. Nothing here is a method version; nothing counts against the 0.80/0.90 bars.

HYPOTHESIS: ink changes the SHAPE of the air-to-sheet depth transition (edge sharpness, edge
position, crest curvature, profile width) rather than only the brightness LEVEL of the profile.
If true, descriptors that are invariant to the profile's level (and to its gain) must carry ink
information, and must ADD information to the level features.

Metric: pixel AUC on the 19.2 um ds8 grid (ds8_y / rebuilt classes for the training segments),
restricted to the pooled mask x[22] > 0.5. Comparators (v1b, v2, v3, team) are re-measured on
exactly the same pixels by mean-pooling their 2.4 um score maps 8x.

Fitted on the 8 TRAINING crops only (20231005123336/train; 20230929220926/held1-4;
20231012184424/held1-3). 20231012184424/held4 = validation only. Evaluation crops judged once:
20231005123336/held1-3 and 20231210121321/held1-4.

Known data limitation, recorded up front: each ds8 depth channel was standardised per crop
(median/MAD over the mask), so absolute profile shape in physical attenuation units is not
recoverable. All shape statements are therefore made in the crop's own standardised depth
coordinates, where signal and nuisance undergo the identical transform. Level-invariant
(difference-across-depth) features are exact; gain/curvature ratios are affected by the per-depth
scaling and are reported as such.

Feature groups (each built from channels spatially smoothed with a mask-aware Gaussian at
sigma_s in {0, 4, 8, 16} ds8 px = 0, 77, 154, 307 um; R = channel minus its 1 mm local background):
  LVL      per-face mean over the 11 depths                        (2 features)  - the "brightness offset"
  CH22     the 22 raw channels                                     (22)          - full linear reference
  D1       central first differences across depth                  (18)          - exactly level-invariant
  D2       second differences across depth                         (18)          - level+tilt invariant
  SHAPE    per-face unit-norm residual profile R/||R||             (22)          - level AND gain invariant
  EDGE     nonlinear per-face descriptors of R: crest depth (subpixel), depth of
           steepest ascent, max slope, sharpness = max slope / amplitude, effective
           width, crest curvature, profile norm                    (14)
Model: logistic regression, C = 1, class-balanced weights, features standardised per crop.
Selection: leave-one-crop-out (LOCO) mean over the 8 training crops.

Declared reading of the result (written before the held-out run):
  * "Ink is a distinct thin layer with its own edge signature" is SUPPORTED only if a
    level-invariant group (D1 / D2 / SHAPE / EDGE) reaches within 0.02 of LVL alone on LOCO,
    or if LVL+that group beats LVL by more than +0.02 LOCO and this survives held-out.
  * Otherwise the hypothesis is REFUTED for this data: ink acts as a depth-weighted brightness
    excess and nothing in the transition's shape adds to it.
  * A single held-out run of the best TRAIN-LOCO combination is reported, next to LVL, CH22 and
    the four existing comparators on identical pixels.

---
## RESULTS (appended after the runs; the declaration above is untouched)

### Step 1 — TRAINING crops, descriptor diagnostics (stats/explore/es_step1_diag.json)
Mean single-feature pixel AUC over the 8 training crops, sigma_s = 16 ds8 px (0.31 mm):
  B-4 0.658 | Blvl (bottom-face level) 0.655 | T+0 0.656 | Bu-4 (gain-invariant shape) 0.638 |
  Bwidth 0.634 | Bsharp 0.399 | Bdslope 0.528 | Bdstar 0.491 | Bcurv 0.483 | Bcen 0.481 | Bnorm 0.529.
  The literal "sharpness / crest position / curvature" descriptors are at chance; the informative
  shape number is the RELATIVE weight of the outermost bottom-face depths (Bu-4).
Text-minus-blank direction (standardised units, sigma 16, mean over crops): positive at EVERY
depth of both faces (T-4 +0.32 ... T+0 +0.59 ... T+6 +0.31; B-4 +0.56, B+0 +0.57, B+6 +0.28).
Geometry in the 22-d profile space (mean over the 8 crops, sigma 16): |cos(delta, PC1)| = 0.79
(per crop 0.76-0.98 except the signal-free crop 20230929220926/held2 at 0.03); 94 % of delta lies
in the top 3 PCs; AUC of the projection on delta 0.685, on PC1 0.39 (= 0.61 with the sign flipped),
on the part of delta ORTHOGONAL to PC1 0.616; in-crop whitened (LDA) discriminant 0.749.

### Step 2 — LOCO over the 8 TRAINING crops (stats/explore/es_step2_loco.json), multi-scale
LVL 0.6559 | CH22 0.6749 | D1 0.6424 | D2 0.6314 | SHAPE 0.6482 | EDGE 0.6365 | EDGE_SHP 0.6380 |
EDGE_AMP 0.6063 | D1+D2 0.6579 | SHAPE+EDGE 0.6511 | INV_ALL 0.6736 | LVL+D1 0.6810 |
LVL+SHAPE 0.6699 | LVL+EDGE 0.6684 | CH22+EDGE 0.6842 | CH22+SHAPE 0.6803 |
CH22+SHAPE+EDGE 0.6871 | ALL 0.6979  <- best on TRAIN, taken to the held-out run.

### Step 3 — SINGLE held-out run, 7 evaluation crops, ds8 pixel AUC (stats/explore/es_step3_heldout.json)
| crop | LVL | CH22 | D1 | INV_ALL | CH22+SHAPE+EDGE | ALL | v1b | v2 | v3 | team |
|---|---|---|---|---|---|---|---|---|---|---|
| seg1 held1 | 0.581 | 0.630 | 0.607 | 0.666 | 0.649 | 0.657 | 0.648 | 0.637 | 0.656 | 0.967 |
| seg1 held2 | 0.660 | 0.688 | 0.694 | 0.726 | 0.733 | 0.732 | 0.690 | 0.767 | 0.701 | 0.957 |
| seg1 held3 | 0.614 | 0.626 | 0.608 | 0.626 | 0.638 | 0.641 | 0.598 | 0.635 | 0.616 | 0.840 |
| seg2 held1 | 0.588 | 0.582 | 0.491 | 0.590 | 0.615 | 0.601 | 0.560 | 0.543 | 0.568 | 0.948 |
| seg2 held2 | 0.600 | 0.619 | 0.634 | 0.642 | 0.643 | 0.648 | 0.562 | 0.572 | 0.585 | 0.910 |
| seg2 held3 | 0.640 | 0.669 | 0.674 | 0.663 | 0.705 | 0.710 | 0.648 | 0.675 | 0.670 | 0.875 |
| seg2 held4 | 0.645 | 0.647 | 0.606 | 0.650 | 0.661 | 0.659 | 0.604 | 0.635 | 0.610 | 0.914 |
| MEAN | 0.6182 | 0.6371 | 0.6163 | 0.6519 | 0.6634 | 0.6639 | 0.6159 | 0.6378 | 0.6294 | 0.9158 |
Paired per-crop differences: ALL - CH22 +0.027 (7/7 crops), CH22+SHAPE+EDGE - CH22 +0.026 (7/7),
ALL - v2 (best existing) +0.026 (6/7), ALL - LVL +0.046 (7/7), D1 - LVL -0.002 (4/7).

### Verdict
1. The literal hypothesis - ink STEEPENS or SHIFTS the air-to-sheet edge - is REFUTED: crest depth,
   depth of steepest ascent, crest curvature and the sharpness ratio are at or below chance
   individually, and the text-minus-blank contrast is positive at every one of the 11 sampled
   depths on both faces (a broad excess, not an edge displacement). This agrees with the already
   recorded topography result (thickness / face-position AUC 0.48-0.53).
2. The weaker form - the profile's SHAPE, not only its level, carries ink information - is
   SUPPORTED: exactly level-invariant depth derivatives alone reach held-out 0.616 = the level's
   0.618, and the gain-invariant unit-norm profile SHAPE plus the nonlinear descriptors add
   +0.026 held-out over using the same 22 channels linearly at the same scales, on 7/7 crops.
   The ink direction in profile space is not parallel to the dominant background brightness mode
   (|cos| 0.79; the orthogonal part alone separates at 0.62 on TRAIN).
3. Size of the effect: best new measure 0.664 held-out vs 0.638 for the best existing declared
   method (v2) measured on the identical pixels, vs 0.916 for the team model. The gap to the team
   model is NOT closed by depth-profile shape; it is not a per-pixel physical quantity.
Recorded limitation: the ds8 channels were standardised per depth per crop, so the profile's
physical shape in attenuation units is not recoverable; all shape statements are made in the
crop's own standardised depth coordinates, where signal and nuisance share the same transform.
