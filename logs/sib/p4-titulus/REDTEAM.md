# Red team of logs/p4/HYPOTHESES.md (p4-titulus, v1, 2026-09-26 ~22:30Z)

Provenance: Project HERCULES | owner the owner | [id removed]
Reviewed: origin/claude/gifted-bell-gavnl5 logs/p4/HYPOTHESES.md and COVERAGE.md, as read at 21:45Z.
Integrity: numbers and published text only. No image was viewed and no title word is proposed. Grades as in QA.md. Every probability here is UNCERTAIN (my judgement, with the arithmetic shown).

Summary of the most consequential findings, in order of expected impact:
1. **Window geometry is mis-cut** (R1). Under the most probable reading of the census (a short last column in c11-c13; QA Q1 (i) 0.65), the *first* end title lies beside it in **c14-c17**. The register splits that slot between L1 (c10-c14) and L2 (c15-c19, labelled "second or calligraphic title"). The windows should be cut by physical column slots, not by tile ranges fixed before the slot structure was known.
2. **L9 (physically lost) is under-weighted** (R2), 0.10 against about 0.25-0.30. The papyrus above the mesh top edge is only about 2 mm, which is less than one title line. Most of L3's mass is therefore lost, not traceable. The honest odds must say so.
3. **A numbers-only test can settle much of Q1 without any reads** (N1): per-tile ink-label fraction of the official labelled segment 20231016151002, which covers c9-c15 r0-r3.
4. **Offset (ink transfer) and stuck layers (sovrapposti/sottoposti) are missing** from the register (N2, N3). The P4-V rule that *voids* a verso candidate matching the facing recto would throw away the one trace that survives when the recto title ink has flaked off.
5. **The functional place of a verso title, the outside of the roll's outer end, is not covered** (N4). P4-V is declared only for the inner title zone.
6. **A kollesis / final-sheet anchor channel is missing** (N5). The join of the final protective sheet is a physical, measurable marker of the end of the book, and of where a title would sit on it.
7. **The positive controls of F1 / P4-W and of the reader-free detector are mis-matched** (T7). Dense body text is not a sparse centred block. A synthetic sparse-block injection control is needed to know the recall for the thing we are looking for.

---

## A. Wrong or mis-structured priors

### R1. Windows A/B are cut in the wrong place
- **Premise.** The column pitch is about 8 cm, i.e. 4 tiles (D 4.2): last full column c7-c9, intercolumn c10, slot 1 c11-c13 (the block), intercolumn at about c13.5-c14, slot 2 c14-c17, slot 3 c18-c19 and beyond.
- **Where the titles fall.** Cavallo: 91 % "beside, always after some space", with measured offsets of 2.5-10 cm (D 1.1).
  - Under Q1 (i), the last column is slot 1. So the first title lies 2.5-10 cm after the end of c13, which is **c14-c18**, centre about c15-c16.
  - Under Q1 (ii), the first title *is* slot 1, and a second calligraphic title would lie 11.5-19 cm on (PHerc. 1497, 1675), which is **c19 or inward of it**.
- **Correction.** Replace L1/L2 by slot-based hypotheses. Masses are from QA Q1/Q2, conditional on the title being on the w010-027 inner end:

  | new id | slot | content | mass |
  |---|---|---|---|
  | S1-hi | c11-c13, r0-r1 | the block itself is (part of) the title (Q1 ii) | 0.20 x P(on this end) |
  | S1-lo | c11-c13, r2-r4 | title below the short last column | 0.65 x 0.3 |
  | S2 | c14-c17, rows r1-r5, or lost above r0 | title beside the short last column | 0.65 x 0.7 |
  | S3 | c18-c19+ | second title, or a title placed far into the blank end (PHerc. 1027: about 10 cm, "almost in the centre of the last sheet") | small, about 0.05 |

