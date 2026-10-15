# Superseded claims

The lab notebook ([`RULES.md`](RULES.md)) is append-only, so every claim this project later retracted, corrected, invalidated,
redefined or narrowed is still printed there, often without a note beside it; this file is the index to those places. It lists
**76 entries** in five eras, each with the claim, where and in which commit it was made, what superseded it, why, and its kind:
**retracted** (withdrawn as wrong), **corrected number** (a value or count replaced by the committed one), **invalidated run** (a
result computed on broken data or a broken setup), **redefined test** (a declared test or bar replaced), **scope narrowed** (true only
in a smaller sense than stated), **design error** (a rule or procedure that could not do what it was declared to do).

**Reading conventions.** Until this release the notebook lived at the repository root, so for any older commit it is
`git show <commit>:RULES.md`; superseded documents moved to `archive/` in `b370331` (`STATE.md` → `archive/docs/STATE_2026-09-17.md`,
`METHOD.md` → `archive/docs/METHOD_v0.2_papyrus_subtraction.md`, `docs/report_2026-09-17.md` → `archive/docs/report_2026-09-17.md`
and `docs/reproduce.md` → `archive/docs/reproduce_2026-09-18.md`). Text in quotation marks is copied from the named file at the named
commit. Values with more than three decimals are copied exactly from a committed file; a three-decimal value marked **trunc.** is truncated toward zero, never rounded up. *This release*
means a correction first made in the release documents. **INFERENCE** marks our interpretation. The confirmation test is cited only as
C1 (pre-registered 46a4bfc; result: see [docs/RESULTS.md §5](RESULTS.md)). Every commit hash below was checked with `git cat-file -t`,
and every quoted string and copied number against `git show <commit>:<path>`; values we computed are marked as computed.

**Status date.** Every fix status below was checked against the release working tree on 2026-10-15; text quoted from a release file
without a commit is quoted from that tree.

## Headline numbers as they now stand

The corrections a reader of the notebook is most likely to trip over. Current values: `results/stats_evaluation7.json` and
`results/per_crop_evaluation7.csv` unless another file is named (pixel values as written in 5ba7764; the stroke and local values of E,
v8, GP-R1, v7 and the team model recomputed at full precision in 0aeb4b2, entry 65).

| quantity | notebook said (commit) | committed value | trunc. | entry |
|---|---|---|---|---|
| v8 pixel AUC, 7-crop mean | 0.840 (bc24d20) | 0.8395000189894518 | 0.839 | 55 |
| v8 stroke AUC | 0.917 (bc24d20) | 0.916766433285967 | 0.916 | 55 |
| GP-R1 pixel AUC | 0.828 (c406bf7) | 0.8276284576194444 | 0.827 | 55 |
| GP-R1 stroke AUC | 0.920 (c406bf7) | 0.9196515862649258 | 0.919 | 55 |
| v6b pixel / stroke | 0.804 / 0.891 (db529dd) | 0.8035827835511089 / 0.8905571428571427 | 0.803 / 0.890 | 46, 55 |
| v6c pixel | 0.785 (cd3ea3d) | 0.7847156970908958 | 0.784 | 47, 55 |
| team model pixel, in 7-crop tables | 0.932 (05d84a7 … c406bf7) — the segment-1 3-crop mean | 0.929004087705171 | 0.929 | 45 |
| team model, quoted range | "0.94–0.98" (6d1c078) | 0.8517727032590168 – 0.978177856332221 | 0.851 – 0.978 | 29 |
| v6b − v6c pixel (value of the team veto) | "+0.02" (cd3ea3d) | 0.018867086460212894 [0.008836696537462187, 0.028754113949181814] | 0.018 | 47 |
| E per-crop passes | "6 of 7 clear the pixel bar and 5 of 7 the stroke bar" (49be302) | 7 of 7 pixel ≥ 0.80, 4 of 7 stroke ≥ 0.90 | — | 61 |
| letter test undefined | "5 of the 7" crops (d27193f) | 2 of 7 under mask J (`stats/s1_gate_*.json`, fe9424c, 72ea621) | — | 34 |
| R1 agreement, v8 vs team model | "0.72–0.87" (e8d6a6c) | 0.717 – 0.865 as recorded in the R1 table | — | 59 |
| R2 agreement, E vs team model | "0.80–0.89" (9de8704) | 0.797 – 0.887 as recorded in the R2 table | — | 59 |
| stroke-test disks per class per crop | "175–760" (a0f3f57) | ink 37–202, blank 272–761 (`stats/stroke_test.json`, a0f3f57) | — | 35 |
| v0.3p held-out mean on w028 | 0.666 (a492c1f) | 0.6657312204512951, mean of the four per-crop values in `stats/w028_gate_t1_v0.3p.json` (a492c1f) | 0.665 | 14 |
| v7 generalisation gap | 0.074 (05d84a7) | 0.7415620423091235 (`stats/s1_v7_weights.json`, 05d84a7) − 0.6683960321669036 | 0.073 | 48 |

---

## All superseded claims

### Era 1 — w028 calibration (2026-09-16 to 2026-09-17)

#### 1. The row test as an ink indicator and face selector
- **Claim** — "Face = the one with the higher row-test peak"; a promising candidate needs "row test positive on the same face"; GATE-F
  needs "row test negative" — `RULES.md` `## GATE-T1 (6.2)`, `## Rule 6.4 derivation`, `## GATE-F (6.5)` @ d160337. Positive "if ≥ 0.25
  on the writing face and < 0.15 on the other face" — `METHOD.md` §5.6 @ a56bd42.
- **Superseded by** — `### GATE-T1 control, blank1, method v0.1b`: the row test is "falsified as an ink indicator on w028 and is dropped
  from the GATE-T1 criteria (recorded, not tuned)." @ 14cee78.
- **Why** — The blank chart shows a stronger ~3 mm periodicity ("bottom peak 0.418 at 3.14 mm", 14cee78) than the text chart ("top peak
  0.258 at 2.99 mm", 2026bab), so the period is fibre/segmentation banding. The face-selection use was never withdrawn:
  `scripts/gate_eval.py` (now `archive/scripts/gate_eval.py`) picks each crop's writing face by row-test peak in bc38713, ee25abe and
  a492c1f. (On Scroll 1 the face was chosen by TRAIN AUC
  instead, 038aef0.)
- **Kind** — redefined test.

#### 2. GATE-T2: a 9 µm test and a route decision
- **Claim** — GATE-T2 on w028 pooled to 9.596 µm and w040 at 9.362 µm, with "Decision rule: T2 fails and T1 passes → 2.4 µm-only route"
  — `## GATE-T2 (6.3)` @ d160337.
- **Superseded by** — T2(b) "Inconclusive on 3.4 % area" @ 2026bab; "GATE-T2(a) (w028 pooled to 9.6 µm) is not run" @ 0825de7.
- **Why** — The 28-slice w040 stack clipped the sheet, leaving a 3.4 % mask; T2(a) became moot when T1 failed. The 9 µm route was never
  fairly tested and the decision rule was never exercised.
- **Kind** — scope narrowed.

#### 3. Unit statistics (rule 6.4) and GATE-F as gate criteria
- **Claim** — the T1 bar "text units flagged ≥ 3× blank units at 1 cm²" and GATE-F "rule flags ≤ 1 unit per 4 cm²" —
  `## GATE-T1 (6.2)`, `## Rule 6.4 derivation`, `## GATE-F (6.5)` @ d160337.
- **Superseded by** — "so the 3× unit bar could not be evaluated" @ bc38713; "remains unevaluable under the declared rule; recorded, not
  relaxed." @ a492c1f.
- **Why** — A unit needed ≥ 50 % valid pixels, but the masks covered at most about 36 % of a chart (text1: "mask 36.0 % (top) / 35.9 %
  (bottom) of the chart", 2026bab; the blank1 control: "mask 22.3 % / 22.4 %", 14cee78), so no unit was classed at any size for any
  method. GATE-F was never evaluated.
- **Kind** — design error.

#### 4. Disk space
- **Claim** — "~30 GB writable disk" — `STATE.md` `## Environment (actual, differs from the brief)` @ d160337.
- **Superseded by** — "~37 GB usable disk" — `STATE.md` `## Environment facts that shaped the work` @ a92863a.
- **Why** — Two figures for the same machine in the history of one file, with no note; both are reported as recorded.
- **Kind** — corrected number.

#### 5. What would carry the w028 signal
- **Claim** — "Expectation for GATE-T1: the pure relief term r is likely weak; the face-intensity residual terms (e, a) carry the rest."
  — `docs/paper_2603.27698.md` @ d160337 (now `docs/background/`).
- **Superseded by** — `### GATE-T1 verdict, method v0.2`: "Mean on the writing face 0.504. **GATE-T1 FAILS for v0.2.**" … "The
  inpainting residual adds nothing." @ ee25abe.
- **Why** — With e and a included, v0.2 sits at chance (0.5037565238179025, `stats/w028_gate_t1_v0.2.json` @ ee25abe). The only w028
  signal came from plain smoothed band brightness (v0.3p) and depth templates.
- **Kind** — retracted.

#### 6. The v0.1 grain mask
- **Claim** — "Grains: S > 99.9th percentile, component ≤ (0.1 mm)² → dilated 0.3 mm." — `METHOD.md` §5.5 @ a56bd42.
- **Superseded by** — `### Declared BEFORE running: method v0.1b`: grain = "connected component area between (0.02 mm)² and (0.1 mm)²"
  @ 625a991.
- **Why** — At 2.4 µm the rule "marked 10 218 fibre-scale bright pixels and their 0.3 mm discs covered ~94 % of the sheet" (mask 5.6 % /
  5.1 %). `METHOD.md` was never updated.
- **Kind** — design error.

#### 7. A 0.4 mm damage margin around every void
- **Claim** — damage mask "dilated by 0.4 mm" — `METHOD.md` §5.5 @ a56bd42.
- **Superseded by** — `### Second pre-AUC mask decision`: "the 0.4 mm margin applies only to MACROSCOPIC damage" @ 2b61f05; later
  `### Judge mask J`: the v0.1b "rule with the margin reduced to 0.1 mm" @ 55cd58e.
- **Why** — At 2.4 µm the on-sheet mask is a lace of fibre-scale voids, and "dilating every void by 0.4 mm blanked 100 % of the chart"
  ("the first text1 judge run returned AUC = None because the mask was empty"). `METHOD.md` was never updated.
- **Kind** — design error.

#### 8. The papyrus-subtraction method would be frozen and applied
- **Claim** — parameters "will be FROZEN after GATE-T1/T2/F and before any eligible scroll is read" — `METHOD.md` header @ a56bd42.
- **Superseded by** — "Route B (papyrus subtraction) is closed on w028." @ ee25abe; E1 audit: "the papyrus-subtraction route is dead"
  @ 3c19230.
- **Why** — It failed GATE-T1 and is near chance on verified Scroll 1 text: "v0.1b 0.515 / 0.423" (pixel / letter, refined reference,
  87dd1bc) and 0.5560154267888036 pixel, CI [0.5422941391002882, 0.570577613748109], over the 7 evaluation crops under mask J
  (`results/stats_evaluation7.json` @ 5ba7764). It was never frozen or applied to an eligible scroll.
- **Kind** — retracted.

#### 9. "Idempotent" drivers
- **Claim** — `scripts/run_w028_crops.sh` header "… (disk-bounded). Idempotent." @ 96fb2f4; `STATE.md` "every driver is sequential and
  idempotent" @ a92863a; `docs/reproduce.md` "All are idempotent and disk-bounded" @ b438fe0.
- **Superseded by** — `### Data-integrity incident (found 2026-09-17 16:30 UTC)`: "The restarted crop driver deleted text2's chunk rows
  144–209 unconditionally" @ 5413b77.
- **Why** — Line 7 of the driver, `rm -rf data/w028/stack.zarr/0/0/$(seq … 144 209)`, runs on every restart and deletes rows that the
  overlapping text3/text4 crops need. Only the fetcher was fixed (5413b77); the line is unchanged in
  `archive/scripts/run_w028_crops.sh` @ b370331.
- **Kind** — design error.

#### 10. A surface-local ink contrast at particular face depths
- **Claim** — D1: "the only contrast agreeing with the reference is a weak face-brightness excess at letter scale"; the top face "peaks AT
  k_top (δ = 0): 0.577 / 0.614" — `### D1 result, text1` @ 20c16db. `STATE.md`: "with a depth signature (peak at the top-face crossing,
  5–7 µm inside the bottom face)" @ a92863a; the report: "peaking at the top-face crossing and 5–10 µm inside the bottom face" @ a6dfd42.
  On Scroll 1: "bottom face = writing face (chosen on TRAIN per the rule)" @ 95cf9a6.
- **Superseded by** — `### E1 partial results` (two faces): the non-writing face reads verified text "held-out at 0.623,
  indistinguishable from the writing face at 0.636. The ink-correlated contrast is NOT surface-local.", with the data-contract correction
  that the δ = 0 channels of the two faces are the "same quantity (corr 0.96)" @ cdc291e. Per crop, the depth of maximum "varies by crop
  (held1 differs)" — `### D2 result` @ 6d1c078.
- **Why** — δ = 0 is a 50 %-of-peak crossing of the bright band, so its contrast tracks the band's brightness level (on text1 the crest
  itself scores 0.581: "Crest peak intensity: 0.581"). INFERENCE: the face choice carries no ink-specific meaning; the contrast is a level effect
  through the sheet.
- **Kind** — retracted.

#### 11. w028 text3/text4 numbers, and v0.3p's two above-bar crops
- **Claim** — per-crop GATE-T1 AUCs for text3 (0.565 / 0.473) and text4 (0.496 / 0.575) as full-crop results —
  `### GATE-T1 verdict, method v0.1b, all 7 crops` @ bc38713 (v0.2 likewise @ ee25abe). v0.3p "**FAILS the 0.70 bar** (two crops
  individually above it)" (text3 0.714, text4 0.710) and the team model's contrast "reproduced at AUC ≈ 0.66 by nothing more than smoothed
  CT brightness" — `### v0.3p result, all crops` @ a492c1f.
