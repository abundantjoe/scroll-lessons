# P4 title-search research dossier (sibling p4-research)

Provenance: Project HERCULES | owner the owner | [id removed]
Serves: RULES.md DECL-P4-10 item 5 (research sibling), DECL-P4-2, -5, -6 (+A1, A2), -7.
Started 2026-09-26 18:00Z. Status: v4, complete (sections 0-7), 2026-09-26 ~19:45Z.

Integrity:
- No image, tile, render, prediction pixel or CT voxel was opened, viewed or described by this sibling.
- Section 4 uses only:
  - committed census numbers (letter counts per tile);
  - labelled-adjacency distances;
  - mesh vertex coordinates (tile_points.npz, float xyz).
- No title word is proposed, and none will be.
- No unpublished competitor claim, Discord post or blog is used as evidence.

Grades:
- **FIRM**: primary source or peer-reviewed, read at source.
- **LIKELY**: reliable secondary source, or read in summary only.
- **UNCERTAIN**: unverified, or our own inference.

---

## 0. Executive summary (for the orchestrator)

1. **The strip's own numbers show where the work ends.** This is new, numbers-only, and graded as our inference.
   - On the 20260701183124-w010-027 canvas, c0 is the outer end (w027 side). The median tile radius falls monotonically from 5.3 mm at c0 to 1.9 mm at c19.
   - r0 is the high-z end (z about 165 mm); r7 is the low-z end (about 42 mm).
   - The P4-B census, blind reads of the official 2.4 um predictions, shows three zones:
     - dense text-like rows in c0-c9, rows r0-r5;
     - a nearly blank c10;
     - text-like signal in c11-c13 **only in the top two rows r0-r1** (z about 147-165 mm);
     - then **nothing at all in c14-c19** (48 of 48 tiles rows N).
   - Weak census columns recur every 4 tiles: c11, c15 and c19 on w028-037, then c2, c6 and c10 on w010-027. The w028-037 c20 tile is continuous with w010-027 c0, as the labelled-segment chain below shows.
   - This gives a column pitch (column plus intercolumn) of about 8 cm, ±2 cm from the 2 cm quantisation.
   - This is the signature of a roll end:
     - the last full column ends at c9;
     - c10 is an intercolumn;
     - c11-c13 is one more column slot. It holds only a few lines at one end, either a short last column or the title itself.
     - c14 onward is blank papyrus toward the core.
   - **The title is expected in c11-c14, about w019-w022.** It could sit below or beside the short block in c11-c13 r0-r1, or in the next slot c14-c17 as "a subsequent column that can be otherwise blank" (organizers, 2024). Section 4 gives the reasoning and caveats.
1b. **Scholarship agrees.** In Cavallo's census of 70 Herculaneum titles, 91% stand *beside* (to the right of) the last column, "always after some space". 7% stand below it (Cavallo 1983, p. 22, verified verbatim). Measured offsets are 2.5-10 cm (PHerc. 1497, 1027). On our canvas, the "right" of the last column is higher c, i.e. inward. So the first-choice title window is **c10-c14**, about 2.5-10 cm past the end of c9. A second, calligraphic title may lie a further 11.5-19 cm on (PHerc. 1497, 1675), in c15-c19.
2. **c11-c13 r0-r1 lies outside the 1.129 um scan's z-range** (z 67.4-135.3 mm). Only the 2.4 um material (M1 predictions, E2 raw CT) covers it. Rows r2-r5 of those columns are inside the 1.129 um scan.
3. **The title zone lies on a labelled segment.**
   - The labelled (ink_9um / S3-label) segment 20231016151002 coincides (distance 0.00 mm) with w010-027 c9-c15, rows r0-r3.
   - So DECL-P4-2's labelled-adjacency rule excludes exactly the title zone from candidacy.
   - The prize rule states: "Ink model outputs of this region should not overlap with any training data used."
   - A raw-CT channel with no trained model avoids the overlap by construction: DECL-P4-5 E2, the DECL-P4-6 dense channel, or the direct-visibility route in item 4.