- **Validation before re-cutting.** The 1 mm column profile (D 5.3) fixes the intercolumn positions to ±1 mm. The pitch must match on c0-c9 and on w028-037. If the pitch is 6 cm, not 8 cm, every slot boundary moves, and the 2 cm quantisation cannot tell (the FAQ gives 5.3-7 cm; D 4.4).

### R2. L3 and L9 must be re-split
- p4-layout: the sheet continues only about 2 mm above the mesh in c9-c14 (L3). A title line pitch is 4-8 mm, and title blocks are 1.5-4 cm tall (TITLE_PRIOR d).
- Q2 gives P(title partly or wholly above the preserved edge) ≈ 0.31.
- Split it as follows:
  - **L3a**, recoverable in the 2 mm strip: descenders or a dash of the lowest lost line. About 0.03.
  - **L3b / L9-top**, physically lost. About 0.25.
- L9 in total, adding other loss (unrolling was never done here, but crushing and flaking were): **0.25-0.30, against the register's 0.10.**
- This lowers the honest odds of any win; it does not change a bar. It is the statement "the top rows are physically missing" taken at face value.

### R3. The register sums as if its locations were exclusive; they are not
- The L-priors sum to 1.02. More importantly, an **initial title (L6) and an end title (L1-L4) can coexist**: PHerc. 1008 and 1457 have both (D 1.3). A verso title can coexist with both.
- The quantity that matters is P(at least one readable title somewhere we can image). Keep one exclusive partition for the *end* title, and separate, independent Bernoulli entries for the initial title, the verso title and the tag.
- Initial title: attested in about 6 of about 118 titles (D 1.3), i.e. about 5 % of rolls. Two further conditions apply: P(the outer beginning of Paris 4 is preserved to within about 12 cm of column 1) and P(detectable). Its independent value is about 0.05 x 0.3 x 0.7 ≈ 0.01.

### R4. Ink priors must be conditioned on location
- I1 is 0.90 unconditionally. But under Q2, the largest recoverable mass (about 0.54) is "on present, traced papyrus where the organizers' model sees nothing".
- **Given that location**, the title is not detected by the carbon-trained 2.4 um model. The possible reasons are:
  - (a) it is not there after all (it is really in S2 or above);
  - (b) the ink is faint or thin (I5);
  - (c) the ink has flaked off or been abraded (N2);
  - (d) the model's size or sparsity prior fails (F1);
  - (e) the ink is non-carbon (I2-I4).
- My conditional split, given the title is in S1-lo/S2 on present papyrus: F1 model or display failure 0.30, faint or thin 0.25, flaked or offset 0.20, the organizers did not inspect it 0.15, non-carbon 0.10.
- Consequence: **non-carbon inks remain a small share even in the conditional world. Faint, flaked and sparse-block failure dominate.** The channel budget should follow this: L3 at d*, N2 offset, P4-W with the synthetic-block control, in that order, with P4-F and dual energy as cheap screens.

### R5. The L1 prior of 0.45 double-counts the Cavallo 91 %
- The 91 % is P(beside | a title is preserved). It is not P(title in window A | Paris 4).
- The chain is: P(end title was written) ≈ 0.95 (most rolls with a preserved end have a final title; PHerc. 994 is a counter-example with a blank agraphon, D 1.1) × P(preserved) × P(beside) × P(in the window).
- With preservation at about 0.7 (R2), the beside-and-present mass is about 0.95 x 0.7 x 0.9 ≈ 0.6 in total, spread over S1-S3. With the Q1 split, S2 alone gets about 0.3-0.35.

## B. Missing hypotheses (each with its mechanism, CT signature and a proposed test)

