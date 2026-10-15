# Title prior for PHerc. Paris 4 (p4-titulus), v1, 2026-09-27 ~01:10Z

Provenance: Project HERCULES | owner the owner | [id removed]
Machine-readable: title_prior.json (same numbers). Status: v0 is pushed early. v1 will add verified measurements from three literature workers (title geometry, roll metrics, inks). Every item marked [v1] is waiting on them.
Integrity: location, layout, size, ink and damage only. No title word, author name, work title or book number for Paris 4 appears here, and none ever will. No image was viewed.
Grades:
- FIRM: primary or peer-reviewed source, read at source.
- LIKELY: review or secondary, or a verbatim quotation inside a thesis.
- UNCERTAIN: my inference or judgement, or an unverified recollection.
Probabilities are UNCERTAIN judgements with the arithmetic shown. Sources marked D are p4-research DOSSIER v4 (sections 0-7).

## (a) Probability over title location

**v2 (02:35Z): SUPERSEDED by QA.md Q4, after CErc 54 (col. -1 is short, 7 lines; the upper margin is lost; pitch 7.9 cm).** The block is col. -1. The new partition and anchor distances are in QA Q4 and title_prior.json `end_title_partition_v2_after_CERC54`. The table below is v1, kept for the record.

### Frame
- High z is the top of the columns, and the roll's upper margin is lost (QA Q1, LIKELY).
- The last full column is c7-c9; c10 is an intercolumn; slot 1 is c11-c13 (the r0-r1 block); slot 2 is c14-c17; beyond that is the blank end (D 4.2, UNCERTAIN census).
- P(an end title was written) ≈ 0.95. Most preserved roll ends carry one, but PHerc. 994 shows a blank agraphon (D 1.1, FIRM via BMCR).

### End title: an exclusive partition that sums to 1
Derived from QA Q1/Q2, re-normalised with the 0.05 "never written" and the damage terms:

| id | where | P | derivation | grade |
|---|---|---|---|---|
| S2 | slot 2, c14-c17, on preserved rows (r1-r5), beside the short last column | 0.24 | Q1 (i) 0.65 × beside 0.7 × not-top 0.7, plus an artefact-world share, × 0.95 × P(surface intact) about 0.85 | UNCERTAIN |
| TOP-LOST | above the preserved top edge, in any slot. It includes the upper lines of S1-hi and a top-aligned S2 title. **Physically lost** (L3b/L9) | 0.20 | Q2 above 0.31, minus the recoverable strip, × 0.95 × 0.7 | UNCERTAIN |
| S1-hi | the c11-c13 r0-r1 block is itself (the surviving lower part of) the title | 0.13 | Q1 (ii) 0.20 × 0.95 × 0.7 (the lost upper lines count under TOP-LOST) | UNCERTAIN |
| S1-lo | below the short last column, c11-c13 r2-r4 | 0.13 | Q1 (i) 0.65 × below 0.3 × 0.95 × 0.7 | UNCERTAIN |
| L3a | in the about 2 mm of sheet above the mesh top edge (descenders or a dash only) | 0.03 | about 10 % of the above-edge mass | UNCERTAIN |
| S3 | c18-c19 and beyond (a title far into the blank end; PHerc. 1027 about 10 cm, "quasi al centro dell'ultimo foglio") | 0.04 | D 1.1 (LIKELY) | UNCERTAIN |
| L5 | the core, w000-w009 | 0.03 | D 4.3 (20 cm or more past the text is anomalous) | UNCERTAIN |
| L10 | on a surface the official mesh does not trace (a sheet switch) | 0.03 | partial numeric exclusion at c11-c13 r0-r1 (QA Q1) | UNCERTAIN |
| L9-other | present once, now lost: surface flaked or peeled (REDTEAM N7), crushed; or never written (0.05) | 0.17 | 0.05 never written + 0.12 damage | UNCERTAIN |

Register mapping (logs/p4/HYPOTHESES.md):
- L1 ≈ S1-hi + S1-lo + the c14 part of S2.
- L2 ≈ the c15-c17 part of S2, plus S3.
- L3 = L3a + part of TOP-LOST.
- L4 = S1-lo.
- L9 = TOP-LOST + L9-other ≈ 0.37.

