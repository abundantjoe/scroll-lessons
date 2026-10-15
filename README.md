<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 gate tile, worker 2: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 gate tile, worker 2

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w2` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can the public PHerc.1667-iteration-5 ink model show Paris 4's known text? This worker computed the second of the three known-text gate tiles for the P4-O stage read.

## Method

The lane used ckpt-screen-b's p4o WORKER.md pipeline (code 98cd075, file sha256 verified) and the sha256-verified iteration-5 checkpoint. The card files were git-oid verified. Geometry: 2.4 um level 0, slices 23-84, forward order only, 4 CPU threads. Outputs were pushed in the WORKER.md layout under the lane directory and never opened. The tile was read blind in stage batch o2s1 (DECL-P4-14-A3 item 2).

## What ran on this branch

One uninterrupted run on 2026-09-27 from 02:42:56Z to 05:14:49Z: 3614 model windows, 4 threads, forward order. A progress log was pushed about every 30 min.

## Outcome

The tile completed (valid_fraction 0.85633, coverage_of_valid 0.98584). About 1.4 % of mesh-valid pixels got no window and are written as 0; this was disclosed and left unchanged. In stage batch o2s1 all 3 known-text gate tiles, this one included, were rows N with 0 letters, so the gate FAILED 0/3 and the batch is UNINFORMATIVE (P4-O-STAGE-O2S1-RESULT). The record attributes this to domain shift of the PHerc.1667 model on Paris 4. Iteration-5 target tiles were stopped.

| key number | meaning | file on this branch |
|---|---|---|
| 3614 | model windows computed for the tile | `logs/sib/o5w2/STATUS.md` |
| 2.531 h | wall time of the single uninterrupted run | `logs/sib/o5w2/o5w2_tile.json` |
| 0a0b11242f53ca40024bb6ddb8a49c5e9e69e2129bb8a62712aa9552eccb6c5d | png_sha256 of the pushed tile, re-verified after copy | `logs/sib/o5w2/o5w2_tile.json` |
| 0.98584 | coverage_of_valid (about 1.4 % of mesh-valid px written as 0) | `logs/sib/o5w2/STATUS.md` |
| 4.172325134277344e-07 | layout max \|logit diff\| check at model load | `logs/sib/o5w2/o5w2_tile.json` |

## Where the records are

- `logs/sib/o5w2/STATUS.md`
- `logs/sib/o5w2/RESUME.md`
- `logs/sib/o5w2/o5w2_tile.json`
- `logs/sib/o5w2/p4o/fleet/o5w2.json`
- `logs/sib/o5w2/p4o/PHerc.1667-iteration-5/`
- `logs/sib/o5w2/progress.log`

## Lesson

Disclosing small coverage gaps in the tile record, rather than patching them, kept the gate read on exactly the declared pipeline output.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w1
- sib-o5w3
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# p4o_tiles.py, infer_1667.py and fetch.py are on sib-ckpt-screen-b at code commit 98cd075; venv /opt/ckb per its p4o/WORKER.md section 3
git worktree add /work/ckb 98cd075 && cd /work/ckb
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w2/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
