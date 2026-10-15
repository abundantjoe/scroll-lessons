# RULES.md — declared tests. Bars are written BEFORE the run and never edited. Results are appended after.

Conventions: pitch from the store's own metadata (w028 2.4 µm stack: 2.399 µm from `.zattrs` coordinateTransformations; w040 9 µm stack: 9.362 µm). 1 cm bar = 10000/µm px. Unit = 0.5 cm² square (side sqrt(0.5)·10000/µm px: 2948 px at 2.399 µm; 755 px at 9.362 µm; 737 px at 9.596 µm pooled).

## Text reference (6.1) — declared 2026-09-16 before any residual was computed
- w028: team 2.4 µm prediction `PHerc1667-20251208130119-2.399um-...-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif` ÷255. text = ref ≥ 0.40; blank = ref ≤ 0.25; on-sheet only (thickness 4–40 voxels and CT > 0); pixels within 240 px (2.4 µm) / 60 px (9.6 µm) of a labelled letter (HF `pherc1667-w028_inklabels.zarr`, slice 10, 9355×7585 canvas at 4× the 2.4 µm level-2 grid) excluded.
- w040: team 2.4 µm prediction likewise (66.7 MB TIFF); for the native 9.362 µm stack the reference is that prediction block-averaged to the 9.362 µm canvas via the two meshes' shared (u,v) parametrisation (both tifxyz share the segment's UV grid: verify shape ratio before use); labels `w040_inklabels.zarr` slice 14 excluded within 60 px.

## GATE-T1 (6.2) — w028 at 2.399 µm, level 0 — bars declared 2026-09-16 22:20 UTC, BEFORE the run
Crops: rule in `scripts/select_crops_w028.py` (5 text + 2 blank 4 cm² windows; chosen 2026-09-16 before any residual was computed; the two "blank" windows are the lowest-text valid windows and still contain 7 % and 13 % text pixels — w028 has no blank 4 cm²; this is recorded, not hidden). Render: published surface volume, 96 of 109 slices (k = 6..101) around the mesh (k = 54). Face = the one with the higher row-test peak.
Judge: per crop, pixel ROC AUC of s_face vs reference (text = 1, blank = 0, other pixels ignored); window-level hit rates of rule 6.4 on text vs blank 0.5 cm² units.
Bars (never edited):
- mean AUC over the 5 text crops ≥ 0.70 → "sees text"
- mean AUC ≥ 0.82 → "beats the public 9 µm model's 0.823"
- text units flagged ≥ 3× blank units at 1 cm²
Every crop is recorded, not the best.

## GATE-T2 (6.3) — 9 µm — bars declared 2026-09-16, BEFORE the run
Same judge and bars as T1, on (a) w028 pooled to 9.596 µm (villa `prepare_9um_isotropic_input --level 2`, 21 slices, ±10 for topography) and (b) w040 native 9.362 µm published stack (28 slices; the published surface volume replaces the 40-slice render because no renderer is available in this environment — recorded as a deviation; topography uses all 28 slices, ±14 around the mesh).
Decision rule: T2 fails and T1 passes → 2.4 µm-only route (targets = the two rescans).

## Rule 6.4 derivation — declared before the run
On w028 (T1 crops, 2.4 µm): per 0.5 cm² unit, mean s_face on text units (unit text fraction ≥ 0.5 of its valid pixels... see below) vs blank units. Unit class: text if ≥ 30 % of its valid pixels are reference-text, blank if ≤ 5 % are reference-text and ≥ 50 % are reference-blank; others unclassed. τ_unit = midpoint of the two class means; M = midpoint of mean(s_face − s_other) on text vs blank units. Flag = mean s_face ≥ τ_unit AND mean(s_face − s_other) ≥ M. PROMISING CANDIDATE = ≥ 3 adjacent flagged units AND row test positive on the same face. BLANK = no flagged unit over ≥ 1.5 cm² valid units on either face. Hit rates at 0.5, 1, 2 cm²; require text ≥ 3× blank at some size or NOT ESTABLISHED.

## GATE-F (6.5) — declared before the run
On the two w028 blank crops and on two damage-rich charts of an eligible scroll (own patches; only if a tracer/renderer becomes available — otherwise the two blank crops plus the tear/hole rims inside the text crops, masked-out region excluded, are the damage control and this substitution is recorded): rule flags ≤ 1 unit per 4 cm² and row test negative.

## Fixed method parameters
See METHOD.md. All parameters are frozen after 6.2–6.5 on w028/w040 and before any eligible scroll is read.

## Results (appended after runs; bars above untouched)

### Pre-AUC mask decision (2026-09-16 22:50 UTC, text1 thickness maps only, no residual or AUC computed yet)
The brief's tear criterion "|∇t| large" at pixel scale masks 57 % of the on-sheet area at 2.4 µm (median |∇t| = 1.2 voxel/px is fibre texture).
Fixed instead: |∇(G_{0.1 mm}(t))| > 0.3 voxel/px. Recorded here so it cannot be mistaken for post-hoc tuning; it is not changed after the first AUC.

### Second pre-AUC mask decision (2026-09-16 22:55 UTC; the first text1 judge run returned AUC = None because the mask was empty)
At 2.4 µm the on-sheet mask is a lace (43 % fibre-scale voids in text1); dilating every void by 0.4 mm blanked 100 % of the chart.
Fixed: the 0.4 mm margin applies only to MACROSCOPIC damage = (not on-sheet OR tear) after a morphological opening by a 0.05 mm disc;
fibre-scale voids remain excluded pixel-wise without a margin. No AUC had been computed when this was decided.

## Results
### GATE-T1, text1, method v0.1 (2026-09-16 23:20 UTC) — recorded as run
- mask covered 5.6 % (top) / 5.1 % (bottom) of the chart: the brief's grain rule (S > 99.9th percentile, component < 0.1 mm, dilate 0.3 mm)
  marked 10 218 fibre-scale bright pixels and their 0.3 mm discs covered ~94 % of the sheet. No 0.5 cm² unit reached 50 % valid → no unit statistics.
- pixel AUC on the remaining area: top 0.540, bottom 0.553; relief-only 0.490 / 0.511 (chance); fibre residual e 0.549 / 0.527. Row test: bottom
  peak 0.225 at 2.59 mm (CT control −0.05), top −0.14. Reference exclusion (labels) 5.1 %.
- Verdict for v0.1 on text1: below the 0.70 bar. Topography (relief) carries no signal at 2.4 µm here, as the paper's resolution curve predicted.
### Declared BEFORE running: method v0.1b (mask change only, score unchanged)
Grain = S > 99.9th percentile AND connected component area between (0.02 mm)² and (0.1 mm)² (a mineral grain, not a single bright fibre pixel); margin 0.3 mm unchanged.
Everything else identical to v0.1. Bars unchanged. The v0.1 numbers above stay on record.
### GATE-T1, text1, method v0.1b (2026-09-16 23:03 UTC) — recorded as run
- mask 36.0 % (top) / 35.9 % (bottom) of the chart (grains found: 28/29). Text px 11.0 M, blank px 11.6 M. No 0.5 cm² unit ≥ 50 % valid.
- pixel AUC: top 0.499, bottom 0.555; relief-only 0.481 / 0.518; fibre residual e 0.529 / 0.516. Row test: top peak 0.258 at 2.99 mm (CT control −0.11),
  bottom 0.054 (max in band 0.224 at 3.21 mm).
- Verdict: v0.1 and v0.1b FAIL the 0.70 pixel-AUC bar on text1 for both faces. Topography (relief MAD 41–44 µm, fibre-scale) carries no ink signal
  at pixel level; the fibre-intensity residual is at chance. This is the paper's prediction at 2.4 µm (resolution curve), now measured on real data.
- Declared diagnostic (not a gate, no tuning): row-mean profile of s vs row-mean profile of the reference (Pearson r at lag 0, ±5 mm lags) to test
  whether the 3 mm row periodicity in s_top is line-level ink signal or unrelated banding.
### GATE-T2(b), w040 9.362 µm, v0.1b — recorded as run
- mask only 3.4 % (band clipped: 25 % of pixels with k_top ≤ 0, 29 % with k_bot ≥ K−1 in the 28-slice stack; sheet fills the stack). AUC top 0.461,
  bottom 0.540; relief 0.477 / 0.527; e 0.512 / 0.506. Inconclusive on 3.4 % area; a wider stack (more slices) is needed for a fair 9 µm test.
- Row-profile diagnostic result (text1, v0.1b): bottom r(lag 0) = 0.248 (best 0.276 at −0.10 mm); top r(lag 0) = 0.040 (best 0.267 at +0.38 mm).
  Reading: a weak line-level agreement exists on the bottom face only; the 3 mm periodicity on top is not aligned with the reference. Neither
  changes the verdict.
### GATE-T1 control, blank1, method v0.1b (2026-09-17 14:10 UTC)
- mask 22.3 % / 22.4 %; reference marks 10.5 % of the masked area as text (the "blank" crop is not fully blank per the team model).
- AUC top 0.520, bottom 0.543 (relief 0.491 / 0.515; e 0.530 / 0.513) — same as text1: the score does not separate the reference's classes anywhere.
- Row test on the BLANK chart: bottom peak 0.418 at 3.14 mm (CT control 0.21), top 0.104. A blank chart shows stronger ~3 mm row periodicity
  than the text chart. Consequence: the ~3 mm periodicity is structural (fibre/segmentation banding), not line spacing. The row test is
  falsified as an ink indicator on w028 and is dropped from the GATE-T1 criteria (recorded, not tuned).

## Declared diagnostic D1 (2026-09-17 14:30 UTC, BEFORE running): where along the normal is the reference contrast?
Purpose: measure, not score. On text1 only, for reference-text vs reference-blank pixels inside the v0.1b mask, the CT profile I(k) sampled
at k_top + δ, k_mid + δ and k_bot + δ for δ = −8…+8 slices (linear sub-slice interpolation): class means and the per-δ pixel AUC
(text vs blank) and the per-δ AUC of 32×32 px (0.077 mm) block means. Also AUC of thickness t and of the crest peak. Script
scripts/depth_profile_diag.py. Reading rule: a peak of |AUC − 0.5| at |δ| ≤ 1 supports the surface-crust premise; a peak inside the
sheet or none at all refutes it for this scroll. From this point, text1 is the EXPLORATION chart: anything designed with D1 in view is a
new version (v0.3+) evaluated on text2–text5 and the blanks only; text1 numbers for such a version are reported but do not count.
### D1 result, text1 (2026-09-17 15:05 UTC) — 11.5 M text px / 11.9 M blank px; 12.2 k / 12.2 k blocks of 0.077 mm
- Thickness t: AUC 0.498 (nothing). Crest peak intensity: 0.581. Text pixels are ~2–3 uint8 units (≈2 %) brighter than blank at every depth.
- Contrast along the normal (pixel AUC / block AUC): top face peaks AT k_top (δ = 0): 0.577 / 0.614, falling to 0.51 by δ = −4 (outside)
  and 0.52 at δ = +5 (inside). Bottom face peaks INSIDE the sheet at δ = −2…−3 slices (5–7 µm): 0.585 / 0.637; at δ = +1 (where v0.1 sampled
  S_bot) only 0.526 / 0.538. Mid-sheet: ≤ 0.55 / 0.60.
- Reading: the surface-crust (relief) premise is refuted on this scroll's CT at 2.4 µm; the only contrast agreeing with the reference is a
  weak face-brightness excess at letter scale. v0.1's fibre subtraction and 0.15–1.2 mm band-pass removed it (AUC 0.50).
- Caveat that stays attached to every later number: the reference is the team's model, so what D1 measures is agreement with that model's
  contrast, not ink truth. Ink truth needs a chart with known text (the 6.6 comparators or a physically verified segment).