- **Superseded by** — `### Data-integrity incident`: every text3/text4 number "was computed on the remaining 61 % of those crops"
  @ 5413b77; `### Post-hoc check v0.3p-hp result`: "text3's drop (0.71 → 0.64) shows part of its number was a density gradient"
  @ ba2310f.
- **Why** — The driver of entry 9 deleted rows 144–209 and the fetch's done-marker hid it. The two above-bar crops are exactly the two
  computed on 61 %, and part of text3's value is a chart-scale gradient. The hp check is itself partial ("partial: text1–text4 and
  blank1"). The numbers stay on record with the caveat.
- **Kind** — invalidated run.

#### 12. Method v0.3f
- **Claim** — v0.3f declared ("v0.3f: s_top = z(G_{0.25 mm}(I(k_top)))", …) to be judged on text2–text5 and the blanks —
  `### Declared BEFORE running: method v0.3` @ 0825de7.
- **Superseded by** — GATE-S1 disk order: "w028 v0.3f is dropped" @ 038aef0.
- **Why** — It needed the raw stacks refetched while the disk was reserved for Scroll 1 crops. Declared, never run.
- **Kind** — scope narrowed.

#### 13. The promised w028 repair
- **Claim** — "text3 and text4 are refetched and ALL their derived products recomputed; the summaries are re-issued." @ 5413b77; "the
  repair is paused for disk and will re-issue them." @ ee25abe.
- **Superseded by** — `### w028 text3/text4 repair dropped`: it cannot change the verdict because text1, text2, text5 and both blanks
  "already put every w028 method at chance" @ d07ddf5.
- **Why** — The disk could not hold both the Scroll 1 work and the refetches. The stated reason overstates: v0.3p scored "text2 0.602"
  and "text5 0.636" on the unaffected crops (a492c1f) — weak, not chance (INFERENCE). The text3/text4 numbers remain on 61 % of their area.
- **Kind** — retracted.

#### 14. w028 and D1 values rounded up
- **Claim** — the values below, printed in `RULES.md`. The v0.3p mean 0.666 is quoted again in the report @ a6dfd42 (which also gives
  the v0.1b / v0.2 means as "0.51 / 0.50"); `docs/RESULTS.md` §8 @ e455383 repeated 0.666, the v0.3p blank1 0.523 and the v0.2 mean
  0.504, and also printed the v0.1b blanks "blank1 0.520 / 0.543, blank2 0.467 / 0.537" and the v0.2 "blank1 0.515 / 0.528", all rounded
  up (0.5195077966213046 / 0.5425413365633472, 0.46699346188256663 / 0.5368141207639716, bc38713; 0.5149910472071102 /
  0.5279106615780657, ee25abe); this release's `docs/RESULTS.md` truncates all of them.
- **Superseded by** — the committed JSON values; corrected in this release.
- **Why** — Rounded half-up, against the release rule (`scripts/release_stats.py` @ 5ba7764: "Numbers are written unrounded; the
  documents truncate toward zero."):

  | printed (commit) | committed value | trunc. |
  |---|---|---|
  | v0.3p held-out mean 0.666 (a492c1f) | (0.6023755578659375 + 0.7140024906217499 + 0.7096619107560864 + 0.6368849225614062) / 4 = 0.6657312204512951, `stats/w028_gate_t1_v0.3p.json` | 0.665 |
  | v0.3p text4 0.710, text1 0.654, blank1 0.523 (a492c1f) | 0.7096619107560864, 0.6535203244570624, 0.5227245435104652 | 0.709, 0.653, 0.522 |
  | v0.1b writing-face mean 0.510, best-face mean 0.570 (bc38713) | 0.5098104892186252 (`stats/w028_gate_t1_v0.1b.json`); best-face mean computed from the same file 0.5696358209484002 | 0.509, 0.569 |
  | v0.2 writing-face mean 0.504 (ee25abe) | 0.5037565238179025 (`stats/w028_gate_t1_v0.2.json`) | 0.503 |
  | D1 top δ = 0, pixel / block 0.577 / 0.614; bottom block 0.637; δ = +1 "0.526 / 0.538" (20c16db) | 0.5769538003900161 / 0.6138753676882089; 0.6365558675387333 (δ = −3); 0.5255459099221009 / 0.5377803564114993 (`stats/d1_text1_depth_profile.json`) | 0.576 / 0.613; 0.636; 0.525 / 0.537 |
  | D1b top 0.615, 0.639, 0.603; bottom 0.537, 0.561, 0.571, 0.580 (84f2947) | 0.6149, 0.6387, 0.6028; 0.5368, 0.5607, 0.5706, 0.5795 (`stats/d1b_text1_scale_sweep.json`) | 0.614, 0.638, 0.602; 0.536, 0.560, 0.570, 0.579 |
  | D1c top 0.640, bottom 0.586, peak 0.651, (top+bot)−rough 0.623 (0825de7) | 0.6395, 0.5858, 0.6508, 0.6226 (`stats/d1c_text1_measures.json`) | 0.639, 0.585, 0.650, 0.622 |

  `docs/RESULTS.md` §8 @ e455383 also labels the v0.1b range "text1–text4 0.473–0.592"; the gate judged five text crops, so the label
  should read text1–text5 (text5's 0.504 / 0.561 lies inside the range). Fixed in this release: `docs/RESULTS.md` §8 reads "text1–text5
  0.473–0.592".
- **Kind** — corrected number.

### Era 2 — Scroll 1 gates (2026-09-17 to 2026-09-18)

#### 15. The letter bar, "never edited"
- **Claim** — "Bars (never edited): mean pixel AUC over the 3 held-out crops ≥ 0.80 AND mean letter AUC ≥ 0.90" — `## GATE-S1` @ 038aef0;
  report "Bars: 0.70 (w028), 0.80 px and 0.90 letter (Scroll 1)." @ a6dfd42.
- **Superseded by** — `## Stroke test (declared …; replaces the letter test …)`: "Bar: the declared pass condition becomes pixel AUC >=
  0.80 AND stroke AUC >= 0.90 on the held-out mean." @ d27193f.
- **Why** — The implemented letter test skips components with < 50 % valid pixels (`if mm.sum() < 0.5 * len(yy): continue`,
  `scripts/s1_judge.py` @ acda042), a filter missing from the declaration. At e72979a the v1b "mean letter AUC" (0.59849157054126 with
  `n` 3 in `stats/s1_gate_20231005123336.json`) averaged only the 2 crops where it was defined. Where defined, it swung with the mask:
  v0.1b, at chance on pixels, scored letter 0.99 on segment-2 held2 ("| held2 | 0.557 / 0.99 |", 72ea621). The bar was replaced, the
  held-out set grew from 3 to 7 crops, and the stated justification was itself wrong (entry 34).
- **Kind** — redefined test.

#### 16. The v0.1b sheet mask for Scroll 1
- **Claim** — "Sheet mask = the v0.1b mask rule (on-sheet, macro-damage margin 0.4 mm, grains 0.02–0.1 mm)." — `## GATE-S1` @ 038aef0.
- **Superseded by** — `### Judge mask J (declared … BEFORE re-running …)` @ 55cd58e.
- **Why** — On the finer segment-2 lace the 0.4 mm margin "leaves 3–9 % of each crop (segment 1: 35 %)", and "The 0.4 mm margin served
  the relief method, which is dead." Mask J uses 0.1 mm and every method was re-judged; the old-mask results stay on record.
- **Kind** — redefined test.

#### 17. One global label registration
- **Claim** — the reference is placed "by ONE global scale+offset found by correlation against the team's ds8 ink overview" @ 038aef0;
  zone correlation 0.330, "so 0.33 is near the attainable maximum); visual check at 32 µm/px: label outlines sit on the letters to ≤ 1 px"
  — `### GATE-S1 registration` @ d2bd6a8.
- **Superseded by** — `### Registration refinement (declared … after the v1 verdict …)`: one translation per crop (`local_offset`)
  @ 7375777; report: "drifted up to 1 mm across the 23 cm segment" @ a6dfd42.
- **Why** — Per-crop residual shifts reached "held2 (−384, 0) µm, held3 (998, −230) µm" against strokes ≈ 0.4 mm wide. The team model
  "drops to 0.616 there" (held3, e72979a), which exposed the error.
- **Kind** — redefined test.

#### 18. Registration refinement "within ±1.2 mm"
- **Claim** — a per-crop translation "found by correlation against the team prediction at 8-px (19 µm) resolution within ±1.2 mm" —
  `### Registration refinement` @ 7375777. Release METHODS: "Four training crops of 20231012184424 (held5–held8) sit at the ±640 px
  limit" @ e455383.
- **Superseded by** — the code, `scripts/s1_refine_reg.py` (`pad = 640` canvas px at 2.4 µm, `ds = 8`) @ 7375777, i.e. ±1.536 mm;
  `docs/RESULTS.md` "±640 px = ±1.536 mm" @ d2564a7. `README.md` (Limitations) said "Four training crops sit at the registration
  search limit" through cc5c843. Fixed in this release: `docs/METHODS.md` §2 (±1.536 mm per axis; held6–held8 at the limit, held5 at
  632 px) and `README.md` (Limitations: "Three training crops sit at the registration search limit and one within 8 px of it").
- **Why** — Stored offsets (canvas px; mm computed as px × 2.4 µm) exceed 1.2 mm or sit on the search edge, where the optimum may lie
  outside the window: `stats/s1_crops_20231012184424.json` @ 0ce50ac — held3 576 px (1.3824 mm, computed), held5 632 px (1.5168 mm,
  computed), held6–held8 640 px (edge); `stats/s1_crops_20230929220926.json` @ 7e01be5 — held4 −520 px (1.248 mm, computed);
  `stats/c1_confirm_20231005123336.json` @ b370331 — conf2 504 px (1.2096 mm, computed). held5 is at 632, not at the limit. Training
  crop held10 registers at correlation 0.257, below the validation crop held4's 0.307. All affected crops are training crops or C1 windows; the 7 evaluation crops lie inside 1.2 mm (largest 416 px,
  20231005123336/held3, `stats/s1_crops_20231005123336.json` @ d2564a7).
