<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-J copper-pigment family (CU): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-J copper-pigment family (CU)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-cu` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **INCOMPLETE** · verdict **UNKNOWN**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0826.

## Question

Could a copper-based blue or green pigment title (Egyptian blue; azurite or malachite turned to CuO; verdigris) be detected in the Paris 4 raw CT? The test was to be validated by injection-recovery (DECL-P4-10, family CU).

## Method

A research memo covered thermal stability and grain size, with NIST SRD 126 attenuation physics and a grey-level calibration on the control only. The grain detector was frozen (params_freeze.json) before any inner-strip number: 26-connected components above T_g, per-cell occupancy at 0.1 mm, stroke smoothing, local-median background, and letter-scale clusters scored by z-sum. The plan was to score four materials (E1, E2 and controls C1, C2) and run injection-recovery in each.

## What ran on this branch

2026-09-26 to 2026-09-30. Scored on this branch: E2 160/160, C2 31, C1 5, E1 0. Injections: E2 12/12, C2 12/12, E1 8/12, C1 1/12. Three sub-sibling sessions were created to split the scoring; their results are on their own branches and were never merged here. A container restart on 2026-09-30 killed all jobs. The branch was then reassigned as First Letters worker fl3-pherc0826 (pipeline launched).

## Outcome

No thresholds, report or verdict were produced. Pre-freeze control checks: the permutation null scored 0 on 7 control tiles, and an injected Egyptian-blue letter scored about 1000-1600 against 0-83 for blank blocks. Physics: Egyptian blue attenuates 11.4x papyrus at 78 keV, close to common minerals (augite 10x, calcite 8x), so intensity alone cannot separate them; Cu offers no K-edge test at the Paris 4 energies.

| key number | meaning | file on this branch |
|---|---|---|
| 160/160 | E2 tiles scored with the frozen detector | `logs/sib/p4-pig-cu/scores/E2/scores_E2.jsonl` |
| 31 / 5 / 0 | C2 / C1 / E1 tiles scored on this branch when work stopped | `logs/sib/p4-pig-cu/STATUS.md` |
| 11.4x | Egyptian blue linear attenuation relative to papyrus at 78 keV | `logs/sib/p4-pig-cu/STATUS.md` |
| ~1000-1600 vs 0-83 | injected Egyptian-blue letter score vs blank control blocks (pre-freeze check) | `logs/sib/p4-pig-cu/STATUS.md` |

## Where the records are

- `logs/sib/p4-pig-cu/STATUS.md`
- `logs/sib/p4-pig-cu/MEMO.md`
- `logs/sib/p4-pig-cu/ASK.md`
- `logs/sib/p4-pig-cu/SUBSIBS.md`
- `logs/sib/p4-pig-cu/physics.json`
- `logs/sib/p4-pig-cu/calib.json`
- `logs/sib/p4-pig-cu/params.json`
- `logs/sib/p4-pig-cu/params_freeze.json`
- `logs/sib/p4-pig-cu/t2_control.json`
- `logs/sib/p4-pig-cu/scores/`
- `logs/sib/p4-pig-cu/injection/`
- `logs/sib/fl3-pherc0826/STATUS.md`
- `tools/sib/p4-pig-cu/`

## Lesson

Sub-lane scores computed on separate branches were never merged back, so the parent stopped without the material needed for a verdict.

## Related

- DECL-P4-10
- DECL-P4-12
- sib-p4-pig-cu-a
- sib-p4-pig-cu-b
- sib-p4-pig-cu-c
- sib-p4-highz
- sib-p4-pig-fe
- sib-p4-pig-red
- sib-p4-pig-gold
- fl3-pherc0826

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/p4-pig-cu/run_all.sh
bash tools/sib/p4-pig-cu/inj_all.sh
python3 tools/sib/p4-pig-cu/cu.py score M 0-99 logs/sib/p4-pig-cu/scores/M
python3 tools/sib/p4-pig-cu/inject.py M logs/sib/p4-pig-cu/injection/inj_M.jsonl
python tools/sib/p4-pig-cu/analyze.py [--onsheet-dir DIR]
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
