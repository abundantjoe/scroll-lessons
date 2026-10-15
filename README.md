<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Dominion research log and rule chain: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Dominion research log and rule chain

**Dominion experiment branch** `claude/gifted-bell-gavnl5` · geometry, reading calibration, tools and records · 2026-09-24..2026-10-11 · status **RESEARCH-LOG** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHerc0841, PHerc0268, PHerc0343P, PHercParis4.

## Question

Where does Dominion keep its single record of declarations, results and verdicts? This is the orchestrator's working branch. It holds the hash-chained RULES.md, LEDGER.md, STATE.md, CHANGELOG.md, RESUME_NOW.md and the per-step logs.

## Method

Every decision is declared in RULES.md before its data are read: DECL-* entries in a hash chain, with METRIC-HASH pins on the code that will score it. Results are appended as result entries, and LEDGER.md summarises each verdict in one row with the scorer-output sha256 and the auditor. Sibling lanes push to their own branches, and the orchestrator records their results here. Blind reads use sealed (age-encrypted) answers and audited transcripts.

## What ran on this branch

The record runs from day 0 on 2026-09-24 (CHANGELOG.md) to 2026-10-11. The history fetched on this branch holds 173 commits from 2026-10-02 to 2026-10-11, covering the FL-4 ring lanes, the PHerc0268 umbilicus, unrolling and end-to-end work, and the hand-off notes. Per-step outputs are under logs/ (c3, d1, handed, readcal, p4, fl2, fl4, fl7, umb, unr, offload and others).

## Outcome

LEDGER.md records these verdicts:
- C3-NT-R1 PASS: the validated 9 um base chain.
- C3-R1 FAIL: the run with test-time augmentation.
- D1 FAIL: blind readers named nothing in our 9 um maps of unseen PHerc0841.
- D3 FOLD-0841 NOT PASSED.
- Handedness AMBIGUOUS, three times.
- READ-CAL: SG-FEAS NOT PASSED.

The STATE.md headline (last updated 2026-09-26): no submission ready and 0 firm letters on any eligible volume; FL6-RESULT in RULES.md (2026-10-03) records that no letter has been claimed at any point. In October, the E2E-1 end-to-end test on PHerc0268 failed four of its declared bars (G2, G3, G5 and the ink-model bars) (logs/unr/E2E-1-RESULT.md).

| key number | meaning | file on this branch |
|---|---|---|
| 0.99960 | C3-NT-R1 forward AUC (PASS), the validated 9 um chain without test-time augmentation | `LEDGER.md` |
| 0.97795 | C3-R1 forward AUC with test-time augmentation, below the 0.987 bar (FAIL) | `LEDGER.md` |
| 0 | namings by 18 blind readers on the D1 model arms over all J windows and blanks (D1 FAIL) | `LEDGER.md` |
| A:B 0:0, 7:1, 5:13 | reader votes in the three handedness tests, all AMBIGUOUS | `LEDGER.md` |
| 0 | firm letters on any eligible volume (STATE.md headline, 2026-09-26) | `STATE.md` |
| 0.579 | pixel AUC of the federated global_r1 ink model on the held-out PHerc0343P shard in E2E-1 (bar 0.90, FAIL) | `logs/unr/E2E-1-RESULT.md` |

## Where the records are

- `LEDGER.md`
- `RULES.md`
- `STATE.md`
- `CHANGELOG.md`
- `RESUME_NOW.md`
- `logs/`

## Lesson

Declaring bars before reading the data, and logging every verdict with a hash, kept a long run of null results honest.

## Related

- data
- DECL-C3
- DECL-D1
- DECL-D3D4
- DECL-HANDED
- DECL-READCAL
- DECL-E2E-1
- DECL-UMB-2
- DECL-REMOTE-HARNESS-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run (tools/c3/run_infer.sh; paths under /work are the original container's)
export OMP_NUM_THREADS=3
python -m vesuvius.ink_detection.inference.infer <render.zarr> step-075000.pth out.tif --direction both --batch-size 4 --num-workers 1 --no-compile   # C2-NT: no --tta-mirror
C3_X0=<x0> C3_Y0=<y0> C3_LAB=<inklabels.zarr/0> C3_SUP=<supervision_mask.zarr/0> python tools/c3/auc_eval.py OUT.json crop <render_valid.npy> fwd=<map.tif>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
