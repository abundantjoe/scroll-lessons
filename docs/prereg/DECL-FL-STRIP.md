# Pre-registration: DECL-FL-STRIP (copy)

This file reproduces below the line, verbatim except for one omitted sentence (marked, decision 1), the declaration
committed **before any result** of the control-strip experiment. It was committed on 2026-10-14 at 19:14 UTC as
commit `9c80b1f` in the private PHerc0268 repository. The first strip results were seen by 19:50 UTC (the exploratory
metrics were added then) and first committed at 20:22 UTC (commit `3af67f1`). The private history cannot be opened from
here, so the timestamps are stated as recorded (**MEASURED**, not independently verifiable). In this release:
- the exploratory arms (F13 margin fill, FD8 the fill on the displaced copy, and the original run's X13 extrapolated
  padding) are labelled exploratory in the METHODS arms table and the RESULTS §1 control and decisions tables;
- the depth arm (d = -2, decision 6) is reported from the original run only;
- rule 4 is scored with all three of its conditions, including "the band rule (3) not met".

---

# DECL-FL-STRIP: can mass-run strip geometry see known ink? (pre-registered 2026-10-14, before any result)

**Question.** The mass PHerc0268 run (poc/mass/) inked 13-20 node-row strips cut from fit meshes. Their renders have about
30 blank rows at each edge, and about 2/3 of them show ink bands 30-50 px inside the valid edges. The audit
(tools/fl/audit/, 2026-10-14) left two questions open:
- (1) does this geometry hide real letters (false negatives)?
- (2) is the band a model artifact of the blank margins?

**Test.** On the PHerc0343 letters surface (Erwin, concat_w047-w048_R5B2_z9500-11000.tifxyz, 128 x 336 nodes; letter
boxes 6-18 in inputs/..._letter_boxes.json, raw frame, never drawn on a submission image), use the exact mass pipeline:
batch_ink.sh, the 3 villa models, reverse maps, KEEP_RENDER=0. All arms use cols 34:166.

| arm | node rows | depths |
|---|---|---|
| REF | 40:110, full context | d = +1, -2 |
| Z13 | 13-row strips, blank margins as in the mass run: 42:55, 55:68, 68:81, 81:94, 94:107 | d = +1, -2 |
| Z20 | 20-row strips: 42:62, 62:82, 82:102 | d = +1 |
| P13 | the Z13 strips rendered with 2 extra node rows each side (40:57 ... 92:109); only the target 13 rows are scored | d = +1 |
| D8 | the Z13 strips on a copy displaced +8 vox along the outward normal (half the sheet spacing; no-ink arm) | d = +1 |

**Metrics** (tools/fl/ctrl_strip/eval.py). Set S = pixels valid in the arm and in REF, inside the target rows. Box =
inside any letter box. Strong = p > 0.55.
- f_in, f_out: strong fraction inside / outside the boxes.
- E = f_in / max(f_out, 1e-4).
- Recall R = |arm strong & REF strong & box| / |REF strong & box|.
- r = Pearson correlation of arm vs REF over S.
- Band: f055 outside the boxes in rows 20-80 px from the column's valid edge, arm vs REF at the same pixels.
- Coverage: letter-box pixels in the target rows that are valid in the arm, as a share of all letter-box pixels in
  those rows.

**Decisions** (d = +1 unless stated):
1. Strip geometry sees ink: Z13 pooled R >= 0.5, E >= 5 and r >= 0.6. [One sentence omitted.]
2. Same rule for Z20.
3. Edge artifact caused by the blank margins: Z13 band f055 outside the boxes >= 0.01 and >= 3 x REF at the same
   pixels.
4. Padding fixes it: P13 R >= 0.7, r >= 0.8, and the band rule (3) not met. If so, any PHerc0268 re-run renders
   +-2 extra node rows and scores only the target rows.
5. No-ink arm works: D8 f_in <= 0.2 x Z13 f_in.
6. Depth: report R(Z13, d=-2) / R(Z13, d=+1). No threshold; it sizes the depth risk of the d = -2 mass run.

Every arm, number and image is pushed to poc/ctrl343_strips/ by tools/fl/ctrl_strip/run.sh, whatever the outcome.
