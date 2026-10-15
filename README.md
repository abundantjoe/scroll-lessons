<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="flatcheck: Progress Prize package: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# flatcheck: Progress Prize package

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pp-flatcheck` · geometry, reading calibration, tools and records · 2026-09-27..2026-09-27 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Package the FLAT-1 flattening-quality checker as a standalone, MIT-licensed public tool for the 2026-09-30 Progress Prize round (DECL-PP-1).

## Method

A standalone package with a CLI and an API. It reads tifxyz meshes, scores the % of quads within +-5 %, detects fold-overs and collapse, and re-flattens with SLIM or ARAP. It ships with tests and a reproducible demo on three public PHerc0139 organizer meshes. Before publication it was scrubbed for secrets, private paths, governance coupling and title-search identifiers.

## What ran on this branch

2026-09-27:
- Package staged under tools/sib/pp-flatcheck/vc-flatcheck/ (28 files).
- 21/21 tests pass on the exact committed tree.
- Demo reproduced: 3 meshes in 1 m 42 s.
- Scrub: 0 hits in 5 categories.
- Published to a public GitHub repository as one commit on top of the owner's licence commit (recorded in PUBLISHED.json).

## Outcome

Published. In the demo, the distributed grid flattening of three PHerc0139 segments has 90.05 %, 92.94 % and 91.83 % of quads within +-5 %, all below the 93.1 % bar. SLIM and ARAP re-flattened crops reach 82.77 to 97.19 %. PUBLISHED.json lists where the submission sheet's wording differed from the published package.

| key number | meaning | file on this branch |
|---|---|---|
| 21/21 | tests passing on the committed tree | `logs/sib/pp-flatcheck/PUBLISHED.json` |
| 0 | scrub hits (secrets, paths, governance, title-search, personal) | `logs/sib/pp-flatcheck/scrub.json` |
| 90.05 / 92.94 / 91.83 % | whole-mesh grid flattening of the three demo segments, % of quads within +-5 % | `tools/sib/pp-flatcheck/vc-flatcheck/results/SUMMARY.md` |

## Where the records are

- `logs/sib/pp-flatcheck/PUBLISHED.json`
- `logs/sib/pp-flatcheck/scrub.json`
- `logs/sib/pp-flatcheck/STATUS.md`
- `tools/sib/pp-flatcheck/vc-flatcheck/`
- `tools/sib/pp-flatcheck/vc-flatcheck/results/SUMMARY.md`

## Lesson

Check the submission text against the published numbers before sending; the mismatches are recorded in PUBLISHED.json.

## Related

- sib-flat1
- sib-pp-handcheck
- sib-pp-tifxyz-dist
- DECL-PP-1
- DECL-PP-1-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
cd tools/sib/pp-flatcheck/vc-flatcheck && pip install -e . && pytest -q
bash scripts/reproduce.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