### N1. Official ink labels already tell where the known text ends (numbers only; highest value per unit cost)
- **Fact.** The labelled segment 20231016151002 lies 0.00 mm from w010-027 c9-c15, rows r0-r3 (D 4.3, p4-excl; FIRM measured). Its official ink labels were drawn by the organizers' team on the known text.
- **Test.**
  - Map the label mask onto the canvas tiles, by the same point-to-surface mapping as p4-excl. For each tile of c9-c15 r0-r3, report the **ink-label pixel fraction** and its z-profile. These are numbers only: no image is displayed, and no label shape is described.
  - If the labels mark ink in c11-c13 r0-r1, the organizers treated that block as ink they had labelled, i.e. almost surely as body text: Q1 (i) confirmed, and S2/S1-lo become the targets.
  - If the labels stop at c9-c10, the block is unlabelled, and Q1 (ii) rises.
- **Validation.** On the known-text columns c5-c9 the label fraction must be above 0 in the rows the census calls text. This is the positive control.
- **Integrity note.** Label masks are ink/no-ink rasters, not text. Reading the pixel sums is a numeric operation. The orchestrator should confirm it is within the RULES viewing rule before running it. I ask this in ASK.md.

### N2. Title ink transferred (offset) to the facing surface, or flaked off
- **Mechanism.** The writing is on the recto, which is the inner face of a rolled book (LIKELY: standard roll practice, Turner). The recto of winding w therefore presses on the verso of winding w-1, the next inner winding.
- Carbonisation, crushing and compression make ink adhere to the facing layer: the Herculaneum "sottoposti / sovrapposti" problem, well known from unrolled papyri. LIKELY: a standard term in Herculaneum papyrology; the CT consequence is my inference.
- So a title whose recto ink has flaked can survive, mirror-reversed, on the verso of the next inner winding at the same angular position.
- **CT signature.** A deposit layer on the *verso* face of w-1, whose letters are mirror images, co-located (in 3-D) with a blank or damaged recto patch on w.
- **Red-team point on DECL-P4-15(b).** It says: "a verso candidate must also be checked against the recto of the adjacent outer winding at the same place (mirror-offset ink transfer). A match there **voids** it."
  - That rule is right for *body text*: offset of known text is not a title.
  - But **when the recto at that place is blank or damaged**, the offset is the only surviving trace of the recto writing. It should become an "offset lead", reported to the owner as such, not voided.
  - Papyrologists do read offsets. Whether an offset image qualifies for the prize is for the organizers.
  - I ask in ASK.md for a declared split of that rule: void if the facing recto *has* matching legible ink; "offset lead" if the facing recto is blank at d*.
- **Test.** P4-V run on the title zone as declared, plus the facing-recto blank check.
- **Validation.** Offsets of known text in c0-c8 exist or do not. Their measured rate is the positive control, and the sign of the mirror is the check.

### N3. The c11-c13 r0-r1 block is a stuck piece of another layer (sovrapposto)
- **Mechanism.** At a crushed top edge, a flake of an adjacent winding (carrying body text from about c9-c10 of w+1) can be fused onto the surface of w.
- **CT signature.** A local double thickness (about 2 x the sheet thickness), a second fibre layer, and letters with an orientation or line pitch discontinuous with the surface underneath.
- **Test** (numbers only): sheet thickness along the surface normal per 1 x 1 cm cell in c9-c14 r0-r1, against the c5-c8 control, from the CT intensity profile.
- **Validation.** Thickness CV on the controls. A flag is > 1.6 x the control median over ≥ 1 cm².
- My sheet-switch check (QA Q1) rules out a *mesh* jump onto traced neighbours. It does **not** rule out a physical flake.

### N4. Verso title at the outer end (the functional place for a label on a closed roll)
- The verso titles are attested (PHerc. 339, 1491, 1670; D 1.3, LIKELY). Their function is to identify a rolled book, so they stand on the outside of the outermost turn, i.e. on the **verso of the beginning** of the roll.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- Prior: about 0.02 x P(the outer turn is preserved) ≈ 0.01. It is cheap if the M-OUT tiles exist anyway.
- Caveat: the outermost turns of Herculaneum rolls are the most damaged (the "scorze"), so preservation is poor.

