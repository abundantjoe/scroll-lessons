<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-O iteration-5 gate tile, worker 1: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-O iteration-5 gate tile, worker 1

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-o5w1` · ink-model training and checkpoint screening · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can the public PHerc.1667-iteration-5 ink model, which was trained on PHerc1667 only, show Paris 4's known text? This worker computed one of the three known-text gate tiles for the P4-O stage read.

## Method

The lane followed ckpt-screen-b's p4o WORKER.md pipeline exactly, at code commit 98cd075 with the sha256 of p4o_tiles.py, infer_1667.py and fetch.py verified. The checkpoint model.safetensors sha256 was verified against the catalogue. Geometry: the 2.4 um surface volume at level 0, slices 23-84, forward order only, window 256, stride 128, clip(0,200)/255. Outputs (a tile PNG plus JSON) were pushed in the WORKER.md layout and never opened. The pairs0814b harness then read the tile blind in stage batch o2s1 under DECL-P4-14-A3 item 2.

## What ran on this branch

One tile ran on 2026-09-27 from 02:43:55Z to 05:20:55Z on a CPU container with 4 threads (torch 2.14.0+cpu): 3792 model windows in one forward order. 426 missing CT chunks were zero-filled, as the builder does. The outputs were pushed under logs/sib/o5w1/.

## Outcome

The tile completed, and its valid_fraction (0.8997) equals the manifest value. In stage batch o2s1 (10 census tiles, 2 valid sessions, verified 12/12) every tile was rows N with 0 letters, including all 3 known-text gate tiles. The gate therefore FAILED 0/3, and the batch is UNINFORMATIVE (P4-O-STAGE-O2S1-RESULT). The result cites this tile's prediction mean of 139/255 with std 52 as evidence that the model does not separate ink from papyrus on the Paris 4 2.4 um volume (domain shift). Further iteration-5 target tiles were stopped, and the model route moved to P4-OWN.

| key number | meaning | file on this branch |
|---|---|---|
| 3792 | model windows computed for the tile | `logs/sib/o5w1/STATUS.md` |
| 9420 s (2.62 h) | tile runtime at 4 threads, one depth order | `logs/sib/o5w1/STATUS.md` |
| 9caf041bcfa59e8f203580faba12207d2817a7ec5e3d9473883f2d807f7675fc | png_sha256 of the pushed tile | `logs/sib/o5w1/p4o/fleet/o5w1.json` |
| 0.98657 | coverage_of_valid of the prediction | `logs/sib/o5w1/STATUS.md` |
| 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b | verified sha256 of the iteration-5 checkpoint | `logs/sib/o5w1/STATUS.md` |

## Where the records are

- `logs/sib/o5w1/STATUS.md`
- `logs/sib/o5w1/RESUME.md`
- `logs/sib/o5w1/p4o/fleet/o5w1.json`
- `logs/sib/o5w1/p4o/PHerc.1667-iteration-5/`
- `logs/sib/o5w1/tools/o5w1_record.py`

## Lesson

Reading known-text gate tiles in the same stage as target tiles let a cross-scroll model's domain-shift failure stop the remaining target tiles at once.

## Related

- sib-ckpt-screen-b
- sib-pairs0814b
- sib-o5w2
- sib-o5w3
- DECL-P4-14-A3
- METRIC-HASH-39
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# p4o_tiles.py, infer_1667.py and fetch.py are on sib-ckpt-screen-b at code commit 98cd075; venv /opt/ckb per its p4o/WORKER.md section 3
git worktree add /work/ckb 98cd075 && cd /work/ckb
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w1/p4o/PHerc.1667-iteration-5 --tiles "<r>,<c>"   # assigned tile id withheld
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
