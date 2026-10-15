# Methods

The pipeline behind the numbers in this release, with the parameters that set them (unrecorded or undeclared ones: §2, §11). Sources:
the scripts named in each section (paths are current; `scripts/` unless stated) and the lab notebook [`docs/RULES.md`](RULES.md), where the
methods were declared before they were run, with the exceptions listed in §11 and §12.
Units: the native pixel is **2.4 µm** (the surface-volume pitch); a crop is **6250 × 6250 px = 15 mm × 15 mm**; "ds8" is the 8× pooled
grid at **19.2 µm**.

## 1. Data

| item | value |
|---|---|
| scroll | Scroll 1, PHerc. Paris. 4 |
| CT | Vesuvius Challenge surface volumes `2.4um-0.22m-78keV-volume-20260411134726.zarr` (OME-zarr v2, uint8, level 0) for segments 20231005123336, 20231210121321, 20230929220926, 20231012184424 |
| reference | the 2023 Grand-Prize hand ink labels (7.91 µm UV), drawn on model output and papyrologically read; for 20231012184424 the label published as 20231012184423 |
| positive control | the team's published 2.4 µm ink prediction, **as its ds8 JPEG overview** (`ink-detection/downsampled/*-ds8.jpg`), i.e. at 19.2 µm |
| roles | **evaluation** (never trained on): 20231005123336 held1–3, 20231210121321 held1–4 (7 crops). **confirmation C1** (never touched before 2026-10-15): 3 + 3 crops on the same two segments. **training**: 20231005123336 train, 20230929220926 held1–4, 20231012184424 held1–3 and held5–11 (15 crops). **validation** (checkpoint selection only): 20231012184424 held4 |

Input files are pinned by URL and SHA-256 in [`results/input_manifest.json`](../results/input_manifest.json); crop coordinates in
`stats/s1_crops_<seg>.json` (evaluation, training), `stats/c1_confirm_<seg>.json` (C1), `stats/r1_unread_<seg>.json` (R1/R2).

## 2. Reference placement (`s1_register_label.py`, `s1_refine_reg.py`)

1. **Global registration** of the label onto the 2.4 µm canvas, against the team's ds8 ink overview: both images resampled to a common
   32 µm grid (label × 7.91/32, overview × 19.2/32 then Gaussian σ = 1 px); residual label scale searched by default over 0.96–1.06 in
   steps of 0.0025 (`np.arange`, 41 values). The two training segments were registered over 0.965–0.99 (11 values;
   `archive/scripts/run_s1_master.sh`, arguments `0.965 0.99`); the range used for the two evaluation segments is not recorded in any
   committed driver or log (both chose the grid value 0.9775, inside either range). The scaled label is smoothed with Gaussian σ = 1 px;
   at each scale the offset is the maximum of an FFT normalised cross-correlation restricted to the labelled zone (scaled, smoothed
   label above 0.2, dilated by 93 iterations of the 4-connected element on the 32 µm grid, i.e. 2.976 mm in city-block distance).
   Output: `scale_label_to_canvas`, `offset_canvas_y/x` (per segment, `stats/s1_registration_<seg>.json`).