**Recoverable mass on the inner end** = S2 + S1-hi + S1-lo + L3a + S3 + L5 + L10 ≈ 0.63. That is the mass on papyrus that exists; it is not the probability of detection. The organizers' "no detectable ink" applies to at least part of it.

### Independent (not exclusive) title entries

| id | what | P(exists, preserved and in imaged papyrus) | derivation | grade |
|---|---|---|---|---|
| L6 | initial title before column 1 at the outer beginning | about 0.01 | about 6 of about 118 titles are initial (D 1.3), i.e. 0.05; P(the outer beginning is preserved within about 12 cm of column 1) about 0.3; P(detectable) 0.7 | UNCERTAIN |
| L7-outer | a verso title on the outside of the outer end (REDTEAM N4) | about 0.005-0.01 | 3 attested verso titles among about 150 (D 1.3) × P(the outer turn is preserved) | UNCERTAIN |
| L7-inner | a verso title in the inner title zone | about 0.005 | no functional reason at the inner end | UNCERTAIN |
| L8 | an attached tag (sillybos) | about 0.002 | tags were separate, small and fragile; none is reported attached to a carbonised roll | UNCERTAIN |

## (b) Vertical position of end titles within the column height (critical)

| case | vertical position | source | grade |
|---|---|---|---|
| PHerc. 1497, bibliological note (after the 2nd title) | "nella parte alta del supporto scrittorio" (in the upper part) | Romano 2005 p. 459 via D 1.1 | FIRM as quoted |
| PHerc. 1027, end title | "quasi al centro dell'ultimo foglio" (horizontal centre of the last sheet; no vertical statement) | Capasso via Romano, D 1.1 | LIKELY |
| PHerc. 1667 (core), end title | "may have been located in the now-lost upper portion of the roll" (the organizers' papyrologists' expectation) | Angelotti et al. 2026, D 3.4 | FIRM that they say it; an expectation, not a measurement |
| Paris 4, the organizers' region | "the top rows are physically missing" (their expected region) | prize page, D 3.1 | FIRM that they say it |
| PHerc. 1667, end of a roll (core) | the **lower** portions of the final columns are preserved, and no title is in them. The organizers' papyrologists place the title in "the now-lost upper portion" | Angelotti et al. 2026, arXiv 2606.29085 p. 17 (read at source, v1) | FIRM that they say it |
| PHerc. 1497, first subscriptio | the column count (152) stands "al di sotto" (below) the first title; the note ΑΒΓΔ is "nella parte superiore esterna dell'ultimo foglio" | Romano 2005 PDF pp. 408, 459, 547 (read at source, v1) | FIRM as quoted |
| PHerc. 1497, bibliological numerals | the column/sheet numbers ΙΒ, ΙΓ, ΙΔ, ΡΝ stand "in corrispondenza della parte centrale del margine superiore" of cols VI, XVI, XXVI, XXXVI | Romano 2005 PDF p. 458 | FIRM as quoted. Annotations *are* written in the upper margin, but these are not titles |
| PHerc. 222, end title | once described as about 1.5 cm below remains of the last column, slightly right of centre; Capasso shows that those remains belong to a different (bisovrapposto) layer, so the case is void | Capasso, Titoli IV (read at source, v1) | FIRM as quoted |
| PHerc. 1050, subscriptio | the column count (118) stands immediately below the subscriptio, in the same hand | Romano 2005 PDF p. 145 | FIRM as quoted. Internal layout only, no height |
| still missing: measured heights for PHerc. 1050, 1426, 1428, 1424, 188, 172, 139 | none found in open text | Del Mastro 2014 (paywalled) | GAP |

Working prior, UNCERTAIN, to be replaced in v1:
- The title block starts level with the top line of the last column, or in the upper third: 0.35.
- It is centred on the column height: 0.40.
- It is in the lower third, or aligned with the last line: 0.25.
- Reasons: centring is the default for a displayed block (the lines are centred horizontally, organizers 2025, D 3.3). The high-placement evidence is 2 of 3 statements above. There is no counter-case of a low title in my sources.
- Consequence for Paris 4: with the roll's upper margin lost (QA Q1), a title in the upper third loses its top lines or all of them. This is why TOP-LOST is large.