- **Kind** — corrected number.

#### 19. TRAIN-crop letter AUC of v0.3p
- **Claim** — "v0.3p (peak brightness): 0.691 / 0.753." — `### GATE-S1 TRAIN crop results` @ 95cf9a6.
- **Superseded by** — the v1 verdict table, row train: v0.3p "0.691 / 0.713" @ e72979a.
- **Why** — 0.753 is the top-face letter AUC (0.7531914893617021); the declared bottom face scores 0.7129629629629629
  (`stats/s1_gate_20231005123336.json` @ e72979a). Corrected silently.
- **Kind** — corrected number.

#### 20. The depth template "transfers to Scroll 1"
- **Claim** — v1b "identical to v1a: the ink depth signature measured on w028 transfers to Scroll 1." @ 95cf9a6; `STATE.md` "A
  22-number depth template measured on w028 transfers to Scroll 1 unchanged." @ a92863a.
- **Superseded by** — "The depth template does not generalise from TRAIN (0.74) to held1 (0.64)" @ 303bc85; re-judged "Held-out means:
  v1b 0.651 / 0.681" @ 87dd1bc.
- **Why** — The template does transfer between scrolls (v1a ≈ v1b on the TRAIN crop), but the signal it carries is weak and fails
  held-out.
- **Kind** — scope narrowed.

#### 21. Two faces sampled as independent channels
- **Claim** — v3 features "I(k_face+δ) for δ ∈ [−4, 6] (11 depths) on both faces" @ b78a1ca; v5 input "the 22 face-aligned depth samples
  I(k_face+δ), δ ∈ [−4, 6], both faces" @ 1c694f2 (the input of every later ds8 model: v5–v8, GP-R1).
- **Superseded by** — "Data-contract correction recorded: k_top and k_bot are both 50 %-of-peak crossings", so the two δ = 0 channels
  are the same quantity, and "the middle 25–35 µm of the sheet is unsampled by our features." @ cdc291e.
- **Why** — The "two faces" are not independent samplings, and no ds8-based model sees the sheet interior.
- **Kind** — design error.

#### 22. held1's letter AUC below 0.5 means "blotches, not strokes"
- **Claim** — letter AUC < 0.5 means letter interiors score lower than blank discs, "i.e. the map is dominated by mm-scale blotches, not
  strokes." @ 303bc85; "held1 is the outlier for every method of ours" (letter AUC < 0.5) @ 5e333a7.
- **Superseded by** — `### Segment 1 under mask J`: "The held1 letter values < 0.5 under the old mask were mask artefacts (letters
  mostly masked);" @ fe9424c.
- **Why** — Under mask J the held1 letter AUCs are 0.717 (v1b), 0.697 (v2) and 0.697 (v3) (trunc., `stats/s1_gate_20231005123336.json`
  @ fe9424c). held1's lower pixel AUC and weaker brightness
  contrast ("text − blank = 1.4 (held1) vs 3.8 (train)", 43a5624) remain valid.
- **Kind** — retracted.

#### 23. The GATE-S1 v1 verdict numbers, and "held3 has no letter"
- **Claim** — "Held-out means: v1b 0.592 / 0.598; v1a 0.589 / 0.595; team 0.829 / 1.000." (commit message: "fails (held-out 0.59 px)");
  "held3 has no letter with ≥ 50 % valid pixels (14 components, heavy damage)" — `### GATE-S1 v1 verdict, all crops` @ e72979a.
- **Superseded by** — `### GATE-S1 re-judged with the refined reference`: "Held-out means: v1b 0.651 / 0.681; v1a 0.649 / 0.686; v0.3p
  0.614 / 0.587; v0.1b 0.515 / 0.423; team 0.935 / 1.000." and held3 letter AUCs now defined (v1b 0.794 trunc., team 1.0, `stats/s1_gate_20231005123336.json`) @ 87dd1bc.
- **Why** — held2 and held3 had been judged against a misplaced reference (entry 17); INFERENCE: held3's undefined letter test was at
  least partly the 998 µm shift, not only damage. Both versions stay on record; the verdict (fail) is unchanged.
- **Kind** — corrected number.

#### 24. The team model as confirmation, and "trained on the same label family"
- **Claim** — "The team model at 0.935 confirms the reference is now well placed." @ 87dd1bc; README Limitations: "The team model is
  trained on the same label family." @ e455383, descended from `docs/reproduce.md`: "on that same label family, so its 0.93–0.98 against
  them is partly circular" @ b438fe0.
- **Superseded by** — the circularity caveat in `docs/reproduce.md` @ b438fe0. Fixed in this release: `README.md` (Limitations) labels
  the label-family statement INFERENCE ("We do not know the team model's training labels").
- **Why** — Both the global and the per-crop placements were "found by correlation against the team" prediction (7375777), so its AUC on
  the placed reference is not independent confirmation. No committed file establishes what the team model was trained on.
- **Kind** — scope narrowed.

#### 25. Parameter counts
- **Claim** — S1-v5 U-Net "≈ 250 k" parameters @ 1c694f2 (`STATE.md` "(≈250 k parameters, 4000 steps)" @ a92863a); GP-R1 "giving 489 k
  parameters and 1.97 s/step" @ 9d4ae3f (again "489 k params" @ c406bf7).
- **Superseded by** — measured "params 270817" (`results/logs/v8.log`) and "parameters 488937" (`results/logs/gpr1.log`) @ bde701a;
  `docs/METHODS.md` "488 937 parameters" @ bde701a and "270 817 parameters" @ e455383. The notebook switched to "The 270 k-parameter net"
  @ 0a834eb without flagging the change.
- **Why** — The U-Net figure was a pre-run estimate; "489 k" rounds 488 937 up. `STATE.md`'s "4000 steps" also predates the 12 000-step
  runs.
- **Kind** — corrected number.

#### 26. Early stopping on a band of the only training crop
- **Claim** — "15 % of TRAIN rows (a contiguous band) held out for early-stopping only." @ 1c694f2; v6: "same early-stopping band on
  segment-1 TRAIN" @ 3816e30.
- **Superseded by** — `### v6 amended BEFORE it runs`: "early stopping on a WHOLE separate crop instead of a row band" @ b9ca77b.
- **Why** — v5's "validation BCE rose monotonically from 0.657 (step 0)", so a band of the training crop could not select a generalising
  checkpoint; the early-stopped v5 was its initialisation. The v6 training set also shrank from "segment-1 TRAIN + 8 crops" (0a834eb) to
  "segment-1 TRAIN + 7 extra crops." (b9ca77b).
- **Kind** — design error.