2. **Per-crop refinement**: for each crop, the registered label window (padded 640 px = 1.536 mm) is shifted over ±80 ds8 px against the
   team overview of the crop (both Gaussian σ = 1.5 ds8 px); the shift with the highest normalised correlation is stored as
   `local_offset` (canvas px) with `local_reg_corr` (rounded to 3 decimals by the script; the correlations quoted below are those stored
   values). (The notebook's description says ±1.2 mm; the code searches ±1.536 mm per axis.)
   **Measured** (`stats/s1_crops_*.json`, `stats/c1_confirm_*.json`): the 7 evaluation crops lie inside the search window (largest
   per-axis |offset| 416 px = 0.998 mm, vector length 1.033 mm, on 20231005123336/held3, where the residual-shift check that first found
   it measured (998, −230) µm = 1.024 mm, `stats/s1_local_registration_check.json` @ 7375777; correlations 0.555–0.814), and so do the 6 C1 crops (largest per-axis
   |offset| 504 px = 1.209 mm, vector length 1.215 mm, which exceeds the notebook's stated ±1.2 mm but not the code's ±1.536 mm;
   correlations 0.547–0.698). Three training crops of 20231012184424 (held6–held8) sit exactly at the +640 px limit in x, held5 at
   632 px and held3 at 576 px, so their labels may be misplaced by more than the search could correct (training-label noise for
   v8/GP-R1; see LESSONS). Below the correlation of every evaluation and C1 crop (minimum 0.547), that segment has the validation crop
   held4 (correlation 0.307), the training crop held10 (0.257) and held8 (0.473, also at the search limit). 20230929220926/held4 is
   offset −520 px (−1.248 mm) in x, correlation 0.411.
3. **Sampling**: canvas pixel (y, x) takes the label pixel `round((y − offset_y − local_offset_y)/scale)`, `round((x − offset_x − local_offset_x)/scale)`;
   the label is binarised at > 127 after conversion to 8-bit grayscale.

**Caveat, stated plainly:** the reference is aligned to the positive-control model. The per-crop step moves the label by at most
640 px = 1.536 mm per axis (2.172 mm diagonally); the largest applied shifts (vector length) are 1.033 mm on the evaluation crops, 1.215 mm
on C1 and 1.621 mm on a training crop (20231012184424/held6). INFERENCE: this is unlikely to create agreement for our detectors by itself,
but they were trained on labels placed the same way, so some inflation cannot be excluded; and the team model's own score is partly
self-referential.

## 3. Crop selection (`s1_select_crops.py`, `select_confirm.py`, `select_unread.py`)

On a 40-canvas-px (96 µm) grid: label density = box mean of the label over a 6250-px window; label zone = label closed with a 5 mm disc;
on-sheet = the segment's on-sheet image (`onsheet_ds8.png`) > 0; where it is absent (20231005123336), crop and C1 selection use the CT
mid-slice overview `mid_l3.png` > 0 and R1 selection (`select_unread.py`) uses the surface-render overview `render_ds8.jpg` > 0. Candidate
windows on a 1250-px step need zone coverage ≥ 0.99 and on-sheet coverage ≥ 0.90; windows are taken greedily in descending density,
rejecting any that overlaps a kept window (overlap = both |Δy| and |Δx| < 6250). On 20231005123336 the selection was column-wise: the
label's x-extent is split at the largest gap of the column-wise label sum (x = 46040 canvas px); TRAIN = the densest window centred in the
left column, held1–2 = the two densest non-overlapping windows centred in the right column, held3 = the densest left-column window not
overlapping TRAIN or held1–2. The other segments use the rule above without columns. C1 additionally rejects any window overlapping
one processed before (`crops.json`, `unread.json`). R1's unread windows: on-sheet ≥ 0.90 and no labelled pixel within 5 mm; reading
window = nearest the label zone, control = farthest.

## 4. Sheet geometry and depth sampling (`fetch_zarr_region.py`, `topo_faces.py`, `s1_score.py --dump`)

- **Fetch**: one 6250 × 6250 window of all slices, 128 × 128 chunks, 24 parallel workers; chunk presence verified even when a completion
  marker exists. Slice range searched for the sheet: K0–K1 = 2–82 (20231005123336) or 24–84 (other segments).
- **Faces**: Gaussian σ = 1 (slice, y, x); crest k\* = argmax; the bright band = the contiguous run containing k\* where the profile is
  ≥ 50 % of the crest; `k_top`, `k_bot` = its ends with linear sub-slice interpolation; valid = band not clipped by the stack ends, crest
  ≥ 24 (uint8), CT at the middle slice of the searched range (K//2) > 0. Tiles of 1024 px with an 8-px halo.
- **Depth stacks**: for each face f ∈ {top, bottom} and offset δ ∈ {−4, …, +6} slices, I(k_f + δ) by linear interpolation along k →
  22 channels, float16. Because both faces are 50 %-of-crest crossings, the two δ = 0 channels sample the same half-crest level
  (correlation 0.96, RULES.md "E1 partial results", two-faces item, cdc291e); they are kept, as declared.

## 5. Judge mask J (`residual.py --edge-margin-mm 0.1`)

On-sheet = valid AND 30 µm ≤ thickness t ≤ 380 µm AND CT > 0. Damage = NOT on-sheet OR |∇ G₀.₁ₘₘ(t)| > 0.3 voxel/px; morphological
opening with a 0.05 mm disc (removes fibre-scale voids, which stay excluded pixel-wise); dilated by **0.1 mm** (mask J; the earlier v0.1b
mask used 0.4 mm, which left 3–9 % of the finer-lace segment). Grains: face intensity > 99.9th percentile with component size between
(0.02 mm)² and (0.1 mm)², dilated 0.3 mm. Mask per face = on-sheet AND NOT dilated damage AND NOT dilated grains; **the judge mask is the
AND of both faces' masks**. Gaussians with σ ≥ 8 px are three box passes of approximately equal variance (box width
round(√(4σ² + 1)) forced odd; e.g. σ = 41.66 px, the 0.1 mm gradient smoothing, gives width 83 and σ_eff = 41.49 px).

## 6. Pooled stack (`s1_ds_stack.py`)

8 × 8 mean pooling of each depth channel weighted by the judge mask (cell value = Σ(x·m)/Σm); per-channel standardisation by median and
1.4826 · MAD over cells with mask coverage > 0.5; zero elsewhere. Output `ds8_x.npy` = 22 channels + coverage (23 × 781 × 781, float32).
Classes `ds8_y.npy`: text where the pooled text class > 0.5, blank where the pooled blank class > 0.5 (text wins), else −1 (ignored).

## 7. Classes (`s1_judge.py`, `build_noveto_y.py`)

text = label AND mask. blank = NOT label AND distance to nearest label ≥ 0.3 mm AND ≤ 5 mm AND mask. On the evaluation and C1 crops no
other rule applies. (The GATE-S1 declaration defines the blank zone as the label *closed* with a 5 mm disc; the code uses distance ≤ 5 mm,
which also admits unlabelled papyrus up to 5 mm outside the text column. Every method and the comparator are judged with the same code.) Training labels: `ds8_y_noveto.npy` uses exactly this rule (v6c, v8, GP-R1). The team-model **veto** variant
(`ds8_y.npy` on training segments; used by v6b and by the v7 fit) additionally keeps as blank only pixels whose team-overview value is at
or below the 40th percentile of the crop's label-free blank pixels (a quantile, because the JPEG overview has a soft floor and the
declared < 0.10 rule left zero blank pixels on all 7 extra-segment training crops — RULES.md, data-integrity incident 3; see LESSONS).