v1 additions (FIRM or LIKELY, from sources read at source):
- **End titles stand at the roll's centre.** Capasso (Titoli IV) argues that the final title normally lay at the centre of the rolled papyrus, the part carbonised and compressed. Rolls were stored rewound, with the beginning outside; he found only one roll stored at the end-of-reading position. FIRM as quoted. So the inner end is the right place to look, and the outer end (L6) is right only for initial titles.
- **Short last columns are attested,** which supports QA Q1 (i).
  - PHerc. 1428: the last column has 23 lines against a mean of 33 (ratio 0.70).
  - PHerc. 1426/1506: the last column has 9 lines against 33-34 (ratio 0.27).
  - Source: Romano 2005, PDF pp. 162, 167, citing Puglia and Bassi. LIKELY.
  - PHerc. 1426/1506 (0.27) matches the size of the c11-c13 block, 2 tile rows of a column of at least 12 cm.
- Working prior for the vertical position, re-weighted by PHerc. 1667 (whose preserved lower portion shows no title): top or upper third **0.40**, centred **0.40**, lower third **0.20**. UNCERTAIN.

## (c) Horizontal distance from the last column; blank end; final sheet

| quantity | value | case | source | grade |
|---|---|---|---|---|
| distance of the first end title from the last column | about 2.5 cm | PHerc. 1497 | Romano n. 940 | FIRM as quoted |
| same | about 10 cm | PHerc. 1027 | Capasso via Romano | LIKELY |
| distance below the last column (when below) | about 3 cm | PHerc. 1675 | Capasso Titoli I via Romano | LIKELY |
| second (calligraphic) title | +11.5 cm after the first | PHerc. 1497 | Romano | FIRM as quoted |
| agraphon between the first and second title | about 19 cm | PHerc. 1675 | Capasso via Romano | LIKELY |
| blank at the start and end of a roll | 10-20 cm | organizers' FAQ (informal) | D 4.4 | LIKELY |
| final protective sheet | a section exists in Del Mastro 2014; [v1] its dimensions | - | D 1.1 | FIRM that the section exists |
| share beside / below / repeated | 91.4 % / 7.1 % / 1.4 % of 70 | Cavallo 1983 p. 22 | D 1.1 | FIRM verbatim |

Paris 4 mapping (UNCERTAIN): the end of slot 1 is at about c13.5. A beside title at 2.5-10 cm lies in c14.5-c18.5. Its centre, for a 3-6 cm block, is in c15-c17.

## (d) Letter heights, block size, lines, decoration
- **Text letter height:** about 3 mm on average in Herculaneum papyri, and 2-3 mm in PHerc. Paris 1 (Mocella et al. 2015; D 1.5). FIRM.
- **Title letters in the text hand:** "the same size as the text or slightly larger" (Schironi 2010 via BMCR; LIKELY). Working range 2.5-4 mm.
- **Title letters in "Auszeichnungsschrift" (a specialist title hand), "modulo ampio":** no published mm value was found (D 1.2 GAP). Working range 4-7 mm, UNCERTAIN; [v1].
- **Lines:** 2-6. The usual order is author; title (1-2 lines); book number (often its own line); an optional count (ἀριθ. + stichometry, or columns) (D 1.2). LIKELY.
- **Block size:** width 3-6 cm, height 1.5-4 cm, centred lines (D 6, organizers 2025). LIKELY/UNCERTAIN.
- **Line pitch in a title:** 1.2-2 x the text line pitch. This is my inference from "centred on new lines" with display spacing. UNCERTAIN; [v1].
- **Decoration** (D 1.2):
  - dashes above and below (PHerc. 172);
  - oblique, horizontal and curved strokes, semicircles and small ellipses (PHerc. 1027);
  - ornaments between the title and the sub-title (PHerc. 1457);
  - a coronis (normally below the last column) marks the end of the text.
  - Geometry: dashes about the width of the line or longer, 1-4 cm; coronis about 1-3 cm tall at the left edge of the last lines. The geometry is UNCERTAIN; [v1].


