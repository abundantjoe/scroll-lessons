<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OFF maps, FL-2 PHerc0175A, FL-4: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OFF maps, FL-2 PHerc0175A, FL-4

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-02` · PARIS-4 investigations · 2026-10-01..2026-10-02 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0175A, PHerc0268.

## Question

Worker lane with three successive jobs: verso-mode and forward S1 maps of assigned PHerc Paris 4 tiles for the P4-OFF offset test (DECL-P4-26-A2); First Letters material on PHerc0175A as its primary worker (DECL-FL-2); then FL-4 Grand Prize-model predictions on PHerc0268 seed segments (lane 2).

## Method

Ran the project's own S1 ink model (sha bfa9f7a6) unchanged through tools/p4/infer_verso.py with reversed layer order (verso face) and in forward order, on an assigned list of PHerc Paris 4 segment tiles, after a byte-identical forward repro of a reference tile as the gate. For FL-2 (official organizer ink_9um step-075000 only, DECL-FL-2-E1) it auto-grew segments from seeds with the organizers' VC3D grower (gate: 0 self-intersections), rendered them, inferred in both directions and cut 2 x 2 cm tiles for the blind-reader census. For FL-4 (DECL-FL-4-A1/-A2) it grew small segments from the declared seed list and ran the organizer-hosted 2023 Grand Prize TimeSformer, variant B (rescale 8.64/7.91), forward then reverse, giving cover cells and a whole-segment window.

## What ran on this branch

2026-10-01 00:11-01:24Z: REPRO PASS, then 6 verso + 6 forward S1 maps. 2026-10-01 02:11-17:03Z: FL-2 on PHerc0175A (8.640 um scan, no organizer segments): 17 grow attempts all kept, 16 rendered and inferred, 128 official tiles. FL-4 PHerc0268: 8 segments grown on 2026-10-01 with 7 renders failing under the first kit; a fresh session on 2026-10-02 produced one GP forward pass (4 cells, 1 window).

## Outcome

Its P4-OFF maps were staged and used; the channel was INFORMATIVE at pixel level (P4-OFF-CORR-RESULT, median r 0.120 vs null p95 0.039) but the verso census gave no candidate and P4-OFF was closed as weak / reader-insensitive (P4-OFF-VW-RESULT). FL-2: 8 of its tiles were read in FL-2 wave 1 and 28 of its windows in FL-3 wave 1, with 0 positives fleet-wide under a gate that was NOT SENSITIVE, so the nulls are uninformative; DECL-FL-5 later found all FL-2/FL-3 unread-scroll tiles came from a grower that cuts across windings. Its FL-4 window was read in FL4-W47 (0 positives) and is VOID with all FL-4 reads (DECL-FL-4-A5); two more seeds of this lane were computed locally by the orchestrator (FL4-W43, FL4-W50). The lane stopped when its keepalive hit the 7200 s harness limit at 07:58Z on 2026-10-02 (DECL-FL-4-A4-A2-E4).

| key number | meaning | file on this branch |
|---|---|---|
| 6 + 6 | verso (reverse order) + forward S1 maps pushed after REPRO PASS; png sha256 checked | `logs/sib/p4v-02/STATUS.md` |
| 17 of 17 | FL-2 auto-grow attempts kept on PHerc0175A (0 self-intersections) | `logs/sib/p4v-02/fl2/STATUS.md` |
| 128 | official ink_9um 2 x 2 cm tiles pushed (16 segments x 8) | `logs/sib/p4v-02/fl2/STATUS.md` |
| 7 of 8 | FL-4 PHerc0268 renders that failed under the first (A1) kit on 2026-10-01 | `logs/sib/p4v-02/fl4/PHerc0268/STATUS.md` |
| 1 | FL-4 GP variant B whole-segment window (forward, 2026-10-02) | `logs/sib/p4v-02/fl4/PHerc0268/STATUS.md` |

## Where the records are

- `logs/sib/p4v-02/STATUS.md`
- `logs/sib/p4v-02/verso/tiles/`
- `logs/sib/p4v-02/fwd_x/`
- `logs/sib/p4v-02/fl2/`
- `logs/sib/p4v-02/fl4/PHerc0268/`

## Lesson

A keepalive that can outlive the harness's 7200 s background limit is killed and, by harness rule, not restarted; it must end inside the limit (fixed in DECL-FL-4-A4-A2-E4).

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
- DECL-FL-4-A4-A2-E4
- FL4-W47-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/p4v-02/gate.sh
setsid nohup bash tools/sib/p4v-02/fl2/watchdog.sh >/dev/null 2>&1 &
bash tools/fl4/go.sh <worker> <SCROLL> <lane> <nlanes>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
