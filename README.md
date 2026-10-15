<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Iteration-5 tile worker S3 (screen B): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Iteration-5 tile worker S3 (screen B)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s3` · ink-model training and checkpoint screening · 2026-09-26..2026-09-27 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This is a worker for the ckpt-screen-b P4-O run. Its job was to compute an assigned share of PHerc.1667-iteration-5 tiles on the PHercParis4 surface volume with the parent's builder, unchanged.

## Method

Ran the parent's builder unchanged, with an RSS and cgroup memory sampler, to diagnose repeated kills. A stage-by-stage diagnostic located the overrun in the norm_mean line of run_tile, not in read_stack as first thought. The worker proposed a row-banded integer-sum replacement and checked it exactly against the old expression on synthetic random arrays. It was not allowed to modify the builder itself.

## What ran on this branch

Ran from 2026-09-26 21:22Z to 2026-09-27 07:02Z. The first tile was killed three times by the 14.3 GB cgroup (OOM). After the parent's 98cd075 fix, peak memory fell and inference started, but the container was then reclaimed and restored without a checkpoint, losing about 4 h of CPU. The worker was stopped under the stop rule with its tile under 10 % done.

## Outcome

0 tiles were produced. The worker's main contribution is the memory diagnosis: the boolean-index and clip copies in the logged norm_mean pushed the peak past the container limit. The parent's banded norm_mean (98cd075) resolved this, with sampled VmHWM 6,818,616 kB against more than 13.2 GB before. The worker's first attribution to read_stack is recorded and corrected on the branch.

| key number | meaning | file on this branch |
|---|---|---|
| 0 | iteration-5 tiles produced on this branch | `logs/sib/ckpt-screen-b/p4o/S3_NOTES.md` |
| 3 | cgroup OOM kills of the first tile before the builder fix | `logs/sib/ckpt-screen-b/p4o/S3_NOTES.md` |
| 6,818,616 kB | VmHWM after the parent's norm_mean fix (was > 13.2 GB RSS and OOM before) | `logs/sib/ckpt-screen-b/p4o/S3_mem_trace_r1c14_98cd075.txt` |
| 3/3 | synthetic checks where the proposed banded norm_mean equals the old value exactly | `logs/sib/ckpt-screen-b/p4o/S3_NOTES.md` |

## Where the records are

- `logs/sib/ckpt-screen-b/p4o/S3_NOTES.md`
- `logs/sib/ckpt-screen-b/p4o/S3_RESUME.md`
- `logs/sib/ckpt-screen-b/p4o/S3_mem_trace_r1c14.txt`
- `logs/sib/ckpt-screen-b/p4o/S3_mem_trace_r1c14_batched.txt`
- `logs/sib/ckpt-screen-b/p4o/S3_mem_trace_r1c14_98cd075.txt`
- `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/`

## Lesson

Measure memory stage by stage before blaming a function: the first attribution here was wrong, and a sampler with a staged diagnostic found the real line.

## Related

- sib-ckpt-screen-b
- sib-ckpt-screen-b-s1
- sib-ckpt-screen-b-s2
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
