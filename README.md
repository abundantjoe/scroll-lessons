<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="TRIBUNAL: pre-read fault controls: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# TRIBUNAL: pre-read fault controls

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-tribunal` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHercParis4, PHerc0191.

## Question

Can fail-closed checks run before any reading catch planted pipeline faults without false alarms on clean data, before a reader sees any image? The faults were a window offset, a mirror, swapped depth order, an off-by-one slice, re-traced training papyrus and a wrong voxel size.

## Method

The lane built src/hercules/tribunal:
- a pre-read gate and fault injectors;
- synthetic concentric-sheet worlds;
- canaries and baits, and a batch-validity scorer;
- an empirical-null tile builder;
- certificates that bind display-image hashes to a passed gate.

It then ran three rounds:
1. Synthetic fault suites.
2. REAL-TRIB-1: official CT renders of 12 PHerc0139 windows with real planted faults.
3. REAL-TRIB-2, pre-registered: unrounded thresholds, an empirical-null dry run on clean PHerc0139, gate calibration at 2.399 um, and PHercParis4 tile checks.

## What ran on this branch

2026-09-25 to 2026-09-26:
- synthetic suites of 40 worlds (v1 and two stress settings);
- REAL-TRIB-1 on 12 windows;
- REAL-TRIB-2;
- the full test suite, 701 passed.

On 2026-09-30 the branch was reused to write FL-1 pass-2 pipeline scripts for PHerc0191. They were not launched, because the permission check refused the detached run.

## Outcome

- Synthetic suites: every fault was caught by its own check 40/40, with 0/40 clean false alarms. The suite exposed a defect in the literal re-trace rule (only 4 of 200 re-traces caught), which became CORR-RETRACE-RULE.
- REAL-TRIB-1 PASSES: clean 12/12 and each fault 12/12. Its thresholds were proposed, not declared.
- REAL-TRIB-2 is mixed. The empirical-null dry run was INSUFFICIENT (4 tiles where >= 40 were needed). At 2.4 um the gate passes clean 12/12 and faults 60/60, but the margins stay below 3x (min 1.15x) and the 9 um-derived slice threshold raises a false alarm on clean data. The PHercParis4 tile checks PASS.

| key number | meaning | file on this branch |
|---|---|---|
| 40/40 | each planted fault caught by its own check in the synthetic v1 suite (clean false alarms 0/40) | `logs/sib/tribunal/faultsuite.json` |
| 4/200 | re-traces caught by the literal vertex-distance rule, the defect behind CORR-RETRACE-RULE | `logs/sib/tribunal/REPORT.md` |
| 12/12 | REAL-TRIB-1 clean windows passing and each real fault caught | `logs/sib/tribunal/real_trib1.json` |
| 1.15x | minimum margin of the gate at 2.4 um (pre-registered need >= 3x) | `logs/sib/tribunal/real_trib2/gate_2p4um.json` |
| 4 | band tiles available for the empirical-null dry run (>= 40 needed, INSUFFICIENT) | `logs/sib/tribunal/REPORT.md` |

## Where the records are

- `logs/sib/tribunal/REPORT.md`
- `logs/sib/tribunal/STATUS.md`
- `logs/sib/tribunal/results.json`
- `logs/sib/tribunal/faultsuite.json`
- `logs/sib/tribunal/real_trib1.json`
- `logs/sib/tribunal/real_trib2/`
- `src/hercules/tribunal/`

## Lesson

Planting real faults exposed a hole in the team's own re-trace rule before anything relied on it.

## Related

- CORR-RETRACE-RULE
- DECL-HARNESS
- sib-readcal2
- sib-rh-e1
- sib-rh-e2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/tribunal/setup_render.sh
env PYTHONPATH=src OMP_NUM_THREADS=2 /opt/hv/bin/python tools/sib/tribunal/real_trib1.py /work/tribunal/rt1 /work/tribunal/s3 logs/sib/tribunal/meshes_fetched.json logs/sib/tribunal/real_trib1_raw.json
/opt/hv/bin/python tools/sib/tribunal/analyse_real_trib1.py logs/sib/tribunal/real_trib1_raw.json logs/sib/tribunal/real_trib1.json
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