v1 metrics (Romano 2005, read at source; FIRM as quoted unless marked):
- PHerc. 1497:
  - columns about 17 cm tall and 5.5-5.7 cm wide;
  - 42-47 lines (mean 44), i.e. a line pitch of about 3.9 mm;
  - 20-23 letters per line;
  - intercolumn a little under 1.5 cm (PDF p. 244).
- Herculaneum lines hold 18-21 letters, against 35-38 per stichos in the Greek rolls of Egypt; 100 stichoi ≈ 180-200 real lines (Cavallo p. 21, via Romano PDF pp. 150-151).
- Columns in other rolls: 33 lines (PHerc. 1428, 1426), 34 (1506), 35 (1425), 38 (1427), 25-26 (1414). LIKELY via Romano.
- The column pitch is about 5.5 + 1-1.5 cm = 6.5-7 cm in these rolls. The census estimate for Paris 4 is 8 ± 2 cm (compatible, but the 1 mm profile should confirm; REDTEAM R1).
- Kollemata:
  - 15.0-17.1 cm (On Poems 2; Capasso BMCR 2021.06.18);
  - 12.4 cm (PHerc. 207);
  - 13-14.5 cm (PHerc. 1675, where two kollemata were added at the end as reinforcement, per Capasso via Romano PDF p. 137).
  - The added end kollemata are the physical "final protective sheet" to look for (REDTEAM N5).
- Title letter heights in mm are **still a GAP** in every open source reached. The ranges in (d) above stay UNCERTAIN.

## (e) Initial titles and verso titles
- Initial titles: PHerc. 222, 253, 1457, 1583, 1786, 1008 (D 1.3; LIKELY). PHerc. 1457 has about 12 cm between the initial title and column 1 (Capasso Titoli II; LIKELY).
- Verso titles: PHerc. 339, 1491, 1670 (D 1.3; LIKELY). Where they stand on the verso: [v1].


v1, from Capasso, "I titoli nei papiri ercolanesi IV" (read at source; FIRM as quoted):
- Initial titles in all 5 Herculaneum cases stand "nell'agraphon iniziale, prima della colonna di apertura". The same position is found in 11 Greek rolls from Egypt.
- Gap between the initial title and column 1:
  - about 12 cm in PHerc. 1457 and PHerc. 222 ("pari all'ampiezza di due colonne");
  - about 25 cm ("un palmo") in the Phanias papyrus.
- Vertical datum: in PHerc. 253, line 1 of the initial title is "a cm 5 ca. dal lembo superiore della scorza". That is the fragment's upper edge, not necessarily the roll's.
- Upper margin: 4 Greek rolls from Egypt *may* carry the initial title in the upper margin of column 1. Capasso calls them "esempi dubbi". No Herculaneum case exists. This bears on QA Q3: none for end titles, 4 doubtful for initial titles, and none in Herculaneum.
- Verso: three initial titles written on the verso are known in Herculaneum, including PHerc. 1491. Each was placed opposite one of the first columns. Luppe estimates the circumference of a closed roll at 20-24 cm, from the positions of verso titles in Greek rolls from Egypt.
[line withheld: prize-candidate detail under review]
- A roll that was not rewound would rarely preserve its end title: the outer, unprotected part was destroyed. Capasso found only one Herculaneum roll stored at the end-of-reading position.

## (f) Ink class for titles specifically

| class | P | basis | grade |
|---|---|---|---|
| the same carbon ink as the body, same deposit (the same scribe; PHerc. 172 and 139 recovered with the body-text pipeline) | 0.90 | Angelotti et al. 2026 (FIRM); Cavallo on the same hand (FIRM) | UNCERTAIN as a probability |
| carbon, but thinner, diluted or more worn (a refilled pen, larger letters with thinner strokes, a later addition) | 0.05 | no source; physical plausibility | UNCERTAIN |
| a carbon ink with a lead additive, distinct from the body ink | 0.01 | Pb inks attested in Herculaneum (Brun 2016, Tack 2016, FIRM), but not title-specific | UNCERTAIN |
| red mineral (minium, cinnabar, ochre) | 0.015 | Roman texts on red *tags* (Ovid, Martial; FIRM as texts); no Herculaneum attestation | UNCERTAIN |
| other colourants (purple, blue, gold, organic dyes) | 0.01 | codex-era practice; no attestation in Greek rolls of the 1st c. BC | UNCERTAIN |
| unknown or other (the remainder) | 0.015 | the reserve, so that the table sums to 1 | UNCERTAIN |

