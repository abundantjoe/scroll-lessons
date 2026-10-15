<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Paris 4 core count and mesh geometry: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Paris 4 core count and mesh geometry

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-core` · PARIS-4 investigations · 2026-09-26..2026-10-01 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Are there papyrus windings inward of the innermost labelled winding of PHerc. Paris 4 beyond the published numbering (DECL-P4-7, 2.4 um volume)? Follow-on tasks asked whether the official mesh geometry is sound enough for downstream channels: mesh audit, holes and edges, detached tags, and facing (neighbour-sheet) surfaces.

## Method

Numbers-only ray counting of sheet crossings inward of the innermost labelled winding on the 2.4 um volume (Gaussian FWHM 20 um smoothing, prominence threshold calibrated on the labelled zone), validated on 192 synthetic spiral cases. Geometry follow-ons: mesh audit (self-intersections, winding jumps, normal flips), DECL-P4-24 holes/edge checks with an extrapolation validation on known mesh, DECL-P4-15 P4-TAG detached-tag search validated with planted tabs, DECL-P4-26/-A1 facing-surface rules (naive, regularised, fallback) gated on controls, DECL-P4-26-A2 facing geometry in both directions across the full grid, and a raw-CT no-data recovery feasibility check. No image or CT pixel was viewed.

## What ran on this branch

2026-09-26 to 2026-10-01 on CPU containers: 3161 valid ray samples over 25 z-levels (2.4 um, level 0); mesh audit of 189 tiles; holes checks on 180 tiles; facing rules on 90 tiles and 36 control tiles; facing geometry on 189/189 tiles; no-data recovery feasibility over 46 tiles. No trace was run.

## Outcome

Count: median 5 peaks inward (IQR 4-6), only 1.8 % of rays above 10, so the DECL-P4-7 criterion is not met. Counter validation was NOT PASSED (63 % of synthetic cases within +-1 winding), so the exact number stays unresolved and there is no evidence for windings beyond the labelled numbering. P4-TAG is NOT TESTABLE because the published volume is SAM2-masked. Facing surfaces: naive rule 0/90 pass, regularised rule rejected (0/36 controls), fallback rule 18/36 controls; full-grid facing geometry done (outer coverage median 0.889, inner 0.860). Raw-CT recovery of no-data areas is not feasible (coverage correlation 1.000).

| key number | meaning | file on this branch |
|---|---|---|
| 5 (IQR 4-6) | median sheet-crossing peaks inward of the innermost labelled winding, 3161 ray samples | `logs/sib/p4-core/count.json` |
| 1.8 % | share of rays with more than 10 inner peaks (criterion needed >= 80 %) | `logs/sib/p4-core/STATUS.md` |
| 63 % | synthetic cases with per-z error within +-1 winding; validation NOT PASSED | `logs/sib/p4-core/synthetic_tests.json` |
| 0/90 | tiles passing the gate under the declared naive facing rule | `logs/sib/p4-core/facing/rules_naive_reg.json` |
| 18/36 | control tiles passing under the fallback facing rule | `logs/sib/p4-core/facing/fallback4.json` |
| 0.889 / 0.860 | median outer / inner facing coverage over 189 tiles | `logs/sib/p4-core/STATUS.md` |
| 17/24 | planted tabs detected in the P4-TAG detector validation | `logs/sib/p4-core/tag.json` |
| 1.000 | correlation of raw-CT coverage with official surface-volume coverage over 46 tiles (recovery not feasible) | `logs/sib/p4-core/nodata_recovery/summary.json` |

## Where the records are

- `logs/sib/p4-core/STATUS.md`
- `logs/sib/p4-core/RESUME.md`
- `logs/sib/p4-core/ASK.md`
- `logs/sib/p4-core/count.json`
- `logs/sib/p4-core/synthetic_tests.json`
- `logs/sib/p4-core/mesh_audit.json`
- `logs/sib/p4-core/holes.json`
- `logs/sib/p4-core/holes_extrap_check.json`
- `logs/sib/p4-core/tag.json`
- `logs/sib/p4-core/facing/`
- `logs/sib/p4-core/facing_all/summary.json`
- `logs/sib/p4-core/nodata_recovery/summary.json`
- `tools/sib/p4-core/`

## Lesson

A peak counter calibrated on labelled windings still over-counted them by about 20 % and failed synthetic validation, so a raw count could not settle the winding question.

## Related

- sib-p4-inner
- DECL-P4-7
- DECL-P4-15
- DECL-P4-24
- DECL-P4-24-A1
- DECL-P4-26
- DECL-P4-26-A1
- DECL-P4-26-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-core/holes.py <mesh_dir> <out_rows.jsonl> <tiles spec: title|ref|rest>
python3 tools/sib/p4-core/holes_agg.py <rows.jsonl> <out holes.json>
python3 tools/sib/p4-core/holes_extrap_check.py <mesh_dir> <out.json>
sh tools/sib/p4-core/chain_after_holes.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
