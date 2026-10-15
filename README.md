<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc0813: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc0813

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0813` · First Letters push · 2026-09-30..2026-09-30 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0813.

## Question

Can the DECL-FL-1 First Letters screen find 10 letters within 4 cm2 on PHerc0813 from auto-grown segments and the official ink model?

## Method

DECL-FL-1 worker (tools/sib/fl-pherc0813/pipeline.sh, run.sh): the bucket has no organizer segments for PHerc0813, so 4 auto-grow attempts on the organizer surface-m7 L0 prediction, kept iff 0 transverse self-intersections and >= 16 cm2, then C2-NT render, ink_9um step-075000 in both directions without TTA, and 2 cm tiles, with a marker per finished unit.

## What ran on this branch

Only the launch: the pipeline was started detached at 2026-09-30 04:02Z. No unit marker, segment, render or tile was ever pushed, and the branch has no later commit.

## Outcome

No result. The branch holds the code and the launch record only. PHerc0813 was later covered in DECL-FL-2 by other workers (not on this branch).

| key number | meaning | file on this branch |
|---|---|---|
| 4 | planned auto-grow attempts (NGROW), gate >= 16 cm2 and 0 self-intersections | `tools/sib/fl-pherc0813/pipeline.sh` |
| 0 | segments or tiles pushed | `logs/sib/fl-pherc0813/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0813/STATUS.md`
- `tools/sib/fl-pherc0813/`

## Related

- claude/gifted-bell-gavnl5 (research log)
- DECL-FL-1
- DECL-FL-2
- sib-p4v-07 (FL-2 primary for PHerc0813)
- sib-tracer (FL-2 second worker for PHerc0813)

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
nohup bash tools/sib/fl-pherc0813/run.sh > /work/fl/run.log 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
