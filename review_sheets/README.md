# Review sheets

One contact sheet per inferred read, produced by `scripts/read_chart.py` with no special handling. Each sheet has four
panels: CT mid slice | forward map as stored | reverse map as stored | forward − reverse per 0.5 cm² unit (flagged
units circled). Every panel carries a 1 cm bar and its µm/px. **[INDEX.md](INDEX.md)** lists every read with its
numbers, copied from the read's own stats. It is sorted by largest flagged cluster, then by margin.

| Folder | Contents |
|---|---|
| `eligible/` | 75 PNGs: 69 distinct read sheets, each linked from INDEX.md (35 BLANK, 22 NOT ESTABLISHED, 12 VOID, 0 PROMISING CANDIDATE), plus 6 unlinked byte-identical copies of the `+plain` sheets of six reads, saved under the short name `<scroll>__<surface>__<VERDICT>.png` (PHerc0358 `auto_grown_20260917230010114` and `auto_grown_20260918104037671`; PHerc0826 `auto_grown_20260918144212741`, `auto_grown_20260918152701336` and `auto_grown_20260918155811706`; PHerc1203 `team_20250923163331524`). INDEX.md lists 199 eligible reads. The other 130 are VOID at the R-CREST pre-check on the render (each has a LEDGER.md line "R-CREST pre-check ... no inference"), so no maps and no sheet exist; INDEX.md gives `-` in place of their numbers. |
| `ineligible/` | the G-OWN read: our own tracer on the w040 known-text control (PHerc0139, not eligible) |
| `qc/` | one patch that failed geometry QC and one that passed, as point overlays on the CT |
| `2um/` | the 2.4 µm route: a PHerc0846A rescan trace and the w028 1 cm² calibration against the team's map |
| `reference/` | the calibration images the notebook uses as visual standards (below) |

**Overlays.** The 150 overlay PNGs (1.4 GB) are derived views for the eye only. They were removed from the release
tree to keep clones small, and they remain in git history. Each overlay link in INDEX.md points to the file at commit
`71720ce`.

## Verdicts (frozen rule 5.5, `scripts/rule55.py`; RULES.md R-5.5)

| Verdict | Meaning |
|---|---|
| PROMISING CANDIDATE | ≥ 3 four-connected flagged 0.5 cm² units on either unit grid (mask-origin or (0, 0)). A unit is flagged when its forward mean ≥ 0.36 AND forward − reverse ≥ 0.08, and it is valid when ≥ 90 % on-sheet. **No read of an eligible scroll has ever produced one** (VERIFIED: verdict column of INDEX.md, 199 eligible rows, 0 PROMISING CANDIDATE). The w040 known-text control does (`reference/CONTROL_...`), but w040 is a training-set sheet of `ink_9um` ([`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`). On held-out known text from PHerc0841 the same frozen rule flagged 1 of 60 valid units and produced no candidate; the reader's verdicts were NOT ESTABLISHED, NOT ESTABLISHED and BLANK (MEASURED, [`RULES.md:3296`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296) `@7925b3a`). |
| BLANK | no flagged unit over ≥ 1.5 cm² of valid units, on both unit grids |
| NOT ESTABLISHED | anything between those two: some flagged units without a qualifying cluster, or too little valid area to call BLANK |
| VOID | the render failed the R-CREST on-sheet test (per-slice CT profile without a central crest ≥ 1.20). Rule 5.5 never decides these. For reads keyed `+nocrest` (R-CREST-POWER, veto lifted on purpose), rule 5.5 ran and its table is in the stats, while the ledger keeps the crest outcome in the verdict column. |
| UNREADABLE | < 0.5 cm² on-sheet, on-sheet CT std ≤ 5 (not tested with `--maps-only`), or no valid (≥ 90 % on-sheet) 0.5 cm² unit |

The 2–4 mm row check is computed and reported in the stats, but it is report-only in `rule55.py` and decides no
verdict.

**What BLANK and NOT ESTABLISHED do not mean.** They mean that this screen found no qualifying cluster. R-HELDOUT
shows that the screen returns the same on real text the model has not seen (1 of 60 units flagged on PHerc0841). A
BLANK or NOT ESTABLISHED sheet is therefore not evidence that the surface carries no ink (INFERENCE,
[`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a`).

## Reference images (`reference/`)

All are shown at matched physical scale. What each shows is quoted from RULES.md R-EYES / R-EYE.

| File | What it is |
|---|---|
| `REFERENCE_w040_known_text_4cm2_9.362um.png` | the w040 known-text sheet, raw CT render, 4 cm²: "a crosshatched papyrus fibre weave, recto and verso fibre bundles crossing at right angles". R-EYE records that this raw CT of known text shows no letters to the eye: "The raw CT render of known text shows NO letters." (VERIFIED, [`RULES.md:2732`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2732) `@40b81b9`) |
| `CONTROL_w040_rule55_PROMISING_CANDIDATE_cluster.png` | the frozen rule on the full w040 canvas: the four-unit PROMISING CANDIDATE (R-CTRL55). This is the visual standard a real candidate has to meet. It was set on a training-set sheet, so it is a best case; held-out text from PHerc0841 produced no candidate (above). |
| `PHerc0826_interior_40gen_FIBRE_WEAVE_std45.4.png` | an R-SMALL interior trace on PHerc0826 that shows the fibre weave, as the known-text sheet does (on-sheet CT std 45.4) |
| `PHerc0826_interior_40gen_featureless_std8.6.png` | an interior trace with an excellent depth crest (3.107) and a featureless face (on-sheet CT std 8.6). Crest and surface texture are independent. |
| `PHerc1203_team_20251005230830031_4cm2_9.362um.png` | the largest published PHerc1203 team surface, 4 cm² view: curving striations and laminae, not a crosshatched weave; on-sheet fraction 0.142 |
| `PHerc1447_z_dbg_gen_00701_4cm2_8.64um_CROSSCUT.png` | a PHerc1447 read: "laminar swirling strata ... no weave anywhere. It is a cross-section THROUGH the wrap stack, not a sheet." |

All images are derived from Vesuvius Challenge data and licensed CC BY-NC 4.0. See [../DATA_NOTICE.md](../DATA_NOTICE.md).
