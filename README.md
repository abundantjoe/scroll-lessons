<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Tile builder: controls, raw CT, L3: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Tile builder: controls, raw CT, L3

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-tiles-b` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0343.

## Question

This was a builder lane. It produced read tiles for the Paris 4 known-text control segment: M1 at 2.4 um and M2b at 1.129 um, both official predictions. It also produced raw-CT E1 tiles of the title strip (DECL-P4-5, and the -A1 rebuild) and ran the L3 ink-depth calibration at 1.129 um (DECL-P4-12-A4).

## Method

The builder approach was the same as p4-tiles-a: anonymous fetch with sha256, mesh-derived grids, 1068 px tiles, and hash and structure checks without viewing. The E1 projection used level 3 and a 47-slice slab with a per-tile 1-99 % stretch; A1 recomputed the stretch excluding zero-CT pixels. The L3 calibration measured the fraction of voxels above T_hi 233 against depth offset on 24 control tiles x 40 chunks, with a declared STOP if the peak was below 3 robust SD.

## What ran on this branch

From 2026-09-26 00:27Z to 21:45Z (calibration utc) it built: the M1 control (198 tiles, 171 eligible); M2b (106 eligible); E1 (60 eligible tiles from 8.83 GB of level-3 chunks in 105.6 s); and the E1-A1 rebuild (33 of 60 PNGs changed). The L3 calibration used 826 of 960 chunks. On 2026-09-30 the branch held a First Letters step-2 S3 listing for PHerc0343, and nothing else.

## Outcome

All tile sets were delivered with hash checks. Prediction regions with no CT input were flagged, not treated as blank: 69 of 106 M2b tiles are >= 5 % zero. The L3 calibration verdict was STOP: peak excess z = 1.12 < 3, so there is no consistent ink depth on the known-text control at 1.129 um with T_hi 233, and no L3E tiles were produced. That is a statement about this channel only, not evidence of absence. 27 unit tests pass. The rule's measured false-pass rate on layer-free profiles is 0.17.

| key number | meaning | file on this branch |
|---|---|---|
| 171 of 198 | read-eligible M1 control tiles | `logs/sib/p4-tiles-b/manifest.json` |
| 415.04 | M1 control canvas px per mm (T = 8301 px) | `logs/sib/p4-tiles-b/grid.json` |
| 106 | read-eligible M2b tiles | `logs/sib/p4-tiles-b/m2b/manifest.json` |
| 60 | eligible raw-CT E1 tiles (A1 rebuild: 33 changed) | `logs/sib/p4-tiles-b/e1a1/manifest.json` |
| z = 1.12 | L3 calibration peak excess on the control; STOP (bar 3) | `logs/sib/p4-tiles-b/l3e/calib_1129.json` |

## Where the records are

- `logs/sib/p4-tiles-b/REPORT.md`
- `logs/sib/p4-tiles-b/manifest.json`
- `logs/sib/p4-tiles-b/grid.json`
- `logs/sib/p4-tiles-b/m2b/`
- `logs/sib/p4-tiles-b/e1/`
- `logs/sib/p4-tiles-b/e1a1/`
- `logs/sib/p4-tiles-b/l3e/`
- `tools/sib/p4-tiles-b/`
- `logs/sib/fl3-pherc0343/`

## Lesson

Measure a calibration rule's false-pass rate on layer-free profiles before trusting a pass; here it was 0.17.

## Related

- sib-p4-tiles-a
- sib-p4-highz
- sib-p4-pig-fe-e2
- DECL-P4-2
- DECL-P4-4
- DECL-P4-5
- DECL-P4-5-A1
- DECL-P4-12-A4

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-tiles-b/tile_w028_037.py <dl> logs/sib/p4-tiles-b 4
python3 tools/sib/p4-tiles-b/tile_m2b.py <dl> logs/sib/p4-tiles-b/m2b logs/sib/p4-tiles-b/m2b/uv_check.json 4
python3 tools/sib/p4-tiles-b/verify_uv_m2b.py <dl> logs/sib/p4-tiles-b/m2b/uv_check.json
python3 tools/sib/p4-tiles-b/e1a1_job.py <scratch> <repo>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
