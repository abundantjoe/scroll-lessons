<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 NULL arm trainer setup: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 NULL arm trainer setup

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-d2-null` · ink-model training and checkpoint screening · 2026-09-26..2026-09-30 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

Can the NULL control arm of decision D2 (TRAIN-1, fold L-0841: P384 tiles with labels permuted by one seeded derangement, seed 1) be set up so that it trains reproducibly and stays paired with the P384 arm, ready to start on real pairs at GO D2?

## Method

The session copied the pinned D2 trainer unchanged from the trainer lane (commit 8475920, with the later head 08d7e42 kept alongside for the hold-out check), rebuilt the training environment, verified the base ink_9um checkpoint sha256 and ran the trainer test suites. It then ran a 10-step synthetic smoke of the exact NULL config, a crash-and-resume test, an independent derangement check, a per-step pairing check against P384 in separate processes, and a synthetic pair-freeze hold-out check including a tamper test. Real training was gated on three things: a D2 pair-freeze record, the D2 amendments in RULES.md, and an explicit GO D2.

## What ran on this branch

Phase 1 only, on 2026-09-26, on a 4-vCPU Cascade Lake container with no AMX (fp32 only). Everything ran on synthetic data: a 96-patch 384 px registry for the smoke and a 24-patch synthetic stage-C tree for the hold-out check. No real data, image or 0841 material was touched, and no weights went to git.

## Outcome

Phase 1 passed every check: final weights were bitwise equal after crash and resume, the derangement had 0 fixed points, batch images were identical to P384 at every step while the labels differed, and 0 held-out ids were loaded. The main step, 12,000 real-data training steps, never started. The D2 amendment (DECL-D2-A1) was never declared, no GO D2 was sent, and the research log records D2 as blocked for lack of a GPU (NOT RUN if no GPU by 2026-11-15). The branch head is a later, unrelated status note: a First Letters pass-3 task on another scroll was blocked and launched nothing (logs/sib/fl3-pherc0175b/STATUS.md).

| key number | meaning | file on this branch |
|---|---|---|
| 148.75 s/step | median step time, NULL arm, P384 full forward, fp32, 4 threads, batch 32 (synthetic smoke) | `logs/sib/d2-null/READY.md` |
| 495.8 h (20.7 days) | projected loop time for 12,000 steps of one arm on this host type at fp32 | `logs/sib/d2-null/READY.md` |
| 9.70 GB | peak RSS of the full-forward smoke | `logs/sib/d2-null/READY.md` |
| 0 fixed points | the NULL derangement over 96 synthetic patches; 96 of 96 patches carry labels that differ from their own | `logs/sib/d2-null/smoke.json` |
| 0.0 | max abs weight difference between the uninterrupted run and the crash-at-step-7, resume-from-step-5 run | `logs/sib/d2-null/smoke.json` |
| 19 loaded, 0 held out | synthetic hold-out check: loaded patches equal the 19-id allowlist and no held-out id was loaded | `logs/sib/d2-null/holdout_check.json` |
| 14 + 12 passed | trainer unit and integration tests at the pinned commit (plus 18 unit tests at the trainer head) | `logs/sib/d2-null/READY.md` |

## Where the records are

- `logs/sib/d2-null/READY.md`
- `logs/sib/d2-null/smoke.json`
- `logs/sib/d2-null/holdout_check.json`
- `logs/sib/d2-null/smoke_configs/`
- `logs/sib/d2-null/runs.jsonl`
- `logs/sib/d2-null/out/`
- `tools/sib/d2-null/`

## Lesson

A CPU arm can be fully validated on synthetic data (pairing, derangement, bitwise resume), but at about 149 s/step a 12,000-step arm needs about 21 days, so D2 could not run without a GPU.

## Related

- sib-trainer
- sib-d2-p128
- sib-d2-p384
- sib-d2-rev
- sib-amx
- DECL-D2
- DECL-D2-A1 (proposal, never declared)
- DECL-AMX-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider --basetemp=/work/pt_units tests/sib_trainer_units_test.py
/opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider --basetemp=/work/pt_integ tests/sib_trainer_integration_test.py
bash tools/sib/d2-null/smoke.sh
/opt/hv-ink/bin/python tools/sib/d2-null/smoke_compare.py
/opt/hv-ink/bin/python tools/sib/d2-null/pair_check.py
/opt/hv-ink/bin/python tools/sib/d2-null/holdout_check.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