## 8. Detectors

| id | what | trained on | parameters |
|---|---|---|---|
| **v8** (`s1_v5.py`) | 2-D U-Net on the 23-channel pooled stack | 15 training crops, no-veto labels | encoder 24/48/96 channels, two 2× pools, bilinear decoder, 270 817 parameters; patch 128 × 128 ds8 px (2.457 mm), batch 16, patches with ≥ 5 % labelled pixels, rot90 × flip augmentation; masked BCE; Adam lr 3e-4, weight decay 1e-4, 12 000 steps, seed 0; validation every 250 steps on the whole validation crop, checkpoint = highest validation pixel AUC (step 9 500). Prediction: sigmoid, ×8 bilinear upsampling to 2.4 µm, masked |
| **GP-R1** (`gpr.py`) | Grand-Prize-style 3-D→2-D detector: 3-D convolutions over the 22 stacked depth channels (11 offsets around the top face followed by 11 around the bottom face, treated as one ordered axis) collapse to a 2-D map, then a 2-D U-Net decoder | same | 3-D encoder widths 8/16/32 with a stride-2 depth convolution in each of three blocks (22 → 11 → 6 → 3 slices, then averaged); 2-D widths 32/64/128; 488 937 parameters; loss BCE + soft Dice; augmentation: full dihedral group, intensity × U(0.9, 1.1) + N(0, 0.05) (one scale and one offset per patch), and with p = 0.3 one 32 × 32 px square (25 % of the patch side, 6.25 % of its area) set to zero; patch 128, batch 8, patches with ≥ 25 % labelled pixels; Adam lr 3e-4, wd 1e-4, 4 000 steps, seed 0; checkpoint by validation pixel AUC (step 3 500). Prediction: mean over the 8 dihedral transforms, standardised by median and 1.4826 · MAD over ds8 cells with mask coverage > 0.5, nearest-neighbour ×8 upsampling. Scaled from the Grand-Prize widths for CPU (6.7 s/step → 1.97 s/step in the pre-training benchmark recorded in RULES.md; the committed run log `results/logs/gpr1.log` gives 8 334 s for 4 000 steps including validation, 2.08 s/step) |
| **E** (`ensemble_e.py`, `inkeval.rank_mean`) | rank-mean of v8 and GP-R1 | — | each map rank-normalised inside the mask, equal-weight mean, Gaussian σ = 0.08 mm by normalised convolution (fixed in advance at half of "0.161 mm", the notebook's "median stroke half-width"; that number is the median distance from a text pixel to the label edge on the segment-1 TRAIN crop, 0.1606 mm in `stats/explore/au_step1_geom.json`, which the notebook rounded up) |
| **v7** (`s1_v7.py`) | best hand-built baseline: ridge on smoothed depth channels | 8 training crops; **team-vetoed** labels on the 7 crops of 20230929220926 and 20231012184424 (the 20231005123336 TRAIN crop's labels carry no veto) | 22 channels × Gaussian σ ∈ {0.05, 0.10, 0.25, 0.60} mm = 88 features; regional removal f − G_σR(f); σR ∈ {1.0, 1.5, 2.5, 4.0 mm, none} and λ ∈ {0.1, 1, 10, 100, 1000} chosen by leave-one-crop-out (chosen σR = 4.0 mm — the largest finite value, next to 'none' = no removal; LOCO 0.741 against 0.723 for 'none' at λ = 0.1 — and λ = 0.1, the smallest value of its grid); per-crop median/MAD standardisation; ridge penalty λ multiplied by the number of training rows; output smoothed 0.10 mm, standardised by median and 1.4826 · MAD over ds8 cells with mask coverage > 0.5, ×8 bilinear |
| v6b / v6c | the v8 network and recipe on 8 crops, checkpoint by validation BCE | v6b team-vetoed (on the same 7 of its 8 crops as v7), v6c no-veto labels | chosen steps 750 / 250 |
| v0.1b, v1b, v2, v3 | papyrus subtraction; depth template; band-passed template; 66-feature ridge | see RULES.md | archived methods, reported as recorded |
| team | the positive control | — | ds8 overview / 255, ×8 bilinear (`s1_team_comparator.py`), masked |

## 9. Metrics (`inkeval.metrics` = exact ports of `s1_judge.py`, `stroke_test.py`, `local_stroke_test.py`)

- **Pixel AUC**: Mann–Whitney AUC of the score on text vs blank pixels of a fixed 5 % subsample (`default_rng(0).random(shape) < 0.05`).
- **Stroke AUC**: disks of radius 0.25 mm (104 px). Ink centres ≥ 0.25 mm inside a stroke; blank centres ≥ 0.5 mm from any label; centres on
  a 104-px grid ≥ 104 px from the border (the grid spacing equals the radius, so neighbouring disks overlap — the declaration's "to avoid
  overlap" does not hold); a disk counts if ≥ 50 % of it is in the mask; every qualifying disk is used, in raster order (the code's seeded
  draw of 8 000 candidates never runs on a 6250-px crop, which has 59 × 59 = 3 481 grid centres, and its cap of 2 000 disks per class
  never binds in the records: the largest class is 855 disks); AUC of the disk-mean scores; undefined below 20 disks per class. Only
  strokes thicker than 0.5 mm contribute ink disks.
- **Local stroke test L**: the same ink and blank disks (the code's caps of 1 500 ink and 6 000 blank disks never bind); each ink disk is
  compared only with blank disks whose centres lie within 1.5 mm; L = mean, over ink disks with at least one blank disk within 1.5 mm, of
  the fraction of those blank disks it out-scores (ties ½). Unpaired ink disks are skipped (`n_paired` in `stats/local_stroke_test.json`;
  e.g. 165 of 202 on 20231005123336/held1).
- **Letter AUC** (retired): component-based (components ≥ 0.5 mm² with ≥ 50 % valid pixels); undefined on 2 of 7 evaluation crops under
  mask J (4 of 7 under the original mask: all four crops of 20231210121321; the stroke-test declaration's "5 of 7" is not supported by the
  records, since segment 2 was first judged after the reference refinement) and unstable with the mask where defined; kept in the
  records, not used.
- **Declared bars**: held-out mean pixel AUC ≥ 0.80 AND held-out mean stroke AUC ≥ 0.90.

## 10. Statistics and controls (`release_stats.py`, `inkeval.stats`)

- Unit of replication: the **crop** (7 evaluation, 6 confirmation; 2 segments). Pixels are spatially correlated and are never treated as
  independent.
- Means with 95 % percentile bootstrap intervals over crops (10 000 resamples, seed 0); paired differences between methods bootstrapped the
  same way, with the count of crops favouring each side.
- **Negative control — label-swap null**: each crop's score map against every other crop's text/blank classes (all ordered pairs, judge
  subsample), which keeps both spatial structures and breaks only their correspondence.
- **Positive control**: the team model, judged identically.
- **Reading runs**: agreement statistic = AUC of a score separating the team overview's confident ink (> 0.80) from confident blank
  (< 0.20) inside the mask; its null (N1, post-hoc) pairs each unread window's score with another window's team classes.
- **Reporting rule**: numbers are truncated toward zero at three decimals, never rounded up. Pixel AUCs are stored at full precision in
  `results/`. Stroke AUC and L are recorded rounded to 4 decimals by `stroke_test.py` / `local_stroke_test.py` (`round(·, 4)`); for E,
  v8, GP-R1, v7 and the team model on the 13 evaluation and C1 crops, `results/` carries the toolkit's full-precision values instead
  (equal to those records at 4 decimals; `results/toolkit_vs_records.json`). Truncating a 4-decimal record can give 0.001 more than
  truncating the full value (E stroke on 20231005123336/held3: full 0.89595…, record 0.896); for the other methods only those records
  exist.

## 11. Parameters that affect headline numbers but were never declared

Recorded so nobody has to discover them, each with the commit where it is fixed in code: the segment-1 slice range K0–K1 = 2–82
(`run_s1.sh`, f3bb3a8, now in `archive/scripts/`); the judge's 5 % pixel subsample (`s1_judge.py`, acda042); the training patches'
labelled-fraction floor (≥ 5 % for v8, `s1_v5.py`, 1c694f2; ≥ 25 % for GP-R1, `gpr.py`, 9d4ae3f); the local test's caps (1 500 ink, 6 000
blank disks, `local_stroke_test.py`, cdc291e — the stroke-test declaration says "up to 2000 disks per class"), listed for completeness
only: they never bind (at most 202 ink and 855 blank disks in any record); v7's ridge penalty multiplied by the number of training rows
(`s1_v7.py`, introduced in 45fe9e0, in the form that produced the committed weights in 4c630c4); the reading-run thresholds (team > 0.80
ink, < 0.20 blank), first written with the R1 result (e8d6a6c) and first committed as code in `n1_reading_null.py` (bde701a); GP-R1's
nearest-neighbour ×8 upsampling (`gpr.py`, 9d4ae3f — v8's bilinear upsampling was declared, GP-R1's was not; post-hoc D3 measured a larger
pixel-AUC gain from smoothing for GP-R1, +0.029 against +0.008 for v8; INFERENCE: this upsampling is the likely cause, untested because
GP-R1 was not re-judged with bilinear upsampling, LESSONS 24). None was tuned on evaluation data.

**Caching that can silently prevent recomputation:** `s1_judge.py` reuses `cls_text.npy`, `cls_blank.npy` and `label.npy` if present;
`stroke_test.py` and `local_stroke_test.py` skip (crop, tag) pairs already in `stats/stroke_test.json` / `stats/local_stroke_test.json`;
the drivers skip crops that already have `ds8_x.npy`; `topo_faces.py` exits if `topo.done` exists; `residual.py` exits if
`residual_<tag>.done` exists, and the drivers use `--tag v0.1b` for both the 0.4 mm and the 0.1 mm (mask J) margin, so a stale 0.4 mm
mask is kept silently; `run_v7_v6b.sh` skips the v7 fit if `stats/s1_v7_weights.json` exists; `fetch_zarr_region.py` skips chunk files
already present at the expected size. To recompute from scratch, delete those files or entries first.

## 12. Pre-registration

The methods, tests and bars above were declared in [`docs/RULES.md`](RULES.md) (parameters that were not: §11);
`scripts/check_preregistration.py` verifies that each declaration heading was committed before its result heading ([`results/preregistration_order.json`](../results/preregistration_order.json)).
Three exceptions where git cannot show the declaration preceded the computation — the stroke test and L (declared in the same commits
as their first results) and R2 (maps computed before its declaration commit) — are listed in
[RESULTS §1](RESULTS.md#1-pre-registered-tests-and-their-order). Post-hoc analyses (D3, N1, the C1 shrinkage interval method) are
labelled as such. Hand-typed times in notebook headings are not evidence; commit times are.
