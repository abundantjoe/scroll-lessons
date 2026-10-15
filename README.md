<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="CU sub-lane b: C1 control scoring: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# CU sub-lane b: C1 control scoring

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-cu-b` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **COMPLETED** · verdict **UNKNOWN**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

As sub-sibling b of p4-pig-cu, score all eligible tiles of the 1.129 um known-text control strip (C1) with the frozen copper-pigment grain detector.

## Method

Verify the sha256 values of the frozen parameters and code (params_freeze.json), then run the parent's cu.py scorer unchanged on C1. Numbers only; no image viewed.

## What ran on this branch

2026-09-26: one commit at 19:11Z with C1 scores for 64 tiles (frozen code, sha256 verified). The branch is a single root commit carrying the whole repository tree and has no STATUS file of its own.

## Outcome

64 control tiles were scored, the full eligible 1.129 um control set. The scores were not merged into the parent, and the CU family never computed thresholds or a verdict, so the experiment's outcome is unknown.

| key number | meaning | file on this branch |
|---|---|---|
| 64 | C1 control tiles scored | `logs/sib/p4-pig-cu/scores/C1/scores_C1.jsonl` |

## Where the records are

- `logs/sib/p4-pig-cu/scores/C1/`
- `logs/sib/p4-pig-cu/SUBSIBS.md`

## Related

- sib-p4-pig-cu
- sib-p4-pig-cu-a
- sib-p4-pig-cu-c
- DECL-P4-10

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
pip install numpy scipy opencv-python-headless requests tifffile
CU_SCRATCH=/tmp/cu python3 tools/sib/p4-pig-cu/cu.py score C1 0-99 logs/sib/p4-pig-cu/scores/C1
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
