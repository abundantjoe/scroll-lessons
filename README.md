<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 tile, worker 6: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 tile, worker 6

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w6` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker computed one assigned P4-O tile with the public PHerc.1667-iteration-5 checkpoint for the first blind stage read (DECL-P4-14-A3).

## Method

The lane used ckpt-screen-b's p4o WORKER.md (at 6aa0345) with code 98cd075 and the iteration-5 checkpoint, whose sha256 was verified before the run. Order: forward (slices 23-84). Outputs went to the WORKER.md layout under logs/sib/ckpt-screen-b/p4o/, with an identical copy under logs/sib/o5w6/ and a summary result.json. No image was opened.

## What ran on this branch

One run on 2026-09-27 from 02:42:48Z to 06:13:28Z: 4356 model windows, 4692 CT chunks read with 0 missing, 4 threads.

## Outcome

The tile completed (coverage 1.0, png re-hashed on disk and matching the record). It was one of the target tiles in stage batch o2s1, where the known-text gate FAILED 0/3 and every tile was rows N with 0 letters. The batch is therefore UNINFORMATIVE, not a null (P4-O-STAGE-O2S1-RESULT). Iteration-5 target work was stopped.

| key number | meaning | file on this branch |
|---|---|---|
| 12614.6 s (3.50 h) | tile runtime | `logs/sib/o5w6/STATUS.md` |
| ffa2497ea57d69ef175b5f3674890881d7f92657143be8f7c2bd3072396663e5 | png_sha256 of the pushed tile | `logs/sib/o5w6/result.json` |
| 4356 | model windows computed | `logs/sib/o5w6/result.json` |
| 0 | missing CT chunks | `logs/sib/o5w6/result.json` |

## Where the records are

- `logs/sib/o5w6/STATUS.md`
- `logs/sib/o5w6/RESUME.md`
- `logs/sib/o5w6/result.json`
- `logs/sib/o5w6/p4o/PHerc.1667-iteration-5/`
- `logs/sib/ckpt-screen-b/p4o/fleet/o5w6.json`
- `logs/sib/o5w6/downloads.jsonl`

## Lesson

Writing outputs in the integrator's exact layout as well as in the lane's own directory made the sha256 hand-off to the stage manifest direct.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w5
- sib-o5w8
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w6/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
