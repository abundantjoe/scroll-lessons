<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Paris 4 inner windings recon + count: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Paris 4 inner windings recon + count

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-inner` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc1218.

## Question

Is there papyrus inward of the innermost segmented winding of PHerc. Paris 4, which has no official mesh? Does it hold more windings than the published labelling implies (DECL-P4-7 items 1-2, 1.129 um volume)?

## Method

Reconnaissance used only listings, JSON metadata, HEAD byte sizes and mesh vertex coordinates (no image). Sheet crossings inward of the innermost labelled winding were then counted along rays (64 rays x 24 z-levels). Two smoothing variants were used, with the threshold calibrated so that the labelled zone counts 10. Planted-sheet and null tests validated the count. Later geometry tasks: tile-direction answers, and official-prediction tile sets with a strip locator for further strips (DECL-P4-15(a), DECL-P4-25).

## What ran on this branch

2026-09-26 to 2026-09-30: recon of 81 segment directories; 1416 of 1536 rays used for the 1.129 um count; one further strip tile set (198-tile grid, 138 eligible) and three more strip sets (147/138/132 eligible). On 2026-09-30 the branch was reused as the First Letters worker fl3-pherc1218: its pipeline launched with 4 seeds, and the record ends at 'attempt 1 failed; restarting'.

## Outcome

Inconclusive. There is no evidence for more than 10 windings inward. The calibrated detector counts a median of 4 crossings (IQR 3-5), and only 1.5 % of rays (6.0 % in the other variant) exceed 10, against the 80 % required. Validation fails: planted-sheet error <= 1 winding in at most about 81 % of trials in any pitch regime, and counts are discontinuous across rays and z. Recon: no traced surface covers the innermost core, which is estimated at radius about 0.7-1.6 mm and area about 66-80 cm2. A reversed column-orientation assumption was caught before any inner count was read.

| key number | meaning | file on this branch |
|---|---|---|
| 4 (IQR 3-5) | median crossings inward of the innermost labelled winding, calibrated variant | `logs/sib/p4-inner/REPORT-P47.md` |
| 1.5 % | rays counting more than 10 (criterion needed >= 80 %) | `logs/sib/p4-inner/count_1129.json` |
| ~81 % | best share of planted-sheet trials with error <= 1 winding, in any pitch regime | `logs/sib/p4-inner/REPORT-P47.md` |
| 66-80 cm2 | estimated area of the unsegmented innermost windings | `logs/sib/p4-inner/RECON.md` |
| 138 of 198 | eligible tiles in the first further-strip tile set | `logs/sib/p4-inner/mout/manifest.json` |

## Where the records are

- `logs/sib/p4-inner/REPORT-P47.md`
- `logs/sib/p4-inner/RECON.md`
- `logs/sib/p4-inner/recon.json`
- `logs/sib/p4-inner/STATUS.md`
- `logs/sib/p4-inner/RESUME.md`
- `logs/sib/p4-inner/count_1129.json`
- `logs/sib/p4-inner/tile_winding_a.json`
- `logs/sib/p4-inner/tile_winding_m2a.json`
- `logs/sib/p4-inner/mout/`
[line withheld: prize-candidate detail under review]
- `logs/sib/fl3-pherc1218/STATUS.md`
- `tools/sib/p4-inner/`

## Lesson

Check grid orientation against geometry before counting: the assumed column order was reversed and was caught only because it was tested before any inner count was read.

## Related

- sib-p4-core
- DECL-P4-7
- DECL-P4-11
- DECL-P4-15
- DECL-P4-25
- fl3-pherc1218

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# scripts named in logs/sib/p4-inner/REPORT-P47.md; run from logs/sib/p4-inner/; argument-free, run order not recorded
cd logs/sib/p4-inner && python3 meshgrid.py && python3 count.py && python3 analyze.py && python3 synth.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