### GATE-T1 verdict, method v0.1b, all 7 crops (2026-09-17 14:38 UTC) — stats/w028_gate_t1_v0.1b.json
| crop | kind | AUC top | AUC bot | relief top/bot | e top/bot |
|---|---|---|---|---|---|
| text1 | text | 0.499 | 0.555 | 0.481/0.518 | 0.529/0.516 |
| text2 | text | 0.498 | 0.592 | 0.470/0.535 | 0.541/0.533 |
| text3 | text | 0.565 | 0.473 | 0.514/0.483 | 0.521/0.499 |
| text4 | text | 0.496 | 0.575 | 0.475/0.530 | 0.543/0.530 |
| text5 | text | 0.504 | 0.561 | 0.475/0.525 | 0.542/0.530 |
| blank1 | blank | 0.520 | 0.543 | 0.491/0.515 | 0.530/0.513 |
| blank2 | blank | 0.467 | 0.537 | 0.484/0.519 | 0.510/0.508 |
Mean AUC over the 5 text crops on the declared writing face: 0.510 (best-face mean 0.570). No unit reached the 50 % valid-pixel threshold at
0.5/1/2 cm², so the 3× unit bar could not be evaluated. **GATE-T1 FAILS for v0.1b** (bar 0.70). Relief is at chance on every crop.
### D1b result, text1 (2026-09-17 15:20 UTC): AUC of face intensity vs smoothing σ (normalised convolution in the mask)
top (S at k_top−1): 0.565 (raw) → 0.615 (0.05 mm) → 0.630 (0.1) → 0.639 (0.2) → 0.637 (0.3) → 0.624 (0.5) → 0.603 (0.8 mm).
bot (S at k_bot+1, the wrong depth per D1): 0.537 → 0.561 → 0.571 → 0.580 → 0.581 → 0.577 → 0.570. Plateau at 0.2–0.3 mm. Plain face
intensity does not reach 0.70 on the exploration chart.
### Declared D1c (exploration chart only, BEFORE running): three more simple measures at σ = 0.25 mm
(1) z(G(S_top)) + z(G(S_bot)); (2) band peak intensity G(peak); (3) local roughness: std of S_top in a 0.05 mm window, then G(0.25 mm),
sign recorded (paper: inked areas smoother in SEM → expected negative); (4) rank-sum of (1) and (3). Reported, not tuned further.
### D1c result, text1 (2026-09-17 15:35 UTC), σ = 0.25 mm: top 0.640, bot(k_bot+1) 0.586, top+bot 0.616, peak 0.651, roughness 0.516,
(top+bot)−rough 0.623, cv_top 0.435 (text has slightly LOWER relative roughness: 0.565 when flipped, consistent in sign with the paper's
SEM note, but negligible). Ceiling of simple physical measures on the exploration chart ≈ 0.65.
### Declared BEFORE running: method v0.3 (no subtraction; evaluated on text2–text5, blank1, blank2; text1 reported but not counted)
- v0.3p: s_top = s_bot = z(G_{0.25 mm}(peak)) over the v0.1b mask (peak = crest intensity of the bright band). Needs no raw stack.
- v0.3f: s_top = z(G_{0.25 mm}(I(k_top))), s_bot = z(G_{0.25 mm}(I(k_bot − 2.5))) (D1 depths), same mask. Needs the raw stacks (refetched).
- Judge and bars: unchanged (GATE-T1 judge, 0.70). Expected from the exploration chart: ≈ 0.65, i.e. a FAIL; the point is the held-out
  ceiling of plain CT brightness against the team model. GATE-T2(a) (w028 pooled to 9.6 µm) is not run: with T1 failed, route B is
  closed regardless of T2.
### v0.3p result, all crops (2026-09-17 16:05 UTC) — stats/w028_gate_t1_v0.3p.json (peak intensity, G 0.25 mm, no subtraction)
text1 (exploration, not counted) 0.654 | text2 0.602 | text3 0.714 | text4 0.710 | text5 0.636 | blank1 0.523 | blank2 0.541.
Held-out mean (text2–text5) 0.666; all-five mean 0.663. **FAILS the 0.70 bar** (two crops individually above it). Units: still none with
≥ 50 % valid pixels at 0.5–2 cm² (mask ≈ 36 %), so the 3× unit bar remains unevaluable under the declared rule; recorded, not relaxed.
Reading: the team model's contrast is reproduced at AUC ≈ 0.66 by nothing more than smoothed CT brightness of the sheet's bright band.
### Post-hoc robustness check (declared 2026-09-17 16:20 UTC AFTER seeing v0.3p; labelled post-hoc, not a new bar attempt)
The v0.3p map on text3 shows a chart-scale brightness gradient aligned with the reference's text-density gradient. v0.3p-hp = v0.3p with the
> 3 mm scale removed (G 0.25 mm minus G 3 mm, normalised convolution). If the AUC holds, the agreement is letter-scale; if it collapses, v0.3p's
0.66 was partly a density-gradient confound. Either way v0.3p's number stays on record as is.
### Data-integrity incident (found 2026-09-17 16:30 UTC): text3 and text4 topography computed on 61 % of the crop
The restarted crop driver deleted text2's chunk rows 144–209 unconditionally; those rows overlap text3 (184–209) and text4 (144–169), which had
already been fetched, and the fetch's done-marker then skipped re-downloading them. The store has data there (HTTP 200, 1.79 MB chunks) and the
level-4 overview shows sheet. Every text3/text4 number above (v0.1b, v0.2, v0.3p) was computed on the remaining 61 % of those crops. Fix: the
fetch now verifies chunk presence even when the marker exists; text3 and text4 are refetched and ALL their derived products recomputed; the
summaries are re-issued. The affected numbers stay in the record above with this note.

## GATE-S1 — Scroll 1 (PHerc.Paris.4) against physically verified text — declared 2026-09-17 17:00 UTC, BEFORE any Scroll 1 stack is read
Reference: the Grand-Prize hand ink labels for segment 20231005123336 (all_labels/20231005123336_inklabels.png in the GP winners' repository,
7.91 µm UV, 29952×11008), covering the two central columns whose text was transcribed by papyrologists in 2023. Registered to the 2.4 µm
surface volume canvas (97280×34880, 109 slices) by ONE global scale+offset found by correlation against the team's ds8 ink overview
(scripts/s1_register_label.py); the fit is recorded before any crop is read. Caveat: the labels are hand-drawn on model output, then verified by
reading; they are the best available physical truth, not profilometry.
Classes: text = label; blank = no label AND ≥ 0.3 mm from any label AND inside the labelled zone (label closed with a 5 mm disc, so
unlabelled columns are never "blank"). Sheet mask = the v0.1b mask rule (on-sheet, macro-damage margin 0.4 mm, grains 0.02–0.1 mm).
Crops (rule): 1.5 cm squares (6250 px) on a 1250 px grid inside the labelled zone, ≥ 90 % on-sheet (level-3 mid slice > 0), ranked by label
density. TRAIN = the densest window in the left column. HELD-OUT = the two densest non-overlapping windows in the right column and the
densest window in the left column not overlapping TRAIN. Coordinates are written by scripts/s1_select_crops.py and frozen.
Judge per held-out crop: pixel AUC (score vs text/blank); letter AUC = P(mean score inside a labelled letter component ≥ 0.5 mm² > mean
score of a random blank disc of the same area, 200 discs per letter); the team 2.4 µm prediction judged identically as the comparator.
Bars (never edited): mean pixel AUC over the 3 held-out crops ≥ 0.80 AND mean letter AUC ≥ 0.90 → "reads verified text". Below that the
method is reported as failing, whatever the w028 numbers say.
Methods (declared now):
- S1-v1a — zero Scroll-1 supervision. Depth template from w028 D1: w_top(δ) = mean_text − mean_blank at the top anchor, w_bot(δ) at the
  bottom anchor, δ ∈ [−4, +6] slices, each normalised to unit L2; score_face = Σ_δ w_face(δ)·I(k_face + δ), then G 0.25 mm in the mask,
  z-scored. Both faces reported; the declared writing face is the one with the higher TRAIN-crop pixel AUC (chosen on TRAIN only).
- S1-v1b — templates re-measured on the TRAIN crop only (same construction), applied to the held-out crops. Thickness is monitored (AUC
  reported) but never enters the score.
