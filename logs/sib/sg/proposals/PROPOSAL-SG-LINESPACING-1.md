Provenance: Project HERCULES | owner the owner | [id removed]

# PROPOSAL-SG-LINESPACING-1 (ruling B9 follow-up, plus a measured B8 risk)

Proposal only; the orchestrator declares. Numbers only: no image was produced, viewed or described.

## 1. What was asked

Ruling B9 asked me to compute line-spacing statistics (baseline pitch / letter height) from the official PHerc0139 human labels, so that an alternative to the ">= 3 rows" default could be declared from measured data.

## 2. What the official labels contain (measured)

- **Source:** s3://vesuvius-challenge-open-data (anonymous), `PHerc0139/segments/<seg>/ink-labels/<volume>/20260918/inklabels.zarr`. Every download is sha256-logged in `logs/sib/sg/label_survey_0139.json` (`downloads`).
- **Sets:** 5 sets on the 9.362 um volume and 8 on the 2.399 um volume (pyramid level 2 = 9.596 um, the scale taken from each level's own OME metadata). PHerc0139 is not an eligible volume; the labels are known text, and nothing was trained.
- **Letter blobs:** each segment's labels hold only **4-25 letter-sized blobs** (connected components, 8-connectivity, value >= 128). The 9.362 um sets carry the same letters as the 2.399 um sets. In total there are **68 distinct letter blobs** with max side >= 1 mm across 8 segments. The rest are 0.01-0.02 mm specks left by downsampling.
- **Supervision masks** cover 1-3.5 % of each canvas.

**Consequence:** the labels are a sparse set of isolated letters, not continuous text. Row pitch, pitch CV and pitch/height need several labelled rows per region, so they **cannot be measured from these labels**.

Earlier outputs `label_spacing_0139_t20.json` / `_t30.json` fit rows to 2-13 blobs per tile. They are **INVALID as statistics** and are kept only as the logged record of that attempt.

**The method itself is validated.** `tools/sib/sg/label_spacing.py` is checked on synthetic text by `tests/sib_sg_label_spacing.py` (6 known-answer tests: pitch within 3 %, row angle within 1 deg, heights within 5-10 %, irregular rows detected, shard decoder round trip). It is ready for any dense known-text mask.

## 3. Letter size on known text (68 blobs; `label_survey_0139.json`, `letter_blobs_2p4um_level2`)

| measure | p5 | p25 | median | p75 | p95 | fraction in 2-4 mm |
|---|---|---|---|---|---|---|
| canvas height | 1.77 | 2.19 | 2.48 | 3.15 | 3.89 | 0.78 |
| canvas width | 1.54 | 2.27 | 2.73 | 3.30 | 4.56 | 0.75 |
| max side | 1.89 | 2.59 | 3.08 | 3.67 | 5.22 | 0.76 |
| min side | 1.54 | 2.09 | 2.31 | 2.62 | 3.26 | 0.76 |

**Risk for ruling B8:** on genuine known text, 75-78 % of the labelled letters fall in 2-4 mm, whichever box side is used. B8 requires >= 80 %, so it would fail this known text. With n = 68 the 95 % binomial interval is about +-10 points.

Caveats that cut both ways:
- human label blobs may be dilated or undilated relative to the ink;
- the text-row direction on these canvases is unknown, so "height" is not measured along the row normal;
- reader-drawn boxes (what SG 11 actually uses) may be tighter or looser than label blobs.

The median (2.5-3.1 mm) is comfortably inside 2-4 mm; it is the 80 % tail bar that is at the edge.

## 4. Proposals (for declaration or rejection)

- **P1 (B9):** keep the ruling's default (SG 11 needs >= 3 qualifying rows). No alternative can be justified from the official labels. A 2-row alternative, such as pitch/height within the known-text range, needs dense known-text line geometry. Candidate sources, in order of preference:
  1. a denser official human label set, if one exists;
  2. the organizers' official 2.4 um ink predictions on clean 0139 windows. These are model output, not human labels, and would need a declaration.
- **P2 (B8):** before any candidate exists, declare whether the >= 80 % height fraction stays as ruled. If it stays, record that it may reject genuine text (section 3). A validation that is measurable without lowering any bar: apply SG 11 mechanically to REF reads of sealed known-text bank windows (SG-FEAS style) and record the pass rate.
- **P3 (B7, information):** re-run under |NCC| (`copytest_null_abs.json`), the floor n_eff >= 30 still gives 0 false flags in all 10 cells at or above it. The highest chance value was 0.743 at n_eff 31 with 1000 patches, up from 0.691 with 100 patches. With 10^4-10^5 real label patches the chance maximum may approach 0.8 even above the floor. B7's pre-SG empirical-null check on the real patch set is the safeguard, and it must actually be run.

## 5. Line spacing on organizer predictions (ASK Q6 approved; ORGANIZER MODEL OUTPUT, CALIBRATION ONLY, never evidence)

**Source:** the official 2.4 um ink predictions (model 20260417190342, volume 20260102150214, voxel 2.399 um from metadata.json) of the **18 PHerc0139 segments that appear in no project record** (ASK Q7 default). Each prediction's shape is checked equal to its segment's 2.399 um surface-volume shape, and every sha256 is in `pred_spacing_0139.json`.

**Method:** downscale x4 (INTER_AREA, 9.596 um), binarise at 96, 128 and 160, then non-overlapping 20 and 30 mm tiles with ink >= 2 %, periodicity >= 0.3, and no peak on the lag edge. The tool is `label_spacing.measure_tile`, validated by 7 known-answer tests. A first run crashed on a negative-pitch refinement bug, which is fixed, tested and logged; all of its partial results were discarded.

Results (`pred_spacing_0139.json`, `pred_spacing_0139_summary.json`). Threshold 128 is shown; 96 and 160 agree within the spread.

| tile | periodic tiles (segments) | row pitch mm p5 / p25 / median / p75 / p95 | pitch CV median (p75) | fraction CV <= 0.20 | band mm median | pitch / band p5 / median / p95 | angle within 10 deg of horizontal |
|---|---|---|---|---|---|---|---|
| 20 mm | 59 (16) | 1.90 / 4.31 / 4.66 / 4.88 / 5.40 | 0.09 (0.45) | 0.65 | 3.08 | 1.19 / 1.46 / 2.13 | 0.92 |
| 30 mm | 35 (15) | 4.13 / 4.58 / 4.78 / 4.93 / 9.65 | 0.16 (0.48) | 0.58 | 3.35 | 1.19 / 1.45 / 1.79 | 1.00 |

- The connected-component heights (median about 0.8 mm) measure stroke fragments, not letters, because the predictions split letters. They are **not** a letter-height statistic.
- The 20 mm p5 pitch of about 1.9 mm, and the 30 mm p95 of about 9.7 mm, are half and double harmonics picked on weak tiles. The interquartile range is tight.

### Proposals

- **P4 (B9 two-row alternative; for declaration or rejection):** with exactly 2 qualifying rows, accept SG 11's row test only if the row pitch divided by the median letter height (reader boxes) lies within the known-text range. Measured here: about 1.2-2.1 by pitch/band.
  - Caveat: band height is the ink extent of a row, not the height of a reader-drawn box. The range must be re-measured on REF reads (reader boxes) of sealed known-text bank windows before it is declared. Until then the ">= 3 rows" default stands, as ruled.
- **P5 (measured risk, SG 11 pitch CV):** on known text, only 58-68 % of periodic tiles have pitch CV <= 0.20. Part of this is row-finder error on faint prediction rows, but the DECL-SG 11 bar may reject genuine text. The same REF-read calibration that was adopted for B8 should record the SG 11 pass rate, CV included, before any candidate exists.
- **Angles:** 91-100 % of tiles lie within 10 deg of the render horizontal, so the baseline-angle bar looks safe for genuine text on organizer flattenings.
