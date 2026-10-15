<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Tracing census plan, 11 JULY volumes: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Tracing census plan, 11 JULY volumes

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-census` · First Letters push · 2026-09-25..2026-10-01 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0125, PHerc0191, PHerc0211, PHerc0257, PHerc0358, PHerc0813, PHerc0826, PHerc0846A, PHerc0846B, PHerc1203, PHerc1545, PHerc0490A, PHercParis4.

## Question

Which of the 11 eligible 9.362 um JULY volumes are most tractable for seeded tracing with the organizer grower, and what would a 60-seed-per-volume tracing census cost in data, disk and time?

## Method

Geometry and CT masks only (no ink model, no tracing, no image viewed). Listed every official surface prediction (m7), normal-grid, lasagna and umbilicus product; measured CT-mask shape at pyramid level 4; took the centre from the official umbilicus where present, otherwise the mask centroid calibrated against the 3 umbilicus volumes; placed 60 seeds per volume (20 z-levels x 3 angles) with admissibility checks; validated duplicate-detection walkers on known same-sheet pairs; built sync plans and run sheets; ranked volumes by a formula declared in ASK.md before any number existed.

## What ran on this branch

Census plan 2026-09-25 (tools/sib/census/, 6 unit tests). The same session then served as a helper: Paris 4 own-model map tiles with reproducibility checks and verso/forward maps (2026-09-30/10-01), a second FL-2 worker on PHerc1203 (8 organizer segments and 4 auto-grown seeds, 52 official ink_9um tiles, 2026-10-01), and FL-4 lane 13 of PHerc0490A (2 grows, 1 segment with GP passes in both directions) until the usage limit stopped the fleet on 2026-10-01.

## Outcome

Plan delivered (REPORT.md, STATUS: DONE): all 11 volumes have complete m7 predictions and normal grids; 654 of 660 planned seeds placed, all passing every check; ranking 0191, 0813, 0211, 0826, 0257, 0125, 0358, 1545, 0846B, then 1203 and 0846A by rule; 5 volumes flagged UNRELIABLE for the centroid centre. The pre-trace duplicate walker is low-reliability, so the binding duplicate test was set after tracing (CORR-RETRACE-RULE form b). The tracing run itself is not on this branch. The FL-2 PHerc1203 tiles fed the central census (0 positives, uninformative gate); the PHerc0490A FL-4 outputs were never read (DECL-FL-4-A3) and are void under DECL-FL-4-A5.

| key number | meaning | file on this branch |
|---|---|---|
| 654 of 660 | planned seeds placed across the 11 volumes, all passing every check | `logs/sib/census/REPORT.md` |
| 13 of 35 vs 5 of 30 (AUC 0.60) | walker v2 SAME calls on determined same-sheet positives vs adjacent-sheet negatives | `logs/sib/census/REPORT.md` |
| 298-386 vox | median centroid-centre error against the official umbilicus on 0125, 0211 and 0826 | `logs/sib/census/REPORT.md` |
| 1.08 h / 3.01 h | time for 60 seeds at 4 in parallel at 45 / 75 generations (measured-scaled) | `logs/sib/census/REPORT.md` |
| 17 | PHerc1203 organizer segments ranked for the FL-2 split after excluding 116 version snapshots and 5 T0 ids | `logs/sib/census/fl2/organizer_selection.json` |
| 52 (20 organizer, 32 auto-grown) | official-model FL-2 tiles over 12 tile manifests under fl2/ | `logs/sib/census/fl2/STATUS.md` |

## Where the records are

- `logs/sib/census/REPORT.md`
- `logs/sib/census/census.json`
- `logs/sib/census/seeds/`
- `logs/sib/census/sync/`
- `logs/sib/census/runsheet/`
- `logs/sib/census/runs.jsonl`
- `logs/sib/census/fl2/`
- `logs/sib/census/fl4/PHerc0490A/`
- `tools/sib/census/`

## Lesson

Validate a pre-trace duplicate detector on known pairs before trusting its counts; here it reached only AUC 0.60, so the binding test was moved after tracing.

## Related

- claude/gifted-bell-gavnl5 (research log)
- sib-tracer
- sib-fl-pherc1203
- CORR-RETRACE-RULE
- DECL-P4-25-A10-A1
- DECL-P4-25-A14
- DECL-P4-25-A16
- DECL-P4-26-A2
- DECL-FL-2
- FL2-WAVE1-RESULT
- FL3-W1-RESULT
- DECL-FL-4-A1
- DECL-FL-4-A3
- DECL-FL-4-A5

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
env PYTHONPATH=src /opt/hv/bin/python tools/sib/census/list_products.py --out /work/census/products
/opt/hv/bin/python tools/sib/census/mask_shape.py --out /work/census/mask --vols 0125 0211 0826 0191 0257 0358 0813 0846A 0846B 1203 1545
env PYTHONPATH=src /opt/hv/bin/python -u tools/sib/census/plan_seeds.py --mask /work/census/mask --umb /work/census/umb --out /work/census/seeds --vols <vols>
env PYTHONPATH=src /opt/hv/bin/python -u tools/sib/census/validate_walker.py --walker v2 --archive /work/census/team1203_dev_meta.json --mask /work/census/mask --out /work/census/valwalk_v2.json
env PYTHONPATH=src /opt/hv/bin/python tools/sib/census/build_report.py
/opt/hv/bin/python -m pytest -q tests/sib_census_test_geometry.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
