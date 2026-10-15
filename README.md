<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="PHerc0009B registration and bank prep: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# PHerc0009B registration and bank prep

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-reg0009b` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **PASSED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0009B, PHerc0490B.

## Question

Can the 2.401 um reference ink maps of the fragment PHerc0009B be registered onto its 8.64 um canvas? How much independent known-text material (windows and papyrus units) does it give a KTLB-M letter bank and the DEV loop?

## Method

Numbers only, official data. Steps:
- A registration gate per segment, with depth correction: whole-segment NCC >= 0.80 after correction and median residual tile shift <= 2 px.
- Re-trace grouping into papyrus units under CORR-RETRACE-RULE (fail-closed).
- Dense-ink 2 x 2 cm candidate windows, deduplicated in 3-D.
- A devzone measurement of the DEV material left outside the candidate windows plus a 144-vox clearance.

## What ran on this branch

2026-09-25 to 2026-09-26:
- Inventory of 20 segment prefixes (201 objects, 903,122,426 B).
- Registration of 18 segments; 119 nearby segment pairs tested for same papyrus.
- devzone under two readings of the clearance unit.
- A DEV-registry extension proposal after the orchestrator's ruling.

On 2026-09-30 the branch was reused to launch an FL-2 PHerc0490B pipeline (status only).

## Outcome

Registration passes on 18/18 segments, but only with depth correction: at the nominal slab centre, 13 of 18 fall below NCC 0.80. 28 of 119 pairs are the same papyrus, which gives 6 papyrus units, and there are 23 deduplicated candidate windows. Under the ruled clearance, PHerc0009B supplies no text DEV window: the primary option is one 1 x 2 cm window without text plus 6 blanks.

| key number | meaning | file on this branch |
|---|---|---|
| 18/18 | segments passing the registration gate after depth correction | `logs/sib/reg0009b/REPORT.md` |
| 13 of 18 | segments below NCC 0.80 at the nominal slab centre (no depth correction) | `logs/sib/reg0009b/REPORT.md` |
| 28 of 119 | segment pairs judged SAME papyrus (6 papyrus units) | `logs/sib/reg0009b/summary.json` |
| 23 | deduplicated 2 x 2 cm dense-reference-ink candidate windows | `logs/sib/reg0009b/REPORT.md` |

## Where the records are

- `logs/sib/reg0009b/REPORT.md`
- `logs/sib/reg0009b/summary.json`
- `logs/sib/reg0009b/STATUS.md`
- `logs/sib/reg0009b/ASK.md`
- `logs/sib/reg0009b/devzone.json`
- `logs/sib/reg0009b/windows.json`
- `logs/sib/reg0009b/proposals/DECL-DEVLOOP-0009B-EXT-proposal.md`
- `logs/sib/reg0009b/reg/`

## Lesson

Registration passed only after correcting the slab depth; a check at the nominal centre would have failed 13 of 18 segments.

## Related

- sib-reg0841
- sib-regrescan
- DECL-DEVLOOP-A1
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/fetch.py
tools/sib/reg0009b/pipeline.sh
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/overlap.py 9
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/windows.py
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/dedupe.py
/opt/hv/bin/python -m pytest -q tests/sib_reg0009b_test_rule.py tests/sib_reg0009b_test_ncc.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
