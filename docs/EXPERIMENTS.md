# The Dominion experiment map

What each experiment of the Dominion programme asked, how it was tested, and what came of it, failures and nulls
included. Every number below comes from the cited file of the private working record (the few marked "counted at survey" or
"computed at survey" were counted or recomputed from it during the survey); the sources cannot be
opened from this public release. The summary table is also in the [README](../README.md#the-experiment-map), and the
branches are listed in [BRANCH_INDEX.md](../BRANCH_INDEX.md).

<!-- BEGIN:experiments_full -->
Survey date 2026-10-15. 175 experiments in 6 families: 103 published here, 72 withheld and only counted. Generated from [`results/experiments/experiment_map.json`](../results/experiments/experiment_map.json) by `scripts/write_tables.py`.

Derived by a read-only survey of the private Dominion record (7 family surveyors, an evidence verifier that re-opened every cited source, and a confidentiality auditor). Numbers are copied from the cited files (a few marked "counted at survey" or "computed at survey" were counted or recomputed from them); sources are in the private working history and cannot be opened from the public release. PHerc. Paris 4 is treated as not officially read, so every experiment on it is withheld whatever it showed, and only counted. Revised after the pre-release reviews of 2026-10-15 (duplicate listings removed, wording and sources corrected).

**Verdicts**

- **PASSED**: met its stated bars (declared before its data for pre-registered tests; for checks and infrastructure, its acceptance check).
- **FAILED**: missed its stated bars (declared before its data for pre-registered tests; for checks and infrastructure, its acceptance check).
- **NULL**: ran as declared and found nothing.
- **INCONCLUSIVE**: ran, but the result cannot decide the question (for example, a detector too insensitive).
- **VOID**: invalidated under its own declared clause (for example, a metric mismatch or a freshness breach).
- **STOPPED**: stood down or stopped before its verdict step.
- **TOOL**: built a tool or ran infrastructure; there is no hypothesis to pass or fail.
- **UNKNOWN**: the outcome is not in the record.

**Families**

| family | period | experiments | outcomes |
|---|---|---:|---|
| [Reading and its calibration](#reading-and-its-calibration) | 24 Sep to 30 Sep | 19 | 3 passed · 5 failed · 4 inconclusive · 2 void · 2 stopped · 3 tool |
| [Fine-tuning and own ink models](#fine-tuning-and-own-ink-models) | 24 Sep to 10 Oct | 15 | 4 failed · 1 inconclusive · 4 stopped · 6 tool |
| [PHerc. Paris 4 (withheld)](#pherc-paris-4-withheld) | - | 72 | 72 withheld |
| [First Letters push](#first-letters-push) | 25 Sep to 14 Oct | 23 | 1 passed · 6 failed · 6 null · 1 inconclusive · 1 void · 5 stopped · 3 tool |
| [Geometry: registration, handedness, flattening, umbilicus, unrolling, spiral fits](#geometry-registration-handedness-flattening-umbilicus-unrolling-spiral-fits) | 25 Sep to 14 Oct | 27 | 4 passed · 15 failed · 1 null · 3 inconclusive · 1 void · 1 stopped · 1 tool · 1 unknown |
| [Tools, infrastructure and operations](#tools-infrastructure-and-operations) | 24 Sep to 10 Oct | 19 | 3 passed · 3 failed · 2 inconclusive · 1 stopped · 10 tool |

72 experiments are withheld and only counted: every experiment on PHerc. Paris 4, whatever it showed. The scroll is treated here as not officially read, so its per-experiment results are not published; withholding says nothing about their outcome.

## Reading and its calibration

24 Sep to 30 Sep 2026 · 19 experiments · 3 passed · 5 failed · 4 inconclusive · 2 void · 2 stopped · 3 tool

This family asked whether blind AI readers can read ink maps of carbonized papyrus, and whether their reads can be trusted. The 9 um base-map chain passed its fidelity gate only on the fourth declared run (one VOID for a metric mismatch, one FAIL with mirror test-time augmentation, one VOID for a freshness breach). Without help, readers named almost nothing on reference maps. With a font key sheet, the readers agreed beyond a shuffle null, and the pre-specified arm replicated once on fresh papyrus. Even so, they never marked an agreed letter as firm, and in three handedness tests they could not tell mirrored maps from normal ones. On a sealed held-out benchmark, the calibrated reader recovered 80 % of the sealed letters from the organizers' 2.4 um reference maps but named nothing at all in the project's own 9 um base or raw maps, so D1 failed. The family also produced tools (the D1 sealed benchmark, a geometric handedness rule, a planted-fault pre-read gate), plus two programmes that were built but never run; the local and remote blind-reader harnesses are listed under Tools, infrastructure and operations.

### C3 gate, run 1 (9 um base chain fidelity, as first declared)

**Verdict: VOID**

**Question.** Does our 9 um render plus the official base ink model, with mirror test-time augmentation, reproduce the organizer surface volume and the organizer pixel AUC bars on labelled papyrus?

**Method.** Official renderer on an organizer mesh of a base-trained segment; pixel AUC of the base ink map against organizer human labels in both depth orders; bars and a VOID clause declared before any data.

**Result.** The render reproduced the organizer surface volume almost exactly (pooled Pearson 0.9999990). The declared AUC definition did not match the one the bars were set on: under it, even the organizers' own map scored 0.9807 against a 0.987 bar. The run was voided under its own clause and re-declared once.

| number | meaning | source |
|---|---|---|
| 0.9999990 | pooled Pearson of our render vs the organizer surface volume (bar >= 0.999) | `RULES.md (entry C3-RUN1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.9807 / 0.4563 | the organizers' own surface volume scored under the AUC definition as declared; forward fails the 0.987 bar, which exposed the definition mismatch | `RULES.md (entry C3-RUN1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.99659 / 0.49633 | the same organizer map scored inside the supervision mask; this reproduces the archive reference 0.9966 / 0.4963 | `RULES.md (entry C3-RUN1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.9902/0.5658 | our base map with TTA, in-mask forward/reverse AUC (recorded, not used for a verdict) | `LEDGER.md (row C3 run 1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Reproduce the reference archive's own numbers under your metric before declaring bars. A bar copied from one metric definition and applied to another voids the test.

### C3-R1: base chain with mirror TTA on a fresh crop

**Verdict: FAILED**

**Question.** Under the corrected (supervision-mask) AUC definition, does the base chain with mirror test-time augmentation meet forward AUC >= 0.987 and reverse AUC < 0.60 on a code-chosen fresh crop?

**Method.** Same chain as run 1. The crop was chosen by hashed code before any map of it existed. AUC was computed inside the organizer supervision mask, both orders, and re-derived by a fresh auditor.

**Result.** Rendering fidelity was met, but with mirror test-time augmentation the forward AUC was 0.97795, below the 0.987 bar. An independent auditor reproduced the numbers exactly, and every 9 um read using that chain was blocked.

| number | meaning | source |
|---|---|---|
| 0.97795 | forward AUC with TTA inside the supervision mask (bar >= 0.987) | `LEDGER.md (row C3-R1); logs/c3/c3_r1_results.json sha256 1473c540...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.56648 | reverse-order AUC with TTA (bar < 0.60, met) | `LEDGER.md (row C3-R1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.99347 | forward AUC without TTA on the same crop (not a bar) | `RULES.md (entry C3-R1-VERDICT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| PASS | independent auditor re-derivation (all numbers re-derived with difference 0.0) | `logs/c3/audit_r1.json (field audit)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Test-time augmentation lowered pixel AUC here. Gate the exact chain you will read, not a component.

### C3-NT: no-TTA variant on the same segment

**Verdict: VOID**

**Question.** Does the base chain without TTA pass the same bars on a new crop of the same labelled segment?

**Method.** No-TTA base chain, code-picked crop, auditor freshness check against the compute ledger and all earlier maps.

**Result.** The numbers passed, but the auditor voided the run. A diagnostic map made during run 1 already covered the 'fresh' crop, and the declaration did not disclose it. The gate was re-declared once on a segment no project map had ever touched.

| number | meaning | source |
|---|---|---|
| fwd 0.99926, rev 0.56528 (not used) | re-derived AUCs that were not used for a verdict | `LEDGER.md (row C3-NT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| VOID | auditor verdict: a no-TTA map of the whole segment made during run 1 already covered the crop, so the crop was not fresh | `logs/c3/audit_nt.json (field audit)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Freshness has to be checked against every artifact ever computed, including whole-canvas diagnostics run for another purpose.

### C3-NT-R1: no-TTA base chain on a never-mapped segment

**Verdict: PASSED**

**Question.** Does the no-TTA base chain meet the C3 bars on a labelled segment that no project map had ever covered?

**Method.** Re-declaration once after the VOID. A code-chosen crop on a segment checked for prior maps, audited before the verdict.

**Result.** The no-TTA chain passed (forward AUC 0.99960, reverse 0.58558, the reverse margin only 0.014) and became the validated 9 um base-map chain. The segment was base-trained, so this shows fidelity only, never generalisation.

| number | meaning | source |
|---|---|---|
| 0.99960 | forward AUC inside the supervision mask (bar >= 0.987) | `LEDGER.md (row C3-NT-R1); logs/c3/c3_nt_r1_results.json sha256 9a430680...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.58558 | reverse-order AUC (bar < 0.60) | `LEDGER.md (row C3-NT-R1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.014 | margin of the reverse AUC below its bar | `RULES.md (entry C3-NT-R1-VERDICT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.9999989 | pooled render Pearson | `LEDGER.md (row C3-NT-R1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| PASS | auditor re-derivation and freshness check | `logs/c3/audit_nt_r1.json (field audit)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A fidelity gate on training papyrus validates the plumbing, not the model's ability on unseen text. The later D1 result bore this out.

### HANDED-1: reader handedness test (coverage-chosen windows)

**Verdict: INCONCLUSIVE**

**Question.** Can blind readers tell which of a pair of reference-map images is mirror-reversed, so that the reading orientation can be fixed?

**Method.** Pairs of an official reference map and its mirror image, sides randomised, 3 fresh readers, votes counted by hashed code.

**Result.** All 12 answers were 'unsure' and no letters were named, so the test was AMBIGUOUS. The windows had been chosen by map coverage alone and may have held no writing.

| number | meaning | source |
|---|---|---|
| A 0, B 0, no vote 12 | votes from 3 readers on 4 pairs (bar >= 10 of 12 for one state) | `RULES.md (entry HANDED-1); logs/handed/handed1_scorer_output.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A perception test needs material known to contain the thing perceived.

### HANDED-R2: reader handedness re-test (label-chosen windows)

**Verdict: INCONCLUSIVE**

**Question.** With windows chosen by human-labelled ink density, can readers pick the normally oriented image?

**Method.** As HANDED-1 on 2 x 2 cm windows chosen by code from human-label ink fraction; sealed-output readers.

**Result.** The decided votes leaned 7:1 toward one state, but the 10-of-12 bar was not met (AMBIGUOUS), so both mirror states stayed as separate reading arms.

| number | meaning | source |
|---|---|---|
| A 7, B 1, no vote (UNSURE) 4 | votes (bar >= 10 of 12) | `RULES.md (entry HANDED-R2); logs/handed/handed_r2_scorer_output.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 8, 10, 12 | letters named per reader in the side judged normal | `logs/handed/handed_r2_scorer_output.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A suggestive lean in a small vote is not a decision. The re-test showed the lean did not hold.

### HANDED-R3B: larger handedness re-test (8 fresh windows)

**Verdict: INCONCLUSIVE**

**Question.** With 8 fresh windows and 24 votes, do readers decide the mirror state at the 83 % threshold?

**Method.** 8 new label-chosen windows sharing no papyrus with earlier ones, 3 fresh sealed-output readers, 24 votes.

**Result.** AMBIGUOUS again: pooled across the two label-chosen rounds, decided votes were 12 vs 14, which is chance, although readers named 2-3 letters per window. The record reads this as evidence that the readers' letter namings were not reliable letter perception.

| number | meaning | source |
|---|---|---|
| A 5, B 13, no vote 6 | votes (bar >= 20 of 24) | `RULES.md (entry HANDED-R3B); logs/handed/handed_r3b_scorer_output.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| A 12 : B 14 | pooled decided votes across R2 and R3B | `RULES.md (entry HANDED-R3B)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 22, 20, 26 | letters named per reader in the side judged normal | `logs/handed/handed_r3b_scorer_output.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Mirror discrimination is a cheap test of whether reader letter claims reflect real shape perception; here it failed. The R3 declaration was voided before any data because its clearance rule left only one usable window.

### READ-CAL bank picker (RCPICK-1)

**Verdict: FAILED**

**Question.** Do enough clean known-text reference windows have at least 5 nameable letters for a fresh picker to build a reading-calibration bank?

**Method.** One fresh blind picker, reference maps only, numbers-only counts returned through the scorer.

**Result.** A sealed-output picker shown 33 half-scale reference windows of clean known-text papyrus named 0-4 letters per window and none firm, so no bank window qualified. The project recorded the standard reading bar as infeasible at that display.

| number | meaning | source |
|---|---|---|
| 0 windows qualify | windows meeting the >= 5 named letters rule out of 33 candidates | `RULES.md (entry RCPICK-1); logs/readcal/picker1_counts.json (selected: [])` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Firm namings: 0 in total | letters marked firm by the picker across all windows | `RULES.md (entry RCPICK-1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Do not assume reference ink maps are blind-legible at a given display scale; measure that first.

### READ-CAL PROBE-1: display and reader-model grid

**Verdict: FAILED**

**Question.** At which display scale and reader model do independent blind readers agree on letters in official reference maps beyond a between-reader shuffle null?

**Method.** 4 known-text windows, 3 fresh readers per arm, agreement = same identity within 150 px from >= 2 of 3 readers, identity-shuffle permutation p.

**Result.** Thirty-six readers across 3 displays, 2 models and 2 mirror states never agreed on more than 4 letters in a window. None of the agreement was firm and no window beat the shuffle null, so the record states that reference maps were not blind-legible at any tested display. An independent audit later reproduced every count.

| number | meaning | source |
|---|---|---|
| max 4 agreed per window, 0 agreed-firm, all shuffle p >= 0.107 | best per-window agreement over 12 arms (pass needed >= 5 agreed with p < 0.05) | `LEDGER.md (row READ-CAL PROBE-1); logs/readcal/probe1_results.json sha256 aaa9bc22...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| every value >= 0.117 | auditor correction of the minimum shuffle p | `RULES.md (entry AUDIT-PROBES)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| N2 all arms 0 [0] | agreed letters at native 2.4 um resolution | `RULES.md (entry PROBE1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 36 fresh readers | readers, all transcripts audited VALID | `RULES.md (entry PROBE1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Inter-reader agreement against a shuffle null is a usable legibility statistic, and here it showed reader namings were mostly idiosyncratic.

### READ-CAL PROBE-2: font key sheet (paired re-read)

**Verdict: INCONCLUSIVE**

**Question.** Does showing readers a font-rendered sheet of the alphabet first raise agreement to >= 5 letters in a window with shuffle p < 0.05?

**Method.** 12 fresh readers on the same 4 windows and images as PROBE-1, with the hashed key sheet shown first; the same scorer.

**Result.** With the key sheet, one of four arms met the declared condition in exactly one window (5 agreed, p = 0.031, no multiplicity correction, 0 firm). The windows were reused from PROBE-1 because fresh ones were unavailable, so by declaration nothing was lifted until a fresh-material replication.

| number | meaning | source |
|---|---|---|
| 5 agreed, p = 0.031 | the single arm-window cell that met the declared condition (exactly at the bar) | `RULES.md (entry PROBE2-RESULT); logs/readcal/probe2_results.json sha256 0e4b3fec...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Agreed-firm: 0 in every arm and window | firm agreement | `RULES.md (entry PROBE2-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| mirror A 15 : B 6 | summed agreement in the two mirror states (which state is correct was unknown) | `LEDGER.md (row READ-CAL PROBE-2)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Declaring in advance that a pass on reused material lifts nothing until it replicates kept a borderline single-cell result from being over-read.

### READ-CAL PROBE-3: fresh-material replication

**Verdict: PASSED**

**Question.** Does the one pre-specified PROBE-2 arm again reach >= 5 agreed letters in a window with shuffle p < 0.05 on fresh, never-viewed known-text papyrus?

**Method.** 12 fresh readers, 3 code-chosen fresh windows that nobody had viewed, one primary arm with no arm multiplicity, mirror check reported only, and a fresh auditor re-deriving every cell.

**Result.** The pre-specified arm replicated on fresh papyrus: 10 agreed letters in one window at the smallest attainable p (1/2001). This lifted the suspension of reading for that display and reader model only. Still, 0 agreed letters were firm in the primary arm (1 in one other arm), agreement came from one window per probe, and it was insensitive to mirroring, which fits shared perception of simple ink shapes better than reading.

| number | meaning | source |
|---|---|---|
| REPLICATED | primary verdict | `logs/readcal/probe3_results.json (field verdict) sha256 222976e3...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 10 | maximum agreed letters in one window, primary arm | `logs/readcal/probe3_results.json (max_agreed_in_window)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 1/2001 (0.0005, the smallest attainable) | identity-shuffle p in that window | `RULES.md (entry PROBE3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| opus 8 vs 9, fable 11 vs 9 | summed agreement, state A vs B; the declared prediction A > B was NOT MET | `RULES.md (entry PROBE3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| PROBE-1: PASS. PROBE-2: PASS. PROBE-3: PASS. | independent auditor re-derivation of all three probes (60/60 transcripts valid) | `RULES.md (entry AUDIT-PROBES); logs/readcal/audit_probe3.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Replication beats a single significant cell, but agreement beyond a shuffle null shows consistency, not correctness. A mirror-insensitive signal is a warning sign. Record verdicts only after the independent audit; here the audit was initially omitted and run afterwards.

### D1 sealed benchmark construction

**Verdict: TOOL**

**Question.** Can a blind picker and three blind sealers build a hash-committed letter seal from official reference maps of held-out text, with confirmed blank windows, before any project render exists?

**Method.** Fresh picker, 3 tool-less sealers, consensus = same identity within 150 px from >= 2 of 3, label-centroid positioning, age-encrypted seal whose sha256 was pushed first.

**Result.** Three sealed-output sealers produced a consensus seal of 20 letters (9 firm) over five held-out windows from the organizers' official reference maps. It was committed by hash before any project render of those windows existed, and two text-free blank windows were confirmed.

| number | meaning | source |
|---|---|---|
| Total 15 named, 3 firm | earlier picker check at the unoriented display before the key sheet existed | `RULES.md (entry JPICK-1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| S' = 20, firm 9 | consensus seal size after sealing with the frozen display (small-seal regime, p_max < 0.005 required) | `RULES.md (entry SEAL-J-D1); logs/d1/jseal_summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| both confirmed (rows N, 0 letters named) | blank windows confirmed by a fresh picker | `RULES.md (entry SEAL-J-D1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A seal made by readers measures what readers perceive, not ground truth. Recall against it is a consistency measure.

### D1 REF ladder (reference legibility calibration)

**Verdict: PASSED**

**Question.** Can the calibrated reader recover the sealed letters from the official 2.4 um reference maps, and how fast does that fall with blur (sigma_crit)?

**Method.** Reference maps blurred at 0, 0.15, 0.30 and 0.45 mm, 3 fresh readers per level, positive canary and blank per session, hashed scorer with 5000 permutations.

**Result.** Twelve fresh readers (3 per blur level) were used; at the unblurred level the summed mean recall was 16.0 of the 20 sealed letters (80 %, p = 1/5001), with 0 namings on blanks. Legibility fell smoothly with Gaussian blur, giving sigma_crit = 0.30 mm, so the benchmark was not void.

| number | meaning | source |
|---|---|---|
| 16.0 | summed mean C_all at R 250 px for the unblurred reference (VOID bar < 10 = 0.5 S') | `logs/d1/d1_ref_summary.json (REF0) sha256 7c3884a2...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 11.367133333333333 | summed mean C_net, unblurred reference | `logs/d1/d1_ref_summary.json (REF0)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 1/5001 | permutation p, unblurred reference | `logs/d1/d1_ref_summary.json (REF0 p_exact)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.3 | sigma_crit in mm (largest blur keeping >= 50 % of C_net) | `logs/d1/d1_ref_summary.json (sigma_crit_mm)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.0 | mean namings per reader on blank windows | `logs/d1/d1_ref_summary.json (blank_namings_mean)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Calibrate the reader on the exact display and benchmark before reading any model output, and express the reader's acuity as a blur tolerance that model maps must meet.

### D1 KTLB-3R: zero-shot reading of our 9 um base and raw maps

**Verdict: FAILED**

**Question.** Do our validated 9 um base-model maps or raw CT slab means make unseen letters blind-legible above chance on the sealed benchmark?

**Method.** Declared arms BASE, RAW and CHANCE in both mirror states. Text order chosen once from pixel AUC before any read, maps masked to valid render, flat uuid image names, max-T permutation scoring, and a 4-lens audit.

**Result.** Eighteen fresh calibrated readers named 0 letters on every benchmark window and blank in both base-map and raw-CT arms, so the decision FAILED (C_net 0, p_max 1). The base-arm and chance-arm readers named 5-10 letters each on a base-map canary of training papyrus (the raw-arm readers named nothing anywhere), and the base map detected ink at pixel AUC 0.73: the maps carried ink signal but did not resolve strokes on unseen text.

| number | meaning | source |
|---|---|---|
| 0 namings on all J windows and blanks (18 readers); C_net 0; p_max 1 | result over BASE, RAW and CHANCE arms in both mirror states | `LEDGER.md (row D1 KTLB-3R); logs/d1/d1_model_summary.json sha256 22b2a0fa...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0 of 180 J panels and 36 blank panels | panels with any letter named | `RULES.md (entry D1-VERDICT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.73332 | pooled base-map forward pixel AUC against organizer labels on the same windows (the map does carry ink signal) | `RULES.md (entry TEXT-ORDER-D1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| PASS 4/4 | multi-lens independent audit (re-derivation, timeline, harness, adversarial), 0 invalidating findings | `LEDGER.md (row D1 KTLB-3R); logs/d1/audit_d1.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Pixel AUC near 0.73 is far from letter legibility. The binding constraint was the 9 um map, not the reader, because the same reader read 2.4 um references.

### Geometric handedness rule (sib-handed)

**Verdict: TOOL**

**Question.** Can the reading orientation (mirror state) of a rendered segment be decided from mesh geometry and scan metadata alone, without readers?

**Method.** Synthetic spiral scrolls with planted glyphs in proper and reflected frames, then real meshes, metadata and CT-mask centroids only. No image or ink map was viewed.

**Result.** A rule based on mesh chirality times metadata frame parity reads planted synthetic glyphs correctly in 32/32 cases and mirrors them in 32/32 wrong-sign controls. It is consistent with all organizer affines and with the known-text scroll's winding sense, and it predicted that the orientation shown in the reader tests was the legible one, although those readers had voted at chance. It was packaged as an open tool and proposed as a declaration, but was not adopted as one in the record.

| number | meaning | source |
|---|---|---|
| 32 | planted-glyph synthetic cases read unmirrored by the rule (of n_rule 32; minimum margin 0.2619) | `logs/sib/handed/handed_summary.json (synthetic.rule_unmirrored)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| 32 | wrong-sign controls that came out mirrored (of 32) | `logs/sib/handed/handed_summary.json (synthetic.wrong_sign_mirrored)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| 114/114 | organizer inter-volume affines whose determinant sign matches the metadata handedness flag | `logs/sib/handed/REPORT.md (section 5.1)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| 36/36 consistent | known-text scroll meshes whose winding sense agrees with the organizer top-to-bottom flag | `logs/sib/handed/REPORT.md (section 5.2)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |

**Lesson.** Settle orientation from geometry and metadata. Asking LLM readers to judge mirror state was not a reliable instrument.

### Second sealed benchmark preparation (KTLB-4P, sib-handed)

**Verdict: STOPPED**

**Question.** Can a second known-text sealed reading benchmark be prepared on another scroll fragment (registration, window certification, blanks, orientation)?

**Method.** Numbers-only builder work: CT patch registration with held-out patches frozen before reading, window certification and orientation sources.

**Result.** Cross-resolution registration failed its first pre-registered held-out test and passed a second, newly pre-registered attempt. The fragment offered no blank window and an unsettled mirror state. The benchmark was never sealed or read.

| number | meaning | source |
|---|---|---|
| 0.8343105717640731 | held-out median correlation, attempt 1 (affine registration), verdict FAIL (bar 0.85) | `logs/sib/ktlb4p-prep/ktlb4p_summary.json (registration.attempt1)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| 0.9291141373068948 | held-out median correlation, pre-registered attempt 2 (affine + RBF field), verdict PASS | `logs/sib/ktlb4p-prep/ktlb4p_summary.json (registration.attempt2)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| 0 | blank-window candidates found (bar < 1 % reference ink) | `logs/sib/ktlb4p-prep/ktlb4p_summary.json (windows.blank_candidates)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| FLAG: sources disagree where both valid; read both mirror states | geometric orientation decision | `logs/sib/ktlb4p-prep/ktlb4p_summary.json (handedness.decision)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |

**Lesson.** A second benchmark needs blanks and a settled orientation, not just registered text windows. Check those blockers early.

### Tribunal: planted-fault pre-read gate (sib-tribunal)

**Verdict: TOOL**

**Question.** Can code catch render faults (offset, swapped depth, mirror, off-by-one slice, re-trace by a training segment, wrong voxel size) before any reader sees an image, without false alarms?

**Method.** Independent reference render of the declared window compared against the delivered stack; one content check per fault type; pre-registered real-data calibration on non-eligible renders.

**Result.** The gate caught every planted fault by its own check, on synthetic worlds and on real 9 um CT renders, with no clean false alarms. It found that the declared same-papyrus rule missed most true re-traces at the official mesh step, and the project adopted a corrected fail-closed rule. Thresholds stayed proposed, not declared, and at 2.4 um the clean margins were too thin (minimum ratio 1.147, goal 3).

| number | meaning | source |
|---|---|---|
| 720/720 faults caught by their own check (100 %) and 0/120 clean false alarms | synthetic fault suites (3 texture/noise settings) | `logs/sib/tribunal/REPORT.md (Round 1, Measured results); logs/sib/tribunal/faultsuite.json` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 4 | re-traces caught by the literal nearest-vertex same-papyrus rule out of 200 (surface form: 200) | `logs/sib/tribunal/faultsuite.json (retrace_at_20vox.caught_by_literal_vertex_rule_alone)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 12 | clean real 9 um CT windows passing under current thresholds (each of 5 real planted fault types caught 12/12) | `logs/sib/tribunal/real_trib1.json (clean.passed_current)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 0 | clean real windows passing under the pre-registered threshold rule (it rounded to 1.0); the working threshold was post hoc | `logs/sib/tribunal/real_trib1.json (clean.passed_preregistered_rule)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 1.1470526009686455 | minimum clean-margin ratio at 2.4 um with current thresholds (goal >= 3) | `logs/sib/tribunal/real_trib2/gate_2p4um.json` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |

**Lesson.** Plant the faults you fear and confirm that code catches them. A pre-registered threshold rule can itself be defective, and thresholds calibrated at one voxel size do not transfer to another.

### Tribunal: empirical-null dry run

**Verdict: FAILED**

**Question.** Can a pre-registered empirical null set of same-radius-band tiles (>= 40) be built around a mock target region on clean known-text papyrus?

**Method.** Mock target on clean known-text papyrus, local sheet pitch measured from the organizer surface prediction, band selection by pre-registered rules.

**Result.** The dry run found 0 of 89 band candidates eligible and only 4 null tiles against the 40 required, because the geometry-only centre estimate was poor and the radius band was ill-defined. A null-set design needs a declared centre source first.

| number | meaning | source |
|---|---|---|
| INSUFFICIENT | null-set status under the pre-registered criterion | `logs/sib/tribunal/real_trib2/null_dryrun/null_dryrun.json (null_set.status)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 4 | tiles obtained (n_total_min 40) | `logs/sib/tribunal/real_trib2/null_dryrun/null_dryrun.json (null_set.n_tiles)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |
| 326.4645387126285 | median normal-line miss distance (vox) of the geometry-only centre curve, showing a poor centre estimate | `logs/sib/tribunal/real_trib2/null_dryrun/null_dryrun.json (centre_curve)` (claude/gifted-bell-gavnl5-sib-tribunal @ a11610163) |

**Lesson.** Dry-run a null design on known material before it is needed; this one would not have produced a usable null.

### READCAL-2 reader-acuity programme (sib-readcal2)

**Verdict: STOPPED**

**Question.** Can in-context calibration (exemplar sheets with a placebo control, multi-scale display, row-first prompting, second reader model) raise reader acuity, measured as sigma_crit, without raising hallucination?

**Method.** Builder-only: display and sheet builders, measured noise spectrum of blank base maps, candidate bank under same-papyrus exclusions, scoring glue reproducing the D1 sigma_crit.

**Result.** The arms, placebo-matched exemplar sheets, noise model, bank candidates and a declaration draft (default outcome: no gain) were built and tested. The programme was never declared or read, so it produced no verdict.

| number | meaning | source |
|---|---|---|
| DONE (builder deliverables complete; see REPORT.md) | lane status: builder only | `logs/sib/readcal2/STATUS.md` (claude/gifted-bell-gavnl5-sib-readcal2 @ 46a7c29a3) |
| no reader, picker or sealer ran | no reads were made | `logs/sib/readcal2/REPORT.md` (claude/gifted-bell-gavnl5-sib-readcal2 @ 46a7c29a3) |
| 30 unit tests | tests for the six arm builders | `logs/sib/readcal2/REPORT.md (Deliverables)` (claude/gifted-bell-gavnl5-sib-readcal2 @ 46a7c29a3) |

**Lesson.** A placebo-controlled exemplar arm is the right design for testing whether prompting improves reading; it remains untested here.

## Fine-tuning and own ink models

24 Sep to 10 Oct 2026 · 15 experiments · 4 failed · 1 inconclusive · 4 stopped · 6 tool

Dominion trained or fine-tuned ink models on CPU and judged them only by pre-registered held-out metrics or sealed, controlled blind reads. Fine-tuning the public 9 um model on nearby papyrus (D3) left unseen text unreadable (0 net letters in every arm). A from-scratch 8.64 um master model reached about 0.58 held-out AUC against a 0.90 bar, while a public dense model reached 0.76. The larger pooled-training (D2) and DEV-loop programmes never trained on real data, for lack of a GPU and a frozen evaluator; several lanes produced tested tools instead.

### D3 fold-0841 fine-tune (four arms, sealed reads)

**Verdict: FAILED**

**Question.** Does a short CPU fine-tune of the public 9 um ink model on nearby PHerc0841 papyrus make unseen 0841 text nameable by blind readers?

**Method.** Four paired arms started from the same base checkpoint: fine-tune, label-deranged null, depth-reversed, and replay-only control. The fine-tune, null and depth-reversed arms trained 2000 CPU steps on a 288-tile pool (half of each batch, kept at least 128 voxels from five sealed known-text windows) plus replay; the replay-only control trained 2000 steps on replay papyrus only. 24 sealed blind reads were scored by pre-hashed code against pre-registered bars, and an independent audit followed.

**Result.** This pre-registered test asked whether fine-tuning the public 9 um ink model on 288 tiles of nearby papyrus from the same scroll makes unseen text legible. Verdict: not passed. In all 24 sealed blind reads, every arm (fine-tune, label-scrambled null, depth-reversed control, replay-only control) scored 0 net letters on the sealed known-text windows, with p_max 1. Every reader named 3-13 letters on a known-text canary, so the readers could read. An independent audit re-derived all 144 scored records with 0 mismatches.

| number | meaning | source |
|---|---|---|
| 306 | PRIMARY text patches available for the fold-A pool (bar 280): D3 feasible on current material | `RULES.md (D3-FEAS-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 288 | fold-A training pool after the 144-voxel slab margin | `RULES.md (DECL-D3-A2)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| C_all/C_net 0 in all 8 arm-states | net letters named on sealed windows, every arm and mirror state | `LEDGER.md (D3 FOLD-0841 row); logs/d1/d3_summary.json sha256 fb8d31c0...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| FA 0 namings on 72 J/blank panels | fine-tune arm readers named nothing on any sealed or blank panel | `LEDGER.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| p_max(FA) 1 | max-T permutation p for the fine-tune arm | `LEDGER.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| canary 3-13 per reader | letters every reader named on the known-text canary (readers could read) | `LEDGER.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0 mismatches over 144 scored records | independent audit re-derivation | `RULES.md (D3-VERDICT); logs/d1/audit_d3.json sha256 3ad936ed...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| kappa 0.6139 | agreement of reference-map teacher labels with official human labels on the 288-tile pool (reported, not deciding) | `RULES.md (D3-PRECHECK-RESULT); logs/d1/d3_label_equiv.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 1.69 h per 2000-step arm | CPU timing per arm (batch 8, fp32, 3 threads) | `RULES.md (DECL-D3-A1); logs/d1/d3_timing.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A small in-domain fine-tune cannot rescue maps that are illegible at 9 um. A known-text canary in every reading session separates 'the reader failed' from 'the map carries nothing'. Teacher labels taken from reference maps agreed only moderately with human labels (kappa 0.61), which caps what such fine-tunes can learn.

### Hecate 9.6 um zero-shot screen on PHerc0841

**Verdict: FAILED**

**Question.** Does the newer official Hecate 9.6 um checkpoint read PHerc0841 ink well enough at pixel level to merit its own blind-read arm?

**Method.** Zero-shot inference with the official recipe on held-out 0841 pixels (at least 144 voxels from the sealed windows), both depth orders, pixel AUC against official human labels. The pre-registered bar was best-order AUC >= 0.75 and no more than 0.02 below the base model, decided before any model-arm read.

**Result.** Screened out. Hecate's best-order AUC was 0.678 against a 0.75 bar (base model 0.634 on the same pixels), so no reads were spent on it. The screen rested on one segment and 0.066 cm^2 (75,093 labelled pixels), because the human labels barely extend outside the sealed-window exclusion shell.

| number | meaning | source |
|---|---|---|
| 0.67834 | Hecate forward-order pixel AUC (best order) | `RULES.md (HECATE-SCREEN); logs/d1/hecate_screen_summary.json sha256 6b90169e...` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.63398 | base model best-order (reverse) AUC on the same pixels | `RULES.md (HECATE-SCREEN)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.75 | pre-registered AUC bar | `RULES.md (DECL-HECATE)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 75,093 | labelled pixels scored (29,716 ink, 45,377 blank; 0.066 cm^2, one segment) | `RULES.md (HECATE-SCREEN)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A cheap pixel-AUC gate before any reader time protects the read budget. On so small a held-out area, though, even the base model is near chance, so the screen bounds a model's usefulness rather than ranking models.

### Master 8.64 um ink model from scratch (federated CPU training)

**Verdict: FAILED**

**Question.** Can a 3-D U-Net with fixed 3-D edge channels, trained from scratch on CPU with organizer high-resolution predictions as pseudo-labels at 8.64 um, generalize to a held-out scroll at the same scan setting?

**Method.** Trained on 18 PHerc0009B segments, with PHerc0343P (8 segments) held out entirely. 12 federated CPU lanes ran 2 fp32 epochs per round and were averaged. Bars were declared before any training data existed: held-out pixel AUC >= 0.90, AP >= 0.50, tile AUC >= 0.85.

**Result.** Failed its bars. On the held-out scroll (600 crops), the averaged model scored pixel AUC 0.5793, AP 0.1667 and tile AUC 0.575 after round 1, and 0.5778 after round 2, against bars of 0.90, 0.50 and 0.85. The lanes reported 0.63-0.68 on their own validation, so the gain did not transfer. The self-supervised and centralized-control lanes produced no committed result before the fleet ran out of usage credits.

| number | meaning | source |
|---|---|---|
| 0.5793 | held-out pixel AUC, round-1 averaged model global_r1 (AP 0.1667, tile AUC 0.575) | `logs/fl7/global_r1.eval.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.5778 | held-out pixel AUC, round-2 model global_r2 (AP 0.1649, tile AUC 0.572) | `logs/fl7/global_r2.eval.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.5756 | held-out pixel AUC of the common init global_r0 | `logs/fl7/global_r0.eval.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.63-0.68 | lanes' own validation AUC in round 1 (did not transfer) | `RULES.md (E2E-1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.9 / 0.5 / 0.85 | declared bars (pixel AUC / AP / tile AUC) | `logs/fl7/global_r1.eval.json (bars)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Validation on the training scroll overstated transfer. A from-scratch CPU model after two rounds sits far below public pretrained weights on the same held-out crops, so a pipeline should start from the strongest public model.

### Fine-tune of a public dense 9 um model on 8.64 um pseudo-labels

**Verdict: FAILED**

**Question.** Does fine-tuning the decoder and head of the strongest public 9 um model on the same pseudo-labels raise its held-out score at the 8.64 um setting?

**Method.** Encoder frozen. Decoder and head trained for 2000 steps, batch 4, AdamW lr 1e-4, Dice+BCE on PHerc0009B pseudo-labels. Held-out evaluation every 250 steps on PHerc0343P, keeping the best checkpoint. Bars unchanged from the master-model declaration.

**Result.** No gain. Fine-tuning only the decoder and head of a public dense 9 um model for 2000 steps on the same pseudo-labels never beat its own starting weights on the held-out scroll: pixel AUC 0.698 at step 0 on isolated crops, 0.634-0.676 at later steps. The kept model is therefore the unchanged public model. Its full-map score (AUC 0.760, AP 0.408, tile AUC 0.688) also misses the 0.90 / 0.50 / 0.85 bars.

| number | meaning | source |
|---|---|---|
| 0.698 | step 0 (unchanged public weights) held-out pixel AUC on isolated crops (AP 0.297, tile AUC 0.626) | `RULES.md (FL7-A1-RESULT); logs/fl7/dense_ft/eval_0.json` (claude/gifted-bell-gavnl5 @ a1f9f4635; fl4t @ a250ae8c2) |
| 0.634-0.676 | held-out pixel AUC at steps 250-2000 (below step 0) | `RULES.md (FL7-A1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| AUC 0.760 / AP 0.408 / tile AUC(p95) 0.688 | full-map score of the kept (base) weights on the held-out segment | `RULES.md (FL7-A1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 726 s | wall time for 2000 steps (0.25 s per step) | `RULES.md (FL7-A1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Fine-tuning on pseudo-labels produced by another model can pull a stronger model toward the labeller's errors. Evaluate step 0 first, and keep the base if no step beats it.

### Public ink models on a held-out 8.64 um scroll (reference)

**Verdict: TOOL**

**Question.** How well do existing public ink models score against the organizer pseudo-labels on the held-out PHerc0343P segment, as a reference for the master-model bars?

**Method.** Each public model was run with its own documented recipe on the same 600 held-out crops, in both depth orders, and scored with the same pixel AUC, AP and tile-AUC code.

**Result.** Reference measurement for the master-model bars on 600 held-out crops. The public dense 9 um model scored pixel AUC 0.7605 in forward depth order (0.7694 averaging depth windows), Hecate 9.6 um 0.7309, a public 8 um model 0.7499 per crop, and the base ink_9um model 0.6539. Reverse depth orders scored 0.5352-0.5847 for the main variants. No public model reaches the declared 0.90 bar against these pseudo-labels.

| number | meaning | source |
|---|---|---|
| 0.7605 | public dense 9 um model, forward order, pixel AUC (0.7694 averaging depth windows) | `logs/fl7/baseline_dense/PHerc0343P_20250511003658/summary.json` (fl4t @ a250ae8c2) |
| 0.7309 | Hecate 9.6 um resampled, forward order, pixel AUC | `logs/fl7/baseline_hecate/PHerc0343P_20250511003658/summary.json` (fl4t @ a250ae8c2) |
| 0.7498928110849713 | public 8 um model, forward order, per-crop pixel AUC | `logs/fl7/baseline_8um/PHerc0343P_20250511003658/v8in_crops_fwd.json` (fl4t @ a250ae8c2) |
| 0.6539 | base ink_9um seed42 step-75k, forward order, pixel AUC | `logs/fl7/baseline_dense/PHerc0343P_20250511003658/summary.json` (fl4t @ a250ae8c2) |
| 0.5847 | public dense model, reverse order (reverse orders of the main variants 0.5352-0.5847) | `logs/fl7/baseline_dense/PHerc0343P_20250511003658/summary.json` (fl4t @ a250ae8c2) |

**Lesson.** Score depth order explicitly, because the wrong order drops every model toward chance. Pseudo-labels from another model also cap any held-out AUC, so the bar must be set against that ceiling.

### Pooled-training CPU trainer (D2 infrastructure)

**Verdict: TOOL**

**Question.** Can a deterministic, resumable CPU trainer be built for the pooled 9 um -> 2.4 um training programme, and what would the programme cost on CPU?

**Method.** The trainer generalized the D3 fine-tune loop. On synthetic data only, it was tested for bitwise equivalence with the D3 loop, determinism, paired sampling, and resume from checkpoint shards pushed to and fetched from a remote ref. Throughput was measured per tile size and precision.

**Result.** A reproducible CPU trainer was built and tested on synthetic data only. It matched the earlier fine-tune loop bitwise, was bitwise deterministic, and resumed bitwise from checkpoint shards stored remotely (26 tests passed). The measured cost made the plan impractical on CPU: 39.8 h per 12k-step arm at 128 px and 346.6 h (14.4 days) at 384 px in fp32, about 135 session-days for all 12 arm-seeds.

| number | meaning | source |
|---|---|---|
| 26 passed, 0 failed | trainer unit and integration tests | `logs/sib/trainer/REPORT.md` (claude/gifted-bell-gavnl5-sib-trainer @ 22a723b75) |
| 39.8 h | 12k-step arm at 128 px, fp32, 4 threads | `logs/sib/trainer/REPORT.md` (claude/gifted-bell-gavnl5-sib-trainer @ 22a723b75) |
| 346.6 h (14.4 d) | 12k-step arm at 384 px, fp32 | `logs/sib/trainer/REPORT.md` (claude/gifted-bell-gavnl5-sib-trainer @ 22a723b75) |
| 135 session-days at fp32 | total for 12 arm-seeds | `logs/sib/trainer/REPORT.md` (claude/gifted-bell-gavnl5-sib-trainer @ 22a723b75) |
| 4e3572c7b3ec58316edd1fe5cefe7cbeb175bb2715ec1761abdfcb6af80d9490 | final weights of the synthetic 2-step test, restored byte-identical from the remote shard ref | `MANIFEST.json` (claude/gifted-bell-gavnl5-sib-trainer-ckpt @ 46d858ddd) |

**Lesson.** Measure throughput before committing to a training programme. Remote checkpoint shards make long CPU runs survive container reclaims, at the cost of unreachable objects piling up on the remote.

### D2 pooled 9 um -> 2.4 um training arms

**Verdict: STOPPED**

**Question.** Does pooled training with native 9 um inputs and 2.4 um targets make unseen scrolls legible above chance (128 px and 384 px arms, with label-deranged and depth-reversed controls)?

**Method.** Each declared arm ran on its own CPU host and passed environment pinning, unit and integration tests, synthetic smoke training with bitwise resume, and a pairing check. Real training waited on a pair freeze, declared recipe amendments and an explicit go signal.

**Result.** Never trained on real data. The four declared arms (128 px, 384 px, label-deranged null, depth-reversed) were each set up on their own CPU host and passed synthetic smoke tests with bitwise resume. The pair freeze, recipe amendments and go signal never came, and no GPU was available. One host measured 148.75 s per step at 384 px, a 20.7-day projection per arm.

| number | meaning | source |
|---|---|---|
| median 148.75 s/step | null arm, 384 px full forward, fp32, batch 32, on a non-AMX host | `logs/sib/d2-null/READY.md` (claude/gifted-bell-gavnl5-sib-d2-null @ 45b1ccf72) |
| 495.8 h = 20.7 days | projected 12k-step null arm on that host | `logs/sib/d2-null/READY.md` (claude/gifted-bell-gavnl5-sib-d2-null @ 45b1ccf72) |
| 18.35 s/step | 128 px arm synthetic smoke, fp32, batch 32 | `logs/sib/d2-p128/STATUS.md` (claude/gifted-bell-gavnl5-sib-d2-p128 @ b737266dd) |
| 147.8 s/step | depth-reversed arm synthetic smoke, fp32 | `logs/sib/d2-rev/STATUS.md` (claude/gifted-bell-gavnl5-sib-d2-rev @ e627fa999) |
| 129.2 s/step | 384 px arm synthetic smoke | `commit message` (claude/gifted-bell-gavnl5-sib-d2-p384 @ 0cec61d6a) |

**Lesson.** Host hardware varied: some containers lacked AMX and ran markedly slower. Throughput has to be measured per host before scheduling a multi-week CPU run.

### DEV-loop recipe screening

**Verdict: STOPPED**

**Question.** Do new recipes (frozen-encoder letter-context head, soft targets, distillation) bring 9 um maps closer to the sharpness of the 2.4 um reference on certified development windows?

**Method.** sigma_eq (the blur of the reference that best matches the model map), computed on a certified, contamination-checked development registry. Every recipe carried null, reversed and chance controls and an alarm rule, and the registry and evaluator had to be frozen and hashed before any training.

**Result.** Never trained on real data. A development loop was designed to rank new recipes by how close their maps come to the sharpness of the 2.4 um reference on certified development windows, with null and reversed controls for each. The evaluator (21 synthetic tests) and a 9-window registry were built, but the registry was never frozen and hashed, so no recipe trained and no development map exists.

| number | meaning | source |
|---|---|---|
| 21 synthetic tests pass | DEV evaluator test suite | `logs/sib/devloop/ASK.md` (claude/gifted-bell-gavnl5-sib-devloop @ 835cff610) |
| 0139 4 text + 1 blank (1 cm); 0814 4 text + 0 blanks | development registry v3 (9 windows); 0814 lacked the required blanks | `logs/sib/devloop/ASK.md` (claude/gifted-bell-gavnl5-sib-devloop @ 835cff610) |
| 121 are dropped and 443 kept | provisional hold-out effect on 564 staged training patches | `logs/sib/dev-distft/STATUS.md` (claude/gifted-bell-gavnl5-sib-dev-distft @ 164ad62a3) |

**Lesson.** A loop that needs a frozen evaluator before any training stalls the whole recipe fleet if the freeze depends on one paused session. The freeze should be a small, separately ownable step.

### Official-checkpoint DEV screen

**Verdict: STOPPED**

**Question.** Does any official checkpoint's 9 um map of unseen known text reach reader-level sharpness on the development evaluator?

**Method.** 14 checkpoints' weights were sha256-verified, their input specifications and documented depth order recorded, and an in-sample guard computed per development window. A ranked table was to come from the frozen evaluator.

**Result.** Never run. Weights, input specifications and in-sample guards were prepared for 14 official checkpoints, but the screen gate never opened because the development evaluator was never frozen. At the ruled geometry the screen was estimated at about 630 CPU-hours for one family before blanks.

| number | meaning | source |
|---|---|---|
| ~630 CPU-h before blanks | estimated cost for 6 checkpoints x 2 orders x 8 text windows at the ruled geometry | `logs/sib/ckpt-screen-b/STATUS.md` (claude/gifted-bell-gavnl5-sib-ckpt-screen-b @ 61111081b) |
| ~394 CPU-min per order per 2x2 cm window | per-window cost of the PHerc.1667 family at the ruled geometry | `logs/sib/ckpt-screen-b/STATUS.md` (claude/gifted-bell-gavnl5-sib-ckpt-screen-b @ 61111081b) |

**Lesson.** Record documented training data per checkpoint early: it also decides, at no extra cost, which checkpoints can be applied to a scroll without training overlap.

### AMX bf16 speed and equivalence on CPU

**Verdict: TOOL**

**Question.** How much do bf16 autocast and Intel AMX speed up the base ink model on CPU, and are bf16 maps equivalent to fp32?

**Method.** Benchmarks on random inputs only, using the official model and the D3 training step, across thread counts, memory formats and precisions. An end-to-end bf16 vs fp32 comparison ran through the official inference CLI. A bf16 training-parity gate was declared, never run.

**Result.** On random inputs, bf16 autocast on AMX CPUs sped up a training step of the base model 1.83-2.06x at 4 threads and inference 1.60-1.74x. Inference was not output-equivalent: 98.18 % / 97.72 % of pixels within +-2 grey levels against a 99.9 % bar, and 98.41 % on real data in a separate chain test. Maps therefore stayed fp32. The declared bf16 training-parity gate was never run.

| number | meaning | source |
|---|---|---|
| 1.83-2.06x | bf16 vs fp32 speed-up of a full training step at 4 threads (batch 8) | `logs/sib/amx/REPORT.md` (claude/gifted-bell-gavnl5-sib-amx @ 872d7dd78) |
| 1.60-1.74x | bf16 inference speed-up (batch 4) | `logs/sib/amx/REPORT.md` (claude/gifted-bell-gavnl5-sib-amx @ 872d7dd78) |
| 98.18 % / 97.72 % | pixels within +-2 grey levels, bf16 vs fp32 end to end (bar 99.9 %): inference stays fp32 | `logs/sib/amx/REPORT.md` (claude/gifted-bell-gavnl5-sib-amx @ 872d7dd78) |
| 98.41 % | same criterion on real 2.4 um data in the chain test | `logs/sib/chain2um/REPORT.md` (claude/gifted-bell-gavnl5-sib-chain2um @ 1c4fb1444) |
| 55 % | share of fp32 inference time spent in the small 3-D stem | `logs/sib/amx/REPORT.md` (claude/gifted-bell-gavnl5-sib-amx @ 872d7dd78) |

**Lesson.** Profile before optimizing: a small 3-D stem took 55 % of fp32 inference time. Check the CPU features of every container, since some hosts lacked AMX, so bf16 could not be used there and fp32 was markedly slower.

### 2.4 um ink chain reproduction on CPU

**Verdict: INCONCLUSIVE**

**Question.** Does our CPU run of the official 2.4 um ink chain reproduce the organizer map and pass the declared end-to-end gate on a labelled control?

**Method.** Official render plus official 2.4 um model inference on a code-selected, organizer-labelled control region, in both depth orders, scored with the project's hashed pixel metrics against human labels and against the organizer map. Gate as declared: AUC >= 0.90 in the text order, <= 0.60 in the other.

**Result.** Our CPU reproduction of the official 2.4 um ink chain matched the organizer map almost exactly (r 0.999986) on a code-selected labelled control. The gate as written (AUC >= 0.90 against labels) was still not met: our map scored 0.88795 and the organizer's own map 0.88798 on the same pixels, so the bar was out of reach even for the reference. The gate was not recorded as passed. The test also showed that 'reverse' depth order is not a convention-free name, because it depends on the render's normal direction.

| number | meaning | source |
|---|---|---|
| 0.999986 | Pearson r of our forward-order map vs the organizer map | `logs/sib/chain2um/REPORT.md` (claude/gifted-bell-gavnl5-sib-chain2um @ 1c4fb1444) |
| 0.88795 | our map's AUC vs human labels (gate bar 0.90) | `logs/sib/chain2um/REPORT.md` (claude/gifted-bell-gavnl5-sib-chain2um @ 1c4fb1444) |
| 0.88798 | the organizer map's own AUC on the same pixels (the ceiling) | `logs/sib/chain2um/REPORT.md` (claude/gifted-bell-gavnl5-sib-chain2um @ 1c4fb1444) |
| 0.47070 | AUC in the other depth order | `logs/sib/chain2um/REPORT.md` (claude/gifted-bell-gavnl5-sib-chain2um @ 1c4fb1444) |

**Lesson.** Calibrate gate thresholds on the reference itself before declaring them. Name the depth order by render frame, not by the word 'forward' or 'reverse'.

### Submission-package factory and verifier

**Verdict: TOOL**

**Question.** Can a submission package be built, verified and reproduced byte-for-byte by code, with planted faults caught?

**Method.** A package maker and an independent 16-check verifier, exercised in dry-run mode on a known-text window outside every sealed set. A fresh-directory reproduction and a planted-fault drill followed.

**Result.** A submission-package factory and a 16-check verifier were built and exercised on a dry-run known-text window. All 16 checks passed, and a fresh reproduction rebuilt render, panel and image byte-identically in 55 s. Each of 6 planted faults (hidden PNG chunk, short scale bar, zero-width character, wrong volume ID, relabelled dry run, gamma change) was rejected by its own check. The full factory bars (fresh-agent rebuild, null tiles, reference read-back) were never run.

| number | meaning | source |
|---|---|---|
| 16/16 pass | verifier checks on the dry-run package | `logs/sib/factory/REPORT.md` (claude/gifted-bell-gavnl5-sib-factory @ a3b07b201) |
| 55 s | fresh reproduction; raw render, CT panel and PNG byte-identical | `logs/sib/factory/REPORT.md` (claude/gifted-bell-gavnl5-sib-factory @ a3b07b201) |

**Lesson.** Make every package claim mechanically checkable, with no image metadata, a measured scale bar and pinned tools, and prove the verifier with planted faults before it matters.

### Submission gate as tested code

**Verdict: TOOL**

**Question.** Can the declared submission gate be implemented as unit-tested code, and do its rules hold up on known material?

**Method.** Gate code, copy test, line-spacing and height surveys on official labels, a licence-lineage checker, and a dry-run answer-sheet kit that refuses any reader text. Rule revisions were based on known material only.

**Result.** The submission gate was coded as tested software (726 passed, 7 skipped, 0 failed), with a dry-run answer-sheet kit that refuses any reader text. A calibration on 68 official labelled ink blobs found only 75-78 % in the 2-4 mm height band, so a proposed '>= 80 % in band' rule was dropped. A licence-lineage checker found that the open data's non-commercial licence blocks permissive release of derived data.

| number | meaning | source |
|---|---|---|
| 726 passed, 7 skipped, 0 failed | merged-layout test suite | `logs/sib/sg/REPORT.md` (claude/gifted-bell-gavnl5-sib-sg @ 20397b831) |
| 75-78 % | share of 68 official labelled ink blobs within the 2-4 mm height band; a '>= 80 % in band' rule was dropped | `CHANGELOG.md (2026-09-25 19:2x sibling harvest)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| overall BLOCKS | licence lineage of the base chain (non-commercial open-data licence blocks permissive release) | `logs/sib/sg/REPORT.md` (claude/gifted-bell-gavnl5-sib-sg @ 20397b831) |

**Lesson.** Calibrate every gate rule on known material before relying on it. A plausible-looking rule would have rejected about a quarter of genuine letters.

### 3-D training-contamination checker

**Verdict: STOPPED**

**Question.** Can contamination between training patches and evaluation regions (re-traces of the same papyrus) be detected fail-closed in 3-D?

**Method.** Point-to-surface clearance and a same-papyrus rule built on densified meshes. Synthetic tests came first, then planted re-trace faults on real meshes.

**Result.** A 3-D contamination checker (training-patch clearance and a fail-closed same-papyrus rule) was built with 26 synthetic tests. On real meshes, planted re-trace faults were caught in every case that was built. Two planted patch cases were never built, so the real-data record reads all_caught false. The session then paused on a direct stop and never resumed.

| number | meaning | source |
|---|---|---|
| 26 synthetic tests | core test suite of the checker | `logs/sib/contam/proposals/PROPOSALS.md` (claude/gifted-bell-gavnl5-sib-contam @ 9dd1af44a) |
| all_caught: false | real-data planted-fault record; every built case was caught, but two patch cases were never built | `logs/sib/contam/planted_faults_0139.json` (claude/gifted-bell-gavnl5-sib-contam @ 9dd1af44a) |

**Lesson.** The same-papyrus rule cannot tell a re-trace from two windings pressed into contact. Over-merging is the safe default for contamination, since it only removes training material.

### Rejection-gated surface tracer

**Verdict: TOOL**

**Question.** Does a distance-gated, compactness-constrained patch to the official surface tracer stop sheet bridging without killing growth?

**Method.** A patch to the official tracer, tested on synthetic scenes (two close sheets, a hole, a clean sheet) against unpatched controls, then run on 6 development seeds of a team-segmented scroll with declared presets. A 75-generation self-test followed.

**Result.** A rejection-gated patch to the official surface tracer never bridged two sheets 8 voxels apart in synthetic scenes, where the unpatched build did. It failed the declared growth-past-rejection test as given and the full-area test in most presets. On 6 development seeds the presets saved 5 of 6 seeds, with median truncated areas of 0.46-0.86 cm^2, and a 75-generation self-test kept 1.60 cm^2. The declared surface test (median >= 3.0 cm^2) was expected to fail and was never run.

| number | meaning | source |
|---|---|---|
| 5/6 | development seeds saved by each L-family preset | `logs/sib/tracer/REPORT.md` (claude/gifted-bell-gavnl5-sib-tracer @ bee2fe682) |
| 0.46 / 0.86 / 0.61 | median truncated (v2) area in cm^2 for presets L15 / L20 / L25 | `logs/sib/tracer/REPORT.md` (claude/gifted-bell-gavnl5-sib-tracer @ bee2fe682) |
| v2 area 1.60 cm² | 75-generation self-test after truncation at generation 46 | `logs/sib/tracer/REPORT.md` (claude/gifted-bell-gavnl5-sib-tracer @ bee2fe682) |

**Lesson.** Synthetic gate tests caught real bridging failures early. Amendments made after seeing results were disclosed, and the failing tests were recorded as failures rather than loosened.

## PHerc. Paris 4 (withheld)

72 experiments · 72 withheld

All work on PHerc. Paris 4 is withheld and only counted, whatever it showed, because the scroll is treated as not officially read. No letters are claimed on any scroll.

## First Letters push

25 Sep to 14 Oct 2026 · 23 experiments · 1 passed · 6 failed · 6 null · 1 inconclusive · 1 void · 5 stopped · 3 tool

From 30 Sep to 3 Oct 2026, Dominion ran an all-out First Letters screen over the 22 eligible volumes. One or two worker lanes per scroll grew surfaces and ran the official 9 um ink model. The resulting 2 x 2 cm tiles and 4 x 4 cm stitched windows went to blind LLM readers, behind a positive control on held-out known text. A Grand Prize TimeSformer arm followed, then surface-following fixes, a row-periodicity detector and a final screen on segments the organizers had published. Every positive control failed (single tiles: 1 of 12 with rows, max 1 letter; windows: max 4 marks against a bar of 5). The FL-2 and FL-3 censuses returned 0 positives, and the FL-4 reads were declared void. The auto-grown surfaces behind nearly all eligible-scroll tiles were later shown to cut across windings, so the nulls say nothing about the scrolls. Nothing was claimed or submitted. What lasts is three released tools (xsec, ringstrip, orgsec-ink; listed under Tools, infrastructure and operations) and a method lesson: prove surface validity and reader sensitivity before spending on any census. The later PHerc0268 mass run, in a separate repository, traced its first-pass signal to a blank-margin artifact (Result 1 of this release, stripqc).

### Per-scroll First Letters material fleet

**Verdict: TOOL**

**Question.** Can a fleet of one or two worker sessions per eligible volume produce official-model ink tiles for all 22 First Letters volumes inside the push window?

**Method.** Each lane takes organizer tifxyz segments where they exist and otherwise auto-grows surfaces on the organizer surface prediction (0 self-intersections, >= 16 cm2). It then renders with the validated 9 um chain, runs the official ink_9um step-075000 both directions without TTA, and cuts 2 x 2 cm tiles, ranked by a code-only ink-score pre-screen. Every tile records its segment's tifxyz sha256.

**Result.** The fleet produced 2650 official-model tiles covering all 22 eligible volumes; wave 1 had tiles for 21, because one worker never got its environment running. Lanes ran into full disks, session safety-classifier refusals, background-job time limits, two pipelines running at once (one lane's two-hour window was invalidated) and a shell-variable bug that rendered an old mesh under a new name (16 tiles withdrawn). The next entry shows that most of this material came from a grower that cuts across windings.

| number | meaning | source |
|---|---|---|
| 2650 official-model tiles | tiles available to the stitched-window census, all verified by png sha256 | `RULES.md (FL3-W1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 21 eligible scrolls x 8 tiles = 168 official-model tiles | wave-1 census material; PHerc0490B had no tiles (worker stuck at env) | `RULES.md (FL2-WAVE1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 32 tiles (4 segments x 2x2 cells x 2 directions) | pilot lane DECL-FL-1 output on PHerc0257 | `logs/sib/fl-pherc0257/STATUS.md` (claude/gifted-bell-gavnl5-sib-fl-pherc0257 @ 1f712d0df) |
| their 16 official tiles are WITHDRAWN (deleted) | tiles rendered from the wrong mesh because a retry loop overwrote a shared shell variable | `logs/sib/fl-pherc0191/fl2/STATUS.md` (claude/gifted-bell-gavnl5-sib-fl-pherc0191 @ edd797045) |
| fl-pherc0358 (x3) | worker-session creation for one scroll refused three times by the safety classifier | `logs/sib/fl_fleet_state.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Per-unit idempotent markers and pushed per-tile provenance made every defect traceable after the fact. A lane fleet still needs a central fix channel and a central quality gate: a bug or flag found by one lane took hours to reach the shared kit.

### Surface-following check of auto-grown segments

**Verdict: FAILED**

**Question.** Do the auto-grown surfaces behind the First Letters tiles actually lie on one papyrus sheet?

**Method.** Numbers-only checks by workers, later repeated by the orchestrating agent:
- fraction of mesh vertices on the organizer surface prediction;
- a normal-offset control (support should peak at offset 0);
- fraction of vertices inside the CT mask;
- median |cos| between surface normal and radial direction, with a synthetic spiral as control.

**Result.** Lane-level numeric checks on the first morning showed that grown meshes had no support peak on the predicted sheet: the median on-sheet fraction was 0.1955 on one scroll, and the normal-offset control failed on another. The declared surface gate (area >= 16 cm2, zero self-intersections) is passed trivially by a smooth extrapolated sheet. On day 2 the cause was confirmed: the grower had run without the organizers' normal grids (median |cos| 0.14-0.40, against 1.00 on a synthetic wrap). As a result, no FL-2/FL-3 null on an unread scroll is informative.

| number | meaning | source |
|---|---|---|
| no peak at 0: on-mesh support equals off-sheet support (FAIL) | normal-offset control on grown segments of one scroll | `logs/sib/fl-pherc0306b/fl2/SURFACE_CHECK.json` (claude/gifted-bell-gavnl5-sib-fl-pherc0306b @ aaa3554ee) |
| 0.1955 | median fraction of vertices on the predicted sheet, 20 kept segments of another scroll (on_sheet_median) | `logs/sib/fl-pherc0846b/fl2/GEOMETRY_CHECK.json` (claude/gifted-bell-gavnl5-sib-fl-pherc0846b @ ebee0c09b) |
| median 0.14-0.40, frac>0.8 = 0.01-0.10 | radial \|cos\| on the 9 locally held FL-4 segments; the synthetic wrap control gives median 1.00 | `RULES.md (DECL-FL-4-A5)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 2,596 tiles, 22 scrolls | every unread-scroll FL-2/FL-3 tile came from the pre-fix grower that cuts across windings | `RULES.md (DECL-FL-5 item 1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Gate the surface before any ink-model or reader spend: sheet support, a normal-offset control and a cross-section. Propagate worker flags centrally. Here two lanes flagged the defect hours before the first census read, the flagged tiles were read anyway, and the same grower settings were reused for the next arm.

### Community dense-model arm

**Verdict: STOPPED**

**Question.** Should a second, community-trained 9 um ink model run alongside the official one?

**Method.** The arm was declared on condition that the pilot lane first verified the weight hashes and reproduced a finite prediction. It was withdrawn by erratum before any download completed.

**Result.** A community-trained 9 um model was declared as a second arm and withdrawn 9 minutes later, before any use. It conflicted with the project's standing rule of official organizer products plus own work only, and the pilot's download was also refused by its session safety classifier. Every First Letters read in this family used the official model only.

| number | meaning | source |
|---|---|---|
| DENSE_FAIL | pilot status: download denied by the session classifier ([Untrusted Code Integration]) before hash check or load | `logs/sib/fl-pherc0257/fl2/DENSE_FAIL.json` (claude/gifted-bell-gavnl5-sib-fl-pherc0257 @ 1f712d0df) |
| the DENSE arm is withdrawn | erratum 9 minutes after the declaration; official model only from then on | `RULES.md (DECL-FL-2-E1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Reconcile a new arm with the standing integrity rules before declaring it, not after workers have been dispatched.

### Training-overlap screen

**Verdict: PASSED**

**Question.** Does any eligible volume, or the gate material, appear in the official ink model's training set?

**Method.** The training scrolls were listed from the official model card, and the held-out gate segments were checked against the organizer training config.

**Result.** No eligible volume is in the official ink_9um training set (PHerc0139, PHerc1667, PHerc Paris 4, PHerc0814), so no tile was excluded. The gate material was then redefined as PHerc0139 segments absent from the training config, which makes them held-out data for the model.

| number | meaning | source |
|---|---|---|
| PHerc0139, PHerc1667, PHercParis4, PHerc0814 | official ink_9um training scrolls (training_scrolls) | `logs/sib/fl-pherc0257/fl2/TRAINING_SCROLLS.json` (claude/gifted-bell-gavnl5-sib-fl-pherc0257 @ 1f712d0df) |
| None of the 22 eligible volumes is among them, so no tile is excluded. | eligibility after the overlap check | `RULES.md (DECL-FL-2-E1 item 3)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| listed in official ink_9um training: NO | the organizer segment considered for the gate is not a training segment | `logs/sib/pairs0139c/fl2_gate/STATUS.md` (claude/gifted-bell-gavnl5-sib-pairs0139c @ be6d4f134) |

**Lesson.** Check training overlap before any package, and use it to choose positive-control material that is held out from the model.

### Single-tile positive-control gate (held-out PHerc0139)

**Verdict: FAILED**

**Question.** Can the pipeline (official model, 2 x 2 cm tile, sigma2t brief, blind reader) surface >= 10 letters on held-out known-text papyrus?

**Method.** Gate material came from PHerc0139 segments outside the model's training list, run through the identical pipeline and pre-screen. SENSITIVE iff >= 1 tile is rows-Y with >= 10 letters. The planned target-strip material was redefined before any read: at 1.67 cm tall it holds no 2 x 2 cm cell. Large segments were rendered in grid-aligned pieces because of disk limits.

**Result.** The positive control failed twice: 1 of 4, then 0 of 8 held-out known-text tiles read as rows, with at most 1 letter against a bar of 10. The pipeline as built never showed it could make even one legible row visible on held-out text. Large held-out segments were rendered in grid-aligned pieces, which reproduced full-canvas tiles (Pearson 1.00000, at most 1 grey level).

| number | meaning | source |
|---|---|---|
| held-out tiles rows Y 1 of 4, max n_letters 1 | wave-1 gate | `RULES.md (FL2-WAVE1-RESULT); logs/fl2/wave1_result.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| rows Y 0 of 8, max n_letters 0. NOT SENSITIVE | wave-2 gate on fresh held-out cells, read before any census | `RULES.md (FL2-WAVE2-GATE); logs/fl2/wave2_gate_result.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 12 held-out tiles from 3 segments, rows Y 1 of 12, max n_letters 1 | pooled gate, waves 1-2 | `RULES.md (FL2-WAVE2-GATE)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Pearson 1.00000 for all 4 | piece-rendered tiles vs full-canvas tiles (at most 1 grey level different on a few px) | `logs/sib/pairs0139c/fl2_gate/STATUS.md` (claude/gifted-bell-gavnl5-sib-pairs0139c @ be6d4f134) |

**Lesson.** Run the positive control first, on enough material, and with cell-level ink labels. Without labels, 'reader/model insensitive' and 'these cells are blank' cannot be told apart.

### FL-2 single-tile census, wave 1

**Verdict: NULL**

**Question.** Do any of the top-ink-score 2 x 2 cm tiles on 21 eligible scrolls show >= 10 legible letters to blind readers?

**Method.** 8 tiles per scroll chosen by ink score, plus one rot-90 null per reader. 22 sealed, audited reader jobs. POSITIVE iff rows-Y and n_letters >= max(10, N0 p99).

**Result.** 0 of 168 tiles on 21 scrolls read as rows; the best batch reached 2 letters against a bar of 10, and there were 0 positives. Because the gate was not sensitive, the null was declared uninformative before it was read. The surfaces were later found to cut across windings, so it says nothing about these scrolls.

| number | meaning | source |
|---|---|---|
| 0 of 168 eligible tiles rows Y | census result | `RULES.md (FL2-WAVE1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 2 | max_letters in any eligible batch (threshold 10 everywhere) | `logs/fl2/wave1_result.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Audit 22/22 valid | reader audit | `RULES.md (FL2-WAVE1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A census under a failed positive control buys no information. Declaring that consequence before the read kept the null from being over-interpreted.

### FL-2 single-tile census, wave 2

**Verdict: STOPPED**

**Question.** Should the second wave of single-tile census reads run after a second gate failure?

**Method.** Wave-2 material and 21 reader jobs were staged and committed. The gate was read first, under DECL-FL-2-E3.

**Result.** After the second gate failure, the staged wave-2 census (21 reader jobs, 168 eligible tiles) was not launched. The agent reported to the owner before spending reader budget on a census that the declaration had already marked uninformative.

| number | meaning | source |
|---|---|---|
| 21 jobs are staged and committed in commit A but NOT launched | census held back after the gate failed again | `RULES.md (FL2-WAVE2-GATE item 5)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Reading the gate before the census, and stopping when it fails, saved a wave of reader usage.

### FL-3 stitched-window gate

**Verdict: FAILED**

**Question.** Do 4 x 4 cm stitched windows (the only format whose positive control had passed elsewhere in the programme) make held-out known text legible enough (>= 5 letters + marks)?

**Method.** Up to 16 windows of 2 x 2 adjacent official-model tiles from held-out PHerc0139 segments (at most 4 per segment), with the frozen 'block' brief. SENSITIVE iff >= 1 window is rows-Y with count >= 5.

**Result.** Windows raised sensitivity compared with single tiles (3 of 16 read as rows, max count 4, against 1 of 12 rows and 1 letter). They still missed the declared bar of 5, which was not changed. Verdict: not sensitive.

| number | meaning | source |
|---|---|---|
| 3 of 16 windows read rows Y; max count (letters + marks) 4 | gate result; bar is count >= 5 | `RULES.md (FL3-W1-GATE); logs/fl2/fl3w1_result_gate.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Going up a scale helped but did not reach legibility. The binding limit was the 9 um maps themselves, not the display format.

### FL-3 stitched-window census

**Verdict: NULL**

**Question.** Do any stitched 4 x 4 cm windows on the 22 eligible scrolls reach >= 5 letters + marks?

**Method.** All eligible windows (mean ink score 0.01-0.40, valid >= 0.5) were read in ink-score order: one batch per scroll, a rot-90 N0 from the same batch, POSITIVE iff rows-Y and count >= max(5, N0 p99). The census ran on owner order despite the failed gate.

**Result.** 92 audited reader jobs read 656 windows across all 22 eligible scrolls. 9 read as rows, the maximum count was 4, and there were 0 positives. The null was uninformative by declaration, because the gate had failed, and the underlying surfaces were later shown to cut across windings.

| number | meaning | source |
|---|---|---|
| 656 census windows | windows read, all 22 eligible scrolls | `RULES.md (FL3-W1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| rows Y on 9 of 656 windows; max count (letters + marks) 4 | census result; 0 positives | `RULES.md (FL3-W1-RESULT); logs/fl2/fl3w1_result.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Audit 92/92 valid | reader jobs audited, prompt == brief | `RULES.md (FL3-W1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Scale does not substitute for a passing control. The registry of read windows (672 identities) at least prevented re-reading the same windows in later waves.

### Grand Prize TimeSformer gate on held-out PHerc0139

**Verdict: STOPPED**

**Question.** Is the 2023 Grand Prize TimeSformer (organizer-hosted), run on the same renders, sensitive to held-out known text?

**Method.** Two declared variants: native layers, and layers rescaled to the model's 7.91 um training voxel. At most 16 windows per variant were to be read under the block brief, with a variant chosen only if sensitive. A fp32 vs bf16 precision check ran first.

**Result.** The Grand Prize model was loaded and checked numerically (fp32 vs bf16 Pearson 0.999926). Its known-text gate was then dropped by owner order before any gate read, so the arm went ahead without any sensitivity check. The variant was fixed without data, and every read of this arm was uninformative by declaration.

| number | meaning | source |
|---|---|---|
| "pearson":0.999926 | fp32 vs reference bf16 autocast output on a test crop | `logs/sib/pairs0139c/fl4_gate/STATUS.md` (claude/gifted-bell-gavnl5-sib-pairs0139c @ be6d4f134) |
| GP gate STOPPED by DECL-FL-4-A1 (owner: PHerc0139 gate dropped) | gate never read | `logs/sib/pairs0139c/fl4_gate/STATUS.md` (claude/gifted-bell-gavnl5-sib-pairs0139c @ be6d4f134) |

**Lesson.** Dropping the positive control to save time left every later read of this arm without meaning. The surface defect it might have exposed was found only a day later.

### GP inner-winding census on PHerc0268 (FL-4 waves 41-50)

**Verdict: VOID**

**Question.** Do whole-segment Grand Prize model windows on PHerc0268 inner-winding surfaces show >= 5 letters + marks?

**Method.** Inner-winding seeds were grown (100 generations), rendered and inked with GP variant B in both directions. Whole-segment windows were read blind under the block brief and bar, by fleet lanes and by local compute.

**Result.** The arm was halted after 43 audited window reads, and every read was declared void. The grower had run without its normal-grid data, so it grew the same 11.667 cm2 square regardless of the CT, cutting across windings (median |cos| 0.14-0.40 vs 1.00 on a synthetic control). The material was meaningless. The declared seam-consistency check between overlapping segments has no recorded result.

| number | meaning | source |
|---|---|---|
| all FL-4 reads (FL4-W41 ... W50, 43 items) are VOID as tests of text | voided after the surface check | `RULES.md (DECL-FL-4-A5)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| every segment is the same 198x198 x step-20 square (11.667 cm2) | data-independent growth: every candidate accepted | `RULES.md (DECL-FL-4-A5)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** When every grow gives an identical area, treat it as a red flag and check it. A self-intersection plus area gate cannot detect a surface that ignores the data.

### GP inner-winding lanes on PHerc0490A

**Verdict: STOPPED**

**Question.** Do Grand Prize model outputs on PHerc0490A inner windings show text?

**Method.** The same FL-4 kit ran on PHerc0490A in lanes fl-pilot, fl-pherc0175b, fl-pherc0483b, fl-pherc0846b, census and pairs0139c.

**Result.** Lanes grew and inked several PHerc0490A inner-winding segments, but reading was narrowed to PHerc0268 when usage ran low. No PHerc0490A output was ever read. The surfaces came from the same defective grower settings.

| number | meaning | source |
|---|---|---|
| PHerc0490A FL-4 outputs are not read. | reading limited to PHerc0268 by declaration | `RULES.md (DECL-FL-4-A3 item 1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| NOT STARTED | fl-pherc0490a lane's FL-4 run, held pending owner permission | `logs/sib/fl-pherc0490a/fl4/PHerc0490A/STATUS.md` (claude/gifted-bell-gavnl5-sib-fl-pherc0490a @ e52e2c1ac) |

**Lesson.** Compute spent without a read plan is lost. Scope reading before fanning out compute.

### Normal-grid grows and the radial sheet gate (ring of 8 patches)

**Verdict: FAILED**

**Question.** With the organizers' normal grids supplied, do grown patches follow one sheet, and does a radial-normal gate certify this?

**Method.** 8 seeds around one winding band were grown for 60 generations with normal grids. A declared gate followed: median |cos| >= 0.8, frac > 0.8 >= 0.7, radial spread < 2 mm per cm. Passing patches got renders and GP maps; then a human cross-section check on raw CT.

**Result.** Supplying normal grids fixed the gross defect (median |cos| 0.93 vs 0.16), and 2 of 8 patches passed the strict gate. A raw-CT cross-section then showed even a passing patch stays on one layer between cracks and jumps layers at cracks. A jumped surface still faces outward, so the radial gate cannot see it, and an automated on-prediction score scored good and jumped patches the same. The GP model marked 46-59 % of every patch as ink. The ring maps were declared void.

| number | meaning | source |
|---|---|---|
| median \|cos\| 0.93, frac>0.8 0.76 | normal-grid test grow passes the gate (old kit 0.16) | `RULES.md (DECL-FL-4-A6)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "pass":false | patches i97 and i100 also fail the strict gate, so 2 of 8 pass in total | `logs/fl4t/ring1/i97/sheet_gate.json; logs/fl4t/ring1/i100/sheet_gate.json` (claude/gifted-bell-gavnl5-fl4t @ a250ae8c2) |
| good i98 0.676, failed i103 0.676, old broken surface 0.628 | an automated on-prediction test does not discriminate | `RULES.md (DECL-FL-4-A7-E2)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| the GP model marking 46-59% of every patch as ink | GP output saturates on this scan | `RULES.md (DECL-FL-4-A8)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 43 LLM reads (A5) and 9 GP maps (A7) are void | consequence | `RULES.md (DECL-FL-4-A8)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** No numeric gate tested here certifies sheet-following on a crushed scroll; a human cross-section check is needed. A model that marks half of every patch as ink gives no usable signal on that scan.

### Row-structure score calibration

**Verdict: FAILED**

**Question.** Can an automatic row-periodicity score (3.5-8 mm line pitch) separate known-text tiles from cross-winding junk well enough to select candidates?

**Method.** Positive set: 112 known-text PHerc0139 tiles. Null set: 144 cross-winding PHerc0268 tiles. SENSITIVE iff >= 25 % of positives exceed the null p99. The thresholds were in the tool header before the calibration ran.

**Result.** Only 1.8 % of known-text tiles beat the junk tiles' 99th percentile, against a bar of 25 %. At 2 cm scale, fibre and crush periodicity scores as high as text. The score selected nothing and was reported only. After this, the push had no automated candidate selector.

| number | meaning | source |
|---|---|---|
| 0.018 (bar 0.25) | fraction of positives above the null p99 | `RULES.md (FL5-ROWSCORE-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 28.0539 | null p99 score (null_p99) | `logs/fl4t/fl5_rowscore_calibration.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 7.47 | positive p25 score (gate_p25) | `logs/fl4t/fl5_rowscore_calibration.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Calibrate a cheap detector against realistic junk before relying on it. Periodicity from papyrus structure looks like text lines.

### ink_9um on normal-grid PHerc0268 patches (three winding bands)

**Verdict: NULL**

**Question.** Do official-model maps on normal-grid patches across three PHerc0268 winding bands show rows or strokes?

**Method.** Patches were grown on three bands, rendered, inked with ink_9um in both directions and unrolled per band into one strip. The orchestrating agent triaged montages by eye; no numeric bar was declared.

**Result.** 16 patches on three windings gave uniform-speckle maps and 0 candidates. The render centre layers showed fibres radiating from the seed, so the surfaces were not flat on one sheet and the null carries no weight. Triage was visual, by the orchestrating agent, with no pre-declared numeric bar.

| number | meaning | source |
|---|---|---|
| 16 own normal-grid patches on three windings | material | `RULES.md (FL6-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0 candidates | outcome; renders not flat (fibres radiate from the seed), maps uniform speckle | `RULES.md (FL6-RESULT; DECL-FL-6 item 1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Without a valid surface and a declared bar, visual triage of ink maps can only report a null.

### Official-model screen on organizer-published segments (PHerc0800, PHerc1203)

**Verdict: NULL**

**Question.** With this project's grower removed from the chain, do official ink_9um maps on organizer segments of two eligible scrolls show text-like structure?

**Method.** 6 PHerc0800 organizer surface volumes and 20 PHerc1203 organizer tifxyz segments (rendered here) were inked with ink_9um in both directions. Rotated full-resolution views and montages were triaged by the orchestrating agent.

**Result.** All 26 organizer sheets (6 + 20, 1.7-4.1 cm wide, flat fibre weave) gave sparse blobs or fine speckle, with no row alignment and no strokes, and unrelated forward and reverse maps: 0 candidates. Either these patches carry no ink or the public models do not transfer to these scans; the data cannot tell which.

| number | meaning | source |
|---|---|---|
| 6 of 6 organizer surface volumes | PHerc0800 coverage; maps sparse (frac>=0.5 0.02-0.06), 0 candidates | `RULES.md (FL6-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| PHerc1203 is now 20 of 20 with 0 candidates | PHerc1203 coverage | `RULES.md (FL6-RESULT-A1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| VERDICT: no First Letters candidate exists in this project. Nothing is submittable. | push-level conclusion | `RULES.md (FL6-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Using organizer segments removes the surface confound, but a null from a transferred model is still not evidence of blank papyrus.

### Two-model agreement test on a PHerc0800 sheet

**Verdict: NULL**

**Question.** Do ink_9um and the Grand Prize model mark the same places on an organizer sheet, beyond rotation/flip controls?

**Method.** Pearson r of 0.5 mm-smoothed maps, compared against rot180, flipud and fliplr controls of the same pair.

**Result.** The two models barely agreed beyond the controls (r 0.134 vs a best control of 0.097). The test gave no evidence of ink-like features shared by both models.

| number | meaning | source |
|---|---|---|
| 0.5 mm-smoothed Pearson r = 0.134 | true alignment | `RULES.md (FL6-AGREE-RESULT); logs/fl4t/sv0800_i1_agree.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| control max 0.097 | best control | `RULES.md (FL6-AGREE-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Cross-model agreement against geometric controls is a cheap sanity check, but it needs a pre-declared threshold and more than three controls to be decisive.

### Grand Prize model on the largest PHerc1203 organizer sheets

**Verdict: INCONCLUSIVE**

**Question.** Does the Grand Prize model, compared with ink_9um, show structure on the five largest PHerc1203 organizer sheets?

**Method.** GP variant B forward on lanes. Triage by eye, plus the agreement test against ink_9um with rotation/flip controls.

**Result.** The Grand Prize model finished on 2 of the 5 planned sheets before the deadline. Agreement with ink_9um was recorded against rotation/flip controls, but no agreement threshold had been declared, and the record drew no candidate from either model. The run was incomplete and had no pre-registered bar.

| number | meaning | source |
|---|---|---|
| i16, i17, i19 did not finish in time | only 2 of 5 planned sheets completed | `RULES.md (FL6-GP-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| No candidate from either model. | recorded outcome | `RULES.md (FL6-GP-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Declare the decision rule for an agreement statistic before computing it; otherwise the number cannot be acted on.

### Raw-density view of organizer sheets

**Verdict: NULL**

**Question.** Do raw-CT centre layers of organizer sheets show letter-shaped density contrast without any ink model?

**Method.** Local-mean-removed (1 mm), contrast-stretched centre layers of 6 organizer sheets, inspected at full resolution by the orchestrating agent.

**Result.** The layers showed fibre weave with cracks, voids and 1-3 mm blotches aligned with fibres or cracks, and no rows. The organizer segments also drift off-sheet at their edges. 0 candidates.

| number | meaning | source |
|---|---|---|
| The raw-density channel yields no candidate. | outcome on 6 sheets (4 PHerc1203, 2 PHerc0800) | `RULES.md (FL6-RAWDENSITY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A model-free channel is a useful cross-check, but at 8.6-9.4 um it showed no letter-scale contrast here.

### Census lane: tracing seed plan for 11 eligible volumes

**Verdict: TOOL**

**Question.** Can a geometry-only census (CT masks, surface prediction, normal grids) plan tracing seeds, centres and sync costs for the 11 eligible 9.362 um volumes before any tracing?

**Method.** Mask shape from pyramid level 4. Centres from the official umbilicus or the mask centroid, calibrated where an umbilicus exists. Seeds in 20 z-levels x 3 angles, snapped to the surface prediction. A sheet-walker duplicate estimate validated on organizer segments. Normal-grid sync and time estimates.

**Result.** The lane delivered seed files for all 11 volumes, a tractability ranking and run sheets for the top 3. The mask centroid lies about 0.14-0.21 r_eq (median) from the official umbilicus, so seed wrap fractions are uncertain on oval scrolls. The pre-trace duplicate estimate is unreliable (AUC 0.60), so the binding duplicate test was deferred until after tracing. Later the lane also served as the second PHerc1203 worker in the First Letters fleet.

| number | meaning | source |
|---|---|---|
| 654 of 660 planned seeds placed | seed plan coverage | `logs/sib/census/REPORT.md` (claude/gifted-bell-gavnl5-sib-census @ d941473f6) |
| AUC of \|dr\| is 0.60 | pre-trace duplicate walker: low reliability | `logs/sib/census/REPORT.md` (claude/gifted-bell-gavnl5-sib-census @ d941473f6) |

**Lesson.** Validate a cheap geometric proxy (centroid, sheet walker) against official ground truth before relying on it. Here one passed with caveats and one was labelled low-reliability.

### PHerc0139 training-pair builders (pairs0139, pairs0139b)

**Verdict: STOPPED**

**Question.** Build 9 um to 2.4 um training pairs on PHerc0139 (D2 programme, not First Letters).

**Method.** Exclusion lists, mesh-affine frame checks and a gated pair build, split across two sessions with a handover file.

**Result.** These lanes belong to the training-pair (D2) work, not First Letters, and are listed for completeness. The primary held on a direct stop and the follow-on never received its handover, so no PHerc0139 pair set was finished. Frame checks run before the hold were clean (render vs organizer NCC 0.996).

| number | meaning | source |
|---|---|---|
| HOLD: owner go-ahead needed in this session. | pairs0139 stopped on a direct owner stop; relayed resume notices were not treated as lifting it | `logs/sib/pairs0139/ASK.md` (claude/gifted-bell-gavnl5-sib-pairs0139 @ 580d5241c) |
| PART 2 was not started. | pairs0139b waited 6 h for a handover that never came | `logs/sib/pairs0139b/ASK.md` (claude/gifted-bell-gavnl5-sib-pairs0139b @ 4ad9cf99e) |

**Lesson.** A handover design with a single upstream session stalls entirely when that session holds.

### PHerc0814 training-pair builders (pairs0814, pairs0814b)

**Verdict: TOOL**

**Question.** Build gated 9 um to 2.4 um training pairs on PHerc0814 (D2 programme, not First Letters).

**Method.** Per-segment blocks of 384 px patches. PASS requires CT NCC >= 0.8 and >= 7 of 9 sub-windows aligned within 1 px. The work was split between two sessions by handover.

**Result.** This is D2 material, listed for completeness. Both halves finished: about 36-43 % of candidate patches passed the CT-correlation and alignment gates. pairs0814b was later reused as a First Letters worker (23 PHerc1545 segments tiled) and as an FL-4 lane.

| number | meaning | source |
|---|---|---|
| 235 (43.1 %) | PASS patches of 545 candidates in the handed-over half | `logs/sib/pairs0814b/REPORT.md` (claude/gifted-bell-gavnl5-sib-pairs0814b @ 694b3fca0) |
| 149 PASS (36 %) | PASS rows in the primary half | `logs/sib/pairs0814b/REPORT.md` (claude/gifted-bell-gavnl5-sib-pairs0814b @ 694b3fca0) |

**Lesson.** Gated pair building with re-derivable PASS flags (all 545 recomputed and matched) makes split work auditable.

### PHerc0268 mass ink run (separate repository)

**Verdict: FAILED**

**Question.** Was the first-pass ink signal of the later PHerc0268 mass ink run (separate repository) ink?

**Method.** Covered in the private PHerc0268 repository; the artifact it uncovered is Result 1 of this release. Recorded here only as the outcome of that run.

**Result.** The PHerc0268 mass run's first-pass ink signal turned out to be a blank-margin artifact of strip inference; no letters were claimed. The pre-registered positive-control test of that artifact and its partial fix are Result 1 of this release (stripqc; README and docs/RESULTS.md).

| number | meaning | source |
|---|---|---|
| Verdict: no letters are claimed. | mass-run verdict: the run's ink signal was traced to a blank-margin artifact | `docs/FL_SEARCH.md (PHerc0268 repository)` (pherc0268 @ 6c989b9) |

**Lesson.** See Result 1 (stripqc) in the README and docs/RESULTS.md.

## Geometry: registration, handedness, flattening, umbilicus, unrolling, spiral fits

25 Sep to 14 Oct 2026 · 27 experiments · 4 passed · 15 failed · 1 null · 3 inconclusive · 1 void · 1 stopped · 1 tool · 1 unknown

This family built and tested the coordinate machinery that every ink read depends on: cross-scan CT registration, mirror-state (handedness) conventions, flattening distortion and, for one crushed scroll (PHerc0268), the umbilicus, sheet tracking and spiral-fit unrolling. Registration mostly worked. One scroll passed only after a pre-registered non-affine model replaced a failed affine, a second rescan passed its affine bars and a third missed the correlation bar by 0.006. A geometric handedness rule passed synthetic and internal-consistency checks, but blind readers could not tell mirrored maps from normal ones (both listed under Reading and its calibration). Flattening bars turned out to be unreachable in curved regions. On PHerc0268, every umbilicus estimator, local sheet-identity tracker and spiral-fit surface failed its declared bars or controls, so no validated unrolled surface was produced.

### CT-only winding-sense estimator

**Verdict: FAILED**

**Question.** Can the inward rotation sense (and hence up/down) be estimated from the pitch angle of sheets in axial CT slices, without traced meshes?

**Method.** Structure-tensor sheet tilt against the circumferential direction, with a harmonic fit to remove centre-error and crushing bias. It was validated on synthetic spirals and then applied to 16 slices of a known-text scroll with the official umbilicus as centre.

**Result.** A CT-only estimator of winding sense worked on synthetic spirals but failed on real data. Per-slice signs split 8/8 and the scatter was about 20 times the expected signal, and an earlier run gave the wrong sign on a second scroll. The 26-volume run was stopped and no CT-only up/down claim was made.

| number | meaning | source |
|---|---|---|
| split 8 positive / 8 negative | per-slice sign of the estimated pitch term on real data | `logs/sib/handed/REPORT.md (section 12.2)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |
| about 20 times the signal | per-slice scatter relative to the expected pitch term | `logs/sib/handed/REPORT.md (section 12.2)` (claude/gifted-bell-gavnl5-sib-handed @ 81d525859) |

**Lesson.** Real sheet deformation swamps the tiny pitch angle of a spiral. Winding sense has to come from traced sheets spanning more than one turn.

### PHerc0841 9 um <-> 2.4 um registration, single affine (REG-0841-R1)

**Verdict: FAILED**

**Question.** Does one affine map the 9.366 um scan onto the 2.403 um rescan to the pre-registered held-out bars (median r >= 0.85, RMS <= 1.5 vox, with a half-pitch shifted control)?

**Method.** CT only. Orientation search over 8 flip/remount candidates, z-band by whole-slice NCC, 3-D phase correlation on 24 fit patches, then 16 new held-out patches pre-registered before analysis. The control shifted the transform by half the local sheet pitch.

**Result.** A single affine between the two scans failed both pre-registered held-out bars (median r 0.724, RMS 1.92 voxels), while the shifted control passed (16/16). Per-patch local shifts reached a median NCC of 0.881, so the failure lies in the model: the inter-scan deformation is smooth but not affine.

| number | meaning | source |
|---|---|---|
| median r 0.724 (min 0.504) | held-out correlation, bar >= 0.85 (FAIL) | `RULES.md (REG-0841-R1); logs/sib/reg0841/reg0841_summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635; claude/gifted-bell-gavnl5-sib-reg0841 commit 487f9e48) |
| RMS 1.92 vox (max 3.38) | held-out residual, bar <= 1.5 (FAIL) | `RULES.md (REG-0841-R1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| median drop 0.405, 16/16 | shifted control drops clearly (PASS) | `RULES.md (REG-0841-R1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.881 | held-out median NCC with a per-patch local shift (shows the data are fine and the model is the limit) | `logs/sib/reg0841/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0841 @ 1bdfd0bae) |

**Lesson.** A pre-registered held-out check with a shifted control separates a bad mapping model from bad data. Correspondences repeated to < 0.25 voxel, so the residual was model misfit. The organizer's own mesh pair is an affine image of itself and is not independent evidence.

### PHerc0841 registration, non-affine model (REG-0841-NA)

**Verdict: PASSED**

**Question.** Does an affine-plus-quadratic field (21 parameters), chosen by leave-one-out on earlier patches only and frozen before new data, meet the same held-out bars on 16 new patches?

**Method.** The model change after the affine failure was disclosed in the record. The model was selected by LOO on the 40 earlier correspondences, frozen and pushed, and then validated on 16 new check patches pre-registered in prereg_na.md, with bars and the half-pitch control unchanged.

**Result.** After the affine failed, a smooth non-affine field chosen by leave-one-out on old patches only and frozen before new data passed every pre-registered bar on 16 fresh patches (median r 0.863, RMS 0.977 voxels, control clear on 15/16). It also showed that the organizer's canvas mapping is off by about 1.2 voxels (median), which is negligible at letter-matching tolerances.

| number | meaning | source |
|---|---|---|
| median r 0.863 (min 0.563) | held-out correlation, bar >= 0.85 (PASS) | `RULES.md (REG-0841-NA); logs/sib/reg0841na/reg0841na_summary.json (sha256 9d6779bf...)` (claude/gifted-bell-gavnl5 @ a1f9f4635; claude/gifted-bell-gavnl5-sib-reg0841 commit 0fcf1e0c) |
| RMS 0.977 vox (max 1.47) | held-out residual, bar <= 1.5 (PASS) | `RULES.md (REG-0841-NA)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| median drop 0.695 (15/16 clear) | shifted control (PASS) | `RULES.md (REG-0841-NA)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| \|D\| median 1.20, p95 2.07, max 2.84 | offset of the organizer canvas mapping at 288 training-pool tiles (9 um vox) | `RULES.md (REG-0841-NA)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** When a declared model fails, a replacement is admissible only if it is chosen on old data, frozen, and checked on fresh pre-registered material. Disclosing the deviation keeps the pass honest.

### PHerc0841 CHAIN VALID preparation

**Verdict: STOPPED**

**Question.** Does our 2.4 um ink chain on 0841 reproduce the organizer map and human labels (r >= 0.60 and AUC >= 0.90 in one order, AUC <= 0.60 in the other) using the validated registration?

**Method.** Meshes were mapped with the frozen non-affine field, a fail-closed exclusion clearance from the sealed benchmark was applied, the inference driver was copied from the 2 um chain lane, and metrics were tested on synthetic data. The runner refuses to start without an explicit GO marker.

**Result.** The registered-chain validation on this scroll was fully prepared: meshes mapped with the validated field, exclusion clearance from the sealed benchmark checked fail-closed, and metrics unit-tested. It stopped waiting for a go-ahead, and no chain result exists.

| number | meaning | source |
|---|---|---|
| STATUS: WAITING FOR GO | preparation complete; the chain run never executed | `logs/sib/reg0841/chainvalid/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0841 @ 1bdfd0bae) |
| The chain check itself is still to run. | last statement in the main record | `RULES.md (REG-0841-NA)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Gating a costly run behind an explicit GO marker prevented any accidental ink map near sealed material, but the record shows the gate was never released.

### PHerc0009B per-segment registration and re-trace grouping (reg0009b)

**Verdict: INCONCLUSIVE**

**Question.** Can each 2.401 um reference map be placed on the 8.64 um canvas within 2 px (whole-segment NCC >= 0.80), and which segments are re-traces of the same papyrus?

**Method.** Band-passed tile NCC of the 8.64 um surface volume against the mapped 2.4 um volume, with a per-pixel depth correction and an offset null. Re-trace grouping used the fail-closed CORR-RETRACE-RULE (vertex or point-to-surface distance bins). Dense reference-ink windows were then counted and deduplicated in 3-D.

**Result.** All 18 fragment segments registered within 2 px once a per-pixel depth correction was applied (13 of 18 failed at nominal depth). The fail-closed re-trace rule grouped them into 6 papyrus units, all 28 same-papyrus pairs coming from the point-to-surface form. The gate was set by the builder, and the depth correction carries some selection optimism that no held-out depth check bounded. No bar was declared for this gate and the orchestrator never adopted it, so the result is recorded as inconclusive rather than passed.

| number | meaning | source |
|---|---|---|
| 18 / 18 segments pass | registration gate after depth correction | `logs/sib/reg0009b/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0009b @ f1b3cbf19) |
| at the nominal slab centre 13 of 18 are below NCC 0.80 | without depth correction most segments fail | `logs/sib/reg0009b/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0009b @ f1b3cbf19) |
| 28 SAME | re-trace pairs among 119 candidate pairs, all found by the point-to-surface form (vertex form found 0) | `logs/sib/reg0009b/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0009b @ f1b3cbf19) |
| 6 papyrus units | connected components of re-trace pairs | `logs/sib/reg0009b/REPORT.md` (claude/gifted-bell-gavnl5-sib-reg0009b @ f1b3cbf19) |

**Lesson.** Nearest-vertex re-trace tests on coarse meshes miss true re-traces, while point-to-surface distance catches them. Slab depth matters as much as in-plane shift for cross-resolution registration.

### PHerc1203 9.362 <-> 2.403 um CT affine (regrescan)

**Verdict: PASSED**

**Question.** Does one affine register this scroll's 9 um scan to its 2.4 um rescan to the held-out bars (median r >= 0.85, RMS <= 1.5 vox on 16 new patches, shifted control clear)?

**Method.** Exhaustive flip/mirror/rotation search, coarse z-band NCC, mid- and full-resolution 3-D phase correlation on 24 fit patches, and a check on 16 new patches committed before any level-0 read, with a half-pitch normal-shift control.

**Result.** A single affine registered this scroll's two scans on 16 fresh patches (median r 0.879, RMS 0.732 voxels, control clear 16/16), and a round-trip test was exact to < 0.5 voxel. A translation-only model would have been about 4x worse (RMS 2.899).

| number | meaning | source |
|---|---|---|
| 0.879 | held-out median r (PASS) | `logs/sib/regrescan/REPORT.md; summary.json heldout_median_r 0.8789436251344623` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |
| 0.732 | held-out RMS in 9 um vox (PASS) | `logs/sib/regrescan/REPORT.md` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |
| translation-only RMS 2.899 vox (max 5.101) vs affine 0.732 vox | the affine terms are needed | `logs/sib/regrescan/REPORT.md` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |

**Lesson.** Search flips and remounts exhaustively before fitting. Pre-committing the check patches made the pass meaningful.

### PHerc0846A 9.362 <-> 2.403 um CT affine (regrescan)

**Verdict: FAILED**

**Question.** Same affine registration and bars as for PHerc1203, on a second eligible scroll.

**Method.** Same pipeline. Two fit iterations were checked on the same 16 pre-fixed patches. Both are reported, and the orchestrator named iteration 1 the result of record.

**Result.** The affine for this scroll missed the held-out correlation bar narrowly (median r 0.8439 against 0.85), while RMS (0.72 voxels) and the control passed. A per-patch diagnostic (0.878) suggests local non-affine misfit, but no non-affine model was pre-registered or run.

| number | meaning | source |
|---|---|---|
| 0.8439 | held-out median r with the specified fit iteration 1 (bar 0.85, FAIL) | `logs/sib/regrescan/REPORT.md` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |
| 0.720 | held-out RMS, fit iteration 1 (the result of record; iteration 2 gave 0.718); bar 1.5 | `logs/sib/regrescan/REPORT.md` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |
| 0.8784 | median r at each patch's own optimum (diagnostic only) | `logs/sib/regrescan/REPORT.md` (claude/gifted-bell-gavnl5-sib-regrescan @ da0a72fbb) |

**Lesson.** Report both fit iterations when the pipeline runs one that was not committed first. Here both failed, so the verdict did not depend on the choice.

### FLAT-1 flattening method selection

**Verdict: PASSED**

**Question.** Which flattening (official ABF++ vc_flatten, SLIM, ARAP) keeps >= 93.1 % of quads within +-5 % of their 3-D edge lengths on 4 of 5 seeded 4 cm^2 rectangles?

**Method.** Five code-selected 4.00 cm^2 rectangles on known-text organizer meshes (9.362 um), all methods on the identical triangulation, with the unflattened levelled grid as a baseline. Secondary runs used 2.4 um meshes and whole meshes.

**Result.** By the pre-declared rule, the official ABF++ flattening was adopted (5/5 rectangles at 98.59-99.67 %), and SLIM and ARAP also passed. The test turned out not to discriminate, because the unflattened grid already scored 97.39-99.55 % on these gently curved rectangles. The run also documented an ABF++ failure mode in which the map collapses on a whole mesh.

| number | meaning | source |
|---|---|---|
| 98.59 to 99.67 % | vc_flatten quads within +-5 % on the 5 primary rectangles (5/5 pass; adopted by rule) | `logs/sib/flat1/REPORT.md; flat1_summary.json sha256 13366219...` (claude/gifted-bell-gavnl5-sib-flat1 @ b5594d021) |
| 97.39 to 99.55 % | unflattened grid baseline on the same rectangles (the test does not discriminate) | `logs/sib/flat1/REPORT.md` (claude/gifted-bell-gavnl5-sib-flat1 @ b5594d021) |
| 27.90/46.55 | whole-mesh ABF++ collapse case (% within +-5 % over all quads / over the region) | `logs/sib/flat1/REPORT.md` (claude/gifted-bell-gavnl5-sib-flat1 @ b5594d021) |

**Lesson.** A method-selection test needs a no-op baseline. If doing nothing passes, the test says nothing about the method.

### FLAT-1 hard set (most curved windows)

**Verdict: FAILED**

**Question.** Do any flattening methods meet the 93.1 % isometry bar on the code-selected most curved or least isometric 4 cm^2 windows?

**Method.** Every fully valid 4 cm^2 window of 38 bank meshes was scored by mean angle defect and grid non-isometry, and the top 5 by each score were flattened by all methods and the grid baseline. Eligible-scroll meshes were too small and were tested at 1 cm^2 only.

**Result.** On the 10 most curved windows no method reliably met the bar (ABF++ 0/10, SLIM 3/10, ARAP 4/10, grid 0/10). Distortion rose monotonically with intrinsic curvature, and a margin-trim fallback never changed a verdict. SLIM never flipped a triangle and scored at least as well as ABF++ in every comparison.

| number | meaning | source |
|---|---|---|
| vc_flatten passes 0/10 (22.2 to 92.8 %), SLIM 3/10 (77.5 to 97.6 %), ARAP 4/10 (77.4 to 97.7 %), and the grid baseline 0/10 (70.8 to 89.5 %) | pass counts on the 10 hard windows | `logs/sib/flat1/REPORT.md` (claude/gifted-bell-gavnl5-sib-flat1 @ b5594d021) |

**Lesson.** Distortion in crushed or curved papyrus is intrinsic (Gauss curvature), so no flattening method or trimming outside the region can remove it. Bars must be set per region, not globally.

### PHerc0268 frame (roll-axis) determination

**Verdict: INCONCLUSIVE**

**Question.** Along which volume axis does the crushed roll's former axis lie?

**Method.** Main record: orthogonal-cut inspection plus a level-4 3-D structure tensor (UMB-GEOMETRY-RESULT). Spiral lane (U2): body inertia, structure-tensor normals tested for radial alignment about a z-centroid, and catalogue conventions.

**Result.** Two lanes reached incompatible frame verdicts from the same scan. The main record read the scroll as a roll flattened with its former axis along the volume's y axis. The spiral-fitting lane concluded with high confidence that the axis is z and that the roll is crushed along its own length (telescoped), which makes slices look face-on. The spiral fleet used the z frame, the main record never retracted its y frame, and it had already voided an earlier centroid axis (and the seed grids) built on the z-axis assumption as being in the wrong frame.

| number | meaning | source |
|---|---|---|
| \|n_z\| median 0.76 | layer normals mostly along z, which the main record read as an axis along y | `RULES.md (UMB-GEOMETRY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| mean \|cos(n_yx, radial)\| = 0.900 | in-plane normals radial about a z axis (random would give 0.637) | `docs/units/U2-umbilicus.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| Roll axis \| **z** (volume axis 0). Not y, not x. \| high | U2 verdict | `docs/units/U2-umbilicus.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Settle the frame with several independent tests (body shape, radial alignment of normals off-centre in each direction, catalogue conventions) before building an axis or tracker on it. A face-on texture in slices can come from axial crushing as well as from flattening.

### Umbilicus pipeline DECL-UMB-1: phantoms

**Verdict: FAILED**

**Question.** Do the structure-tensor umbilicus estimators recover a known axis on procedural phantoms within the declared bars (clean <= 0.15 mm, crushed <= 0.5 mm, kink within 1.1 mm, no false confidence)?

**Method.** Circular spiral phantoms (curved axis, 2:1 crush, holes, debris, rings, noise; 4 seeds) and a flattened-roll phantom (aspect 0.25), tested with concurrency and topological (director-index) estimators. Seeds 1-3 were run after the declaration.

**Result.** On circular phantoms the estimators met the error bars (clean max 0.072-0.087 mm). A 2 mm kink was missed by the concurrency estimator and found by the topological one. On a flattened-roll phantom both failed the 0.15 mm bar (topological median 0.437 mm, concurrency median 1.34 mm), so the pipeline could locate the core region to only one to three layer spacings.

| number | meaning | source |
|---|---|---|
| clean-zone max error 0.087 / 0.072 / 0.072 mm (bar <= 0.15: PASS) | circular phantoms, concurrency estimator | `RULES.md (UMB-PHANTOM-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| median error 0.437 mm, p90 1.03 mm, max 1.36 mm. Bar <= 0.15 mm: FAIL | flattened-roll phantom, topological estimator | `RULES.md (UMB-PHANTOM-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| clean median 1.34 mm, max 7.9 mm: FAIL | flattened-roll phantom, concurrency estimators | `RULES.md (UMB-PHANTOM-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Phantoms must match the real geometry class. Estimators that pass on round spirals fail on flattened stacks, where layer normals are parallel and lever arms amplify folds.

### Umbilicus of PHerc0268 at survey resolution (UMB-PHERC0268-RESULT)

**Verdict: FAILED**

**Question.** Can a single umbilicus line be delivered for PHerc0268 with confidence >= 0.5 on >= half the in-domain sections?

**Method.** Topological director-index core finding on 95 level-3 sections (69 um), with point-concurrency as a cross-check and a fold-defect census tracked along the section axis.

**Result.** No single umbilicus line could be delivered. A stable core was found in at most 1 of 86 sections against a 50 % coverage bar, and loops enclosed zero net winding charge where a nested roll should give +1. The 69 um survey scale could not resolve individual sheets, and the fold interpretation drawn from it was later withdrawn.

| number | meaning | source |
|---|---|---|
| coverage 1/86 against the declared >= 0.5 | sections with a stable core; single axis NOT DELIVERED | `RULES.md (UMB-PHERC0268-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "value": 0.0 | coverage_clean_frac in the validation record (0 clean of 95 slabs) | `logs/umb/PHerc0268/validation.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 14,176 | director defects over the scroll at R = 3 mm | `RULES.md (UMB-PHERC0268-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Make sheet-level claims only at the scan's native voxel size. Coarse levels resolve packets of windings and seams, not sheets, so they can only locate windows.

### Native-resolution umbilicus DECL-UMB-2 (U-turn operator)

**Verdict: FAILED**

**Question.** Can the innermost U-turn of each edge column be found at 8.64 um so that left/right core heights agree, crossings balance, and a phantom precondition (B6) passes?

**Method.** Hessian ridge centrelines and ridge-tangent streamlines in edge windows, an innermost empty-interior U-turn rule, and a central-strip crossing count. The B6 phantom suite (6 flattened-roll cases x 8 sections) is a precondition for reading the real output, and an operator self-test runs before every run.

**Result.** The native-resolution operator failed its own phantom precondition (0 of 48 phantom sections pass; core height errors of 3-4 mm in half the cases; innermost apex never resolved). On real data the two edge columns disagreed by 14-43 mm at all 3 sampled positions. The umbilicus stays NOT DETERMINED, and no umbilicus number from this operator was used downstream.

| number | meaning | source |
|---|---|---|
| n_sections": 48, "n_pass": 0 | B6 flattened-roll phantom suite: 0 of 48 sections pass | `logs/umb/phantom_native/summary.json` (claude/gifted-bell-gavnl5-fl4t @ a250ae8c2 (RULES cites 19d299bbd)) |
| B1 agreement <= 2 pitches: 0/3 | real data at 3 positions: left and right core heights disagree by 14-43 mm | `RULES.md (E2E-1-RESULT, S1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| B5 coverage 0 (fail) | no core delivered on the sampled range | `RULES.md (E2E-1-RESULT, S1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Run the phantom precondition before reading real output. The phantom showed that the operator cannot find the innermost turn even when the geometry is known.

### Unrolling design DECL-UNR-1: X0 survey and X1 v0 tracker self-test

**Verdict: FAILED**

**Question.** What are the real sheet thickness and pitch at native resolution, and does the version-0 per-section sheet tracker resolve sheets?

**Method.** Native-resolution peak statistics on one 16-section edge slab, a level-2 census (20 rows planned), and a version-0 per-section 3-MAD peak tracker run on a code-path phantom and one real slab, against sanity bars.

**Result.** Native measurements replaced the assumed sheet geometry (sheet width median 122 um, pitch median 380 um at the scroll edge). The coarse census stopped at 8 of 20 rows. The version-0 tracker passed its phantom but failed on real data: spacing 27.5 voxels against a 44-voxel target and ridge coverage 0.16, so it tracked plies and fibre bundles rather than sheets. The staged X1-X6 pipeline never went past this point, and a version-1 tracker was never declared.

| number | meaning | source |
|---|---|---|
| median 122 um | native sheet width (edge window) | `RULES.md (UNR-X0-SURVEY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| median 380 um | native vertical pitch (edge window) | `RULES.md (UNR-X0-SURVEY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 8 of 20 planned rows | level-2 census stopped by OOM and not resumed | `RULES.md (UNR-X0-SURVEY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| ridge coverage FAIL (0.16) | X1 v0 on real data resolves plies and fibre bundles, not sheets | `RULES.md (UNR-X1-V0-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** High forward/backward agreement (0.96) measures self-consistency, not sheet identity. Sanity bars on spacing and coverage caught that the operator worked at the wrong scale.

### End-to-end band pipeline E2E-1 (trace, mesh, render, ink)

**Verdict: FAILED**

**Question.** Does the pipeline produce a continuous, sheet-centred surface over a 5 mm band of the crushed scroll that passes the geometry bars G1-G5, with a validated ink layer?

**Method.** Orientation-field streamline sheet trace from the best of 219 grid seeds, ridge tracking across sections, mesh checks, a 17-layer render, and the in-house ink model, with forward/reverse and rotation controls. Bars and thresholds were declared before the band result.

**Result.** The pipeline ran end to end at native resolution and produced one tapering 19 mm strip, not a scroll surface. Section coverage (0.053), seam consistency (0.23) and sheet centring (0.61 against 0.90) all failed. The ink model was far below its held-out bars (AUC 0.579), so its output was recorded only as unvalidated model output.

| number | meaning | source |
|---|---|---|
| "G2_coverage_frac": 0.053 | sections covering >= 90 % of the seed trace (FAIL) | `logs/unr/e2e/ (E2E-1 band run) checks.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| G5 (centre brighter than the +-6 layers) 0.61 FAIL (bar 0.90) | surface sits on a sheet ridge for 61 % of samples | `RULES.md (E2E-1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| global_r1 pixel AUC 0.579, AP 0.167, tile AUC 0.575 | ink model on the held-out scroll, bars 0.90 / 0.50 / 0.85 (FAIL) | `RULES.md (E2E-1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| self-intersections 0 (pass) | mesh check | `RULES.md (E2E-1-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Sheet identity in the crushed interior was lost within about 1 mm across sections with per-section operators. Ridge trackers can lock onto crack rims instead of sheets, which is why controls such as the symmetric-flank gate were needed.

### ORD-3 ordered-stack tracker: phantom pilot A (three runs)

**Verdict: FAILED**

**Question.** Does the ordered-stack sheet tracker (row Viterbi, twin competitors, identity invariants) follow one lamina on declared phantoms with no wrong-lamina anchors and >= 90 % coverage?

**Method.** Phantoms with known geometry (three seeds, including typical spacing), injected one-spacing hops and shear lines, and null controls (between-laminae and random positions). Each amendment answered a measured failure and lowered no bar.

**Result.** All three phantom pilots failed. The tracker was accurate wherever it stayed anchored (sub-2-voxel error outside hop windows) but missed one-spacing hops. Rules that revived lost cells raised coverage to 0.45 while raising errors to 24 voxels RMS and wrong-lamina cells to 9,502, and no grammar reached 90 % coverage.

| number | meaning | source |
|---|---|---|
| RMS error on ANCHORED cells 9.63 vox (p95 33.0), 2838 wrong-lamina cells of 43146 anchored | run 1, seed 0 | `RULES.md (ORD3-PILOTA-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| coverage 0.45 (was 0.34), RMS 24.4 vox (was 10.2), 9502 wrong-lamina | run 3: revival rules bought coverage at the cost of identity | `RULES.md (ORD3-PILOTA3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Coverage and identity trade off. Revival across gaps needs a prediction better than half the competitor spacing, and a rigid one-spacing shear in a uniform stack is invisible to geometry-only invariants.

### ORD-3 on the raw native block (pilot B)

**Verdict: FAILED**

**Question.** On raw 8.64 um sections, does ORD-3 carry sheet identity across sections with acceptance margins >= 0.30 over controls, >= 0.80 coverage within 0.28 mm, and detection of injected hops?

**Method.** A 3.3 mm raw block around the seed, with a 4-section step, CLEAN-only export, between-laminae and random-position nulls per row, 20 injected one-spacing hops with unshifted controls, and texture-power and mesh checks.

**Result.** On real sections the tracker lost sheet identity within about 0.3 mm. The acceptance margin over control positions decayed from about 0.45 to under 0.1, 70 % of injected hops went undetected (control false alarm 0.05), and the fibre-texture test had no power. The mesh itself was clean (0 self-intersections).

| number | meaning | source |
|---|---|---|
| minimum within +-0.28 mm 0.275 (bar 0.80) | CLEAN anchored fraction of seed cells | `RULES.md (ORD3-PILOTB-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| V2 medians over the sweep T-C1 0.077, T-C3 0.128 (bar 0.30) | acceptance margin over between-laminae and random controls | `RULES.md (ORD3-PILOTB-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| detection (flagged or unexported >= 50 %) 0.30, flagged-only 0.0, controls 0.05 false alarm | injected hop detection: 70 % pass unnoticed | `RULES.md (ORD3-PILOTB-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| >= 0.8 on 0 % of rows (bar 80 %) | fibre-texture identity test has no power at this resolution | `RULES.md (ORD3-PILOTB-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Per-row 2-D ridge acceptance cannot tell a sheet from its neighbours 8-14 voxels away. The operator's own acceptance did not reveal when it was lost, and only the declared nulls did.

### Band-observability survey of PHerc0268 (OBS-SURVEY)

**Verdict: NULL**

**Question.** Are other regions of the scroll more observable for the local operators than the pilot band (one-step margins >= 0.30 over between-laminae and random positions)?

**Method.** 216 windows (72 positions x 3 depths) over the scroll body, with the pilot's acceptance statistics, twin distances, texture power and motion computed without tracking. The reading rule was declared before data.

**Result.** Every one of 216 windows passed the declared one-step rule, including the band where tracking had already failed, so the rule does not discriminate. The scroll body proved statistically homogeneous for these operators (competitor spacing 8-16 voxels, motion about 1 voxel per 4 sections, texture power below the bar everywhere). No better region exists to move to.

| number | meaning | source |
|---|---|---|
| "observable_frac": 1.0 | all 216 windows pass the declared rule | `logs/unr/obs/summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| min 0.319 / p10 0.391 / p50 0.431 | margin over between-laminae positions | `RULES.md (OBS-SURVEY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| min 0.333 / p50 0.475 / max 0.563 | texture power, below the 0.8 bar in every window | `RULES.md (OBS-SURVEY-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A one-step margin on self-selected strong ridge cells measures that a ridge reappears, not that it can be followed. Validate a screening rule on a case with a known outcome before using it to select regions.

### 3-D sheet-likeness operator for ORD-3 (ORD3-S3)

**Verdict: FAILED**

**Question.** Does replacing the 2-D ridge with a 3-D Hessian sheet-likeness operator improve identity tracking on the phantom and the raw block?

**Method.** The same solver and bars as pilots A and B, with only the ridge field and normal replaced by a 3-D two-scale Hessian with sheet-likeness and in-section-normal gates.

**Result.** The 3-D operator sharpened what it accepted (centring 0.935, passing its bar) but accepted less, and it separated the sheet from neighbours no better (margin 0.06-0.08). Its hop detection rose only together with a 0.40 control false-alarm rate. Together with the survey, this closed the local-operator line on this scroll at 8.64 um.

| number | meaning | source |
|---|---|---|
| V3 min within 0.28 mm 0.157 (0.275) | CLEAN coverage, lower than with the 2-D ridge | `RULES.md (ORD3-S3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| V4 hop detection 0.60 (0.30) but control false alarm 0.40 (0.05): uninterpretable | hop test | `RULES.md (ORD3-S3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| G5 0.935 | sheet centring on the accepted cells (passes 0.90), on fewer cells | `RULES.md (ORD3-S3-RESULT)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A hop detector is interpretable only alongside its unshifted-control false-alarm rate. Here a higher detection rate came with an equally higher false-alarm rate.

### Identity audit of 78 VC3D-grown PHerc0268 surfaces (DECL-E2E-4)

**Verdict: VOID**

**Question.** Do surfaces grown with the established community grower stay on one lamina, as judged by on-peak, clearance and jump statistics, given a declared sensitivity control (surface minus half-spacing-displaced copy >= 0.30)?

**Method.** Per-vertex W3 peak and clearance statistics on each surface and on a copy displaced along the normal by half the local spacing. The run stops by rule if the statistic cannot separate a sheet from the gap beside it.

**Result.** The audit stopped by its own sensitivity rule after 2 of 78 surfaces. The peak statistic scored the surfaces and their half-spacing-displaced controls the same (difference -0.001 against a 0.30 bar), so no surface was read or selected. The peak detector, tuned on edge regions with wide spacing, had no power in the crushed interior.

| number | meaning | source |
|---|---|---|
| "sensitivity_onpeak_surface_minus_control_median": -0.001 | the statistic does not separate surfaces from displaced controls (bar 0.30) | `logs/unr/vc3d_audit/summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "n_audited": 2 | surfaces audited before the sensitivity rule stopped the audit | `logs/unr/vc3d_audit/summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A displaced-copy control run before the full audit saved hours of uninformative statistics. Detectors tuned where sheets are 44 voxels apart do not transfer to regions where they are 8-16 voxels apart.

### Spiral-fit inputs for PHerc0268: umbilicus, axis and outward sense (unit U2)

**Verdict: INCONCLUSIVE**

**Question.** What are the roll axis, an umbilicus curve over the papyrus extent, and the outward winding sense, with evidence?

**Method.** Body inertia and photo, a radial-alignment test of structure-tensor normals, a least-squares curvature centre per 160-slice band with smoothing, radial-alignment maps and polar unwraps as checks, and the catalogue convention for winding sense.

**Result.** The unit delivered an axis verdict (high confidence) and an umbilicus curve of 82 control points. This is a curvature centre, not an identified innermost turn, and two estimators disagree by 2-7 mm at mid heights. The outward winding sense was taken from the catalogue convention because the required CT confirmation came out inconclusive.

| number | meaning | source |
|---|---|---|
| 82 control points | umbilicus curve delivered | `docs/units/U2-umbilicus.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 2–7 mm | disagreement between two independent centre objectives at mid heights (9-14 mm near the ends) | `docs/units/U2-umbilicus.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| **My own reading (required: a sheet followed outward in ≥ 3 sections): inconclusive.** | outward sense not CT-confirmed (taken from the catalogue) | `docs/units/U2-umbilicus.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Record which inputs are measured and which are inherited from metadata. The unit itself found a catalogue example inconsistent with the catalogue's own rule.

### Spiral-fit input tooling: band tracks (U3), distance field (U4), low-z track extractor (T0)

**Verdict: PASSED**

**Question.** Can the published spiral tracks be extracted per band without full download, can the surf-SDT distance field be built on CPU, and can tracks be extracted below the published z range with the organizers' parameters, all exactly?

**Method.** HTTP range reads compared against the full published store by the fit's own loader, the unmodified SDT script compared with an independent recompute, and the organizers' extractor rerun on the overlap with the published tracks.

**Result.** All three input tools reproduced their references exactly: the per-band track store matched the full published store (2,659,851 tracks, SHA-256 identical), the CPU distance field matched an independent recompute voxel for voxel, and the low-z extractor matched all 601,994 published horizontal tracks on the overlap.

| number | meaning | source |
|---|---|---|
| 2,659,851 tracks, 54,717,756 points | band store identical to the full DBM on the test band (SHA-256 match) | `docs/units/U3-tracks.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| An independent recompute matches it voxel for voxel | SDT on one band | `docs/units/U4-sdt.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 601,994/601,994 identical | low-z extractor reproduces published horizontal tracks on the overlap | `docs/BANDS.md (Order 6-A3)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Exact-reproduction checks against published artefacts are cheap and remove a whole class of input doubts before fitting.

### CPU spiral-fit engineering (memory, speed, settings)

**Verdict: TOOL**

**Question.** Can the GPU-oriented spiral fit run per band on 4-CPU, ~15 GB sibling containers, and which settings hold memory flat and reduce time per step without changing results?

**Method.** A fleet experiment matrix (allocator variants, gc per step, sample budgets, window sizes) with per-step RSS and seconds logged, a profiler-driven patch review, and bitwise-identity checks of patched results.

**Result.** The fit was made to run on CPU-only containers. A per-step garbage collection held memory flat, one patch saved time, and a second patch that looked faster in a kernel benchmark was retired after measuring about 40 % slower end to end. A coarser sampling setting was rejected because it undercounted sheet crossings by 4-7 %.

| number | meaning | source |
|---|---|---|
| One `gc.collect()` per step holds RSS flat with unchanged losses | memory-growth root cause and fix | `docs/BANDS.md (Order 6)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 0001–0003 23.55 s/step, +0004 21.93, +0004+0005 30.71 | end-to-end timing; patch 0005 retired as about 40 % slower despite a kernel-only gain | `docs/BANDS.md (Order 6-A4)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 4–7 % undercount | sheet-crossing undercount that rejected a coarser spacing setting | `docs/BANDS.md (Order 6)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Measure speed-ups end to end on the target machine. A kernel-only benchmark taken under contention reversed sign.

### Spiral-fit fleet: do fitted windings lock onto sheets?

**Verdict: FAILED**

**Question.** Do the 2000-step CPU band fits (before and after enabling the track_dt loss) place windings on the papyrus sheets, as judged by phase lock against the surface prediction and by normal orientation against the CT sheet direction?

**Method.** Phase-lock curves of the surface prediction along node normals with per-node random-shift nulls, a CT-contrast profile, and the angle between mesh normals and structure-tensor sheet normals, compared with a published successful fit of another scroll (after its snap and flatten).

**Result.** Raw band fits sat at random phase relative to the sheets (lock 0.98-1.01), and enabling the missing track-attachment loss moved lock by only +0.03. The root cause was orientation: inner windings were about 42 degrees off the sheet direction, against 6 degrees for a successful published fit. Winding indices also did not agree between adjacent band fits (3-15 sheets apart), so the fleet produced no global winding numbering.

| number | meaning | source |
|---|---|---|
| 0.981 | lowest raw-fit phase lock among eight pre-track_dt snapshots (1.0 = random phase) | `docs/POC.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 1.012 | highest raw-fit phase lock among the same snapshots | `docs/POC.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| +0.03 | change in lock after 200 steps of track_dt | `docs/POC.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 42° | median mesh-normal vs sheet-normal angle on inner windings (control fit 6°; random 52-60°) | `docs/POC.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| 3-15 sheets apart | the same winding index in adjacent units lands on different sheets | `docs/FL_SEARCH.md (strip geometry audit)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Copy a recipe's full optimisation schedule, not its step count. A shortened horizon disabled a loss term entirely. Calibrate any positive control: the 2.46 lock first used as a bar came from a post-snap, post-flatten mesh, not raw fit output.

### Proof-of-concept patch: fit -> snap -> render -> ink (PoC v0/v1)

**Verdict: FAILED**

**Question.** Can the chain deliver a sheet-validated 4 cm^2 patch (stitched across band windows) and an ink test on it?

**Method.** Patch winding chosen by a rule written before any image (lowest sheet angle passing the snap gate). Checks: snap onto the surface prediction, a 66-layer render with layer-profile peak and fibre visibility, seam matching across windows, sheet growth with per-tile on-sheet checks, and the ink ensemble with a control on known letters.

**Result.** Only about 0.5 cm² of a single band window showed a validated single-sheet surface. Window seams after snapping were 8-56 voxels, so no stitched sheet existed, and growth to 4.6 cm² left only about 2 cm² on-sheet. Ink tests on the validated area were null, and the first patch was too short (2.2 mm) for a meaningful letter test.

| number | meaning | source |
|---|---|---|
| ≈ 0.5 cm² | area showing continuous single-sheet fibres in PoC v0 (patch only 2.19 mm tall) | `docs/POC.md` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9 (PoC v0 commit 43e91ca)) |
| window seams after snap 8-56 vox (no stitched sheet) | cross-window seams too large to stitch | `poc/v1/seams.json (summary in commit message)` (pherc0268 commit a0774a8) |
| sheet growth to 4.6 cm2 with 9/18 tiles on-sheet (~2 cm2) | grown surface, about half on-sheet | `poc/v1/layer_profile_tiles.json (summary in commit message)` (pherc0268 commit a0774a8) |

**Lesson.** Validate geometry tile by tile before running ink, and size test patches to exceed letter height plus line spacing. Otherwise an ink null carries no information.

### 3-D tracer and on-sheet gate for PHerc0268 surfaces (FL_SEARCH phase 1 geometry engines)

**Verdict: FAILED**

**Question.** Does a 3-D tracer grown from a validated strip stay on one sheet, does an on-sheet tile gate separate real surfaces from displaced copies, and does any existing PHerc0268 surface qualify?

**Method.** Tracer tested on ground truth from a published fit of another scroll. Tile gate tested on that ground truth and on a validated strip against +-8-voxel displaced copies. Orientation audit of the 103 existing PHerc0268 surfaces.

**Result.** The 3-D tracer failed on ground truth (46 % of grown nodes drifted by more than one sheet). The on-sheet gate separated true surfaces from displaced copies well enough for screening only. An orientation audit found no usable surface among 103 existing ones, and showed that an earlier batch of surfaces sat at random orientation, which voided the reads made on them.

| number | meaning | source |
|---|---|---|
| 46 % of grown nodes drift more than one sheet off | tracer on ground truth; tracer NOT FIT | `docs/FL_SEARCH.md (Phase 1)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| w047 34/52 tiles ON, its +8 copy 5/52, its −8 copy 0/47 | gate control on ground truth (usable for screening only) | `docs/FL_SEARCH.md (Phase 1)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |
| No winnable surface exists in the pool. | orientation audit of 103 existing surfaces | `docs/FL_SEARCH.md (Phase 1)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Test a tracer on ground truth from a scroll where the answer is known before growing on an unknown one. Audit the orientation of inherited surfaces before trusting any read made on them.

### Long 10,000-step spiral fits (Order 9 autopilot)

**Verdict: UNKNOWN**

**Question.** Do longer fits (10k steps, track loss from step 3333) converge to sheet-locked windings across the fleet?

**Method.** A one-command autopilot per unit, with snapshots pushed every 1000 steps to the unit branches.

**Result.** Long fits were launched across the fleet, but no convergence or sheet-lock result for them was found in the record available here, so the outcome is unknown.

| number | meaning | source |
|---|---|---|
| 10,000 steps | declared long-fit horizon | `docs/BANDS.md (Order 9)` (pherc0268 claude/gifted-bell-gavnl5 @ 6c989b9) |

**Lesson.** Record the evaluation of a launched run on the shared branch, not only on per-unit branches.

## Tools, infrastructure and operations

24 Sep to 10 Oct 2026 · 19 experiments · 3 passed · 3 failed · 2 inconclusive · 1 stopped · 10 tool

Besides its research questions, Dominion built and released tools. It also ran a blind-reader harness with a decryption and view audit trail, offloaded data from a nearly full disk to a git data branch, and ran a fleet of sibling sessions: 118 registered between 25 September and 2 October and 52 more on 9 October. Six standalone tools were published for the monthly Progress Prizes, three in September and three in October; each passed clean-clone tests and a leak scrub. The log confirms one September entry as submitted, and the prize outcome is not in the record. The main costs were usage limits, container reclaims, background-time limits and permission refusals. The sibling fleet finally stopped on 2026-10-10, when the account ran out of usage credits.

### flatcheck: flattening-quality checker

**Verdict: TOOL**

**Question.** Can a per-quad isometry check show where official tifxyz flattenings distort, fold over or collapse, and do SLIM and ARAP do better than the official ABF++?

**Method.** Per-quad checks (length kept within +-5 %, fold-overs, area and angle distortion, collapse) plus SLIM/ARAP re-flattening. Run on public organizer meshes of a known-text scroll and compared with the official ABF++ on identical triangles. Released as an MIT package with 21 tests on synthetic geometry.

**Result.** Published as a standalone MIT tool. A clean-clone install passed 21/21 tests and the leak scrub was clean. On the 10 hardest 4 cm2 windows from 38 public meshes of a known-text scroll, the official ABF++ met the 93.1 % reference bar in 0/10 windows, SLIM in 3/10 and ARAP in 4/10. SLIM was at least as good as ABF++ in 33 of 33 comparisons, 8 of them ties. ABF++ collapsed on some meshes (27.9 % of quads within +-5 % after a x2.58 rescale); SLIM never did. The grid flattening as distributed scored 90.1-92.9 % on three whole meshes. The entry was submitted by hand to the September 2026 Progress Prize, because the form needs a signed-in account. No award outcome is recorded.

| number | meaning | source |
|---|---|---|
| 21 passed in 7.61s | pytest on the public repo, clean-clone verification | `logs/pp/verify_flatcheck.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| ABF++ 0/10, SLIM 3/10, ARAP 4/10 | hard 4 cm2 windows reaching the 93.1 % bar | `tools/sib/pp-flatcheck/vc-flatcheck/README.md` (claude/gifted-bell-gavnl5-sib-pp-flatcheck @ ec5d06476) |
| 33 of 33 | comparisons in which SLIM >= ABF++ (8 are ties at 100 % on small windows) | `tools/sib/pp-flatcheck/vc-flatcheck/README.md` (claude/gifted-bell-gavnl5-sib-pp-flatcheck @ ec5d06476) |
| 27.9 % | ABF++ quads within +-5 % on a collapsed whole mesh (rescaled x2.58, 3 fold-overs); SLIM 98.1 % on the same mesh | `tools/sib/pp-flatcheck/vc-flatcheck/README.md` (claude/gifted-bell-gavnl5-sib-pp-flatcheck @ ec5d06476) |
| 90.1-92.9 % | distributed grid flattening of three whole meshes, quads within +-5 % | `logs/pp/SUBMIT_SHEET.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "confirmed": true | flatcheck entry submitted by hand (signed in) | `logs/pp/submissions.jsonl` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Gentle patches do not separate flattening methods: the unflattened grid already scores 97-99 % there. Test on the most curved and least isometric windows. Report a reference bar as a parameter, not as a validated readability threshold.

### handcheck: mirror/handedness predictor

**Verdict: TOOL**

**Question.** Can mesh geometry plus catalogue metadata predict, before rendering, whether a tifxyz render will read mirrored, and flag meshes that cannot be decided?

**Method.** The mesh chirality, sign(det[dP/du, dP/dv, r_out]), is multiplied by the catalogue frame parity. Independent centre sources are cross-checked, and a CT frame check tests whether mesh vertices fall on masked-out CT. Validated on planted synthetic glyph renders with a wrong-sign control. Released with 94 tests.

**Result.** Published as a standalone MIT tool: a clean install passed 94 tests with 1 skipped, and the scrub was clean. Every decided public organizer mesh reads unmirrored as stored, including all 38 meshes of a known-text scroll at HIGH confidence. An independent winding-sense check agreed with the catalogue up/down flag on 36/36 checked meshes. The frame check found that 10 of 15 organizer meshes of one scroll lie 41-91 % on masked-out CT, against at most 3.6 % for every control mesh. These are reported as flags for the organizers, not as established errors. In planted-glyph validation 32/32 renders read unmirrored (min NCC 0.954), and the wrong-sign control came out mirrored 32/32. The brief said 9 of 15 meshes on that scroll were flagged; rerun from public data, the packaged rule flags 11 of 15, and the packager published the rerun number. Reported by the owner as submitted by hand for September (not in the submissions log); no award outcome is recorded.

| number | meaning | source |
|---|---|---|
| 94 passed, 1 skipped in 4.58s | pytest, clean-clone verification | `logs/pp/verify_handcheck.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 38/38 (HIGH) | known-text scroll meshes decided unmirrored | `logs/pp/SUBMIT_SHEET.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 41-91 % | share of sampled vertices on masked-out CT for the 10 frame-unverified meshes (controls at most 3.6 %) | `logs/pp/SUBMIT_SHEET.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 32/32 | planted-glyph renders read unmirrored (min NCC 0.954, margin 0.262) | `logs/pp/SUBMIT_SHEET.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| flags 11 of 15 (10 FRAME_UNVERIFIED + 1 FLAG) | packaged rule rerun from public data (the brief said 9 of 15) | `logs/sib/pp-handcheck/PUBLISHED.json` (claude/gifted-bell-gavnl5-sib-pp-handcheck @ 2cfef810c) |

**Lesson.** A handedness check means something only if the mesh actually sits on the scroll in its declared frame. Without a frame test, off-scan meshes pass silently. Publish numbers from the packaged rule rerun on public data, not from an earlier internal rule.

### tifxyz-dist: certified surface clearance

**Verdict: TOOL**

**Question.** Can exact point-to-surface distances and certified mesh-to-mesh clearance bounds replace unreliable nearest-vertex checks for train/prediction overlap?

**Method.** An exact point-to-triangle kernel with pruning, plus certified [lower, upper] mesh-to-mesh bounds with a witness point and a PASS/FAIL certificate at a chosen margin. Checked against an independent kernel and against brute force. Demonstrated on manual vs auto-grown pairs of public segment meshes from an already-read scroll.

**Result.** Published as a standalone MIT tool: 25/25 tests pass on a clean clone, and the scrub was clean. For a point 1 voxel above a sheet meshed on a 20-voxel grid, the nearest-vertex distance can be off by up to 13.1 voxels; the exact method's error is 0.0. The kernel matches an independent implementation to 2.1e-14, and pruning matches brute force exactly on 4,000 queries. Of 100,000 points sampled on a real 385k-quad segment, none returned a distance above 2.7e-12 voxel. The public demo certified 243 of 396 manual x auto-grown segment pairs. At a 20-voxel margin, 225 passed, 18 failed and 0 were inconclusive. One manual segment touches all 9 auto-grown segments. Several claims on the submission sheet were corrected to match the packaged numbers before submission. Reported by the owner as submitted by hand for September (not in the submissions log); no award outcome is recorded.

| number | meaning | source |
|---|---|---|
| 25 passed in 41.88s | pytest, clean-clone verification | `logs/pp/verify_tifxyz-dist.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 13.098059384076038 | max nearest-vertex error (vox) for a point 1 vox above the sheet; exact-method error 0.0 | `logs/sib/pp-tifxyz-dist/accuracy.json` (claude/gifted-bell-gavnl5-sib-pp-tifxyz-dist @ b98504cb5) |
| 2.1316282072803006e-14 | kernel max abs difference vs an independent implementation | `logs/sib/pp-tifxyz-dist/accuracy.json` (claude/gifted-bell-gavnl5-sib-pp-tifxyz-dist @ b98504cb5) |
| 2.7284841053187847e-12 | max distance (vox) of 100000 on-surface points on a real 385047-quad mesh | `logs/sib/pp-tifxyz-dist/accuracy.json` (claude/gifted-bell-gavnl5-sib-pp-tifxyz-dist @ b98504cb5) |
| 225 PASS, 18 FAIL, 0 inconclusive | certificates at a 20-voxel (158 um) margin over 243 of 396 pairs | `logs/pp/SUBMIT_SHEET.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Nearest-vertex distances on coarse meshes are not a valid contamination test: true re-traces and touching sheets can look several voxels apart. Use point-to-surface distances with certified bounds, and freeze a demo subset rather than waiting for the full set of pairs.

### Progress Prize submission path

**Verdict: FAILED**

**Question.** Can the agent itself submit a verified tool to the monthly Progress Prize form, with every number checked against the published repo?

**Method.** An entry was marked READY only if: the public repo was re-cloned; tests passed in a clean environment; the leak scrub was clean; the citation and licence rules were met; and the README supported every number. A submission script checked the live form fields and POSTed the entry.

**Result.** All three September packages passed the automated release checks: install, tests, citation, licences, AI disclosure and zero scrub hits. Automated submission failed twice. First, the agent's own safety check refused the form POST as a real-world transaction. After the owner granted permission, the form endpoint returned HTTP 401, because it accepts only signed-in accounts. The entry was not retried, and the owner submitted by hand from a prepared sheet. The submissions log confirms one hand submission. The owner reported that the other two were submitted, but they are not logged. Three October packages were prepared the same way; their submission is not recorded. No award outcome for any entry is in the record.

| number | meaning | source |
|---|---|---|
| "http": 401 | form endpoint response to the automated flatcheck POST (confirmed false) | `logs/pp/submissions.jsonl` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "auto_checks_pass": true | release checks passed for flatcheck, handcheck, tifxyz-dist, xsec, ringstrip and orgsec-ink | `logs/pp/verify_*.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "leak_hits": [] | zero leak-scrub hits in every verify record | `logs/pp/verify_*.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Before automating a submission, check whether the form requires a signed-in account. Keep a per-entry confirmation log that the human also fills in; otherwise the record cannot show what was submitted.

### xsec: cross-section check of grown surfaces

**Verdict: TOOL**

**Question.** Do numeric surface gates catch a grown surface that jumps between windings, and can a cross-section view catch it instead?

**Method.** Draw the grown tifxyz surface on four raw-CT slices through its height range, from a local zarr or from s3. Compare with the radial-normal gate and an on-papyrus fraction, on a public crushed scroll and on synthetic cylinders and shells.

**Result.** Published as part of the October package: 3/3 tests pass on a fresh clone, and the reproduce script was checked against the public bucket. A 2 x 2 cm patch grown with normal grids passed every numeric bar: median |cos| 0.928, 75 % of normals above 0.8, and 0.90 mm per cm of radial spread. Its cross-section still showed it jumping to the neighbouring layer at every crack. An automated on-papyrus fraction did not separate good from jumped surfaces: 0.676 vs 0.676, and 0.628 for a cross-winding surface. Submission is not recorded.

| number | meaning | source |
|---|---|---|
| 3 passed in 2.08s | pytest, verification record | `logs/pp/verify_xsec.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| median \|cos\| 0.928 | radial gate score of a winding-jumping patch that passed every numeric bar | `logs/pp/SUBMIT_SHEET_OCT2026.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.676 vs 0.676 vs 0.628 | on-papyrus fraction: good vs jumped vs cross-winding surface (no separation) | `logs/pp/SUBMIT_SHEET_OCT2026.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A surface that has jumped windings still faces outward, so normal-direction gates pass it. Before trusting any render or ink map built on an auto-grown surface, inspect cross-sections or use an identity measure.

### ringstrip: patch-to-strip unrolling

**Verdict: TOOL**

**Question.** Can many small grown patches of one winding be placed into one continuous unrolled strip, so that patch-wise ink maps can be read as a sheet?

**Method.** Every patch pixel is placed at its azimuth about the scroll axis (times a reference radius) and its height. Overlaps are averaged, small holes are closed and seams are recorded. Tested on synthetic cylinder patches and on five real patches.

**Result.** Published as part of the October package: 2/2 tests pass on a fresh clone, and the reproduce script was checked. It unrolled five real patches into one 10,513 x 2,507 px strip. The ink map on that strip is uniform speckle; the package states this is a property of the surfaces and models, not of the tool. In synthetic tests, a line stays continuous across a seam over more than 90 % of its length, and three overlapping tiles reassemble to within 2 grey levels. Submission is not recorded.

| number | meaning | source |
|---|---|---|
| 2 passed in 0.39s | pytest, verification record | `logs/pp/verify_ringstrip.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 10,513 × 2,507 px | size of the strip built from five real patches | `logs/pp/SUBMIT_SHEET_OCT2026.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** The stitching works mechanically, but a strip is only as good as the surfaces under it. Validate surface identity (see xsec) before stitching ink maps.

### orgsec-ink (package orgseg-ink): public ink models on organizer sheets

**Verdict: TOOL**

**Question.** Run on CPU on segments the organizers published for two eligible scrolls, do the two public Herculaneum ink models produce maps that agree with each other or show text structure?

**Method.** The public 9 um ink model (both layer orders) and the 2023 Grand Prize model were run on 26 organizer sheets. Agreement was measured as the Pearson r of 0.5 mm-smoothed maps, against rotated and flipped controls. A row-periodicity score was calibrated on 112 known-text tiles against 144 cross-winding junk tiles.

**Result.** Published as a package that reports nulls. Across 26 organizer sheets, the fraction of each 9 um map above 0.5 was 0.012-0.158, no pixel exceeded 0.90, and the 1-3 mm blobs showed no row alignment. Forward and reverse layer orders were unrelated. On the published agreement test the two models' maps correlated at only r = 0.13, against 0.10 for the best rotation/flip control: they do not agree. The row-periodicity score is not a text detector: only 1.8 % of known-text tiles beat the junk 99th percentile. Neither model produced a candidate. 3/3 tests pass, and the reproduce script was checked. Its null results are counted under First Letters (official-model screen, two-model agreement test, row-structure score calibration).

| number | meaning | source |
|---|---|---|
| 0.13425493240356445 | Pearson r between the two models' maps on the published agreement test | `packages/orgseg-ink/results/agree_PHerc0800_i1_ink9um_vs_gp.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.09693858027458191 | best rotation/flip control r on the same sheet | `packages/orgseg-ink/results/agree_PHerc0800_i1_ink9um_vs_gp.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 1.8 % | known-text tiles beating the junk 99th percentile on the row-periodicity score | `logs/pp/SUBMIT_SHEET_OCT2026.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 3 passed in 5.78s | pytest, verification record | `logs/pp/verify_orgseg-ink.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A null from off-the-shelf models on a new scroll means little unless they detect a positive control on the same type of scan. Publish calibration nulls, such as row periodicity failing on known text, so that nobody reuses a non-detector.

### Blind-reader harness (local)

**Verdict: PASSED**

**Question.** Can LLM readers be run blind and audited by code, so that no answer reaches the orchestrator and image geometry is preserved?

**Method.** Readers see only images with random UUID names and stripped metadata. A transcript audit voids any tool call beyond reads of the listed images, one age-encrypted answer write and a DONE hand-back. Synthetic tests covered decoy files (a planted-file test), coordinate fidelity at two image sizes, and the sealed-output mode.

**Result.** The planted-file test was valid: the reader opened no decoy. The coordinate test showed that the harness silently resamples images larger than 1068 px. At 2136 px the median centre error was 57.5 px with a fitted scale of 0.966/0.964, against 0.7 px at 1068 px, so every display was capped at 1068 px per side. A read-only agent type could not write sealed answers. General-purpose agents in sealed-output mode passed the audit with 12/12 correct synthetic answers. The local job ledger records 197 jobs between 24 and 26 September (191 reads, 3 pickers, 3 sealers), all audit-valid. Disclosed residual risk: separation from the key holder is procedural and audited, not enforced by the OS.

| number | meaning | source |
|---|---|---|
| centre error median 0.7 px | 1068 x 1068 px synthetic image, coordinates exact | `RULES.md (HARNESS-COORD)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| centre error median 57.5 px | 2136 x 2136 px synthetic image, resampled by the harness (fitted scale 0.966 (x), 0.964 (y)) | `RULES.md (HARNESS-COORD)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 197 | rows in the local job ledger (191 reader, 3 picker, 3 sealer), all valid=True; counted at survey | `logs/harness_jobs.tsv` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 12/12 | synthetic Greek capitals named correctly at 1068 px | `RULES.md (entry HARNESS-COORD)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 12/12 letters named with correct identities | sealed-output live test, answer decrypted only by scorer code | `RULES.md (entry HARNESS-SEALED-TEST)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Measure the harness on synthetic images with known geometry before any real read: the hidden resampling would have corrupted every large display. A code audit of transcripts makes it safe to use a more capable agent type.

### Remote blind-reader harness

**Verdict: TOOL**

**Question.** Can blind reads run in sibling containers while the answers stay sealed to a key that only the orchestrator holds, with commit order and transcripts verifiable afterwards?

**Method.** Commit A (keys, jobs, briefs, image manifest) is pushed before any reader runs. Readers write age-sealed answers. Commit B carries the sealed files, audits and gzipped transcripts. A verifier script (rh_verify.py) checks 12 items, including that commit A precedes every answer and that each brief was used verbatim.

**Result.** This harness was declared because the main container had about 109 MB of disk free. The verifier had a normalisation bug: a batch's partial last session never matched the reference brief. It was fixed under a new code hash before any affected answer was decrypted, and the earlier batch still verified 12/12.

| number | meaning | source |
|---|---|---|
| earlier batch still passes 12/12 | verifier regression after the partial-session fix | `RULES.md (METRIC-HASH-30)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Commit-before-read ordering plus a scripted verifier makes remote blind reads auditable. Regression-test the verifier on batch-size edge cases, such as a partial final session.

### Seal-key and view bookkeeping

**Verdict: TOOL**

**Question.** Is every decryption of a sealed answer and every image view logged, so that blindness can be audited?

**Method.** Answers are decrypted only through a logging scorer function, which appends a row (time, purpose, sealed path, sha256) to key_reads.tsv. Every image view, by a human or an agent, is appended to views.tsv with its hash and purpose.

**Result.** The decryption log holds 1,938 logged decryptions of 713 distinct sealed files, made between 24 September and 2 October, mostly for scoring, consistency checks and audits. The view log holds 22 rows: 21 owner views from a human-review set of raw CT overviews, and 1 orchestrator view of a synthetic font chart (not scroll data). The human-review set was cancelled after its first batch. The seal key lived only in the ephemeral container, and STATE records that seals would be lost if the container were reclaimed before scoring.

| number | meaning | source |
|---|---|---|
| 1938 | logged decryption rows (713 distinct sealed files, 2026-09-24T23:48:13Z to 2026-10-02T16:22:57Z); counted at survey | `logs/key_reads.tsv` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 22 | view rows (21 owner HRV-1, 1 orchestrator synthetic key sheet); counted at survey | `logs/views.tsv` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| HRV-1 is cancelled after batch 1 | human-review viewing set stopped | `CHANGELOG.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Route all decryption through one logging function, and keep views in their own ledger. Store the key outside the ephemeral container (a persistent secret) so that seals survive restarts; the project left this to the owner as optional.

### Compute ledger and hardware

**Verdict: INCONCLUSIVE**

**Question.** What compute did the programme use, and was it ledgered?

**Method.** Every job was meant to be logged in gpu_ledger.tsv (host, gpu, command, times, exit code, output hash), with cumulative usage summarised in STATE.md.

**Result.** The main container had 4 CPU cores, 15 GB RAM, 30 GB of free disk and no GPU. The compute ledger holds 78 jobs, all on CPU, 73 with exit code 0. It covers only the first ~4.5 hours (24-25 September), so later CPU work and the whole sibling fleet are missing from it. STATE records 0 GPU-hours and ~14 CPU core-hours up to 25 September. The planned GPU training arm stayed blocked throughout for lack of a GPU. Total compute cannot be reconstructed from the record.

| number | meaning | source |
|---|---|---|
| 78 | rows in the compute ledger, all host vm / gpu cpu, last end 2026-09-25T02:16:21Z; counted at survey | `logs/gpu_ledger.tsv` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| GPU-h 0. CPU: ~14 core-h | cumulative usage to 2026-09-25 11:00Z | `STATE.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 4 CPU cores, 15 GB RAM, 30 GB free disk, no GPU | hardware inventory at start | `CHANGELOG.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** The job runner must append to the compute ledger automatically. Manual logging lapsed within a day, and the fleet's compute was never ledgered.

### PHerc0841 known-text bank

**Verdict: TOOL**

**Question.** Can a known-text benchmark bank be built on one scroll, with the 2.4 um reference ink mapped onto the 9 um canvas accurately enough for sealed reading tests?

**Method.** Fetched the organizer meshes, surface volumes and 2.4 um reference slices, and mapped 2.403 -> 9.366 um by a separable area average. The mapping was validated on synthetic data and by cross-resolution NCC at small shifts. Also measured: the text area outside the exclusion shell, and whether blank windows exist. Every file is hashed in a manifest; no image was viewed.

**Result.** Built: 4,147 files (3.67 GB) with a hashed manifest. The mapping error on a synthetic test was 0.012 px, and cross-resolution NCC put the real reference mapping within ~1.4 px. The mesh grids imply a 0.37 px offset from the declared formula; this was judged negligible and disclosed. The scroll had no usable blank windows, so blanks were taken from a different known-text scroll. Reference text outside the exclusion shell was 0.248 cm2, below the 0.5 cm2 needed, so the text-order decision was pooled over all benchmark windows. Whether two segments are the same sheet was disputed and recorded as unresolved.

| number | meaning | source |
|---|---|---|
| 4147 files, 3.67 GB | bank manifest size | `RULES.md (B0841-BANK)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| synthetic test error 0.012 px | 2.4 -> 9 um mapping error on a synthetic test | `RULES.md (B0841-BANK)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| total 0.248 < 0.5 cm^2 | reference text outside the exclusion shell; forced the pooled text order | `RULES.md (B0841-BANK)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.01144340000791999 | synthetic_test_max_err_px9 | `logs/bank0841/summary.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Build the benchmark bank first, and record every contradiction (offsets, label semantics) as a numbered correction. Here they changed two downstream design choices, the blank source and the pooled order, before any read happened.

### Window render pipeline smoke test

**Verdict: PASSED**

**Question.** Does the window pipeline (levelling, orientation, official renderer, alignment gate) reproduce the organizer surface volume and handle the mirror convention correctly?

**Method.** One 1068 px window on a known-text segment was levelled and rendered with the official renderer from remote zarr. Our centre slice was compared with the organizer surface volume by NCC at integer shifts, with 5 px shifted controls. A mirror check was run with the opposite convention, and the five sealed benchmark windows were checked on geometry only. The pipeline has 82 unit tests.

**Result.** The smoke test passed. Alignment NCC was 0.986 at zero shift, against 0.74-0.76 for the 5 px shifted controls, and the render took 57 s. The level angle was 97.6 deg with a 1.0 deg spread. Rendering with the opposite convention flipped the measured sign as expected (positive fraction 0.0002 vs 1.0). On geometry alone the benchmark windows had spreads of 3.0-8.9 deg, and none was mirrored under the default convention. The full test suite stood at 524 passed at that point.

| number | meaning | source |
|---|---|---|
| 0.986153578470647 | best NCC at zero shift (render slice 15 vs SV slices 13-14) | `logs/pipeline/w040_smoke.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 57.4 | render seconds (returncode 0) | `logs/pipeline/w040_smoke.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 0.00016831238779174148 | levelled-sign frac_positive with convention -1 (mirror check; 0.9998 at +1) | `logs/pipeline/w040_smoke_zasc_c-1.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| spread 3.0-8.9 deg, none mirrored at convention +1 | geometry of the five benchmark windows | `CHANGELOG.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Take renderer conventions (pixel-to-grid offsets, the surface slice index) from the source code. Gate every render by NCC against the organizer product, with shifted controls, before using it.

### Data offload to a git data branch

**Verdict: PASSED**

**Question.** Can bulk outputs be moved off a nearly full disk into a private git branch, with round-trip integrity verified before any local deletion?

**Method.** One commit per batch, whose tree holds only that batch, built from a blob-free shallow fetch. Files are refused on size, extension, key material or symlinks. The remote tip is verified before any local removal, and every file's sha256 goes into a manifest. A synthetic round-trip self-test ran first. Pushing to the branch and deleting files each needed the owner's explicit approval.

**Result.** The self-test passed: a synthetic array was pushed, deleted locally and fetched back with an identical sha256 and equal values. After the owner's approval, 3 batches of closed-decision data (1,323 files, 3.39 GB) were offloaded, each with a verified remote tip and per-file hashes. Before that approval, the agent's safety check refused to delete a regenerable 4.9 GB docker image store. Free disk stayed near 109 MB until the owner approved the deletion, which freed about 5 GB.

| number | meaning | source |
|---|---|---|
| sha256 identical, array equal | offload round-trip self-test | `CHANGELOG.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 3 batches (1,323 files, 3.39 GB) | closed-decision offload completed | `RULES.md (METRIC-HASH-30 note)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 1479821428 | bytes in batch closed-20260926T1747-00 (704 files); -01 is 1503093646 (333 files), -02 is 408374184 (286 files) | `logs/offload/manifest.jsonl` (claude/gifted-bell-gavnl5 @ a1f9f4635; data branch @ 2444e884e) |

**Lesson.** Use git as cold storage only with per-batch verification and hard limits on size and file type, and get explicit approval for pushes and deletions up front. The disk crisis cost most of a day and forced reads onto remote containers.

### Sibling fleet operation

**Verdict: STOPPED**

**Question.** How large did the fleet of sibling sessions grow, how was it coordinated, and how did it stop?

**Method.** Builder/trainer sibling cloud sessions, each on its own branch, with no access to seals, scoring or viewing. Orders went out by one-shot triggers, decision requests came back through ASK.md, and each sibling kept a RESUME.md. The fleet grew in waves from 25 September. On 9 October an owner standing order asked for the maximum fleet at all times, with every sibling running a declared, measurable job.

**Result.** The registry lists 118 sibling sessions created between 25 September and 2 October, on 95 branches (94 of them sib-* worker branches plus fl4t). Another 22 sib-* branches are not in the registry (sub-siblings and other worker lanes started outside the registry, among them one First Letters lane and a checkpoint branch), giving 116 sib-* worker branches. A further fleet of 52 sessions started on 9 October for umbilicus, ink-model and survey lanes. On 9 October it was found that idle containers are reclaimed after a turn ends and their detached jobs die, so the effective fleet had been a fraction of the session count. Earlier, on 2 October, every lane's keepalive had overrun the 7,200 s background limit and been killed; the lanes stopped because the harness forbade restarting the command. At about 05:15Z on 10 October every sibling session stopped with 'out of usage credits' (a seven-day limit), and the remaining survey work ran locally.

| number | meaning | source |
|---|---|---|
| 118 | sibling session entries in the registry (95 branches; created 2026-09-25 to 2026-10-02); counted at survey | `logs/sib/registry.json` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| "count": 52 | sessions in the 2026-10-09 fleet | `logs/sib/registry.json (fleet_2026-10-09)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 116 | worker branches (claude/gifted-bell-gavnl5-sib-*), including 22 sub-sibling branches not in the registry; counted at survey | `git refs` (refs/remotes/origin/claude/gifted-bell-gavnl5-sib-*) |
| 7200 s background limit | the keepalive (about 7150 s plus a sleep of up to 120 s) overran it at 07:58-08:01Z on 2026-10-02, and the lanes stopped | `RULES.md (DECL-FL-4-A4-A2-E4)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| out of usage credits | every sibling session stopped at about 05:15Z on 2026-10-10 (seven-day overage; reset 2026-10-14 03:00Z) | `logs/owner/INBOX.md (item 36)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Session count is not compute. Make jobs resumable, keep each turn alive within known background-time limits, and budget the account's usage before scaling out. A fleet that outgrows its usage budget stops all at once.

### Keepalive dispatch protocol

**Verdict: FAILED**

**Question.** Can a dispatcher sibling send resumable, keep-alive job orders to the whole fleet from a committed brief?

**Method.** SIB-KEEPALIVE-1: job scripts are resumable and write DONE markers; siblings poll in calls of under 10 minutes until DONE; backup triggers fire 100 minutes later. A dispatcher sibling was to create the 72 triggers from logs/sib/dispatch_2026-10-09_2300.md.

**Result.** The dispatcher created 0 of 72 triggers. Its permission classifier refused both the plan script and the first trigger, treating orders that tell sessions to keep themselves alive with detached jobs as creating unsafe agents. The dispatcher did not rephrase the orders to get around the refusal. The orchestrator created 12 re-run triggers itself, and the 24-lane second pass was never dispatched. A later survey order went to 24 lanes, but only 17 of 72 positions, from 8 lanes, finished before usage credits ran out.

| number | meaning | source |
|---|---|---|
| 0 of 72 triggers created | dispatcher outcome, 2026-10-09 23:00-23:03Z | `logs/sib/dispatch_2026-10-09_2300.blocked.md` (claude/gifted-bell-gavnl5-fl4t @ a250ae8c2) |
| no umbcore pass-1 lane pushed "done" within 85 min | the observation that motivated the keepalive protocol | `RULES.md (SIB-KEEPALIVE-1)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| 17 of 72 y positions | survey positions finished on the lanes before the credit stop | `logs/owner/INBOX.md (item 36)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** To a permission layer, orders that tell other sessions to keep themselves alive look like creating unsafe agents. Agree the orchestration pattern and its permissions before scaling, or run the compute without AI turns, as the later fleet did.

### Multi-agent prompt regeneration

**Verdict: FAILED**

**Question.** Can a multi-agent workflow regenerate the master prompt after each context condensation without losing integrity rules?

**Method.** After a condensation, a workflow of 24 agents drafted, critiqued and verified a new master prompt. Under the compute-economy order it was limited to one run per 24 hours.

**Result.** The v8 run used 1,454,186 subagent tokens across 24 agents, and only 3 completed. The account usage limit killed it, and the run itself helped hit that limit. It was retired. Its replacement is a single-pass refresh at most once per 24 hours, with a scripted diff that checks every integrity rule is kept verbatim, plus a live handover file that is read first after every restart.

| number | meaning | source |
|---|---|---|
| 1,454,186 subagent tokens across 24 agents | cost of the v8 regeneration run | `RULES.md (STANDING-ORDER-COMPACT-A2)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| Only 3 agents completed | completion of that run | `RULES.md (STANDING-ORDER-COMPACT-A2)` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** Large self-maintenance workflows draw on the same usage budget as the research. A small, maintained handover file plus a scripted integrity diff was cheaper and enough.

### Operating cost and failure modes

**Verdict: INCONCLUSIVE**

**Question.** What did operations cost, and what broke?

**Method.** Collected the events recorded in RULES.md, the CHANGELOG, the owner inbox and an internal adversarial review: usage-limit stops, container restarts, permission refusals and background-time kills. No complete ledger of time or usage exists.

**Result.** There is no complete cost ledger, so the total cost cannot be stated. An internal review on 30 September estimated that 43 % of project time went to usage limits, and ~25-40 h to container reclaims, refusals and serial CPU work. These are estimates, not measurements. Recorded failure classes:
- repeated account usage-limit stops of readers, auditors and siblings;
- at least seven container restarts, which wiped RAM-disk scratch;
- agent safety-check refusals of form submission, file deletion, a data-branch push, recurring check-ins, session creation and cross-branch code, none of which was routed around;
- a 7,200 s limit on background commands;
- a near-full disk;
- a final seven-day credit exhaustion.
The validity machinery itself (hashing, audits, sealing) cost minutes.

| number | meaning | source |
|---|---|---|
| 43 % of project time went to usage limits | estimate in the 2026-09-30 adversarial review (not measured) | `logs/owner/AUDIT_2026-09-30.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| ~25-40 h went to container reclaims, refusals and serial CPU work | estimate from the same review | `logs/owner/AUDIT_2026-09-30.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |
| The validity machinery costs minutes | from the same review | `logs/owner/AUDIT_2026-09-30.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** On a usage-capped, CPU-only, ephemeral platform, the binding constraint was availability, not method. Budget usage explicitly, make every job resumable and pushed, and keep an automatic ledger of time and usage from day one.

### Append-only decision log integrity

**Verdict: TOOL**

**Question.** Is the hash-chained declaration log intact, so that declarations demonstrably precede results?

**Method.** Each RULES.md entry carries the sha256 of the previous entry, and the project verifier recomputes the chain. VERIFY.md documents one-command checks for code hashes and for re-scoring. The survey re-ran the verifier read-only.

**Result.** The project's chain verifier, re-run at survey time, returned OK on all 397 entries, from 24 September to the last result on 10 October. The ledger of decision verdicts (LEDGER.md) holds 12 rows, most with scorer-output hashes. None concerns this family: tools and operations were recorded as declarations and results in the chained log, not as ledger verdicts.

| number | meaning | source |
|---|---|---|
| 397 | entries verified OK by hercules.records.rules_append.verify_file; last entry VC3D-AUDIT-RESULT 2026-10-10T10:52:34Z; computed at survey, not copied | `RULES.md` (claude/gifted-bell-gavnl5 @ a1f9f4635) |

**Lesson.** A hash-chained, append-only log plus per-result code hashes is cheap and lets outsiders verify the ordering after the fact. Keep it running even when everything else is failing.
<!-- END:experiments_full -->