### N5. The final kollesis and protective sheet as an anchor (a geometry-only channel)
- **Mechanism.**
  - Rolls are glued from kollemata of about 15-17 cm (Janko, On Poems 2: 99 kollemata of 15.0-17.1 cm; D 1.5, FIRM via review). Each kollesis is a 1-2 cm overlap, i.e. a double-thickness band across the full height.
  - A roll may end in a final protective sheet (Del Mastro 2014 has a section "foglio di protezione finale"; D 1.1, FIRM that the section exists). The title is often on the last sheet, near its centre (PHerc. 1027).
- **CT signature.**
  - Periodic double-thickness vertical bands at the kollema spacing.
  - Possibly a change of fibre direction on the recto of an added protective sheet. That is my UNCERTAIN inference: the protokollon at the start is attested with vertical fibres on the recto in Egyptian rolls; for a final sheet I have no Herculaneum measurement.
- **Test** (numbers only): the per-column (1 mm bins) median sheet thickness and the fibre-orientation structure tensor at d*, along the whole w010-037 canvas.
- **Validation.**
  - Spacing regularity on the known-text strip: CV < 10 %, and a period in 14-20 cm.
  - Joins never fall inside a column. Scribes wrote across joins, so this is a weak check, but a join inside the c11-c19 blank end, together with a fibre change, marks the start of the final sheet.
- **Pay-off.** It locates the physical end of the book and the "last sheet", whose centre is a documented title position (PHerc. 1027), independently of ink.

### N6. The canvas's slot pitch is wrong because the columns are not vertical on the canvas
- Herculaneum columns lean ("Maas's law": the left edges of columns drift leftward downward). LIKELY. Maas's law is attested in Greek bookrolls (Johnson 2004); for Herculaneum rolls it is my UNCERTAIN recollection.
- Canvas crushing can add shear. A title block in c14 could therefore sit in the tiles of c13 at r0 and c14 at r4.
- **Test.** Measure the column-edge x-position per row on c0-c9 from the 1 mm profile. Report the slope (mm per cm of height) and carry it into the slot boundaries of R1.

### N7. The end of the text is not at c9-c13 because c14-c19 is damaged, not blank
- "Rows N" in the census means that the model or the reader sees no ink. It does not mean blank papyrus.
- Surface loss (a peeled recto fibre layer) in the crushed inner turns would give the same census. The title would then be absent physically: L9, not a failure of the channels.
- **Test.** Surface integrity per 1 x 1 cm cell: the presence of the two-layer fibre structure and the recto surface gradient at d*.
- **Validation.** Control on the c0-c8 text cells.
- If the c14-c17 recto is intact, the title's absence there becomes informative. If it is damaged, the negative there is uninformative, and COVERAGE must say so.

### N8. A coronis or end marks as a locator
- A coronis is "di norma posta sotto l'ultima colonna" (normally under the last column; Romano via D 1.2, LIKELY). It is a large non-letter mark at the left of the last lines of the text. Under Q1 (i) it would stand at the left edge of c11, at the lower end of the r0-r1 block.
- The "block" brief (DECL-P4-17) counts non-letter marks. Its reports for c10-c11 r1-r2 should be read as a locator for the end of the text, not only as ornament.

## C. Failure modes of each declared test

