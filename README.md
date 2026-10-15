<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="0139 pairs part 3, then helper jobs: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# 0139 pairs part 3, then helper jobs

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pairs0139c` · geometry, reading calibration, tools and records · 2026-09-26..2026-10-01 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHercParis4, PHerc0490A.

## Question

Originally part 3 of the PHerc0139 D2 pair build. When that never started, the session became a helper: it computed own-model maps for the PHercParis4 own-model coordination lane, ran an FL-2 gate on PHerc0139, and ran an FL-4 lane on PHerc0490A.

## Method

Each job ran a fixed, hash-pinned kit from the orchestrator, with no parameter changes, numbers only and no image viewed. Own-model S1 maps were checked for reproducibility: one tile's map had to be byte-identical to the coordinating lane's map of the same tile. The FL-2 gate rendered with C2-NT, ran the official ink_9um model (step-075000, both directions, no TTA) on PHerc0139 segments, and used the template tiler unchanged; official data only, after DECL-FL-2-E1 withdrew a community checkpoint arm. FL-4 ran seed, grow, render and GP (timesformer_GP_scroll1) inference under the shared watchdog.

## What ran on this branch

- 2026-09-26: environment built; waited 6 h for the pairs0139 handover, which never came.
- 2026-09-30 to 2026-10-01, own-model maps: passes of 4, 9 and 11 assigned tiles, plus 7 verso and 2 forward maps. Every reproducibility tile matched byte for byte.
- FL-2 gate: 112 official gate tiles were written before the gate was stopped by hand to give FL-4 priority.
- GP gate: stopped by DECL-FL-4-A1 when the owner dropped the PHerc0139 gate.
- FL-4, PHerc0490A lane 15/16: grew one 11.665 cm^2 surface and wrote its first GP tile.

## Outcome

Part 3 never ran. The helper outputs were pushed with hashes. Gate and census decisions were left to the orchestrator and are not on this branch. The record ends mid-run in the FL-4 PHerc0490A pipeline (last entry 2026-10-01 18:24Z), with no completion marker.

| key number | meaning | file on this branch |
|---|---|---|
| 112 | official FL-2 gate tiles written before the gate was stopped for FL-4 | `logs/sib/pairs0139c/fl2_gate/STATUS.md` |
| 0.999926 | Pearson r between fp32 and bf16 GP inference in the precision check | `logs/sib/pairs0139c/fl4_gate/precision_check.json` |
| 4/4 | assigned map tiles pushed in the first helper pass, with the reproducibility tile byte-identical | `logs/sib/pairs0139c/STATUS.md` |
| 11.665 cm^2 | area of the one PHerc0490A surface grown in FL-4 (0 self-intersections) | `logs/sib/pairs0139c/fl4/PHerc0490A/STATUS.md` |

## Where the records are

- `logs/sib/pairs0139c/ASK.md`
- `logs/sib/pairs0139c/STATUS.md`
- `logs/sib/pairs0139c/fl2_gate/`
- `logs/sib/pairs0139c/fl4_gate/STATUS.md`
- `logs/sib/pairs0139c/fl4/PHerc0490A/`

## Related

- sib-pairs0139
- sib-pairs0139b
- DECL-D2
- DECL-FL-2
- DECL-FL-2-E1
- DECL-FL-4-A1
- DECL-P4-25-A10-A1
- DECL-P4-26-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/pairs0139c/fl4/setup_gp.sh
bash tools/sib/pairs0139c/fl4/run.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
