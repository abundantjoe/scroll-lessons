# Results

Every number here is copied from a committed file named beside it; the generated sheet
[`results/FACTS.md`](../results/FACTS.md) (`scripts/release_facts.py`) prints the means, intervals, per-crop values, paired differences,
label-swap nulls, D3, N1 and the pre-registration order directly from the result files. It does not print the C1 shrinkage table, the
disk counts, or the notebook and exploratory values of §7–§9.

**Labels.** **VERIFIED**: re-checked for this release by re-running code or against an independent source. **MEASURED**: produced
by the committed pipeline and recorded in the named file. **INFERENCE**: our interpretation, which a reader may reject.
**Reporting rule.** Values are truncated toward zero at three decimals, never rounded up. Where the lab notebook printed a value
rounded up, both appear and the correction is listed in [`SUPERSEDED_CLAIMS.md`](SUPERSEDED_CLAIMS.md).
**Unit of replication.** The crop (a 15 mm × 15 mm window, 6250² px at 2.4 µm), never the pixel. Pixels within a crop are spatially
correlated, and the label-swap null (§4) shows a single crop can reach AUC 0.69 from layout alone.

| set | crops | segments | used for | status |
|---|---|---|---|---|
| training | 15 (v8, GP-R1) / 8 (v6b, v6c, v7) / 1 (v1b, v2, v3, v5; v1a used none, its template came from w028) | 3 (20230929220926, 20231012184424, 20231005123336 TRAIN crop) | fitting | — |
| validation | 1 (20231012184424/held4) | — | checkpoint selection | — |
| **evaluation** | **7**: 20231005123336 held1–3, 20231210121321 held1–4 | 2 | judging every method since S1-v1 | reused across 13 methods |
| **confirmation C1** | **6**: conf1–3 on each evaluation segment | 2 | judged once, frozen weights | untouched until 2026-10-15 |
| unread windows | 4: unread1 + control1 on each evaluation segment | 2 | reading runs R1, R2 | no labels exist |

Crop coordinates: `stats/s1_crops_<segment>.json` (evaluation), `stats/c1_confirm_<segment>.json` (C1), `stats/r1_unread_<segment>.json`
(unread). Registrations: `stats/s1_registration_<segment>.json`.

---

## 1. Pre-registered tests and their order

Every test below was declared in the lab notebook [`RULES.md`](RULES.md). `scripts/check_preregistration.py` finds the commit that
introduced the declaration heading and the result heading of 16 of the 18 rows below, plus the post-hoc D3 and N1, with `git log -S` and
checks their order (VERIFIED, `results/preregistration_order.json`): every declaration heading precedes its result heading. The two rows
it does not cover, S1-v2/S1-v3 and v6, were checked by hand against the times of their declaration and result commits (table): each
declaration commit precedes its result commit (VERIFIED). These checks are necessary, not sufficient.
**Three exceptions (the first two VERIFIED by inspecting the commits; the third rests on file times that are not in git):**
- **Stroke test** — its declaration commit d27193f already contains `stats/stroke_test.json` with results on one evaluation crop
  (20231005123336:held1) for v0.1b, v1b, v2, v3 and the team model: the test was declared and first run in one step, so git cannot
  show that the definition preceded the numbers. It replaced a test that was undefined on 2 of 7 crops; at the time it rescued no
  method of ours (all failed it, a0f3f57).
- **Local stroke test L** — its declaration commit cdc291e already contains `stats/local_stroke_test.json` with segment-1 results. Same
  status: a diagnostic, never a bar.