- Comparators: v0.3p (peak, 0.25 mm) and the team's 2.4 µm prediction.
Disk order: Scroll 1 crops are fetched one at a time (4.3 GB each) after the w028 text3/text4 repair fetches finish; w028 v0.3f is dropped.
### GATE-T1 verdict, method v0.2 (inpainting term added), all 7 crops (2026-09-17 16:50 UTC) — stats/w028_gate_t1_v0.2.json
text1 0.487/0.548 | text2 0.494/0.584 | text3 0.540/0.469 | text4 0.500/0.570 | text5 0.498/0.546 | blank1 0.515/0.528 | blank2 0.452/0.510 (top/bot).
Mean on the writing face 0.504. **GATE-T1 FAILS for v0.2.** The inpainting residual adds nothing. Route B (papyrus subtraction) is closed on w028.
(text3/text4 here still on 61 % of their area; the repair is paused for disk and will re-issue them.)
### GATE-S1 registration (2026-09-17 17:10 UTC, before any crop was read)
label → canvas: canvas = label × 3.2217 + (266.7, 2013.3) px; zone-restricted correlation 0.330 against the team ds8 overview (binary label vs
soft prediction, so 0.33 is near the attainable maximum); visual check at 32 µm/px: label outlines sit on the letters to ≤ 1 px
(review_sheets/s1/label_overlay_crop.png). Residual scale 0.9775 relative to the nominal 7.91/2.4.
### GATE-S1 TRAIN crop results (2026-09-17 17:26 UTC; TRAIN numbers never count toward the bar)
bottom face = writing face (chosen on TRAIN per the rule). v1a (w028 template, zero S1 supervision): px 0.739 / letter 0.898 (top 0.639/0.681).
v1b (template measured on TRAIN): px 0.740 / letter 0.898 — identical to v1a: the ink depth signature measured on w028 transfers to Scroll 1.
v0.3p (peak brightness): 0.691 / 0.753. Team 2.4 µm model: 0.938 / 1.000. 18 label components ≥ 0.5 mm² in the crop.
### Declared BEFORE running on held-out crops: S1-v2 (designed on TRAIN only; held-out crops judged once with the TRAIN-selected setting)
Base = the v1b bottom-face projection p = Σ_δ w_bot(δ)·I(k_bot+δ) (raw, before smoothing; saved as proj_bot_v1b.npy).
Candidates (all with the v0.1b mask, normalised convolution): (a) ratio p / G_{1 mm}(peak) then G 0.25 mm; (b) band-pass G_{σ1}(p) − G_{σ2}(p)
for (σ1, σ2) ∈ {(0.10, 1.0), (0.15, 2.0), (0.25, 3.0)} mm; (c) ratio then band-pass with the same three pairs. Selection: the candidate with
the highest TRAIN pixel AUC becomes v2; recorded with all candidates' TRAIN numbers. Then applied unchanged to held1–held3. Bars unchanged.
Monitored on TRAIN (verified letters): thickness AUC 0.478, k_top 0.535, k_bot 0.524, peak (unsmoothed) 0.565. Old method v0.1b (papyrus
subtraction) 0.494 top / 0.557 bottom px. The topography premise is refuted against physically verified text as well.
### Declared BEFORE running: S1-v3 (fit on TRAIN only; held-out judged once)
Features per pixel: I(k_face+δ) for δ ∈ [−4, 6] (11 depths) on both faces, each smoothed at σ ∈ {0.05, 0.15, 0.40} mm (normalised
convolution in the mask) → 66 features, standardised on TRAIN. Model: ridge regression on ±1 labels (text/blank classes of the judge,
TRAIN pixels subsampled 2 %), λ chosen among {1e-2, 1e-1, 1, 10, 100} by a 2-fold row split of TRAIN (upper/lower half). Score = linear
output smoothed G 0.10 mm, z-scored. Interpretation recorded: the weight table (depth × scale × face). Applied unchanged to held1–held3.
Bars unchanged (px ≥ 0.80 and letter ≥ 0.90 on held-out). Anything fitted here is 67 numbers, all reported.
### GATE-S1 held1 (right column) — first held-out crop (2026-09-17 17:40 UTC): px / letter, 15 label components
v0.1b (subtraction) 0.543 / 0.408 | v1a 0.639 / 0.265 | v1b 0.643 / 0.265 | v0.3p 0.559 / 0.184 | team model 0.975 / 1.000 (bottom face).
The depth template does not generalise from TRAIN (0.74) to held1 (0.64); letter AUC < 0.5 means letter interiors score lower than blank
discs on average, i.e. the map is dominated by mm-scale blotches, not strokes.
### GATE-S1 v1 verdict, all crops (2026-09-17 18:12 UTC) — stats/s1_gate_20231005123336.json, bottom face, px / letter
| crop | v0.1b | v1a | v1b | v0.3p | team model |
|---|---|---|---|---|---|
| train (not counted) | 0.557 / 0.824 | 0.739 / 0.898 | 0.740 / 0.898 | 0.691 / 0.713 | 0.938 / 1.000 |
| held1 | 0.543 / 0.408 | 0.639 / 0.265 | 0.643 / 0.265 | 0.559 / 0.184 | 0.975 / 1.000 |
| held2 | 0.496 / 0.404 | 0.653 / 0.925 | 0.657 / 0.932 | 0.644 / 0.969 | 0.896 / 1.000 |
| held3 | 0.527 / — | 0.476 / — | 0.476 / — | 0.465 / — | 0.616 / — |
Held-out means: v1b 0.592 / 0.598; v1a 0.589 / 0.595; team 0.829 / 1.000. **S1-v1 FAILS the bar (0.80 / 0.90).** held3 has no letter
with ≥ 50 % valid pixels (14 components, heavy damage) and even the team model drops to 0.616 there, which flags a possible local
registration error of the global label transform in that corner; checked next (declared as an alignment check, applied to all methods alike).
### Registration refinement (declared 2026-09-17 18:20 UTC after the v1 verdict; alignment of the REFERENCE, applied to all methods alike)
Per-crop check of the global label transform against the team ds8 prediction (scripts/s1_local_reg_check.py): residual shifts train
(77, −154) µm, held1 (0, −77) µm, held2 (−384, 0) µm, held3 (998, −230) µm. Strokes are ≈ 0.4 mm wide, so held2/held3 were judged against a
misplaced reference (the team model itself drops to 0.62 on held3). Fix: one translation per crop, found by correlation against the team
prediction at 8-px (19 µm) resolution within ±1.2 mm, stored in crops.json as local_offset and used by the judge for every method. The
label→canvas transform is then canvas = label×3.2217 + (266.7, 2013.3) + local_offset. All v1-era numbers above stay on record as run;
every method is re-judged once with the refined reference. The team prediction is only used to place the reference, never as a label.
### GATE-S1 re-judged with the refined reference (2026-09-17 18:50 UTC), bottom face, px / letter
| crop | v0.1b | v1a | v1b | v0.3p | team model |
|---|---|---|---|---|---|
| train (not counted) | 0.573 / 0.830 | 0.742 / 0.913 | 0.743 / 0.927 | 0.692 / 0.621 | 0.951 / 0.990 |
| held1 | 0.541 / 0.468 | 0.639 / 0.274 | 0.644 / 0.274 | 0.557 / 0.194 | 0.982 / 1.000 |
| held2 | 0.521 / 0.648 | 0.679 / 0.963 | 0.683 / 0.973 | 0.659 / 0.900 | 0.967 / 1.000 |
| held3 | 0.484 / 0.154 | 0.629 / 0.821 | 0.628 / 0.795 | 0.627 / 0.667 | 0.857 / 1.000 |
Held-out means: v1b 0.651 / 0.681; v1a 0.649 / 0.686; v0.3p 0.614 / 0.587; v0.1b 0.515 / 0.423; team 0.935 / 1.000.
The team model at 0.935 confirms the reference is now well placed. **S1-v1 FAILS (bar 0.80 / 0.90).** The papyrus-subtraction method
is at chance against verified text. The w028-derived depth template (no Scroll-1 supervision) carries a real but weak ink signal.
### w028 text3/text4 repair dropped (2026-09-17 19:05 UTC)
Disk on this machine cannot hold both the Scroll 1 verified-text work and the w028 refetches. The repair cannot change the w028 verdict
(text1, text2, text5 and both blanks already put every w028 method at chance), so it is dropped; the text3/text4 numbers stay marked as
computed on 61 % of their area. The w028 per-crop base maps (except text1) are deleted; uint8 score maps and all JSON records remain.
### Post-hoc check v0.3p-hp result (partial: text1–text4 and blank1; run ended when the w028 base maps were deleted for disk)
v0.3php vs v0.3p (top): text1 0.647 vs 0.654 | text2 0.622 vs 0.602 | text3 0.637 vs 0.714 | text4 0.700 vs 0.710 | blank1 0.545 vs 0.523.
Removing scales > 3 mm keeps most of the agreement: it is mainly letter-scale; text3's drop (0.71 → 0.64) shows part of its number was a
density gradient. Closed; no bar attempt.
### Declared BEFORE running: S1-v5 — surface-aligned small CNN (fit on TRAIN only; held-out judged once)
Input: the 22 face-aligned depth samples I(k_face+δ), δ ∈ [−4, 6], both faces, mean-pooled 8× to 19.2 µm/px (stroke ≈ 20 px), standardised
per crop by the median/MAD over the mask; plus the mask as a 23rd channel. Model: U-Net, channels 24/48/96, two down-samplings, ≈ 250 k
parameters, receptive field ≈ 1.2 mm. Training: TRAIN crop only, 128×128 patches, random flips/rot90, BCE on masked text/blank pixels
(judge classes), Adam 1e-3, batch 16, 4000 steps, seed 0; 15 % of TRAIN rows (a contiguous band) held out for early-stopping only.
Output: sigmoid map upsampled 8× (bilinear) to the crop grid, judged exactly like every other method. Bars unchanged.
What this tests: whether surface-aligned depth sampling plus 1.5 cm of verified training text suffices to read held-out text.
Honesty clause: this is a learned detector; its claim is only what the held-out crops show, and every parameter file is kept.
### Declared BEFORE running: GATE-S1 transfer segment 20231210121321 (one column, 17 lines of Grand-Prize text; label 12544×15872 at 7.91 µm)
Everything fitted on segment 20231005123336 (v1b template, v2 setting, v3 weights, v5 U-Net) is applied unchanged; every crop here is
held-out. Reference: the GP label registered by the same global-scale + per-crop-offset procedure; on-sheet map from the 2.4 µm surface
render ds8 (> 12, opened/closed), validated on segment 1 against the level-3 mid slice (98.3 % agreement). Stack window k = 24…84 (the
mesh sheet sits at the centre of the 109-slice stack; tightly wound neighbours fill the rest). Crops: the 4 densest non-overlapping
1.5 cm windows (rule in scripts/s1_select_crops.py, all-held mode). Judge and bars unchanged; the same 4 comparators reported.
### Segment 20231210121321 registration (2026-09-17 20:55 UTC): canvas = label × 3.2217 + (66.7, 106.7) px; zone correlation 0.361;
visual check review_sheets/s1/label_overlay_crop_20231210121321.png (outlines on the letters). Per-crop offsets follow the same rule.
### S1-v2 result (2026-09-17 21:20 UTC): TRAIN candidates a 0.698, b0 0.631, b1 0.712, b2 0.768, c0 0.610, c1 0.670, c2 0.722 → chosen b2
(band-pass 0.25–3 mm of the depth projection, no ratio). Held-out (px / letter): held1 0.636 / 0.242, held2 0.749 / 0.995, held3 0.663 / 0.872;
mean 0.683 / 0.703 (v1b 0.651 / 0.681; team 0.935 / 1.000). **S1-v2 FAILS the bar.** held1 is the outlier for every method of ours
(letter AUC < 0.5) while the team model reads it at 0.982; its depth profile is examined with the pooled stacks from the v5 stage.
Crop geometry check (2026-09-17 21:30 UTC): all four segment-1 crops have the same sheet geometry (median thickness 22.6–24.6 slices ≈ 57 µm,
faces at k ≈ 26 / 54), so held1 is not a face-assignment failure. Its brightness contrast is simply the weakest: median crest intensity
text − blank = 1.4 (held1) vs 3.8 (train), 2.5 (held2), 3.0 (held3) uint8 units. The team model reads held1 from cues other than brightness.
### Declared BEFORE any v5 result is read (2026-09-17 21:50 UTC): additional labelled segments and the v6 plan
Segments 20230929220926 (label 23552×9984) and 20231012184424 (label 20231012184423, 23552×15872) are registered by the same procedure.
Role: TRAINING data only, for S1-v6 = the v5 architecture and recipe trained on segment-1 TRAIN plus the 4 densest 1.5 cm windows of each
of these two segments (12 000 steps, same early-stopping band on segment-1 TRAIN). HELD-OUT for v6 stays exactly segment-1 held1–held3 and
segment-2 (20231210121321) held1–held4: none of those crops is ever used for fitting or selection. Bars unchanged. If v5 already
passes, v6 is still run to report the effect of training data; if v5 fails, v6 tests whether data, not the surface-aligned input, is the limit.
### S1-v3 result (2026-09-17 21:35 UTC): ridge on 66 multi-depth multi-scale features, λ = 1 (2-fold CV on TRAIN 0.730, n = 235 k px)
TRAIN 0.773 / 0.883; held1 0.650 / 0.274; held2 0.684 / 0.954; held3 0.637 / 0.769 → held-out mean 0.657 / 0.666 (v2 0.683 / 0.703).
Largest weights: bottom face δ = −4…−2 at σ 0.40 and 0.15 mm (the inside-the-bottom-face depth band found by D1), then the top face δ = +2…+4.
**S1-v3 FAILS.** The linear family (v1–v3) saturates at 0.65–0.68 px on held-out verified text: more linear features fit TRAIN better and
generalise no better. Whatever the team model uses beyond this is non-linear 2-D/3-D context. v5 (surface-aligned small U-Net) runs next.
### Extra-segment registrations (2026-09-17 21:45 UTC): 20230929220926 canvas = label × 3.2382 + (80.0, 173.3), corr 0.378;
20231012184424 canvas = label × 3.1887 + (66.7, 173.3), corr 0.312. Overlays in review_sheets/s1/label_overlay_crop_<seg>.png; per-crop
offsets follow in the preparation driver. Training-only segments (v6); never judged.
### Declared BEFORE the v6 preparation runs (2026-09-17 21:50 UTC): blank-class veto on TRAINING segments only
The labels of 20230929220926 and 20231012184424 are partial (overlays show unlabelled letters next to labelled words). For those two
segments only, blank = no label AND ≥ 0.3 mm from any label AND team ds8 prediction < 0.10 at that pixel; text = label. This uses the team
model only to keep unlabelled ink out of the negatives of the training set; the evaluation crops (segment-1 held1–held3, segment-2
held1–held4) keep their complete GP labels and never see this veto.
### D2 result (2026-09-17 21:55 UTC): per-depth pixel AUC on verified text, 19.2 µm pooled stacks (δ = −4…+6 slices)
train  top max 0.570 (δ 0) | bot max 0.579 (δ −3…−2)
held1  top max 0.538 (δ −1) | bot max 0.564 (δ −4), second bump 0.539 at δ +3
held2  top max 0.571 (δ +1) | bot max 0.563 (δ −3)
held3  top max 0.559 (δ +1) | bot max 0.572 (δ −1)
No single depth exceeds 0.58 anywhere: the ink's per-pixel brightness contrast on Scroll 1 at 2.4 µm is weak and its depth of maximum
varies by crop (held1 differs). The 0.94–0.98 of the team model therefore comes from spatial integration over strokes and letter shapes,
not from any pixel-wise physical contrast. This bounds what any pixel-wise or linear "physics" score can reach on this data.
### S1-v5 training record (2026-09-17 22:05 UTC, while running): step 0 train 0.751 / val 0.657; 250: 0.320 / 1.396; 500: 0.137 / 2.573;
750: 0.095 / 2.898; 1000: 0.060 / 2.342. The 270 k-parameter net memorises the single 1.5 cm training crop (≈ 50 letters); no checkpoint
beats initialisation on the validation band, so the early-stopped v5 model is essentially untrained. Its held-out numbers are recorded when
the run ends but the verdict is already determined: **v5 as declared cannot pass.**
### v6 recipe amended BEFORE it runs (2026-09-17 22:06 UTC): Adam lr 3e-4 (was 1e-3), weight decay 1e-4 (was 0), 12 000 steps, same
architecture, patches, augmentation and early-stopping band; training set = segment-1 TRAIN + 8 crops of the two extra segments (blank veto).
Reason: the v5 overfitting above. Held-out set unchanged.
### S1-v5 result (2026-09-17 22:40 UTC): validation BCE rose monotonically from 0.657 (step 0) to 3–6 while training BCE fell to 0.010;
the early-stopped model is the initialisation. Held-out px / letter: held1 0.545 / 0.000, held2 0.506 / 0.447, held3 0.540 / 0.897
(train 0.544 / 0.248). **S1-v5 FAILS** (as recorded in advance). One 1.5 cm crop cannot train a 270 k-parameter detector.
### v6 amended BEFORE it runs (2026-09-17 22:41 UTC): early stopping on a WHOLE separate crop instead of a row band — held4 of
20231012184424 is removed from the training set and used only for validation/checkpoint selection (never judged, never trained on).
Training set = segment-1 TRAIN + 7 extra crops. lr 3e-4, wd 1e-4, 12 000 steps as amended above. Held-out set unchanged.
### GATE-S1 transfer segment 20231210121321 (2026-09-18 00:02 UTC): all four crops held-out, nothing fitted on this segment; pixel AUC, bottom face
| crop | v0.1b | v0.3p | v1a | v1b | v2 | v3 | v5 | team model |
|---|---|---|---|---|---|---|---|---|
| held1 | 0.542 | 0.621 | 0.606 | 0.609 | 0.610 | 0.619 | 0.490 | 0.980 |
| held2 | 0.595 | 0.752 | 0.699 | 0.700 | 0.723 | 0.719 | 0.536 | 0.980 |
| held3 | 0.548 | 0.585 | 0.631 | 0.634 | 0.633 | 0.652 | 0.506 | 0.900 |
| held4 | 0.429 | 0.665 | 0.722 | 0.720 | 0.742 | 0.742 | 0.523 | 0.975 |
Means: v0.1b 0.528 | v0.3p 0.656 | v1a 0.664 | v1b 0.666 | v2 0.677 | v3 0.683 | v5 0.514 | team 0.958. Same ceiling as segment 1 (0.65–0.68):
the linear surface-physics family saturates identically on a second segment with verified text. Letter AUC was undefined on all four
crops (no label component met the ≥ 50 % valid-pixel rule); diagnosed below, pixel AUC unaffected.
### Judge mask J (declared 2026-09-18 00:20 UTC, BEFORE re-running; applied to every method and the comparator alike)
Diagnosis: segment 20231210121321 is a finer lace (on-sheet 0.44–0.46 vs 0.59–0.70 on segment 1); the v0.1b mask's 0.4 mm margin around
all macroscopic damage then leaves 3–9 % of each crop (segment 1: 35 %), so the transfer numbers above rest on tiny areas, the letter test is
undefined, and the v6 training crops would be nearly empty. The 0.4 mm margin served the relief method, which is dead. Mask J = the v0.1b
rule with the margin reduced to 0.1 mm (opening 0.05 mm, grain rule, thickness and validity criteria unchanged). Every Scroll 1 crop
(segments 1 and 2, training segments) is recomputed with mask J and every method re-judged; the v0.1b-mask results above stay on record.
Fitted artefacts (v1b template, v2 setting, v3 weights, v5 net) are NOT refitted: the seg-1 TRAIN crop re-judged under mask J is reported
but still not counted. v6 is trained on mask-J crops as declared.
### Segment 1 under mask J (2026-09-18 01:21 UTC; judged area 53–56 % of each crop), bottom face, px / letter
| crop | v0.1b | v0.3p | v1b | v2 | v3 | v5 | team |
|---|---|---|---|---|---|---|---|
| train (not counted) | 0.558 / 0.67 | — | 0.733 / 0.87 | 0.756 / 0.90 | 0.761 / 0.89 | 0.538 / 0.42 | 0.949 / 1.00 |
| held1 | 0.555 / 0.60 | — | 0.649 / 0.72 | 0.639 / 0.70 | 0.659 / 0.70 | 0.545 / 0.45 | 0.978 / 1.00 |
| held2 | 0.547 / 0.69 | — | — | 0.768 / 0.90 | 0.699 / 0.69 | — | 0.967 / 1.00 |
| held3 | 0.531 / 0.68 | — | — | 0.638 / 0.64 | 0.619 / 0.61 | — | 0.852 / 1.00 |
Held-out means: v0.1b 0.544 / 0.658 | v0.3p 0.628 / 0.664 | v1a 0.644 / 0.659 | v1b 0.646 / 0.662 | v2 0.681 / 0.745 | v3 0.659 / 0.666 |
v5 0.531 / 0.460 | team 0.932 / 0.999. The held1 letter values < 0.5 under the old mask were mask artefacts (letters mostly masked);
the pixel numbers are unchanged. Verdicts unchanged: every method of ours fails the 0.80 / 0.90 bar.
### Segment 2 under mask J (2026-09-18 02:40 UTC; judged area ≈ 33 % of each crop), bottom face, px / letter
| crop | v0.1b | v0.3p | v1b | v2 | v3 | v5 | team |
|---|---|---|---|---|---|---|---|
| held1 | 0.582 / — | — | — | 0.545 / — | 0.569 / — | — | 0.961 / — |
| held2 | 0.557 / 0.99 | — | — | 0.574 / 1.00 | 0.588 / 1.00 | — | 0.925 / 1.00 |
| held3 | 0.586 / — | — | — | 0.681 / — | 0.674 / — | — | 0.895 / — |
| held4 | 0.534 / 0.45 | — | — | 0.634 / 0.27 | 0.611 / 0.64 | — | 0.926 / 1.00 |
Means (4 crops): v0.1b 0.565 | v0.3p 0.594 | v1a 0.593 | v1b 0.595 | v2 0.608 | v3 0.610 | v5 0.507 | team 0.927 (letter, 2 crops:
v2 0.63, v3 0.82, team 1.00). Letter AUC stays undefined on held1/held3 (merged word-sized label components, none ≥ 50 % valid).
Across both segments (7 held-out crops, mask J): v2 0.64, v3 0.63, v1b 0.62, v0.1b 0.55, team 0.93. **Every method of ours fails.**

