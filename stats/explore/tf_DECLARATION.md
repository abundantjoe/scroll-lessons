# twoface — declared BEFORE any evaluation crop is touched (2026-09-18, exploration E1 item 3)

This is an E1 EXPLORATION, not a gate. Nothing here is a method version and nothing counts
against the 0.80/0.90 bars. It is declared here so that the held-out numbers below it are
reported once and cannot be re-selected.

Metric: pixel AUC on the 19.2 um ds8 grid (ds8_y: 1 = verified text, 0 = blank), restricted to
the pooled mask x[22] > 0.5. NOT the full-resolution judge. The comparators (v1b, v2, v3, team)
are re-measured on exactly these same pixels by pooling their 2.4 um score maps 8x, so every
number in the table is computed on the identical pixel set.

Fitted on the 8 TRAINING crops only (20231005123336/train; 20230929220926/held1-4;
20231012184424/held1-3). 20231012184424/held4 was not used at all.
Evaluation crops, judged once: 20231005123336/held1-3 and 20231210121321/held1-4.

Features: the hole-filled 22 face-aligned channels at 5 isotropic scales (sigma = 0, 4, 8, 16,
32 ds8 px = 0, 77, 154, 307, 614 um), each column standardised per crop by its own mask
mean/std (unsupervised; identical operation on training and evaluation crops).
Model: logistic regression, C = 1, class-balanced sample weights.

Declared models (LOCO mean over the 8 training crops, already measured):
  CH1      single feature B-4 @ sigma 16                            LOCO 0.6733   <- baseline
  ALL      both faces, 110 features                                 LOCO 0.6840
  BOT      writing face only, 55 features                           LOCO 0.6708
  TOP      NON-writing face only, 55 features                       LOCO 0.6670
  SYM10    10 depth-symmetric sums T(+d)+B(-d), T(-d)+B(+d), d=1..4  LOCO 0.6729
  ASYM10   the matching 10 antisymmetric differences                LOCO 0.6028
  BOT+TOPOUT  writing face + T-4..T-1                               LOCO 0.6831

Declared reading of the result:
  * The hypothesis "two-sided / through-thickness features beat one-sided ones" is supported
    only if ALL beats both CH1 and BOT by more than +0.02 held-out pixel AUC.
  * TOP's held-out number is the physical statement about whether verified text is detectable
    at all from the non-writing face of the sheet.
