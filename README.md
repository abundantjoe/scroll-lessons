<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="READ-CAL-2 builder (display arms): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# READ-CAL-2 builder (display arms)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-readcal2` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHerc0814, PHercParis4, PHerc0826.

## Question

Prepare a second reading calibration (READ-CAL-2). Does any display arm help fresh blind readers name more consistently perceived letters on known-text reference maps, against a declared NO_GAIN default? The arms were the key sheet, exemplar and placebo sheets, multi-scale, row and sigma variants.

## Method

Builder only: no reader, picker or sealer ran, and no image was viewed. The lane built:
- the arm generators and draft briefs;
- exemplar and placebo sheets at 0.15, 0.30 and 0.45 mm;
- a noise model from the base maps of two blank windows;
- reference-ladder, MS and ROW builders, plus scoring glue;
- a fail-closed candidate bank on PHerc0139, plus PHerc0814 ribbons.

It drafted DECL-READCAL2 and READCAL2-BANK-1, and also a display-scale calibration proposal for known-text PHercParis4 papyrus (p4ms).

## What ran on this branch

2026-09-25 to 2026-09-26 on CPU, official data only (257 downloads hashed):
- 30 unit tests pass.
- Candidate bank: 4016 text and 46 blank windows, a 95-window picker tiling, and 1125 windows held back.
- 78 PHerc0139 reference windows rendered in state A (73 shown, 5 ambiguous-sign windows excluded); not pushed and never viewed.

On 2026-09-30 the branch was reused to launch an FL-2 PHerc0826 pipeline (status and log only).

## Outcome

The builder deliverables are complete. READ-CAL-2 itself was never declared or run: RULES.md has no DECL-READCAL2 entry, so there is no reading result. Findings:
- The earlier picker set could not be reconstructed from the record, so its papyrus was held out fail-closed.
- Blank base maps are not white noise: 82 % of their power lies below 0.01 cycles/px.
- The scoring glue reproduces the D1 sigma_crit.

| key number | meaning | file on this branch |
|---|---|---|
| 4016 / 46 | text / blank candidate windows in the bank (1125 held back) | `logs/sib/readcal2/candidates.json` |
| 30 | unit tests passing for the builders, geometry and scoring | `logs/sib/readcal2/REPORT.md` |
| 82 % | share of blank base-map power below 0.01 cycles/px | `logs/sib/readcal2/REPORT.md` |
| 0.30 / 0.35 mm | D1 sigma_crit reproduced by the scoring glue (discrete / interpolated) | `logs/sib/readcal2/REPORT.md` |

## Where the records are

- `logs/sib/readcal2/REPORT.md`
- `logs/sib/readcal2/report.json`
- `logs/sib/readcal2/STATUS.md`
- `logs/sib/readcal2/ASK.md`
- `logs/sib/readcal2/proposals/DECL-READCAL2.md`
- `logs/sib/readcal2/proposals/READCAL2-BANK-1.md`
- `logs/sib/readcal2/candidates.json`
- `logs/sib/readcal2/noise_psd.json`
- `logs/sib/readcal2/refwin_manifest.json`
- `logs/sib/readcal2/p4ms/PROPOSAL.md`

## Lesson

If a picker set's coordinates exist only in a lost key file, the papyrus has to be held out fail-closed; publish exclusion lists as numbers.

## Related

- DECL-READCAL
- READCAL-FREEZE
- DECL-READCAL-PROBE3
- DECL-D1-A4
- sib-tribunal

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/readcal2/setup_ink_env.sh
/opt/hv/bin/python tools/sib/readcal2/fetch_all.py all
/opt/hv/bin/python tools/sib/readcal2/build_sheets.py
/opt/hv/bin/python -m pytest -q tests/sib_readcal2_builders_test.py tests/sib_readcal2_geom_test.py tests/sib_readcal2_score_test.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
