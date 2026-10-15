<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF maps, FL-2 PHerc0268, FL-4: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF maps, FL-2 PHerc0268, FL-4

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-03` · PARIS-4 investigations · 2026-09-30..2026-10-02 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0268.

## Question

Worker lane with three successive jobs: verso-mode and forward S1 maps of PHerc Paris 4 tiles for P4-OFF (DECL-P4-26-A2, including tiles reassigned under -E2/-E3); First Letters material on PHerc0268 as its primary worker (DECL-FL-2); then FL-4 Grand Prize-model predictions as PHerc0268 lane 0.

## Method

Ran the project's own S1 ink model (sha bfa9f7a6) unchanged through tools/p4/infer_verso.py with reversed layer order (verso face) and in forward order, on an assigned list of PHerc Paris 4 segment tiles, after a byte-identical forward repro of a reference tile as the gate. For FL-2 (official organizer ink_9um step-075000 only, DECL-FL-2-E1) it auto-grew segments from seeds with the organizers' VC3D grower (gate: 0 self-intersections), rendered them, inferred in both directions and cut 2 x 2 cm tiles for the blind-reader census. For FL-4 (DECL-FL-4-A1/-A2) it grew small segments from the declared seed list and ran the organizer-hosted 2023 Grand Prize TimeSformer, variant B (rescale 8.64/7.91), forward then reverse, giving cover cells and a whole-segment window.

## What ran on this branch

2026-09-30 23:30Z-2026-10-01 01:19Z: REPRO PASS, 11 verso + 8 forward S1 maps (own list plus reassigned extras). 2026-10-01 02:13-17:19Z: FL-2 on PHerc0268 (8.640 um): 24 grow attempts, 22 kept, 18 rendered and inferred, 144 official tiles; stopped by DECL-FL-4-A1. FL-4 lane 0: one segment's GP forward pass on 2026-10-01 (A1 tiles and 4 cover cells, no window); a fresh session at 23:28Z the same day failed its environment and wrote a false lane-complete.

## Outcome

Its P4-OFF maps were staged and used; the channel was INFORMATIVE at pixel level (P4-OFF-CORR-RESULT, median r 0.120 vs null p95 0.039) but the verso census gave no candidate and P4-OFF was closed as weak / reader-insensitive (P4-OFF-VW-RESULT). FL-2: 8 of its tiles were read in FL-2 wave 1 and 30 of its windows in FL-3 wave 1, with 0 positives fleet-wide under a gate that was NOT SENSITIVE, so the nulls are uninformative; DECL-FL-5 later found all FL-2/FL-3 unread-scroll tiles came from a grower that cuts across windings. Its FL-4 forward item was read in FL4-W41 (0 positives) and is VOID (DECL-FL-4-A5). The false ALL_DONE is recorded in DECL-FL-4-A4-A1-E2; a restart message was refused by the orchestrator session's safety classifier (DECL-FL-4-A4-A2-E3), and the orchestrator's last commit here (2026-10-02 05:36Z) only added the FL-4 kit.

| key number | meaning | file on this branch |
|---|---|---|
| 11 + 8 | verso + forward S1 maps pushed (incl. reassigned extras), REPRO PASS | `logs/sib/p4v-03/STATUS.md` |
| 22 of 24 | FL-2 grow attempts kept on PHerc0268 | `logs/sib/p4v-03/fl2/STATUS.md` |
| 144 | official ink_9um tiles pushed (18 of 22 kept segments complete at stop) | `logs/sib/p4v-03/fl2/STATUS.md` |
| 0 segments | false 'lane complete' written by the fresh FL-4 session after its environment failed | `logs/sib/p4v-03/fl4/PHerc0268/STATUS.md` |

## Where the records are

- `logs/sib/p4v-03/STATUS.md`
- `logs/sib/p4v-03/verso/tiles/`
- `logs/sib/p4v-03/fwd_x/`
- `logs/sib/p4v-03/fl2/`
- `logs/sib/p4v-03/fl4/PHerc0268/`

## Lesson

An environment check that tested only the wrapper and docker let a lane without Python write a false lane-complete; check every tool used and never write a completion marker for an empty work list.

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
- DECL-FL-4-A4-A1-E2
- DECL-FL-4-A4-A2-E1
- DECL-FL-4-A4-A2-E3
- FL4-W41-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
setsid nohup bash tools/sib/p4v-03/fl2/watchdog.sh >/dev/null 2>&1 &
bash tools/fl4/go.sh <worker> <SCROLL> <lane> <nlanes>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