| Test | Failure mode | Consequence | Mitigation (measurable) |
|---|---|---|---|
| M1 (official 2.4 um predictions) | The labelled segment 20231016151002 covers c9-c15 r0-r3. If the official model trained on its labels, M1 there is in-sample: it can reproduce label shapes and suppress unlabelled strokes | The c11-c13 block may be memorised labels; a title absent from the labels would be under-predicted | N1 (label fraction per tile); flag in-sample tiles; use model-free channels only for the title zone |
| M1 / M2a size prior | The models were trained on body letters of about 2-3 mm with dense lines. Sparse, larger, decorated title letters are off-distribution | Low recall on the title | Synthetic sparse-block injection is not possible for a model's *input*. Rely on L3, P4-W and the detector |
| M2a (1 um) | z 67-135 mm only. A top-aligned title in S2 (c14-c17 r0-r1) is **outside** it | M2a cannot test the most likely "above-edge-adjacent" part of S2 | COVERAGE should mark S2 r0-r1 as 2.4 um only |
| E2 (±53 um mean) | Dilutes a 15 um deposit about 7x (D 5.1) | Uninformative (already seen: 0 letters) | Retire E2 as a title channel; keep it as a context display |
| L2/L2S (±15 um) | Depth-blind if the ink layer is offset from the mesh (DECL-P4-12-A3) | False negatives | L3 at d* |
| L3 at d* | d* is calibrated on c0-c8 but may drift along the strip. The mesh-to-surface offset changes with crushing and mesh fit, especially at the top edge | The title zone is rendered at the wrong depth | Measure the local surface position per 1 x 1 cm cell from the density gradient (ink-free) in c9-c19. Report the d* drift. Bar: |drift| < 10 um, else use a per-cell d* |
| L3 top-edge trace | Only about 2 mm of papyrus exists above the mesh (R2) | Low yield | Treat as confirmation only; seam-consistency metric on the extension |
| P4-F dense | Screened only within ±15 um until the re-run at d* (DECL-P4-6-A3 already corrects this). Thresholds come from the control strip | The dense-ink null is conditional | As declared. Also add a d*-drift check |
| P4-W block | The positive control ("block Y" on known text ≥ 50 %) is dense body text, not a sparse centred block. Windows are cut at a 2 cm stride over c9-c19 only, and never extend past the top edge | Recall for the actual target is unmeasured. A block half cut off at the edge is scored against full windows | **T7**: a synthetic sparse-block control, made by code from the same material: blank c16-c19 windows plus letters cut from the c0-c8 material, laid out as 2-4 centred short lines at 1.5 x line pitch. It is used only as a validation control, never shown next to the title zone, and never submitted. Report recall at 2, 3 and 4 lines. Also allow edge-anchored windows at r0 |
| Reader-free detector | T_d frozen at the intercolumn p99. Intercolumns can carry marginal marks (stichometric letters, paragraphoi, corrections) | T_d biased high, lower recall | Use the c14-c19 blank end (if N7 shows an intact surface) as a second null; report both |
| P4-M-OUT | The outer turns ("scorze") are the most damaged part of Herculaneum rolls. The 20 % gate may fail and give "uninformative" | Expected | Also N4 (verso) on the same tiles |
| P4-V | The voiding rule (see N2); recto-trained readers on mirrored images | Loses offset leads | Split the rule (ASK.md); the mirrored known-text gate is already declared |
| P4-TAG | Sillyboi were small parchment or papyrus tags, probably lost during the eruption or excavation. A >0.5 mm-outside rule misses a tag lying flat against the roll | Very low yield | Keep it as a geometry note; no further spend |
| DECL-P4-7 core | An end title 20 cm or more past the text is anomalous (D 4.3) | Low prior | As declared |
| Dual energy (I3) | The 137 keV ROI covers only r3 (14-27 % of r3 c10-c17). Neither the S1-hi rows r0-r1 nor S2-top is covered | Purple and high-Z untested where Q2 puts most of the high mass | State it in COVERAGE as "uncovered: no 137 keV data" |
| Census N0 (rot90) | The null is rotated *text*, not blank papyrus. It measures letter naming on rotated strokes | A blank-papyrus null would be lower. A sparse title is compared against a null that is dense in strokes, which disfavours sparse blocks | Add a blank-end null (c16-c19 tiles, if N7 shows an intact surface), per variant |

## D. Things that are right and should stay
- Raw-CT or model-free channels for the title zone: required by the prize rule on training overlap, given the labelled-segment coincidence.
- The low priors on coloured or purple ink (I2-I4). The literature gives no Herculaneum attestation, and the conditional analysis in R4 keeps them small.
- No title words anywhere; the organizers' papyrologists read.