- **R2** — by their file modification times on the run machine (not in git, so not checkable from this repository), the GP-R1 maps
  on all four unread windows and the first E map were written before the declaration commit c74372d (21:51:29 UTC): the maps were
  computed before R2 was declared, not after. No R2 agreement number was recorded before that commit, and the detector (E, declared
  5915848) and the windows (R1's, selected in c73cea4) were fixed earlier (INFERENCE from the record).
The UTC times typed into notebook headings are not reliable (several are later than their own commits); commit order is the evidence.

| test | declared | result | bars / prediction | outcome |
|---|---|---|---|---|
| GATE-T1, w028 calibration scan (v0.1, v0.1b, v0.2, v0.3p) | d160337 (bars); v0.1b 625a991, v0.3p 0825de7 | 625a991 … ee25abe | pixel AUC ≥ 0.70 | **fail** for all four methods (§8) |
| GATE-S1, Scroll 1 against read text (S1-v1a, v1b) | 038aef0 | 95cf9a6, e72979a | pixel ≥ 0.80 AND letter ≥ 0.90 on held-out mean | **fail** (§8) |
| S1-v2, S1-v3 | 95cf9a6, b78a1ca | 5e333a7, 4db0997 | same | **fail** |
| S1-v5 (U-Net, one crop) | 1c694f2 | b9ca77b | same | **fail**, as predicted in 0a834eb before the run ended |
| transfer to segment 20231210121321 | 8cff448 | 7e01be5 | same | **fail** for every method of ours |
| judge mask J | 55cd58e | fe9424c, 72ea621 | rule change, applied to all methods | every method of ours still fails |
| stroke test (replaces the letter test) | d27193f | a0f3f57 | pixel ≥ 0.80 AND **stroke ≥ 0.90** | bars used from here on |
| local stroke test L | cdc291e | 7d30ea7 | diagnostic, no bar | reported for every method |
| v6 (U-Net, 8 crops) | 3816e30 | a76fdba | — | **invalid**: the declared veto deleted every negative (incident 3) |
| v7 hand-built ridge | 7d30ea7 | 05d84a7 | pixel ≥ 0.80 AND stroke ≥ 0.90 | **fail** both |
| v6b U-Net, 8 crops, team-vetoed | 3c19230 | db529dd | same | **fail** (stroke 0.890 < 0.90) |
| v6c control, no veto | db529dd | cd3ea3d | control | **fail** both |
| v8 U-Net, 15 crops | f3b43d3 (amended 8a3998f before any crop was prepared) | bc24d20 | same | **pass** on the mean |
| GP-R1 Grand-Prize-style baseline | 3f88fdf (parameters 9d4ae3f) | c406bf7 | same | **pass** on the mean |
| E ensemble of v8 and GP-R1 | 5915848 (before either component's result) | 49be302 | same | **pass** on the mean and on the CI lower bound |
| R1 reading run, v8, unread papyrus | a31bbc1 | e8d6a6c | recover legible characters | **fail**; declared negative control invalid by construction |
| R2 reading run, E, same windows | c74372d | 9de8704 | same | **fail** |
| **C1 confirmation, 6 untouched crops** | 46a4bfc | 0e040c1 | E clears both bars on the C1 mean AND beats v7 on every C1 crop | **held** (E 0.830 / 0.928; ahead of v7 on 6/6 crops); v8 and GP-R1 alone fall below the pixel bar on C1 |

Declared or promised and never completed (reported so that the record is complete): GATE-T2a (9 µm, d160337; GATE-T2(b) was
inconclusive on a 3.4 % mask, so the 9 µm route is untested); GATE-F (d160337; its unit test was never evaluable and its row test was
falsified in 14cee78); v0.3f (dropped for disk, 038aef0); the w028 text3/text4 repair (promised 5413b77, dropped d07ddf5); E1 items 6–8
and E1's adversarial re-measure of every gain (declared 47febe8, not reported); the held-out step of the E1 calibration test (script
added 3c19230, no output); diagnostic D2-distil (0e86155; deferred at 3f88fdf); **GP-R2** (GP-R1 at 9.6 µm, 3f88fdf) — the declared
next experiment and the most informative one not run, so "resolution is the bottleneck" remains an untested hypothesis.

---

## 2. Evaluation set — 7 held-out crops

`results/stats_evaluation7.json` (written by `scripts/release_stats.py`: first in 5ba7764, last in 0aeb4b2, which switched stroke and L
to full precision); per-crop table `results/per_crop_evaluation7.csv`.
Means over crops with 95 % crop-level percentile bootstrap intervals (10 000 resamples, seed 0). The interval method was fixed in the C1
declaration (46a4bfc) and computed afterwards (5ba7764; stroke and L recomputed at full precision in 0aeb4b2); the point estimates were already known, so the intervals are **post-hoc
descriptions** of pre-registered results (MEASURED).

| method | status on this set | pixel AUC [95 % CI] | stroke AUC [95 % CI] | local L [95 % CI] | bars |
|---|---|---|---|---|---|
| **E** (v8 + GP-R1 rank-mean) | pre-registered, judged once | **0.876 [0.846, 0.907]** | **0.935 [0.902, 0.967]** | 0.934 [0.883, 0.977] | pass |
| v8 2-D U-Net, 15 crops | pre-registered, judged once | 0.839 [0.805, 0.871] | 0.916 [0.890, 0.943] | 0.907 [0.855, 0.957] | pass (mean) |
| GP-R1 3-D→2-D | pre-registered, judged once | 0.827 [0.795, 0.865] | 0.919 [0.874, 0.960] | 0.912 [0.835, 0.972] | pass (mean) |
| v6b U-Net, 8 crops, team-vetoed | pre-registered, judged once | 0.803 [0.764, 0.849] | 0.890 [0.859, 0.927] | 0.922 [0.884, 0.959] | fail |
| v6c U-Net, 8 crops, no veto | pre-registered control | 0.784 [0.745, 0.830] | 0.873 [0.835, 0.916] | 0.881 [0.809, 0.948] | fail |
| v7 hand-built ridge | pre-registered, judged once | 0.668 [0.622, 0.717] | 0.712 [0.643, 0.779] | 0.757 [0.658, 0.834] | fail |
| v2 band-passed depth template | re-judged under mask J and stroke test¹ | 0.639 [0.593, 0.691] | 0.686 [0.626, 0.748] | 0.697 [0.613, 0.773] | fail |
| v3 ridge, 66 features | re-judged¹ | 0.630 [0.599, 0.663] | 0.670 [0.628, 0.711] | 0.721 [0.637, 0.798] | fail |
| v1b depth template | re-judged¹ | 0.617 [0.585, 0.649] | 0.659 [0.616, 0.700] | 0.706 [0.629, 0.776] | fail |
| v0.1b papyrus subtraction | re-judged¹ | 0.556 [0.542, 0.570] | 0.590 [0.550, 0.626] | 0.590 [0.564, 0.615] | fail |
| team 2.4 µm model | **positive control** (§4) | 0.929 [0.896, 0.956] | 0.975 [0.957, 0.992] | 0.983 [0.969, 0.995] | — |

¹ v0.1b–v3 were pre-registered and failed under the original mask and letter test (§8). Mask J (55cd58e) and the stroke test (d27193f)
were declared after those verdicts and applied to every method and the comparator alike; the verdicts did not change.

**Bars on the lower CI bound** (not the declared criterion, which is the mean; reported because it is the stricter reading): of our
methods only E clears both (pixel 0.846 ≥ 0.80, stroke 0.902 ≥ 0.90); the team positive control also clears both (0.896, 0.957).
v8's stroke interval [0.890, 0.943] and GP-R1's [0.874, 0.960] span 0.90. On the untouched C1 crops (§5) v8 and GP-R1 fall below
the pixel bar; E passes there too.

Per-crop pixel / stroke / local L (MEASURED, `results/per_crop_evaluation7.csv`):

| crop | E | v8 | GP-R1 | v7 | team |
|---|---|---|---|---|---|
| 20231005123336:held1 | 0.882 / 0.939 / 0.929 | 0.817 / 0.886 / 0.888 | 0.843 / 0.924 / 0.910 | 0.695 / 0.747 / 0.843 | 0.978 / 1.000 / 1.000 |
| 20231005123336:held2 | 0.953 / 0.991 / 0.995 | 0.915 / 0.978 / 0.992 | 0.922 / 0.990 / 0.995 | 0.791 / 0.872 / 0.908 | 0.966 / 0.997 / 0.998 |
| 20231005123336:held3 | 0.810 / 0.895 / 0.889 | 0.757 / 0.861 / 0.822 | 0.788 / 0.898 / 0.923 | 0.663 / 0.716 / 0.769 | 0.851 / 0.935 / 0.945 |
| 20231210121321:held1 | 0.904 / 0.983 / 0.992 | 0.854 / 0.943 / 0.891 | 0.854 / 0.978 / 1.000 | 0.562 / 0.565 / 0.766 | 0.960 / 0.998 / 1.000 |
| 20231210121321:held2 | 0.851 / 0.967 / 0.997 | 0.817 / 0.939 / 0.971 | 0.802 / 0.961 / 0.978 | 0.622 / 0.765 / 0.792 | 0.924 / 0.981 / 0.979 |
| 20231210121321:held3 | 0.884 / 0.897 / 0.805 | 0.861 / 0.900 / 0.806 | 0.814 / 0.875 / 0.706 | 0.680 / 0.607 / 0.495 | 0.894 / 0.946 / 0.973 |
| 20231210121321:held4 | 0.847 / 0.871 / 0.932 | 0.851 / 0.907 / 0.981 | 0.766 / 0.810 / 0.873 | 0.663 / 0.712 / 0.722 | 0.926 / 0.969 / 0.988 |

Stroke and L sample sizes per crop: `stats/stroke_test.json` and `stats/local_stroke_test.json` (ink disks 37–202, blank disks 272–761 per
evaluation crop; paired ink disks for L 25–166). Those two files store per-crop values rounded to the nearest 4th decimal (Python
`round`, so some are rounded up). For E, v8, GP-R1, v7 and the team model the release statistics use the toolkit's full-precision
stroke and L instead (`results/toolkit_vs_records.json`, each equal to its record at 4 decimals; 0aeb4b2), so four per-crop values here
are 0.001 below the truncated record: E stroke on 20231005123336:held3 (record 0.8960, full precision 0.8959), v7 L on
20231005123336:held2 (0.9090, 0.9089), v7 stroke on 20231210121321:held2 (0.7660, 0.7659) and team stroke on 20231210121321:held2
(0.9820, 0.9819). For v6b, v6c, v3, v2, v1b and v0.1b only the 4-decimal records exist, so any of their stroke and L values (per crop,
mean or bound) can be 0.001 above the full-precision truncation. The D3 script recomputes v8, GP-R1 and E at full precision from
the score maps with the same `inkeval` functions (`results/d3_decomposition.json`; not an independent implementation); truncated, its
per-crop values and statistics for them equal those quoted here (MEASURED).

## 3. Paired differences — evaluation set

Same file. Mean difference over crops [95 % paired crop-level bootstrap], and the number of crops on which the first method is ahead.
Computed post-hoc for the release (5ba7764; stroke and L recomputed at full precision in 0aeb4b2); no comparison here was a declared
gate except as noted. MEASURED.

| comparison | pixel | stroke | local L | what it answers |
|---|---|---|---|---|
| E − v8 | +0.036 [0.020, 0.051], 6/7 | +0.018 [−0.003, 0.037], 5/7 | +0.027 [−0.006, 0.061], 5/7 | ensemble vs its better component |
| E − GP-R1 | +0.048 [0.034, 0.063], 7/7 | +0.015 [0.003, 0.032], 6/7 | +0.022 [−0.006, 0.053], 5/7 | |
| v8 − GP-R1 | +0.011 [−0.014, 0.042], 3/7 | −0.002 [−0.031, 0.034], 2/7 | −0.004 [−0.063, 0.056], 2/7 | architecture at 19.2 µm: a tie (see D3, §6) |
| v8 − v6c | +0.054 [0.027, 0.084], 7/7 | +0.042 [0.016, 0.070], 5/7 | +0.025 [−0.022, 0.084], 3/7 | 15 crops + AUC checkpointing vs 8 crops + BCE checkpointing (two changes) |
| v8 − v6b | +0.035 [0.003, 0.067], 5/7 | +0.026 [−0.003, 0.051], 5/7 | −0.014 [−0.041, 0.009], 3/7 | |
| v6b − v6c | +0.018 [0.008, 0.028], 7/7 | +0.016 [−0.001, 0.032], 6/7 | +0.040 [−0.014, 0.099], 5/7 | what team-model vetoing of negatives is worth (declared control) |
| E − v7 | +0.207 [0.171, 0.257], 7/7 | +0.222 [0.163, 0.296], 7/7 | +0.177 [0.123, 0.236], 7/7 | learned vs best hand-built |
| v8 − v7 | +0.171 [0.128, 0.218], 7/7 | +0.204 [0.144, 0.274], 7/7 | +0.150 [0.083, 0.224], 7/7 | |
| E − v2 | +0.236 [0.198, 0.283], 7/7 | +0.248 [0.185, 0.316], 7/7 | +0.237 [0.187, 0.287], 7/7 | |
| team − E | +0.052 [0.030, 0.074], 7/7 | +0.040 [0.019, 0.064], 7/7 | +0.048 [0.010, 0.094], 6/7 | remaining gap to the positive control |

INFERENCE: with 7 crops, the only differences we would act on are those whose 95 % interval excludes zero and that favour the same
method on 6/7 or 7/7 crops; v8 vs GP-R1 is a tie.

## 4. Controls

**Positive control — the team's 2.4 µm model** (the community model whose ds8 overview is public; `scripts/s1_team_comparator.py`).
Pixel 0.929 [0.896, 0.956], stroke 0.975 [0.957, 0.992] on the 7 evaluation crops (MEASURED). INFERENCE: it shows that the labels,
registration, mask and judge do not prevent a strong detector from scoring high; because of the caveat below it is not an independent
check of them. **Caveat (MEASURED, structural):** the reference labels were *placed* by correlating them with this model's overview
(global scale/offset fit, then a per-crop refinement of up to ±640 px = ±1.536 mm; `scripts/s1_register_label.py`,
`scripts/s1_refine_reg.py`), so its score is partly self-referential and is an upper reference, not an independent one.
The 7-crop mean is 0.929; the notebook once quoted the 3-crop segment-1 mean 0.932 in a 7-crop table (corrected, see SUPERSEDED_CLAIMS).

**Negative control — cross-crop label swap** (computed by `scripts/release_stats.py`; the same procedure is packaged as
`inkeval.label_swap_null`, which was not itself run on these crops; every ordered pair of evaluation crops, 42 pairs; each crop's
score map judged against another crop's labels and mask on the overlapping canvas). A detector of letters should sit near 0.5. MEASURED:

| detector | null mean | null range (42 pairs) | matched mean |
|---|---|---|---|
| E | 0.517 | 0.267 – 0.694 | 0.876 |
| v8 | 0.519 | 0.323 – 0.665 | 0.839 |
| v7 | 0.509 | 0.333 – 0.627 | 0.668 |
| team | 0.513 | 0.285 – 0.686 | 0.929 |

The means sit near 0.5 (0.509–0.519; no criterion was declared, see below). The ranges are the finding: a **single** crop can score
0.69 against labels that belong to a different place, so from the spatial layout of scores and labels alone (the swap keeps both
layouts and breaks only their correspondence). Which features of the layout produce it (for example ink-rich vs ink-poor halves,
damage, sheet edges) was not tested. INFERENCE: a single-crop AUC below ≈ 0.70 is not evidence of ink detection on these data, and a
per-crop AUC must be read against this null, not against 0.5. No numeric criterion was declared for this control in advance (46a4bfc
declares the control, not a threshold).

## 5. Confirmation test C1 — 6 untouched crops (pre-registered)

**Why.** Every method from S1-v5 to E was designed after earlier methods' numbers on some or all of the same 7 evaluation crops had
been read (S1-v1, S1-v2 and S1-v3 were declared before any evaluation-crop result was recorded: 038aef0, 95cf9a6, b78a1ca). Each judgement
was made once, but the *sequence* adapted to the set. C1 was designed to measure the size of that bias on labelled papyrus that no step had touched.
**Declared** 46a4bfc (2026-10-15 04:45 UTC) before any window was selected, fetched or scored: window rule, frozen methods (E, v8, GP-R1,
v7, team, label-swap null), metrics, prediction, statistics. Windows selected mechanically by `scripts/select_confirm.py`
(`stats/c1_confirm_<segment>.json`), scored by `scripts/run_c1.sh` with the released weights, no retraining, no tuning; log
`results/logs/c1.log`; statistics `results/stats_confirmation.json`.

MEASURED (`results/stats_confirmation.json`; crop-level bootstrap 10 000, seed 0):

| method | pixel AUC [95 % CI] | stroke AUC [95 % CI] | local L [95 % CI] | bars |
|---|---|---|---|---|
| **E** | **0.830 [0.800, 0.856]** | **0.928 [0.905, 0.947]** | 0.926 [0.912, 0.941] | pass (also at both lower bounds) |
| v8 | 0.774 [0.754, 0.796] | 0.881 [0.859, 0.908] | 0.889 [0.861, 0.914] | fail |
| GP-R1 | 0.786 [0.750, 0.818] | 0.908 [0.869, 0.942] | 0.920 [0.901, 0.938] | fail (pixel) |
| v7 | 0.618 [0.573, 0.650] | 0.664 [0.593, 0.731] | 0.716 [0.641, 0.779] | fail |
| team (positive control) | 0.899 [0.873, 0.922] | 0.978 [0.956, 0.992] | 0.982 [0.967, 0.996] | — |
| v1b (computed by crop preparation; not a declared C1 method, no verdict) | 0.593 [0.542, 0.639] | 0.616 [0.540, 0.676] | 0.659 [0.585, 0.713] | — |

Per-crop pixel / stroke / local L:

| crop | E | v8 | GP-R1 | v7 | team |
|---|---|---|---|---|---|
| 20231005123336:conf1 | 0.872 / 0.935 / 0.934 | 0.815 / 0.895 / 0.864 | 0.839 / 0.937 / 0.936 | 0.634 / 0.795 / 0.825 | 0.905 / 0.980 / 0.961 |
| 20231005123336:conf2 | 0.819 / 0.920 / 0.901 | 0.746 / 0.867 / 0.829 | 0.765 / 0.869 / 0.890 | 0.633 / 0.605 / 0.710 | 0.892 / 0.993 / 0.998 |
| 20231005123336:conf3 | 0.842 / 0.931 / 0.960 | 0.765 / 0.855 / 0.892 | 0.796 / 0.912 / 0.940 | 0.674 / 0.732 / 0.794 | 0.939 / 0.996 / 0.995 |
| 20231210121321:conf1 | 0.764 / 0.881 / 0.925 | 0.751 / 0.886 / 0.915 | 0.708 / 0.829 / 0.894 | 0.517 / 0.518 / 0.553 | 0.846 / 0.927 / 0.954 |
| 20231210121321:conf2 | 0.823 / 0.934 / 0.909 | 0.761 / 0.846 / 0.909 | 0.783 / 0.949 / 0.909 | 0.622 / 0.666 / 0.684 | 0.922 / 0.993 / 1.000 |
| 20231210121321:conf3 | 0.861 / 0.966 / 0.926 | 0.806 / 0.940 / 0.926 | 0.825 / 0.956 / 0.951 | 0.626 / 0.665 / 0.730 | 0.890 / 0.981 / 0.986 |

As in §2, stroke and L for E, v8, GP-R1, v7 and team are the toolkit's full-precision values; three values here are 0.001 below what
the 4-decimal records give: v7 stroke on 20231005123336:conf3 (record 0.7330, full precision 0.7329), team L on 20231210121321:conf3
(0.9870, 0.9869) and v7's L upper bound (0.780 from the records, as first written in the notebook; 0.779). v1b exists only at 4 decimals.

Stroke disks per crop: ink 36–107, blank 227–855 (every crop above the 20 disks per class below which the stroke test is undefined,
`scripts/stroke_test.py:25`); paired ink disks for L 22–103 (counts in `stats/stroke_test.json` and `stats/local_stroke_test.json`).
Paired on C1: E − v8 +0.055 [0.037, 0.069] pixel (6/6), +0.046 [0.020, 0.070] stroke (5/6); E − GP-R1 +0.043 [0.037, 0.051] pixel
(6/6); v8 − GP-R1 −0.012 [−0.025, 0.010] pixel (1/6), local L −0.030 [−0.056, −0.003] (1/6); team − E +0.068 [0.045, 0.090] pixel (6/6).
Negative control (label swap, 30 ordered pairs): E mean 0.546, range 0.361–0.654; v8 0.538, 0.421–0.633; v7 0.510, 0.371–0.635; team
0.558, 0.339–0.671. Every matched E crop (lowest 0.764) lies above E's largest null pair.

**Prediction** (stated in advance): *E clears both bars on the C1 mean (pixel ≥ 0.80, stroke ≥ 0.90) and beats v7 on every C1 crop.*
**Held** (`results/c1_analysis.json`): E's C1 means are 0.8305 (pixel, bar 0.80) and 0.9282 (stroke, bar 0.90), and the lower CI
bounds also clear (0.8002, 0.9055); E is above v7 on every C1 crop on pixel AUC (6/6) and on stroke AUC (6/6). Disclosure: the
declaration did not name the metric for "beats v7", and `scripts/c1_analysis.py`, which checks it, was committed (d2564a7, 06:08 UTC)
after 5 of the 6 C1 crops had been judged and written to the run log (the fifth logged done at 06:03 UTC, `results/logs/c1.log`; the
script's docstring says 4 of the 6 pixel values had been seen); it therefore reports both metrics, and both hold.

**Shrinkage** (the measurement C1 exists for): C1 mean minus evaluation mean, two-sample crop-level bootstrap (the two crop sets
resampled independently; this interval method was chosen in `scripts/c1_analysis.py`, after 5 of 6 C1 crops had been judged and
logged). Differences are given to 4 decimals so that a loss is not understated by truncation.

| method | pixel | stroke | local L |
|---|---|---|---|
| E | −0.0456 [−0.0885, −0.0055] | −0.0070 [−0.0451, 0.0305] | −0.0085 [−0.0548, 0.0445] |
| v8 | −0.0649 [−0.1029, −0.0248] | −0.0348 [−0.0710, 0.0014] | −0.0181 [−0.0755, 0.0410] |
| GP-R1 | −0.0410 [−0.0912, 0.0053] | −0.0106 [−0.0663, 0.0463] | +0.0077 [−0.0545, 0.0872] |
| v7 | −0.0503 [−0.1131, 0.0079] | −0.0483 [−0.1471, 0.0494] | −0.0407 [−0.1495, 0.0764] |
| team (positive control; post-hoc row, see `posthoc_note` in `results/c1_analysis.json`) | −0.0297 [−0.0674, 0.0087] | +0.0028 [−0.0246, 0.0274] | −0.0007 [−0.0204, 0.0186] |

Post-hoc and descriptive (added after 5 of 6 C1 crops had been judged and logged): team − E is 0.0527 on the evaluation crops and
0.0686 on C1, a widening of 0.0159 pixel AUC. INFERENCE: of E's 0.0456 pixel loss, 0.0297 is matched by the positive control,
consistent with harder windows (the C1 windows are the next-densest after excluding every processed window: label density 0.200–0.253
against 0.233–0.293 on the evaluation crops); the remaining 0.0159 (the widening above) is consistent with optimistic bias from reusing
the evaluation set, and 6 + 7 crops cannot separate it from noise. On the stroke metric E's loss is small (−0.0070) and its interval includes zero. The single U-Net v8 loses more
(−0.0649) and falls below both bars on C1: its evaluation-set pass does not replicate, while the pre-declared ensemble's does.

## 6. Post-hoc analyses (declared after the related result was known; they qualify claims, they cannot create them)

### D3 — ensembling vs smoothing in E (declared bf040d0, result bde701a; `results/d3_decomposition.json`, `scripts/d3_decompose.py`)

E rank-normalises, averages and then smooths (σ = 0.08 mm). Smoothing alone could produce part of E's gain, and v8 and GP-R1 were
upsampled differently (v8 bilinear, `scripts/s1_v5.py:70`; GP-R1 nearest-neighbour, `scripts/gpr.py:159`). Same 7 crops, same judge:

| variant | pixel | stroke | local L |
|---|---|---|---|
| v8 as published | 0.839 [0.805, 0.871] | 0.916 [0.890, 0.943] | 0.907 [0.855, 0.957] |
| v8 rank-normalised + smoothed 0.08 mm | 0.847 [0.814, 0.879] | 0.914 [0.887, 0.942] | 0.916 [0.868, 0.962] |
| GP-R1 as published | 0.827 [0.795, 0.865] | 0.919 [0.874, 0.960] | 0.912 [0.835, 0.972] |
| GP-R1 rank-normalised + smoothed | 0.857 [0.824, 0.894] | 0.917 [0.873, 0.958] | 0.917 [0.841, 0.974] |
| rank-mean of v8 and GP-R1, **no** smoothing | 0.864 [0.834, 0.896] | 0.934 [0.902, 0.966] | 0.936 [0.883, 0.980] |
| E as published | 0.876 [0.846, 0.907] | 0.935 [0.902, 0.967] | 0.934 [0.883, 0.977] |

Paired (pixel): smoothing alone v8_s − v8 = +0.008 [0.007, 0.010], 7/7; ensembling without smoothing mean_nos − v8 = +0.024 [0.007, 0.039],
6/7; ensembling given smoothing E − v8_s = +0.028 [0.012, 0.041], 6/7; smoothing given ensembling E − mean_nos = +0.012 [0.010, 0.013], 7/7.
Stroke: smoothing alone slightly *lowers* stroke AUC (v8_s − v8 = −0.002 [−0.005, −0.000], 2/7; GP-R1 −0.002 [−0.004, −0.000], 1/7 — a
small, consistent loss), so E's +0.018 [−0.003, 0.037] stroke gain over v8 (5/7; the interval includes zero) is matched by
ensembling without smoothing (mean_nos − v8 = +0.018 [−0.003, 0.036], 5/7). Like-for-like architecture comparison
(both smoothed): GP-R1 − v8 = +0.009 [−0.019, 0.033], 5/7 (pair `gpr1_s-v8_s`, added to `scripts/d3_decompose.py` for the release and
recomputed from the committed per-crop values; it equals the value first written in the notebook) — a tie with the sign reversed relative
to the published −0.011. MEASURED. INFERENCE: "ensembling helps" survives, with roughly a quarter to a third of the pixel gain being smoothing;
"the architecture buys nothing" holds only as "no measurable architecture effect at 19.2 µm on 7 crops".

### N1 — a null for the reading-run agreement statistic (declared 2e92310, result bde701a; `results/n1_reading_null.json`)

R1/R2 measured how well our detector separates the team model's confident ink (> 0.80) from its confident blank (< 0.20) on unread windows.
That statistic was introduced after R1 and had no null. N1: each window's score map against every *other* window's team classes
(12 ordered pairs of the 4 windows), judge 5 % subsample.

| detector | seg1 unread1 | seg1 control1 | seg2 unread1 | seg2 control1 | null mean | null range (12 pairs) |
|---|---|---|---|---|---|---|
| v8 | 0.801 | 0.716 | 0.737 | 0.864 | 0.519 | 0.304 – 0.641 |
| E | 0.886 | 0.804 | 0.793 | 0.879 | 0.509 | 0.246 – 0.652 |

All 4 matched windows exceed the largest null pair for both detectors (MEASURED). The notebook's R1/R2 values (0.802 / 0.717 / 0.739 /
0.865 for v8; 0.887 / 0.804 / 0.797 / 0.880 for E; e8d6a6c, 9de8704) were computed by inline code that was not committed; the committed
N1 script reproduces them within 0.004 on its 5 % subsample (INFERENCE: the difference is the subsample). n = 4 windows on 2 segments.

## 7. Reading runs R1 and R2 — unread papyrus (pre-registered; goal failed)

Declared a31bbc1 / c74372d with a mechanical window rule (on-sheet ≥ 0.90, no label within 5 mm, nearest to the read zone), an
anti-fabrication rule (describe only what is visible; no transcription; no plausible text) and a negative control (farthest window).

- **No legible character was recovered** by v8 (R1, e8d6a6c) or E (R2, 9de8704). Nothing is transcribed or proposed as a reading.
- The detectors are **not blind** there: agreement with the team model 0.716–0.864 (v8) and 0.793–0.886 (E) in the committed N1
  recomputation (0.717–0.865 and 0.797–0.887 as first recorded), every window above the N1 null (§6). This agreement statistic is
  **post-hoc for R1** — R1's declaration said the team model would not be used to "select, score, threshold or adjust anything" — and
  was declared for R2 (c74372d).
- The declared **negative control was invalid by construction**: distance from read text does not imply blank papyrus — the team model
  finds 2 618 k confident-ink pixels in the segment-1 control window, more than the 810 k in the reading window (e8d6a6c).
- The team model's own output on these windows is "blobby rather than cleanly legible" (e8d6a6c): INFERENCE, the windows adjacent to where
  papyrologists stopped reading are plausibly the hard ones.
- Renders: [`docs/figures/fig3_unread_e_vs_team.png`](figures/fig3_unread_e_vs_team.png), [`docs/figures/reading_runs/`](figures/reading_runs/).

INFERENCE: on unread papyrus detection improved with every AUC gain while legibility did not follow; the binding limit is stroke-scale
contrast against fibre texture (the E1 audit measured a contrast-to-noise ratio of 1.591 for v2 vs 6.262 for the team model, mean
over the 7 evaluation crops, `stats/explore/au_step4_<crop>.json`; the notebook printed 1.6 vs 6.3, 3c19230).

## 8. Earlier pre-registered gates (all failed) — the physics route

Values truncated from `stats/w028_gate_t1_<method>.json` (the notebook rounded several of them half-up).

**w028 calibration scan** (segment w028 of PHerc. 1667 at 2.399 µm, per the reference file name in RULES.md; bars d160337: pixel AUC
≥ 0.70). The reference here is **the team 2.4 µm model's prediction** (text ≥ 0.40, blank ≤ 0.25), not hand labels, so these gates test
agreement with that model, not ink. Pixel AUC top / bottom face.

| method | result commit | text crops | blanks | verdict |
|---|---|---|---|---|
| v0.1 papyrus subtraction | 625a991 | text1 0.540 / 0.553 (on the 5 % of the chart the mask left; as recorded, no JSON) | — | fail |
| v0.1b (mask fix) | bc38713 | text1–text5 0.473–0.592 | blank1 0.519 / 0.542, blank2 0.466 / 0.536 | fail |
| v0.2 (inpainting term) | ee25abe | writing-face mean 0.503 | blank1 0.514 / 0.527, blank2 0.452 / 0.510 | fail; route closed |
| v0.3p (peak intensity, no subtraction) | a492c1f | held-out mean 0.665 (text2–5; 0.6657 = mean of the text2–text5 writing-face values in `stats/w028_gate_t1_v0.3p.json`, whose stored all-five mean 0.6632 includes text1; the notebook printed 0.666) | blank1 0.522 / 0.522, blank2 0.541 / 0.541 | fail (two crops > 0.70, both computed on 61 % of their area) |

Data-integrity incident (5413b77): text3 and text4 numbers for v0.1b, v0.2 and v0.3p were computed on 61 % of the crop (deleted chunk
rows); flagged, repair dropped (d07ddf5). On the writing faces, the v0.1b verdict could change only if text3 and text4 averaged
≥ 0.999 on their full area, the v0.2 verdict only if they averaged above 1 (impossible), and the v0.3p verdict (text2–text5 mean) only
if they averaged ≥ 0.780, against 0.711 on 61 % of their area (INFERENCE: unlikely; not measured).

**Scroll 1 against read text** (bars 038aef0: pixel ≥ 0.80 AND letter ≥ 0.90, held-out mean). Pixel / letter, original mask, after the
declared reference refinement (87dd1bc) where applicable; values truncated from `stats/s1_gate_20231005123336.json` as committed in
b9ca77b (`git show b9ca77b:stats/s1_gate_20231005123336.json`; the file in the tree now holds the mask-J re-judgement, fe9424c):

| method | result commit | held-out mean | verdict |
|---|---|---|---|
| S1-v1a depth template (w028) | e72979a → 87dd1bc | 0.648 / 0.686 (notebook 0.649 / 0.686) | fail |
| S1-v1b depth template (TRAIN) | e72979a → 87dd1bc | 0.651 / 0.680 (notebook 0.651 / 0.681) | fail |
| S1-v2 band-passed template | 5e333a7 | 0.682 / 0.703 (notebook 0.683 / 0.703) | fail |
| S1-v3 ridge, 66 features | 4db0997 | 0.656 / 0.665 (notebook 0.657 / 0.666) | fail ("the linear family saturates at 0.65–0.68") |
| S1-v5 U-Net, one crop | b9ca77b | held1 0.545, held2 0.506, held3 0.540 (pixel) | fail (memorised its crop) |
| v0.1b papyrus subtraction | 87dd1bc | 0.515 / 0.423 | at chance |
| team (comparator) | 87dd1bc | 0.935 / 1.000 | — |

Physics measurements: sheet thickness AUC 0.478 against read text on the Scroll 1 TRAIN crop (as recorded in the notebook, 4f9ef66;
no JSON) and 0.498 against the team reference on w028 text1 (MEASURED, D1, `stats/d1_text1_depth_profile.json`, 20c16db), where mean
text-minus-blank brightness ranged from −0.027 to +7.818 uint8 units over the three anchors and 17 depths (at most 5.897 % of blank;
text darker at one depth, bottom anchor δ = +3), not the notebook's "≈ 2–3 uint8 units (≈ 2 %) brighter at every depth". On the four
crops of segment 20231005123336 (TRAIN, held1–held3) no single depth of the 19.2 µm pooled stack exceeds pixel AUC 0.58 (D2, 6d1c078;
as recorded, no JSON).

## 9. Exploratory (not pre-registered; no headline rests on these)

| id | commit | finding (MEASURED unless marked) |
|---|---|---|
| E1-FIBRE | cdc291e | widening the across-fibre window 13× changes held-out AUC by 0.004: no fibre-orientation signal |
| E1-SHAPE | cdc291e | the optimal 41 × 41 linear kernel is radially symmetric; smoothing each depth channel before combining helps (LOCO 0.71) |
| E1-TWOFACE | cdc291e | non-writing face 0.623 vs writing face 0.635 held-out (notebook 0.636); two-face gain +0.007 (notebook +0.008; `stats/explore/tf_step5_heldout.json`); INFERENCE: ink contrast is not surface-local |
| E1-EDGESHAPE | 8fa65b7 | literal edge-steepening hypothesis refuted; profile shape and edge descriptors add +0.026 (7/7) over the same 22 depth channels used linearly; gap to team not closed (0.663 vs 0.915, `stats/explore/es_step3_heldout.json`; the verdict printed 0.664 vs 0.916) |
| E1-CALIB | 96ab51d | per-crop mis-calibration hypothesis refuted by its own declared rule (−0.035 < +0.02); verdict never written up until this release |
| E1 audit: localisation | 3c19230 | contrast-to-noise 1.591 (v2) vs 6.262 (team), mean of the 7 evaluation crops (`stats/explore/au_step4_<crop>.json`; notebook 1.6 vs 6.3); INFERENCE: the deficit is amplitude, not localisation |
| E1 audit: reference noise | 3c19230 | label noise bounds a perfect-reference AUC for our scores at 0.675; registration residual 164 µm rms (held-out mean, `stats/explore/au_step5_bound.json`; notebook 165) |
| E1 audit: off-label | 3c19230 | where label and team disagree, our scores side with the team on average (held-out mean AUC 0.336–0.449 across v2, v3, v1b and v0.1b, inverted; `stats/explore/au_step2_<crop>.json`; notebook 0.34–0.45), not on every crop (above 0.5 on 20231005123336:held2 for v1b, v2 and v3, and on 3 of 7 crops for v0.1b) |
| v8 window count | 8a3998f | segment 20230929220926 supports no further window under the crop rule; 20231012184424 supports 7 more (labelled coverage 15.8 % → 39.3 %) |

## 10. What is and is not established (INFERENCE, stated once)

Established on this data, at this n: a small learned detector trained only on hand labels, ensembled, detects ink on held-out read text of
Scroll 1 at pixel AUC 0.876 and stroke AUC 0.935 on the evaluation set (0.830 and 0.928 on 6 untouched crops, where the pre-registered
prediction held), far above every hand-built physics score we built (the pre-registered ones stay below 0.683 held-out mean pixel AUC,
the highest being S1-v2 on segment 1, §8, and S1-v3 on segment 2, 7e01be5, both 0.682 under the original mask; v7 reaches 0.668 pixel /
0.712 stroke on the same 7 crops), and below the community model (0.929 pixel, 0.975 stroke). Not established: generalisation beyond
2 segments of 1 scroll; any effect of architecture at the Grand-Prize resolution (GP-R2 not run); any legible new text.