#### 27. Letter AUCs "of 0.70–0.75" and how much they were "inflated"
- **Claim** — S1-v2 held-out "mean 0.683 / 0.703" @ 5e333a7; under mask J "v2 0.681 / 0.745" @ fe9424c.
- **Superseded by** — `### Stroke test results`: "The earlier letter AUCs of 0.70–0.75 were inflated by the component test's
  valid-pixel rule." @ a0f3f57.
- **Why** — The letter numbers rest on a filtered, partly undefined test (entry 15). The size of the inflation was overstated: on the
  same 3 segment-1 crops v2's stroke AUCs are 0.6791, 0.8309 and 0.6705 (`stats/stroke_test.json` @ a0f3f57), mean
  0.7268333333333333 (computed; 0.726 trunc.), against letter 0.7452462304083385 (`stats/s1_gate_20231005123336.json` @ fe9424c) — a
  difference of 0.018 (computed from the unrounded values, trunc.). INFERENCE: the notebook set 3-crop letter means against 7-crop stroke means.
- **Kind** — corrected number.

#### 28. `STATE.md` as the project status
- **Claim** — "**No submission ready. No method of ours reads verified text at the declared bar.**", with v1 0.651 / 0.681, v2 0.683 /
  0.703, papyrus subtraction 0.515, and v3 and v5 "are running" — `STATE.md` @ a92863a (last edited 602b6b6).
- **Superseded by** — `### Segment 1 under mask J` @ fe9424c; the S1-v3 and S1-v5 results (4db0997, b9ca77b); `## v8 RESULT` @ bc24d20
  and `## Ensemble E RESULT` @ 49be302; archived as `archive/docs/STATE_2026-09-17.md` @ b370331.
- **Why** — Never updated after 602b6b6: mask J changed the numbers ("v1b 0.646 / 0.662 | v2 0.681 / 0.745"), v3 and v5 failed, and v8
  and E later pass the redefined bars on the mean. "No submission" still holds for reading new text: no legible character has been
  recovered (R1, R2).
- **Kind** — scope narrowed.

#### 29. The team model's range, "0.94–0.98"
- **Claim** — "The 0.94–0.98 of the team model therefore comes from spatial integration over strokes and letter shapes," — `### D2 result`
  @ 6d1c078; report "with the team model's 0.94–0.98 on the same crops" @ a6dfd42; `docs/reproduce.md` "its 0.93–0.98 against them"
  @ b438fe0.
- **Superseded by** — re-judged table, team held3 0.857 / 1.000 @ 87dd1bc; per-crop team pixel AUCs in
  `results/per_crop_evaluation7.csv` @ 5ba7764.
- **Why** — Over the 7 evaluation crops under mask J the team range is 0.8517727032590168 – 0.978177856332221 (0.851 – 0.978 trunc.).
  The same report also says "The team model reads the same crops at 0.86–0.98", contradicting its own 0.94–0.98.
- **Kind** — corrected number.

#### 30. The calibration report's results table
- **Claim** — Scroll 1 held-out (px / letter) column: v0.1b/v0.2 0.515 / 0.423, "| v0.3p smoothed band brightness | density | 0.666 |
  0.614 / 0.587 |", v1 0.649 / 0.686, v2 0.683 / 0.703, v3 0.657 / 0.666, team 0.935 / 1.000; "Linear methods over this contrast
  saturate at 0.65–0.68 px held-out" — `docs/report_2026-09-17.md` @ a6dfd42.
- **Superseded by** — `### Segment 1 under mask J` @ fe9424c and `### Segment 2 under mask J` @ 72ea621. The report appended mask-J
  pixel numbers ("Under mask J (declared; judged area 55 % on segment 1, 33 % on segment 2)…", 5bd212b) but left the table unchanged.
- **Why** — Under mask J the segment-1 held-out means are "v0.1b 0.544 / 0.658 | v0.3p 0.628 / 0.664 | v1a 0.644 / 0.659 | v1b 0.646 /
  0.662 | v2 0.681 / 0.745 | v3 0.659 / 0.666 |", "v5 0.531 / 0.460 | team 0.932 / 0.999."; across the 7 crops "v2 0.64, v3 0.63".
- **Kind** — corrected number.

#### 31. Segment 2: "Same ceiling as segment 1"
- **Claim** — "Same ceiling as segment 1 (0.65–0.68):" the linear family "saturates identically" (v3 0.683, v2 0.677, team 0.958) —
  `### GATE-S1 transfer segment 20231210121321` @ 7e01be5 (commit message: "linear ceiling 0.68 confirmed"); `STATE.md` "v3 0.683, v2
  0.677, team 0.958", v5 "fails (0.51–0.53)" @ 602b6b6.
- **Superseded by** — "so the transfer numbers above rest on tiny areas" @ 55cd58e; `### Segment 2 under mask J`: "Means (4 crops): v0.1b
  0.565 | v0.3p 0.594 | v1a 0.593 | v1b 0.595 | v2 0.608 | v3 0.610 | v5 0.507 | team 0.927" @ 72ea621.
- **Why** — The originals rest on 3–9 % of each crop; with "judged area ≈ 33 % of each crop" our linear methods fall by about 0.07
  (v3 0.683 → 0.610, v2 0.677 → 0.608), and v5 (0.507) is below the stated 0.51–0.53. `STATE.md` was never updated.
- **Kind** — corrected number.

#### 32. The v6 plan
- **Claim** — "S1-v6 = the v5 architecture and recipe trained on segment-1 TRAIN plus the 4 densest" windows of two extra segments
  @ 3816e30; report: "v6 = same net trained on 9× more verified text" @ a6dfd42.
- **Superseded by** — `## Data-integrity incident 3`: "**v6 is invalid.**", stopped "at step 4000 of 12000 and its checkpoint is
  discarded, not judged." @ a76fdba; replaced by v6b @ 3c19230.
- **Why** — 7 of its 8 training crops and its validation crop had no blank pixels (entry 33), so its falling validation BCE "(0.657 →
  0.022)" measured only "predict ink everywhere".
- **Kind** — invalidated run.

#### 33. The training-segment blank veto
- **Claim** — blank = no label AND ≥ 0.3 mm from any label AND "team ds8 prediction < 0.10 at that pixel" —
  `### Declared BEFORE the v6 preparation runs` @ 4043cae.
- **Superseded by** — `## Data-integrity incident 3`: the veto redeclared as the team prediction "below its own 40th percentile" over the
  crop's masked, label-free area @ a76fdba.
- **Why** — The team's overview JPEG never falls below 0.10 ("below 0.10 = 0.000 on 20230929220926/held1", likewise on two crops of
  20231012184424), so every extra-segment training crop had zero negatives.
- **Kind** — design error.

### Era 3 — E1, stroke test, local test L, v6b, v6c, v7 (2026-09-18)

#### 34. The letter test "UNDEFINED on 5 of the 7 evaluation crops"
- **Claim** — the letter test "is UNDEFINED on 5 of the 7 evaluation crops and the 0.90 letter bar cannot be evaluated" —
  `## Stroke test (declared …)` @ d27193f. Repeated in this release's drafts: README "a letter-level test that silently became undefined
  on 5 of 7 crops" and "Undefined on 5 of 7 crops here"; METHODS "undefined on 5 of 7 evaluation crops under mask J" @ e455383.
- **Superseded by** — `stats/s1_gate_20231005123336.json` @ fe9424c and `stats/s1_gate_20231210121321.json` @ 72ea621, both committed
  **before** d27193f: under mask J the letter AUC is defined on segment-1 held1–held3 and segment-2 held2 and held4, and "Letter AUC stays
  undefined on held1/held3" of segment 2 (72ea621). Corrected in this release: `README.md`, `docs/METHODS.md` and the
  `inkeval/metrics.py` docstring give 2 of 7 under mask J and 4 of 7 under the original mask after the per-crop refinement.
- **Why** — Under mask J it was undefined on 2 of 7. Under the original 0.4 mm mask after the per-crop refinement it was undefined on 4 of
  7 (all of segment 2, "Letter AUC was undefined on all four", 7e01be5; segment-1 held1–held3 defined, 87dd1bc). "5 of 7" matches only
  the pre-refinement segment-1 verdict (held3 undefined, e72979a) combined with segment 2. `RULES.md` was never corrected.
- **Kind** — corrected number.

#### 35. Stroke-test disk counts, and disks drawn "to avoid overlap"
- **Claim** — disks drawn "with seed 0 on a 0.25 mm grid to avoid overlap." @ d27193f; results "defined everywhere (175–760 disks per
  class per crop)" — `### Stroke test results` @ a0f3f57.
- **Superseded by** — `stats/stroke_test.json` @ a0f3f57, committed with the claim: per evaluation crop `n_ink` 37–202 and `n_blank`
  272–761; `scripts/stroke_test.py` places centres with `g[r:-r:r, r:-r:r] = True`, r = the disk radius ("radius 0.25 mm (104 px at 2.4
  um)") @ d27193f. Corrected in this release: `docs/METHODS.md` §9 says that neighbouring disks overlap, and `docs/RESULTS.md` §2
  gives ink 37–202 and blank 272–761 disks per evaluation crop.
- **Why** — The counts contradict the file committed with them, and centres one radius apart give overlapping disks. The unit of
  inference is the crop, not the disk.
- **Kind** — corrected number.

#### 36. Integrating "over a stroke-sized support gains nothing"
- **Claim** — the stroke test "does NOT rescue any method: integrating our scores over a stroke-sized support gains nothing" —
  `### Stroke test results` @ a0f3f57.
- **Superseded by** — 7-crop means in `results/stats_evaluation7.json` @ 5ba7764.
- **Why** — "does NOT rescue any method" stands; "gains nothing" does not. Stroke minus pixel AUC: v2 0.6869714285714286 −
  0.639650986922841 = +0.047, v3 +0.039, v1b +0.042, team +0.046 (all trunc.). INFERENCE: the sentence compared against segment-1 pixel
  means.
- **Kind** — corrected number.

#### 37. "a level effect, not a profile-shape effect"
- **Claim** — "It is a level effect, not a profile-shape effect (LVL 0.663 > SHAPE21 0.636 LOCO)." — `### E1 partial results` @ cdc291e.
- **Superseded by** — `stats/explore/es_DECLARATION.md` `### Verdict`: "The weaker form - the profile's SHAPE, not only its level,
  carries ink information - is SUPPORTED" @ 8fa65b7.