## Exploration phase E1 (declared 2026-09-18 03:45 UTC, BEFORE it runs): what do we not see that the team model does?
Every declared physics measure has failed (0.55–0.68 held-out px AUC vs bar 0.80) while the team model reads the same crops at 0.93.
E1 is an EXPLORATION, not a gate: eight independent investigations, each fitting only on the TRAINING crops (20231005123336/train,
20230929220926/held1–4, 20231012184424/held1–3) and reporting the evaluation crops (20231005123336/held1–3, 20231210121321/held1–4)
once. Hypotheses declared now: (1) stroke-shape matched integration vs isotropic smoothing; (2) fibre-frame background removal and why
v0.1b's version failed; (3) two-face / through-thickness coupling; (4) depth-profile SHAPE (edge sharpness) rather than level;
(5) reference-noise audit (AUC vs distance inside letters, team model under the same restriction, agreement off-label, registration
bound); (6) per-crop calibration and geometry conditioning, leave-one-crop-out inside TRAINING; (7) RESOLUTION: the same per-depth
contrast measured at 1.129 µm on segment 20231210121321 against 2.4 µm; (8) a broad simple-feature sweep to bound what simple physics
can reach. Every claimed gain above baseline + 0.02 is adversarially re-measured by two independent agents (leakage lens, artifact lens).
Standing rule: NOTHING from E1 counts as a gate result. A measure that survives E1 must be re-declared as a new method version with its
bars, then judged once on the evaluation crops. E1's role is to tell us where the signal is, honestly, including negative results.

## Stroke test (declared 2026-09-18 03:50 UTC, BEFORE running; replaces the letter test, applied to every method and comparator alike)
Problem measured: the declared letter test needs label components of >= 0.5 mm^2 with >= 50 % valid pixels. On segment 20231210121321
the hand labels merge into word-sized components (13-17 per crop, median valid fraction 0.02-0.08), so the test is UNDEFINED on 5 of the
7 evaluation crops and the 0.90 letter bar cannot be evaluated. The defect is in the test, not the methods.
Stroke test: sample disks of radius 0.25 mm (104 px at 2.4 um). INK disks = centres where the label is true and the distance to the
nearest non-label pixel is >= 0.25 mm (i.e. the disk lies inside a stroke), and >= 50 % of the disk is inside the judge mask.
BLANK disks = centres where the label is false, distance to the nearest label pixel >= 0.5 mm, same mask condition. Score of a disk =
mean of the score map over its masked pixels. Statistic = AUC of ink-disk scores vs blank-disk scores, up to 2000 disks per class drawn
with seed 0 on a 0.25 mm grid to avoid overlap. It measures exactly what the letter test was for - detection integrated over a
stroke-sized support - and is defined wherever strokes and blank both exist.
Bar: the declared pass condition becomes pixel AUC >= 0.80 AND stroke AUC >= 0.90 on the held-out mean. The letter numbers already
recorded stay on record; where both are defined both are reported.
### Stroke test results (2026-09-18 04:05 UTC), all 7 evaluation crops, defined everywhere (175–760 disks per class per crop)
| crop | v0.1b | v1b | v2 | v3 | team |
|---|---|---|---|---|---|
| seg1 held1 | 0.602 | 0.690 | 0.679 | 0.691 | 1.000 |
| seg1 held2 | 0.601 | 0.730 | 0.831 | 0.744 | 0.998 |
| seg1 held3 | 0.520 | 0.616 | 0.670 | 0.630 | 0.936 |
| seg2 held1 | 0.658 | 0.592 | 0.573 | 0.599 | 0.998 |
| seg2 held2 | 0.645 | 0.695 | 0.710 | 0.729 | 0.982 |
| seg2 held3 | 0.591 | 0.579 | 0.592 | 0.596 | 0.947 |
| seg2 held4 | 0.513 | 0.717 | 0.754 | 0.708 | 0.970 |
| (seg1 train, not counted) | 0.636 | 0.837 | 0.866 | 0.879 | 0.992 |
Held-out means: v0.1b 0.590 | v1b 0.660 | v2 0.687 | v3 0.671 | team 0.976. The stroke test tracks the pixel AUC closely and does NOT
rescue any method: integrating our scores over a stroke-sized support gains nothing, while the team model is near-perfect at that support.
The earlier letter AUCs of 0.70–0.75 were inflated by the component test's valid-pixel rule. **Every declared method fails both bars.**

### E1 partial results (2026-09-18 05:30 UTC, exploration — not a gate)
- **fibre frame (no signal).** Real anisotropic papyrus texture exists (autocorrelation 47–181 µm along vs 38–50 µm across). It carries
  no ink contrast: widening the across-fibre window 13× (3.6 → 48 µm) changes held-out AUC by 0.004. Why v0.1b failed is now measured:
  at its σ_t = 6 px the orientation field is noise (median top-vs-bottom-face disagreement 24.6°, chance 45°); it becomes physical only
  at σ_t ≥ 25 px (12–16°). Best variant held-out 0.660 vs v2 0.640.
- **stroke shape (dead as stated).** The optimal 41×41 linear kernel fitted on TRAIN comes out radially symmetric; its stroke-frame
  anisotropic counterpart and its own radial average score identically (0.6754 / 0.6755 / 0.6742). Measured stroke width 0.70 mm.
  One real gain: smoothing each depth channel BEFORE combining beats project-then-smooth (LOCO 0.714 vs 0.672) — the best depth
  signature differs by spatial scale, which no fixed depth template can express. Held-out 0.666 vs 0.640.
- **two faces (no payoff, but decisive physics).** The NON-writing face — 50–60 µm of papyrus away from the ink — reads verified text
  held-out at 0.623, indistinguishable from the writing face at 0.636. The ink-correlated contrast is NOT surface-local. It is a level
  effect, not a profile-shape effect (LVL 0.663 > SHAPE21 0.636 LOCO). Two-face features gain only +0.008 over one face.
  Data-contract correction recorded: k_top and k_bot are both 50 %-of-peak crossings, so the δ = 0 channels of the two faces are the
  same quantity (corr 0.96); the middle 25–35 µm of the sheet is unsampled by our features.

## Local stroke test L (declared 2026-09-18 05:35 UTC, BEFORE running; applied to every method and the comparator alike)
The three E1 findings above are all consistent with an alternative to "we see faint ink": that our scores carry only REGIONAL
information (areas that bear writing are systematically brighter/denser) and no letter-level information at all. A signal that is not
surface-local, not stroke-shaped, and is a pure level effect is exactly what a regional confound looks like. Test L settles it.
For every ink disk of the stroke test (0.25 mm radius, centre ≥ 0.25 mm inside a stroke), draw the blank disks whose centres lie
within 1.5 mm of it and ≥ 0.5 mm from any label, and score the pair. Statistic L = fraction of (ink, local blank) pairs in which the
ink disk scores higher, over all such pairs, equally weighted per ink disk. L is the same quantity as the stroke AUC except that ink
is only ever compared with blank papyrus a stroke or two away, so any contrast varying on scales above ~2 mm cancels.
Reading rule declared now: if a method's stroke AUC is well above 0.5 while L ≈ 0.5, that method has NO letter-level information and
its apparent performance is regional. Bars are unchanged; L is diagnostic and is reported for every method including the team model.

