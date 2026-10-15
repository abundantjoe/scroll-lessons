<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="FE detector: E1 independent re-run: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# FE detector: E1 independent re-run

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-fe-e1` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This was a sub-task of p4-pig-fe. It computed the frozen FE (ochre) detector's maps and raw tile scores for the 60 E1 title-strip tiles (1.129 um) in a separate container, to split the parent's wall time.

## Method

Starting from the parent branch at the params freeze, it ran tools/sib/p4-pig-fe/strip.py in two steps: 'maps E1' and then 'score E1' with sigma0 = 1.0, so z equals the raw response r (the parent divides by its control sigma0). No code or parameter was changed. Numbers only; no image was viewed and no further siblings were created.

## What ran on this branch

Created 2026-09-26 ~18:31Z, pushed 2026-09-27 07:33Z. The maps step fetched 289,883 chunks (9,977 absent) in 1,211.6 s. The score step covered 70,058,674 positions on 60 of 60 eligible tiles in 244 s. The 2.16 GB map file stayed in scratch. The container restarted between the two steps; scoring reused the saved maps, and nothing was re-fetched.

## Outcome

Both steps exited with rc=0. The parent finished E1 first and recorded this run as redundant, but usable as an independent re-run. A read-only comparison for this README found that this branch's raw scores reproduce the parent's E1 tile responses exactly: r_max is identical on all 60 tiles (maximum absolute difference 0.0). The FE verdict belongs to the parent: insensitive at 5-10 um.

| key number | meaning | file on this branch |
|---|---|---|
| 60/60 | eligible E1 tiles scored | `logs/sib/p4-pig-fe/1129/STATUS_E1.md` |
| 70,058,674 | detector positions scored | `logs/sib/p4-pig-fe/1129/scores_E1_raw.json` |
| 289,883 (9,977 absent) | CT chunks fetched for the E1 maps | `logs/sib/p4-pig-fe/1129/STATUS_E1.md` |
| 0.0 | maximum absolute difference in per-tile r_max against the parent's 1129/scores_E1.json, over all 60 tiles | `logs/sib/p4-pig-fe/1129/scores_E1_raw.json` |

## Where the records are

- `logs/sib/p4-pig-fe/1129/scores_E1_raw.json`
- `logs/sib/p4-pig-fe/1129/STATUS_E1.md`

## Lesson

A deterministic frozen detector re-run in a second container reproduced the parent's numbers exactly, a cheap independent check.

## Related

- sib-p4-pig-fe
- sib-p4-pig-fe-e2
- DECL-P4-10
- DECL-P4-12

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-pig-fe/strip.py maps E1 <scratch>
python tools/sib/p4-pig-fe/strip.py score E1 <scratch> logs/sib/p4-pig-fe/1129/scores_E1_raw.json --sigma0 1.0
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
