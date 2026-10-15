# p4-titulus Q&A with the orchestrator (OWNER-STANDING-ORDER-2 item 6)

Provenance: Project HERCULES | owner the owner | [id removed]
Sibling p4-titulus, branch claude/gifted-bell-gavnl5-sib-p4-titulus. Started 2026-09-26 ~21:40Z.

Integrity: no image, tile, render, prediction pixel or CT voxel was opened, viewed or described. Only committed numbers (census letter counts, mesh vertex coordinates) and published text were used. No title word, author name, work title or book number for PHerc. Paris 4 is written here or anywhere by this sibling. The DOSSIER was read only to the end of section 7.3.

Grades: FIRM = primary source or peer-reviewed text read at source (by p4-research or this sibling); LIKELY = reliable secondary, a review, or a verbatim quotation inside a thesis; UNCERTAIN = my own inference or professional judgement, or an unverified recollection of the literature. Every probability below is UNCERTAIN unless stated otherwise: it is a judgement with its arithmetic shown, not a measurement.

Abbreviations: D = p4-research DOSSIER v4 (sections 0-7 only); census = logs/p4/census_a_summary.json as tabulated in D 4.2 (blind-reader letter counts per 2 x 2 cm tile on the official 20260417190342 predictions; unconfirmed, N0 null max 4).

---

## Q1 (2026-09-26, answered 21:55-22:05Z)
> DOSSIER s4.2 describes a text-like block only in the top two 2 cm rows of the column slot after an intercolumn (w010-027 c11-c13 r0-r1, z about 147-165 mm), with blank rows below it and blank slots after it. Which is more probable for a Herculaneum roll end, and with what numbers: (i) a short last column of body text, with the title below or beside it, or (ii) the title block itself, sitting high on the sheet? Which of these fits "the top rows are physically missing"?

**Answer: (i), a short last column of body text, is more probable: about 0.65, against about 0.20 for (ii); about 0.15 that the block is not writing at all (model or reader artefact). UNCERTAIN.** "Top rows physically missing" is compatible with both, and it does not discriminate between them. It is incompatible only with one sub-case of (i), a title *below* the short column. That region, c11-c13 r2-r4, is physically present, and it reads blank.

### First, which end is the top? (needed for Q1 and Q2)
- The census has text-like rows up to r0 (median z 165 mm) in every column c0-c9. The lowest row r7 (z about 42 mm) is almost blank (D 4.2).
- p4-layout reports that the sheet continues only about 2 mm above the mesh top edge in c9-c14 (HYPOTHESES L3).
- So at the high-z end the writing runs to within about 1 cm of the preserved edge in every column. No upper-or-lower margin of normal size (2-5 cm; see TITLE_PRIOR.md d) is preserved there. At the low-z end a blank band of about 1.5-2 cm is preserved (r6-r7).
- The end where the writing is cut by the preserved edge is the end where rows are "physically missing". The organizers say the *top* rows are missing. So **high z = the top of the columns, and the whole roll has lost its upper margin and probably its first line or lines at z above about 170 mm.** LIKELY (inference). It rests on two conditions: the census r0 signal being real, and "rows" meaning lines of writing.
- Loss of the upper edge is the commonest damage pattern of carbonised Herculaneum rolls. The organizers' own paper suggests it for PHerc. 1667: "the now-lost upper portion of the roll" (Angelotti et al. 2026, D 3.4; FIRM that they say so).
- Validation: CErc 54 (Nicolardi et al. 2024) gives the lines per column and whether the first lines of the final columns are lost. See SOURCES in TITLE_PRIOR.md.

### Evidence and likelihood ratios (LR > 1 favours (i))
Prior before the census evidence: 0.5 : 0.5. Both layouts are common at a roll end: the last column is almost never exactly full, and 91 % of titles stand beside the last column (Cavallo 1983 p. 22 via Romano 2005; FIRM verbatim, D 1.1).

| # | Evidence (numbers) | P under (i) | P under (ii) | LR |
|---|---|---|---|---|
| E1 | The block begins exactly one column pitch after the last full column. The census minima c2, c6, c10 give a 4-tile (about 8 cm) period, and c11-c13 is the next slot (D 4.2) | about 1: a body column is placed at the pitch by construction | about 0.5: a title stands "after some space"; measured offsets are 2.5-10 cm (PHerc. 1497, 1027), and only part of that range coincides with the next slot | about 2 |
| E2 | The block fills the full slot width: letters in all three tiles c11, c12, c13 in r1 (7, 8, 2) and r0 (1, 2, 8), about 6 cm, which is a full column width | about 0.9: body lines are justified to the column width | about 0.4: title lines are centred, and the author and number lines are short (organizers 2025, D 3.3). Only a long title line reaches full width | about 2 |
| E3 | The block starts at the top of the column (r0 = the top row of c0-c9 too) | 1: a column always starts at the top line | about 0.35: no published rule for the vertical position of end titles (D 1.1: GAP). Cases: PHerc. 1027 near the centre of the last sheet; the PHerc. 1497 bibliological note "in the upper part"; the organizers suggest the upper portion for PHerc. 1667 | about 3 |
| E4 | The block is short: 2 tile rows, at most about 4 cm of a column of at least about 12 cm | about 0.3: if the text ends at a uniformly random line, P(the last column is filled for at most 30 % of its height) is about 0.3 | about 0.8: title blocks are 2-6 lines, about 1.5-4 cm tall (D 1.2, 6) | about 0.38 |
| E5 | The organizers, who have the same official predictions and read 2.4 um ink directly (Angelotti et al. 2026, FIRM), say the *expected title region* shows **no** detectable ink | high: under (i) the block is the end of the text, which they have read (CErc 54, "final columns"), and the expected title region is next to it and empty | low: under (ii) the title would be visible in their own prediction and at 2.4 um. It would then not be described as "no detectable ink" | about 3 |

