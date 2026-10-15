# calib (ca) — declared BEFORE any evaluation crop is touched (2026-09-18, exploration E1 item 6)

E1 EXPLORATION, not a gate. Nothing here is a method version; nothing counts against the 0.80/0.90 bars.

HYPOTHESIS: the ink signal exists per crop but is MIS-CALIBRATED across crops. Pooling crops under a
single global linear model destroys a contrast that is real within each crop. If true, a model fitted
with a crop's own labels must read that crop substantially better than the pooled model does, and the
per-crop optimum must be predictable from unsupervised, physical properties of the crop.

Metric: pixel AUC on the 19.2 um ds8 grid (ds8_y / rebuilt classes for the training segments), restricted
to the pooled mask x[22] > 0.5 — identical pixel convention to the tf/es/mf investigations, so numbers are
directly comparable. Comparators (v2, v3, team) re-measured on the same pixels by 8x mean-pooling their
2.4 um score maps.

Fitted on the 8 TRAINING crops only (20231005123336/train; 20230929220926/held1-4; 20231012184424/held1-3).
20231012184424/held4 = validation only. Evaluation crops (20231005123336/held1-3, 20231210121321/held1-4)
are touched once, at the end.

Features (base set B88): the 22 face-anchored depth channels, mask-aware Gaussian smoothed at
sigma_s in {0, 4, 8, 16} ds8 px (0, 77, 154, 307 um) = 88 maps, standardised per crop over the mask.
Model: logistic regression, C = 1, class-balanced weights. Up to 20000 text + 20000 blank pixels per crop,
seed 0.

STEP 1 — the decisive diagnostic (declared reading written now):
  GLOBAL(i)   = model fitted on the other 7 training crops, evaluated on crop i (leave-one-crop-out).
  SELF(i)     = model fitted on one spatial half of crop i, evaluated on the OTHER half (both
                split directions, averaged) — a fair per-crop number that uses that crop's own labels.
  GLOBAL_h(i) = the LOCO model evaluated on exactly the same held-out halves, for a matched comparison.
  * The mis-calibration hypothesis is SUPPORTED only if mean(SELF) - mean(GLOBAL_h) > +0.02 AUC.
  * If SELF <= GLOBAL_h + 0.02, per-crop calibration has no headroom to recover, whatever mechanism is
    used, and the hypothesis is REFUTED for this feature family: the ceiling is not a calibration problem.
  In-sample per-crop fits are also reported, labelled as optimistic, never used as evidence.

STEP 2 — where the variation is: per-crop weight vectors, pairwise cosine similarity, within- vs between-
segment structure, and regression of the weight variation on unsupervised per-crop physical summaries
(sheet thickness, face depth/offset, mask coverage / damage fraction, brightness level and spread,
depth-profile shape).

STEP 3 — unsupervised calibration mechanisms, each selected by LOCO on the TRAINING crops only:
  (N) local (spatially varying) gain normalisation: divide each channel's local residual by a local MAD
      estimated over sigma_N in {26, 52, 104} ds8 px, instead of the crop-global MAD.
  (D) per-crop depth recalibration: estimate a sub-slice depth shift from the crop's own mean depth
      profile and resample the 11 channels onto a common profile coordinate before fitting.
  (G) geometry conditioning: append locally estimated geometry (thickness, face depth, local brightness,
      coverage) and its interactions with the strongest depth features.

STEP 4 — the single best LOCO configuration from step 3 is run once on the 7 evaluation crops, reported
next to the pooled baseline B88 and the comparators on identical pixels. One number, reported once.
