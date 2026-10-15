<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="tifxyz-dist: Progress Prize package: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# tifxyz-dist: Progress Prize package

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pp-tifxyz-dist` · geometry, reading calibration, tools and records · 2026-09-27..2026-09-27 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0172.

## Question

Publish a tool for exact point-to-surface distances and certified mesh-to-mesh distances as a public tool for the 2026-09-30 Progress Prize round (DECL-PP-1). Its use is to prove the clearance between prediction regions and training segments.

## Method

Point-to-triangle distances are exact, with no densification. Mesh-to-mesh distance is a certified [lower, upper] interval with a witness point. Accuracy was checked against an independent kernel and against brute force. The demo measures pairwise clearance between public PHerc0172 manual and auto-grown segments (7.91 um volume). The package was scrubbed before publication.

## What ran on this branch

2026-09-27:
- 25/25 tests pass.
- Kernel vs an independent implementation: max difference 2.1e-14.
- 100,000 on-surface points on a public mesh: max error 2.7e-12 vox.
- Demo frozen at 243 of 396 segment pairs (44.6 min of compute).
- Published to a public GitHub repository on top of the owner's initial commit.

## Outcome

Published. At a 1-vox margin the demo classifies 228 pairs PASS, 14 FAIL and 1 INCONCLUSIVE. PUBLISHED.json records where the submission sheet's wording disagreed with the published numbers, for example 1.6e-11 vs 2.7e-12 vox.

| key number | meaning | file on this branch |
|---|---|---|
| 25/25 | tests passing in the published package | `logs/sib/pp-tifxyz-dist/PUBLISHED.json` |
| 0.0 | max difference from brute force over 4000 queries (vox) | `logs/sib/pp-tifxyz-dist/accuracy.json` |
| 228 / 14 / 1 | PASS / FAIL / INCONCLUSIVE segment pairs at a 1-vox margin | `tools/sib/pp-tifxyz-dist/pkg/results/RESULTS.md` |
| 243 of 396 | manual x auto-grown pairs frozen in the demo results | `logs/sib/pp-tifxyz-dist/PUBLISHED.json` |

## Where the records are

- `logs/sib/pp-tifxyz-dist/PUBLISHED.json`
- `logs/sib/pp-tifxyz-dist/accuracy.json`
- `logs/sib/pp-tifxyz-dist/scrub.json`
- `logs/sib/pp-tifxyz-dist/STATUS.md`
- `tools/sib/pp-tifxyz-dist/pkg/`
- `tools/sib/pp-tifxyz-dist/pkg/results/RESULTS.md`

## Lesson

Vertex-only distance checks can overstate clearance at edge contacts (5.1 vs 1.0 vox), so the tool certifies bounds instead.

## Related

- sib-pp-flatcheck
- sib-pp-handcheck
- DECL-PP-1
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
cd tools/sib/pp-tifxyz-dist/pkg && pip install -e . && pytest -q
bash demo/quickstart.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
