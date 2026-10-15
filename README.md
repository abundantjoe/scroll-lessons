<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-L thin-slab raw-CT channel (2.4 um): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-L thin-slab raw-CT channel (2.4 um)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-l2` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Does a thin-slab maximum of raw 2.4 um CT around the official mesh show ink on known text well enough to use for the Paris 4 title search? The question covers P4-L (DECL-P4-12) and its variants: the L2S row-baseline display, a block detector (DECL-P4-17) and surface-following L4 faces (DECL-P4-18).

## Method

Thresholds were frozen on the known-text control (17 of 168 tiles: T_mid 93, T_hi 203) before any tile. L2 is the per-pixel maximum over 13 slices (+-14.4 um) at level 0, with a global stretch, cut into 1068 px tiles on the frozen grid; L2S is a row-baseline variant. A cell-level block detector was frozen on the control with a held-out bar (text recall >= 0.90 at FPR <= 0.05). L4 surface-following faces were built with a control pre-gate. Tiles were read blind through another lane's harness.

## What ran on this branch

2026-09-26 to 2026-09-27: L2 160/160 tiles (682,668 level-0 chunk reads), L2S 160/160, P4-W windows (70 + 56); block-detector cells on 64 control tiles; L4 pre-gate at level 1 on 40 text and 24 intercolumn control tiles.

## Outcome

Every gate failed. The blind census of L2, recorded in the research log as P4-L2-CENSUS-RESULT, named 0 letters on all 160 tiles and passed 0 of 72 known-text tiles, so L2 is uninformative. The block detector at L2S depth reached held-out recall 0.0891 at FPR 0.0321: FAIL. The L4 pre-gate reached held-out recall 0.074 (L4-) and 0.033 (L4+): FAIL, so no L4 number was computed for the inner strip. L3 was never built because p4-depth returned STOP.

| key number | meaning | file on this branch |
|---|---|---|
| 160/160 | L2 tiles built (manifest complete) | `logs/sib/p4-l2/l2/manifest.json` |
| 93 / 203 | frozen control thresholds T_mid / T_hi | `logs/sib/p4-l2/STATUS.md` |
| 0.0891 at FPR 0.0321 | block-detector held-out text recall (bar 0.90 at FPR <= 0.05) | `logs/sib/p4-l2/BLOCK_FREEZE.md` |
| 0.074 / 0.033 | L4- / L4+ held-out recall in the control pre-gate | `logs/sib/p4-l2/PREGATE_L4.json` |

## Where the records are

- `logs/sib/p4-l2/STATUS.md`
- `logs/sib/p4-l2/RESUME.md`
- `logs/sib/p4-l2/ASK.md`
- `logs/sib/p4-l2/BLOCK_FREEZE.md`
- `logs/sib/p4-l2/PREGATE_L4.json`
- `logs/sib/p4-l2/l2/`
- `logs/sib/p4-l2/l2s/`
- `logs/sib/p4-l2/l4/`
- `logs/sib/p4-l2/block/`
- `logs/sib/p4-l2/w_l2s/`
- `logs/sib/p4-l2/wpc_l2s/`
- `tools/sib/p4-l2/`

## Lesson

On known text, a bright-voxel slab at a constant offset from the official mesh does not separate ink from papyrus, and the channel failed its own control before the target was interpreted.

## Related

- DECL-P4-12
- DECL-P4-12-A1
- DECL-P4-12-A2
- DECL-P4-17
- DECL-P4-18
- P4-L2-CENSUS-RESULT
- sib-p4-depth
- sib-p4-highz

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-l2/test_l2.py
python3 tools/sib/p4-l2/l2.py thresholds <ctl_mesh_dir> <out_dir> --worker k --nworkers n
python3 tools/sib/p4-l2/l2.py thresholds-merge <ctl_mesh_dir> <out_dir>
bash tools/sib/p4-l2/run_tiles.sh   # 4 tile workers; commits and pushes
bash tools/sib/p4-l2/run_l2s.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
