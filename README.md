<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Iteration-5 tile worker S2 (screen B): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Iteration-5 tile worker S2 (screen B)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s2` · ink-model training and checkpoint screening · 2026-09-26..2026-09-27 · status **STOPPED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This is a worker for the ckpt-screen-b P4-O run. Its job was to compute an assigned share of PHerc.1667-iteration-5 tiles on the PHercParis4 surface volume with the parent's builder, unchanged.

## Method

Ran the parent's p4o_tiles.py and infer_1667.py unchanged (fp32, card geometry, weights checked by sha256 against the catalogue) and pushed tiles for the parent to merge. Builder defects were reported rather than patched: a memory overrun from two full-size copies in the logged norm_mean statistic, and a crash after each finished tile. The worker relied on a 16 GiB swapfile and an external re-run driver until the parent's fixes, which it then checked out verbatim.

## What ran on this branch

Ran from about 2026-09-26 21Z to 2026-09-27 08:58Z on a 13.36 GiB, 4-vCPU container. The first attempt was OOM-killed by the memory cgroup. Two tiles were completed. A container stall and restart cost about 4 h of wall time, but no computed windows, because the in-tile checkpoint survived.

## Outcome

This branch holds 2 iteration-5 tiles. The first was in the stage batch that failed its known-text gate (P4-O-STAGE-O2S1-RESULT). The second was more than half done at the ruling, so it was finished under the stop rule and merged into the parent's final 13-tile manifest. After that the worker stopped.

| key number | meaning | file on this branch |
|---|---|---|
| 2 | iteration-5 tiles produced on this branch | `logs/sib/ckpt-screen-b/p4o/S2_RESUME.md` |
| about 14 GB | transient peak from the norm_mean copies, above the 13.36 GiB container limit | `logs/sib/ckpt-screen-b/p4o/S2_NOTES.md` |
| 2293 of 4356 | windows done (0.53) on the final tile at the stop ruling, so it was allowed to finish | `logs/sib/ckpt-screen-b/p4o/S2_RESUME.md` |

## Where the records are

- `logs/sib/ckpt-screen-b/p4o/S2_NOTES.md`
- `logs/sib/ckpt-screen-b/p4o/S2_RESUME.md`
- `logs/sib/ckpt-screen-b/p4o/S2_progress.jsonl`
- `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/`

## Lesson

A statistic that is only logged can still crash a worker: a boolean-index copy of a 4.6 GB stack doubled peak memory.

## Related

- sib-ckpt-screen-b
- sib-ckpt-screen-b-s1
- sib-ckpt-screen-b-s3
- DECL-P4-14
- DECL-P4-14-A3
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
