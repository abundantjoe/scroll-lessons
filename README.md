<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 tile, worker 5: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 tile, worker 5

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w5` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker computed one assigned P4-O tile with the public PHerc.1667-iteration-5 checkpoint for the first blind stage read (DECL-P4-14-A3).

## Method

The lane used ckpt-screen-b's p4o WORKER.md (at 6aa0345) with code commit 98cd075, all tool sha256 verified, and checked the checkpoint sha256 both through the catalogue and independently. Order: forward only (slices 23-84). The layout check gave max |logit diff| 4.17e-7. Outputs were pushed in the WORKER.md layout re-rooted under logs/sib/o5w5/, with progress checkpoints every 30 min, and never opened.

## What ran on this branch

One run on 2026-09-27 from 02:42:45Z to 05:40:37Z with a single process start: 4356 model windows at 4 threads on a 4-vCPU CPU container.

## Outcome

The tile completed and was one of the target tiles in stage batch o2s1. In that batch every tile was rows N with 0 letters, including all 3 known-text gate tiles, so the gate FAILED 0/3. The record states the batch is UNINFORMATIVE, not a null for its target tiles (P4-O-STAGE-O2S1-RESULT). Iteration-5 target work was stopped, and the model route moved to P4-OWN.

| key number | meaning | file on this branch |
|---|---|---|
| 4356 | model windows planned and computed for the tile | `logs/sib/o5w5/STATUS.md` |
| 3b2b40420621f0a68cb0834c6b44fa1838bbf9a81960fcb2391d9ba571d39e9f | png_sha256 of the pushed tile | `logs/sib/o5w5/p4o/fleet/o5w5.json` |
| 4.17e-7 | layout max \|logit diff\| check at model load | `logs/sib/o5w5/STATUS.md` |

## Where the records are

- `logs/sib/o5w5/STATUS.md`
- `logs/sib/o5w5/RESUME.md`
- `logs/sib/o5w5/p4o/fleet/o5w5.json`
- `logs/sib/o5w5/p4o/PHerc.1667-iteration-5/`
- `logs/sib/o5w5/progress.jsonl`

## Lesson

A target-tile read means nothing when the same batch's known-text gate fails, so the record marks it uninformative rather than null.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w6
- sib-o5w8
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# p4o_tiles.py, infer_1667.py and fetch.py are on sib-ckpt-screen-b at code commit 98cd075; venv /opt/ckb per its p4o/WORKER.md section 3
git worktree add /work/ckb 98cd075 && cd /work/ckb
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w5/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
