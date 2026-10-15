<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 pairs PHerc0139, part 2 (unstarted): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 pairs PHerc0139, part 2 (unstarted)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pairs0139b` · geometry, reading calibration, tools and records · 2026-09-26..2026-09-26 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Run part 2 of the PHerc0139 D2 pair build once pairs0139 hands over its segment list and pinned code.

## Method

Poll for logs/sib/pairs0139/HANDOVER.md on the pairs0139 branch, then run the unchanged pairs0139 pipeline on the segments handed over.

## What ran on this branch

2026-09-26: the environment was built and checked: dockerd with the official vc3d-deps image, villa 41701aa with 7 VC apps built, and pairs0139's 6 unit tests passing. The waiter then polled for 6 h and timed out at 11:30Z.

## Outcome

HANDOVER.md never appeared, so part 2 never started: no segment was rendered, no pair built and no shard written. The session recorded ASK.md and stopped.

| key number | meaning | file on this branch |
|---|---|---|
| 6 h | time spent waiting for the pairs0139 handover before the waiter timed out | `logs/sib/pairs0139b/ASK.md` |
| 0 | segments rendered or pairs built | `logs/sib/pairs0139b/ASK.md` |

## Where the records are

- `logs/sib/pairs0139b/ASK.md`
- `logs/sib/pairs0139b/runs.jsonl`
- `logs/sib/pairs0139b/lscpu_df.txt`

## Lesson

A dependent lane needs a deadline and a fallback, not just a waiter.

## Related

- sib-pairs0139
- sib-pairs0139c
- DECL-D2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/pairs0139b/env_setup.sh
bash tools/sib/pairs0139b/wait_handover.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
