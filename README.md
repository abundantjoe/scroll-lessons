<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Colour-agnostic morphology gate: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Colour-agnostic morphology gate

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-purple-mo` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can ink be detected from sheet morphology alone, whatever its colour, so that a purple or organic title could be found? The candidate cues were face height (relief), thickness, indentation, roughness and crackle at the face. Each was to be validated on the known-text control before any title-strip use (DECL-P4-16 item 4).

## Method

A protocol was pre-registered before any feature number. Amendment A1 (a sheet anchor) followed a dev-tile face-fraction trigger and came before any control or gate number. The lane ran 9 declared tests on the 2.4 um surface volume (level 0) of the known-text control segment: 16 gate tiles (seed 20260928) in 19.2 um cells. No human ink labels exist there, so labels came from the official 2.4 um prediction (ink >= p90, background <= p50). Each test was scored by AUC with Bonferroni(9) intervals and rot-90 nulls. A positive control planted 10 and 20 um deposits.

## What ran on this branch

This ran 2026-09-26 to 2026-09-27 02:11Z, numbers only, streaming about 120 GB. It scored 1,351,721 ink cells and 6,986,386 background cells. No title-strip number was computed.

## Outcome

GATE FAIL: 0 of 9 tests passed. The best cue was crackle at the + face, AUC 0.656 [0.636, 0.675]. Relief and thickness scored 0.48-0.53, and the nulls 0.47-0.53. The positive control also failed by the declared rule: a planted 10 um deposit was measured correctly (7.3 / 6.4 um), but its glyph AUC was only 0.60 / 0.58 (0.68 / 0.65 at 20 um) against a 0.90 bar. Natural face-height variability therefore sets a floor, and a relief-only title below about 20 um is under this pipeline's per-cell detection limit. No morphology channel became a candidate channel.

| key number | meaning | file on this branch |
|---|---|---|
| 0/9 | morphology tests passing the gate | `logs/sib/p4-purple/mo/gate.json` |
| 0.656 | best AUC (F5+ crackle at the + face), below the bar | `logs/sib/p4-purple/mo/gate.json` |
| 0.60 / 0.58 | positive-control glyph AUC for a planted 10 um deposit (bar 0.90) | `logs/sib/p4-purple/mo/posctl.json` |
| 1,351,721 / 6,986,386 | ink / background cells scored | `logs/sib/p4-purple/mo/REPORT.md` |
| 0.47-0.53 | range of the 9 rot-90 null AUCs | `logs/sib/p4-purple/mo/REPORT.md` |

## Where the records are

- `logs/sib/p4-purple/mo/REPORT.md`
- `logs/sib/p4-purple/mo/PROTOCOL.md`
- `logs/sib/p4-purple/mo/gate.json`
- `logs/sib/p4-purple/mo/posctl.json`
- `logs/sib/p4-purple/mo/tface.json`
- `logs/sib/p4-purple/mo/unit_tests.json`
- `logs/sib/p4-purple/mo/runs.jsonl`
- `tools/sib/p4-purple/mo/`

## Lesson

A positive control that measures the planted relief correctly yet stays near chance shows the limit is the sheet's natural variability, not the code.

## Related

- sib-p4-purple
- sib-p4-purple-de
- sib-p4-crackle
- DECL-P4-16

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-purple/mo/dev.py <scratch> tface
python tools/sib/p4-purple/mo/dev.py <scratch> posctl
python tools/sib/p4-purple/mo/gate.py <scratch> compute <worker> <n_workers>
python tools/sib/p4-purple/mo/gate.py <scratch> analyse
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