- **Why** — Shape descriptors add "+0.026 held-out over using the same 22 channels linearly at the same scales, on 7/7 crops." The literal
  edge-steepening hypothesis is refuted and level still dominates. The verdict was written only to the side file; `RULES.md` was never
  updated. This release reports the finding in `docs/RESULTS.md` §9 (row E1-EDGESHAPE).
- **Kind** — scope narrowed.

#### 38. "The evaluation crops are touched once"
- **Claim** — E1 reports "the evaluation crops … once" @ 47febe8; v7: "The evaluation crops are touched once, at the end." @ 7d30ea7;
  headline results read as unbiased ("**the first method of ours to pass both declared bars**", bc24d20; "best result of the project",
  49be302).
- **Superseded by** — `## Confirmation test C1`: "Even with every individual judgement made once, the SEQUENCE adapts to the evaluation
  set, so the headline numbers carry an unknown optimistic bias." @ 46a4bfc.
- **Why** — v7 was designed after "the regional component was noticed via L measured on the EVALUATION crops" (7d30ea7), and every later
  method after earlier numbers on the same 7 crops. The size of that bias is what C1 (pre-registered 46a4bfc; result: see docs/RESULTS.md
  §5) measures.
- **Kind** — scope narrowed.

#### 39. v7 as "hand-built physics", independent of the team model
- **Claim** — v7 tabulated as "| v7 (best hand-built physics) |" beside methods with no team-model input — `## Ensemble E RESULT`
  @ 49be302; README "**Before** — best hand-built physics (v7)" @ e455383; the frozen "hand-built baseline" of C1 @ 46a4bfc.
- **Superseded by** — `scripts/s1_v7.py` loads `ds8_y.npy` (line 38 @ 45fe9e0; the same line @ d2564a7 after the 4c630c4
  reformulation), which `scripts/run_fix_veto.sh` rebuilds:
  "Rebuild the training-segment class masks with the redeclared quantile veto, then ds8_y, then refit v7." @ 96ab51d. Release METHODS
  labels v7's labels "**team-vetoed**" @ e455383.
- **Why** — v7's negatives were chosen with the team model in the loop — the channel control v6c measured at +0.018867086460212894 pixel
  for v6b (`results/stats_evaluation7.json`, entry 47) — and v7 never had a no-veto control. INFERENCE: its role as the hand-built
  comparator, including in C1, carries this unmeasured dependence.
- **Kind** — scope narrowed.

#### 40. "stroke half-width median 0.161 mm", measured on the evaluation crops
- **Claim** — "Measured on the 7 evaluation crops:" … "Label geometry measured: stroke half-width median 0.161 mm, max 0.618 mm." —
  `### E1 reference-noise audit` @ 3c19230; it set E's smoothing, "half the measured stroke half-width (0.161 mm median, from the E1 label
  geometry)" @ 5915848.
- **Superseded by** — `scripts/explore/au_step1_geom.py` (now `archive/scripts/explore/au_step1_geom.py`) "AUDIT step 1 (TRAINING
  crop only): label geometry." and
  `stats/explore/au_step1_geom.json` (only `20231005123336/train`: median of `d_in_mm_quantiles_on_text` 0.1606, `d_in_mm_max` 0.6182)
  @ cdc291e, committed before the claim.
- **Why** — Wrong crop set and wrong quantity: it is the TRAIN crop's median distance from a text pixel to the label edge, not a
  half-width. Stroke width also appears as "≈ 0.4 mm" (7375777) and "Measured stroke width 0.70 mm." (cdc291e). E's parameter came from a
  training crop and was fixed in advance, so there is no leakage; only the description is wrong. The printed 0.161 also rounds 0.1606 up
  (trunc. 0.160). Not corrected in this release: `docs/METHODS.md` §8 (method E) still says "half the measured median stroke
  half-width 0.161 mm".
- **Kind** — corrected number.

#### 41. v6b as a test of the 12 000-step recipe
- **Claim** — v6b trained with "… weight decay 1e-4, 12 000 steps, seed 0)", judged once — `## Method v6b` @ 3c19230.
- **Superseded by** — `### v6b result`: "the result is therefore a statement about a LIGHTLY trained network, not about the declared 12
  000-step recipe." @ db529dd.
- **Why** — The judged checkpoint is "**step 750 of 12 000**" (validation minimum, BCE 0.704); the network memorised its 8 crops within a
  few hundred steps.
- **Kind** — scope narrowed.

#### 42. L "re-measured there first"
- **Claim** — "and L is re-measured there first to confirm the effect exists in training data" — `## Method v7` @ 7d30ea7.
- **Superseded by** — `### Honesty note on v7's motivation`: "So the regional-removal step is NOT confirmed on training data." @ 81d26cc.
- **Why** — "7 of the 8 training crops have no score maps"; on segment-1 TRAIN "L = 0.827 is LOWER than its stroke" AUC 0.879, the
  opposite sign. Regional removal became one leave-one-crop-out candidate among five.
- **Kind** — scope narrowed.

#### 43. L: a local comparison "is EASIER", and "no local information" for v0.1b
- **Claim** — comparing a stroke with nearby blank "is EASIER (+0.05 mean, up to +0.13 on seg1 held1/held2)" for v1b/v2/v3; for v0.1b "L =
  stroke = 0.590: it has no local information either" — `### Local stroke test L result` @ 7d30ea7.
- **Superseded by** — the section's own means ("v1b 0.706/0.660 | v2 0.697/0.687 | v3 0.722/0.671"); `results/stats_evaluation7.json`
  @ 5ba7764.
- **Why** — L minus stroke is +0.046 for v1b (0.7061714285714286 − 0.6597714285714286) and +0.050 for v3 (trunc.), but only +0.010 for v2
  (0.6973142857142857 − 0.6869714285714286, trunc.). INFERENCE: v0.1b's L of 0.5901857142857142 is above 0.5, i.e. weak rather than absent
  local information.
- **Kind** — scope narrowed.

#### 44. v7's first fit
- **Claim** — "Implement method v7 as declared" (fit on the 8 training crops) @ 45fe9e0.
- **Superseded by** — `## Data-integrity incident 3`: "**v7's first fit failed** for the same reason" @ a76fdba (05:43:12 UTC); process
  note @ 4c630c4 (06:28:57 UTC): a v7 fit — called "The first v7 fit" there, but recorded after the refit was queued in 96ab51d
  (05:44:34 UTC); INFERENCE: it was the refit — was "killed by the OOM reaper (8.9 GB resident)" and rewritten with Gram accumulation.
- **Why** — With every negative removed by the veto (entry 33), leave-one-crop-out folds had no negatives and returned undefined AUC. The
  refit used the quantile veto (96ab51d) and the constant-memory reformulation.
- **Kind** — invalidated run.

