<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 gate tile, worker 3: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 gate tile, worker 3

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w3` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can the public PHerc.1667-iteration-5 ink model show Paris 4's known text? This worker computed the third of the three known-text gate tiles for the P4-O stage read.

## Method

The lane ran ckpt-screen-b's WORKER.md (at 6aa0345) with the tools from code commit 98cd075, all sha256-verified. The checkpoint sha256 was verified against WORKER.md, the catalogue and the loader. Geometry: 2.4 um level 0, slices 23-84, window 256, stride 128, halo 128, clip(0,200)/255, fp32, forward order, 4 threads. Outputs were pushed in the WORKER.md layout and never opened. The tile was read blind in stage batch o2s1.

## What ran on this branch

One run on 2026-09-27 from 02:42:41Z to 06:25:09Z: 4356 model windows with 0 resumes, 0 missing CT chunks and 13322.9 s of tile time. Progress was pushed every 30 min.

## Outcome

The tile completed (valid_fraction 1.0, coverage_of_valid 1.0). In stage batch o2s1 every tile was rows N with 0 letters, including all 3 known-text gate tiles, so the gate FAILED 0/3 and the batch is UNINFORMATIVE (P4-O-STAGE-O2S1-RESULT). Per the record, the PHerc.1667 model does not separate ink from papyrus on the Paris 4 2.4 um volume at this geometry. Further iteration-5 target tiles were stopped.

| key number | meaning | file on this branch |
|---|---|---|
| 4356 | model windows computed, 0 resumes | `logs/sib/o5w3/STATUS.md` |
| 13322.9 s | tile compute time (wall 3 h 42 min) | `logs/sib/o5w3/STATUS.md` |
| ac62be5d9c6c216a53ce3db1520d4e2705af750625296b76be66af7d16a70c24 | png_sha256 of the pushed tile (recomputed ok) | `logs/sib/o5w3/STATUS.md` |
| 0 | missing CT chunks | `logs/sib/o5w3/p4o/fleet/o5w3.json` |

## Where the records are

- `logs/sib/o5w3/STATUS.md`
- `logs/sib/o5w3/RESUME.md`
- `logs/sib/o5w3/p4o/fleet/o5w3.json`
- `logs/sib/o5w3/p4o/PHerc.1667-iteration-5/`

## Lesson

A gate of at least 3 known-text tiles showed in one stage read that the cross-scroll model was blind on the target scroll.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w1
- sib-o5w2
- DECL-P4-14-A3
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# p4o_tiles.py, infer_1667.py and fetch.py are on sib-ckpt-screen-b at code commit 98cd075; venv /opt/ckb per its p4o/WORKER.md section 3
git worktree add /work/ckb 98cd075 && cd /work/ckb
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w3/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
