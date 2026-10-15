<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="FLAT-1/2: mesh flattening study: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# FLAT-1/2: mesh flattening study

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-flat1` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-27 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHercParis4, PHerc0800, PHerc1447.

## Question

Which flattening of an organizer tifxyz mesh keeps at least 93.1 % of quads within +-5 % of their 3-D size, as the reading plan's SG item 10 requires? The candidates were the official vc_flatten (ABF++), SLIM and ARAP.

## Method

Geometry only: mesh coordinates and volume metadata, with no CT voxel, render or image. The main test used five seeded 4 cm^2 PHerc0139 rectangles on the 9.362 um meshes, under a pre-declared adoption rule. Further tests repeated this at 2.399 um, used whole meshes, and used a hard set chosen by code: the 10 most curved or least isometric 4 cm^2 windows over all 38 bank meshes. Each method was scored by % of quads within +-5 %, flips and collapse. FLAT-2 measured the official flattening of two PHercParis4 segments and packaged the module. The branch's own commit adds the DECL-PP-1 flatcheck package under pp/flatcheck/.

## What ran on this branch

2026-09-25 to 2026-09-27, on a 4-core CPU container:
- FLAT-1: primary set, 2.399 um secondary set, whole meshes and hard set.
- FLAT-2: official flattening of two PHercParis4 segments (28.2 M and 29.4 M quads) plus seeded crops.
- A full-resolution flattening of about 318 cm^2 of one PHercParis4 segment (14.0 M quads).
- The flatcheck package: 22 tests pass and 1 is skipped without ABF++; all 23 pass with ABF++ available.

## Outcome

The pre-declared rule adopted vc_flatten (5/5 primary meshes, 98.59 to 99.67 %). The primary set cannot discriminate, though: the unflattened grid already scores 97.39 to 99.55 %. On the hard set no method reaches the bar (vc_flatten 0/10, SLIM 3/10, ARAP 4/10). ABF++ collapsed 3 times, while SLIM never flipped and scored at least as well as vc_flatten in 33/33 cases, so SLIM is recommended. The official PHercParis4 flattenings reach 84.30 % and 86.46 % of quads, and most read-eligible tiles (65 % and 64 %) fail the 93.1 % bar.

| key number | meaning | file on this branch |
|---|---|---|
| 0/10, 3/10, 4/10 | hard-set windows passing 93.1 % for vc_flatten, SLIM and ARAP | `logs/sib/flat1/flat1_report.json` |
| 97.39 to 99.55 % | unflattened grid baseline on the primary set, showing the primary set does not discriminate | `logs/sib/flat1/REPORT.md` |
| 3 | ABF++ (vc_flatten) collapses; SLIM had 0 flips | `logs/sib/flat1/flat1_report.json` |
| 84.30 % / 86.46 % | official whole-segment flattening of the two PHercParis4 segments, % of quads within +-5 % | `logs/sib/flat1/p4_flat.json` |
| 86.49 % vs 78.07 % | SLIM vs vc_flatten on the ~318 cm^2 full-resolution region | `logs/sib/flat1/p4win/metrics.json` |

## Where the records are

- `logs/sib/flat1/REPORT.md`
- `logs/sib/flat1/flat1_report.json`
- `logs/sib/flat1/flat1_summary.json`
- `logs/sib/flat1/flat1_hard_summary.json`
- `logs/sib/flat1/p4_flat.json`
- `logs/sib/flat1/p4win/REPORT.md`
- `logs/sib/flat1/p4win/metrics.json`
- `pp/flatcheck/`

## Lesson

A benchmark set must be able to fail: the gentle primary rectangles passed even unflattened, and only the hard set separated the methods.

## Related

- sib-pp-flatcheck
- DECL-PP-1
- DECL-P4-2
- DECL-OFFLOAD-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
tools/sib/flat1/build_abf_uv_dump.sh
/opt/hv/bin/python tools/sib/flat1/flat1_run.py select
/opt/hv/bin/python tools/sib/flat1/flat1_run.py all 9um
tools/sib/flat1/run_abf.sh <patch.tifxyz> <uv_out>
/opt/hv/bin/python tools/sib/flat1/flat1_hard.py
/opt/hv/bin/python tools/sib/flat1/flat1_whole.py
PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python -m pytest -q tests/sib_flat1_test_flatten.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