#### 45. The team model's 0.932, and other segment-1 numbers, in 7-crop tables
- **Claim** — v7 result: "team 0.932 / 0.976 / 0.983.", comparators "v2 0.681 / 0.687 / 0.713; v3 0.659 / 0.671 / 0.735;", and v7
  "slightly below v2" on pixel AUC — `### v7 result` @ 05d84a7. The 0.932 repeated @ db529dd, cd3ea3d, bc24d20 ("remains ahead at
  0.932/0.976."), c406bf7.
- **Superseded by** — `## Ensemble E RESULT`: "| team 2.4 µm model | 0.929 | 0.976 | 0.983 |" @ 49be302 (switched without a note);
  `results/stats_evaluation7.json` @ 5ba7764: team 0.929004087705171, v2 0.639650986922841, v3 0.6309096209997238, v7
  0.6683960321669036. Stated in this release (`docs/RESULTS.md` §4).
- **Why** — 0.932, 0.681 and 0.659 are segment-1 3-crop pixel means (fe9424c; the team's three segment-1 values in
  `results/per_crop_evaluation7.csv` average 0.9321661023061054, computed), placed beside 7-crop values. The L comparators 0.713 / 0.735
  match neither the L table in the same file (0.697 / 0.722, 7d30ea7) nor the release (0.6973142857142857 / 0.7215857142857143). Over the
  same 7 crops v7 is above v2 on pixel AUC.
- **Kind** — corrected number.

#### 46. "v6b PASSES the pixel bar"
- **Claim** — "**v6b PASSES the pixel bar (0.804 ≥ 0.80)" — `### v6b result` @ db529dd.
- **Superseded by** — `results/stats_evaluation7.json` @ 5ba7764: v6b pixel 0.8035827835511089, CI [0.7648430705786049,
  0.8499634376035186].
- **Why** — A margin of 0.003 (trunc.), 3 of 7 crops at or above 0.80, and a crop-bootstrap interval spanning the bar. The stroke mean is
  0.8905571428571427 (0.890 trunc.; printed 0.891). The verdict — no pass on both bars — is unchanged.
- **Kind** — scope narrowed.

#### 47. Control v6c: "the veto is worth +0.02, not the result"
- **Claim** — commit message "the veto is worth +0.02, not the result"; v6c "holds near v6b (−0.019 pixel, −0.017 stroke)" —
  `### Control v6c result` @ cd3ea3d.
- **Superseded by** — `results/stats_evaluation7.json` `paired_differences` v6b−v6c @ 5ba7764.
- **Why** — Pixel +0.018867086460212894 [0.008836696537462187, 0.028754113949181814], positive on 7 of 7 crops; stroke
  +0.016699999999999986 (trunc. +0.018 pixel, +0.016 stroke). INFERENCE: "not substantially distillation" stands, but on pixel AUC the
  channel is consistently non-zero (7 of 7, CI excludes 0); on stroke the CI [−0.0011428571428571596, 0.03238749999999998] includes 0
  (6 of 7 positive). v6c's pixel mean is 0.7847156970908958 (0.784 trunc.).
- **Kind** — corrected number.

#### 48. Rounded-up differences: the two-face gain and the v7 gap
- **Claim** — "Two-face features gain only +0.008 over one face." @ cdc291e; "Training LOCO 0.742 against held-out 0.668 is a 0.074
  generalisation gap" @ 05d84a7.
- **Superseded by** — `stats/explore/tf_step5_heldout.json` (held-out mean ALL 0.6432, BOT 0.6355) @ cdc291e;
  `stats/s1_v7_weights.json` `loco_mean` 0.7415620423091235 @ 05d84a7, with v7 pixel 0.6683960321669036
  (`results/stats_evaluation7.json` @ 5ba7764).
- **Why** — 0.6432 − 0.6355 = 0.0077 (trunc. 0.007); 0.7415620423091235 − 0.6683960321669036 = 0.073 (trunc.). Both were computed from
  rounded terms and rounded up.
- **Kind** — corrected number.

### Era 4 — v8, GP-R1, ensemble E, reading runs, post-hoc D3 (2026-09-18 to 2026-10-15)

#### 49. v8's data rule: 16 crops
- **Claim** — the crop rule "is extended from 4 to 8 windows on 20230929220926" and 20231012184424; "Training set: 1 + 8 + 7 = 16 crops" —
  `## Method v8` @ f3b43d3.
- **Superseded by** — `### v8 data rule AMENDED (… before any crop was prepared)`: "1 (segment-1 TRAIN) + 4 + 10 = 15 crops" @ 8a3998f.
- **Why** — Infeasible as declared: 20230929220926 admits no further strict window, while "20231012184424 supports 7 more". Amended
  before any crop was built, criteria unchanged.
- **Kind** — design error.

#### 50. The three remaining labelled segments "CANNOT be added"
- **Claim** — "the three remaining labelled segments (20231005123333, 20231007101615, 20231012184423) CANNOT be added" — `## Method v8`
  @ f3b43d3.
- **Superseded by** — "20231012184424 (label 20231012184423, 23552×15872)" @ 3816e30; `results/input_manifest.json` "published as
  20231012184423" @ 412b7c7.
- **Why** — 20231012184423 is already the label of training segment 20231012184424, so only two unused labelled segments remain.
  Uncorrected in `RULES.md`; this release's `docs/METHODS.md` §1 gives the label mapping.
- **Kind** — corrected number.

#### 51. "data was a binding constraint"
- **Claim** — "The judged checkpoint is step 9500 of 12 000 … More data removed the immediate memorisation …, which is the mechanism
  behind the gain and confirms data was a binding constraint." — `## v8 RESULT` @ bc24d20.
- **Superseded by** — `models/v8_unet.pt.json` `val_curve` @ 412b7c7; `results/stats_evaluation7.json` v8−v6c @ 5ba7764; this release
  attributes the gain jointly (`README.md`, `docs/RESULTS.md` §3).
- **Why** — v8 changed two things at once: data (8 → 15 crops) and "**Checkpoint selection by validation pixel AUC**" (f3b43d3). Its
  validation BCE still bottoms at step 250 (0.6002644300460815) and rises to 0.9818353652954102 at step 12 000; step 9500 was chosen by
  validation AUC (0.7026650761409663, where validation BCE is 0.916637122631073). The late step reflects the selection rule, not the end
  of memorisation. The joint effect is v8 − v6c = +0.05478432189855577 [0.02752120488541527, 0.08476158690902418] pixel, 7 of 7 crops.
- **Kind** — scope narrowed.

#### 52. The resolution question: D2, then GP-R2
- **Claim** — Strategy note: "so it is worth one cheap diagnostic first." and `## Diagnostic D2` @ 0e86155; GP-R2 at 9.6 µm "Declared
  now, run after GP-R1." @ 3f88fdf; "GP-R2 at 9.6 µm is the declared next test and is now the highest-value experiment in the project."
  @ c406bf7; "GP-R1 established it is not architecture; resolution is the" declared next test @ 49be302.
- **Superseded by** — "Diagnostic D2 is deferred: GP-R2 answers the same resolution question directly." @ 3f88fdf; no GP-R2 result
  exists in `RULES.md` through d2564a7; the tests declared next were C1 (46a4bfc), D3 (bf040d0) and N1 (2e92310).
- **Why** — Neither D2 nor GP-R2 was run, so "The candidates left are resolution (we feed 19.2 µm; the Grand-Prize work used 7.91 µm)
  and the scale of data and compute" (c406bf7) remains an untested hypothesis. The name D2 also collides
  with the per-depth `### D2 result (2026-09-17 21:55 UTC)` of 6d1c078.
- **Kind** — scope narrowed.

#### 53. GP-R1 as a reproduction of the winning approach
- **Claim** — failure mode 3: "We have never once reproduced a known-good recipe as a baseline" @ 0e86155; "**GP-R1** — GP-style
  architecture and training protocol on the EXISTING 19.2 µm pooled stacks" @ 3f88fdf; GP-R1 "retires failure mode 3 of the strategy
  note" @ c406bf7.
- **Superseded by** — `### GP-R1 parameters fixed`: "the faithful-width 3D encoder costs 6.7 s/step (22 h for 12 000 steps)", so widths
  8/16/32 and "Step budget **4000** (2.2 h)" @ 9d4ae3f.
- **Why** — Failure mode 3 was true when written and was addressed, but by a CPU-scaled reproduction at 19.2 µm (the original used 7.91 µm
  and GPUs). Conclusions about "architecture" apply only to that setting (entry 60).
- **Kind** — scope narrowed.

#### 54. v8 "PASSES"; GP-R1 and v8 "Both pass both bars, and they are tied"
- **Claim** — "**PASSES: pixel 0.840 >= 0.80 AND stroke 0.917 >= 0.90**" and "**the first method of ours to pass both declared bars**"
  @ bc24d20; "**Both pass both bars, and they are tied**" @ c406bf7.
- **Superseded by** — the crop-level bootstrap in `results/stats_evaluation7.json` @ 5ba7764.
- **Why** — The passes hold on the declared criterion, the point mean. v8's stroke CI lower bound is 0.8904428571428572 < 0.90 (its pixel
  lower bound, 0.805444814902787, clears); GP-R1's pixel CI starts at 0.7956104744102388 and its stroke CI at 0.8740571428571429, both
  below the bars; v8 − GP-R1 pixel CI is [−0.014611542734137466, 0.04230588226788047], so a v8 − GP-R1 difference anywhere from −0.014
  to +0.042 (trunc.) cannot be excluded. Of our methods, only E clears both bars at the lower bound (0.846068183828077,
  0.9027360714285714). The notebook itself recorded that v8 clears both bars
  on only "5 of 7" crops.
- **Kind** — scope narrowed.

#### 55. Headline means rounded half-up
- **Claim** — means and differences printed in `RULES.md` and commit messages (table below).
- **Superseded by** — `results/stats_evaluation7.json` @ 5ba7764; truncated in this release (`docs/RESULTS.md` §2–§3).
- **Why** —

  | printed (commit) | committed value | trunc. |
  |---|---|---|
  | v8 mean row 0.840 / 0.917 / 0.908 (bc24d20) | 0.8395000189894518 / 0.9167714285714287 / 0.9077714285714286 | 0.839 / 0.916 / 0.907 |
  | GP-R1 row 0.828 / 0.920 (c406bf7) | 0.8276284576194444 / 0.9196428571428571 | 0.827 / 0.919 |
  | v6b mean row 0.804 / 0.891 / 0.923 (db529dd) | 0.8035827835511089 / 0.8905571428571427 / 0.9227285714285715 | 0.803 / 0.890 / 0.922 |
  | v6c row 0.785 / 0.874 / 0.882 (cd3ea3d) | 0.7847156970908958 / 0.873857142857143 / 0.8818142857142858 | 0.784 / 0.873 / 0.881 |
  | E local L 0.935 (49be302) | 0.9348142857142857 | 0.934 |
  | team stroke 0.976 (05d84a7 … 49be302) | 0.9758000000000001 | 0.975 |
  | GP-R1 "−0.012 pixel, +0.003 stroke against v8" (c406bf7) | v8 − GP-R1 = 0.011871561370007475 / −0.0028714285714285565 | GP-R1 − v8 = −0.011 / +0.002 |
  | gap to team "0.053 pixel and 0.041 stroke" (49be302) | team − E = 0.052732456164895095 / 0.04049999999999998 | 0.052 / 0.040 |

  Stroke and local means here are means of 4-decimal per-crop values (entry 65); 0aeb4b2 recomputed those of v8, GP-R1, E and the team
  model at full precision, and every truncated value in the last column is unchanged.
- **Kind** — corrected number.

#### 56. R1: a negative control chosen by distance
- **Claim** — a control window "OFF any text column (the farthest such window from the labelled zone on the same segment)" —
  `## Reading run R1` @ a31bbc1.
- **Superseded by** — `## R1 RESULT`: "**The negative control was invalid by construction, and that is a design error of mine.**"
  @ e8d6a6c; R2 reports the control windows "as additional unread windows" @ c74372d; C1 uses a "cross-crop label-swap null" @ 46a4bfc.
- **Why** — Distance from labels is not absence of ink: the team model finds 2 618 k confident-ink pixels in the segment-1 control window,
  against 810 k in the reading window (R1 table).
- **Kind** — design error.

#### 57. R1: windows adjacent to read text
- **Claim** — take the window nearest the labelled zone, because "adjacent to read text is where the same column most likely continues"
  — `## Reading run R1` @ a31bbc1.
- **Superseded by** — `## R1 RESULT`: "Regions left unread by papyrologists are plausibly the harder ones, which is a selection effect R1's
  window rule walked straight into" @ e8d6a6c.
- **Why** — The rule selected the papyrus most likely to be hard; this was recorded only after the run, and R2 reused the same windows.
- **Kind** — design error.

#### 58. R1: the team model "not used to … score, threshold"
- **Claim** — the team model "is not used to select, score, threshold or adjust anything in R1."; only the renders are reported —
  `## Reading run R1` @ a31bbc1.
- **Superseded by** — `## R1 RESULT`: "AUC of v8 separating the team model's confident ink (> 0.80) from its confident blank (< 0.20)"
  @ e8d6a6c; adopted for R2 ("The same agreement statistic", c74372d); given a null by N1 (bde701a).
- **Why** — A team-thresholded statistic was added after the renders were seen, so the R1 AUCs are post-hoc. The R1/R2 values "were
  computed by inline code that was not committed" (`docs/RESULTS.md` @ e455383); the 0.80 / 0.20 thresholds first appear in committed
  code as `team[k] = (t > 0.80, t < 0.20)` in `scripts/n1_reading_null.py` @ bde701a.
- **Kind** — redefined test.

