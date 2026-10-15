<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF verso/forward map maker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF verso/forward map maker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-10` · PARIS-4 investigations · 2026-09-30..2026-10-01 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Map-maker for P4-OFF (DECL-P4-26-A2): produce verso-mode and forward S1 ink maps of 5 assigned PHerc Paris 4 tiles, so the offset-correlation test and the verso census could ask whether ink offset from the facing winding is detectable.

## Method

Ran the project's own S1 ink model (sha bfa9f7a6) unchanged through tools/p4/infer_verso.py with reversed layer order (verso face) and in forward order, on an assigned list of PHerc Paris 4 segment tiles, after a byte-identical forward repro of a reference tile as the gate. Numbers only: no map, tile or CT image was opened by the lane.

## What ran on this branch

2026-09-30 23:32Z-2026-10-01 00:29Z: REPRO PASS on the reference tile, then 5 verso (reverse order) + 5 forward S1 maps, each png sha256 checked against its record (run script logs/sib/p4v-10/run_p4v10.sh). The branch holds no FL-2 or FL-4 output, although the research log's FL-2 and FL-4 assignment files list this worker.

## Outcome

All 10 maps were staged into P4-OFF (5 verso, 5 forward from this maker). P4-OFF-CORR-RESULT was INFORMATIVE (median r 0.120 vs null p95 0.039, Mann-Whitney p 4.6e-7); in the verso census (P4-OFF-VW-RESULT) no window became a candidate (0 candidates), and the channel was closed as weak / reader-insensitive. The record does not say why this worker never started its FL-2/FL-4 assignments.

| key number | meaning | file on this branch |
|---|---|---|
| 5 + 5 | verso + forward S1 maps pushed | `logs/sib/p4v-10/STATUS.md` |
| REPRO PASS | forward repro of the reference tile byte-identical to own-lead (png sha256 6954db7d...) | `logs/sib/p4v-10/STATUS.md` |
| bfa9f7a6 | S1 model checkpoint sha256 prefix, verified before the run | `logs/sib/p4v-10/STATUS.md` |

## Where the records are

- `logs/sib/p4v-10/STATUS.md`
- `logs/sib/p4v-10/verso/tiles/`
- `logs/sib/p4v-10/fwd_x/`
- `logs/sib/p4v-10/run_p4v10.sh`

## Lesson

Pixel-level informativeness did not imply reader-level sensitivity: readers could not see known text through the facing winding, so the census null excludes only a strong offset.

## Related

- sib-own-lead
- DECL-P4-26-A2
- DECL-P4-26-A2-E2
- DECL-P4-26-A2-E3
- P4-OFF-CORR-RESULT
- P4-OFF-VW-RESULT
- sib-p4v-01
- sib-p4v-13

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash logs/sib/p4v-10/run_p4v10.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
