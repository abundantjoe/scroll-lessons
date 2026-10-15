<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Tile builder: title-strip predictions: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Tile builder: title-strip predictions

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-tiles-a` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This was a builder lane. It produced number-checked read tiles of the published ink predictions on the Paris 4 title-strip segment: M1 at 2.4 um (DECL-P4-2) and M2a at 1.129 um (DECL-P4-4). It also cut title-scale block windows (DECL-P4-17-A1) and ran the DECL-P4-19 line-structure test.

## Method

Official predictions, tifxyz meshes and volume metadata were fetched anonymously from the public bucket, with sha256 logged. Grid geometry came from the median mesh edge, giving px/mm. 2 x 2 cm tiles (1068 px) were cut under the eligibility rules, and PNG structure and hashes were checked without viewing. Scan coverage was checked from geometry only (DECL-P4-4-A1). The line test used 0.5 mm-binned profiles of the published prediction. The 4 x 4 cm block windows were given uuid4 file names, with the key held only in the manifest.

## What ran on this branch

This ran 2026-09-26 to 2026-09-27 02:23Z. M1: 189 tiles, 160 read-eligible (623.27 cm2). M2a: 126 tiles, 100 at least half mesh-valid, 60 eligible after the coverage rule (agreeing with p4-tiles-b's E1 grid). The P4-19 profiles took 12.9 s. 15 block windows were built.

## Outcome

All tiles were delivered and verified: 0 nonzero prediction pixels outside the mesh-valid mask, and every sha256 matched and was unique. The DECL-P4-19 test was INVALID as declared, so nothing was concluded. Its body-text control groups gave 0 detected lines because the threshold sat above their profile maximum (ratios 1.081, 1.065), even though both were strongly periodic (pitch 6.61 and 6.41 mm). All 15 block windows are labelled-adjacent, so none can become a candidate.

| key number | meaning | file on this branch |
|---|---|---|
| 417.131 | M1 canvas px per mm (tile T = 8343 px) | `logs/sib/p4-tiles-a/grid.json` |
| 160 of 189 | read-eligible M1 tiles | `logs/sib/p4-tiles-a/manifest.json` |
| 60 | M2a tiles eligible after the DECL-P4-4-A1 coverage rule (40 excluded) | `logs/sib/p4-tiles-a/m2a/coverage_A1_summary.json` |
| INVALID | DECL-P4-19 line-structure verdict (control groups had 0 detected lines) | `logs/sib/p4-tiles-a/p419_profile.json` |
| 15 | uuid-named block windows built, all labelled-adjacent | `logs/sib/p4-tiles-a/w1/manifest.json` |

## Where the records are

- `logs/sib/p4-tiles-a/REPORT.md`
- `logs/sib/p4-tiles-a/manifest.json`
- `logs/sib/p4-tiles-a/grid.json`
- `logs/sib/p4-tiles-a/tile_census.jsonl`
- `logs/sib/p4-tiles-a/m2a/`
- `logs/sib/p4-tiles-a/w1/`
- `logs/sib/p4-tiles-a/p419_profile.json`
- `tools/sib/p4-tiles-a/`

## Lesson

A peak-outlier line rule fails on dense body text, so run any detection threshold on the control before declaring it.

## Related

- sib-p4-tiles-b
- sib-p4-titulus
- sib-p4-struct
- DECL-P4-2
- DECL-P4-4
- DECL-P4-4-A1
- DECL-P4-17-A1
- DECL-P4-19

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-tiles-a/tile_m2a.py <scratch_dl2> logs/sib/p4-tiles-a/m2a
python3 tools/sib/p4-tiles-a/m2a_coverage.py <x.tif> <y.tif> <z.tif> <0/.zarray> logs/sib/p4-tiles-a/m2a <tiles_b_e1_manifest>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