Conditional note (REDTEAM R4): given that the title lies on preserved papyrus inside the organizers' inspected region, the non-detection shifts weight. It moves toward faint, flaked or sparse-block failure (0.75 together), not toward non-carbon inks (about 0.10).

## (g) What a "fancy" title looks like in a 1st-c. BC Greek roll (as opposed to codex illumination)
- **The letters themselves:** well-spaced capitals, bilinear, sometimes larger than the text, sometimes in a formal "display" hand by a specialist title scribe (Del Mastro's scribes A and B; D 1.2, FIRM via review). There are no minuscules, no ligatures, and no enlarged initial letter; initials in Greek rolls of this period are at most slightly enlarged (my UNCERTAIN recollection).
- **Framing:**
  - horizontal dashes (or rows of dashes) above and below the block;
  - oblique, curved or elliptical strokes around it;
  - small ornaments between the lines;
  - a coronis (a stylised hooked or bird-like pen ornament) at the end of the text, and a paragraphos (a short horizontal stroke) at line beginnings.
  - All are **pen strokes in the same black ink** as far as the literature records (D 2.1, 2.3).
- **What does not occur:** painted or illuminated initials, gold or silver lettering, coloured frames, figurative ornament, and purple-dyed papyrus. These belong to late-antique and Byzantine codices (4th-6th c. AD onward; D 2.3, LIKELY). The owner's reference picture (an ornate decorated initial) is in that tradition.
- **Consequence for detection:**
  - a sparse block with extra non-letter strokes: 5-30 strokes of 1-4 cm (dashes), plus 10-50 letters;
  - letters at 1-2 x the text size;
  - a total of 1.5-4 cm × 3-6 cm.
  - It is covered by DECL-P4-17 (P4-W, the "block" brief), subject to the T7 synthetic-block control of REDTEAM.

## Sources that would most change these priors (paywalled or unread)
1. **Nicolardi, Delattre, Del Mastro, Fowler, Janko, CErc 54 (2024) 9-27, "The final columns of PHerc. Paris. 4".** It would settle:
   - whether the final column is short, and its line count (QA Q1 (i) against (ii));
   - lines per column, column height and width, intercolumn, letter height and line pitch (the slot geometry of REDTEAM R1);
   - whether the first lines of the final columns are lost (the top edge);
   - whether a coronis or end mark was seen;
   - how the end of the text was established.
   Expected shift: Q1 from 0.65/0.20 to about 0.95/0.02 either way.
2. **Nicolardi et al., ZPE 229 (2024) 1-13.** Column metrics and the numbering from the end; the hand. It would settle the letter-height ratio needed for the title size prior, and the pitch.
3. **Del Mastro 2014, CErc Suppl. 5.** The catalogue of 118 titles with position, hand, decoration and the final protective sheet section. It would settle (b) (the vertical position rate), (c) (the distance distribution), (d) (the calligraphic letter sizes) and (e) (the verso title positions).
4. **Capasso, "Titoli" I-IV** (and his *Manuale di papirologia ercolanese*, 1991). Per-roll measurements of the distance and the agraphon.
5. **Cavallo 1983, CErc Suppl. 1**, pp. 20-23 and the tables. The 70-title census by position, and the scribes.
6. **Angelotti et al. 2026, Supplementary Information (if published).** The PHerc. 172 and 139 title geometry in 3-D (distance to the last column, vertical position, letter mm). These are the two closed-roll analogues read by the same pipeline.
7. **Schironi 2010** (ASP 48): the statistics of end-title position in hexameter rolls. It would give an Egyptian comparandum for (b).
