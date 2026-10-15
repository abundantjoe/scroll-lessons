<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Iron-pigment (ochre) title detector: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Iron-pigment (ochre) title detector

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-fe` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Could a Paris 4 title written in an iron-based pigment (red or yellow ochre, green earth) be detected in the published raw CT of the title strip? If so, does the strip show any such signal?

## Method

Step 1 was a cited physics memo: thermal stability at 300-400 C, grain size, and attenuation at 78 keV, which puts standard ochre ink at 4.5x papyrus in electron density and 10.9x in mu. A stroke matched-filter detector then counted a clipped intensity band within +-20 um of the mesh. Its parameters were frozen in params.json from a control-only calibration before any title-strip number existed. Validation used injection-recovery: synthetic Greek-capital letters (2-4 mm tall, 0.3-0.6 mm strokes) were planted at 2/5/10/20 um in three contrast regimes, at 12 locations per material. False positives were measured on the carbon-ink known-text control and a rot-90 null. Only then were the title-strip tiles scored at 1.129 um (E1) and 2.4 um (E2) (DECL-P4-10 steps 1-4, DECL-P4-12 addendum).

## What ran on this branch

This ran 2026-09-26 to 2026-09-27, numbers only, streaming public CT chunks without viewing any image. This branch ran the 1.129 um family: 63 control tiles (C) and 60 title-strip tiles (E1). The 2.4 um family (188 control tiles C2, 160 title tiles E2) was run by sub-sibling p4-pig-fe-e2 with the identical frozen code. Sub-sibling p4-pig-fe-e1 re-ran the E1 maps independently.

## Outcome

The detector is INSENSITIVE at the plausible ochre thickness of 5-10 um. In the electron-density regimes it recovered 0/12 letters at every thickness up to 20 um, on all four materials. In the optimistic mu regime the detection limit is 20 um (C, E1, E2) and 10 um (C2). The title-strip score distributions match the carbon-ink control. Each strip has one tile marginally above theta, as the ~1 % null rate predicts, and both are labelled-adjacent, so there are 0 strict hotspots and no lead. This rules out only mu-regime ochre letters >= 20 um thick on the traced surface; it is a detector limit, not evidence of absence.

| key number | meaning | file on this branch |
|---|---|---|
| 0/12 | letters recovered in the standard electron-density regime (x4.5) at 5, 10 and 20 um, on C, E1, C2 and E2 | `logs/sib/p4-pig-fe/REPORT.md` |
| 20 um / 10 um | mu-regime detection limit (sensitivity >= 0.8) on C, E1, E2 / on C2 | `logs/sib/p4-pig-fe/REPORT.md` |
| 14.016 / 13.844 | hotspot threshold theta (p99 of control) for the 1.129 um / 2.4 um family | `logs/sib/p4-pig-fe/summary.json` |
| 1/63 and 2/188 | leave-one-out false positives on the 1.129 um / 2.4 um known-text controls | `logs/sib/p4-pig-fe/summary.json` |
| 14.63 / 14.04 | maximum title-strip tile z on E1 / E2, at the level the null predicts (control max 14.23 / 16.16) | `logs/sib/p4-pig-fe/REPORT.md` |
| 0 | DECL-P4-10 strict (non-labelled-adjacent) hotspots on both title strips | `logs/sib/p4-pig-fe/hotspots.json` |

## Where the records are

- `logs/sib/p4-pig-fe/REPORT.md`
- `logs/sib/p4-pig-fe/summary.json`
- `logs/sib/p4-pig-fe/scores.json`
- `logs/sib/p4-pig-fe/hotspots.json`
- `logs/sib/p4-pig-fe/MEMO.md`
- `logs/sib/p4-pig-fe/params.json`
- `logs/sib/p4-pig-fe/calib_control.json`
- `logs/sib/p4-pig-fe/1129/`
- `logs/sib/p4-pig-fe/24/`
- `tools/sib/p4-pig-fe/`

## Lesson

Natural surface structure already scores 9-16 sigma, so a clean strip from a detector that cannot see the plausible layer thickness reflects the detector's limit, not absence.

## Related

- sib-p4-pig-fe-e1
- sib-p4-pig-fe-e2
- sib-p4-pig-gold
- sib-p4-pig-red
- sib-p4-highz
- DECL-P4-10
- DECL-P4-12
- DECL-P4-5
- DECL-P4-6

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-pig-fe/calib.py <scratch>
python tools/sib/p4-pig-fe/run_family.py <control> <title> <scratch> <branch> [nloc]
python tools/sib/p4-pig-fe/final.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