### Local stroke test L result (2026-09-18 05:50 UTC), 7 evaluation crops, L / stroke AUC
| crop | v0.1b | v1b | v2 | v3 | team |
|---|---|---|---|---|---|
| seg1 held1 | 0.611/0.602 | 0.757/0.690 | 0.762/0.679 | 0.809/0.691 | 1.000/1.000 |
| seg1 held2 | 0.634/0.601 | 0.853/0.730 | 0.858/0.831 | 0.877/0.744 | 0.998/0.998 |
| seg1 held3 | 0.562/0.520 | 0.674/0.616 | 0.664/0.670 | 0.693/0.630 | 0.946/0.936 |
| seg2 held1 | 0.579/0.658 | 0.657/0.592 | 0.654/0.573 | 0.692/0.599 | 1.000/0.998 |
| seg2 held2 | 0.637/0.645 | 0.793/0.695 | 0.788/0.710 | 0.793/0.729 | 0.980/0.982 |
| seg2 held3 | 0.538/0.591 | 0.520/0.579 | 0.500/0.592 | 0.523/0.596 | 0.973/0.947 |
| seg2 held4 | 0.569/0.513 | 0.689/0.717 | 0.654/0.754 | 0.663/0.708 | 0.988/0.970 |
Means: v0.1b 0.590/0.590 | v1b 0.706/0.660 | v2 0.697/0.687 | v3 0.722/0.671 | team 0.984/0.976.
The regional-confound hypothesis is REFUTED for v1b/v2/v3: comparing a stroke with blank papyrus 1–2 strokes away is EASIER
(+0.05 mean, up to +0.13 on seg1 held1/held2) than comparing it with distant blank. The scores do carry letter-level information;
a regional brightness component costs ≈ 0.05 globally. For v0.1b (papyrus subtraction) L = stroke = 0.590: it has no local
information either, consistent with every other measurement of it. The team model is 0.98 both ways (no regional component).

## Method v7 (declared 2026-09-18 05:55 UTC, BEFORE fitting or judging)
Motivation, stated honestly: the regional component was noticed via L measured on the EVALUATION crops. Every design choice and
every parameter below is nevertheless selected by leave-one-crop-out on the 8 TRAINING crops only, and L is re-measured there first
to confirm the effect exists in training data. The evaluation crops are touched once, at the end.
Construction, on the 19.2 µm surface-aligned pooled stacks (ds8_x: 22 face-anchored depth channels + coverage):
1. Per-channel multi-scale smoothing BEFORE combining (E1 "shape": LOCO 0.714 vs 0.672 for project-then-smooth): normalised-convolution
   Gaussians at σ ∈ {0.05, 0.10, 0.25, 0.60} mm applied to each of the 22 channels → 88 features.
2. Regional removal: each feature f is replaced by f − G_{σ_R}(f) (normalised convolution in the mask), σ_R chosen from
   {1.0, 1.5, 2.5, 4.0} mm by LOCO on the TRAINING crops. The un-removed variant (σ_R = ∞) is one of the candidates.
3. Model: ridge regression on ±1 text/blank labels, all 88 features standardised per crop, λ from {0.1, 1, 10, 100, 1000} by the same
   LOCO. Output smoothed at 0.10 mm, z-scored in the mask, upsampled ×8 bilinearly to the 2.4 µm judge grid.
4. Judged once on the 7 evaluation crops: pixel AUC, stroke AUC, L. Bars unchanged (pixel ≥ 0.80 AND stroke ≥ 0.90).
Everything fitted is 88 weights + 2 hyperparameters, all reported.
### Honesty note on v7's motivation (2026-09-18 06:20 UTC, before the fit finished)
The training-crop confirmation of the local-vs-global effect could NOT be obtained: 7 of the 8 training crops have no score maps (the
preparation driver builds only pooled stacks for them), and on the one that does (segment-1 TRAIN) L = 0.827 is LOWER than its stroke
AUC 0.879 — the opposite sign to the evaluation crops. So the regional-removal step is NOT confirmed on training data. It remains in v7
only as one candidate among five (σ_R ∈ {1.0, 1.5, 2.5, 4.0} mm and no-removal), decided by leave-one-crop-out on the training crops.
Recorded so the motivation cannot later be read as stronger than it was.

## Data-integrity incident 3 (found 2026-09-18 06:30 UTC): the declared blank veto removed EVERY negative on the training segments
The training-segment veto declared on 2026-09-17 ("blank also requires team ds8 prediction < 0.10") is unsatisfiable: the team's
downsampled overview JPEG has a soft background floor and never falls below 0.10 anywhere on those crops (measured: fraction of the
crop below 0.10 = 0.000 on 20230929220926/held1, 20231012184424/held1 and /held4; mean value 0.30–0.40). Consequently all 7
extra-segment training crops carry text pixels and ZERO blank pixels (measured: 40–60 k text, 0 blank each).
Consequences, both recorded as invalid:
- **v6 is invalid.** Its training set was 7 all-positive crops plus segment-1 TRAIN, and its early-stopping crop (20231012184424/held4)
  is also all-positive, so its falling validation BCE (0.657 → 0.022) measured nothing but "predict ink everywhere". The run was stopped
  at step 4000 of 12000 and its checkpoint is discarded, not judged.
- **v7's first fit failed** for the same reason (leave-one-crop-out folds with no negatives return an undefined AUC).
Fix, declared now, before any re-run: blank additionally requires the team ds8 prediction to be below its own 40th percentile over that
crop's masked, label-free area — a per-crop, self-calibrating threshold that cannot be empty by construction and keeps the original
intent (exclude the most ink-like unlabelled pixels from the negatives). The evaluation crops are unaffected: they never used a veto.

### E1 reference-noise audit (2026-09-18 06:00 UTC, exploration) — the most informative result so far
Measured on the 7 evaluation crops:
- **Our measures detect real ink, in the right place.** The cross-stroke profile of v1b/v2/v3 rises monotonically into the stroke and
  peaks 0.53 mm inside it, the same place the team map peaks (0.48 mm), against a centreline bin of 0.57 mm. There is no registration
  offset in our scores. What differs is amplitude: contrast-to-noise across the stroke is 1.6 (v2) vs 6.3 (team) — a factor of 4.
- **Reference noise is real but small.** Label-noise attenuation bounds our de-noised AUC at 0.675 (held-out mean); the measured
  registration residual is 165 µm rms, while pulling a perfect detector down to our 0.65 would take 0.82–0.99 mm. Eroding both classes
  by 0.3 mm lifts ours 0.640 → 0.730 and the team 0.929 → 0.984. So ≈ 0.07 of the 0.29 gap is reference noise, ≈ 0.22 is missing method.
- **Our scores see the same physical thing the learned model sees.** On unlabelled on-sheet area they separate the team's confident ink
  calls from its confident blanks at 0.68 (v2), with no label involved; and on label-vs-team disagreement pixels our scores side with the
  team (AUC 0.34–0.45, inverted), the signature of a correct detector judged against a slightly wrong reference.
- Label geometry measured: stroke half-width median 0.161 mm, max 0.618 mm. 7–29 % of "text" pixels are called blank by the team model.
Conclusion recorded: the papyrus-subtraction route is dead, but the brightness-excess signal is genuine ink physics, detected at the
right place and about four times too weakly. The gap is amplitude, i.e. spatial and contextual integration, not localisation.

## Method v6b (declared 2026-09-18 06:10 UTC, BEFORE training, replacing the invalid v6)
Identical to the amended v6 recipe except that its data are correct: the surface-aligned small U-Net (270 k parameters, 23 input
channels at 19.2 µm, patches 128², flips/rot90, Adam lr 3e-4, weight decay 1e-4, 12 000 steps, seed 0) trained on segment-1 TRAIN plus
the 7 extra-segment crops whose negatives are now non-empty under the quantile veto (measured after the fix: 45–60 k text and 47–77 k
blank pooled pixels per crop), with 20231012184424/held4 (56 k text, 77 k blank) as the validation crop for checkpoint selection only.
Judged once on the 7 evaluation crops: pixel AUC, stroke AUC, L. Bars unchanged (pixel ≥ 0.80 AND stroke ≥ 0.90).
Justification recorded in advance: the audit above localises the deficit as amplitude, not position, and the E1 shape probe showed the
optimal LINEAR pooling kernel is radially symmetric and saturates — so a non-linear stroke-scale model on the depth stack is the
declared next test of whether the missing factor of 4 is recoverable at all from these voxels.
### Process note (2026-09-18 06:30 UTC): v7 fit rewritten for memory, no change to the declared method
The first v7 fit was killed by the OOM reaper (8.9 GB resident) while holding every training row in memory. The fit now accumulates
per-crop Gram matrices [X 1]'[X 1] and [X 1]'y (89×89 each) and forms each leave-one-crop-out fold by subtracting that crop's Gram, so
memory is constant in the pixel count (263 MB measured). This is an exact reformulation of the same ridge problem, and it removes the
15 % pixel subsample the first attempt needed: the fit now uses every labelled on-sheet pixel of the 8 training crops. The declared
method, its feature set, its candidate grids and its one-shot judging are unchanged.

### v7 result (2026-09-18 07:10 UTC), fitted on the 8 TRAINING crops, judged once on the 7 evaluation crops
Chosen by leave-one-crop-out on TRAINING: σ_R = 4.0 mm, λ = 0.1, LOCO 0.7416. The regional-removal step DID help in training
(LOCO 0.7416 at σ_R = 4.0 vs 0.7232 with no removal, +0.018), and the best value sat at the edge of the declared grid.
| crop | seg1 h1 | seg1 h2 | seg1 h3 | seg2 h1 | seg2 h2 | seg2 h3 | seg2 h4 | mean |
|---|---|---|---|---|---|---|---|---|
| v7 pixel AUC | 0.696 | 0.791 | 0.663 | 0.562 | 0.623 | 0.681 | 0.663 | **0.668** |
Held-out means, all three tests: v7 pixel 0.668 / stroke 0.712 / L 0.757; v2 0.681 / 0.687 / 0.713; v3 0.659 / 0.671 / 0.735;
team 0.932 / 0.976 / 0.983.
**v7 FAILS both bars** (pixel ≥ 0.80, stroke ≥ 0.90). It is the best of our methods on the stroke and local tests and slightly below v2
on pixel AUC. Training LOCO 0.742 against held-out 0.668 is a 0.074 generalisation gap across segments, and segment 2 is the weaker half
(0.562–0.681 vs 0.663–0.791), the same segment split seen in every earlier method.

### v6b result (2026-09-18 10:30 UTC), trained on the 8 corrected TRAINING crops, judged once on the 7 evaluation crops
| crop | pixel | stroke | L |
|---|---|---|---|
| seg1 held1 | 0.844 | 0.928 | 0.951 |
| seg1 held2 | 0.919 | 0.986 | 0.998 |
| seg1 held3 | 0.755 | 0.840 | 0.841 |
| seg2 held1 | 0.773 | 0.879 | 0.888 |
| seg2 held2 | 0.748 | 0.876 | 0.952 |
| seg2 held3 | 0.827 | 0.877 | 0.875 |
| seg2 held4 | 0.759 | 0.848 | 0.955 |
| **mean** | **0.804** | **0.891** | **0.923** |
**v6b PASSES the pixel bar (0.804 ≥ 0.80) and FAILS the stroke bar (0.891 < 0.90).** Under the declared pass condition
(pixel ≥ 0.80 AND stroke ≥ 0.90) v6b does not pass, but it is a large, real advance over every hand-built measure:
v7 0.668 / 0.712 / 0.757, v2 0.681 / 0.687 / 0.713, team 0.932 / 0.976 / 0.983.
Recorded honestly: the judged checkpoint is from **step 750 of 12 000**, the validation minimum (BCE 0.704). Validation diverges
immediately after (0.90 at step 1000, 1.51 at 2000, 1.36 at the end) while the training loss falls to 0.090 — the network memorises
its 8 training crops within a few hundred steps. 94 % of the declared training budget was wasted, and the result is therefore a
statement about a LIGHTLY trained network, not about the declared 12 000-step recipe.

