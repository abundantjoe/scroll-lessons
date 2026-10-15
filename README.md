<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="CU sub-lane c: E2 and C2 scoring: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# CU sub-lane c: E2 and C2 scoring

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-cu-c` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **INCOMPLETE** · verdict **UNKNOWN**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

As sub-sibling c of p4-pig-cu, score the 2.4 um inner-strip material E2 and then the 2.4 um known-text control C2 with the frozen copper-pigment grain detector, E2 first (DECL-P4-12 priority).

## Method

All 6 sha256 values in params_freeze.json were verified (0 mismatches), then the parent's cu.py scorer ran unchanged. The E2 run resumed after the parent's 29 tiles already scored; the scorer skips finished tiles and is deterministic. Missing remote refs on the first launch were fixed by fetching them, with no code or parameter change.

## What ran on this branch

2026-09-26, 18:40Z to 19:29Z: E2 160/160 tiles and C2 101 tiles (261 in total), pushed in one commit.

## Outcome

E2 is complete. C2 stopped at 101 of 171 eligible tiles, and STATUS was never updated to done. The scores were not merged into the parent, and the CU family never computed thresholds or a verdict.

| key number | meaning | file on this branch |
|---|---|---|
| 160/160 | E2 tiles scored | `logs/sib/p4-pig-cu/scores/E2/scores_E2.jsonl` |
| 101 of 171 | C2 control tiles scored when the record ends | `logs/sib/p4-pig-cu/scores/C2/scores_C2.jsonl` |
| 0 | sha256 mismatches against the frozen parameters and code | `logs/sib/p4-pig-cu-c/STATUS.md` |

## Where the records are

- `logs/sib/p4-pig-cu-c/STATUS.md`
- `logs/sib/p4-pig-cu/scores/E2/`
- `logs/sib/p4-pig-cu/scores/C2/`

## Related

- sib-p4-pig-cu
- sib-p4-pig-cu-a
- sib-p4-pig-cu-b
- DECL-P4-10
- DECL-P4-12

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
pip install numpy scipy opencv-python-headless requests tifffile
CU_SCRATCH=/tmp/cu python3 tools/sib/p4-pig-cu/cu.py score C2 0-99 logs/sib/p4-pig-cu/scores/C2
CU_SCRATCH=/tmp/cu python3 tools/sib/p4-pig-cu/cu.py score E2 0-99 logs/sib/p4-pig-cu/scores/E2
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
