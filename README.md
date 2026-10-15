<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="handcheck: Progress Prize package: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# handcheck: Progress Prize package

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pp-handcheck` · geometry, reading calibration, tools and records · 2026-09-27..2026-09-27 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHerc0800, PHerc1447, PHerc0009B.

## Question

Publish the geometry-based mirror-state predictor from the handed lane as a standalone public tool for the 2026-09-30 Progress Prize round (DECL-PP-1).

## Method

The package comes from tools/sib/handed/handcheck/. It includes synthetic validation, a reproduction of the official-mesh results from public data, and a CT frame check, and it was scrubbed before publication. The lane first paused: the permission check denied attaching the public repository and reading the handed branch. It waited for the owner's own approval in the session and did not act on a relayed notice.

## What ran on this branch

2026-09-27, after the owner's approval:
- Published to a public GitHub repository: the package commit plus a fix to the test extras.
- Clean install from GitHub: 94 tests passed, 1 skipped.
- Scrub ok: 0 findings, 10 reviewed exceptions.
- 224/224 mesh files match the handed lane's sha256 manifest.

## Outcome

Published. Results reproduced from public data:
- PHerc0139: 38/38 meshes HIGH confidence unmirrored; winding check 36/36.
- PHerc0800: 6/6 unmirrored.
- PHerc1447: 11 of 15 flagged (10 frame-unverified, 1 FLAG).
- PHerc0009B: 7 OK and 11 frame-unverified, a gate limitation for fragments; 18/18 read unmirrored without the gate.

PHerc0841 was left out of the public results because its original run excluded a held-out region whose points are not public.

| key number | meaning | file on this branch |
|---|---|---|
| 94 passed, 1 skipped | tests on a clean install from the published repository | `logs/sib/pp-handcheck/PUBLISHED.json` |
| 38/38 | PHerc0139 meshes HIGH unmirrored, reproduced from public data | `logs/sib/pp-handcheck/STATUS.md` |
| 11 of 15 | PHerc1447 meshes flagged under the packaged rule | `logs/sib/pp-handcheck/STATUS.md` |
| 224/224 | mesh files matching the handed lane's sha256 manifest | `logs/sib/pp-handcheck/STATUS.md` |

## Where the records are

- `logs/sib/pp-handcheck/PUBLISHED.json`
- `logs/sib/pp-handcheck/STATUS.md`
- `logs/sib/pp-handcheck/scrub.json`
- `logs/sib/pp-handcheck/ASK.md`

## Lesson

A relayed 'authorised' notice is not the owner's consent; the lane waited for the owner's own reply.

## Related

- sib-handed
- sib-pp-flatcheck
- sib-pp-tifxyz-dist
- DECL-PP-1
- DECL-PP-1-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
