# Lessons learned

This is every lesson we could extract from the research record of the Scroll 1 (PHerc. Paris. 4) ink-detection study that produced
`inkeval`: the lab notebook [`docs/RULES.md`](RULES.md), the git history, the committed result files, and the release audit. Overlapping
items were merged; nothing distinct was dropped. **The record supports 84 distinct lessons; we did not pad or trim to a target.**

Each entry gives what happened with the decisive numbers, the evidence as `path @ commit — quote or number`, one actionable lesson, and
the fix (with its commit, or "Fixed in this release" with the file) or **Open — not fixed**.

**Status date.** Every fix status was checked against the release working tree on 2026-10-15. "Fixed in this release" marks an item
closed after the first draft of this file (cc5c843).

**How to check an entry.** `docs/RULES.md` was `RULES.md` at the repository root in every commit cited here, so run
`git show <commit>:RULES.md`. Archived files are cited by their current path, with the path they had at that commit in parentheses.
`commit message of X` and `commit time of X` refer to `git show -s --format=%B X` and `--format=%cI X`.

**Labels.** Every evidence bullet is VERIFIED: its hash resolves with `git cat-file -t`, and the quoted text or number was found at that
commit with `git show <commit>:<path> | grep -F`. INFERENCE marks our interpretation. **We never round a number up.** Numbers from
`docs/RULES.md` are copied exactly as written (the notebook itself rounded half-up, see [68](#lesson-68)). Numbers from JSON or CSV files
are either given in full or truncated toward zero at three decimals, and we say "truncated" when we do it.

The confirmation test is referred to throughout as C1 (pre-registered 46a4bfc; result: see [`docs/RESULTS.md`](RESULTS.md) §5). This
file does not state its outcome.

## The ones that would change another team's conclusions

1. **Assert both classes exist before training:** a veto no pixel could pass deleted every negative on 7 training crops. [→ 31](#lesson-31)
2. **Do not put a bar on a component letter test over merged hand labels:** undefined on 4 of 7 crops under the original mask and 2 of 7 under the final mask; replaced by the stroke test. [→ 4](#lesson-4)
3. **Measure a label-swap null instead of assuming 0.5:** single swapped crop pairs reach 0.694 from layout alone. [→ 22](#lesson-22)
4. **Crops, not pixels, are n:** at 7 crops, v6b's pixel "pass" (0.803 truncated; RULES.md: 0.804) has an interval of [0.764, 0.849]. [→ 21](#lesson-21)
5. **Reusing an evaluation set adaptively needs an untouched confirmation set:** every method from v1 to E was judged on the same 7 crops, and each one from v5 on was designed after reading earlier methods' numbers on those crops (v1–v3 were declared before any evaluation-crop result; C1). [→ 13](#lesson-13)
6. **Change one thing at a time, or do not attribute the gain:** v8 changed the training data and the checkpoint criterion together. [→ 23](#lesson-23)
7. **Separate ensembling from smoothing (D3), and upsample compared methods the same way.** [→ 24](#lesson-24)
8. **Do not let the comparator place the reference it is scored on:** the team model aligned the labels its score was read against. [→ 2](#lesson-2)
9. **Register labels per crop, with a positive control on every crop:** a 998 µm shift surfaced only when the team model fell to 0.615 (truncated). [→ 1](#lesson-1)
10. **Detection is not legibility, and blank controls need evidence of absence:** agreement up to 0.886 (committed N1 code, truncated; RULES.md: 0.887) came with no legible character. [→ 17](#lesson-17), [→ 9](#lesson-9)
11. **Reproduce the known-good recipe before inventing methods:** the notebook counts seven methods invented before the baseline (3f88fdf), which then tied v8. [→ 60](#lesson-60)
12. **Never round up, and generate every table from one versioned per-crop file.** [→ 68](#lesson-68), [→ 34](#lesson-34)

---

## Evaluation design

<a id="lesson-1"></a>
### 1. Register labels on every crop, with a positive control on every crop

**What happened.** One global scale and offset placed the labels ("≤ 1 px" visually). The team model fell to 0.615 (truncated; RULES.md:
0.616) on segment-1 held3, exposing per-crop shifts up to 998 µm against strokes ≈ 0.4 mm wide. Per-crop translations raised held-out pixel
means from 0.592 to 0.651 (v1b) and 0.829 to 0.935 (team).

**Evidence.**
- `docs/RULES.md @ d2bd6a8` — "label outlines sit on the letters to ≤ 1 px"
- `docs/RULES.md @ e72979a` — "even the team model drops to 0.616 there"; "Held-out means: v1b 0.592 / 0.598; v1a 0.589 / 0.595; team 0.829 / 1.000."
- `stats/s1_gate_20231005123336.json @ e72979a` — held3 team bot "auc_px": 0.6157206422426539
- `docs/RULES.md @ 7375777` — "held2 (−384, 0) µm, held3 (998, −230) µm"; "Strokes are ≈ 0.4 mm wide"
- `stats/s1_local_registration_check.json @ 7375777` — held3 "corr_at_zero": 0.124, "best_corr": 0.554
- `docs/RULES.md @ 87dd1bc` — "Held-out means: v1b 0.651 / 0.681"; "team 0.935 / 1.000."

**Lesson.** Measure the residual label shift on every evaluation crop, and treat a positive control that fails on one crop as a data fault
until shown otherwise.

**Fix.** `scripts/s1_refine_reg.py` (7375777) stores one translation per crop, used for every method; all methods were re-judged once
(87dd1bc); C1 uses the same refinement (46a4bfc). See [2](#lesson-2), [6](#lesson-6).

<a id="lesson-2"></a>
### 2. Do not let the comparator place the reference it is scored on

**What happened.** Both the global and the per-crop registrations were fitted by correlation against the team model's output. The team
model's 0.935 was then read as confirming that "the reference is now well placed". That reasoning is circular.

**Evidence.**
- `docs/RULES.md @ 038aef0` — "ONE global scale+offset found by correlation against the team's ds8 ink overview"
- `docs/RULES.md @ 7375777` — "one translation per crop, found by correlation against the team"
- `docs/RULES.md @ 87dd1bc` — "The team model at 0.935 confirms the reference is now well placed."
- `docs/METHODS.md @ bde701a` — "it means the team model's own score is partly self-referential" (about reference placement)

**Lesson.** Align the reference with a signal that no scored model produced. Otherwise, report the comparator that placed it as an
alignment check and an upper reference, never as independent validation.

**Fix.** Disclosed as a limitation (`README.md`, since e455383 — "so the team model's score is partly self-referential"). No independent
re-alignment exists. **Open — not fixed.**

<a id="lesson-3"></a>
### 3. Report agreement with a model separately from agreement with ink

**What happened.** On w028 (PHerc. 1667) the text reference was the team model's own prediction, so every w028 AUC measured agreement with
that model, not ink. The notebook attached this caveat to D1 and then declared GATE-S1 against papyrologically read hand labels.

**Evidence.**
- `docs/RULES.md @ d160337` — "text = ref ≥ 0.40; blank = ref ≤ 0.25" (ref = the team prediction)
- `docs/RULES.md @ 20c16db` — "so what D1 measures is agreement with that model's" [contrast, not ink truth]
- `docs/RULES.md @ 038aef0` — "## GATE-S1 — Scroll 1 (PHerc.Paris.4) against physically verified text"

**Lesson.** Name the reference beside every AUC. Report an AUC against a model's output as agreement with that model, apart from AUCs
against verified text.

**Fix.** GATE-S1 (038aef0) judges against Grand-Prize hand labels. The team model is scored as a comparator and was also used to place
those labels (see [2](#lesson-2)). Every release headline number is against those labels.

<a id="lesson-4"></a>
### 4. Letter tests on merged hand labels cannot carry a bar

**What happened.** The bar used mean letter AUC ≥ 0.90 over label components, skipping those < 50 % valid. Before the per-crop
reference refinement it was undefined on segment-1 held3, one of the 3 held-out crops judged then (the v1 held-out letter mean is stored
with "n": 3 but averages two values). Under the original mask after the refinement it was undefined on 4 of 7 (all four segment-2
crops; segment-1 held1–held3 defined, 87dd1bc), and on 2 of 7 under mask J (merged word-sized components). The stroke-test
declaration's "5 of 7" (d27193f) matches none of these states (INFERENCE: it adds held3 from before the refinement to the four
segment-2 crops, which were first judged after it, 7e01be5). Where defined, it moved with the mask (segment-1 held1, v1b, refined
reference: letter 0.274, truncated, under the original mask; 0.72 under mask J) and could disagree with pixel AUC (segment-2 held2,
v0.1b: letter 0.99, pixel 0.557).

**Evidence.**
- `docs/RULES.md @ 038aef0` — "Bars (never edited): mean pixel AUC over the 3 held-out crops ≥ 0.80 AND mean letter AUC ≥ 0.90"
- `docs/RULES.md @ e72979a` — "held3 has no letter"; `stats/s1_gate_20231005123336.json @ e72979a` — "auc_letter": 0.59849157054126, "n": 3 (= mean of 0.2653061224489796 and 0.9316770186335404)
- `stats/s1_gate_20231005123336.json @ 87dd1bc` — held1 v1b bot "auc_letter": 0.27419354838709675; `docs/RULES.md @ 72ea621` — "| held1 | 0.555 / 0.60 | — | 0.649 / 0.72 |" [segment 1, mask J]
- `docs/RULES.md @ 7e01be5` — "Letter AUC was undefined on all four" [segment-2 crops]
- `docs/RULES.md @ 72ea621` — "Letter AUC stays undefined on held1/held3 (merged word-sized label components, none ≥ 50 % valid)"; "| held2 | 0.557 / 0.99 |"
- `docs/RULES.md @ d27193f` — "so the test is UNDEFINED on 5 of the" [7 evaluation crops]
- `inkeval/metrics.py @ 5ba7764` — "measured: undefined on 5 of 7 evaluation crops"

**Lesson.** Never rest a bar on a statistic that can be undefined or flip with the mask; report each mean's n; justify replacements with
current numbers.

**Fix.** Stroke test for all methods (d27193f; a0f3f57); README, METHODS and the `inkeval/metrics.py` docstring corrected in this
release (2 of 7 under mask J, 4 of 7 under the original mask).

<a id="lesson-5"></a>
### 5. Report the judged area beside every AUC, and build the judge mask for the evaluation

**What happened.** The judge inherited the relief method's 0.4 mm damage margin, which left 3–9 % of each segment-2 crop (segment 1: 35
%). The transfer means (v2 0.677, v3 0.682, team 0.958, truncated) were read as the same linear ceiling on a second segment; under mask J
(≈ 33 % judged) they became 0.608, 0.610 and 0.926 (truncated; RULES.md: v3 0.683 before, team 0.927 after).

**Evidence.**
- `docs/RULES.md @ 55cd58e` — "leaves 3–9 % of each crop (segment 1: 35 %)"
- `docs/RULES.md @ 7e01be5` — "v2 0.677 | v3 0.683 | v5 0.514 | team 0.958"
- `docs/RULES.md @ 72ea621` — "judged area ≈ 33 % of each crop"; "v2 0.608 | v3 0.610 | v5 0.507 | team 0.927"
- `stats/s1_gate_20231210121321.json @ 7e01be5` — held_out_means v2_bot 0.6770568311808798, v3_bot 0.6828794951864599, team_bot 0.9583649918683336; same file `@ 72ea621` — v2_bot 0.6083369023968537, v3_bot 0.6100846555328032, team_bot 0.9266325767544701

**Lesson.** Report judged area and class sizes beside every AUC; build the judge mask for the evaluation.

**Fix.** Mask J (0.1 mm margin), declared before re-running (55cd58e), applied to every method and comparator; old numbers kept.
`inkeval.judge` reports `text_px` and `blank_px` (5ba7764).

<a id="lesson-6"></a>
### 6. Make the code implement the declaration

**What happened.** Refinement is declared "within ±1.2 mm" but searches 640 px (±1.536 mm): C1 window conf2 sits at 504 px (504 × 2.4 µm =
1.2096 mm), and three training crops of 20231012184424 (held6–held8) sit exactly on the +640 px search limit (held5 at 632 px);
INFERENCE: their true offsets may lie beyond the search. The blank zone is declared as the label "closed with a 5 mm disc"; the judge
dilates it by 5 mm.

**Evidence.**
- `docs/RULES.md @ 7375777` — "within ±1.2 mm"; `scripts/s1_refine_reg.py @ 7375777` — "pad = 640"
- `stats/c1_confirm_20231005123336.json @ b370331` — conf2 local_offset [48, 504]
- `stats/s1_crops_20231012184424.json @ 0ce50ac` — held6 local_offset [-216, 640], held7 [176, 640], held8 [-32, 640]; held5 [-32, 632]; held10 "local_reg_corr": 0.257
- `docs/RULES.md @ 038aef0` — "label closed with a 5 mm disc"; `scripts/s1_judge.py @ acda042` — "zone = dist <= 5.0"

**Lesson.** Diff every script against its declaration before the first run, and flag fitted values on a search edge.

**Fix.** `docs/METHODS.md` discloses the ±1.536 mm search (e455383), the three training crops on the search limit (§2, 043ba8d) and, in
§7, the blank-zone difference (8c85019). The crop records were not re-registered with a wider search (`stats/s1_crops_20231012184424.json`
last changed in 0ce50ac). INFERENCE: with ≥ 0.99 zone coverage the zone difference can affect at most ~1 % of a crop.

<a id="lesson-7"></a>
### 7. Declare every parameter and filter that moves a headline number

**What happened.** Parameters that move every headline AUC were fixed only in code: the letter test's < 50 % valid-pixel skip, the judge's
5 % pixel subsample, the segment-1 slice range, per-patch label floors, the local test's caps (1 500 ink, 6 000 blank; the stroke
declaration says "up to 2000 disks per class"), v7's row-scaled λ and the reading-run thresholds.

**Evidence.**
- `scripts/s1_judge.py @ acda042` — "if mm.sum() < 0.5 * len(yy): continue"; "sub = rng.random(text.shape) < 0.05"
- `docs/RULES.md @ d27193f` — "up to 2000 disks per class"
- `docs/METHODS.md @ e455383` — "## 11. Parameters that affect headline numbers but were never declared"; "the local test's caps (1 500 ink, 6 000 blank disks)"

**Lesson.** Declare every filter, cap and subsample with the method, or list it as fixed in code at a cited commit before results are
read.

**Fix.** Inventoried in `docs/METHODS.md` §11 (e455383), with the commit that fixes each one in code (8c85019), except the letter test's
50 % valid-pixel skip: §9 describes it without a commit (the test is retired). `docs/RULES.md` left as written.

<a id="lesson-8"></a>
### 8. Dry-run every declared rule on the data before declaring it

**What happened.** Three declared rules were unsatisfiable: unit bars needing ≥ 50 % valid pixels under masks of ≈ 36 % (no unit was ever
classed); the training veto "team ds8 prediction < 0.10", which no pixel passed because the JPEG overview never falls below 0.10; and v8's
4-to-8 windows per segment, infeasible on 20230929220926.

**Evidence.**
- `docs/RULES.md @ a492c1f` — "≥ 50 % valid pixels at 0.5–2 cm² (mask ≈ 36 %)"; `stats/w028_gate_t1_v0.1b.json @ bc38713` — "n_text": 0
- `docs/RULES.md @ 4043cae` — "team ds8 prediction < 0.10 at that pixel"; `docs/RULES.md @ a76fdba` — "crop below 0.10 = 0.000"
- `docs/RULES.md @ 8a3998f` — "20230929220926 supports NO additional window beyond its 4"

**Lesson.** Before declaring a rule, run it on the data (seconds) and check that it admits a non-empty, plausible set.

**Fix.** Units recorded, not relaxed (GATE-F never evaluated). The veto became a per-crop 40th percentile (a76fdba), then was dropped
(f3b43d3). v8's rule was amended to 15 crops before any data was built (8a3998f).

<a id="lesson-9"></a>
### 9. Choose a negative control by evidence of absence, and report its impurity

**What happened.** w028 has no blank 4 cm² window; its "blank" crops held 7 % and 13 % reference text. R1 took its control as the window
farthest from labels, and the team model found 2 618 k confident-ink pixels there against 810 k in the reading window: unread writing is
almost everywhere.

**Evidence.**
- `docs/RULES.md @ d160337` — "still contain 7 % and 13 % text pixels"
- `docs/RULES.md @ a31bbc1` — "the farthest such window from the labelled zone"
- `docs/RULES.md @ e8d6a6c` — "| 20231005123336 control1 | 43.6 mm | 2 618 k | 0.717 |"; "| 20231005123336 unread1 | 12.5 mm | 810 k | 0.802 |"; "A valid blank control has to be chosen by evidence of absence"

**Lesson.** Choose a blank control by evidence of absence (both detectors blank, a margin, an interval), never by distance, and report its
impurity.

**Fix.** R2 reports the R1 controls as unread windows (c74372d). Labelled crops use a cross-crop label-swap null (46a4bfc, 5ba7764).
Unread papyrus has no valid blank control: **Open — not fixed**.

<a id="lesson-10"></a>
### 10. Test an ink indicator on a blank control; re-declare what depended on it

**What happened.** The ~3 mm row-periodicity test was stronger on a blank chart (0.4175, truncated 0.417; RULES.md: 0.418) than on text
(0.258) and was dropped as an ink indicator. Twenty-one minutes later the v0.1b verdict still used it to pick each crop's writing face,
picking the worse face on 4 of 5 text crops (computed here): headline 0.5098 (truncated 0.509; RULES.md: 0.510), against a best-face mean
of 0.5696 (truncated 0.569; RULES.md: 0.570).

**Evidence.**
- `docs/RULES.md @ 14cee78` — "Row test on the BLANK chart: bottom peak 0.418 at 3.14 mm (CT control 0.21)"; "falsified as an ink indicator on w028 and is dropped from the GATE-T1 criteria"
- `docs/RULES.md @ 2026bab` — "Row test: top peak 0.258 at 2.99 mm"; `docs/RULES.md @ d160337` — "Face = the one with the higher row-test peak."
- `stats/w028_gate_t1_v0.1b.json @ bc38713` — 0.5098104892186252 (writing-face mean); text3 bottom (chosen) 0.47314019149475 vs top 0.5648746261312187; blank1 row_bot "peak": 0.4175077725642626
- `docs/RULES.md @ bc38713` — "0.510 (best-face mean 0.570)"; commit times: 14cee78 14:17:05Z, bc38713 14:38:59Z

**Lesson.** Test every ink indicator on a blank control first; when one falls, re-declare what depends on it.

**Fix.** GATE-S1 picks the writing face by TRAIN pixel AUC (038aef0). The w028 verdict was not re-issued; both numbers stay on record.

<a id="lesson-11"></a>
### 11. Separate letter-level information from regional brightness

**What happened.** A brightness gradient that follows text density can raise AUC with no letter information in it. Removing scales above
3 mm cut text3 from 0.714 to 0.637. Test L compares each ink disk only with blank disks within 1.5 mm. It refuted the purely regional
explanation for v1b, v2 and v3. Even so, it moved v2 by only +0.010 (L 0.697 against stroke 0.686, truncated; RULES.md: 0.687).

**Evidence.**
- `docs/RULES.md @ ba2310f` — "text3 0.637 vs 0.714"
- `docs/RULES.md @ 7d30ea7` — "The regional-confound hypothesis is REFUTED for v1b/v2/v3"; "Means: v0.1b 0.590/0.590 | v1b 0.706/0.660 | v2 0.697/0.687 | v3 0.722/0.671 | team 0.984/0.976."
- `results/stats_evaluation7.json @ 5ba7764` — v2 stroke "mean": 0.6869714285714286, local "mean": 0.6973142857142857

**Lesson.** Report a local test such as L beside every global AUC, per method. A detector with a high pixel AUC and L ≈ 0.5 is reading
regional brightness.

**Fix.** L is a standing metric for every method and is part of the toolkit (`inkeval.local_stroke_auc`, 5ba7764).

<a id="lesson-12"></a>
### 12. Confirm a motivating effect on training data before building on it

**What happened.** v7's regional-removal step was motivated by L measured on the evaluation crops, and the declaration promised to
confirm the effect on training data first. That was impossible: 7 of the 8 training crops had no score maps. On the one crop that had
them, v3's L (0.826, truncated; RULES.md: 0.827) was below its stroke AUC (0.879), the opposite sign. Removal then improved training
LOCO by only +0.018.

**Evidence.**
- `docs/RULES.md @ 7d30ea7` — "and L is re-measured there first"
- `docs/RULES.md @ 81d26cc` — "7 of the 8 training crops have no score maps"; "L = 0.827 is LOWER than its stroke"
- `stats/local_stroke_test.json @ 81d26cc` — 20231005123336:train v3 "L": 0.8268; `stats/stroke_test.json @ 81d26cc` — v3 "stroke_auc": 0.8791
- `docs/RULES.md @ 05d84a7` — "(LOCO 0.7416 at σ_R = 4.0 vs 0.7232 with no removal, +0.018)"

**Lesson.** Confirm any effect that motivates a design on training data before fitting. If you cannot, record that you could not.

**Fix.** The failed confirmation was recorded before the fit finished (81d26cc). Removal stayed in v7 only as one LOCO-selected candidate.

<a id="lesson-13"></a>
### 13. Adaptive reuse of an evaluation set needs an untouched confirmation set

**What happened.** Every method from v1 to E was judged on the same 7 evaluation crops (re-judged only when the reference or mask
changed, for all methods alike). v1 was declared before any Scroll 1 stack was read, and v2 and v3 before any evaluation-crop result (95cf9a6, b78a1ca;
first held-out result 303bc85), but each method from v5 on was designed after reading the earlier methods' numbers on those crops, and v7 was motivated directly by L measured on them. Limiting how often each method is judged
does not remove the optimistic bias of the sequence as a whole.

**Evidence.**
- `docs/RULES.md @ 038aef0` — "BEFORE any Scroll 1 stack is read" [v1 declared]
- `docs/RULES.md @ 47febe8` — "reporting the evaluation crops (20231005123336/held1–3, 20231210121321/held1–4)" [once]
- `docs/RULES.md @ 7d30ea7` — "the regional component was noticed via L measured on the EVALUATION crops"
- `docs/RULES.md @ 46a4bfc` — "every method from v1 to E was judged on the same 7 evaluation crops"; "the SEQUENCE adapts to the evaluation set, so the headline"

**Lesson.** Keep an untouched, pre-registered labelled set. Spend it once, with frozen weights and both positive and negative controls,
to measure the bias of the whole sequence.

**Fix.** C1 (pre-registered 46a4bfc; result: see [`docs/RESULTS.md`](RESULTS.md) §5). Its windows were selected mechanically and
committed in `stats/c1_confirm_*.json` (b370331).

<a id="lesson-14"></a>
### 14. Commit the confirmation analysis code before any confirmation number is seen

**What happened.** C1's declared prediction ("beats v7 on every C1 crop") names no metric. The script that checks it (on pixel AUC) was
first committed 1 h 22 min later; its docstring says its post-hoc part was "written after 4 of the 6 C1 pixel values had been seen in the
run log".

**Evidence.**
- `docs/RULES.md @ 46a4bfc` — "and beats v7 on every C1 crop"; commit time 2026-10-15T04:45:30Z
- `scripts/c1_analysis.py @ d2564a7` (the file's first commit, 06:08:20Z) — "\"Beats v7\" is checked on pixel AUC (the primary metric)"; "written after 4 of the 6 C1 pixel values had been seen in the run log"
- `docs/RESULTS.md @ 8362c4b` — "declaration did not name the metric for \"beats v7\""

**Lesson.** Commit the analysis script, with every metric and verdict rule, in the same commit as the declaration.

**Fix.** Disclosed in `docs/RESULTS.md` §5 (8362c4b): the declaration named no metric, so `scripts/c1_analysis.py` reports both (pixel
and stroke). Its timing was corrected in this release (`docs/RESULTS.md` §5; appended note in `docs/RULES.md`, 5ce2d4d): the script was
committed (06:08:20Z) after 5 of the 6 C1 crops had been judged and logged (the fifth at 06:03:52Z, `results/logs/c1.log`); its
docstring says 4 of the 6 pixel values had been seen. The analysis code was still not committed with the declaration, and that cannot
be repaired after the fact.

<a id="lesson-15"></a>
### 15. Validation windows cannot discover text

**What happened.** The crop rule required label-zone coverage of at least 0.99. Until R1, every crop therefore lay in text that
papyrologists had already read: "A perfect detector under this rule yields zero new characters."

**Evidence.**
- `docs/RULES.md @ 038aef0` — "1.5 cm squares (6250 px) on a 1250 px grid inside the labelled zone"
- `docs/RULES.md @ 0e86155` — "A perfect detector under this rule yields zero new characters. GUILTY, by construction."

**Lesson.** Keep validation windows (read text, for scoring) and discovery windows (unread text, for reading) as separate, separately
declared sets.

**Fix.** Reading runs R1 and R2 on unread windows (declared a31bbc1 and c74372d).

<a id="lesson-16"></a>
### 16. Windows next to read text are the hardest papyrus

**What happened.** R1 took the admissible window nearest the read text, on the assumption that the column continues there. Regions that
papyrologists left unread are plausibly the hardest ones, and the team model's own output there was blobby rather than legible.

**Evidence.**
- `docs/RULES.md @ a31bbc1` — "adjacent to read text is where the same column most likely"
- `docs/RULES.md @ e8d6a6c` — "the team model's own output on these windows is blobby rather than cleanly legible"; "R1's window rule walked straight into"

**Lesson.** Choose reading windows by a measured quantity declared in advance, such as local contrast or detector confidence, not by
proximity to read text.

**Fix.** None: R2 reused the same windows so that no window could be chosen after seeing output. **Open — not fixed.**

<a id="lesson-17"></a>
### 17. Detection is not legibility

**What happened.** On the four unread windows, v8 agreed with the team model's confident ink at 0.717–0.865 and E at 0.797–0.887 as
recorded in RULES.md (computed by uncommitted code, [38](#lesson-38)); the committed N1 code (bde701a) gives 0.716–0.864 (v8) and
0.793–0.886 (E), truncated. Every matched window was above its swapped-window null (N1). No render shows a legible character. The E1
audit had measured our contrast-to-noise across a stroke at 1.6 (v2), against 6.3 for the team model.

**Evidence.**
- `docs/RULES.md @ e8d6a6c` — R1 table "| 20231005123336 control1 | 43.6 mm | 2 618 k | 0.717 |"; "| 20231210121321 control1 | 17.6 mm | 483 k | 0.865 |"; "Statistical detection and legibility are different things"
- `docs/RULES.md @ 9de8704` — "**0.887**"; "**0.797**"; "**And still no legible character appears in any render.**"
- `results/n1_reading_null.json @ bde701a` — "matched_above_null_max": 4 (v8 and E); v8 matched 0.7164590120477256 to 0.8641189924919674; E matched 0.7936729604281341 to 0.8863642386585272
- `docs/RULES.md @ 3c19230` — "contrast-to-noise across the stroke is 1.6 (v2) vs 6.3 (team)"

**Lesson.** Treat AUC as a measure of detection only. A claim to have read text needs its own declared legibility measure and human
review.

**Fix.** The release reports the null as measured (`README.md`, since e455383 — "No character has been recovered from unread papyrus.";
`docs/RESULTS.md` §7, since e455383 — "No legible character was recovered"). No legibility measure exists. **Open — not fixed.**

<a id="lesson-18"></a>
### 18. Measure and disclose every teacher-model path into training

**What happened.** v6b's negatives were filtered by the team model (quantile veto), a distillation path. The no-veto control v6c measured
it: v6b − v6c = +0.018 pixel (truncated), 7 of 7 crops. v8, GP-R1 and E use no team-model veto (their labels were still placed by
correlation with the team model, see [2](#lesson-2)), but v7, C1's frozen hand-built baseline, was fitted on the vetoed labels with no
no-veto control.

**Evidence.**
- `docs/RULES.md @ cd3ea3d` — "| **v6c (no team model at all)** | **0.785** | **0.874** | **0.882** |"
- `results/stats_evaluation7.json @ 5ba7764` — v6b-v6c pixel 0.018867086460212894, positive_crops 7
- `scripts/run_fix_veto.sh @ 96ab51d` — "then ds8_y, then refit v7"; `scripts/s1_v7.py @ 45fe9e0` — 'Y = np.load(os.path.join(d, "ds8_y.npy"))'
- `docs/RULES.md @ 46a4bfc` — "hand-built baseline, frozen weights stats/s1_v7_weights.json"
- `docs/RULES.md @ f3b43d3` — "Negatives carry NO team-model veto"; `docs/RULES.md @ 7375777` — "one translation per crop, found by correlation against the team"

**Lesson.** List every path by which a teacher model touches training data, measure each with a control that removes it, and label
baselines that keep it.

**Fix.** Control v6c (cd3ea3d); v8 and GP-R1 use no-veto labels (f3b43d3); v7's dependence is disclosed (`README.md` Limitations, since
e455383). No no-veto v7: **Open — not fixed**.

<a id="lesson-19"></a>
### 19. Keep exploration-grid and judge-grid AUCs apart

**What happened.** The E1 investigations scored on the 19.2 µm ds8 grid with a pooled mask, which is explicitly not the judge. On that
grid the team model scores 0.9158, against 0.929 on the judge. E1 numbers are comparable only with other E1 numbers computed on identical
pixels.

**Evidence.**
- `stats/explore/tf_DECLARATION.md @ cdc291e` — "NOT the full-resolution judge."
- `stats/explore/final_heldout.json @ cdc291e` — team "ds8_auc_px": 0.9158, "full_auc_px": 0.929

**Lesson.** Tag every AUC with the grid and mask it was computed on, and never compare AUCs across grids.

**Fix.** The E1 tables re-measured their comparators on identical pixels. The release lists E1 as exploration.

<a id="lesson-20"></a>
### 20. Make a comparative bar strictly beat its comparator

**What happened.** The GATE-T1 bar read "mean AUC ≥ 0.82 → 'beats the public 9 µm model's 0.823'". A score of 0.820–0.822 would have met
that bar without beating 0.823.

**Evidence.**
- `docs/RULES.md @ d160337` — "mean AUC ≥ 0.82 → \"beats the public 9 µm model's 0.823\""

**Lesson.** State a comparative bar as strictly above the comparator, with the uncertainty of both.

**Fix.** The bar was never triggered: the best w028 held-out mean was 0.665 (truncated; RULES.md: 0.666; see [27](#lesson-27)).

## Statistics

<a id="lesson-21"></a>
### 21. Count crops, not pixels

**What happened.** Means rest on 3–7 correlated crops from 1–2 segments; pixels add no independent samples (the judge subsamples 5 % of
them anyway). At n = 7 (crop-bootstrap 95 % intervals, truncated): v6b "PASSES the pixel bar (0.804 ≥ 0.80)" with [0.764, 0.849]; v8's
stroke interval starts at 0.890; v8 − GP-R1 pixel is [−0.014, 0.042]. Of our methods, only E clears both bars at the lower bound (0.846,
0.902); the team comparator does too (0.896, 0.957).

**Evidence.**
- `docs/RULES.md @ db529dd` — "**v6b PASSES the pixel bar (0.804 ≥ 0.80)"
- `results/stats_evaluation7.json @ 5ba7764` — v6b pixel ci95 [0.7648430705786049, 0.8499634376035186]; v8 stroke lower 0.8904428571428572; v8-gpr1 pixel [-0.014611542734137466, 0.04230588226788047]; E lower 0.846068183828077 / 0.9027360714285714; team lower 0.8968283871135085 / 0.9574546428571429
- `docs/RULES.md @ 46a4bfc` — "no pixel-level CI is presented as if pixels were" [independent]

**Lesson.** Treat crops and segments as the unit of replication; bootstrap over crops and read passes and ties from the interval.

**Fix.** Crop-level percentile bootstrap, 10 000 resamples (planned 46a4bfc, computed 5ba7764; `inkeval.bootstrap_ci`).

<a id="lesson-22"></a>
### 22. Measure a null, and read it as a distribution

**What happened.** Under the cross-crop label-swap null (42 ordered pairs) the mean sits near 0.5 (E 0.517), but single pairs reach 0.694
(E) and 0.686 (team) from layout alone (truncated). The R1/R2 per-window agreement AUCs had no null until N1, whose largest null pair was
0.641 (v8) and 0.652 (E).

**Evidence.**
- `results/stats_evaluation7.json @ 5ba7764` — "pairs": 42; E "mean": 0.5176753487034217, "max": 0.6942885990522629; team "max": 0.6869752412939095
- `docs/RULES.md @ 2e92310` — "That agreement statistic was introduced after R1's result and was never given a null."
- `results/n1_reading_null.json @ bde701a` — "null_max": 0.6415017872755293 (v8), "null_max": 0.6527057347860917 (E)

**Lesson.** Measure a null distribution on the actual layout and read single-crop or single-window values against its tail, not against
0.5.

**Fix.** Label-swap null in the release statistics (5ba7764) and the toolkit (`inkeval.label_swap_null`); N1 for the reading runs
(declared post-hoc 2e92310, run bde701a).

<a id="lesson-23"></a>
### 23. Change one thing at a time, or attribute the gain jointly

**What happened.** v8 changed the training set (8 → 15 crops) and the checkpoint criterion (BCE → AUC) together, and the gain was credited
to data ("confirms data was a binding constraint"). v8's validation BCE is lowest at step 250 (0.600) and rises to 0.981 at 12 000
(truncated), so its step-9500 checkpoint reflects AUC selection. v8 − v6c = +0.054 [0.027, 0.084] pixel (truncated, 7/7) is a joint
effect.

**Evidence.**
- `docs/RULES.md @ f3b43d3` — "v8 fixes exactly those two things and nothing else"; `docs/RULES.md @ bc24d20` — "confirms data was a binding constraint"
- `models/v8_unet.pt.json @ 412b7c7` — val_bce 0.6002644300460815 (step 250), 0.9818353652954102 (step 12000)
- `results/stats_evaluation7.json @ 5ba7764` — v8-v6c pixel 0.05478432189855577

**Lesson.** Change one factor per experiment, or attribute the gain jointly and name the missing control.

**Fix.** The release attributes it jointly (`README.md`, since e455383). No single-factor control: **Open — not fixed**.

<a id="lesson-24"></a>
### 24. Decompose a combined gain; post-process compared methods identically

**What happened.** E (rank-mean of v8 and GP-R1, then 0.08 mm smoothing) was credited to "decorrelated errors" with no smoothing-only
control, and GP-R1 was upsampled nearest-neighbour, v8 bilinear. Post-hoc D3 (truncated): smoothing alone +0.008 pixel; ensembling +0.024
unsmoothed, +0.028 smoothed; smoothing gives GP-R1 +0.029; like for like GP-R1 − v8 = +0.009 (5/7), sign reversed; smoothing slightly
lowers stroke AUC.

**Evidence.**
- `scripts/gpr.py @ 9d4ae3f` — "up = np.repeat(np.repeat(z, F, axis=0), F, axis=1)"; `scripts/s1_v5.py @ 1c694f2` — 'scale_factor=8, mode="bilinear"'
- `docs/RULES.md @ 49be302` — "which is the ordinary ensembling" [gain from decorrelated errors]
- `results/d3_decomposition.json @ bde701a` — v8_s−v8 0.008385350693501834; mean_nos−v8 0.02476475028645775; e−v8_s 0.028386261857322324; gpr1_s−gpr1 0.02967406643906236; v8_s−v8 stroke −0.0026996330398864543, CI upper −0.00011364361437407997
- `docs/RULES.md @ bf040d0` — "(v8/GP-R1 nearest-neighbour, v7 bilinear)" (wrong for v8)
- `docs/RULES.md @ bde701a` — "GP-R1 − v8 = +0.009 [−0.019, 0.033] (5/7)"; first computed by committed code in `results/d3_decomposition.json @ 043ba8d` — -0.01940031461976945, 0.03304815913418372

**Lesson.** Post-process compared methods identically, and decompose a combined gain before crediting any part.

**Fix.** D3 (bf040d0, bde701a); the declaration's upsampling error is corrected in the `d3_decompose.py` docstring (e455383), and the
like-for-like pair is computed by committed code (043ba8d). GP-R1 is not re-judged with bilinear upsampling: **Open — not fixed**.

<a id="lesson-25"></a>
### 25. Know what the stroke-disk test samples

**What happened.** The record says "175–760 disks per class per crop" on a grid "to avoid overlap". The committed ink counts are 37–202,
the grid spacing equals the disk radius (disks overlap), and ink centres must lie ≥ 0.25 mm inside a stroke, so only thick strokes are
sampled: on the segment-1 TRAIN crop 39.13 % of text pixels lie deeper than 0.2 mm, 15.08 % deeper than 0.3 mm.

**Evidence.**
- `docs/RULES.md @ a0f3f57` — "(175–760 disks per class per crop)"; `docs/RULES.md @ d27193f` — "with seed 0 on a 0.25 mm grid to avoid overlap"
- `stats/stroke_test.json @ a0f3f57` — "n_ink": 202 … "n_ink": 37
- `scripts/stroke_test.py @ d27193f` — "g[r:-r:r, r:-r:r] = True" (r = disk radius)
- `stats/explore/au_step1_geom.json @ cdc291e` — 20231005123336/train "0.2": 0.3913, "0.3": 0.1508

**Lesson.** Report realised counts and the support a disk test samples; n is still crops.

**Fix.** Inference uses the crop bootstrap (5ba7764). `docs/METHODS.md` states that the disks overlap (8c85019); `inkeval` keeps the grid
to reproduce the published numbers.

<a id="lesson-26"></a>
### 26. Check whether the crops that clear a bar are the defective ones

**What happened.** Under v0.3p, the only two w028 crops above the 0.70 bar (text3 0.714, text4 0.709, truncated; RULES.md: 0.710) are
exactly the two that were computed on 61 % of their area. Part of text3's value is a density gradient ([11](#lesson-11)). INFERENCE
(counterfactual): without them, the held-out mean is (0.6023755578659375 + 0.6368849225614062)/2 = 0.619 (truncated).

**Evidence.**
- `docs/RULES.md @ a492c1f` — "text3 0.714 | text4 0.710"; "(two crops individually above it)"
- `docs/RULES.md @ 5413b77` — "was computed on the remaining 61 % of those crops"
- `stats/w028_gate_t1_v0.3p.json @ a492c1f` — 0.6023755578659375 (text2), 0.7140024906217499 (text3), 0.7096619107560864 (text4), 0.6368849225614062 (text5)

**Lesson.** Before reading anything into the crops that clear a bar, check whether they are the ones with known defects.

**Fix.** None needed for the verdict, since v0.3p fails either way. The 61 % caveat stays attached to the per-crop numbers.

<a id="lesson-27"></a>
### 27. Fix an exploration set and write down the held-out prediction

**What happened.** After D1, text1 became the exploration chart. Everything designed with it in view was judged only on text2–text5,
against a prediction written in advance ("≈ 0.65, i.e. a FAIL"). The held-out mean was 0.666 in RULES.md, or 0.6657 from the JSON
(truncated 0.665; computed here). The prediction held.

**Evidence.**
- `docs/RULES.md @ 9a62d8c` — "From this point, text1 is the EXPLORATION chart"
- `docs/RULES.md @ 0825de7` — "Expected from the exploration chart: ≈ 0.65, i.e. a FAIL"
- `docs/RULES.md @ a492c1f` — "Held-out mean (text2–text5) 0.666"; per-crop values in `stats/w028_gate_t1_v0.3p.json @ a492c1f` (0.6023755578659375, 0.7140024906217499, 0.7096619107560864, 0.6368849225614062)

**Lesson.** Fix an exploration set, write down the predicted held-out score before judging, and compare the two afterwards.

**Fix.** The practice was kept: GATE-S1 separates a TRAIN crop from the held-out crops (038aef0).

<a id="lesson-28"></a>
### 28. Report every variant computed, not only the best

**What happened.** The declaration said "rank-sum of (1) and (3)" while expecting roughness to enter with a negative sign, so the sign
was ambiguous. The JSON holds both: the literal rank-sum 0.5909 and the difference 0.6226. RULES.md reports only the difference (0.623),
the higher one.

**Evidence.**
- `docs/RULES.md @ 84f2947` — "sign recorded (paper: inked areas smoother in SEM → expected negative); (4) rank-sum of (1) and (3)"
- `stats/d1c_text1_measures.json @ 0825de7` — "rank(top+bot) - rank(rough)": 0.6226; "rank(top+bot) + rank(rough)": 0.5909
- `docs/RULES.md @ 0825de7` — "(top+bot)−rough 0.623"

**Lesson.** Fix every sign and variant in the declaration, and report every variant computed.

**Fix.** Disclosed here. This was an exploration-chart diagnostic with no bar, and no number depends on it.

<a id="lesson-29"></a>
### 29. Bound reference noise before blaming the labels

**What happened.** The E1 audit put "≈ 0.07 of the 0.29 gap" down to reference noise (label-noise bound 0.675, registration residual 164 µm
rms, truncated; RULES.md: 165). The committed bound file picks the best of v0.1b/v2/v3 per crop (observed 0.6497), mildly optimistic, and
its erosion result (0.741) does not match RULES.md's "0.640 → 0.730", so the split cannot be re-derived.

**Evidence.**
- `docs/RULES.md @ 3c19230` — "bounds our de-noised AUC at 0.675"; "registration residual is 165 µm rms"; "lifts ours 0.640 → 0.730 and the team 0.929 → 0.984"; "So ≈ 0.07 of the 0.29 gap is reference noise, ≈ 0.22 is missing method."
- `stats/explore/au_step5_bound.json @ a76fdba` — "best_tag": "v0.1b" (one crop); "held_out_mean_auc_ours_obs": 0.6497; "held_out_mean_bound1_perfect_reference_ceiling_for_ours": 0.6751; "held_out_mean_auc_ours_erode0.3": 0.741; "held_out_mean_tile_residual_um_rms": 164.7857

**Lesson.** Bound label and registration noise before blaming the labels, and compute the bound from one stated score.

**Fix.** The conclusion (reference noise is small) stands; the split is not reproducible from committed files: **Open — not fixed**.

<a id="lesson-30"></a>
### 30. Extend a grid when the selected setting sits on its edge

**What happened.** v2 chose the widest band-pass in its grid (0.25–3 mm, TRAIN 0.7677). v7 chose both the largest σ_R (4.0 mm) and the
smallest λ (0.1). The notebook noted only the σ_R edge.

**Evidence.**
- `docs/RULES.md @ 95cf9a6` — "(σ1, σ2) ∈ {(0.10, 1.0), (0.15, 2.0), (0.25, 3.0)} mm"; `stats/s1_v2_config.json @ 1c694f2` — "b2": 0.7677
- `docs/RULES.md @ 7d30ea7` — "{1.0, 1.5, 2.5, 4.0} mm by LOCO"; "λ from {0.1, 1, 10, 100, 1000}"
- `stats/s1_v7_weights.json @ 05d84a7` — "4.0_0.1": 0.7416; `docs/RULES.md @ 05d84a7` — "the best value sat at the edge of the declared grid"

**Lesson.** When the selected setting sits on a grid edge, extend the grid before judging, or report the score as a lower bound for that
method family.

**Fix.** None: refitting now would be post-hoc. **Open — not fixed** (disclosed).

## Data integrity

<a id="lesson-31"></a>
### 31. Assert coverage and both classes before any fit or judgement

**What happened.** 39 % of w028 text3/text4 was missing, yet AUCs were produced on the remaining 61 %. Later the declared veto left 7
training crops with "40–60 k text, 0 blank each"; v6 trained to step 4000 while validation BCE fell 0.657 → 0.022, measuring only "predict
ink everywhere". The judge printed the blank count but checked nothing.

**Evidence.**
- `docs/RULES.md @ 5413b77` — "was computed on the remaining 61 % of those crops"
- `docs/RULES.md @ a76fdba` — "measured: 40–60 k text, 0 blank each"; "falling validation BCE (0.657 → 0.022)"; "at step 4000 of 12000"
- `scripts/s1_judge.py @ 4043cae` — 'print("veto applied: blank px", int(blank.sum()))'

**Lesson.** Assert expected spatial coverage and non-empty classes per crop before any fit or judgement, and stop if either fails.

**Fix.** v6 discarded; v6b retrained on measured class counts (3c19230); `inkeval` returns None for an empty class (5ba7764), and in this
release `inkeval judge` warns when a metric is undefined and `inkeval.label_swap_null` raises when no crop pair has both classes
(`inkeval/cli.py`, `inkeval/stats.py`). No assertion in the training code: **Open — not fixed**.

<a id="lesson-32"></a>
### 32. Key deletions to their owner; verify chunks despite a completion marker

**What happened.** On restart, the w028 crop driver deleted text2's chunk rows 144–209 unconditionally, including rows the overlapping
text3/text4 crops had fetched, and the fetcher's done-marker skipped re-downloading them. The old reproduce guide called every driver
idempotent.

**Evidence.**
- `archive/scripts/run_w028_crops.sh @ 96fb2f4` (then `scripts/`) — "rm -rf data/w028/stack.zarr/0/0/$(seq -s ' data/w028/stack.zarr/0/0/' 144 209)"
- `docs/RULES.md @ 5413b77` — "The restarted crop driver deleted text2's chunk rows 144–209 unconditionally"; "the fetch's done-marker then skipped re-downloading them"
- `archive/docs/reproduce_2026-09-18.md @ b438fe0` (then `docs/reproduce.md`) — "All are idempotent"

**Lesson.** Key every deletion to the crop that owns the data, check overlaps, and treat a completion marker as a claim to verify.

**Fix.** The fetcher now checks chunk presence despite the marker (`scripts/fetch_zarr_region.py @ 5413b77` — "marker present but
{len(missing)} chunks missing: refetching") and rejects empty metadata (e047741). The archived driver keeps the rm line without a warning
(b370331): **Open — not fixed**.

<a id="lesson-33"></a>
### 33. Escalate a data defect wherever it is found

**What happened.** The E1 helper libraries, committed at 03:43:35Z, already noted that the training segments' stored blank class was
identically zero. They rebuilt it silently for exploration. The defect reached the notebook as Incident 3 at 05:43:12Z, 1 h 59 min later.
Meanwhile v6 trained on the defective data until it was stopped ([31](#lesson-31)).

**Evidence.**
- `archive/scripts/explore/mf_lib.py @ a0f3f57` (then `scripts/explore/`) — "stored cls_blank.npy is identically zero (a defect of the earlier run)"
- `archive/scripts/explore/fb_lib.py @ a0f3f57` (then `scripts/explore/`) — "their cls_blank.npy is empty"
- `docs/RULES.md @ a76fdba` — "## Data-integrity incident 3 (found 2026-09-18 06:30 UTC)"; commit times: a0f3f57 03:43:35Z, a76fdba 05:43:12Z

**Lesson.** A data defect found anywhere, including in exploration code, goes into the notebook at once and halts every run that depends
on the data.

**Fix.** Incident 3 was recorded, v6 was discarded and the veto redeclared (a76fdba). The class maps were rebuilt (96ab51d).

<a id="lesson-34"></a>
### 34. Generate every table, comparator and count from one per-crop file

**What happened.** Hand-typed summaries erred three ways. v7's 7-crop 0.668 was compared with 3-crop segment-1 means (v2 0.681, team
0.932), giving "slightly below v2"; on the same 7 crops v2 is 0.639 and the team 0.929 (truncated). E's text says "6 of 7 … and 5 of 7"
where its table shows 7 and 4. TRAIN v0.3p letter 0.753 is the top face; the bottom is 0.712 (truncated).

**Evidence.**
- `docs/RULES.md @ 05d84a7` — "slightly below v2"; "v2 0.681 / 0.687 / 0.713"; "team 0.932 / 0.976 / 0.983."
- `docs/RULES.md @ fe9424c` — "v2 0.681 / 0.745"; "team 0.932 / 0.999" (segment-1 means, 3 crops)
- `results/stats_evaluation7.json @ 5ba7764` — v2 0.639650986922841, v7 0.6683960321669036, team 0.929004087705171
- `docs/RULES.md @ 49be302` — "Per-crop, 6 of 7 clear the pixel bar and 5 of 7 the stroke bar"; stroke rows 0.896, 0.897, 0.871
- `docs/RULES.md @ 95cf9a6` — "v0.3p (peak brightness): 0.691 / 0.753."; `stats/s1_gate_20231005123336.json @ e72979a` — top 0.7531914893617021, bot 0.7129629629629629
- `scripts/release_stats.py @ 5ba7764` — "per-crop pixel AUC (judge_<tag>.json, bottom face), stroke AUC (stats/stroke_test.json), local stroke test L"; no line of it mentions a CSV (checked); `git log -S per_crop_evaluation7 cc5c843` lists only 5ba7764 (a print in `inkeval/example.py`; the same commit adds the CSV), e455383 and cc5c843 (documents)

**Lesson.** Generate every table entry, comparator and count by code from one per-crop file at a cited commit.

**Fix.** Release statistics are computed by `scripts/release_stats.py` (5ba7764) from the per-crop judge records (`judge_<tag>.json`, in
`data/`) and `stats/stroke_test.json` / `stats/local_stroke_test.json` (full-precision stroke and L from `results/toolkit_vs_records.json`
where the toolkit recomputed them, [68](#lesson-68)), and are written to `results/stats_evaluation7.json` and
`results/stats_confirmation.json`. Fixed in this release: `scripts/release_stats.py` also writes the per-crop tables
`results/per_crop_evaluation7.csv` and `results/per_crop_confirmation.csv` (0db607f); `release_stats.py --csv` regenerates both
committed tables byte for byte from the two statistics files (checked). `docs/RULES.md` left as written.

<a id="lesson-35"></a>
### 35. Never overwrite a cited result file

**What happened.** The JSON cited for the S1-v1 verdict was rewritten by five later commits, and its current version (last changed in fe9424c) holds mask-J numbers.
For example, held1 v1b reads 0.649… where the cited commit had 0.643…. Weights lived only in the git-ignored `data/` until the release;
the per-crop judge records (`judge_<tag>.json`, score and class maps) still do.

**Evidence.**
- `docs/RULES.md @ e72979a` — "GATE-S1 v1 verdict, all crops (2026-09-17 18:12 UTC) — stats/s1_gate_20231005123336.json"
- `stats/s1_gate_20231005123336.json @ e72979a` — 0.6432383905877149; same file `@ fe9424c` — 0.6490334397775628; `git log` of the file lists 87dd1bc, 5e333a7, 4db0997, b9ca77b, fe9424c after e72979a
- `.gitignore @ d160337` — "data/"; `.gitignore @ cc5c843` — "/data/"; "*.npy"; `git ls-tree -r cc5c843` lists no `judge_*.json` (checked)

**Lesson.** Write one immutable result file per run, cite it with its commit, and never overwrite a file the notebook cites.

**Fix.** The weights and their SHA-256 sums (`models/SHA256SUMS @ 412b7c7`) and the per-crop release tables (5ba7764; the confirmation
table 0db607f) are committed.
Earlier values can be recovered with `git show <commit>:<path>`. The per-crop judge records are not committed: **Open — not fixed**
(partly).

<a id="lesson-36"></a>
### 36. Reconcile a quantity measured more than once

**What happened.** Two quantities have inconsistent values in the record:
- **Class sizes.** Two analyses of text1 inside the same v0.1b mask report 11.0 M / 11.6 M (RULES.md) and 11 463 835 / 11 862 541
  text/blank pixels (D1 JSON; RULES.md: 11.5 M / 11.9 M). The difference is not explained.
- **Stroke width.** It appears as "≈ 0.4 mm", as a "measured" 0.70 mm, and as a "half-width median 0.161 mm". The last is the TRAIN
  crop's median depth of text pixels inside the label, and it set E's smoothing σ.

**Evidence.**
- `docs/RULES.md @ 2026bab` — "Text px 11.0 M, blank px 11.6 M"; `docs/RULES.md @ 20c16db` — "11.5 M text px / 11.9 M blank px"
- `stats/d1_text1_depth_profile.json @ 20c16db` — "n_text_px": 11463835, "n_blank_px": 11862541
- `docs/RULES.md @ 7375777` — "Strokes are ≈ 0.4 mm wide"; `docs/RULES.md @ cdc291e` — "Measured stroke width 0.70 mm"
- `stats/explore/au_step1_geom.json @ cdc291e` — 20231005123336/train "50": 0.1606
- `docs/RULES.md @ 5915848` — "half the measured stroke half-width (0.161 mm median"

**Lesson.** Give each physical quantity one definition and one measurement. Log class counts with every analysis, and explain any
disagreement.

**Fix.** **Open — not fixed.**

<a id="lesson-37"></a>
### 37. Invalidate cached class maps by content, not by file existence

**What happened.** The judge builds `cls_text.npy` and `cls_blank.npy` only if they do not exist. A changed reference or veto therefore
takes effect only if a driver deletes the cache first. The re-judge and veto-fix drivers each did so by hand.

**Evidence.**
- `scripts/s1_judge.py @ acda042` — 'if not os.path.exists(os.path.join(d, "cls_text.npy")):'
- `archive/scripts/run_s1_rejudge.sh @ 7375777` (then `scripts/`) — "rm -f $D/cls_text.npy $D/cls_blank.npy $D/label.npy $D/judge_*.json"
- `scripts/run_fix_veto.sh @ 96ab51d` — "rm -f $D/cls_text.npy $D/cls_blank.npy $D/label.npy"

**Lesson.** Key cached labels by a hash of their inputs (label, registration, mask and veto), or rebuild them on every run.

**Fix.** The toolkit never caches classes to disk; `inkeval.judge` rebuilds them on every call unless the caller passes them
(`inkeval/metrics.py @ 5ba7764` — "text, blank = judge_classes(label, mask, pitch_um)"), and `docs/METHODS.md` §11 discloses the caching
(e455383). `scripts/s1_judge.py` still caches by existence: **Open — not fixed** (research pipeline).

<a id="lesson-38"></a>
### 38. Know what a reference map is before thresholding it

**What happened.** The reading-run agreement AUC thresholds the team prediction at > 0.80 and < 0.20 on `ink_ds8.jpg`. That is the
downsampled JPEG overview which Incident 3 found has a soft background floor (mean 0.30–0.40, never below 0.10). INFERENCE: the
"confident blank" class may be small and biased. The original R1/R2 values were computed by code that was never committed.

**Evidence.**
- `scripts/n1_reading_null.py @ bde701a` — "team[k] = (t > 0.80, t < 0.20)"; "overview/ink_ds8.jpg"
- `docs/RULES.md @ a76fdba` — "downsampled overview JPEG has a soft background floor"; "mean value 0.30–0.40"
- `docs/RESULTS.md @ e455383` — "were computed by inline code that was not committed"

**Lesson.** Know the provenance, resolution and value distribution of any reference map before thresholding it, and report class sizes
with every agreement AUC.

**Fix.** N1 gives the statistic a layout null (bde701a). It does not address class sizes or the JPEG floor. **Open — not fixed.**

<a id="lesson-39"></a>
### 39. Re-check a substitute input against the declared threshold

**What happened.** Segment 20231005123336 has no `onsheet_ds8.png`, so R1's on-sheet test used `render_ds8.jpg` instead. The check run
afterwards found coverages of 0.97, 0.89, 0.94 and 0.91, so one window was below the declared 0.90. The text nevertheless concludes that
the substitution "did not admit an off-sheet window".

**Evidence.**
- `docs/RULES.md @ a31bbc1` — "on-sheet coverage is >= 0.90"
- `scripts/select_unread.py @ c73cea4` — "overview/render_ds8.jpg"
- `docs/RULES.md @ c73cea4` — "0.97, 0.89, 0.94, 0.91), so the substitution did not admit an off-sheet window"

**Lesson.** When a declared input is replaced, re-check the result against the declared threshold, and report any failure as a deviation.

**Fix.** C1 names its fallback in advance (`docs/RULES.md @ 46a4bfc` — "else the CT mid-slice overview mid_l3.png"). The R1 window at 0.89
stands as run and is disclosed here.

<a id="lesson-40"></a>
### 40. Check availability, near-duplicates and identifiers before planning

**What happened.** The v8 plan found three more labelled segments unusable, because their surface volumes are not published. One of them
is a probable near-duplicate of an evaluation segment, so using it would have leaked. Another of the three IDs, 20231012184423, is the
label ID of training segment 20231012184424. Only two unused segments really remain.

**Evidence.**
- `docs/RULES.md @ f3b43d3` — "(20231005123333, 20231007101615, 20231012184423) CANNOT be added"; "20231005123333 would in any case have been excluded as a probable" [near-duplicate]
- `docs/RULES.md @ 3816e30` — "20231012184424 (label 20231012184423, 23552×15872)"
- `results/input_manifest.json @ 412b7c7` — "note": "published as 20231012184423"

**Lesson.** Before planning, check that every input is published, screen for near-duplicates of the evaluation data, and keep segment IDs
and label IDs apart.

**Fix.** The near-duplicate was excluded in advance (f3b43d3). The identifier slip remains in RULES.md and is stated here.

<a id="lesson-41"></a>
### 41. Hash inputs and outputs, and state exactly what was verified

**What happened.** Verification covered less than the drafts claimed: 12 of 20 manifest inputs verified identical to public copies (the
other 8 are `.zarray`/`.zattrs` metadata), 4 weight checksums, no CT-chunk hashes, map regeneration on 1 of 7 evaluation crops, and
`tests/test_published.py` on one crop, skipped without data. The drafts (e455383) already said maps regenerate "bit for bit".

**Evidence.**
- `results/input_manifest.json @ 412b7c7` — "verified_identical": true on 12 of 20 inputs (counted here)
- `results/reproducibility_check.json @ 412b7c7` — a single key, "20231005123336:held1"; `models/SHA256SUMS @ 412b7c7` — 4 lines
- `tests/test_published.py @ d2564a7` — '"20231005123336", "derived", "held2"'; 'reason="full research data not on disk"'
- `README.md @ e455383` — "The released weights regenerate the published v8, GP-R1 and E maps **bit for bit**"

**Lesson.** Hash inputs and outputs, and state each check's exact coverage next to the claim.

**Fix.** Regeneration now covers all 7 evaluation crops (`results/reproducibility_check.json @ 0e040c1`), and the toolkit matches 65 of 65
published records on 13 crops (`results/toolkit_vs_records.json @ a16a6a2` — "failures": 0). CT chunks unhashed: **Open — not fixed**.

## Physics: what 2.4 µm CT does and does not show

<a id="lesson-42"></a>
### 42. Sheet topography carries no ink signal at 2.4 µm

**What happened.** The profilometry paper's resolution curve predicted this, and the data agreed:
- Relief was at chance on every w028 crop.
- Thickness was at chance on text1 (0.498) and on verified Scroll 1 letters (0.478, one TRAIN crop).
- Papyrus subtraction scored 0.515 held-out on segment 1, and 0.556 over the 7 evaluation crops (truncated).

**Evidence.**
- `docs/background/paper_2603.27698.md @ d160337` (then `docs/paper_2603.27698.md`) — held-out Dice of the paper's ink segmentation from profilometry heightmaps (not an AUC): "0.516 at 2.04 µm; 0.478 at 2.72 µm" (unrelated to our thickness AUC 0.478)
- `docs/RULES.md @ bc38713` — "Relief is at chance on every crop."; `docs/RULES.md @ 20c16db` — "Thickness t: AUC 0.498 (nothing)."
- `docs/RULES.md @ 4f9ef66` — "thickness AUC 0.478"; `docs/RULES.md @ 87dd1bc` — "v0.1b 0.515 / 0.423"
- `results/stats_evaluation7.json @ 5ba7764` — v0.1b pixel 0.5560154267888036

**Lesson.** Do not pursue surface-relief ink detection on 2.4 µm CT. Check published resolution curves before choosing a route.

**Fix.** Route B (papyrus subtraction) was closed (ee25abe), and later methods use brightness. For how the 0.478 was reported in the
release, see [69](#lesson-69).

<a id="lesson-43"></a>
### 43. Ink-correlated contrast is not surface-local

**What happened.** The non-writing face, 50–60 µm from the ink, reads verified text held-out at 0.6234 against 0.6355 for the writing
face (RULES.md: 0.623 / 0.636).
k_top and k_bot are both 50 %-of-peak crossings, so the faces' δ = 0 channels are the same quantity (corr 0.96) and the middle 25–35 µm of
the sheet is never sampled. Two-face features add 0.6432 − 0.6355 = 0.0077 (RULES.md: "+0.008").

**Evidence.**
- `docs/RULES.md @ cdc291e` — "held-out at 0.623, indistinguishable from the writing face at 0.636"; "same quantity (corr 0.96); the middle 25–35 µm of the sheet is unsampled by our features"; "Two-face features gain only +0.008 over one face."
- `stats/explore/tf_step5_heldout.json @ cdc291e` — "ALL": 0.6432, "BOT": 0.6355, "TOP": 0.6234
- `docs/RULES.md @ 1c694f2` — "Input: the 22 face-aligned depth samples" (v5); `@ 7d30ea7` — "ds8_x: 22 face-anchored depth channels + coverage"

**Lesson.** Do not model ink as surface-local at this resolution; check what a depth anchor samples first.

**Fix.** Recorded as a data-contract correction (cdc291e). INFERENCE: the learned models use the same face-anchored channels, so the sheet
middle is still unsampled: **Open — not fixed**.

<a id="lesson-44"></a>
### 44. Measure the depth profile per crop before fixing sampling depths

**What happened.** On text1 the bottom-face contrast peaks 2–3 slices inside the sheet. v0.1 sampled S_bot one slice outside, where the
block AUC is 0.537, against 0.636 at the peak (truncated). On Scroll 1 the depth of maximum contrast varies by crop (held1: δ −4, with a
second bump at +3), and "No single depth exceeds 0.58 anywhere".

**Evidence.**
- `docs/RULES.md @ 20c16db` — "Bottom face peaks INSIDE the sheet at δ = −2…−3 slices (5–7 µm)"
- `stats/d1_text1_depth_profile.json @ 20c16db` — bottom auc_block 0.6365558675387333 (δ −3), 0.5377803564114993 (δ +1)
- `archive/docs/METHOD_v0.2_papyrus_subtraction.md @ a56bd42` (then `METHOD.md`) — "S_bot = I(k_bot + 1)"
- `docs/RULES.md @ 6d1c078` — "bot max 0.564 (δ −4), second bump 0.539 at δ +3"; "No single depth exceeds 0.58 anywhere"

**Lesson.** Measure the depth profile on each crop before fixing sampling depths, and prefer features that span depth.

**Fix.** The S1-v1 templates span "δ ∈ [−4, +6] slices" (038aef0). The learned models take all 22 depth channels.

<a id="lesson-45"></a>
### 45. The deficit is amplitude, not position

**What happened.** Our hand-built scores peak 0.53 mm inside strokes, close to where the team map peaks (0.48 mm), with no registration
offset. Their contrast-to-noise across the stroke is 1.6 (v2), against 6.3 for the team model.

**Evidence.**
- `docs/RULES.md @ 3c19230` — "peaks 0.53 mm inside it, the same place the team map peaks (0.48 mm)"; "contrast-to-noise across the stroke is 1.6 (v2) vs 6.3 (team)"; "The gap is amplitude, i.e. spatial and contextual integration, not localisation."

**Lesson.** Before choosing the next method, find out whether a performance gap is one of position, amplitude or context.

**Fix.** This finding motivated the non-linear stroke-scale model v6b (3c19230), which led to v8 and E.

<a id="lesson-46"></a>
### 46. Ink contrast is a broad brightness excess, and profile shape adds a little

**What happened.**
- Edge descriptors scored at or below chance (sharpness 0.399).
- Text-minus-blank contrast was positive at every sampled depth.
- Profile shape still added +0.026 held-out over the same 22 channels used linearly, on 7 of 7 crops. This narrows the notebook's "level
  effect, not a profile-shape effect".
- The gap to the team model (0.6639 against 0.9158 on the ds8 grid; the declaration's prose rounds them to 0.664 and 0.916) was not
  closed.

**Evidence.**
- `stats/explore/es_DECLARATION.md @ 8fa65b7` — "Bsharp 0.399"; "the text-minus-blank contrast is positive at every one of the 11 sampled"; "+0.026 held-out over using the same 22 channels linearly at the same scales, on 7/7 crops."; "best new measure 0.664 held-out"
- `stats/explore/es_step3_heldout.json @ 8fa65b7` — held-out mean "ALL": 0.6639, "team": 0.9158; `stats/explore/es_DECLARATION.md @ 8fa65b7` — "| MEAN | 0.6182 | 0.6371 | 0.6163 | 0.6519 | 0.6634 | 0.6639 |"
- `docs/RULES.md @ cdc291e` — "effect, not a profile-shape effect (LVL 0.663 > SHAPE21 0.636 LOCO)"
- `docs/RULES.md @ 20c16db` — "Text pixels are ~2–3 uint8 units (≈2 %) brighter than blank at every depth."

**Lesson.** At 2.4 µm, model ink as a weak brightness excess spread over depth. Shape features help a little but do not replace spatial
context.

**Fix.** Exploration only. The shape verdict never reached RULES.md ([66](#lesson-66)).

<a id="lesson-47"></a>
### 47. Measure an orientation field's reliability before using it

**What happened.** v0.1b's fibre-frame subtraction smoothed the structure tensor at σ_t = 6 px. At that scale the orientation field is
noise: the top and bottom faces disagree by 24.6°, against 45° by chance. It becomes physical only at σ_t ≥ 25 px. Fibre texture is real
but carries no ink contrast.

**Evidence.**
- `docs/RULES.md @ cdc291e` — "at its σ_t = 6 px the orientation field is noise (median top-vs-bottom-face disagreement 24.6°, chance 45°)"; "at σ_t ≥ 25 px (12–16°)"; "changes held-out AUC by 0.004"

**Lesson.** Measure an orientation field's reliability at the scale where you use it, for example by agreement between independent
estimates, before building on it.

**Fix.** The papyrus-subtraction route was closed (ee25abe), and the audit recorded that "the papyrus-subtraction route is dead"
(3c19230).

<a id="lesson-48"></a>
### 48. Equal sheet geometry can hide large contrast differences

**What happened.** All segment-1 crops share the same sheet geometry, yet the median text-minus-blank crest contrast ranges from 1.4
(held1) to 3.8 (train) uint8 units. held1 is the worst crop for every hand-built method, while the team model reads it at 0.982. A
declared per-crop calibration test on the 8 training crops found no calibration headroom: mean SELF − GLOBAL_h = −0.0354, where more than
+0.02 was needed. INFERENCE: mis-calibration does not explain held1.

**Evidence.**
- `docs/RULES.md @ 43a5624` — "median thickness 22.6–24.6 slices ≈ 57 µm"; "text − blank = 1.4 (held1) vs 3.8 (train), 2.5 (held2), 3.0 (held3) uint8 units"
- `docs/RULES.md @ 5e333a7` — "held1 is the outlier for every method of ours"; `docs/RULES.md @ 87dd1bc` — held1 row ending "0.982 / 1.000 |"
- `stats/explore/ca_DECLARATION.md @ a76fdba` — "Fitted on the 8 TRAINING crops only"; "SUPPORTED only if mean(SELF) - mean(GLOBAL_h) > +0.02 AUC"; `stats/explore/ca_step1_percrop.json @ 96ab51d` — "SELF_minus_GLOBAL_h": -0.0354

**Lesson.** Expect large per-crop differences in contrast even on geometrically identical sheet. Brightness-only scores need spatial
context, and per-crop recalibration does not supply it.

**Fix.** Not applicable: this is a physics finding.

<a id="lesson-49"></a>
### 49. A depth template transfers across scrolls, but weakly

**What happened.** A depth template measured on w028 (PHerc. 1667), with no Scroll 1 supervision (v1a), scored the Scroll 1 TRAIN crop
like a template measured on that crop (0.739 against 0.740). After registration it also scored the same held-out (0.649 against 0.651).
The shared signal is weak: it falls from 0.74 on TRAIN to 0.64 on held1.

**Evidence.**
- `docs/RULES.md @ 95cf9a6` — "px 0.739 / letter 0.898"; "v1b (template measured on TRAIN): px 0.740 / letter 0.898"
- `docs/RULES.md @ 303bc85` — "The depth template does not generalise from TRAIN (0.74) to held1 (0.64)"
- `docs/RULES.md @ 87dd1bc` — "Held-out means: v1b 0.651 / 0.681; v1a 0.649 / 0.686"

**Lesson.** A depth signature can transfer between scrolls, but a weak signal stays weak after transfer. Judge it held-out.

**Fix.** Not applicable: this is a physics finding.

<a id="lesson-50"></a>
### 50. Check stack depth before running a 9 µm test

**What happened.** The published 28-slice w040 surface volume clipped the sheet's bright band and left a mask of 3.4 %. GATE-T2(b) was
therefore inconclusive, and T2(a) was never run. The 9 µm route was never fairly tested.

**Evidence.**
- `docs/RULES.md @ 2026bab` — "mask only 3.4 % (band clipped: 25 % of pixels with k_top ≤ 0, 29 % with k_bot ≥ K−1 in the 28-slice stack"; "a wider stack (more slices) is needed for a fair 9 µm test"
- `docs/RULES.md @ 0825de7` — "GATE-T2(a) (w028 pooled to 9.6 µm) is not run"

**Lesson.** Check that the stack contains the whole sheet before running a gate on it.

**Fix.** The release lists GATE-T2a as declared and never run (`docs/RESULTS.md @ e455383`). The 9 µm route remains untested.
**Open — not fixed.**

## Modelling

<a id="lesson-51"></a>
### 51. Re-derive pixel-scale mask rules when the voxel size changes

**What happened.** Damage and grain rules written for 9 µm data destroyed 2.4 µm charts, where fibres are resolved: the pixel-scale tear
rule masked 57 % of the on-sheet area, a 0.4 mm dilation of every void blanked 100 %, and the grain rule's 0.3 mm discs covered ~94 % of
the sheet. Re-expressed above fibre scale, the mask covered 36.0 % (top face).

**Evidence.**
- `docs/RULES.md @ a56bd42` — "masks 57 % of the on-sheet area at 2.4 µm"
- `docs/RULES.md @ 2b61f05` — "dilating every void by 0.4 mm blanked 100 % of the chart"
- `docs/RULES.md @ 625a991` — "their 0.3 mm discs covered ~94 % of the sheet"
- `docs/RULES.md @ 2026bab` — "mask 36.0 % (top) / 35.9 % (bottom) of the chart"

**Lesson.** When the voxel size changes, re-express mask rules in physical units above fibre scale and check coverage before any AUC.

**Fix.** Tear rule on smoothed thickness (a56bd42); margin only around macroscopic damage (2b61f05); grains by component area (625a991);
mask J, 0.1 mm margin (55cd58e).

<a id="lesson-52"></a>
### 52. Check that background subtraction does not remove the signal

**What happened.** The fibre-background subtraction and 0.15–1.2 mm band-pass of v0.1/v0.2 removed the only contrast present (AUC 0.50).
v0.2's writing-face mean was 0.503 (truncated; RULES.md: 0.504). Plain smoothed band brightness (v0.3p) reached 0.666 held-out (RULES.md;
0.665 from the JSON, truncated).

**Evidence.**
- `docs/RULES.md @ 20c16db` — "v0.1's fibre subtraction and 0.15–1.2 mm band-pass removed it (AUC 0.50)"
- `docs/RULES.md @ ee25abe` — "Mean on the writing face 0.504."; `stats/w028_gate_t1_v0.2.json @ ee25abe` — "mean_auc_text_crops_writing_face": 0.5037565238179025
- `docs/RULES.md @ a492c1f` — "Held-out mean (text2–text5) 0.666"

**Lesson.** Measure where the contrast is before designing what to subtract, and check that the subtraction keeps it.

**Fix.** v0.3 drops all subtraction ("method v0.3 (no subtraction", 0825de7).

<a id="lesson-53"></a>
### 53. Integrate at stroke scale, per depth channel, before combining

**What happened.** Raw pixel contrast is about 2 % and noisy.
- Smoothing to 0.2 mm raised face-intensity AUC from 0.565 to 0.638 (truncated).
- Block means beat pixels: 0.613 against 0.576 for the top face at δ = 0 (truncated).
- The optimal linear pooling kernel is radially symmetric, so stroke-shaped kernels add nothing.
- Smoothing each depth channel before combining beats projecting first and smoothing afterwards (LOCO 0.714 against 0.672).

**Evidence.**
- `docs/RULES.md @ 84f2947` — "0.565 (raw) → 0.615 (0.05 mm) → 0.630 (0.1) → 0.639 (0.2)"; `stats/d1b_text1_scale_sweep.json @ 84f2947` — "0.2": 0.6387
- `stats/d1_text1_depth_profile.json @ 20c16db` — top δ = 0 pixel 0.5769538003900161, block 0.6138753676882089
- `docs/RULES.md @ cdc291e` — "(0.6754 / 0.6755 / 0.6742)"; "beats project-then-smooth (LOCO 0.714 vs 0.672)"

**Lesson.** Integrate at stroke scale (0.2–0.3 mm), and do it per depth channel before combining the channels.

**Fix.** v0.3p and S1-v1 smooth at 0.25 mm (0825de7, 038aef0). Smooth-then-combine is step 1 of v7 (7d30ea7).

<a id="lesson-54"></a>
### 54. Measure each term alone before adding it

**What happened.** The inpainting-residual term of v0.2 scored at chance on its own (text1 top 0.493, truncated). Adding it moved the
writing-face mean from 0.509 (v0.1b) to 0.503 (truncated from `stats/w028_gate_t1_v0.1b.json @ bc38713` and
`stats/w028_gate_t1_v0.2.json @ ee25abe`; RULES.md: 0.510 / 0.504).

**Evidence.**
- `stats/w028_gate_t1_v0.2.json @ ee25abe` — "auc_a": 0.49337053228012495; "mean_auc_text_crops_writing_face": 0.5037565238179025
- `stats/w028_gate_t1_v0.1b.json @ bc38713` — "mean_auc_text_crops_writing_face": 0.5098104892186252
- `docs/RULES.md @ bc38713` — "on the declared writing face: 0.510"; `docs/RULES.md @ ee25abe` — "The inpainting residual adds nothing."

**Lesson.** Measure each term's AUC on its own before adding it to a combined score, and drop terms that add nothing.

**Fix.** Route B was closed (ee25abe).

<a id="lesson-55"></a>
### 55. Few training crops mean immediate memorisation

**What happened.**
- With one training crop, v5's validation BCE rose from step 0, and "the early-stopped model is the initialisation".
- With 8 crops, v6b and v6c peaked at steps 750 and 250 of 12 000. 93.75 % of v6b's budget was unused (RULES.md: "94 %") and 97.9 %
  of v6c's (truncated).
- With 15 crops, v8's checkpoint came at step 9500. That is partly an artefact of AUC selection ([23](#lesson-23)).

**Evidence.**
- `docs/RULES.md @ 0a834eb` — "1000: 0.060 / 2.342"; `docs/RULES.md @ b9ca77b` — "the early-stopped model is the initialisation"
- `docs/RULES.md @ db529dd` — "**step 750 of 12 000**"; "94 % of the declared training budget was wasted"
- `docs/RULES.md @ cd3ea3d` — "v6c's judged checkpoint is step **250** of 12 000"; `docs/RULES.md @ bc24d20` — "The judged checkpoint is step 9500 of 12 000"

**Lesson.** With few training crops, expect memorisation within a few hundred steps. Add data before adding steps, and size the step
budget from the measured curve.

**Fix.** More training crops (f3b43d3, 8a3998f). GP-R1's 4000-step budget was set from this measurement (9d4ae3f).

<a id="lesson-56"></a>
### 56. Validate on a whole separate crop

**What happened.** v5 early-stopped on a contiguous band of 15 % of the rows of its only training crop. That band is spatially adjacent to
the training pixels.

**Evidence.**
- `docs/RULES.md @ 1c694f2` — "15 % of TRAIN rows (a contiguous band) held out for early-stopping only"
- `scripts/s1_v5.py @ 1c694f2` — "val[int(0.85 * H):] = True"
- `docs/RULES.md @ b9ca77b` — "early stopping on a WHOLE separate crop instead of a row band"
- `docs/RULES.md @ f3b43d3` — "(20231012184424/held4 stays the validation crop and is never trained on)"; `docs/RULES.md @ 3f88fdf` — "no-team-veto labels, same validation crop"
- `docs/RULES.md @ 7d30ea7` — "every parameter below is nevertheless selected by leave-one-crop-out on the 8 TRAINING crops only" (v7)

**Lesson.** Validate on a whole crop that is never trained on or judged, not on a band of a training crop.

**Fix.** `scripts/s1_v5.py @ b9ca77b` adds a separate validation crop ('VAL_DIR = os.environ.get("V5_VAL_DIR")'). The U-Nets from v6 on
(v6b, v6c, v8) and GP-R1 select checkpoints on it. v7, a ridge regression, is selected by leave-one-crop-out on the training crops and
uses no validation crop.

<a id="lesson-57"></a>
### 57. Select checkpoints by the bar's metric, on more than one crop

**What happened.** BCE selection picked v6b's step 750 (BCE 0.703, truncated; INFERENCE: worse than a constant predictor's ≈ 0.68 at the
56 k / 77 k balance) and v6c's step 250, though the bars are AUC. With AUC selection on one validation crop, v8's validation AUC is flat
from step 1000 (0.653–0.702, truncated). INFERENCE: the chosen step (9500) is the maximum of noise. Its validation AUC (0.702) sits far
below the evaluation AUC (0.839, truncated), and `models/v8_unet.pt.json` records no per-step evaluation AUC to check tracking against.

**Evidence.**
- `docs/RULES.md @ cd3ea3d` — "checkpoints are selected by validation BCE while the bars are AUC"
- `models/v6b_unet.pt.json @ 412b7c7` — "best_val_bce": 0.7039644718170166; `docs/RULES.md @ 3c19230` — "(56 k text, 77 k blank)"
- `models/v8_unet.pt.json @ 412b7c7` — val_auc 0.6535116607087867 (min, steps ≥ 1000) and 0.7026650761409663 (max, step 9500)
- `results/stats_evaluation7.json @ 5ba7764` — v8 pixel "mean": 0.8395000189894518

**Lesson.** Select checkpoints by the bar's metric, on more than one validation crop, and check that validation tracks evaluation.

**Fix.** v8 selects by validation AUC (f3b43d3); single validation crop: **Open — not fixed**.

<a id="lesson-58"></a>
### 58. Gains on the training crop are not generalisation

**What happened.** From v1b to v2 to v3, TRAIN pixel AUC rose (0.743, 0.768, 0.773), but held-out AUC did not follow (0.651, 0.683,
0.657). Across 7 crops under mask J, v2, v3 and v1b score 0.64, 0.63 and 0.62.

**Evidence.**
- `docs/RULES.md @ 87dd1bc` — TRAIN v1b "| 0.743 / 0.927 |"; held-out "v1b 0.651 / 0.681"
- `docs/RULES.md @ 5e333a7` — "b2 0.768"; "mean 0.683 / 0.703"
- `docs/RULES.md @ 4db0997` — "TRAIN 0.773 / 0.883"; "held-out mean 0.657 / 0.666"; "more linear features fit TRAIN better and" [generalise no better]
- `docs/RULES.md @ 72ea621` — "v2 0.64, v3 0.63, v1b 0.62"

**Lesson.** Judge feature additions on held-out data. Gains on the training crop are not evidence of generalisation.

**Fix.** The project moved to non-linear learned models (v5, then v6b, then v8).

<a id="lesson-59"></a>
### 59. Leave-one-crop-out does not show the cross-segment gap

**What happened.** v7's training leave-one-crop-out AUC (0.7415, truncated) overstated its held-out pixel AUC (0.668) by 0.073 (computed
here; RULES.md says "0.074", from rounded terms). Segment 2 was weaker for every method. For v7, segment-2 crops scored 0.562–0.680 (truncated; RULES.md:
0.562–0.681) and segment-1 crops 0.663–0.791.

**Evidence.**
- `docs/RULES.md @ 05d84a7` — "Training LOCO 0.742 against held-out 0.668 is a 0.074 generalisation gap"; "(0.562–0.681 vs 0.663–0.791)"
- `stats/s1_v7_weights.json @ 05d84a7` — "loco_mean": 0.7415620423091235; `results/stats_evaluation7.json @ 5ba7764` — v7 pixel 0.6683960321669036

**Lesson.** Expect a cross-segment gap that within-training leave-one-crop-out does not show, and hold out whole segments where possible.

**Fix.** C1 adds untouched windows on both evaluation segments, "up to 3 per segment" (46a4bfc). Transfer to a third segment is untested.
 **Open — not fixed.**

<a id="lesson-60"></a>
### 60. Reproduce a known-good recipe before inventing new ones

**What happened.** By the notebook's count (3f88fdf), seven methods were invented before the public Grand-Prize approach was reproduced. The learned models also took 19.2 µm
input (an 8× lateral decimation), where the Grand-Prize work used 7.91 µm. Once it was reproduced at this scale, GP-R1 tied the plain
U-Net v8 after one CPU run of 8 334 s: v8 − GP-R1 pixel = +0.011 [−0.014, 0.042] (truncated), positive on 3 of 7 crops.

**Evidence.**
- `docs/RULES.md @ 0e86155` — "We have never once reproduced a known-good recipe as a baseline"; "8x lateral decimation"
- `docs/RULES.md @ 3f88fdf` — "this project invented seven methods without ever reproducing"; `docs/RULES.md @ c406bf7` — "It also retires failure mode 3 of the strategy note"
- `results/stats_evaluation7.json @ 5ba7764` — v8-gpr1 pixel 0.011871561370007475; `results/logs/README.md @ bde701a` — "GP-R1 training (4 000 steps, 8 334 s)"

**Lesson.** Reproduce the known-good recipe as a baseline before inventing new methods. It is often the cheapest informative experiment.

**Fix.** GP-R1 was declared (3f88fdf), parameterised (9d4ae3f) and run (c406bf7). GP-R2 at 9.6 µm was declared and never run
([66](#lesson-66)).

<a id="lesson-61"></a>
### 61. A scale-limited reproduction limits what its negative result means

**What happened.** The full-width GP encoder cost 6.7 s/step (22 h) on 4 CPUs, so GP-R1 was scaled to 488 937 parameters (RULES.md: "489
k"), 4000 steps and 19.2 µm input. Its qualifier was declared ("a difference in degree that must be remembered"), dropped by the E result
("GP-R1 established it is not architecture") and restored by D3 ("no measurable architecture effect at 19.2 µm on 7 crops").

**Evidence.**
- `docs/RULES.md @ 9d4ae3f` — "6.7 s/step (22 h for 12 000 steps)"; "giving 489 k parameters and 1.97 s/step"; `docs/METHODS.md @ bde701a` — "488 937 parameters"
- `docs/RULES.md @ 3f88fdf` — "that is a difference in degree that must be remembered"; `docs/RULES.md @ 49be302` — "GP-R1 established it is not architecture"
- `docs/RULES.md @ bde701a` — "\"no measurable architecture effect at 19.2 µm on 7 crops\""

**Lesson.** State a reproduction's scale with every negative result it yields, and carry the qualifier wherever it is cited.

**Fix.** The release keeps it (`README.md`, since e455383 — "CPU-scaled version of the architecture").

<a id="lesson-62"></a>
### 62. Render calibrated outputs, not rank-normalised maps

**What happened.** E rank-normalises each map inside the mask, which makes the score distribution uniform by construction. A percentile
display stretch then fills the render with texture.

**Evidence.**
- `scripts/ensemble_e.py @ 4df539e` — "r[mask] = (rankdata(x[mask]) / mask.sum()).astype(np.float32)"
- `docs/RULES.md @ 9de8704` — "rank-normalisation makes the score uniform by construction"

**Lesson.** Render a calibrated probability output for human inspection, and never use a rendering choice to support a letter that the
measurement does not support.

**Fix.** Not implemented; recorded as a limitation of R2. **Open — not fixed.**

## Process and honesty

<a id="lesson-63"></a>
### 63. Use commit times, not typed timestamps, as pre-registration evidence

**What happened.** The typed "UTC" stamps in RULES.md disagree with the commit times:
- GATE-S1 is "declared 2026-09-17 17:00 UTC" in a commit made at 15:56:42Z.
- R1's result is stamped 21:00 in a commit made at 20:48:09Z.
- v0.1b is stamped 23:03, earlier than v0.1's 23:20, and was committed at 04:07:36Z the next day.

Two stamps were later corrected by hand.

**Evidence.**
- `docs/RULES.md @ 038aef0` — "declared 2026-09-17 17:00 UTC, BEFORE any Scroll 1 stack is read"; commit time 2026-09-17T15:56:42Z
- `docs/RULES.md @ e8d6a6c` — "## R1 RESULT (2026-09-18 21:00 UTC)"; commit time 2026-09-18T20:48:09Z
- `docs/RULES.md @ 2026bab` — "method v0.1b (2026-09-16 23:03 UTC)"; `@ 625a991` — "method v0.1 (2026-09-16 23:20 UTC)"; commit time of 2026bab 2026-09-17T04:07:36Z
- commit message of 10d098e — "Fix two timestamps in RULES.md"

**Lesson.** Use commit hashes and commit times as the evidence of order. Typed timestamps are only notes.

**Fix.** `results/preregistration_order.json` records commit times (bde701a; regenerated 34cc327), and `docs/METHODS.md` states
"Hand-typed times in notebook headings are not evidence; commit times are." (bde701a).

<a id="lesson-64"></a>
### 64. Commit each declaration on its own before any result exists

**What happened.** The stroke-test and L declaration commits already contain results; tf was declared and reported together; D1b has no
declaration; ca's declaration preceded its result by 82 s; the order check still marked stroke and L "OK". E, by contrast, was declared
before v8's result (18:59:51Z vs 19:21:12Z).

**Evidence.**
- commit message of d27193f — "Declare and implement the stroke test"; `stats/stroke_test.json @ d27193f` — "stroke_auc": 0.6791
- commit message of cdc291e — "Declare and run the local stroke test L"; `stats/local_stroke_test.json @ cdc291e` — "L": 0.7623; `stats/explore/tf_DECLARATION.md` and `tf_step5_heldout.json` both added in cdc291e
- `docs/RULES.md @ 84f2947` — "### D1b result, text1 (2026-09-17 15:20 UTC)" (no D1b declaration anywhere); `stats/explore/ca_DECLARATION.md @ a76fdba` (05:43:12Z), result 96ab51d (05:44:34Z)
- `results/preregistration_order.json @ bde701a` — "declared_commit": "d27193f", "result_commit": "a0f3f57", order "OK"
- `README.md @ e455383` — "the git history proves the order"

**Lesson.** Commit each declaration alone, before any result exists, and point the order check at the first commit containing a result.

**Fix.** Later tests declared separately (46a4bfc, bf040d0, 2e92310). Disclosed as a limitation: `docs/RESULTS.md` §1 lists the stroke
test, L and R2 as exceptions (043ba8d); the heading-based check (34cc327) still marks them "OK".

<a id="lesson-65"></a>
### 65. Do not add a statistic the declaration ruled out

**What happened.** R1 was declared to report renders "and nothing else", with the team model not used to "score, threshold or adjust
anything". The result then scored v8 against the team model's thresholded confident ink and blank. That statistic is post-hoc for R1, and
pre-registered only from R2 on.

**Evidence.**
- `docs/RULES.md @ a31bbc1` — "The rendered score map, at the same scale and stretch as the validation renders, and nothing else."; "score, threshold or adjust anything in R1"
- `docs/RULES.md @ e8d6a6c` — "AUC of v8 separating the team model's confident ink (> 0.80) from its confident blank (< 0.20)"
- `docs/RULES.md @ c74372d` — "The same agreement statistic (AUC of our score against the team model"

**Lesson.** Do not add a statistic that the declaration ruled out. If you add one anyway, label it post-hoc where it is used.

**Fix.** N1's declaration records that the statistic "was introduced after R1's result and was never given a null" (2e92310).

<a id="lesson-66"></a>
### 66. Close every declared or promised item with an outcome

**What happened.** The w028 repair was promised, then dropped for an inaccurate reason ("already put every w028 method at chance"; v0.3p
scored text2 0.602). E1 declared eight hypotheses and an adversarial re-measure; RULES.md writes up items 1, 2, 3 and 5 only, omitting
item 4's "SUPPORTED" verdict, items 6, 7 and 8, and the re-measure. D2 was deferred and GP-R2 never run.

**Evidence.**
- `docs/RULES.md @ 5413b77` — "text3 and text4 are refetched and ALL their derived products recomputed"; `@ d07ddf5` — "(text1, text2, text5 and both blanks already put every w028 method at chance)"; `@ a492c1f` — "text2 0.602"
- `docs/RULES.md @ 47febe8` — "Every claimed gain above baseline + 0.02 is adversarially re-measured"; "(7) RESOLUTION: the same per-depth"; "(8) a broad simple-feature sweep to bound what simple physics"
- `stats/explore/es_DECLARATION.md @ 8fa65b7` — "SUPPORTED: exactly level-invariant depth derivatives alone reach held-out 0.616"; `archive/scripts/explore/hr_step1_reg.py @ 8fa65b7` (then `scripts/explore/hr_step1_reg.py`) — "published at 2.258 um/px"
- `docs/RULES.md @ 3f88fdf` — "Diagnostic D2 is deferred"; `@ c406bf7` — "GP-R2 at 9.6 µm is the declared next test"

**Lesson.** Close every declared or promised item with a reported outcome, including "not done, because …".

**Fix.** Disclosed: `docs/RESULTS.md` §1 lists every declared item not completed, including the w028 repair, "E1 items 6–8" and the
adversarial re-measure (0e040c1), as well as D2-distil and GP-R2.

<a id="lesson-67"></a>
### 67. Keep failed and superseded numbers, and re-judge every method once

**What happened.** Every crop was recorded, not only the best, and failed versions stayed on record. When the reference changed
(per-crop offsets) or the judge mask changed (mask J), earlier numbers stayed "as run". Every method and comparator was re-judged once,
and fitted artefacts were not refitted. This kept reference and mask changes from becoming tuning, and it is what makes every incident in
this file traceable.

**Evidence.**
- `docs/RULES.md @ d160337` — "Every crop is recorded, not the best."; `@ 625a991` — "The v0.1 numbers above stay on record."
- `docs/RULES.md @ a56bd42` — "Recorded here so it cannot be mistaken for post-hoc tuning"; `@ 7375777` — "All v1-era numbers above stay on record as run"
- `docs/RULES.md @ 55cd58e` — "Fitted artefacts (v1b template, v2 setting, v3 weights, v5 net) are NOT refitted"

**Lesson.** Keep failed and superseded numbers in place. When the judge changes, re-judge every method once without refitting.

**Fix.** The practice was kept throughout the notebook.

<a id="lesson-68"></a>
### 68. Never round up, and keep full precision end to end

**What happened.** RULES.md and commit messages rounded half-up (v8 0.8395000189894518 became "0.840") and rounded ranges outward (R1
0.717–0.865 as "0.72–0.87"; R2 0.797–0.887 as "0.80–0.89"); the release drafts repeated them. The "unrounded" release means at
5ba7764 averaged per-crop stroke and local values stored at 4 decimals, so v8's stroke mean was 0.9167714… in one release file and
0.9167664… in another.

**Evidence.**
- `results/stats_evaluation7.json @ 5ba7764` — "mean": 0.8395000189894518 and "mean": 0.9167714285714287; commit message of bc24d20 — "pixel 0.840, stroke 0.917"
- `docs/RULES.md @ e8d6a6c` — "at 0.72–0.87"; `@ 9de8704` — "on unread papyrus at 0.80–0.89"; `docs/RESULTS.md @ e455383` — "0.72–0.87 (v8) and 0.80–0.89 (E)"
- `results/per_crop_evaluation7.csv @ 5ba7764` — "20231005123336:held1,0.8828924602993242,0.9394,0.9293"; `README.md @ e455383` — "stroke_auc": 0.9393775777052081
- `results/d3_decomposition.json @ bde701a` — 0.916766433285967

**Lesson.** Never round up: keep full precision end to end, truncate only for display, and print ranges from exact endpoints.

**Fix.** Release policy and `inkeval.stats.trunc` ("never rounds a number up in magnitude", 5ba7764; float-safe since 0aeb4b2); outward
ranges corrected in the release text. Fixed in this release for the released methods: `scripts/release_stats.py` takes stroke AUC and L
at full precision from `results/toolkit_vs_records.json` for the 65 method-crop pairs the toolkit recomputed (E, v8, GP-R1, v7 and the
team comparator on all 13 crops, 0aeb4b2), so v8's stroke mean is 0.916766433285967 in both `results/stats_evaluation7.json` and
`results/d3_decomposition.json`. The other methods' per-crop stroke and L (v6b, v6c, v3, v2, v1b, v0.1b) are still the research
scripts' 4-decimal, half-up records: **Open — not fixed** (partly).

<a id="lesson-69"></a>
### 69. Label every number with its quantity, crop set and n

**What happened.** The interim report put text1-only thickness (0.498) as 0.50 under "5 text crops". RULES.md listed "stroke half-width
median 0.161 mm" under "Measured on the 7 evaluation crops", but it comes from the segment-1 TRAIN crop. The release README draft gave
"0.478 (MEASURED)" beside 7-crop means; it is one TRAIN crop under the old mask.

**Evidence.**
- `archive/docs/report_2026-09-17.md @ a6dfd42` (then `docs/report_2026-09-17.md`) — "w028 vs team model (mean AUC, 5 text crops)"; "| thickness alone | topography | 0.50 |"
- `docs/RULES.md @ 20c16db` — "Thickness t: AUC 0.498 (nothing)." (text1 only)
- `docs/RULES.md @ 3c19230` — "Measured on the 7 evaluation crops:"; "stroke half-width median 0.161 mm, max 0.618 mm"; source key in `stats/explore/au_step1_geom.json @ cdc291e` — "20231005123336/train"
- `README.md @ e455383` — "0.478 (MEASURED)"; `docs/RULES.md @ 4f9ef66` — "thickness AUC 0.478" (TRAIN crop)

**Lesson.** Attach quantity, crop set and n to every number wherever it is copied.

**Fix.** The release README scopes the thickness value (`README.md @ 043ba8d` — "0.478 (one crop, the segment-1 TRAIN crop)"), and
`docs/METHODS.md` §8 now describes E's "0.161 mm" as the TRAIN crop's median distance from a text pixel to the label edge (0.1606 mm,
rounded up by the notebook). Fixed in this release.

<a id="lesson-70"></a>
### 70. Retire stale documents; regenerate derived records with their generator

**What happened.** METHOD.md was never updated after its first commit (original grain rule; retired changes "none yet"); STATE.md, last
edited before v8, still says "No submission ready"; LEDGER.md held only a header. The pre-registration generator gained an N1 row
(e455383), but its committed output was not regenerated: no N1 row, and D3 still "pending" though its result is committed.

**Evidence.**
- `archive/docs/METHOD_v0.2_papyrus_subtraction.md @ a56bd42` (then `METHOD.md`) — "component ≤ (0.1 mm)² → dilated 0.3 mm"; "- none yet"
- `archive/docs/STATE_2026-09-17.md @ 602b6b6` (then `STATE.md`) — "**No submission ready. No method of ours reads verified text at the declared bar.**"
- `LEDGER.md @ d160337` — "scroll | surface | method-version | face | verdict | date | notes" (deleted in b370331)
- `scripts/check_preregistration.py @ e455383` — '("N1 reading-run null (post-hoc)"'; `results/preregistration_order.json @ bde701a` (its only commit before the regeneration in 34cc327) — "D3 smoothing-vs-ensembling (post-hoc)", order "pending"

**Lesson.** Keep one living record, mark the rest historical, and regenerate derived records in the generator's commit.

**Fix.** Old documents archived and LEDGER.md deleted (b370331); METHODS and REPRODUCE drafted (bde701a);
`results/preregistration_order.json` regenerated with N1 and D3 (34cc327).

<a id="lesson-71"></a>
### 71. Give every experiment, variant and crop a unique name

**What happened.** Several names are ambiguous:
- "D2" names both the per-depth result of 2026-09-17 and the distillation diagnostic of 2026-09-18.
- "v1 depth template" means v1b in STATE.md (0.651 / 0.681) but v1a in the interim report (0.649 / 0.686).
- Training and validation crops are named held1–held11.

**Evidence.**
- `docs/RULES.md @ 6d1c078` — "### D2 result (2026-09-17 21:55 UTC)"; `@ 0e86155` — "## Diagnostic D2 (declared 2026-09-18 16:05 UTC"
- `archive/docs/STATE_2026-09-17.md @ a92863a` (then `STATE.md`) — "v1 depth template", "0.651 / 0.681"; `archive/docs/report_2026-09-17.md @ a6dfd42` (then `docs/report_2026-09-17.md`) — "| v1 depth template (from w028, no Scroll-1 fit) | ink depth signature | — | 0.649 / 0.686 |"
- `stats/s1_crops_20231012184424.json @ 47febe8` — rule "all held-out"; same file `@ 0ce50ac` — "name": "held11"

**Lesson.** Give every experiment, variant and crop a unique name that states its role.

**Fix.** `docs/RESULTS.md @ e455383` uses "D2-distil" for the second D2. The crop names are unchanged. **Open — not fixed.**

<a id="lesson-72"></a>
### 72. Declare an ensemble before its members' results are known

**What happened.** E's members, equal weights and 0.08 mm smoothing were committed at 18:59:51Z, before v8's result (19:21:12Z) and
GP-R1's (21:47:06Z), and no weighted or re-smoothed variant was allowed afterwards. INFERENCE: so E's composition, weights and smoothing
involve no selection on the evaluation crops; it still carries the bias of the sequence as a whole ([13](#lesson-13)).

**Evidence.**
- `docs/RULES.md @ 5915848` — "## Method E (declared 2026-09-18 19:00 UTC, BEFORE v8's or GP-R1's results are known)"; "no weighted or re-smoothed variant will be introduced afterwards to rescue it"
- commit times: 5915848 18:59:51Z, bc24d20 19:21:12Z, c406bf7 21:47:06Z

**Lesson.** Declare an ensemble (its members, weights and post-processing) before any member's result is known, and forbid rescue
variants.

**Fix.** A practice to keep.

<a id="lesson-73"></a>
### 73. Commit anti-fabrication rules before looking at unread papyrus

**What happened.** Before any output on unread papyrus was seen, R1 declared its rules:
- windows are selected mechanically;
- nothing is transcribed and no readings are proposed;
- an illegible result is reported as illegible;
- the team map is shown only as a second opinion.

R2 reused the identical windows, so there was "no opportunity to shop". Both runs report zero characters.

**Evidence.**
- `docs/RULES.md @ a31bbc1` — "I will NOT transcribe characters, propose readings, or name letters"; "No plausible-looking text will be produced under any circumstances"
- `docs/RULES.md @ c74372d` — "so there is no opportunity to shop for a better-looking region"; `@ 9de8704` — "Nothing is transcribed."

**Lesson.** Commit the anti-fabrication rules and the window choices before seeing any output on unread papyrus.

**Fix.** A practice to keep.

<a id="lesson-74"></a>
### 74. Do not announce results, files or checks before they exist

**What happened.** The drafts at e455383 announced work not in the repository: C1 "on six untouched labelled windows" with no committed
result; an "independently confirmed" study; "every published number … exactly", where three tests check one crop and skip without data;
and links to files then absent (`results/FACTS.md`, `results/stats_confirmation.json`, `results/logs/c1.log`, `docs/SUPERSEDED_CLAIMS.md`,
three figures).

**Evidence.**
- `CHANGELOG.md @ e455383` — "**Confirmation test C1** on six untouched labelled windows"
- `README.md @ e455383` — "pre-registered, independently confirmed"; "every published number of this study **exactly**"; `SUBMISSION.md @ e455383` — "independently confirmed"
- `docs/RESULTS.md @ e455383` — "results/FACTS.md"; "results/stats_confirmation.json"; "`results/logs/c1.log`"; `results/logs/README.md @ bde701a` — lists "`c1.log`"
- `git cat-file -e d2564a7:<path>` fails for each of the files listed above (checked)
- `docs/REPRODUCE.md @ cc5c843` — "| 4 | every published number, from public data, with released weights |"; "## Level 4 — every published number from public data"; "Only E, v8, GP-R1, v7 and the team comparator are regenerated by `run_judge_crops.sh`."

**Lesson.** Generate every claim and link from committed outputs; fail the build on a dangling link.

**Fix.** Overclaims removed from README, SUBMISSION and CHANGELOG (no "independently confirmed" in the release); linked results and figures
committed (0e040c1, 8362c4b); ⟦TOOLKIT_SCOPE⟧ filled (a16a6a2); this file and `docs/SUPERSEDED_CLAIMS.md` committed (cc5c843).
Fixed in this release (0db607f): `SUBMISSION.md` states the counts (84 lessons, 76 retracted or corrected claims) in place of
⟦N_LESSONS⟧ and ⟦N_CLAIMS⟧, and `docs/REPRODUCE.md` Level 4 no longer says "every published number": it is scoped to "the released
methods' pixel AUCs from public data, and the statistics". No build step fails on a dangling link or on a claim without a committed
source: **Open — not fixed** (partly).

## Engineering and operations

<a id="lesson-75"></a>
### 75. Make main the release branch, and release early

**What happened.** Judges see the default branch. At cc5c843, `main` and `origin/main` are 68454e8, the initial LICENSE-only commit, and
all work sits 126 commits ahead on a `claude/` branch. Nothing was committed between 2026-09-19T00:57:43Z and 2026-10-15T04:45:30Z, and
DATA_NOTICE says the repository is private.

**Evidence.**
- `git rev-parse main origin/main` — 68454e8 (both); `git show --stat 68454e8` — "Initial commit", "LICENSE | 21"
- `git rev-list --count main..cc5c843` — 126; commit times: 9de8704 2026-09-19T00:57:43Z, 46a4bfc 2026-10-15T04:45:30Z
- `DATA_NOTICE.md @ 412b7c7` — "The repository is currently **private**"

**Lesson.** Release early on the default branch, and make the public state match what the documents describe.

**Fix.** Not done in the release working tree: `main` is still 68454e8, and `DATA_NOTICE.md` and `SUBMISSION.md` state that the
repository is private. Fast-forwarding `main` to the release branch and making the repository public are the owner's steps before
submission. **Open — not fixed.**

<a id="lesson-76"></a>
### 76. Test the release from a fresh clone

**What happened.** The unanchored `data/` rule in `.gitignore` kept the bundled example `inkeval/data/example_scroll1.npz` out of git; 10
of 11 tracked `scripts/*.sh` drivers ran `cd /home/user/megara` (`git grep` at b370331); the README at d2564a7 linked figures that
were not in the repository.

**Evidence.**
- `.gitignore @ d160337` — "data/"; `.gitignore @ e455383` — "/data/"; `git show --stat e455383` — "inkeval/data/example_scroll1.npz"
- `scripts/run_c1.sh @ cc5c843` — "cd /home/user/megara"; `docs/REPRODUCE.md @ cc5c843` — "`/home/user/megara` (the release machine's checkout path)"
- `README.md @ d2564a7` — "docs/figures/fig2_reading_median_worst.png" (absent at d2564a7, as are `fig3_unread_e_vs_team.png` and `figS_all_crops.png`)
- commit message of d2564a7 — "quick-start timings from a fresh clone"

**Lesson.** Test every release from a fresh clone on a clean machine, as a release step.

**Fix.** Example tracked (e455383); the linked figures added (8362c4b); absolute paths removed in e455383 except `scripts/run_c1.sh`,
which kept it until after C1. Fixed in this release (0db607f): `scripts/run_c1.sh` now runs `cd "$(dirname "$0")/.."`, and no tracked
file under `scripts/`, `inkeval/` or `tests/` names the release machine's checkout path. Archived scripts under `archive/scripts/` keep
the path (disclosed in `docs/REPRODUCE.md`).

<a id="lesson-77"></a>
### 77. Commit the driver, inputs, code and output of every reported number

**What happened.** R1/R2 windows and renders were git-ignored and their agreement AUCs "computed by inline code that was not committed";
commit 3f8295d mentions "R1 renders" but holds two stats JSONs. D3's like-for-like interval [−0.019, 0.033] was quoted in RULES.md
(bde701a) but computed by no committed code until 043ba8d.

**Evidence.**
- `.gitignore @ d160337` — "review_sheets/**/*.png"; `docs/RESULTS.md @ e455383` — "were computed by inline code that was not committed"
- `git show --stat 3f8295d` — "Ensemble E judging artefacts and R1 renders", "2 files changed"
- `docs/RULES.md @ bde701a` — "GP-R1 − v8 = +0.009 [−0.019, 0.033] (5/7)"; `scripts/d3_decompose.py @ bde701a` — 'pairs = [("e", "v8"), ("v8_s", "v8"), ("gpr1_s", "gpr1"), ("mean_nos", "v8"), ("e", "mean_nos"), ("e", "v8_s")]'; `scripts/d3_decompose.py @ 043ba8d` — '("gpr1_s", "v8_s")'

**Lesson.** Commit the driver, input identities, computing code and output of every reported number with the result.

**Fix.** Window records, renders (b370331), logs and the N1 script (bde701a) are committed; N1 recomputes R1 agreement (v8 0.716–0.864,
truncated) approximately; the D3 pair is committed (043ba8d). The original R1/R2 computation is lost: disclosed as a limitation.

<a id="lesson-78"></a>
### 78. Budget disk explicitly, and record where it changed the science

**What happened.** The machine had ~30–37 GB of disk, and each raw crop took 4.3 GB. Disk limits caused four losses:
- v0.3f was dropped.
- The w028 repair was stopped.
- The w028 base maps were deleted, which left v0.3p-hp partial.
- The full-resolution stacks that GP-R2 needed were deleted.

**Evidence.**
- `archive/docs/STATE_2026-09-17.md @ d160337` (then `STATE.md`) — "~30 GB writable disk"; `@ a92863a` — "~37 GB usable disk"
- `docs/RULES.md @ 038aef0` — "w028 v0.3f is dropped"; `@ d07ddf5` — "The w028 per-crop base maps (except text1) are deleted"
- `docs/RULES.md @ ba2310f` — "run ended when the w028 base maps were deleted for disk"; `@ 3f88fdf` — "the full-resolution stacks were deleted for disk"

**Lesson.** Budget disk before planning, record every decision that disk forced as a limitation, and keep a hashed input manifest so that
deleted inputs can be fetched again.

**Fix.** The decisions are recorded in RULES.md. There is an input manifest with SHA-256 sums (412b7c7) and a fetcher,
`scripts/fetch_inputs.py` (bde701a).

<a id="lesson-79"></a>
### 79. Use constant-memory formulations on small machines

**What happened.** The machine had 15 GB of RAM:
- One 8337² chart peaked at 12.3 GB.
- The residual stage was killed for running out of memory twice.
- One residual took 28 CPU-minutes.
- The first v7 ridge fit died at 8.9 GB resident.

Disc dilation (equal to the distance-transform rule, "== distance transform <= r"), freed intermediates and per-crop Gram accumulation
(263 MB) are exact. The triple box filter (96fb2f4) only approximates the Gaussian: three box passes are not a Gaussian, and
their variance matches only approximately because the width L is rounded to an odd integer.

**Evidence.**
- `CHANGELOG.md @ f882ebd` — "28-CPU-minute residual"; "two out-of-memory kills (15 GB RAM"; "12.3 GB"
- `scripts/residual.py @ f882ebd` — "binary dilation by a disc of radius r px (== distance transform <= r), low memory."; `@ 96fb2f4` — "for sigma >= 8 px three box passes of width L = sqrt(4 sigma^2 + 1) (same variance, O(1)/px)"; "L = int(round(np.sqrt(4 * sigma * sigma + 1))) | 1"
- `docs/RULES.md @ 4c630c4` — "killed by the OOM reaper (8.9 GB resident)"; "(263 MB measured)"

**Lesson.** On small machines, prefer exact formulations with constant memory and O(1) cost per pixel, record that they are exact, and
label approximations as approximations.

**Fix.** Fixed in f882ebd, 96fb2f4 and 4c630c4.

<a id="lesson-80"></a>
### 80. Assume restarts and shared cores: chain jobs explicitly, kill child processes

**What happened.** Killing a driver shell left its Python child running, so three v7 fits once shared a 4-core box. The D2 and GP-R1
drivers waited on the same `V8_JUDGED` sentinel and would have started together had D2 not been deferred. Container restarts killed
watcher loops but not `nohup`/`setsid` jobs, and logs lived in `/tmp`.

**Evidence.**
- `archive/docs/reproduce_2026-09-18.md @ 1c8f45e` (then `docs/reproduce.md`) — "Killing a driver shell does not kill the Python child it launched."; "Three v7 fits once ran concurrently on a 4-core box"
- `archive/scripts/run_d2.sh @ 4a4af4d` (then `scripts/run_d2.sh`) and `scripts/run_gpr1.sh @ 9d4ae3f` — 'until grep -q -E "V8_JUDGED|Traceback|Error" /tmp/v8.log'
- `archive/docs/STATE_2026-09-17.md @ a92863a` (then `STATE.md`) — "Container restarts kill watchers, not nohup/setsid jobs."; `results/logs/README.md @ bde701a` — "copied verbatim from the machine they ran on (`/tmp/*.log`"

**Lesson.** Chain each job on its own predecessor's sentinel, kill child PIDs, list survivors before relaunching, and keep logs out of
temporary storage.

**Fix.** Process check documented (1c8f45e); single chain driver (8fa65b7); logs archived in `results/logs/` (bde701a). No lock-file
guard: **Open — not fixed**.

<a id="lesson-81"></a>
### 81. Smoke-test each script on a tiny crop before queueing it

**What happened.** Queued jobs failed on an off-by-one argument slice, uncropped blocks, NaN depths, and a validation band whose size was
not a multiple of 4. Each needed a fix, and one forced the master chain to restart.

**Evidence.**
- commit messages: 329e796 "Fix D1 script argument slice and block cropping"; 5f9b96b "D1: sanitise NaN depths before sampling"; 09a30f1 "validation band cropped to a multiple of 4; master chain restarted from v5"

**Lesson.** Smoke-test every script on a tiny crop, which takes seconds, before queueing it behind long jobs.

**Fix.** Each failure got a point fix. The toolkit has a test suite (`tests/`, 5ba7764), but the research scripts have no smoke-test
harness. **Open — not fixed.**

<a id="lesson-82"></a>
### 82. Deduplicate only identical artefacts, and make commit messages match their diffs

**What happened.** To save disk, `s_top_<tag>.npy` was replaced by a symlink to `s_bot_<tag>.npy` for v2, v3, v5, v0.3p and the team
model. For these tags the judged top and bottom values are identical, so no number changed (INFERENCE: one map per method). But nothing
documents the aliasing. Separately, commit 499e037 says "deduplicate score maps to symlinks" while its diff changes only crop counts, and
3f8295d mentions renders it does not contain ([77](#lesson-77)).

**Evidence.**
- `scripts/run_s1_seg.sh @ ccad107` — 'ln -s s_bot_$t.npy "$f"'
- `stats/s1_gate_20231005123336.json @ fe9424c` — held1 v2 top and bottom auc_px both 0.6385082434675391
- commit message of 499e037 — "deduplicate score maps to symlinks"; `git show --stat 499e037` — "scripts/run_v8.sh | 13" (no symlink code)

**Lesson.** Deduplicate only byte-identical artefacts, and record each alias. Make every commit message describe its diff.

**Fix.** **Open — not fixed** (the aliases are undocumented in METHODS).

<a id="lesson-83"></a>
### 83. Keep the judge's code unambiguous

**What happened.** In the veto fix, the judge's threshold argument changed from an absolute team score to a quantile without a rename, so
an old command passing 0.10 now means the 10th percentile. The judge also computes the minimum letter area as (0.5/pitch·1000)², 0.25 mm²
despite its "0.5 mm^2" comment, then overwrites it with the correct value; deleting that line would silently halve the threshold. Both are
unchanged in the release (`scripts/s1_judge.py` last changed in 96ab51d).

**Evidence.**
- `scripts/s1_judge.py @ 96ab51d` — "# thr is now a QUANTILE (RULES.md, incident 3)"
- `scripts/s1_judge.py @ acda042` — "min_px = (0.5 / pitch * 1000) ** 2 * 1  # 0.5 mm^2"; "min_px = 0.5e6 / (pitch * pitch)"
- `scripts/s1_judge.py @ cc5c843` — all three quoted lines present (lines 28, 39, 40)

**Lesson.** Never change an argument's meaning in place (add a new name), and delete dead or wrong lines from the judge.

**Fix.** **Open — not fixed** (the letter test is retired; `inkeval` has none).

<a id="lesson-84"></a>
### 84. Record mid-run implementation changes per crop

**What happened.** A speed approximation entered `s1_v2.py` partway through a run: Gaussians with σ > 100 px are computed on an 8× pooled
grid. As a result, held1 and held2 were computed exactly and the later crops approximately. The claimed error bound, "error < 1e-3",
appears only in a docstring and was never measured in the record.

**Evidence.**
- `scripts/s1_v2.py @ b0bb88b` — "for σ > 100 px computed on an 8x mean-pooled grid"; "error < 1e-3"; commit message — "held1/held2 computed exactly"
- commit message of 658c5e8 — "v3: pooled-grid Gaussians"

**Lesson.** Record any implementation change made mid-run, per crop, and measure an approximation's error before relying on it.

**Fix.** Docstring note only. **Open — not fixed.**

---

## Lessons that are open (not fixed)

Entries whose fix is open, in whole or in part. "Partly" means part of the problem is fixed, and the entry says which part is not.

| # | Lesson | What remains open |
|---|---|---|
| [2](#lesson-2) | Comparator placed the reference | no alignment independent of the team model |
| [9](#lesson-9) | Negative controls | no valid blank control for unread papyrus |
| [14](#lesson-14) | Confirmation analysis code committed late | cannot be repaired after the fact; disclosed in RESULTS §5 and the notebook |
| [16](#lesson-16) | Reading windows next to read text | no contrast-based window rule |
| [17](#lesson-17) | Detection is not legibility | no legibility measure |
| [18](#lesson-18) | Teacher-model paths | partly: no no-veto control for v7 |
| [23](#lesson-23) | One change at a time | partly: no single-factor control for v8 |
| [24](#lesson-24) | Identical post-processing | partly: GP-R1 not re-judged with bilinear upsampling |
| [29](#lesson-29) | Reference-noise bound | the split is not reproducible from committed files |
| [30](#lesson-30) | Grid edges | no extended grids |
| [31](#lesson-31) | Assert both classes | partly: no assertion in the training code |
| [32](#lesson-32) | Unconditional deletion | partly: the archived driver keeps the rm line, with no warning |
| [35](#lesson-35) | Never overwrite a cited file | partly: the per-crop judge records are still only in the git-ignored `data/` |
| [36](#lesson-36) | Reconcile repeated measurements | class counts and stroke width unreconciled |
| [37](#lesson-37) | Cached class maps | partly: the research judge still caches by existence (disclosed) |
| [38](#lesson-38) | Reference map before thresholding | class sizes and the JPEG floor |
| [40](#lesson-40) | Identifiers before planning | the 20231012184423 identifier slip remains in RULES.md (append-only) |
| [41](#lesson-41) | Verification coverage | partly: CT chunks unhashed |
| [43](#lesson-43) | Not surface-local | sheet middle unsampled by the learned models (INFERENCE) |
| [50](#lesson-50) | 9 µm stack depth | 9 µm route untested |
| [57](#lesson-57) | Checkpoint selection | partly: a single validation crop |
| [59](#lesson-59) | Cross-segment gap | partly: no third segment |
| [62](#lesson-62) | Calibrated renders | not implemented |
| [68](#lesson-68) | Never round up | partly: per-crop stroke and L of v6b, v6c, v3, v2, v1b and v0.1b still 4-decimal, half-up records |
| [71](#lesson-71) | Unique names | partly: training and validation crops still named held* |
| [74](#lesson-74) | Announcing before existence | partly: no build step fails on a dangling link or an unsourced claim |
| [75](#lesson-75) | Release branch | `main` still the initial commit and the repository private (owner's steps before submission) |
| [80](#lesson-80) | Job control | partly: no lock-file guard |
| [81](#lesson-81) | Smoke tests | partly: no harness for the research scripts |
| [82](#lesson-82) | Aliases and commit messages | undocumented aliases |
| [83](#lesson-83) | Judge code hygiene | in-place argument change; dead line |
| [84](#lesson-84) | Mid-run changes | error bound unmeasured |