4. **Ink in PHerc. Paris 4 is directly visible in the 2.4 um BM18 volume, with no ML.** Angelotti et al. 2026 (arXiv 2606.29085, organizers' paper) report "ink-bearing strokes appear as bright, surface-associated deposits with apparent cross-sectional thicknesses of approximately 10-20 µm", thanks to Paganin phase retrieval (δ/β 1000). FIRM.
   - So the "no detectable ink" statement means more than "carbon models miss it". In the expected title region, the raw 2.4 um volume shows none of the bright surface deposits that the known text shows.
   - That fits three explanations:
     - (a) the title is not in the region the organizers searched;
     - (b) the surface is missing or damaged there ("the top rows are physically missing");
     - (c) the ink is physically different, low-density or thin, with no bright deposit.
   - A dense mineral ink (red lead, cinnabar or gold) would be *brighter*, not invisible, and would have been seen at a surface the organizers inspected. The dense-pigment hypothesis is therefore only viable for a region the organizers did not inspect, or on a surface the official meshes do not trace.
5. **Honest priors (section 2.4, UNCERTAIN):**
   - P(visibly coloured title) ≈ 2% (1-5%);
   - P(title ink physically different from the body) ≈ 3-5%;
   - P(dense high-Z title distinct in CT) ≈ 2-4%.
   No coloured title or pigment is published for any Herculaneum papyrus. Titles are by the text scribe (PHerc. 172). Rubrication and chrysography are codex-era practice.

---

## 3. What the organizers have published about the PHerc. Paris 4 Title Prize

### 3.1 The prize page (rules, deadline, status)
Source: Vesuvius Challenge, "Open Prizes", https://scrollprize.org/prizes, fetched 2026-09-26T18:02:46Z (raw HTML sha256 661c7d08fe5f8405...). FIRM (official). Verbatim:
- Amount and scope: "PHerc. Paris 4's Title: $50,000 to the first team to discover the title of PHerc. Paris 4 (Scroll 1), using any of its scans — including the 2.4 µm volumes."
- Context and the ink statement: "Scroll 1 is one of our most-read scrolls: substantial continuous Greek text of an Epicurean prose work has been recovered, yet its author and title remain unknown. The expected title region has shown no detectable ink so far — possibly a different ink, and the top rows are physically missing — so finding it may take better methods, higher resolution, or looking somewhere new."
- Deadline: "Deadline: June 25th, 2027 (11:59pm Pacific)". Also: "Submissions remain open until the prize is won: if we discover months from now that your method was right all along, you will then win."
- Why a title matters: "We have already recovered the titles of PHerc. 172 and PHerc. 139 — but the title of Scroll 1, the scroll where the first passages were read, is still missing."
- Requirements (summarised; all verbatim on the page):
  - **Mesh**: tifxyz of the surface region containing the title, "already including a low-distortion isometric 2D parametrization (flattening)".
  - **Image**: "an image of the virtually unwrapped region, showing the title visibly and legibly."
    - "Illustrate the ink predictions in the spatial context of the title search, similar to what is shown here" (link: https://scrollprize.substack.com/p/30k-first-title-prize).
    - "You do not have to read the title yourself — you have to produce an image of it that our team of papyrologists is able to read."
  - **Programmatic generation**: "Images must be generated programmatically from the reconstructed CT scan volume and the mesh submitted in the same package, and should not contain manual annotations of characters or text. Ink model outputs of this region should not overlap with any training data used."
  - **Scan and scale**: name which scan the image comes from (any published Scroll 1 volume qualifies); include a 1 cm scale bar, plus "the pixel and millimeter dimensions of a few representative letters".
  - **Traceability**: name the image after the tifxyz mesh.
  - **Methodology**: Docker, or instructions plus a video.
  - **False-positive mitigation**: "The larger your model's window size, the easier it is for it to invent plausible letterforms … you must demonstrate the letters and words are not hallucinated — for example by validating on a held-out region with known ground-truth."
  - **Held-out validation**: run on "the public input renders/volumes with known ground truth (using k-fold validation if you trained on them)".
  - Review: "reviewed by the review teams to verify technical validity and papyrological plausibility and legibility."
  - Embargo: "you must not make your discovery public until the prize is officially announced."

**What counts as a winning reading (FIRM).**
- An image the organizers' papyrologists can read, whether or not the team reads it itself, that shows the title "visibly and legibly".
- It must be produced programmatically, from the declared mesh, with no overlap with training data.
- The page sets no fixed letter count. The 2024 First Title rule was "our papyrologists can read enough of it to identify the work" (3.2), which is the practical bar.
- The page caption shows "Visible Title in a Physically Opened Papyrus (PHerc. 1050)" as the model example.

**Is the prize still open on 2026-09-26? Yes (FIRM).** The live page lists it under open prizes with the June 25th, 2027 deadline. The winners list shows no Paris 4 title award (checked in logs/p4/recon.md at 00:04Z; re-confirmed by this fetch). STATE.md's "Prize: … no award" agrees.

### 3.2 The 2024 First Title Prize post (the organizers' layout guidance)
Source: Vesuvius Challenge, "$30k First Title Prize", Substack, published 2024-06-05T18:48:14Z, https://scrollprize.substack.com/p/30k-first-title-prize (sha256 c7a5b557f0bfe522...). FIRM (official). Verbatim:
- "We know from the opened ones that Herculaneum scrolls often contain a final title at the end of the roll."
- "If you find the title in Scroll 1 and our papyrologists can read enough of it to identify the work, the First Title prize is yours!"
- "This image shows the end of the scroll, and the segments that have so far been made in a search for the title." The figure was not viewed (image rule). Its segment IDs are the five listed in logs/p4/recon.md; they are on the 7.91 um EduceLab volumes.
- "The title often follows the end of the primary text, in a subsequent column that can be otherwise blank. When the final column of the primary text is short, it may also appear below this last column."
- "Typically, there is additional information grouped with the title. It often starts with the author's name on a line of its own. The title itself follows, sometimes spanning multiple lines if it is long enough. If the work consists of multiple books, the next line might indicate the book number. Finally, sometimes the number of lines or the number of columns in the book are included below that. Decorative elements like serifs or other strokes sometimes also appear around the title. Here's an example from PHerc. 1050". The example image source is Chartes.it.

### 3.3 The PHerc. 172 title award (layout precedent from a closed roll)
Source: Vesuvius Challenge, "$60,000 First Title Prize awarded", published 2025-05-05T21:54:50Z, https://scrollprize.substack.com/p/60000-first-title-prize-awarded (sha256 86050080cc3808b8...). FIRM (official).
- "the written title of this scroll has been recovered from deep inside its carbonized folds of papyrus", read by the team led by Federica Nicolardi as Philodemus, *On Vices*, Book 1(?).
- "Typically, the author's name, the title, and the number are each center justified on new lines". PHerc. 172 was the first seen with the book number on the title's line.
- Decoration: "the framing of the title by the decorative dashes above and below."
- Angelotti et al. 2026 (3.4) add, on the PHerc. 172 final title: "The title was written by the same scribe who copied the text." FIRM.

### 3.4 Organizers' June 2026 publications
- **Announcement** (June 25th, 2026), https://scrollprize.org/firstscroll (sha256 f08aad8b9397b80d...). FIRM.
  - For Paris 4, "a higher-resolution imaging technique makes the ink directly visible inside the scroll itself, in the three-dimensional X-ray data, for the first time … that ink matches the text read in the 2023 Grand Prize one-to-one".
  - For PHerc. 139: "we recover the scroll's title and author attribution: the work is identified as Philodemus, On Gods, Book 8".
- **Paper**: G. Angelotti, S. Parsons, F. Nicolardi, … G. Del Mastro, M. McOsker, K. Fleischer, … W. B. Seales, "Complete virtual unwrapping and reading of a rolled Herculaneum papyrus", arXiv:2606.29085, 2026-06-27, https://arxiv.org/abs/2606.29085. Preprint by the organizers' team, graded FIRM for what they report of their own data.
  - Paris 4: "In the optimized high-resolution BM18 scan of PHerc. Paris 4, thanks to phase retrieval, ink-bearing strokes appear as bright, surface-associated deposits with apparent cross-sectional thicknesses of approximately 10–20 µm". Extended Data Fig. 3 compares "No Paganin (δ/β 0.0001)", where "contrast is weak and washed out", with "Paganin (δ/β 1000)", where "ink flakes … are brighter than the surrounding papyrus". The scan was at 78 keV, 2.4 µm, 0.22 m propagation.
  - PHerc. 139: the book number "is written here on the same line as the title, despite the more commonly attested practice in titles from Herculaneum, where the title and book number appear on two separate lines." Fig. 4 has a 5 mm scale bar.
  - PHerc. 1667 (a core, "midollo"): "The title, which in ancient bookrolls was typically written also at the end of the text, has not been recovered and may have been located in the now-lost upper portion of the roll." This is a direct precedent: the end title's region can be physically lost at the top.
- **Open problems**: Vesuvius Challenge, "Open Problems: Why Reading Every Herculaneum Scroll Is Still a Challenge", https://scrollprize.org/2026_open_problems ("Last updated: July 10, 2026"; sha256 3aa7e021cdfd6e2c...). FIRM.
  - "In recent high-resolution scans of PHerc. Paris 4, ink-bearing deposits become visible enough to support direct volumetric segmentation … the letter is directly visible" (panel c: "Virtually unwrapped PI (no ink detection …)").
  - The official 3D model "ink_3d_dino_guided is trained specifically for PHerc. Paris 4".

### 3.5 The expected title region: what is and is not published
- **Published (FIRM):**
  - The known text is the end of the work. The data browser captions it "Ink detection across windings 28–37 (2.4µm)" (recon.md, critic additions).
  - The CErc paper title is "The final columns of PHerc. Paris. 4": Nicolardi, Delattre, Del Mastro, Janko, Fowler 2024, *Cronache Ercolanesi* 54, 9-27. Its abstract: "portions of sixteen columns from the final part of the roll" (https://cispe.org/abstracts-cronache-ercolanesi-54-2004/).
  - The title region "has shown no detectable ink so far", and its "top rows are physically missing".
- **Not published (FIRM, absence verified on the pages above):**
  - no winding number;
  - no segment ID for the 2026 title region;
  - no coordinates;
  - no statement of which rows are the "top".
  The 2024 figure's segments are on the 7.91 um EduceLab volume; their mapping to the 2026 w-numbering is not published.
- **Context of "possibly a different ink" (FIRM + inference):**
  - The sentence was published on the prize page while the organizers had the direct-visibility result for known-text ink in the 2.4 um volume (3.4).
  - Our reading (UNCERTAIN): at the surface they consider the title region, they see neither model ink nor the bright 10-20 µm deposits that carbon ink forms elsewhere. "Different ink" is offered as one of three explanations (ink / missing top rows / wrong place), not as a finding. Their own advice: "better methods, higher resolution, or looking somewhere new".

---

## 4. Physical layout implications for our data

All numbers in this section are ours. They come from committed files and were computed by this sibling from numbers only. Grade: UNCERTAIN (our inference) unless marked. Script and outputs: logs/sib/p4-research/geom/.

### 4.1 Orientation of the w010-027 canvas (measured)
Source: tile_points.npz (branch sib-p4-tiles-a, 4096 mesh points per tile, 20260411134726 frame, 2.4 um voxels).
- **Rows (z):** the median z per tile row is r0 165, r1 147, r2 128, r3 112, r4 93, r5 74, r6 57 and r7 42 mm. So **r0 is the high-z end.**
- **Columns (radius):** the median radius from a per-5-mm-z centroid (a crude axis proxy) falls monotonically, row by row, from 5.3-5.6 mm at c0-c1 to 1.7-2.0 mm at c19. So **c0 is the outer end, adjacent to w028, and c19 is the innermost, near w010-w012.**
- **Winding estimate:**
  - Formula: w ≈ 10 + (r − 1.46 mm)/0.22 mm, using r(w010) = 1.46 mm and a pitch of about 0.22 mm outside w010 (both from p4-inner RECON.md).
  - Mesh-area check: 641 cm² / 14.4 cm ≈ 44.5 cm of sheet over 18 windings.
  - Mapping: c0 ≈ w027; c9-c10 ≈ w021-w022; c11-c13 ≈ w019-w021; c14-c19 ≈ w012-w018. The error is ±2 windings, because the roll is crushed and the centroid axis is crude.
- **Labelled-chain check (p4-excl excl_a/excl_b, per-tile nearest labelled segment):** walking c0 → c20 on w028-037 and then c0 → c19 on w010-027, the nearest labelled segment runs monotonically:
  - 20230929220926 / 20231007101619 / 20231210121321 (w028-037 c0-c3);
  - 20231012184424 (w028-037 c4-c17);
  - 20231106155351 / 20231031143852 (w028-037 c15-c20, w010-027 c0-c5);
  - 20230702185753 (w010-027 c5-c9);
  - 20231016151002 (w010-027 c9-c15).
  This independently confirms that both canvases increase inward and that w028-037 c20 is continuous with w010-027 c0.

### 4.2 The end of the text (census signature)
Source: logs/p4/census_a_summary.json and census_b1_summary.json (P4-B phase 1; the blind-reader letter count per 2 x 2 cm tile on the official 20260417190342 2.4 um predictions).
- These are **unconfirmed** LLM counts. The N0 null reaches 4 letters.
- They are used here only as a coarse text/no-text profile, never as letters.

w010-027 letters per tile ("." = rows N):
```
     c0  c1  c2  c3  c4  c5  c6  c7  c8  c9 c10 c11 c12 c13 c14 c15 c16 c17 c18 c19
r0    5   5   3   3   4   6   .  13   4   8   .   1   2   8   .   .   .   .   .   .   z~165
r1   11   6   2   6   4   4   .   8   6   9   1   7   8   2   .   .   .   .   .   .   z~147
r2   12   4   2   4   4   6   1   9  10   6   .   .   .   .   .   .   .   .   .   .   z~128
r3    5   9   1   4   4   7   .   7   7   9   .   .   .   .   .   .   .   .   .   .   z~112
r4    9  10   .   6   3   6   1   6   4   5   .   .   .   .   .   .   .   .   .   .   z~93
r5    5   8   1  10  10   9   2   8  10   4   .   .   .   .   .   .   .   .   .   .   z~74
r6    1   0   1   .   5   1   1   0   2   2   .   .   .   .   .   .   .   .   .   .   z~57
r7    .   0   .   .   1   1   2   0   .   1   .   .   .   .   .   .   .   .   .   .   z~42
```
Readings, all UNCERTAIN:
- **Column period.** The minimum columns fall at c2, c6 and c10 here, and at c11, c15 and c19 on w028-037 (c19: 7 of 8 tiles rows N). Across the strip join this is a regular pitch of 4 tiles, about **8 cm per column plus intercolumn**. For Philodemus rolls a pitch of this size is normal; section 1 will cite values.
  - Validation: the pitch must be the same on both strips. It is: 4, 4, 4 tiles across the join.
- **Last full column: c7-c9.** Text-like counts run to c9 at every height r0-r5.
- **c10:** 7 of 8 tiles rows N. This is consistent with an intercolumn.
- **c11-c13, one more column slot, has signal only at r0-r1 (z about 147-165 mm).** Its counts are 1, 2, 8 / 7, 8, 2 letters, and 4 of 6 exceed the null maximum of 4. The other 18 tiles in c11-c13 are rows N. This is a block a few lines high at the high-z end.
- **c14-c19: 48 of 48 tiles rows N.** This is blank papyrus to the core. It is consistent with the uninscribed end of a roll (a model non-detection, not proof of blankness).
- **The raw-CT census (E2, census_e2_summary.json) is uninformative:** rows Y in 5 of 160 tiles, 0 letters anywhere. This is the declared contrast channel (±53 um mean), not the 10-20 um deposit channel of 3.4.

### 4.3 Where the end title should be (ranked hypotheses)
Direction of writing: the text starts outside and ends in the core, so the title follows further inward (higher c).
- **H1: the c11-c13 r0-r1 block is the short last column of text, and the title lies below it**, i.e. at lower z in c11-c13 rows r2-r4 (z about 90-130 mm).
  - This matches the organizers' rule "When the final column of the primary text is short, it may also appear below this last column."
  - Official predictions show nothing there, which matches "no detectable ink so far".
  - Caveat: this needs the high-z end to be the column top. If instead high z is the bottom of the page, the r0-r1 block sits at the column foot, which would favour H2.
- **H2: the c11-c13 r0-r1 block is itself (part of) the title.**
  - It is a small block at one end, centred in its own column slot one intercolumn after the last full column. That is the "subsequent column that can be otherwise blank" layout.
  - Then its missing lines would lie just beyond r0 (z > 165 mm, off the written region) or in r1-r2. The organizers write "the top rows are physically missing".
- **H3: the title is in the next slot, c14-c17 (about w016-w019).** In this reading the c11-c13 block is the tail of the text in a short last column.
- **H4: the title lies inward of w010, in w000-w009, the core of radius 0.7-1.6 mm (DECL-P4-7). Low prior.**
  - An end title normally sits within one column pitch (about 8 cm) of the last text. From c11 to the w010 end of the strip there are still about 16-18 cm of traced papyrus (c11-c19 plus the canvas margin), 2 column slots, and all of it reads blank.
  - Precedents such as PHerc. 1050 and PHerc. 1497 show the end title followed by a blank end; section 1 will cite them. An end title about 20 cm or more beyond the text would be anomalous.
  - Prior: P(title inward of w010) ≈ 0.05-0.10.
- **Relation to the 1.129 um scan (z 67.4-135.3 mm):**
  - r0 (165) and r1 (147) are **outside** it. r2-r5 (128-74) are inside; r6-r7 are outside.
  - H2's block, and any part of the title near it at high z, can only be examined in 2.4 um material (M1 predictions, E2 raw CT, 20260411134726).
  - H1's region (c11-c13 r2-r4) is inside the 1.129 um footprint, so E1 and P4-D M2a cover it.
- **The labelled-segment overlap (FIRM, measured by p4-excl):** 20231016151002 lies at 0.00 mm from w010-027 c9-c15, rows r0-r3. So:
  - the DECL-P4-2 labelled-adjacency rule excludes these tiles from candidacy;
  - any model trained on the ink_9um / S3 labels of that segment would breach the prize rule "Ink model outputs of this region should not overlap with any training data used";
  - a no-model raw-CT channel has no overlap by construction.

### 4.4 Column width and intercolumn on the known-text strip
- **Published values for Paris 4:** Nicolardi et al. 2024 (CErc 54) is the source. Their numbers are pending section 1: the full text is not open, and the research agent is checking. A search-engine summary says the roll height is 16.75 cm with 5.38 cm "unrevealed", which is UNCERTAIN and unverified.
- **Organizers' FAQ** (https://scrollprize.org/faq, fetched 2026-09-26 ~18:55Z, sha256 22c840a1ae027146...; informal notes on the official page, so LIKELY):
  - "10-20cm blank at start and end of scroll";
  - "4.5-6cm columns, 1/6 of column space between columns";
  - "~1/8 height paddings top and bottom".
  - That implies a pitch of about 5.3-7 cm, and a blank end of 10-20 cm. Our blank zone c14-c19 is 12 cm or more of traced sheet, plus the untraced w000-w009.
- ~~A search-engine summary gives "13.2 m, ~165 columns" for ZPE 229~~ **RETRACTED.** Sub-worker (c) traced it to Wikipedia or press only; there is no peer-reviewed or organizer source. It is not used anywhere.
- **Our measurement from the census period** (UNCERTAIN): column plus intercolumn ≈ 8 ± 2 cm. At the w019-w022 radii (per-winding sheet length about 2.7-3.5 cm), **one column spans about 2-3 windings**. So the title block, if a few centimetres wide, spans about 1-2 windings in the 3-D volume.
- **Validation for a finer measurement:** a numbers-only column-profile check that sums prediction values over z per canvas column at 1 mm bins (no viewing) would give the intercolumn positions to ±1 mm. It is proposed under a builder declaration in section 5.

---

## 1. End-titles and initial titles: position, size, decoration, stichometry

Compiled by sub-worker (a).
- Full texts of Cavallo 1983, Capasso, Del Mastro 2014, Delattre 2007, Johnson 2004, Turner-Parsons, ZPE 229 and CErc 54 were paywalled or blocked.
- The key measurements come from A. Romano, *Segni e particolarità grafiche nel PHerc. 1497*, PhD thesis, Università di Napoli Federico II, 2004-05, http://www.fedoa.unina.it/2723/1/Romano_Filologia_Classica.pdf ("Romano 2005"). It quotes Cavallo and Capasso with page numbers.
- **This sibling downloaded the thesis and verified the Cavallo quotation and the PHerc. 1497 distances verbatim** (text lines cited below).
- Romano 2005 is a deposited doctoral thesis, not peer-reviewed. Its quotations of peer-reviewed works are graded FIRM for the quoted words.

### 1.1 Position of the end title (subscriptio)
- **Cavallo's census of 70 Herculaneum rolls with a preserved title.** G. Cavallo, *Libri scritture scribi a Ercolano* (CErc Suppl. 1, 1983), p. 22, quoted verbatim in Romano 2005, n. 147 (thesis p. 77):
  - "5 (7,14%) recano il titolo stesso, lasciato un certo spazio, al di sotto dell'ultima colonna": 5 have it *below* the last column, after some space.
  - "64 (91, 42%) a fianco di quest'ultima, sempre lasciato un certo spazio": 64 have it *beside*, i.e. to the right of, the last column, always after some space.
  - "1 (1, 42%) reca il titolo ripetuto": PHerc. 1497, with the title repeated.
  - **FIRM** (verified verbatim). Romano notes that the figures need updating from later work (Capasso, Del Mastro).
- **Measured offsets from the last column:**
  - **PHerc. 1497** (Philodemus, *On Music* IV):
    - first title "A destra dell'ultima col., ca 2,5 cm più avanti", in the text hand, with the column count (152) below it;
    - a second title "dopo 11,5" cm in calligraphic "Auszeichnungsschrift dal modulo ampio";
    - a bibliological note (the letters of the books) c. 5 cm further, "nella parte alta del supporto scrittorio" (in the upper part).
    - Romano 2005, n. 940 (PDF p. 408) and PDF p. 459. **FIRM** as quoted; Cavallo p. 23.
  - **PHerc. 1675** (Philodemus, *On Vices*, flattery): first title c. 3 cm below the last column, then an agraphon of c. 19 cm, then a second title. Capasso, "Titoli I", pp. 237-252, via Romano. LIKELY.
  - **PHerc. 1027** (Carneiscus): the title is "quasi al centro dell'ultimo foglio" (almost in the centre of the last sheet), c. 10 cm from the last column, in the text hand. Capasso, *Carneisco*, pp. 144-149, via Romano. LIKELY.
  - **PHerc. 188** (Demetrius Laco, *Poetics* I): the title stands in a long agraphon. It has six lines: 2 (author, title), a gap of c. 20 mm, then 4 bibliological lines. A. Giandomenico, review of Del Mastro 2014, *Papyrologica Lupiensia*, http://siba-ese.unisalento.it/index.php/plup/article/download/19111/16306. FIRM (review).
  - **PHerc. 994** (Philodemus, *On Poems* 2): the true end survives, but the agraphon is blank. Capasso suggests the title was on a part lost in unrolling. M. Capasso, BMCR 2021.06.18, https://bmcr.brynmawr.edu/2021/2021.06.18/. FIRM.
- **Alignment:** author, title and book number are "each center justified on new lines" (organizers, 2025; 3.3). Schironi 2010 (via BMCR 2011.03.22) says the book number is "in most cases, centred beneath the title". LIKELY.
- **Vertical position: no published rule was found.** UNCERTAIN.
  - PHerc. 1497's note is "in the upper part".
  - PHerc. 1027's title is near the centre of the last sheet.
  - PHerc. 1667's title "may have been located in the now-lost upper portion" (Angelotti et al. 2026).
- **Doubled titles:** a second, calligraphic final title 11.5-19 cm beyond the first is attested (PHerc. 1497, 1675). FIRM/LIKELY.
- **Blank end:** the organizers' FAQ says "10-20cm blank at start and end of scroll" (LIKELY; 4.4). Del Mastro 2014 has a section on the "foglio di protezione finale" (final protective sheet). FIRM that the section exists.

### 1.2 Hand, letter size, lines, decoration
- **Hand:** subscriptions are "per lo più vergate dalla medesima mano" as the text (Cavallo, via Romano, p. 77). **FIRM.**
  - Some are in an impersonal "Auszeichnungsschrift" by specialist title scribes. Del Mastro 2014 names two:
    - Scribe A: PHerc. 26, 222, 253, 873, 896, 1003, 1275, 1424, 1457, 1675.
    - Scribe B: PHerc. 1497, 1005/862, probably 757.
  - Source: Giandomenico review, n. 5. FIRM (review).
  - PHerc. 172: "same scribe who copied the text" (Angelotti et al. 2026). FIRM.
- **Letter size:** no mm values for Herculaneum titles were found in any accessible source. This is a GAP.
  - Qualitative: in the text hand the letters are "the same size as the text or slightly larger" (Schironi 2010 on hexameter rolls, via the BMCR review; LIKELY).
  - Calligraphic second titles have a "modulo ampio" (large letter size; FIRM, Romano).
- **Lines:**
  1. author in the genitive;
  2. title (one or more lines);
  3. book number (often a separate line, but on the same line in PHerc. 172 and 139);
  4. optionally a count: ἀριθ(μός) plus stichometric number, the number of columns, κολλήματα.
  - Attested counts: 2 lines (PHerc. 1457 final, 1008), 3 (873), 4 (1497, first title), 5 (1533), 6 (188). LIKELY.
- **Decoration** (Romano, citing Capasso and Puglia; LIKELY):
  - oblique, horizontal and curved strokes, semicircles and small ellipses around the title (PHerc. 1027);
  - dashes above and below (PHerc. 172, organizers 2025);
  - ornaments between the general title and the sub-title (PHerc. 1457);
  - a coronis, "di norma posta sotto l'ultima colonna" (normally placed under the last column), marks the end of the text.
- **Stichometry:** acrophonic numerals (Ι 1, Π 5, Δ 10, Η 100, Χ 1000), usually after ΑΡΙΘ. Examples:
  - PHerc. 1027: 3238;
  - PHerc. 1533: 2015;
  - PHerc. 1050: column count 118;
  - PHerc. 1497: 152 columns.
  Marginal letters mark every 100 stichoi (Cavallo 1983, pp. 20-21, via Romano). LIKELY.

### 1.3 Initial titles
- Initial titles are known for PHerc. 222, 253, 1457, 1583, 1786 (a scorza) and the "Phanias" roll with PHerc. 1008. Both initial and final titles survive in PHerc. 1008 and 1457. Titles on the verso: PHerc. 339, 1491, 1670 (Del Mastro 2014, via Giandomenico; Capasso, *Titoli* I-IV). LIKELY/FIRM.
- PHerc. 1457: c. 12 cm between the initial title and column 1 (Capasso, *Titoli* II, pp. 110f.). LIKELY.
- **For Paris 4, an initial title would sit at the outer beginning of the roll.** It is almost certainly lost or unrelated to our inner strips: the beginning is on the outer windings, and Paris 4 is a fragment of a longer roll (section 7). It is not a search target for the inner strips.

### 1.4 Same ink?
No source reached states explicitly that end titles are in the same ink. The sources speak of the same *hand* (Cavallo; the PHerc. 172 scribe). The ink question is taken up in section 2.

### 1.5 Addenda (sub-worker (a), revised report)
- **Text letter size:** Mocella et al. 2015 (*Nat. Commun.* 6:5895, doi:10.1038/ncomms6895) report letters "roughly in agreement with the average letter size in the Herculaneum papyri (around 3 mm high)", and about 2-3 mm in PHerc. Paris 1. FIRM.
- **Umbilicus:** Herculaneum rolls "did not always have a stick … quite frequently they were simply rolled upon themselves". R. Janko, "The Herculaneum Library: some recent developments", *Estudios Clásicos* 121 (2002) 25-41, https://ancphil.lsa.umich.edu/-/downloads/papyri/JankoRecentDevelopments.pdf. FIRM. So the innermost core (w000-w009) may be the rolled-up end of the sheet itself, i.e. the blank end.
- **Roll scale:** Janko's reconstruction of *On Poems* 2 has 99 kollemata of 15.0-17.1 cm, about 16 m and 222 columns (Capasso, BMCR 2021.06.18). That is a column pitch of about 7.2 cm, consistent with our 8 ± 2 cm. FIRM (review).
- **Johnson 2004 / GMAW:** only the review-level facts were verified (S. Stephens, BMCR 2005.01.04): column width is uniform within a roll, and philosophical texts favour narrower columns. Every other Johnson or GMAW number is UNCERTAIN and unused.
- **Expected blank after the title:** about 5-20 cm, roughly half to one kollema, more if a protective sheet was added (inference from PHerc. 1027, 1497, 1675). Low confidence.
- **PHerc. 1533 stichometry:** 2015 (Romano) or 2060 (Janko 2002, n. 19: "may not be complete"). UNCERTAIN.

## 2. Title ink in Herculaneum and comparable papyri (3rd c. BC to 1st c. AD)

Compiled by a research subagent. Seiler 2026 and Bonnerot 2020 were re-verified at source by this sibling (search results and publisher pages, 2026-09-26 ~18:50Z). Nothing below was taken from images.

### 2.1 Coloured titles: attestations
- **No coloured Herculaneum title is published.** Del Mastro, *Titoli e annotazioni bibliologiche nei papiri greci di Ercolano* (CErc Suppl. 5, 2014), catalogues 118 certain and 30 uncertain titles (initial, intermediate, final).
  - Its review (T. Dorandi, BMCR 2015.04.55, https://bmcr.brynmawr.edu/2015/2015.04.55/) lists graphic features, decorative elements and separation signs. It reports no coloured ink.
  - No Philodemus edition we found reports a subscriptio in a different colour.
  - Grade: LIKELY. The book itself was not opened.
- **Titles are written by the text scribe.** Of the PHerc. 172 final title, Angelotti et al. 2026 write: "The title was written by the same scribe who copied the text." FIRM.
- **Greek hexameter rolls: no coloured end-titles reported.** F. Schironi, *To Mega Biblion: Book-Ends, End-Titles and Coronides in Papyri with Hexametric Poetry* (ASP 48, 2010), describes end-titles as usually the work on one line and the book number on the next, "surrounded by some kind of decoration". The BMCR 2011.03.22 review mentions no coloured ink. LIKELY.
- **Red ink in Greek papyri is rare, and mostly documentary or magical.**
  - L. Blumell, "P.Mich. inv. 1568v …", *BASP* 46 (2009) 23-29: a red-ink document, "a very small corpus" of about 50 Roman-period examples, mostly 2nd-3rd c. AD. LIKELY.
  - Blanco Cesteros, "Written in Blood? …", in *Traces of Ink* (Brill 2021), doi:10.1163/9789004444805_004: red inks in the magical papyri. FIRM (topic).
- **Egyptian-language temple books use red rubrics as standard.** T. Christiansen et al., *PNAS* 117 (2020), doi:10.1073/pnas.2004534117 (Tebtunis, 1st-2nd c. AD).
  - "red ink was often used to highlight headings, instructions, keywords".
  - The red is ochre (Fe, with hematite by µXRD). Lead is present as a drier, and "minium and lead white were not detected."
  - FIRM. This is a different scribal tradition, not Greek literary rolls.
- **Roman literary texts on red book titles: the main reason the prior is not zero.**
  - Ovid, *Tristia* 1.1.7, "nec titulus minio … notetur".
  - Martial 3.2.11, "cocco rubeat superbus index".
  - Pliny, *NH* 33.122: minium is used "in voluminibus … scriptura".
  - FIRM as texts. Most probably they refer to the external tag (index/sillybos) of luxury copies, not to the end-title inside a working philosophical roll. That reading is UNCERTAIN.
- **Qumran parallel.** Cinnabar red occurs on 4 Dead Sea Scroll fragments only: Nir-El & Broshi, *Archaeometry* 38 (1996) 97-102, doi:10.1111/j.1475-4754.1996.tb00763.x. FIRM.

### 2.2 Analyses of Herculaneum inks
| Study | Material | Method | Finding | Source | Grade |
|---|---|---|---|---|---|
| Mocella et al. 2015 | a rolled Paris papyrus and a fragment | XPCT, ESRF | carbon-ink letters visible by phase contrast | *Nat. Commun.* 6:5895, doi:10.1038/ncomms6895 | FIRM |
| Brun et al. 2016 | 2 fragments, Institut de France "Objet 59" (roll unknown) | synchrotron XRF, XRD, XANES | high Pb in the black ink, co-located with P and Cl; intentional additive | *PNAS* 113:3751, doi:10.1073/pnas.1519958113 | FIRM |
| Tack et al. 2016 | same fragments | XRF, XANES, Monte Carlo | Pb 84±5 and 16±5 µg/cm²; closest to Pb(II) acetate; **minium excluded**; Cu not co-located | *Sci. Rep.* 6:20763, doi:10.1038/srep20763 | FIRM |
| Parker et al. 2019 | PHerc. Paris 2 fr. 96 | micro-CT + 3D CNN | carbon ink gives a subtle, learnable CT signal; trace Pb too low for contrast | *PLOS ONE* 14:e0215775, doi:10.1371/journal.pone.0215775 | FIRM |
| Bonnerot, Del Mastro, Hammerstaedt, Mocella, Rabin 2020 | 38 Naples scorze | portable XRF | Pb clear in 2 of 38 (PHerc. 254, 411, Philodemus); Cu in 3; Fe in 3; P in 5; **no coloured pigment reported** | *ZPE* 216 (2020) 50-52; https://www.fdr.uni-hamburg.de/record/1569 | FIRM |
| Bonnerot et al. (29th Int. Congr. Papyrology) | same campaign, full report | XRF | detailed version | http://siba-ese.unisalento.it/index.php/29th_ICP/article/view/25276 | LIKELY (not read) |
| Seiler, LaManna, McOsker, Kreimer, Daugherty, Dopke 2026 | model carbonised scroll, Pb-salt ink | handheld XRF, X-ray/neutron CT | Pb survives carbonisation, detectable by XRF, and makes letters bright in CT, down to 25 µg/cm² | *PLOS ONE*, Sept 2026, doi:10.1371/journal.pone.0353485 | FIRM |
| Angelotti et al. 2026 | Paris 4, 1667, 139 | BM18 phase-contrast CT, 2.4 µm, 78 keV | Paris 4 ink is bright 10-20 µm surface deposits after Paganin phase retrieval; the PHerc. 139 end title was recovered with the same pipeline as the body text | arXiv:2606.29085 | FIRM (own data; preprint) |

- No cinnabar, minium, ochre, Egyptian blue, malachite or gold has been reported on any Herculaneum papyrus. This is an absence of evidence, and titles were not specifically sampled. LIKELY.

### 2.3 Separation from codex practice
- Coloured incipits and explicits, rubrication, chrysography and purple codices belong to late-antique and Byzantine **codices**, from about the 4th-6th c. AD onward: for example the red opening lines of the Codex Alexandrinus (5th c.) and the 6th-c. purple codices. LIKELY (secondary).
- Schironi 2010 notes that the coronis becomes ornamental only in the codex era. LIKELY.
- Neither these codices nor Egyptian temple rubrics are evidence for a 1st-c. BC Greek philosophical roll from Italy.
- The owner's inputs recorded in DECL-P4-6-A1/A2 ("titles … in a different color ink virtually every time"; gold, blue and green) describe that later codex practice, not Herculaneum rolls.

### 2.4 Honest priors for the Paris 4 end title
UNCERTAIN (our judgement, from 2.1-2.2):
- **Title in a visibly coloured ink (red, gold, blue or green): about 2%**, range 1-5%. This is non-zero only because of the Roman *minium titulus* texts and the Qumran cinnabar.
- **Title ink physically different from the body ink** (any cause: another pigment or additive, a diluted ink, a different batch): **about 3-5%**.
- **Title in a dense high-Z ink that stands out from the body in absorption CT: about 2-4%.**
  - If the whole roll's black ink were leaded, the title would share it. Then it would be dense but not distinctive, and in that case the known-text control would light up too. The DECL-P4-6 control, which checks the known text itself, tests this.
  - Angelotti et al. 2026 describe Paris 4 ink as phase-contrast-visible deposits and do not report dense metallic ink.
- **Conditioning on the organizers' "no detectable ink in the expected region":**
  - A dense or mineral title in a region they inspected would appear *brighter*, not invisible.
  - The statement therefore shifts weight toward "wrong place / surface missing / faint ink" rather than toward "coloured mineral ink".
- **Consequence for DECL-P4-6/-10:** the dense-pigment detectors are worth running only as cheap screens. Each must carry the known-text control. Their positive predictive value is low.

## 5. Recommendations (ranked)

1. **Window A: w010-027 c10-c14, all rows** (the canvas strip about 20-30 cm from its outer end; about w019-w022). This is where 91% of Herculaneum end titles would be: beside the last column, 2.5-10 cm on (1.1). The unexplained c11-c13 r0-r1 block lies here. Confidence that the title lies in window A: **~0.45**.
   - **Material, rows r0-r1 (z 147-165 mm):** only 2.4 um (E2 raw CT, 20260411134726; M1 predictions).
   - **Material, rows r2-r5:** also 1.129 um (E1; P4-D M2a).
   - **Channel:** a thin surface-slab (±10-15 um) **maximum or p90** projection of the Paganin 2.4 um volume. This targets the 10-20 um bright deposits that ink forms in this scan (Angelotti et al. 2026). It is not the ±53 um mean, which dilutes a 15 um layer about 7x. It is the DECL-P4-6 channel, so it also covers dense inks.
   - It needs a declaration naming window A before any number is computed. The known-text control is c7-c9 of the same strip: same material, same rows.
   - **Scale:** 1 x 1 cm windows at native resolution. For 2-6 mm letters that gives at least 100 px per letter height.
   - The current 2 x 2 cm tiles at 53.4 px/mm give 107-320 px per letter. That is adequate in pixels, but a whole title (3-6 lines, 3-6 cm wide) spans 2-4 tiles. A 3 x 3 cm or 4 x 4 cm display centred on c11-c13 would keep the block intact for readers.
2. **Window B: c15-c19 (about w013-w018).** This is where a second or calligraphic end title would stand (PHerc. 1497, 1675: 11.5-19 cm further on) and where a title "in a subsequent column that can be otherwise blank" could fall. Confidence: **~0.20**. Same channel.
3. **Before any read: numeric column profile, edge check and organizer-segment mapping** (numbers only, a builder task).
   - Per canvas column of c5-c19, at 1 mm bins, the z-summed prediction and thin-slab-max values. This locates the intercolumns and the extent of the c11-c13 block to ±1 mm.
   - Per row, the mesh-valid fraction near r0 (z > 160 mm). This tests "top rows physically missing".
   - Validation: the pitch must match on the known-text columns (c0-c9, and w028-037).
   - Map the organizers' 2024-25 title-search segments onto the w010-027 canvas by mesh distance (7.3). This tells us whether "no detectable ink" refers to window A.
4. **Top edge above r0**, on the same columns. The organizers write "top rows are physically missing". If the sheet continues above the official mesh edge, extend the trace (tracer sibling) by 1-2 cm in z. Confidence that the title is (partly) there: **~0.10**.
5. **Core, w000-w009 (DECL-P4-7): ~0.05.** It is anomalous for an end title to lie 20 cm or more past the text, but the core is kept as the low-priority fallback.
6. **Remaining ~0.20:** elsewhere or not preserved. For example the title may lie in a part lost from the roll, as the organizers suspect for PHerc. 1667.

## 6. Decision advice (for the orchestrator)

| Question | Recommendation | Reasons | Confidence |
|---|---|---|---|
| Which windings, and where in them? | w010-027 canvas c10-c14 (about w019-w022) first, then c15-c19 (about w013-w018) | Last full text column c7-c9; blank c10; blank c14-c19 (4.2). 91% of titles stand beside the last column at 2.5-10 cm (1.1) | 0.45 / 0.20 |
| Title letter height vs text | Text letters are about 3 mm (Mocella 2015, FIRM). Titles about 3-5 mm, or up to ~6 mm if calligraphic. **Widen the readers' size prior from 2-4 mm to 2-6 mm** | Schironi (same or slightly larger); "modulo ampio" for calligraphic titles (1.2, 1.5). No mm data published for titles (GAP) | medium (0.6) for the ratio; low for the mm values |
| Number of lines | 2-4 lines expected (author; title; book number; optional count), centred, possibly with dashes above and below. Block ≈ 3-6 cm wide, 1.5-4 cm tall | 1.1-1.2; organizers 2024 and 2025 | 0.7 |
| Initial title? | Not a target for the inner strips. It would be at the outer start, which is lost or far away | 1.3 | 0.9 |
| Prior for non-carbon ink | Coloured ≈ 2%; physically different ≈ 3-5%; dense and CT-distinct ≈ 2-4%. Run the pigment detectors only as cheap screens with the known-text control | 2.4 | 0.8 (that it is low) |
| Best display scale | Native 2.4 um (or 1.129 um) thin-slab-max. Windows 3 x 3 or 4 x 4 cm centred on c11-c13 so that a whole title block is in one view; keep 1 cm context tiles for letter-level reads | Title block 3-6 cm; letters 2-6 mm; ink deposits 10-20 um thick | 0.6 |
| Inward of w010? | Low (~0.05). Do P4-G/core work after windows A/B | 4.3 H4; 12+ cm of blank traced sheet before w010 | 0.8 |
| Outside the 1.129 um z-range? | **Yes, partly:** rows r0-r1 (z 147-165 mm) of window A are outside z 67-135 mm. Use 2.4 um material there | 4.1 measured z per row | 0.95 (geometry) |
| Blind-reader integrity | No expected word, name or letter sequence may enter any brief, key sheet or display. Section 7's EXPECTED-TEXT subsection is for the orchestrator only | owner guardrail; I1/I13 | mandatory |

## 7. PHerc. Paris 4 itself: provenance, published text, hand (sub-worker (c))

### 7.1 Provenance and physical history
- **The 1802 gift.** Six rolls were given to Bonaparte in 1802 and are kept at the Institut de France.
  - Delattre 2013 (FIRM): Ferdinand IV offered them on the promise that they would be unrolled and published. They were Portici "papiri interi" nos. 148, 171, 184, 185, 205 and 10091. They are catalogued as "Objet 59". The two intact rolls were named PHerc. Paris. 3 and 4 in 2009.
    - D. Delattre, "Enquête sur les PHerc. Paris 5 et 6", *CRAI* 157-2 (2013) 531-545, doi:10.3406/crai.2013.95214.
  - Mocella et al. 2015 (FIRM): Paris 4 is "an (almost) entire rolled-up scroll".
- **Fate of the six rolls.**
  - 1816: one roll destroyed (Hayter and Tyrwhitt).
  - 1877: an attempt at the Louvre; a quarter survives.
  - 1986-87: two rolls opened in Naples by the Oslo method. They are Paris 1 (Hellenistic dynastic history) and Paris 2 (Philodemus, *On Slander*).
  - 2002: returned to Paris.
  - Sources:
    - Delattre interview, Fondation Napoléon, 2010, https://www.napoleon.org/magazine/interviews/d-delattre-les-rouleaux-dherculanum-donnes-au-consul-bonaparte-2010/ (LIKELY);
    - Mocella et al. 2015 (FIRM);
    - Parsons et al. 2023, arXiv:2304.02084 (FIRM).
- **Size.** Mocella et al. 2015 give "~16 cm length" (FIRM). Our reading that this is the axial height is UNCERTAIN. **"16.75 cm" is not verified anywhere; do not use it.**
- **Shape.** The roll is crushed and its umbilicus is not straight. Organizer FAQ; Substack 2024-11-27. FIRM (organizer).
- **Scans (FIRM):**
  - 2009 Institut de France micro-CT, 23.94 µm;
  - 2013 ESRF ID17 phase contrast, 70 keV ("did not produce the results hoped for": Fowler 2024, p. 100 n. 16);
  - 2019 Diamond I12, 7.91 µm, 54 keV;
  - March 2026 ESRF BM18: 45.5 µm overview, 2.4 µm at 78 and 137 keV, and 1.129 µm at 78 keV.
  - Sources: Parsons et al. 2023; Mocella et al. 2015; https://scrollprize.org/data_browser/PHercParis4.
  - **No scan brackets a K-edge.** 78 keV is below the Au, Hg and Pb K-edges. 137 keV is a small region near the axis. The DECL-P4-6-A1/A2 K-edge idea therefore has no scan pair on the w010-027 strip, unless the 137 keV region of interest covers it. This is an inference; p4-highz's inventory decides.

### 7.2 Published text
- **ZPE paper.** Nicolardi, Parsons, Delattre, Del Mastro, Fowler, Janko, Reinhardt, Parker, Chapman and Seales, "Revealing text from a still-rolled Herculaneum papyrus scroll (PHerc.Paris. 4)", *ZPE* 229 (2024) 1-13. The bibliography is FIRM; the content was not accessible.
- **CErc paper.** Nicolardi, Delattre, Del Mastro, Fowler and Janko, "The final columns of PHerc.Paris. 4 revealed through virtual unwrapping", *CErc* 54 (2024) 9-27. The CISPE abstract (FIRM) says: "portions of sixteen columns from the final part of the roll … an Epicurean philosophical treatise discussing perceptions and pleasure, with frequent references to food and music".
- **Grand Prize page** (https://scrollprize.org/grandprize, Feb 2024): 15 columns reviewed, numbered from the end (col. −1, −2, …), and about 5% of the scroll read. It says: "Since this is the end of a scroll, this phrasing may suggest that more is coming in subsequent books". FIRM (organizer).
- **Fowler 2024**, "The Herculaneum Papyri", *Manuscript and Text Cultures* 3.1, 84-105, doi:10.56004/v3.1rlf, p. 102. FIRM:
  - "as this is the end of the scroll, it is possible that topics are being outlined for the succeeding scroll";
  - it gives no author certainty.
- **2026.** "the team managed to unwrap approximately 140 columns of text from PHerc. Paris 4 (Scroll 1)". Vesuvius Challenge, "A new $1M Grand Prize for 2027", Substack, 2026-07-15, sha256 a4a2b94ac83591b6... **Verified by this sibling.** FIRM (organizer).
- **Not accessible (GAPs):** column width, intercolumn, lines per column, letter height of Paris 4, the scribe and hand, the date, and *how* the end of the text was established. ZPE 229 and CErc 54 are needed; **the owner could obtain these PDFs**, which is the single highest-value literature action left.

### 7.3 The organizers' title search history
- 2024-06-05: the title prize post; segments are shown only in a figure (3.2). FIRM.
- **2025-01-23:** "Elian Rafael Dal Prá … and Sean Johnson … manually segmented and uploaded a large region in the area of Scroll 1 where we expect there might be a scroll title hiding. Though we still haven't been able to identify a title, it is helpful to continue exploring this region!" Vesuvius Challenge, "Vesuvius Challenge Progress Prizes", Substack, 2025-01-23, https://scrollprize.substack.com/p/vesuvius-challenge-progress-prizes (sha256 9a4b71c2cefdf973...). **Verified by this sibling.** FIRM.
  - The region's segment ID and location are not given in text.
  - It was segmented on the 2019 7.91 µm data (pre-2026). Mapping it to our w-numbering needs the mesh; that is a builder task (see 5.3).
- 2025-02-27: "we've yet to locate a title in any of our scans". FIRM (sub-worker (c); not re-verified).
- 2026: the prize page and data browser say "The title region shows no detectable ink (possibly a different ink; the top rows are physically missing)". FIRM.
- **Implication (UNCERTAIN):**
  - The organizers' "expected title region" is a specific manually segmented area, known since January 2025.
  - If it corresponds to our window A (c10-c14), the "no detectable ink" statement applies there. That would raise the weight on the top edge (5.4), on thin-slab channels the official 2D models do not use (5.1), and on window B.
  - **Action:** a builder finds whether any official segment ID from 2024-25 (for example the 2024-06-04 IDs in logs/p4/recon.md, or a 2025 upload) maps onto w010-027 c9-c19. The check uses mesh distances only, as in p4-excl.

### EXPECTED-TEXT (never to readers)
QUARANTINED. Nothing in this subsection may enter a reader brief, key sheet, task text, display, N0 selection or candidate ranking. It exists only so the orchestrator understands the stakes. Every character the project claims must rest on imaging evidence alone (I1, I13).
- **Author:** Philodemus is probable but unproven.
  - Janko on the Grand Prize page: "It seems very likely".
  - Fowler 2024, p. 102: "could be Philodemus, but there is not enough text to be sure yet".
  - The data browser says "attributed to Philodemus".
  - Grade: LIKELY.
- **Work:** a book of Philodemus's *On Music* was suggested by Janko on the Grand Prize page ("Quite possibly"). Grade: UNCERTAIN.
- **Book number:** the closing words point forward to a following book (Grand Prize page; Fowler 2024), so the end title may carry a book number.
- **Deliberately omitted:** Greek word forms. They add nothing to any imaging decision and would raise priming risk.

Integrity: no issues (v4).
