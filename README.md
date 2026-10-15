<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 tile, worker 7: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 tile, worker 7

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w7` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to compute one assigned P4-O tile with the public PHerc.1667-iteration-5 checkpoint for a blind stage read (DECL-P4-14-A3).

## Method

The lane followed ckpt-screen-b's p4o WORKER.md (at 6aa0345, code 98cd075) exactly, with the tool and checkpoint sha256 verified. The only deviation was the output location: --out under logs/sib/o5w7/. Geometry: forward order, slices 23-84, 4 threads, with 15-min in-tile checkpoints.

## What ran on this branch

The tile started at 02:43:49Z on 2026-09-27 with 4356 windows planned. The first process died at a container restart after its last checkpoint at window 606. It was relaunched at 05:57Z and resumed from window 606. On orchestrator order it was killed at 07:10Z at 1748/4356 windows (40 %), and the in-tile checkpoint directory was deleted.

## Outcome

The lane was stopped under P4-O-STAGE-O2S1-RESULT: iteration-5 failed its known-text gate 0/3, and no iteration-5 target tile below 50 % done continued. No tile PNG or .png.json exists. Only the run logs and the worker log remain as the record.

| key number | meaning | file on this branch |
|---|---|---|
| 1748/4356 | windows done (40 %) when the run was killed | `logs/sib/o5w7/STATUS.md` |
| 606/4356 | checkpoint at which the first process died at a container restart; the relaunch resumed from it | `logs/sib/o5w7/STATUS.md` |
| 0 | tile outputs produced (no PNG or .png.json) | `logs/sib/o5w7/STATUS.md` |

## Where the records are

- `logs/sib/o5w7/STATUS.md`
- `logs/sib/o5w7/RESUME.md`
- `logs/sib/o5w7/worker.log`
- `logs/sib/o5w7/p4o/PHerc.1667-iteration-5/run_700.log`
- `logs/sib/o5w7/p4o/PHerc.1667-iteration-5/run_430.log`
- `logs/sib/o5w7/fetch_downloads.jsonl`

## Lesson

In-tile checkpoints saved the lane from a container restart, but a failed gate made the remaining 60 % of the tile not worth computing.

## Related

- sib-ckpt-screen-b
- sib-o5w5
- sib-o5w8
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w7/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
