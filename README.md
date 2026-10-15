<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Iteration-5 tile worker S1 (screen B): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Iteration-5 tile worker S1 (screen B)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s1` · ink-model training and checkpoint screening · 2026-09-26..2026-09-27 · status **STOPPED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This is a worker for the ckpt-screen-b P4-O run. Its job was to compute an assigned share of PHerc.1667-iteration-5 tiles on the PHercParis4 surface volume with the parent's builder, unchanged.

## Method

Ran tools/sib/ckpt-screen-b/p4o_tiles.py and infer_1667.py byte-identical to the parent: fp32, card geometry, sha256-verified weights. Each finished tile's PNG and JSON was pushed for the parent to merge with hash checks. Each parent fix was adopted verbatim (the log crash fix b87d9dd, bounded reads 4741d69 and the banded norm_mean 98cd075), and work resumed from 15-min in-tile checkpoints.

## What ran on this branch

Ran from about 2026-09-26 21Z to 2026-09-27 07:01Z on a 4-vCPU container. One tile was finished and pushed. A second tile ran through several relaunches and a container restart that cost about 4 h of wall time. The worker found and reported the builder's crash after each finished tile, and worked around it without code changes by re-running the idempotent command.

## Outcome

This branch holds 1 iteration-5 tile. It was merged into the parent manifest and was part of the stage batch that failed its known-text gate (0/3, P4-O-STAGE-O2S1-RESULT). The stop rule let the second tile (58 % done) finish, but the parent's final status records that further S1 tiles never landed. No other assigned tile was started.

| key number | meaning | file on this branch |
|---|---|---|
| 1 | iteration-5 tiles produced on this branch | `logs/sib/ckpt-screen-b/p4o/S1_NOTES.md` |
| 0/3 | known-text gate tiles passing in the stage read that included this worker's tile (gate FAIL) | `logs/sib/ckpt-screen-b/p4o/S1_NOTES.md` |
| 2007 of 3452 | windows checkpointed on the second tile when the stop rule arrived | `logs/sib/ckpt-screen-b/p4o/S1_NOTES.md` |
| ~4 h | wall time lost to a container restart | `logs/sib/ckpt-screen-b/p4o/S1_NOTES.md` |

## Where the records are

- `logs/sib/ckpt-screen-b/p4o/S1_NOTES.md`
- `logs/sib/ckpt-screen-b/p4o/S1_RESUME.md`
- `logs/sib/ckpt-screen-b/p4o/S1_progress.jsonl`
- `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/`

## Lesson

Re-running an idempotent builder after a post-tile crash was safe only because every output was written before the crash and finished tiles are skipped.

## Related

- sib-ckpt-screen-b
- sib-ckpt-screen-b-s2
- sib-ckpt-screen-b-s3
- DECL-P4-14
- DECL-P4-14-A3
- DECL-P4-14-A4
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
git checkout 98cd075 -- tools/sib/ckpt-screen-b/
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "R,C" >> /work/p4o/worker.log 2>&1 < /dev/null &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