## Control v6c (declared 2026-09-18 10:35 UTC, BEFORE running) — is v6b distilled from the team model?
v6b's negatives were chosen with the team model in the loop: the quantile veto keeps as "blank" only the 40 % least ink-like
label-free pixels per crop, as judged by the team's own prediction. That is a channel through which the team model's knowledge can
enter our training set, and with v6b now at the pixel bar this channel has to be measured rather than assumed harmless.
v6c is identical to v6b in every respect — same architecture, same 8 crops, same lr/wd/steps/seed, same validation crop, same
early stopping, same one-shot judging — except that its negatives are ALL label-free on-sheet pixels between 0.3 mm and 5.0 mm from
any label, with NO team-model veto. Nothing from the team model touches its training data.
Reading rule declared now: if v6c holds near v6b, the veto is not doing the work and v6b's result stands as our own. If v6c collapses
toward the hand-built methods (≈ 0.67), then v6b is substantially distillation from the team model and must be reported as such, not
as physics recovered from the CT.

### Control v6c result (2026-09-18 14:00 UTC) — the veto is worth +0.02, not the result
Identical recipe, negatives with NO team-model veto (nothing from the team model touches its training data).
| | pixel | stroke | L |
|---|---|---|---|
| v6b (team-vetoed negatives) | 0.804 | 0.891 | 0.923 |
| **v6c (no team model at all)** | **0.785** | **0.874** | **0.882** |
| v7 (best hand-built) | 0.668 | 0.712 | 0.757 |
| team 2.4 µm model | 0.932 | 0.976 | 0.983 |
Per-crop v6c pixel: 0.807 / 0.899 / 0.726 (seg1 held1–3), 0.767 / 0.745 / 0.824 / 0.725 (seg2 held1–4).
Under the reading rule declared in advance, v6c holds near v6b (−0.019 pixel, −0.017 stroke), so **v6b is not substantially
distillation**: the team-model veto contributes ≈ +0.02 pixel AUC and the rest is learned from the CT and the hand labels alone.
**Neither passes both bars.** v6b passes pixel (0.804 ≥ 0.80) and fails stroke (0.891 < 0.90); v6c fails both.
Recorded: v6c's judged checkpoint is step **250** of 12 000 (val BCE 0.655), v6b's was step 750. Both peak within a few hundred steps
and then diverge — with only 8 training crops the network memorises almost immediately. Two defects in the recipe are now measured
rather than suspected: the training set is far too small, and checkpoints are selected by validation BCE while the bars are AUC.

## Method v8 (declared 2026-09-18 14:20 UTC, BEFORE preparing data, fitting or judging)
v6b/v6c measured two defects in the learned recipe: the training set is too small (the network memorises 8 crops within 250–750 steps)
and checkpoints are selected by validation BCE while the declared bars are AUC. v8 fixes exactly those two things and nothing else.
1. **More training data, from the pure-training segments only.** The declared crop rule ("the densest non-overlapping windows", which
   is deterministic and density-ordered, so the existing crops keep their identity) is extended from 4 to 8 windows on 20230929220926
   and on 20231012184424. No extra crop is taken from either EVALUATION segment (20231005123336, 20231210121321) — those two segments
   contribute only the single pre-existing segment-1 TRAIN crop, exactly as before. Training set: 1 + 8 + 7 = 16 crops
   (20231012184424/held4 stays the validation crop and is never trained on). The evaluation crops are untouched.
2. **Checkpoint selection by validation pixel AUC**, evaluated on the validation crop every 250 steps, instead of validation BCE.
Negatives carry NO team-model veto (the v6c data), so v8 is fully independent of the team model. Architecture, lr 3e-4, wd 1e-4,
12 000 steps and seed 0 are unchanged from v6b/v6c. Judged once on the same 7 evaluation crops: pixel AUC, stroke AUC, L.
Bars unchanged: pixel ≥ 0.80 AND stroke ≥ 0.90.
Recorded in advance: the three remaining labelled segments (20231005123333, 20231007101615, 20231012184423) CANNOT be added — their
surface volumes are not published in the open-data bucket. 20231005123333 would in any case have been excluded as a probable
near-duplicate of the evaluation segment 20231005123336.
### v8 data rule AMENDED (2026-09-18 14:45 UTC, before any crop was prepared) — to what the labelled area actually supports
The declared "extend from 4 to 8 windows on both pure-training segments" is not achievable and was replaced before any data was built.
Measured (scripts/count_train_windows.py, diagnostic only): under the UNCHANGED strict window criteria (label-zone coverage >= 0.99,
on-sheet coverage >= 0.90, non-overlapping) 20230929220926 supports NO additional window beyond its 4 - the segment's labelled band is
four crops wide, and even at relaxed criteria only one more appears - while 20231012184424 supports 7 more, taking its labelled-pixel
coverage from 15.8 % to 39.3 %. The existing 4 crops of each segment cover only 31.0 % and 15.8 % of their labelled pixels respectively.
Amended rule, unchanged in criteria and still deterministic: take ALL non-overlapping windows the strict rule admits, rather than the
densest 4. That gives 4 crops on 20230929220926 and 11 on 20231012184424. Training set for v8: 1 (segment-1 TRAIN) + 4 + 10 = 15 crops
(20231012184424/held4 remains the validation crop and is never trained on), up from 8. Everything else in the v8 declaration stands:
no team-model veto, checkpoints chosen by validation pixel AUC, same architecture/lr/wd/steps/seed, judged once, bars unchanged.

## Strategy note (2026-09-18 16:00 UTC): inverting the question — what would guarantee failure?
Listed without flattery, then checked against what this project has actually done.
1. **Never look at unread papyrus.** Our crop rule requires label-zone coverage >= 0.99, so every crop we have ever processed sits
   inside text papyrologists have already read. A perfect detector under this rule yields zero new characters. GUILTY, by construction.
2. **Optimise a ranking statistic instead of legibility.** AUC over a huge blank class can improve while letterforms stay unreadable.
   Partly guilty: the stroke test and L were added for this reason, but nothing yet measures whether a human could read the output.
3. **Insist on originality before competence.** The 2023 Grand Prize was won and its approach is public: large models on the native
   surface volume, many segments, heavy augmentation and ensembling. We have never once reproduced a known-good recipe as a baseline;
   every method here was invented from scratch. GUILTY, and this is the Munger point — inventing before reproducing.
4. **Throw away resolution before the model sees it.** Our data is 2.4 um. The learned methods here train on 19.2 um pooled input, an
   8x lateral decimation, and the Grand-Prize work used 7.91 um — finer than what we feed our own network. GUILTY.
5. **Starve the model.** 8 training crops (now 15), covering 31 % and 16 % of the labelled pixels on the two pure-training segments,
   against a network that memorises them within 250-750 steps. GUILTY, partially addressed by v8.
6. **Confuse a measured ceiling with a physical one.** The audit showed our measures sit at the right place on the stroke with 1/4 the
   contrast-to-noise, and that reference noise explains only 0.07 of the 0.29 gap. The remaining gap is method, not physics.
The two that are cheapest to fix and most likely binding are (4) and (5). Which one binds is an empirical question, and guessing it
costs 3-7 CPU-hours per wrong guess, so it is worth one cheap diagnostic first.

## Diagnostic D2 (declared 2026-09-18 16:05 UTC, BEFORE running) — does our input representation even carry the signal?
Question: is the 19.2 um pooled surface stack (ds8_x) an information bottleneck, or is our limit training data and capacity?
Method: train the SAME network on the SAME 15 training crops to regress the TEAM model's prediction (not the hand labels), then
measure on the 7 evaluation crops (a) agreement with the team map and (b) pixel AUC against the verified-text labels.
This is a DIAGNOSTIC and can never be a method of ours: it is distillation from the team model and is excluded from every table of
results by construction. Its only purpose is to bound what our input representation can support.
Reading rule declared now: if D2 reaches ~0.90 pixel AUC from ds8 input, the pooled representation retains the signal and the binding
constraint is labelled data and training, so the next method scales data and capacity at 19.2 um. If D2 plateaus near our current 0.80,
the pooling is destroying the signal and the next method must work at 9.6 um or finer, matching the Grand-Prize scale.

