<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF maps, FL-2 PHerc0813: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF maps, FL-2 PHerc0813

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-07` · PARIS-4 investigations · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0813.

## Question

Worker lane with two successive jobs: verso-mode and forward S1 maps of PHerc Paris 4 tiles for P4-OFF (DECL-P4-26-A2); then First Letters material on PHerc0813 as its primary worker (DECL-FL-2).

## Method

Ran the project's own S1 ink model (sha bfa9f7a6) unchanged through tools/p4/infer_verso.py with reversed layer order (verso face) and in forward order, on an assigned list of PHerc Paris 4 segment tiles, after a byte-identical forward repro of a reference tile as the gate. For FL-2 (official organizer ink_9um step-075000 only, DECL-FL-2-E1) it auto-grew segments from seeds with the organizers' VC3D grower (gate: 0 self-intersections), rendered them, inferred in both directions and cut 2 x 2 cm tiles for the blind-reader census.

## What ran on this branch

2026-09-30 23:29Z-2026-10-01 01:23Z: REPRO PASS (an earlier FAIL line was voided as a driver bug that logged an empty hash), 6 verso + 6 forward S1 maps. 2026-10-01 02:12-04:30Z: FL-2 on PHerc0813 (9.362 um): 24 grow attempts, 23 kept, 3 segments rendered, inferred and tiled, 24 official tiles.

## Outcome

Its P4-OFF maps were staged and used; the channel was INFORMATIVE at pixel level (P4-OFF-CORR-RESULT, median r 0.120 vs null p95 0.039) but the verso census gave no candidate and P4-OFF was closed as weak / reader-insensitive (P4-OFF-VW-RESULT). FL-2: 8 of its tiles were read in FL-2 wave 1 and 6 of its windows in FL-3 wave 1, with 0 positives fleet-wide under a gate that was NOT SENSITIVE, so the nulls are uninformative; DECL-FL-5 later found all FL-2/FL-3 unread-scroll tiles came from a grower that cuts across windings. The lane's next trigger was refused at about 06:0xZ on 2026-10-01 and not retried, so it never joined FL-4 (DECL-FL-4-A1 item 1).

| key number | meaning | file on this branch |
|---|---|---|
| 6 + 6 | verso + forward S1 maps pushed, REPRO PASS after a voided driver-bug FAIL line | `logs/sib/p4v-07/STATUS.md` |
| 23 of 24 | FL-2 grow attempts kept on PHerc0813 | `logs/sib/p4v-07/fl2/STATUS.md` |
| 24 | official ink_9um tiles (3 segments x 8) pushed by 04:30Z | `logs/sib/p4v-07/fl2/pipeline.log` |

## Where the records are

- `logs/sib/p4v-07/STATUS.md`
- `logs/sib/p4v-07/verso/tiles/`
- `logs/sib/p4v-07/fwd_x/`
- `logs/sib/p4v-07/fl2/`

## Lesson

A driver that logs an empty hash as REPRO FAIL can fake a gate failure; the line was voided and the gate re-run, and only the real comparison counted.

## Related

- sib-own-lead
- DECL-P4-26-A2
- DECL-P4-26-A2-E2
- DECL-P4-26-A2-E3
- P4-OFF-CORR-RESULT
- P4-OFF-VW-RESULT
- DECL-FL-2
- DECL-FL-2-E1
- FL2-WAVE1-RESULT
- DECL-FL-3
- FL3-W1-RESULT
- DECL-FL-5
- DECL-FL-4-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
setsid nohup bash tools/sib/p4v-07/fl2/watchdog.sh >/dev/null 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
