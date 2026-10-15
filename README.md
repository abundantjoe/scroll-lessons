<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 tile, worker 4: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 tile, worker 4

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w4` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker computed one assigned P4-O tile with the public PHerc.1667-iteration-5 checkpoint so that it could enter a blind stage read under DECL-P4-14-A3.

## Method

The lane used ckpt-screen-b's p4o WORKER.md pipeline (code 98cd075, sha256-verified tools) and the checkpoint sha256-verified against the catalogue and WORKER.md. Geometry: 2.4 um level 0, slices 23-84, window 256, stride 128, clip(0,200)/255, forward order, 4 threads. Outputs were pushed in the WORKER.md layout rooted under logs/sib/o5w4/ and never opened.

## What ran on this branch

One run on 2026-09-27 from 02:43:04Z to 06:37:08Z: 3389 model windows. 3772 CT chunks were read and 851 were missing (zero-filled). The environment disclosed s3fs/fsspec as installed but unused.

## Outcome

The tile completed and its valid_fraction equals the manifest value. It was not one of the 10 tiles of stage batch o2s1, which failed its known-text gate 0/3 (P4-O-STAGE-O2S1-RESULT). Under that result, such a tile could be read only in a later batch under the same gate, and the record shows no later P4-O stage batch. The tile was therefore never read, and there is no verdict for it.

| key number | meaning | file on this branch |
|---|---|---|
| 3389 | model windows computed for the tile | `logs/sib/o5w4/STATUS.md` |
| 14014 s (3.89 h) | tile runtime | `logs/sib/o5w4/STATUS.md` |
| 2bcb73c2974991c471126d8d229c9cebdf20689150276490608ee6099dd26aa5 | png_sha256 of the pushed tile (re-verified) | `logs/sib/o5w4/p4o/fleet/o5w4.json` |
| 851 | missing CT chunks (of 3772 read), zero-filled as in the builder | `logs/sib/o5w4/STATUS.md` |
| 0.80497 | valid_fraction, equal to the manifest value | `logs/sib/o5w4/STATUS.md` |

## Where the records are

- `logs/sib/o5w4/STATUS.md`
- `logs/sib/o5w4/RESUME.md`
- `logs/sib/o5w4/p4o/fleet/o5w4.json`
- `logs/sib/o5w4/p4o/PHerc.1667-iteration-5/`

## Lesson

Tiles that finish after a stage batch is cut stay unread when the gate fails, so a fleet should check the gate before it spends compute on target tiles.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w1
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# p4o_tiles.py, infer_1667.py and fetch.py are on sib-ckpt-screen-b at code commit 98cd075; venv /opt/ckb per its p4o/WORKER.md section 3
git worktree add /work/ckb 98cd075 && cd /work/ckb
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w4/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