## Baseline GP-R (declared 2026-09-18 16:40 UTC, BEFORE implementing or running) — reproduce the known-good approach
Failure mode 3 of the strategy note: this project invented seven methods without ever reproducing the approach that actually won the
Grand Prize. GP-R fixes that. It is run as a BASELINE, judged exactly like our own methods, on the same evaluation crops.
**What the winning approach is, stated with its uncertainty.** From the 2023 Kaggle Ink Detection solutions and the Grand-Prize ink
model, the structural elements I am confident of: (i) the input is a stack of CT slices around the segmented surface at native
resolution, not a pooled projection; (ii) the network is a 3D convolutional encoder over that slice axis feeding a 2D segmentation
decoder ("3D-to-2D"); (iii) training is patch-based with heavy dihedral and intensity augmentation; (iv) the loss combines
binary cross-entropy with a soft-Dice term; (v) inference uses test-time augmentation over the dihedral group, and the published
results ensemble several folds/models. Details I am NOT certain of and therefore do not claim to reproduce exactly: the precise
backbone (ResNet3D/I3D/SegFormer variants were all used by different teams), the exact patch size and slice count, and the exact
augmentation list. Where I am unsure I choose the simplest option and record it. The original work used GPUs and 7.91 µm data;
this machine has 4 CPU cores and no GPU, so the reproduction is scaled, and that is a difference in degree that must be remembered
when reading the numbers.
**Split into two baselines so each ingredient is attributable** (changing resolution and architecture together would tell us nothing):
- **GP-R1** — GP-style architecture and training protocol on the EXISTING 19.2 µm pooled stacks, same 15 training crops, same
  no-team-veto labels, same validation crop, same one-shot judging as v8. Isolates what the architecture and protocol are worth.
  3D encoder over the 22-channel depth axis collapsing to 2D, 2D decoder; patches 128² (2.46 mm, matching the GP's ~1.8 mm extent);
  BCE + soft Dice; dihedral and intensity augmentation and cutout; 8-fold dihedral TTA at inference; checkpoint by validation AUC.
- **GP-R2** — the same at 9.6 µm (ds4), which is the Grand-Prize working scale and 2× finer than anything we have fed a model.
  Requires rebuilding the depth stacks from the raw CT (the full-resolution stacks were deleted for disk), about 15 min per crop.
  Isolates what resolution is worth. Declared now, run after GP-R1.
Bars unchanged (pixel ≥ 0.80 AND stroke ≥ 0.90). Diagnostic D2 is deferred: GP-R2 answers the same resolution question directly.
### GP-R1 parameters fixed (2026-09-18 16:55 UTC, BEFORE training)
Measured on this machine: the faithful-width 3D encoder costs 6.7 s/step (22 h for 12 000 steps), which is not runnable here. The
encoder is therefore scaled — widths 8/16/32 and a stride-2 depth convolution in each of its three blocks (22 → 11 → 6 → 3 slices,
then averaged), lateral resolution untouched — giving 489 k parameters and 1.97 s/step. Step budget **4000** (2.2 h), justified by
measurement rather than convention: v6b and v6c peaked at steps 750 and 250 of 12 000 and diverged thereafter, so 4000 steps with
checkpoint selection by validation AUC covers the useful range with margin. Patch 128² (2.46 mm), batch 8, Adam lr 3e-4, wd 1e-4,
seed 0. Augmentation: full dihedral group, intensity scale 0.9–1.1 and offset N(0, 0.05), 25 % cutout with probability 0.3.
Inference averages the 8 dihedral transforms. Training crops, labels, validation crop and judging are identical to v8.

## Method E (declared 2026-09-18 19:00 UTC, BEFORE v8's or GP-R1's results are known)
Ensembling is the one element of the winning approach still missing from everything we have run. E is declared now, while both of its
components are still training and neither result has been seen, so nothing about it can be chosen after the fact.
E = per-crop rank-normalisation of the v8 and GP-R1 score maps within the judge mask (each mapped to its own rank in [0,1], which makes
the two comparable without any fitted scaling), averaged with equal weight, then smoothed with a Gaussian of sigma = 0.08 mm.
The smoothing scale is fixed in advance at half the measured stroke half-width (0.161 mm median, from the E1 label geometry), not tuned.
Both components use no-team-veto labels, so E is fully independent of the team model. Judged once on the same 7 evaluation crops:
pixel AUC, stroke AUC, L. Bars unchanged: pixel >= 0.80 AND stroke >= 0.90.
If E fails, it fails on the record with everything else; no weighted or re-smoothed variant will be introduced afterwards to rescue it.

## v8 RESULT (2026-09-18 19:15 UTC) — **the first method of ours to pass both declared bars**
Trained on the 15 declared crops with no-team-veto labels (nothing from the team model touches its training data), checkpoint chosen by
validation AUC, judged once on the 7 evaluation crops.
| crop | pixel | stroke | local L |
|---|---|---|---|
| seg1 held1 | 0.817 | 0.886 | 0.888 |
| seg1 held2 | 0.916 | 0.979 | 0.992 |
| seg1 held3 | 0.758 | 0.862 | 0.823 |
| seg2 held1 | 0.855 | 0.943 | 0.891 |
| seg2 held2 | 0.818 | 0.939 | 0.972 |
| seg2 held3 | 0.862 | 0.901 | 0.807 |
| seg2 held4 | 0.851 | 0.908 | 0.981 |
| **mean** | **0.840** | **0.917** | **0.908** |
**PASSES: pixel 0.840 >= 0.80 AND stroke 0.917 >= 0.90**, on the held-out mean as the bars were declared. Progression of the learned
branch: v6c 0.785/0.874 (8 crops, BCE selection) -> v6b 0.804/0.891 (8 crops, team-vetoed) -> **v8 0.840/0.917** (15 crops, AUC selection,
no team model). The team's 2.4 um model remains ahead at 0.932/0.976.
Verified before recording: the training list contains no evaluation crop (segment-1 TRAIN plus 4 crops of 20230929220926 and 10 of
20231012184424); segment-1 TRAIN does not overlap held1-3; labels were ds8_y_noveto.npy throughout; the crops were judged exactly once.
Qualifications recorded with the result, because the bars are a mean:
- Two crops are individually below the stroke bar (seg1 held1 0.886, seg1 held3 0.862), and seg1 held3 is below the pixel bar at 0.758.
  The bars were declared on the held-out mean, and on that basis v8 passes; per-crop, 5 of 7 clear both.
- The judged checkpoint is step 9500 of 12 000, against step 750 for v6b and 250 for v6c on 8 crops. More data removed the immediate
  memorisation this project measured earlier, which is the mechanism behind the gain and confirms data was a binding constraint.
- This is agreement with verified text, not a reading of new text. No character has been recovered from unread papyrus.

## Reading run R1 (declared 2026-09-18 19:45 UTC, BEFORE any window is chosen or any output is seen)
Every crop this project has ever processed lies inside text that has already been read. R1 is the first run on UNREAD papyrus, so the
discipline is tighter than for validation: there is no ground truth to catch a mistake, and the failure mode is inventing letters.
**Window rule, fixed now and applied mechanically.** On each of the two evaluation segments, consider windows of 6250 px (15 mm) whose
on-sheet coverage is >= 0.90 and which contain NO labelled pixel within 5 mm (i.e. entirely outside the read zone and its margin).
Among those, take the one whose centre is NEAREST the labelled zone — adjacent to read text is where the same column most likely
continues — with the tie broken by the lower row index. One window per segment, chosen by this rule before any score map is computed.
**Detector.** v8 exactly as judged (same weights, no retraining, no tuning), which passed both declared bars on held-out verified text.
**What will be reported.** The rendered score map, at the same scale and stretch as the validation renders, and nothing else. I will
describe only what is visible in the image. I will NOT transcribe characters, propose readings, or name letters unless a shape is
unambiguous in the image itself, and any such statement will be marked as a candidate requiring papyrological review, never as a result.
No plausible-looking text will be produced under any circumstances; an empty or illegible result will be reported as empty or illegible.
**Corroboration, not truth.** The team's 2.4 um model is rendered on the identical window as an INDEPENDENT second opinion. Agreement
between two independently built detectors on a letterform is evidence; the team model is not ground truth and is not used to select,
score, threshold or adjust anything in R1.
**Negative control, declared now and reported whatever it shows.** The same detector is rendered on a window of comparable on-sheet
coverage that lies OFF any text column (the farthest such window from the labelled zone on the same segment). If letterforms appear
there too, the letterforms in the reading windows mean nothing, and R1 will be reported as a failure.
### R1 windows selected (2026-09-18 19:55 UTC), mechanically, before any score map was computed
| segment | window | canvas y0,x0 | distance to nearest label |
|---|---|---|---|
| 20231005123336 | unread1 (reading) | 14880, 8680 | 12.5 mm |
| 20231005123336 | control1 (negative control) | 23560, 89280 | 43.6 mm |
| 20231210121321 | unread1 (reading) | 11160, 1240 | 13.1 mm |
| 20231210121321 | control1 (negative control) | 1240, 0 | 17.6 mm |
354 and 13 windows were admissible respectively. Deviation recorded: segment 20231005123336 has no onsheet_ds8.png, so its on-sheet
coverage was taken from the surface render instead. Verified afterwards that all four windows are genuinely on sheet (surface coverage
0.97, 0.89, 0.94, 0.91), so the substitution did not admit an off-sheet window.

## R1 RESULT (2026-09-18 21:00 UTC) — no letters recovered; the run is reported as a failure of its stated goal
**No legible character was recovered from unread papyrus.** The v8 renders of both reading windows show fibre texture and damage-mask
discs, with no letterform visible to me at any point. Nothing is transcribed, nothing is proposed as a reading.
Measured rather than eyeballed — AUC of v8 separating the team model's confident ink (> 0.80) from its confident blank (< 0.20), on the
identical unread windows:
| window | distance from read text | team-ink pixels | v8 AUC |
|---|---|---|---|
| 20231005123336 unread1 | 12.5 mm | 810 k | 0.802 |
| 20231005123336 control1 | 43.6 mm | 2 618 k | 0.717 |
| 20231210121321 unread1 | 13.1 mm | 261 k | 0.739 |
| 20231210121321 control1 | 17.6 mm | 483 k | 0.865 |
So v8 is NOT blind on unread papyrus: it detects the same features an independently built detector calls ink, at 0.72–0.87. What it
lacks is contrast against the fibre texture — the same contrast-to-noise deficit the E1 audit measured, still present after v8 cleared
the statistical bars. Statistical detection and legibility are different things, and R1 is the measurement that separates them.
**The negative control was invalid by construction, and that is a design error of mine.** It assumed distance from labelled text implies
absence of ink. It does not: the team model finds 2.6 M confident-ink pixels in the segment-1 control window, more than in the reading
window. On these scrolls almost every on-sheet region carries unread writing, so "far from labels" selects unread text, not blank papyrus.
A valid blank control has to be chosen by evidence of absence (e.g. a region both detectors call blank, or a margin/interval), not by
distance. No conclusion in this record rests on the control as declared.
**Also recorded:** the team model's own output on these windows is blobby rather than cleanly legible, so the best available detector
does not yield readable text here either. Regions left unread by papyrologists are plausibly the harder ones, which is a selection effect
R1's window rule walked straight into by choosing windows adjacent to where reading stopped.

## GP-R1 RESULT (2026-09-18 21:20 UTC) — the winning architecture buys us nothing at this resolution
Reproduction of the Grand-Prize-style approach (3D encoder over the depth axis -> 2D decoder, BCE + soft Dice, full dihedral and
intensity augmentation with cutout, 8-fold dihedral TTA), on the same 15 crops, same no-veto labels, same validation crop, judged once.
| | pixel | stroke | local L |
|---|---|---|---|
| **GP-R1** (GP-style, 489 k params, TTA) | **0.828** | **0.920** | 0.912 |
| **v8** (our plain 2D U-Net, 270 k params, no TTA) | **0.840** | 0.917 | 0.908 |
| team 2.4 µm model | 0.932 | 0.976 | 0.983 |
Per-crop GP-R1 pixel: 0.844 / 0.923 / 0.788 (seg1), 0.855 / 0.803 / 0.815 / 0.766 (seg2). Checkpoint step 3500 of 4000.
**Both pass both bars, and they are tied** (GP-R1 −0.012 pixel, +0.003 stroke against v8; well inside the spread across crops).
Conclusion recorded: at 19.2 µm on 15 crops, the 3D-to-2D architecture, the Dice term, the heavy augmentation and 8-fold TTA together
are worth approximately nothing over a plain 2D U-Net. This is a useful negative result and it relocates the remaining 0.09 gap to the
team model: it is not architecture. The candidates left are resolution (we feed 19.2 µm; the Grand-Prize work used 7.91 µm) and the
scale of data and compute. GP-R2 at 9.6 µm is the declared next test and is now the highest-value experiment in the project.
It also retires failure mode 3 of the strategy note: the known-good approach has now been reproduced and measured, not assumed.

## Ensemble E RESULT (2026-09-18 21:35 UTC) — best result of the project, declared before its components were known
| crop | pixel | stroke | local L |
|---|---|---|---|
| seg1 held1 | 0.883 | 0.939 | 0.929 |
| seg1 held2 | 0.953 | 0.992 | 0.996 |
| seg1 held3 | 0.810 | 0.896 | 0.890 |
| seg2 held1 | 0.904 | 0.984 | 0.993 |
| seg2 held2 | 0.852 | 0.968 | 0.998 |
| seg2 held3 | 0.885 | 0.897 | 0.805 |
| seg2 held4 | 0.847 | 0.871 | 0.933 |
| **mean** | **0.876** | **0.935** | **0.935** |
Full standing of every method, held-out means over the same 7 crops:
| method | pixel | stroke | local |
|---|---|---|---|
| **E (v8 + GP-R1, rank-mean, 0.08 mm)** | **0.876** | **0.935** | **0.935** |
| v8 (2D U-Net, 15 crops) | 0.840 | 0.917 | 0.908 |
| GP-R1 (Grand-Prize-style, TTA) | 0.828 | 0.920 | 0.912 |
| v6b (8 crops, team-vetoed) | 0.804 | 0.891 | 0.923 |
| v7 (best hand-built physics) | 0.668 | 0.712 | 0.757 |
| team 2.4 µm model | 0.929 | 0.976 | 0.983 |
**E passes both bars with margin** (0.876 vs 0.80, 0.935 vs 0.90) and is our best result. Every pixel of it is independent of the team
model. Its components were tied with each other and E beats both by +0.036/+0.015 over the better one, which is the ordinary ensembling
gain from decorrelated errors — and it is the last cheap win available: two models were combined, not twenty.
Per-crop, 6 of 7 clear the pixel bar and 5 of 7 the stroke bar; seg2 held4 is the weakest at 0.847/0.871.
The remaining gap to the team model is 0.053 pixel and 0.041 stroke. GP-R1 established it is not architecture; resolution is the
declared next test.

## Reading run R2 (declared 2026-09-18 21:40 UTC, BEFORE running) — the best detector on the same unread windows
R1 used v8 and recovered nothing legible, while measuring that v8 does detect ink there (AUC 0.72–0.87 against the team model).
E is materially stronger (0.876/0.935 against 0.840/0.917) and its rank-mean plus 0.08 mm smoothing is exactly the kind of noise
reduction R1's failure pointed at. R2 applies E, unchanged, to the IDENTICAL four windows chosen mechanically for R1 — no new window is
selected, so there is no opportunity to shop for a better-looking region.
All R1 rules carry over unchanged: no transcription, no proposed readings, candidate shapes marked as requiring papyrological review,
an illegible result reported as illegible, and the team map shown only as an independent second opinion. The R1 control windows are
included and remain invalid as blank controls for the reason already recorded, so they are reported as additional unread windows, not
as controls. The same agreement statistic (AUC of our score against the team model's confident ink vs confident blank) is reported
alongside each render, so R2 is judged on a number as well as on my reading of an image.

## R2 RESULT (2026-09-19 00:20 UTC) — detection improved, legibility did not follow
Ensemble E, unchanged, on the identical four windows of R1. AUC against the team model's confident ink vs confident blank:
| window | v8 (R1) | E (R2) | change |
|---|---|---|---|
| 20231005123336 unread1 | 0.802 | **0.887** | +0.085 |
| 20231005123336 control1 | 0.717 | **0.804** | +0.087 |
| 20231210121321 unread1 | 0.739 | **0.797** | +0.058 |
| 20231210121321 control1 | 0.865 | **0.880** | +0.015 |
E agrees with an independently built detector on unread papyrus at 0.80–0.89, a large improvement over v8 and close to what E scores
against hand labels on read crops (0.876). **And still no legible character appears in any render.** Nothing is transcribed.
This is the central result of the two reading runs, and it is now measured twice with two detectors: on unread papyrus our detection
improves with every gain in AUC, while legibility does not follow at all. The limit is not whether the ink is found — it is found —
but contrast against fibre texture at the scale of a stroke, the same deficit the E1 audit put at a factor of four and which no amount
of the statistical improvement recorded in this file has removed.
Recorded honestly as a limitation of the render itself: rank-normalisation makes the score uniform by construction, so the display
stretch is filled by texture. A calibrated probability output would render better and is worth doing, but it would change the picture,
not the underlying contrast, and no rendering choice will be used to claim a letter that the measurement does not support.

## Confirmation test C1 (declared 2026-10-15, BEFORE any window is selected, fetched or scored)
Why: every method from v1 to E was judged on the same 7 evaluation crops, and each new method was designed after reading the previous
method's numbers on them. Even with every individual judgement made once, the SEQUENCE adapts to the evaluation set, so the headline
numbers carry an unknown optimistic bias. C1 measures that bias directly on labelled papyrus no step of this project has touched.
**Windows (mechanical, fixed now).** On each of the two evaluation segments (20231005123336, 20231210121321) — never used for training —
take 6250 px (15 mm) windows meeting the ORIGINAL strict crop criteria (label-zone coverage >= 0.99, on-sheet coverage >= 0.90 on the
segment's on-sheet image: onsheet_ds8.png where it exists, else the CT mid-slice overview mid_l3.png), non-overlapping with EVERY window
this project has processed on that segment (crops.json and unread.json), in descending label density, up to 3 per segment.
The per-crop reference refinement (s1_refine_reg.py) is applied to them exactly as it was to the evaluation crops, written to a separate
file data/s1/<seg>/confirm.json so the evaluation crop records are not touched.
**Methods, all frozen — no retraining, no re-fitting, no tuning.** E (the declared ensemble of v8 and GP-R1), v8, GP-R1, v7 (best
hand-built baseline, frozen weights stats/s1_v7_weights.json), the team 2.4 um model (POSITIVE control), and a cross-crop label-swap null
(NEGATIVE control: each crop's score map judged against another crop's labels, all ordered pairs, which preserves the spatial structure
of both and should sit near 0.5 if the detector reads letters rather than texture statistics).
**Metrics.** Pixel AUC (mask J), stroke AUC, local stroke test L — the same judge code, unchanged.
**Prediction, stated in advance.** E clears both bars on the C1 mean (pixel >= 0.80, stroke >= 0.90) and beats v7 on every C1 crop.
Expected: some shrinkage relative to the 7 evaluation crops; its size IS the measurement. Whatever C1 shows is reported as-is; no
method, window or metric will be changed after any C1 number is seen.
**Statistical plan for the release (fixed now).** Crop-level percentile bootstrap, 10 000 resamples, seed 0, for every mean and for every
paired difference between methods; effective n stated as crops (and segments); no pixel-level CI is presented as if pixels were
independent.

## Post-hoc decomposition D3 (declared 2026-10-15, AFTER E's result was known — labelled post-hoc, not a gate)
E = rank-mean of v8 and GP-R1, THEN smoothed at 0.08 mm. The +0.036 pixel gain of E over v8 was credited to ensembling, but smoothing
alone could produce part of it, and the methods being compared were also upsampled differently (v8/GP-R1 nearest-neighbour, v7 bilinear).
D3 separates the two on the same 7 evaluation crops with the same judge: (a) v8 alone, rank-normalised and smoothed 0.08 mm; (b) GP-R1
alone, the same; (c) the rank-mean of v8 and GP-R1 WITHOUT smoothing; (d) E as published. Because it is defined after E's result, it
cannot support any claim of a pre-registered gain; it can only qualify the existing one, and it is reported whatever it shows.

## Post-hoc null N1 for the reading runs (declared 2026-10-15, AFTER R1/R2 — labelled post-hoc)
R1 and R2 reported that our detectors separate the team model's confident ink from its confident blank on unread windows at AUC
0.72–0.89 (v8) and 0.80–0.89 (E). That agreement statistic was introduced after R1's result and was never given a null. The label-swap
null on read crops (results/stats_evaluation7.json) shows single-crop AUCs reaching ~0.69 from spatial layout alone, so a per-window
agreement of 0.7–0.9 is weaker evidence than R1/R2 implied. N1 measures it: each unread window's score map against every OTHER window's
team-confident classes (all ordered pairs of the four R1 windows), for v8 and E, beside the matched values. Reported whatever it shows.

## D3 RESULT (2026-10-15, post-hoc) — ensembling survives; smoothing is a minority share; the architecture tie is a tie either way
results/d3_decomposition.json, 7 evaluation crops, crop-level bootstrap (10 000, seed 0); values truncated.
| variant | pixel | stroke | local L |
|---|---|---|---|
| v8 as published | 0.839 | 0.916 | 0.907 |
| v8 rank-normalised + smoothed 0.08 mm | 0.847 | 0.914 | 0.916 |
| GP-R1 as published | 0.827 | 0.919 | 0.912 |
| GP-R1 rank-normalised + smoothed 0.08 mm | 0.857 | 0.917 | 0.917 |
| rank-mean of v8 and GP-R1, NO smoothing | 0.864 | 0.934 | 0.936 |
| E as published | 0.876 | 0.935 | 0.934 |
Of E's +0.036 pixel gain over v8 [0.020, 0.051]: smoothing alone gives +0.008 [0.007, 0.010] (7/7 crops); ensembling without smoothing
gives +0.024 [0.007, 0.039] (6/7); ensembling given smoothing (E − smoothed v8) +0.028 [0.012, 0.041] (6/7). On the stroke metric
smoothing contributes nothing (−0.002) and E's +0.018 stroke gain is ensembling. So the ensembling claim survives, with roughly a quarter
to a third of the pixel gain being smoothing. GP-R1 benefits much more from smoothing (+0.029) than v8 (+0.008) because it was upsampled
nearest-neighbour while v8 was upsampled bilinearly; compared like for like (both smoothed) GP-R1 − v8 = +0.009 [−0.019, 0.033] (5/7) —
still a tie, with the sign reversed relative to the published comparison. The published "architecture buys nothing" therefore stands only
as "no measurable architecture effect at 19.2 µm on 7 crops".

## N1 RESULT (2026-10-15, post-hoc) — the reading-run agreement is above its null
results/n1_reading_null.json. Agreement AUC (team confident ink vs confident blank), judge 5 % subsample. v8 matched 0.801 / 0.716 / 0.737
/ 0.864 (seg1 unread1, seg1 control1, seg2 unread1, seg2 control1); null over the 12 ordered window pairs: mean 0.519, range 0.304–0.641.
E matched 0.886 / 0.804 / 0.793 / 0.879; null mean 0.509, range 0.246–0.652. All 4 matched windows exceed the largest null pair for both
detectors. The R1/R2 statement "detected, but not legible" is therefore supported by a null; the unread-window agreement is not an artefact
of layout. (n = 4 windows, 2 segments; no legible character recovered, unchanged.)

## C1 RESULT (2026-10-15, pre-registered 46a4bfc) — the prediction holds for E; v8 and GP-R1 alone do not clear the bars on untouched crops
results/stats_confirmation.json (scripts/release_stats.py), results/c1_analysis.json (scripts/c1_analysis.py), run log results/logs/c1.log.
6 untouched windows (3 per evaluation segment, stats/c1_confirm_<seg>.json), frozen weights, same judge. Crop-level bootstrap 10 000,
seed 0. Values truncated toward zero; differences given to 4 decimals.
| method | pixel [95 % CI] | stroke [95 % CI] | local L [95 % CI] |
|---|---|---|---|
| E | 0.830 [0.800, 0.856] | 0.928 [0.905, 0.947] | 0.926 [0.912, 0.941] |
| v8 | 0.774 [0.754, 0.796] | 0.881 [0.859, 0.908] | 0.889 [0.861, 0.914] |
| GP-R1 | 0.786 [0.750, 0.818] | 0.908 [0.869, 0.942] | 0.920 [0.901, 0.938] |
| v7 | 0.618 [0.573, 0.650] | 0.664 [0.593, 0.731] | 0.716 [0.641, 0.780] |
| team 2.4 um model (positive control) | 0.899 [0.873, 0.922] | 0.978 [0.956, 0.992] | 0.982 [0.967, 0.996] |
Per-crop E pixel: 0.872, 0.819, 0.842 (segment 1), 0.764, 0.823, 0.861 (segment 2). Stroke disks per crop: ink 36–107, blank 227–855.
**Prediction: HELD.** E's C1 means clear both bars (pixel 0.8305 >= 0.80, stroke 0.9282 >= 0.90; also at the CI lower bounds,
0.8002 and 0.9055). E beats v7 on every C1 crop on pixel AUC (6/6) and on stroke AUC (6/6). Disclosure: the declaration did not name the
metric for "beats v7"; scripts/c1_analysis.py, which checks it, was committed (d2564a7) after 4 of the 6 C1 pixel values had been seen in
the run log, so it reports both metrics; both hold.
**Shrinkage (the measurement C1 exists for)**, C1 mean minus evaluation mean, two-sample crop bootstrap: E pixel −0.0456 [−0.0885, −0.0055],
stroke −0.0070 [−0.0450, 0.0305], L −0.0085; v8 pixel −0.0649 [−0.1029, −0.0248]; GP-R1 −0.0410 [−0.0912, 0.0053]; v7 −0.0503
[−0.1131, 0.0079]. The positive control also loses pixel AUC on these crops: team −0.0297 [−0.0674, 0.0087]. Post-hoc (added after 4 of 6
values were seen, descriptive only): the team − E gap widens from 0.0527 (evaluation) to 0.0686 (C1), i.e. by 0.0159.
**Negative control** (label swap, 30 ordered pairs): E null mean 0.546, range 0.361–0.654; team 0.558, 0.339–0.671; every matched E crop
(min 0.764) lies above the largest null pair.
**Paired, C1:** E − v8 pixel +0.055 [0.037, 0.069] (6/6), E − GP-R1 +0.043 [0.037, 0.051] (6/6), v8 − GP-R1 −0.012 [−0.025, 0.010] (1/6).
**Reading (INFERENCE).** The headline survives untouched data, but with less margin: E's pixel lower bound sits at the bar. Of E's 0.046
pixel loss, about 0.03 is matched by the positive control, consistent with harder windows (the C1 windows are the next-densest after
excluding every processed window: label density 0.200–0.253 vs 0.233–0.293 on the evaluation crops); the remaining ~0.016 is consistent
with optimistic bias from reusing the evaluation set, and n = 6 + 7 crops cannot separate it from noise. **v8's evaluation-set pass does
not replicate** (C1 0.774 / 0.881, both below the bars), so the claim "v8 passes both bars" is narrowed to the evaluation set; only the
pre-declared ensemble passes on untouched crops. v1b and v0.1b appear in the C1 records because crop preparation computes them; they
were not among C1's declared methods and carry no verdict. Nothing was changed after any C1 number was seen.

## Release corrections to the C1 RESULT (2026-10-15, appended; the entry above is left as written)
1. **Timing of the analysis script.** The C1 RESULT says scripts/c1_analysis.py was committed "after 4 of the 6 C1 pixel values had been
   seen". By the run log (results/logs/c1.log) five of the six crops had finished when it was committed (20231210121321:conf2 "done" at
   06:03:52 UTC; d2564a7 committed at 06:08:20 UTC), so the disclosure is: written after 4 values had been read, committed after 5 had been
   judged. The prediction is unaffected (it was declared in 46a4bfc); the metric used for "beats v7" and the two-sample shrinkage interval
   were chosen in that script, and both metrics are reported.
2. **Full-precision stroke and L.** The release statistics now use the toolkit's full-precision stroke AUC and L for the 65 method-crop
   pairs it recomputed (each equal to its 4-decimal research record; results/toolkit_vs_records.json) instead of the half-up 4-decimal
   records. In the C1 RESULT table above this changes one value: v7 local L interval [0.641, 0.780] becomes [0.641, 0.779]. The shrinkage
   bounds change in the fourth decimal (E stroke [−0.0451, 0.0305]). Every verdict and every pixel value is unchanged.

## Release note on paths (2026-10-15, appended)
Paths named in this notebook are as they were when written. In the release reorganisation (b370331) superseded scripts moved to
`archive/scripts/` (for example `scripts/select_crops_w028.py`, `scripts/depth_profile_diag.py`, `scripts/explore/`), and `METHOD.md`,
`STATE.md`, `docs/report_2026-09-17.md` and `docs/reproduce.md` moved to `archive/docs/` (see `archive/README.md`); this notebook itself
moved from the repository root to `docs/RULES.md` (043ba8d). `git show <commit>:<old path>` reads any file as it was.
