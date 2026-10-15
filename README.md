<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Purple and organic title inks: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Purple and organic title inks

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-purple` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0125.

## Question

The owner asked how a purple (or organic or lake) title that looks invisible on CT could be captured. Can such inks be seen in the published Paris 4 scans, and by which channel (DECL-P4-16 items 1, 3, 4)?

## Method

The lane built an xraylib physics table for 25 colourants at 5/10/20 um, with mu at 78 and 137 keV and the Paganin phase term, bracketing papyrus density. It delegated two parts to sub-siblings. p4-purple-de ran a dual-energy 78/137 keV feasibility study, designed on the known-text control and frozen as DUAL_FREEZE.md. p4-purple-mo ran a colour-agnostic morphology gate on the control. The lane merged both, wrote hypothesis-register additions, and had de apply the frozen dual-energy method once to the title zone after the METRIC-HASH (METRIC-HASH-40).

## What ran on this branch

This ran 2026-09-26 21:48Z to 2026-09-27 13:50Z, numbers only. Both sub-siblings stopped at usage limits and were resumed. On 2026-09-30 the branch was reused by a DECL-FL-1 First Letters worker for PHerc0125. It launched an auto-grow pipeline whose first run was VOID (a missing-directory bug) and relaunched it after three tooling fixes. The branch records only the first kept grow (26.3 cm2, 0 self-crossings) and no further output.

## Outcome

In the published 2.4 um Paganin volume, a purple, lake or organic deposit shows by electron density at 0.9-1.4x carbon ink of equal thickness. It is visible as a deposit, but it cannot be told apart from the black text. Dual energy detects only CuO, orpiment and gold at 10-20 um. Tyrian purple, purpurissum and lakes are undetectable at <= 20 um. The morphology gate FAILED (0/9 tests). The single title-zone dual-energy application was NULL: hotspot rate 0.0001 against a control FPR of 0.0215. That excludes only Cu/As/Au layers >= 10 um on the part of the zone that the 137 keV scan covers. A purple title is 'untestable with published data', not absent. A dye with no thickness needs XRF or hyperspectral imaging, which only the organizers can do.

| key number | meaning | file on this branch |
|---|---|---|
| 25 | colourants modelled at 5/10/20 um, 78 and 137 keV | `logs/sib/p4-purple/colourants.json` |
| 0.9-1.4x | purple/lake/organic deposit contrast relative to carbon ink of equal thickness (Paganin volume) | `logs/sib/p4-purple/REPORT.md` |
| 0/9 | morphology gate tests passed (sub-sibling mo) | `logs/sib/p4-purple/REPORT.md` |
| 0.48 | dual-energy AUC on known-text carbon ink (chance; no composition difference) | `logs/sib/p4-purple/REPORT.md` |
| 0.0001 vs 0.0215 | title-zone dual-energy hotspot rate vs control false-positive rate (NULL) | `logs/sib/p4-purple/STATUS.md` |

## Where the records are

- `logs/sib/p4-purple/REPORT.md`
- `logs/sib/p4-purple/STATUS.md`
- `logs/sib/p4-purple/COLOURANTS.md`
- `logs/sib/p4-purple/colourants.json`
- `logs/sib/p4-purple/DUAL_FREEZE.md`
- `logs/sib/p4-purple/REGISTER_ADD.md`
- `logs/sib/p4-purple/SUBSIBS.md`
- `tools/sib/p4-purple/`
- `logs/sib/fl-pherc0125/`

## Lesson

Colour is invisible to CT, so separate what a channel cannot see ('untestable') from what it saw and found empty ('absent').

## Related

- sib-p4-purple-de
- sib-p4-purple-mo
- sib-p4-highz
- DECL-P4-16
- DECL-P4-6-A3
- METRIC-HASH-40
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-purple/colourants.py <repo>
python tools/sib/p4-purple/colourants_md.py <repo>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