#### 59. Reading-run agreement ranges
- **Claim** — R1: "v8 detects ink weakly (AUC 0.72-0.87)" (commit message) and "at 0.72–0.87" @ e8d6a6c, repeated in the R2 declaration
  @ c74372d; R2: "at 0.80–0.89" @ 9de8704; N1 declaration: "0.72–0.89 (v8) and 0.80–0.89 (E)" @ 2e92310. This release's drafts:
  `docs/RESULTS.md` "agreement with the team model 0.72–0.87 (v8) and 0.80–0.89 (E)" and README "AUC 0.79–0.88 per" window @ e455383.
- **Superseded by** — the R1 table (0.802, 0.717, 0.739, 0.865) @ e8d6a6c and the R2 table (0.887, 0.804, 0.797, 0.880) @ 9de8704; N1:
  "v8 matched 0.801 / 0.716 / 0.737 / 0.864" and "E matched 0.886 / 0.804 / 0.793 / 0.879" @ bde701a. Corrected in this release:
  `README.md` gives E's N1 range 0.793–0.886, and `docs/RESULTS.md` §7 both the N1 ranges and the ranges as first recorded.
- **Why** — Both ranges were rounded outward: as recorded R1 spans 0.717–0.865 and R2 0.797–0.887. The N1 declaration's v8 maximum of
  0.89 matches neither the R1 table (0.865) nor N1 (0.864). The two release drafts disagreed with each other (R2 values vs N1 values); N1's
  5 % subsample gives slightly different values from R1/R2.
- **Kind** — corrected number.

#### 60. "the winning architecture buys us nothing"
- **Claim** — `## GP-R1 RESULT (2026-09-18 21:20 UTC) — the winning architecture buys us nothing at this resolution` @ c406bf7; "GP-R1
  established it is not architecture" @ 49be302.
- **Superseded by** — `## D3 RESULT`: like-for-like GP-R1 − v8 "+0.009 [−0.019, 0.033] (5/7)"; the published claim is narrowed to
  "no measurable architecture effect at 19.2 µm on 7 crops" @ bde701a.
- **Why** — The published comparison was confounded by upsampling (entry 63): GP-R1 gains +0.02967406643906236 pixel from rank-normalising
  and smoothing, v8 only +0.008385350693501834 (`results/d3_decomposition.json`). Like for like it is still a tie, with the sign reversed.
  The 49be302 restatement "GP-R1 established it is not architecture" omits c406bf7's qualifier "at 19.2 µm on 15 crops" (which stays in
  `RULES.md`). The like-for-like interval had no committed source through d2564a7; this release commits it (043ba8d:
  [−0.01940031461976945, 0.03304815913418372], 5 of 7), matching the notebook's truncated [−0.019, 0.033] (entry 64).
- **Kind** — scope narrowed.

#### 61. E's per-crop pass counts
- **Claim** — "Per-crop, 6 of 7 clear the pixel bar and 5 of 7 the stroke bar" — `## Ensemble E RESULT` @ 49be302.
- **Superseded by** — the per-crop table in the same section; `results/per_crop_evaluation7.csv` @ 5ba7764. Corrected in this release
  (the table above; per-crop values in `docs/RESULTS.md` §2).
- **Why** — 7 of 7 crops have pixel ≥ 0.80 (minimum 0.8101339149373259, segment-1 held3) and 4 of 7 have stroke ≥ 0.90 (segment-1 held3
  0.896, segment-2 held3 0.8975 and segment-2 held4 0.8711 fall below). The counts contradict the table they follow.
- **Kind** — corrected number.

#### 62. E's gain credited to ensembling
- **Claim** — "E beats both by +0.036/+0.015 over the better one, which is the ordinary ensembling" gain from decorrelated errors —
  `## Ensemble E RESULT` @ 49be302.
- **Superseded by** — post-hoc `## D3 RESULT` and `results/d3_decomposition.json` @ bde701a.
- **Why** — E also smooths at 0.08 mm. Of E − v8 = +0.03677161255082416 pixel: smoothing alone gives +0.008385350693501834; ensembling
  without smoothing +0.02476475028645775; ensembling given smoothing +0.028386261857322324; and smoothing given ensembling (E − unsmoothed
  rank-mean) +0.012006862264366409 [0.01050117045313578, 0.013413743875808406], 7 of 7 — a pair D3 computed but `RULES.md` does not
  report. D3 itself says "roughly a quarter to a third of the pixel gain being smoothing" (bde701a); computed, smoothing is 0.228
  (alone) to 0.326 (given ensembling) of E − v8 (trunc.), so the lower end is below a quarter. On stroke, E − v8 is not distinguishable from zero at
  n = 7 (CI [−0.0037610516883680284, 0.037627408554458], `results/stats_evaluation7.json` @ 0aeb4b2).
- **Kind** — scope narrowed.

#### 63. D3: which method was upsampled nearest-neighbour
- **Claim** — "the methods being compared were also upsampled differently (v8/GP-R1 nearest-neighbour, v7 bilinear)" —
  `## Post-hoc decomposition D3` @ bf040d0; `scripts/d3_decompose.py` docstring "v8, gpr1 … as published (nearest-neighbour upsampled
  from 19.2 um)" @ bde701a (alignment spaces elided).
- **Superseded by** — `## D3 RESULT`: GP-R1 "was upsampled nearest-neighbour while v8 was upsampled bilinearly" @ bde701a; docstring
  corrected ("v8 bilinear …") @ e455383.
- **Why** — The code: v8 is predicted by `scripts/s1_v5.py` with `scale_factor=8, mode="bilinear"` (line 50 @ 1c694f2; the same call at
  line 70 @ d2564a7);
  GP-R1 by `scripts/gpr.py` line 159, `up = np.repeat(np.repeat(z, F, axis=0), F, axis=1)` (@ 9d4ae3f); v7 by `zoom(…, 8, order=1)`
  (bilinear, @ 45fe9e0). The declaration was corrected only implicitly by the result.
- **Kind** — retracted.

#### 64. D3: the like-for-like architecture interval, and "smoothing contributes nothing" on stroke
- **Claim** — "compared like for like (both smoothed) GP-R1 − v8 = +0.009 [−0.019, 0.033] (5/7)" and "On the stroke metric smoothing
  contributes nothing (−0.002)" — `## D3 RESULT` @ bde701a; the interval repeated in README and `docs/RESULTS.md` @ e455383.
- **Superseded by** — `results/d3_decomposition.json` @ bde701a, committed with the claim; for the interval, UNFOUND through d2564a7:
  `scripts/d3_decompose.py` computes only the pairs e−v8, v8_s−v8, gpr1_s−gpr1, mean_nos−v8, e−mean_nos and e−v8_s (@ bde701a; the same
  pairs @ d2564a7), and the JSON has no `gpr1_s-v8_s` entry. This release adds that pair to the script and regenerates the file from the
  stored per-crop values (043ba8d); the regenerated interval [−0.01940031461976945, 0.03304815913418372] truncates to the notebook's
  [−0.019, 0.033], so the number was right but had no committed source through d2564a7.
- **Why** — Interval: the mean (0.009417154375553047) and 5 of 7 positive crops can be re-derived from the per-crop values in the JSON;
  the interval cannot be traced to any commit through d2564a7. Stroke: v8 smoothed − v8 is −0.0026996330398864543
  [−0.005166241082929068, −0.00011364361437407997] (2 of 7 positive) and GP-R1 smoothed − GP-R1 −0.002054516653930432
  [−0.004046025164390898, −0.0004309950026992431] (1 of 7). Both intervals exclude 0: a small, consistent loss, not nothing.
- **Kind** — corrected number.

### Era 5 — release preparation (2026-10-15)

#### 65. Per-crop stroke and local values stored at 4 decimals
- **Claim** — the release statistics are "written unrounded" (`scripts/release_stats.py` @ 5ba7764), so the stroke and local means in
  `results/stats_evaluation7.json` read as full-precision summaries.
- **Superseded by** — `results/per_crop_evaluation7.csv` @ 5ba7764 stores stroke and local per crop at 4 decimals (E on
  20231005123336:held1: "0.8828924602993242,0.9394,0.9293," against the judge's 0.9393775777052081 / 0.929321519960213 quoted in README
  @ e455383); `results/d3_decomposition.json` @ bde701a recomputes from full precision. Fixed in this release for E, v8, GP-R1, v7
  and the team model: `results/stats_evaluation7.json` and `results/per_crop_evaluation7.csv` take their stroke and L at full precision
  from `results/toolkit_vs_records.json` (0aeb4b2), as `docs/RESULTS.md` §2 states (it also lists the four per-crop values whose
  truncation falls by 0.001). Still open for v6b, v6c, v3, v2, v1b and v0.1b, whose stroke and L exist only as 4-decimal records.
- **Why** — The "unrounded" stroke and local means are means of rounded inputs, so one quantity has two committed values: v8 stroke
  0.9167714285714287 vs 0.916766433285967; E stroke 0.9353 vs 0.9352864106367927; E − v8 stroke 0.01852857142857142 vs
  0.018519977350825938. The truncated 3-decimal values are unaffected (0.916, 0.935, 0.018); pixel AUCs are stored at full precision.
- **Kind** — corrected number.

#### 66. Pre-registration order "proved" by git
- **Claim** — `results/preregistration_order.json` marks the stroke test (declared d27193f) and L (declared cdc291e) as order OK and D3
  as "pending" @ bde701a; README "the git history proves the order", `docs/RESULTS.md` "Every test below was declared … in a commit that
  precedes the commit recording its result.", `docs/REPRODUCE.md` "the commit introducing the declaration precedes the commit introducing
  the result" @ e455383.
- **Superseded by** — git: the stroke-test declaration commit d27193f already contains `stats/stroke_test.json` with results (v2 on
  segment-1 held1: 0.6791), and the L declaration commit cdc291e already contains `stats/local_stroke_test.json` with L for segment-1
  held1–held3 and all 5 methods. This release regenerates the file (34cc327, 18 rows; it still marks the stroke test and L "OK" because
  it compares heading commits) and lists three exceptions in `docs/RESULTS.md` §1: the stroke test, L, and R2, whose maps predate
  c74372d (INFERENCE from file times, which are not in git). `docs/REPRODUCE.md` stated the order "for all 15 completed pre-registered
  tests" without exceptions through cc5c843. Fixed in this release: `README.md` names the three exceptions, and `docs/REPRODUCE.md`
  (Pre-registration order) calls the check "necessary, not sufficient" and names them.
