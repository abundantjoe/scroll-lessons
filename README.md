<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-H 1 um crackle-texture channel: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-H 1 um crackle-texture channel

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-crackle` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can a 1 um 'crackle' texture-energy channel computed from raw 1.129 um CT serve as an independent carbon-ink detector for the Paris 4 title search (DECL-P4-9)?

## Method

A validation gate was pre-registered (gate_plan.json, commit 44b77c3) before any crackle number existed. On the known-text control strip, 16 tiles were drawn by fixed seed from 64 eligible. Per slice: DoG (sigma 1.5 / 6 px), squared, then averaged over 17 slices (+-18.1 um) and resampled to the 1068 px prediction grid. Pixel AUC was measured against the official 1 um model prediction (ink >= pooled p90, background <= p50, 50 um boundary exclusion), with a tile-bootstrap CI and a rot-90 sanity control. The bar was AUC >= 0.70.

## What ran on this branch

2026-09-26, builder role only (numbers, no image viewed): 16 control tiles at level 0 (about 30 s fetch and 24 s DoG per tile), 1,194,031 ink and 6,099,191 background pixels; 7 unit tests pass.

## Outcome

Gate FAIL: pooled AUC 0.584 [0.565, 0.603], below the 0.70 bar. The rot-90 control is at chance (0.485), so the weak association is real: 15 of 16 tiles are above 0.5 and the best reaches 0.659. Per DECL-P4-9 item 2, P4-H stopped: no title-strip tile was computed and there was no census. No other scale was tried after the result.

| key number | meaning | file on this branch |
|---|---|---|
| 0.584 [0.565, 0.603] | pooled pixel AUC of crackle energy vs the official 1 um prediction, tile-bootstrap 95 % CI | `logs/sib/p4-crackle/gate.json` |
| 0.70 | pre-registered pass bar for the AUC | `logs/sib/p4-crackle/gate_plan.json` |
| 0.485 | rot-90 sanity AUC (within 0.50 +- 0.03, passes) | `logs/sib/p4-crackle/REPORT.md` |
| 0.659 | best single-tile AUC of 16 | `logs/sib/p4-crackle/REPORT.md` |

## Where the records are

- `logs/sib/p4-crackle/REPORT.md`
- `logs/sib/p4-crackle/STATUS.md`
- `logs/sib/p4-crackle/gate.json`
- `logs/sib/p4-crackle/gate_plan.json`
- `logs/sib/p4-crackle/unit_tests.txt`
- `tools/sib/p4-crackle/`

## Lesson

Crackle energy at fixed DoG scales carries real but weak ink information on known text, far below what an independent ink channel needs.

## Related

- DECL-P4-9
- DECL-P4-4-A1
- DECL-P4-5-A1
- sib-p4-tiles-b
- P4-CHANNELS-RESULT-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python -m pytest -q tools/sib/p4-crackle/test_crackle.py
python tools/sib/p4-crackle/gate.py <scratch_dir> compute
python tools/sib/p4-crackle/gate.py <scratch_dir> analyse
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
