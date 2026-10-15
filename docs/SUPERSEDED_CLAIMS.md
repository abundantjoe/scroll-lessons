# Superseded claims

Every claim of the work behind Result 1 and the lessons (the PHerc0268 strip runs, the PHerc0343 control and their tools)
that we made and later retracted or corrected is listed here, with the reason. Retractions in other experiments are
noted in their entries in [EXPERIMENTS.md](EXPERIMENTS.md). The record was kept during the
work in the project's private log and reports; the numbers below are the corrected ones used in this release.

| # | claim as first stated | correction | why |
|---|---|---|---|
| S1 | A raw spiral fit "fails" because its phase lock is below 2.46 | Invalid comparison: 2.46 is measured after snap and flatten | Wrong pipeline stage (LESSONS 1) |
| S2 | A renderer calibration pool was valid | Withdrawn: it contained a PHerc1203 sample | Cross-scroll contamination (LESSONS 2) |
| S3 | The v0 ink image showed the surface's ink | Withdrawn: forward + reverse averaged, per-image stretch | Invalid display (LESSONS 3) |
| S4 | 3-D seam test: the ink-model maps of two meshes anti-correlate, r = −0.20 | r = +0.43 (0.43 after removing each strip's row-mean band) | Overlay orientation assumed flipped; it was not (LESSONS 6) |
| S5 | Seam agreement significance p = 0.09 | p ≈ 0.01 (A→B) to 0.03 (B→A) with a full-sample circular-shift null | Non-wrapped shifts had unequal n and correlated neighbours (LESSONS 7) |
| S6 | "Every strip is 2.25 mm, one letter tall; no strip can show a letter row" | Two strip heights among the 56 mass-run strips: about 1.8 mm valid (40, the 240/260 px renders) and about 2.9 mm (16, the 380/400 px renders). The 2.9 mm strips can hold the ink cores of control-size letters (about 1.1-1.8 mm) when a row aligns; 9 of the control's 18 letter boxes are taller than 2.9 mm | Generalised from one strip (LESSONS 9) |
| S7 | Control letters are "240-300 px tall" | Ink cores about 130-210 px (1.1-1.8 mm); letter boxes 230-566 px | One crop measured, and one overlay was a half-resolution copy |
| S8 | The edge bands are "a model boundary artifact" (first a guess) | Measured: the bands depend on the blank margin (natural experiment) and largely disappear when the margin is filled (fill test; RESULTS §1-3). The code path that sees the zeros (robust normalisation without a mask, then InstanceNorm and the convolutions) is VERIFIED from the villa source; which step produces the artifact, and why its sign differs between scrolls, is not isolated | The first statement had no evidence behind it |
| S9 | A narrow pass of the 20-row control certifies the 20-row strip geometry beyond the control | Overstated: the 20-row control passed narrowly (CI includes the bar), at one depth (d = +1) on one scroll; a pass does not carry over to another scroll, depth or sheet contrast without a control run there | LESSONS 10 |
| S10 | "Nearly every strip shows two bands 50-70 px inside its edges" | About 2/3 of strips; peak 30-50 px inside the valid edge | Pooled numbers, imprecise wording |
| S11 | "The margin fill cut strong ink 3-700× on all 7 strips" | 2.96-623.9× (`results/margin_artifact/fill_test_PHerc0268_aggregate.json`) | Rounded up |
| S12 | Natural experiment: band 0.130 with a 30-row margin vs 0.020 with a 10-row margin, 29/32 strips | With this release's code: 0.163 vs 0.049, 24/29 strips (260 px); 0.190 vs 0.029, 6/7 (400 px) (`results/margin_artifact/natural_experiment_PHerc0268.json`) | The first numbers came from an audit's scratch script with different window and tolerance details, not shipped. Same direction and conclusion; we report only what our committed code gives |
| S13 | "A stroke-energy index separates letters from blobs" | Withdrawn: control 0.28 vs known-negative 0.62 | Failed calibration (LESSONS 8) |
| S14 | The declaration of the PHerc0268 margin-fill test (RESULTS §3; not reproduced here) was labelled "before any data" while quoting the control's exploratory fill-arm numbers | It preceded only the new data it tested; the quoted numbers were already computed | LESSONS 19 |
| S15 | "The 13-row control strips do not see ink" (pre-registered verdict, fixed threshold) | Stands as pre-registered. Exploratory: they keep the ranking (box AUC 0.67 vs 0.71); the fixed threshold loses the ink because the p scale compresses | A clarification, not a reversal |
| S16 | "The introduction message reached its destination" (operational) | It started a new session instead | LESSONS 33 |

No claim of letters on any scroll was made in this work, and none is made here.