- **Why** — The check compares each declaration with a later result commit, so it cannot see first results committed together with the
  declaration. The file also marks D3 "pending" although `## D3 RESULT` is in the same commit (bde701a), and it was not regenerated when
  `scripts/check_preregistration.py` gained an N1 row (e455383), so it has none.
- **Kind** — scope narrowed.

#### 67. "bit for bit" and "every published number of this study exactly"
- **Claim** — README: the released weights "regenerate the published v8, GP-R1 and E maps **bit for bit**" and the toolkit reproduces
  "every published number of this study **exactly** (`tests/test_published.py`)"; CHANGELOG "a check that regenerates v8, GP-R1 and E
  bit-for-bit from the released weights" @ e455383.
- **Superseded by** — this release states the coverage.
- **Why** — `results/reproducibility_check.json` (412b7c7) covers one evaluation crop of seven (20231005123336:held1);
  `tests/test_published.py` checks crop 20231005123336/held2 only and is skipped when the research data are absent ("full research data
  not on disk"). Fixed in this release: the check covers all 7 evaluation crops (`results/reproducibility_check.json` @ 0e040c1), and
  `README.md`, `CHANGELOG.md` and `SUBMISSION.md` state that coverage ("bit for bit on all 7 evaluation crops", on the release machine);
  `README.md` replaces "every published number" with the 65 of 65 judge records the toolkit reproduces (`results/toolkit_vs_records.json`).
  `tests/test_published.py` still covers held2 only, as `docs/REPRODUCE.md` (Level 1) states.
- **Kind** — scope narrowed.

#### 68. "independently confirmed", and C1 listed as shipped
- **Claim** — README "the pre-registered, independently confirmed" study; SUBMISSION "with a pre-registered and independently confirmed
  Scroll 1 study"; CHANGELOG 1.0.0 "**Confirmation test C1** on six untouched labelled windows" @ e455383.
- **Superseded by** — Fixed in this release: `README.md` and `SUBMISSION.md` no longer say "independently confirmed", and the C1 line
  of `CHANGELOG.md` now follows the committed result (docs/RESULTS.md §5).
- **Why** — No C1 result was committed through d2564a7, so the drafts asserted an outcome before it existed; the outcome is reported only
  as C1 (pre-registered 46a4bfc; result: see docs/RESULTS.md §5). INFERENCE: "independently" also overstates a check run by the same
  authors on held-back windows. The same CHANGELOG entry's "lab notebook to `docs/RULES.md`" was untrue at e455383 (the file was still at
  the root) and becomes true with this release's move.
- **Kind** — retracted.

#### 69. C1's analysis rule fixed in words, operationalised later
- **Claim** — "**Statistical plan for the release (fixed now).**" and the prediction "E clears both bars on the C1 mean (pixel >= 0.80,
  stroke >= 0.90) and beats v7 on every C1 crop." — `## Confirmation test C1` @ 46a4bfc (2026-10-15 04:45:30 UTC).
- **Superseded by** — `scripts/c1_analysis.py` @ d2564a7 (06:08:20 UTC): "Beats v7" is checked on pixel AUC (the primary metric) and
  separately on stroke; shrinkage uses a two-sample crop bootstrap; the team-relative part is labelled post-hoc, "written after 4 of the
  6 C1 pixel values had been seen in the run log". `docs/RULES.md` `## Release corrections to the C1 RESULT` (appended 5ce2d4d) adds
  that by the run log five of the six crops had been judged when the script was committed.
- **Why** — The declaration names no metric for "beats v7" and plans a bootstrap "for every mean and for every" paired difference, not a
  two-sample shrinkage interval. INFERENCE: since these choices were committed in a script written after part of the C1 data had been
  seen, git cannot show that they preceded the data. This entry says nothing about the C1 outcome.
- **Kind** — scope narrowed.

#### 70. Sheet thickness "0.478 (MEASURED)" beside 7-crop means
- **Claim** — README: "sheet thickness alone" … "0.478 (MEASURED)", in a list of 7-crop results @ e455383.
- **Superseded by** — source: "Monitored on TRAIN (verified letters): thickness AUC 0.478" @ 4f9ef66. Fixed in this release: `README.md`
  gives "0.478 (one crop, the segment-1 TRAIN crop)".
- **Why** — It is the single segment-1 TRAIN crop under the old v0.1b mask, not a held-out mean; `docs/RESULTS.md` @ e455383 already
  scoped it ("sheet thickness AUC 0.478 against read text on the Scroll 1 TRAIN crop (4f9ef66)").
- **Kind** — scope narrowed.

#### 71. Runtimes in the release guide
- **Claim** — `docs/REPRODUCE.md` "## Level 5 — retrain from scratch (≈ 7 h + 1.5 h)", level 0 "2.9 s", level 1 "46 s" @ bde701a; README
  `pytest -q` "~45 s: 15 tests (18 with the research data present" … @ e455383.
- **Superseded by** — "## Level 5 — retrain from scratch (≈ 5.5 h training + ≈ 1.7 h preparation)" @ e455383; README "~10 s: 15 pass, 3
  skipped" and REPRODUCE "15 passed, 3 skipped in 9.93s" in a fresh clone, with "18 passed in 46.11s" only when the research data are
  present @ d2564a7; level 0 "≈ 3 s" @ d2564a7 (no re-timing committed; 2.9 s is the only committed value, so "≈ 3 s" rounds it up).
  Fixed in this release in `docs/REPRODUCE.md`: level 5 "5.49 h training, measured; ≈ 1.4–1.7 h preparation, estimated", with the
  estimate derived from the per-crop times it cites; level 0 "2.5 s in a fresh clone"; level 1 "9.1–9.9 s; 46–53 s with the research
  data". Not corrected: `README.md` gives "~10 s" for the 9.13–9.93 s fresh-clone test runs, which rounds up.
- **Why** — Training re-derived from the measured logs ("MEASURED 11 458 s" for v8, "MEASURED 8 334 s" for GP-R1, bde701a): 11 458 s +
  8 334 s = 19 792 s = 5.497 h (computed, trunc.); the release's "≈ 5.5 h" rounds this up. The "≈ 1.7 h preparation" figure has no
  committed derivation: at "~5.5 min each" per training crop (bde701a), 15 crops take 1.375 h (computed). The test-suite times were
  re-timed from a fresh clone without `data/`.
- **Kind** — corrected number.

#### 72. Which commit to run the archived scripts from
- **Claim** — run them "from commit `9de8704`, the last commit" before the release reorganisation — `docs/REPRODUCE.md` @ bde701a.
- **Superseded by** — "run them from commit `bde701a`, the last commit before the release reorganisation (`b370331`)" @ e455383.
- **Why** — 9de8704 (R2 result) is the last commit of the original research run, not the last commit before b370331; six commits
  (46a4bfc, 5ba7764, 412b7c7, bf040d0, 2e92310, bde701a) lie between them, among them the C1 pre-registration and the D3 and N1
  declarations and results.
- **Kind** — corrected number.

#### 73. The face validity rule in METHODS
- **Claim** — "CT at the mesh slice > 0" — `docs/METHODS.md` §4 Sheet geometry @ bde701a.
- **Superseded by** — "CT at the middle slice of the searched range (K//2) > 0" @ e455383.
- **Why** — `scripts/topo_faces.py` tests `kmid = K // 2`, the middle of the searched slice range, not the mesh slice.
- **Kind** — design error.

#### 74. The bundled example kept out of git
- **Claim** — "## Level 0 — demo on bundled real data (2.9 s)" (`docs/REPRODUCE.md`) with `EXAMPLE = os.path.join(HERE, "data",
  "example_scroll1.npz")` (`inkeval/example.py`) @ bde701a, under the `.gitignore` rule `data/` (since d160337).
- **Superseded by** — `.gitignore` `/data/` and `inkeval/data/example_scroll1.npz` tracked @ e455383.
- **Why** — The unanchored rule ignored every directory named `data/`, including `inkeval/data/`, so the demo failed on a clean checkout.
- **Kind** — design error.

#### 75. "drivers no longer cd to an absolute path"
- **Claim** — commit message "drivers no longer cd to an absolute path" @ e455383.
- **Superseded by** — `scripts/run_c1.sh` ran `cd /home/user/megara` (line 5 @ d2564a7, and still at cc5c843). Fixed in this release
  (0db607f): line 5 of `scripts/run_c1.sh` is `cd "$(dirname "$0")/.."`, and no file in `scripts/` contains the absolute path.
- **Why** — run_c1.sh was left untouched while C1 was running; every other driver in `scripts/` dropped the absolute path in e455383.
  The archived drivers keep it, as `docs/REPRODUCE.md` states ("Drivers of that era `cd` to" …).
- **Kind** — scope narrowed.

#### 76. Typed UTC times in notebook headings
- **Claim** — headings carry typed UTC times that read as a timeline, e.g. GATE-S1 "declared 2026-09-17 17:00 UTC, BEFORE any Scroll 1
  stack is read" @ 038aef0.
- **Superseded by** — git commit times; this release uses commit order, not typed times, as the pre-registration evidence.
- **Why** — Several typed times are later than the commit that introduced them: GATE-S1 17:00 vs commit 15:56:42 (038aef0); "found
  2026-09-17 16:30 UTC" vs author time 15:47:48 (5413b77; committer time 15:48:12); stroke test "declared 2026-09-18 03:50 UTC" vs
  03:40:13 (d27193f); stroke results "04:05 UTC" vs 03:43:35 (a0f3f57); incident 3 "found 2026-09-18 06:30 UTC" vs 05:43:12 (a76fdba); R1 RESULT "21:00 UTC" vs 20:48:09
  (e8d6a6c). Only two stamps were ever fixed ("Fix two timestamps in RULES.md", 10d098e). Commit order still supports declared-before-run
  in most cases; entry 66 and `docs/RESULTS.md` §1 list where it does not.
- **Kind** — corrected number.

---

## Not listed here

- Statements that were true when written and are merely dated (for example the repository's visibility as stated in `DATA_NOTICE.md`).
- Release work in progress: files that the drafts at d2564a7 link to but that are created or moved during the release (results sheet,
  C1 outputs, lessons and superseded-claims files, the moved notebook `docs/RULES.md`, three figures). They are release tasks, not
  claims; all of them are present in the release working tree.
- Parameters that move headline numbers but were never declared in the notebook; they are listed in `docs/METHODS.md`
  §11 "Parameters that affect headline numbers but were never declared".
