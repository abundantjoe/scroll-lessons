<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF map maker: repro gate fail: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF map maker: repro gate fail

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-13` · PARIS-4 investigations · 2026-09-30..2026-10-01 · status **STOOD-DOWN** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Map-maker for P4-OFF (DECL-P4-26-A2): make verso-mode and forward S1 maps of 5 assigned PHerc Paris 4 tiles, after first passing a byte-identical forward repro of a reference tile.

## Method

Same pinned code and model as the other makers (tools/p4/infer_verso.py, own-lead infer.py, S1 checkpoint bfa9f7a6); the gate requires the reference tile's forward map png sha256 to equal own-lead's before any listed tile is made.

## What ran on this branch

2026-09-30 23:32Z-2026-10-01 00:30Z: the repro run only (interrupted by a container restart and resumed from a band checkpoint), then a stand-down on the orchestrator's order (DECL-P4-26-A2-E2); a clean diagnostic re-run was stopped after 2 bands. CPU with AVX512, torch 2.14.1+cpu, 4 threads.

## Outcome

REPRO FAIL: forward png sha256 fb6a6900... vs own-lead 6954db7d...; DECL-P4-26-A2-E2 records the same valid pixels and means differing by a relative ~4e-10, likely floating-point nondeterminism on this container's CPU or library build. No listed map was made, none of this maker's output was used, and its 5 tiles were reassigned to finished makers. Its own two runs agreed exactly on bands 1-2 (0 px differ); candidate causes (library version or AVX512 path, thread count, checkpoint resume) were listed but not tested.

| key number | meaning | file on this branch |
|---|---|---|
| fb6a6900... vs 6954db7d... | repro forward png sha256 here vs own-lead (gate requires equality) | `logs/sib/p4v-13/STATUS.md` |
| 0 | listed verso/forward maps made or pushed | `logs/sib/p4v-13/STATUS.md` |
| 0 px | pixels differing between this container's resumed and clean runs on bands 1-2 | `logs/sib/p4v-13/STATUS.md` |

## Where the records are

- `logs/sib/p4v-13/STATUS.md`
- `logs/sib/p4v-13/fwd_x/repro/tiles/`

## Lesson

A byte-identity repro gate caught a cross-container numeric difference of about 4e-10 before any of this maker's maps could enter the census.

## Related

- sib-own-lead
- sib-p4v-03
- sib-p4v-06
- DECL-P4-26-A2
- DECL-P4-26-A2-E2
- P4-OFF-CORR-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
