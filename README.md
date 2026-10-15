<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 REV arm trainer setup: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 REV arm trainer setup

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-d2-rev` · ink-model training and checkpoint screening · 2026-09-26..2026-09-26 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

Can the REV control arm of decision D2 (TRAIN-1, fold L-0841: P384 with every 21-slice input stack reversed in depth, labels unchanged, seed 1) be set up so that it is exactly paired with P384 and resumes bitwise, ready for GO D2?

## Method

The session pinned the environment, copied the trainer (commit 8475920) byte-identically, verified the base checkpoint and ran the unit and integration tests. It then ran a 10-step synthetic REV smoke with an interrupt-and-resume test and a dedicated REV pairing check: the inputs must be the exact depth-reverse of P384's, with identical labels, RNG state and sample digests.

## What ran on this branch

Phase 1 only, on 2026-09-26, on a 4-vCPU Cascade Lake container with no AMX (fp32 only). Synthetic data only (40 patches); no real data or image was touched, and no weights were pushed.

## Outcome

Phase 1 passed: units 14/14, integration 12/12, REV pairing with P384 bitwise, save and resume bitwise, 147.8 s/step, 9.1 GiB peak. At fp32 one REV seed would take about 20.5 days for 12,000 steps on this host. The arm never trained: the pair-freeze record, the D2 amendments and GO D2 never arrived, and D2 is recorded as blocked for lack of a GPU.

| key number | meaning | file on this branch |
|---|---|---|
| 147.8 s/step | median step time, REV arm, fp32, 4 threads, batch 32 (synthetic smoke) | `logs/sib/d2-rev/smoke.json` |
| 9.101 GB | peak RSS of the uninterrupted smoke run | `logs/sib/d2-rev/smoke.json` |
| about 20.5 days | projected fp32 time for one REV seed of 12,000 steps on this host | `logs/sib/d2-rev/STATUS.md` |
| 14/14 and 12/12 | trainer unit and integration tests passed | `logs/sib/d2-rev/STATUS.md` |
| true | final weights bitwise equal after interrupt and resume from step 5 | `logs/sib/d2-rev/smoke.json` |

## Where the records are

- `logs/sib/d2-rev/READY.md`
- `logs/sib/d2-rev/STATUS.md`
- `logs/sib/d2-rev/smoke.json`
- `logs/sib/d2-rev/runs.jsonl`
- `logs/sib/d2-rev/out/`
- `tools/sib/d2-rev/`

## Lesson

Host CPU differences (no AMX, slower clock) change per-arm cost by tens of percent, so step time has to be measured on each host before a run is planned.

## Related

- sib-trainer
- sib-d2-p384
- sib-d2-null
- sib-d2-p128
- DECL-D2
- DECL-D2-A1 (proposal, never declared)
- DECL-OFFLOAD-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider tests/sib_trainer_units_test.py
env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider tests/sib_trainer_integration_test.py
bash tools/sib/d2-rev/smoke.sh
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /opt/hv-ink/bin/python tools/sib/d2-rev/rev_pairing_check.py --registry <synthetic registry.json> ...
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
