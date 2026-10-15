<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF maps, FL-2 PHerc0343, FL-4: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF maps, FL-2 PHerc0343, FL-4

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-04` · PARIS-4 investigations · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0343, PHerc0490A.

## Question

Worker lane with three successive jobs: verso-mode and forward S1 maps of PHerc Paris 4 tiles for P4-OFF (DECL-P4-26-A2); First Letters material on PHerc0343 as its primary worker (DECL-FL-2); then FL-4 Grand Prize-model predictions on PHerc0490A seed segments.

## Method

Ran the project's own S1 ink model (sha bfa9f7a6) unchanged through tools/p4/infer_verso.py with reversed layer order (verso face) and in forward order, on an assigned list of PHerc Paris 4 segment tiles, after a byte-identical forward repro of a reference tile as the gate. For FL-2 (official organizer ink_9um step-075000 only, DECL-FL-2-E1) it auto-grew segments from seeds with the organizers' VC3D grower (gate: 0 self-intersections), rendered them, inferred in both directions and cut 2 x 2 cm tiles for the blind-reader census. For FL-4 (DECL-FL-4-A1/-A2) it grew small segments from the declared seed list and ran the organizer-hosted 2023 Grand Prize TimeSformer, variant B (rescale 8.64/7.91), forward then reverse, giving cover cells and a whole-segment window.

## What ran on this branch

2026-09-30 23:32Z-2026-10-01 01:22Z: REPRO PASS, 7 verso + 7 forward S1 maps (6 listed tiles plus one -E3 extra). 2026-10-01 02:26-17:21Z: FL-2 on PHerc0343 (8.640 um): 6 grows kept, 48 official tiles; stopped by DECL-FL-4-A1. 2026-10-01 17:23-19:12Z: FL-4 on PHerc0490A: one segment GP forward and reverse (1 tile each, A1 kit), a second segment grown.

## Outcome

Its P4-OFF maps were staged and used; the channel was INFORMATIVE at pixel level (P4-OFF-CORR-RESULT, median r 0.120 vs null p95 0.039) but the verso census gave no candidate and P4-OFF was closed as weak / reader-insensitive (P4-OFF-VW-RESULT). FL-2: 8 of its tiles were read in FL-2 wave 1 and 12 of its windows in FL-3 wave 1, with 0 positives fleet-wide under a gate that was NOT SENSITIVE, so the nulls are uninformative; DECL-FL-5 later found all FL-2/FL-3 unread-scroll tiles came from a grower that cuts across windings. Its FL-4 PHerc0490A outputs were never read (DECL-FL-4-A3); the A1 workers stopped at the 5-hour usage limit and the PHerc0490A restart batch was never created before FL-4 was halted as not sheet-following (DECL-FL-4-A5).

| key number | meaning | file on this branch |
|---|---|---|
| 7 + 7 | verso + forward S1 maps pushed, REPRO PASS | `logs/sib/p4v-04/STATUS.md` |
| 6 | FL-2 segments grown, kept and tiled on PHerc0343 | `logs/sib/p4v-04/fl2/STATUS.md` |
| 48 | official ink_9um tiles (6 segments x 8, 4 forward / 4 reverse each) | `logs/sib/p4v-04/fl2/STATUS.md` |
| 1 + 1 | FL-4 GP variant B tiles (forward, reverse) for one PHerc0490A segment | `logs/sib/p4v-04/fl4/PHerc0490A/STATUS.md` |

## Where the records are

- `logs/sib/p4v-04/STATUS.md`
- `logs/sib/p4v-04/verso/tiles/`
- `logs/sib/p4v-04/fwd_x/`
- `logs/sib/p4v-04/fl2/`
- `logs/sib/p4v-04/fl4/PHerc0490A/`

## Lesson

Accepting a grown surface on area and zero self-intersections alone let data-independent extrapolations through; a sheet-following check and a known-ink positive control must gate rendering (DECL-FL-4-A5 item 2).

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
- DECL-FL-4
- DECL-FL-4-A1
- DECL-FL-4-A2
- DECL-FL-4-A5
- DECL-FL-4-A8
- DECL-FL-4-A3
- DECL-FL-4-A4-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
setsid nohup bash tools/sib/p4v-04/fl2/watchdog.sh >/dev/null 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