Product of LRs: 2 x 2 x 3 x 0.38 x 3 ≈ 14, i.e. (i):(ii) ≈ 0.93 : 0.07 before the artefact reserve. **I shrink this heavily**, because the LRs are my judgements, E1-E4 rest on unconfirmed LLM letter counts (only 4 of the 6 block tiles exceed the N0 maximum of 4), and E5 assumes that the organizers' "expected region" is this one (unverified, D 7.3).
- Shrunk result: (i) 0.65, (ii) 0.20, artefact / not writing 0.15.
- Sensitivity: dropping E5 (if the organizers' region lies elsewhere) gives about (i) 0.55, (ii) 0.30.

### Excluded as an explanation: a mesh sheet-switch onto the adjacent winding (numbers, this sibling)
- The worry: at a crushed top edge a mesh can jump onto the next winding, which carries the text of c8-c10. This would import body text into c11-c13 r0-r1.
- Test (tools/sib/p4-titulus/sheet_switch_check.py; output logs/sib/p4-titulus/sheet_switch_check.txt; input tile_points.npz sha256 02ebb98e...):
  - For each tile, the nearest 3-D distance from its mesh points to the points of all tiles at least 2 columns outward (and, separately, inward) in the same or adjacent rows.
  - The in-tile point spacing is 0.147 mm.
- Result for c11-c13 r0-r1:
  - outward: p5 0.18-0.23 mm, median 0.38-0.44 mm;
  - inward: p5 0.21-0.30 mm;
  - 0.000 of points closer than 0.05 mm.
  - The controls c5-c8 r0-r1 give the same pattern: p5 0.17-0.20 mm.
- So the mesh does not collapse onto any traced neighbouring winding there. The p5 distances are about one winding pitch (0.22 mm, p4-inner).
- Limits:
  - This cannot exclude a switch onto an *untraced* sheet, or a sub-sampling-scale jump under 0.15 mm.
  - The per-vertex normal-flip and neighbour-ratio audit of L10 is still needed; this is a necessary check, not a sufficient one.

### Which fits "the top rows are physically missing"?
Since high z = the top (above), the preserved sheet ends at about z 167-175 mm in these columns. Every column, text and title alike, has lost what stood above that edge.
- Under **(ii)**: the block is the lower surviving part of a title block. The upper lines are lost above the edge; in the usual order these are the author line and the first title line (organizers 2024, D 3.2). The surviving lines would then be the lower ones (title continuation, book number, count). That fits "top rows missing" **directly**: the missing rows are the title's own rows.
- Under **(i)**: the title stood beside the short column, in slot c14-c17. If it was placed level with the top of the short column, it is lost in the missing top. That also fits the statement. If it was centred or low, it is on preserved papyrus in c14-c17 r1-r4, and reads blank, so it would need faint or different ink.
- Under **(i) with the title below the short column** (c11-c13 r2-r4): the papyrus is present. "Top rows missing" does not explain the non-detection there, so this sub-case needs a faint or different ink.
- Net: the statement alone does not separate (i) from (ii). Together with E5 it suggests that the organizers' papyrologists expected the title **high**, at a level that is now missing. This is consistent with their 1667 comment.

### Measurable validation (what would settle Q1)
1. Line structure of the block, numbers only. A z-profile of the official prediction, summed over x in c11-c13 at 0.5 mm bins, compared with c7-c9 at the same rows.
   - Body text gives the same line pitch as c7-c9 (the Paris 4 line pitch, from the census material). A title gives fewer lines, wider line spacing, and possibly larger letter heights.
   - The line count and the pitch ratio are the test. Letter height ratio > 1.3, or line pitch ratio > 1.3, favours (ii).
2. Horizontal profile in the same rows: body text fills the slot edge to edge with a straight left edge aligned to the column; a title is centred with ragged edges on both sides.
   - Test: the left-edge x-position of each line. Its standard deviation is about 1 mm for body text and more than 3 mm for a centred title.
3. CErc 54 (Nicolardi et al. 2024) states whether the final column is short, and how many lines it has. That would settle Q1 without any imaging. It is the highest-value literature item (SOURCES).

---

## Q2 (answered 22:05Z)
> If the high-z end is the top of the column, where would the title's missing lines most likely be: above z 165 mm (off the traced sheet), or lower?

**Answer: conditional on the block being the title (ii), the missing lines are most likely ABOVE, beyond the preserved edge (about 0.85). Unconditionally, the title is more likely at LOWER, preserved z but undetected (about 0.55) than above the edge (about 0.30). The rest (about 0.15) is the artefact case. UNCERTAIN.**

Arithmetic, with Q1's posterior (i) 0.65, (ii) 0.20:
- **(ii), the block is the title** (0.20). Directly below the block, r2 (z about 128 mm) reads blank, and so does the rest of c11-c13 r2-r7. The r1 tile runs to about z 138 mm.
  - So a title continuing downward would have to stop within about 1 cm below the block. The lines that are *missing* are therefore more plausibly the top lines (author, first title line), lost above.
  - P(missing lines above | ii) ≈ 0.85; P(below, in faint ink) ≈ 0.15.
  - Contribution: above 0.17; lower 0.03.
- **(i), the block is the short last column** (0.65). The title is beside it in c14-c17 or below it in c11-c13 r2-r4.
  - P(below | short last column) ≈ 0.3. Cavallo: 7 % below overall, but "below" is used almost only when the last column is short (organizers 2024, D 3.2), so it is raised here.
  - P(beside) ≈ 0.7. For a beside title, P(placed at or near the top line) ≈ 0.3. That is my judgement from PHerc. 1497 (note "in the upper part"), PHerc. 1027 (centre) and the organizers' 1667 remark.
  - Above the edge: 0.65 x 0.7 x 0.3 ≈ 0.14.
  - Lower but present: 0.65 x (0.3 + 0.7 x 0.7) ≈ 0.51.
- Totals: above the edge ≈ 0.31; lower, on present papyrus ≈ 0.54; artefact ≈ 0.15.

Physical consequence (important):
- p4-layout measured only about 2 mm of sheet above the mesh top in c9-c14 (L3). A title line pitch is about 4-8 mm (TITLE_PRIOR.md d).
- So **at most the bottoms of the letters of one lost line** could survive above the mesh. The remaining "above" mass, about 0.25-0.30 of the total, is **physically lost** and falls under L9, not under a tracing fix.
- L3's value is therefore mostly as a *confirmation* channel: descenders or a decoration dash at the very edge. It is not a recovery channel.
- The "lower" mass (about 0.54) is on papyrus that exists and is traced. It is recoverable **only if** the ink is detectable by a channel other than the official 2D model, which is where the organizers saw nothing:
  - L3 at d*;
  - the P4-W block brief;
  - the reader-free detector.
- This is where the project's effort should go. My ranking of the "lower" regions:
  1. c14-c16 r1-r3: beside, centred;
  2. c11-c13 r2-r3: below the short column;
  3. c15-c19 all rows: a second or calligraphic title (L2).

Validation: none on the imaging side for "above" beyond the 2 mm strip, and that strip needs the L3 top-edge trace with seam-consistency metrics. For "lower", the declared L3 and P4-W channels apply, with the known-text gate on c0-c8.

---

## Q3 (answered 22:10Z)
> Is there any Herculaneum case where the end title lies in the upper margin, or in the space above the last column?

**Answer: none that I can cite. In Cavallo's census of 70 Herculaneum rolls with preserved titles, 64 are beside the last column, 5 below it, 1 repeated, and 0 above it or in its upper margin (Cavallo 1983 p. 22, FIRM verbatim via Romano 2005 n. 147, D 1.1).**
- By the rule of three, the 95 % upper bound on the rate of "above" placement is about 3/70 ≈ 4 %. The Laplace point estimate is 1/72 ≈ 1.4 %.
- Del Mastro 2014 (118 certain titles) supersedes Cavallo. Its full text was not reachable (D 1). Its BMCR review reports no such placement (LIKELY).
- Grade: LIKELY that no Herculaneum end title is known in the upper margin above the last column.

Three caveats that matter for Paris 4:
1. **Preservation bias.** Upper margins of Herculaneum rolls are the parts most often lost to carbonisation and unrolling damage (the "top rows are physically missing" pattern itself). A title placed in an upper margin would be under-represented among *preserved* titles. So 0/70 is biased low. My adjusted estimate is about 2-5 % (UNCERTAIN).
2. **Distinguish "above the column" from "beside, high".**
   - Placement in the upper part of the sheet beside the last column, level with its first lines, is attested in the sense of "nella parte alta del supporto scrittorio": the bibliological note of PHerc. 1497, 5 cm after its second title (Romano 2005, FIRM as quoted, D 1.1).
   - That is a beside placement, not an upper-margin one. It is the relevant high-placement precedent for Q1 (ii).
3. **Initial titles.** In Greek book rolls from Egypt, initial titles and running titles are sometimes written in the upper margin above the first column (UNCERTAIN recollection; the reference would be M. Caroli, *Il titolo iniziale nel rotolo librario greco-egizio*, 2007). For Herculaneum, the attested initial titles (PHerc. 1457: about 12 cm *before* column 1, Capasso *Titoli* II, LIKELY) stand in the agraphon, not above the column. Neither is evidence for an end title above the last column.

Consequence for the register: I recommend **no new location hypothesis for an end title in the upper margin**. Its mass (about 0.02-0.04) is already inside L3/L9, because the upper margin of these columns is not preserved (Q1 "which end is the top").

---

## Addendum to Q1-Q3 (2026-09-27 01:10Z, from sources read at source; details in TITLE_PRIOR v1)
- **Q1 E4 re-graded.** Short last columns are attested: PHerc. 1426/1506 has a last column of 9 lines against 33-34 (0.27); PHerc. 1428 has 23 against 33 (Romano 2005, citing Bassi and Puglia; LIKELY).
  - The E4 likelihood ratio of 0.38 stands.
  - Q1 is unchanged: (i) 0.65, (ii) 0.20.
- **Q3 caveat added.** Bibliological *numerals* do stand in the upper margin: PHerc. 1497 has them at the centre of the upper margin of cols VI, XVI, XXVI, XXXVI (Romano PDF p. 458; FIRM as quoted).
  - So writing in the upper margin is a real scribal practice, but for counts, not titles.
  - Still no end title in an upper margin; the answer stands.
- **Q2 support.** In PHerc. 1667 the lower portions of the final columns survive without a title, and the organizers' papyrologists place the title in the lost upper portion (Angelotti et al. 2026, FIRM). This is the closest analogue to Paris 4's top-lost state.
  - The vertical prior moves slightly upward: upper third 0.40, centre 0.40, lower third 0.20.
  - TOP-LOST rises by at most about 0.02, within rounding. The partition is kept.

---

## Q4 (asked 02:13Z, answered 02:35Z): re-derivation from CERC54-LAYOUT-RESULT (logs/p4/cerc54_layout.json)

Inputs, all from cerc54_layout.json (graded as the orchestrator's extraction; LIKELY):
- col. -1 is short, 7 lines. This is inferred from the edition: no lacuna sign after its last line, and a final stop.
- Every column, col. -1 included, begins with a lacuna sign. So line(s) and the upper margin are lost at the top.
- Column width about 6.2 cm, intercolumn about 1.7 cm, pitch 7.9 cm.
- 18-19 lines in at most 11.37 cm of revealed height, and the lower 5.38 cm could hold 8-9 more. So the **line pitch is about 6.0-6.3 mm**, and 7 lines take about 4.2-4.4 cm.

Derived (UNCERTAIN):
- The pitch of 7.9 cm equals the census 4-tile period (8 cm).
- The c11-c13 r0-r1 block (0-4 cm below the preserved top edge) has the height of 7 lines plus the lost top.
- So **the block is col. -1**, and c7-c9 is col. -2.

### (a) Q1 posterior and the location partition
- **Q1 re-derived:** (i) short last column **0.95**; (ii) the block is the title **0.05** (it would require col. -1 to lie elsewhere); artefact **< 0.01**.
- Partition inputs:
  - P(an end title was written) 0.95.
  - Given a short last column: below 0.18, beside 0.82. Cavallo's 7 % below overall, divided by about 0.4 of rolls having a short last column.
  - Beside, near (c14-c17) 0.80; far (≥ c18; PHerc. 1027 at about 10 cm) 0.20.
  - Vertical: V1 level with col. -1's first line 0.45; V2 centred on the column 0.35; V3 low 0.20.
  - A V1 title is wholly lost above the edge with P 0.30.
  - The surface is intact with P 0.85.
- Arithmetic: tools/sib/p4-titulus/q4_partition.json.

| cell | P |
|---|---|
| beside, c14-c17, top: wholly lost above the edge | 0.08 |
| beside, c14-c17, top: partly preserved, rows r0-r1 | 0.15 |
| beside, c14-c17, centred, rows r2-r3 | 0.17 |
| beside, c14-c17, low, rows r4-r5 | 0.10 |
| further, c18 and beyond, preserved | 0.10 |
| further, top wholly lost | 0.02 |
| below col. -1, c11-c13 rows r2-r4 | 0.13 |
| on present papyrus but surface damaged or flaked | 0.12 |
| the block itself is the title | 0.05 |
| never written | 0.05 |
| core, or on an untraced surface (L5/L10) | 0.04 |

Check of the orchestrator's provisional re-rank:

| | orchestrator | mine | verdict |
|---|---|---|---|
| beside c14-c17 | 0.60 | 0.50, or 0.55 with its damage share | about right |
| of which top | 0.20 | 0.23 (0.08 wholly lost + 0.15 partly preserved in r0-r1) | split it: the r0-r1 part is **recoverable** |
| of which preserved rows | 0.40 | 0.27 | too high |
| below | 0.08 | **0.13** | too low. A 7-line column leaves about 8-10 cm of blank column below it, and the organizers (2024) name "below" for exactly this case |
| further | 0.10 | 0.12 | about right |
| lost | 0.15 | **0.26** (0.10 above the edge + 0.12 damage + 0.05 never written) | too low |
| other | 0.07 | 0.09 | about right |

### (b) Most likely position of the title block
The measurements rest on two anchors:
- the right edge of col. -1, E, at about **28.4 cm from the canvas origin**: col. -2 ends at about 20.5 cm, then 1.7 cm of intercolumn, then 6.2 cm of column. The uncertainty is ±1 cm from the 2 cm census quantisation; the 1 mm column profile fixes it;
- the preserved top edge, T (the canvas top, r0).

| | horizontal: block centre from E | vertical: block centre below T | block extent |
|---|---|---|---|
| mode | **+4.8 cm** (a centred block in the next column slot: 1.7 intercolumn + 6.2/2) | **1.5-2.5 cm** (level with col. -1's text, which runs 0-4.5 cm below T) | 3-6 cm wide × 1.5-4 cm tall (TITLE_PRIOR d; line pitch in a title about 6-9 mm, i.e. 1-1.5 x the text) |
| 50 % interval | +3.5 to +6.5 cm | 0.5 to 5 cm | |
| 80 % interval | +2.5 to +10 cm (PHerc. 1497: 2.5 cm; 1027: about 10 cm) | lost above T (−2 cm) to 9 cm | |
| canvas position | centre x about 33 cm, i.e. c16; 80 % in c15-c19 | rows r0-r1 (mode), r2-r3 (V2) | |
| "below" alternative | centred under col. -1: x about 25.3 cm (c12-c13) | the last line of col. -1 at about 4.5-5 cm, plus 1.5-3 cm of space, so a centre at **6.5-9 cm** below T (r3-r4) | |

### (c) The first 4 x 4 cm windows to read (top-left tile r, c; each covers 2 x 2 tiles)
Ranked by probability mass per window:
1. **(r0, c15)**: x 30-34 cm, 0-4 cm below T. The V1 mode, partly preserved.
2. **(r0, c16)**: x 32-36 cm. The same band, with the block centre at the mode of +4.8 cm.
3. **(r2, c15)**: 4-8 cm below T. The V2 centred mode.
4. **(r3, c12)**: x 24-28 cm, 6-10 cm below T. Below col. -1.
5. **(r1, c15)**: 2-6 cm below T. It bridges V1 and V2.
6. **(r2, c16)**.
7. **(r0, c18)**: far, the PHerc. 1027 distance.
8. **(r4, c15)**: V3 low.

Controls for the same session:
- **(r0, c11)**, col. -1 itself, as the known-text positive control, but note it lies on labelled-adjacent tiles;
- a blank-end null at **(r4, c18)**.

Validation that would move these:
1. The 1 mm column profile: E to ±1 mm, and the col. -1 line pitch from the z-profile, which should give 7 lines at about 6.2 mm.
2. REDTEAM N7 surface integrity of c14-c17. A damaged surface there moves mass to "lost".
3. The ASK-1 label fractions for c11-c13 r0-r2. Labels on col. -1 confirm the anchor.

Note: CErc 54 itself reports possible "virtual sottoposti" in the intercolumn of cols. -12/-11. This is a direct attestation, in Paris 4, of the failure mode in REDTEAM N2/N3: the title search must check layer mixing.

---

## Q5 (owner via the orchestrator, asked 06:08Z, answered ~06:40Z): initial titles, the top edge, a re-weight after P4-W1 and DECL-P4-24

Sources were read at source this session: Romano 2005 (PhD thesis, Naples; Oxford/Naples citations of Capasso, Delattre and Del Mastro), Capasso, "I titoli nei papiri ercolanesi IV", and the Giandomenico review of Del Mastro 2014. Grades as before. No title words appear here: positions, measurements and counts only.

### (a) PHerc. 1497 (the De musica IV roll): where its titles sit
**The owner is right that this roll has an initial title. It *also* has two final titles.** The roll carries three titles in all; the initial title is an addition, not a replacement.
- **Two final titles, on PHerc. 1497 itself** (Romano PDF pp. 408 n. 940, 459, 547; FIRM as quoted):
  - the first stands to the right of the last column, "ca 2,5 cm più avanti", in the text hand, with the column count (152) below it;
  - the second stands "dopo 11,5" cm, in a calligraphic "Auszeichnungsschrift dal modulo ampio";
  - a bibliological note stands about 5 cm further, "nella parte alta/superiore esterna dell'ultimo foglio".
- **Initial title, on PHerc. 1583, a *scorza* (outer layer) of the same roll.**
  - Delattre's reconstruction orders the pieces 1583, 411, 1572, 225, 424, 1578, 1575, 1094, 1497. He first placed 1583 as col. X, then found parts of an initial title on it and "ha spostato tale fr. prima della I col." (Romano PDF pp. 180-181; FIRM as quoted).
  - The identification from multispectral images is Del Mastro's ("Subscriptio", pp. 248 ff., n. 28; Romano PDF p. 140; LIKELY).
  - It is by the same calligraphic scribe B as the second final title of 1497 (Del Mastro via Romano PDF p. 462; Giandomenico n. 5: scribe B "PHerc 1583/1497"; FIRM or LIKELY).
  - **Its exact position (cm before col. 1, height on the sheet) is not given in any source I have.** GAP; Del Mastro 2014 has it.
- Reconciliation with my dossier: the 2.5 and 11.5 cm figures are the *final* titles, and they stand. The owner's point adds an *initial* title on the outermost layer. Lesson for Paris 4: **the same roll can carry an initial title outside and final titles inside**, so L6 is not an alternative to the end title; it is an independent second chance.

### (b) Herculaneum rolls with an attested initial title

| roll | placement | measured | source | grade |
|---|---|---|---|---|
| PHerc. 1457 | recto, in the initial agraphon before col. 1; also has a final title | about 12 cm before col. 1 | Capasso, Titoli II pp. 110 f.; IV | LIKELY / FIRM (IV) |
| PHerc. 222 | recto, initial agraphon | about 12-13 cm (= 2 columns of 5-6 cm) | Capasso, Titoli IV | FIRM as quoted |
| PHerc. 253 (scorza) | recto, initial agraphon (fibres horizontal) | line 1 is about 5 cm below the upper edge of the scorza | Capasso, Titoli IV | FIRM as quoted |
| Phanias papyrus (lost; its second half is PHerc. 1008, which has the final title) | recto, initial agraphon | about 25 cm ("un palmo") | Capasso, Primo titolo iniziale, via Titoli IV | LIKELY |
| PHerc. 1786 (scorza) | recto, initial agraphon; long taken for a final title | "un certo spazio", not quantified | Capasso, Titoli IV | FIRM as quoted |
| PHerc. 1583 (scorza, De musica) | recto, before col. I | not given | Delattre and Del Mastro via Romano | LIKELY |
| verso titles: PHerc. 339, 1491, 1670, and one unnumbered scorza | on the verso, opposite one of the first columns | not given; Luppe puts the closed-roll circumference at 20-24 cm from verso-title positions in rolls from Egypt | Del Mastro 2014 §2.1 via Giandomenico n. 4; Capasso IV | LIKELY |
| upper margin above col. 1 | **0 in Herculaneum**; 4 doubtful cases in Greek rolls from Egypt | - | Capasso IV ("esempi dubbi") | FIRM as quoted |
| intermediate title | 1 (PHerc. 558) | - | Del Mastro §2.3 via Giandomenico | LIKELY |
| sillybos (tag) | **none ever found at Herculaneum** | - | Capasso, BMCR 2021.06.18 | FIRM (review) |

- **Frequency.** 6 recto initial and 4 verso titles among 118 titles (Del Mastro), about 8 %. Cavallo's census of the end: 64/70 beside, 5/70 below.
- **Capasso's reason for the rarity is preservation, not practice.** The outer beginning of a roll "più di ogni altra rischiava di andare distrutta" (Titoli IV; FIRM).
  - Where beginnings survive, initial titles are not rare: 3 of the 6 recto cases also carry a final title (1457, Phanias/1008, 1583/1497).
  - My estimate is P(an initial title was written) ≈ 0.25 (range 0.1-0.5). UNCERTAIN.

### (c) Paris 4: where an initial title would be, and whether the beginning survives
- **Position.** The rolls were stored rewound, beginning outside (Capasso, Titoli IV, FIRM), and the Paris 4 text runs outside to inside (D 4.1). So an initial title would be on the **recto (inner face) of the outermost turn(s)**, in the agraphon **12-25 cm outward of col. 1**.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - A verso title would be on the **outer face** of the turn that carries col. 1 or 2.
- **Is the beginning preserved?** Unknown. The evidence:
  - (i) CErc 54 gives about 160 columns in all; at a pitch of 7.9 cm that is about 12.6 m of text.
  - Crude sheet length: 130 windings × mean circumference about 10.5 cm ≈ 13.7 m, ±15 % from the crushed and oval section.
  - The difference of about 1.1 m, minus the traced blank end of about 0.2-0.4 m, leaves room for an outer agraphon, but ±2 m of error decides nothing.
[line withheld: prize-candidate detail under review]
- **Data that cover it:**
[line withheld: prize-candidate detail under review]
  - the 45 um overview volumes (geometry only);
  - no 1.129 um volume and no 137 keV coverage.

### (d) A title on the top edge above the official mesh, c14-c19 (DECL-P4-24 (e))
- The mechanism: a beside title at level V1, with its first line level with col. -1's first line, which is itself lost (col. -1 begins with a lacuna sign). The title's upper part stands at or above the preserved edge.
- If L mm of papyrus continues above the mesh top in c14-c17, then **P(title ink in that strip) ≈ P(near, V1) × min(1, L / 12.5 mm)**. Here 12.5 mm is my mean height of the lost part of a V1 block, taken as uniform over 0-25 mm; P(near, V1) = 0.24 after W1.
  - L = 2 mm: **0.04**.
  - L = 5 mm (about one line): **0.10**.
  - L = 10 mm: **0.19**.
  - L ≥ 25 mm: **0.24**.
  - UNCERTAIN.
- **Upper margin above the last column:** 0 attested (Q3). It adds at most 0.02-0.05 × P(preserved), and does not change the formula.
- **Enlarged or "fancy" titles.** Calligraphic letters of about 4-7 mm (a GAP in mm, UNCERTAIN) and a block of 2-4 cm, framed by dashes above and below (PHerc. 172), span 1-2 tile rows.
  - For a V1 title the top dash and first line are the highest elements, so they are the first lost and the first recovered by any extension.
  - A 4-7 mm letter needs L ≥ about 5 mm to show a readable line. So the 5 mm figure above is the practical threshold.

### (e) Register re-weighted after P4-W1-RESULT, DECL-P4-23 and DECL-P4-24
- Method: I applied P(W1 null on the M1 material | the title is in that cell) to the Q4 partition.
  - Windows seen blank by W1: ×0.45-0.6. They stay well above 0 because a non-carbon or faint ink is invisible to M1, and the organizers' null was already priced in.
  - Cells only partly covered: ×0.55-0.75. The r0 tiles are only 83-90 % mesh-valid (DECL-P4-24).
  - Uncovered cells: ×1.
  - The block-is-title cell: ×0.4 (CErc 54 says col. -1 is text).
  - L10: its r0-r4 share falls to about 0.01, per P4-CORE-AUDIT.
- DECL-P4-23 (our own model) is a *future* test, so it changes no weight yet.
- Arithmetic: tools/sib/p4-titulus/q5_partition.json.

| cell | Q4 | now |
|---|---|---|
| beside c14-c17, top, wholly above the edge | 0.08 | **0.11** |
| beside c14-c17, top, partly in r0 | 0.15 | 0.12 |
| beside c14-c17, centred, r2-r3 | 0.17 | 0.11 |
| beside c14-c17, low, r4-r5 | 0.10 | 0.09 |
| further, c18 and beyond, preserved | 0.10 | 0.12 |
| further, top lost | 0.02 | 0.03 |
| below col. -1 | 0.13 | 0.10 |
| surface damaged or flaked | 0.12 | **0.17** |
| the block is the title | 0.05 | 0.03 |
| never written | 0.05 | 0.07 |
| core / untraced | 0.04 | 0.05 |

- **Independent: L6, an initial title, readable in the imaged data ≈ 0.25 (written) × 0.3 (beginning preserved) × 0.6 (detectable) ≈ 0.045.** Before: 0.01. It rises 4x on the owner's point and Capasso's preservation argument. Verso-outer: about 0.01.
- **P(at least one title recoverable)** ≈ 1 − (1 − 0.52 × 0.5) × (1 − 0.045) × (1 − 0.01) ≈ **0.30**.
  - 0.52 is the end-title mass on present papyrus, and 0.5 is P(detectable by some declared channel).
  - UNCERTAIN, and optimistic.

### (f) Red team: the 3 highest-value things still untested, each with a numbers-only test
1. **The first-text-column locator at the outer end (for L6).**
[line withheld: prize-candidate detail under review]
   - Decision: ≥ 12 cm blank and traced means the agraphon survives, so read that region with the P4-W "block" brief on L3 raw CT. < 2 cm means the beginning is lost, so L6 falls to about 0.005.
[line withheld: prize-candidate detail under review]
   - Add the verso of the same turn (mirrored), which is REDTEAM N4.
2. **The top-edge continuation, measured and then read, in c14-c19 (DECL-P4-24 (e), declared but not yet run).**
   - The number that matters is **L in mm per column c14-c17**. Convert it with the formula in (d).
   - If L ≥ 5 mm on ≥ 25 % of rays, extend the trace and compute the d* deposit fraction in 5 × 5 mm cells of the new strip, against a col. -1 control (the same strip above c11-c13) and a blank-end null (c18-c19).
3. **The facing-surface offset channel for the title windows (REDTEAM N2).**
   - The title ink may have transferred from the recto onto the verso of the next inner winding, at the same angle, which is where "damaged or flaked" (now 0.17, the largest single cell) would leave its only trace.
   - Test: the deposit fraction at −d* on the facing surface of the W1 windows, in 5 × 5 mm cells.
   - Positive control: the offset rate of col. -2/-3 text onto their facing surfaces, which must be > 0 for the channel to count.
   - Null: the facing surfaces of the blank end c18-c19.
   - Runner-up: the kollesis and final-sheet anchor profile (REDTEAM N5), because the final sheet's centre is a documented title position (PHerc. 1027).

Integrity: no issues. No image was viewed, no title word was written, and the DOSSIER EXPECTED-TEXT section was never opened.

---

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

Definitions:
- s increases inward, i.e. forward in the text.
- Let the candidate block be B = [s1, s2] with width W = s2 − s1.
- G_out is the blank gap outward of B, to the nearest block at lower s.
- G_in is the blank gap inward, to the next block N at s3.
- P = s3 − s1, start to start.
- All measured on the p4-layout profile (1 mm bins, z-summed M1, rows r1-r6, block = a run above median + 3 MAD of the declared baseline bins).
- The tolerance for scan and carbonisation shrinkage is ±12 %. CERC54 measured the same crumpled roll, so the reference values are already "as scanned".

### 1. Predictions

| quantity | (a) text column | (b) initial-title block | sources |
|---|---|---|---|
| block width W | **5.5-7.0 cm** (6.2 ± 12 %). A column fills its width edge to edge; a short or damaged column can only be *narrower* if the loss is lateral | **2-5.5 cm**: the width of the longest centred line. Titles are 2-4 centred lines, 3-6 cm wide; the author line is short | CERC54 (6.2 cm); organizers 2025 ("each center justified"); D 1.2, TITLE_PRIOR (d) |
| G_in (to the next block) | **1.3-2.2 cm** if the next column is visible. **8.8-10.8 cm** if exactly one column is invisible to M1 (6.2 + 2 × 1.7, ± 12 %) | **9-14 cm** typical, up to 26 cm. PHerc. 222: 12-13 cm from the right edge of the title to the left edge of col. 1 (Capasso, Titoli IV, FIRM); PHerc. 1457: about 12 cm (Titoli II, LIKELY); Phanias: about 25 cm | as cited |
| G_out (outward) | 1.3-2.2 cm (the previous column), or 8.8-10.8 cm (one invisible column), or open-ended blank if B is col. 1 | open-ended blank (the initial agraphon or protokollon). There is **no** ink block within 8 cm outward | Capasso IV (the title stands in the initial agraphon) |
| pitch P = s3 − s1 | **7.0-8.8 cm or 14.0-17.7 cm** (1 or 2 × 7.9 ± 12 %) | W + G_in: **11-19.5 cm** typical, up to 31 cm. It is not tied to multiples of 7.9 | derived |
[line withheld: prize-candidate detail under review]
| line pitch within B | **6.0-6.3 mm** (CERC54: 18-19 lines in at most 11.37 cm, and 8-9 lines in 5.38 cm) | 1.0-1.5 × the text pitch, i.e. **6-9.5 mm**, with larger letters possible (a calligraphic hand) | CERC54; D 1.2 |
| line count within B | fills the preserved height at the text pitch | **2-6** | organizers 2024; D 1.2 |
| line edges | left edges aligned (std ≤ 2 mm); line widths similar | centred: line mid-points aligned (std ≤ 3 mm); line widths differ (max/min ≥ 1.3); left-edge std > 3 mm | layout convention |

### 2. Decision table for the p4-layout profile
Score each row: +1 favours (b), −1 favours (a), 0 undecided.

| measure | favours (a) (−1) | undecided (0) | favours (b) (+1) |
|---|---|---|---|
| W | ≥ 5.6 cm | 4.9-5.5 cm | ≤ 4.8 cm |
| G_in | 1.0-2.5 cm | 8.8-10.8 cm, or 2.6-8.7 cm (fits neither: flag it) | 10.9-14.5 cm; also 14.6-26 cm, but score that +0.5 |
| P | 7.0-8.8 cm, or 14.0-17.7 cm **and** W ≥ 4.9 cm | 14.0-17.7 cm with W ≤ 4.8 cm | 8.9-13.9 cm, or 17.8-31 cm |
[line withheld: prize-candidate detail under review]
| row consistency (the per-row r1-r6 s-extents of B) | extents equal within 3 mm on ≥ 2 rows | only 1 row carries signal | the widths differ by ≥ 30 % between rows, with the mid-points aligned within 3 mm |

Verdict:
- Sum ≥ +3 means **layout favours (b)**; ≤ −3 means **favours (a)**; otherwise undecided.
- A row is skipped (0) if the valid fraction is < 0.5 over the bins concerned.
- The verdict is descriptive only (DECL-P4-25-A2 item 2).
- Note, fixed now: the geometry already reported gives s1 ≈ 105 and s3 ≈ 119, i.e. P ≈ 14 cm. That sits at the (a) two-pitch lower bound (14.0) and inside the (b) range. **P alone therefore cannot decide**; W and G_in carry the weight.

### 3. Other numbers-only discriminators (to run in addition, if declared)
[line withheld: prize-candidate detail under review]
2. **The vertical-extent ratio** of B's rows to N's rows on the same strip (rows with signal above baseline): ≤ 0.6 favours (b); ≥ 0.9 favours (a). This is confounded by damage, so compare within the same strip only.
[line withheld: prize-candidate detail under review]
   - (b) needs this region to be *blank papyrus* (agraphon or protokollon);
   - if it is intact **and** carries deposits at a text-like fraction, then col. 1 lies further out, and B is a column: favours (a).
[line withheld: prize-candidate detail under review]
4. **A kollesis or protokollon join outward of B** (REDTEAM N5): a double-thickness band 1-2 cm wide in s < 105. A protokollon with vertical recto fibres directly outward of B favours (b). It is weak and optional.

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- **The candidate before the extended test and the layout.**
[line withheld: prize-candidate detail under review]
  - P(pattern | b) ≈ 0.6.
  - The block's apparent width of at most about 4-5 cm (c3 and c6 are empty) gives an LR of about 2 for (b).
  - Prior P(b) ≈ 0.075, from an initial title existing (0.25) × being preserved here (0.3).
  - **P(b) ≈ 0.25 (range 0.1-0.4).**
- Conditional on the outcomes:

| extended test | layout verdict | P(B is an initial-title block) | L6 (a readable initial title in hand or recoverable) |
|---|---|---|---|
| EXT-CONFIRMED | favours (b) | about 0.65 | about 0.6 |
| EXT-CONFIRMED | undecided | about 0.30 | about 0.3 |
| EXT-CONFIRMED | favours (a) | about 0.07 | about 0.08 (the baseline, plus a small chance of a title further out) |
| not confirmed | favours (b) | about 0.45 (the block is real ink, but M1 is not legible enough) | about 0.15; go to raw-CT L3 and P4-W on B |
| not confirmed | undecided or (a) | about 0.15 or 0.05 | about 0.07 (the baseline) |

Red-team caveat, fixed in advance:
[line withheld: prize-candidate detail under review]
- A blank of about 1 m is longer than any attested initial agraphon (12-25 cm). So (b) implies that most of that metre is **damaged or unreadable** outer layers, not blank. If it is damaged, text columns could lie there invisibly, and then "col. 1 at s = 119" is unproven.
- Discriminator 3 (surface integrity of s 60-101) is therefore the most important supporting number.

Integrity: no issues. This was written before any layout-profile number existed. No image or letter content was seen. No title word was written.
