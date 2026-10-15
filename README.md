<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Dual-energy 78/137 keV feasibility: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Dual-energy 78/137 keV feasibility

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-purple-de` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can the published 78 keV and 137 keV 2.4 um Paris 4 scans be combined to detect a high-Z or bromine-bearing (Tyrian purple) title ink? The method was to be designed on the known-text control only and then applied once to the title zone (DECL-P4-16 item 3).

## Method

The lane first inventoried both volumes' published metadata. For the title strip it computed geometry only, under a hard fence: no 137 keV byte from the strip until the orchestrator recorded the METRIC-HASH. On the control alone it refined the registration by 3-D block matching with an affine correction, checked on held-out blocks. The grey-to-mu unit calibration failed, so the decomposition used an empirical papyrus line (k 0.679). The detector is a depth-column residual z per 0.2 mm patch, with a hotspot at |z| > 3.07 on-sheet. Validation on 40 held-out sites covered carbon-ink AUC, a rot-90 null, the false-positive rate and a misregistration test, plus pigment injection (480 patches per cell). The method was frozen as DUAL_FREEZE.md, and the title zone was then scanned once with apply.py.

## What ran on this branch

This ran 2026-09-26 21:57Z to 2026-09-27 12:45Z, numbers only. 1.29 M control vertices lay inside the 137 keV extent. The application covered 1,781 blocks and 39,242 patch records (37,202 used). It resumed after a usage-limit stop and a container restart without recomputing any block.

## Outcome

Registration: held-out residual 1.7 um median and 3.2 um p90; sheet-surface residual 2.4 um median, below the 5 um goal. The unit calibration failed. Carbon-ink AUC was 0.48, as expected since carbon ink differs in no composition the method sees. The false-positive rate was 0.022 per patch, rising to 0.118 with 250 um misregistration. Only CuO, orpiment and gold are detectable at 10-20 um; Tyrian purple (any bromine loss), purpurissum, lakes, carbon ink, ochre, cinnabar and lead white are not detectable at <= 20 um. The title-zone application was NULL: hotspot rate 0.0001 against the control's 0.0215. A drift artefact where the 137 keV volume extends beyond the control domain was reported, not fixed. Only 3.01 % of the title strip's mesh vertices lie inside the 137 keV extent.

| key number | meaning | file on this branch |
|---|---|---|
| 3.01 % | title-strip mesh vertices inside the 137 keV extent (geometry only) | `logs/sib/p4-purple/de/overlap.json` |
| 1.7 um / 3.2 um | registration residual on held-out blocks, median / p90 | `logs/sib/p4-purple/de/registration.json` |
| 0.48 | known-text carbon-ink AUC [0.33, 0.63] | `logs/sib/p4-purple/de/validation.json` |
| 0.022 | false-positive rate per patch (nominal 0.01) | `logs/sib/p4-purple/de/validation.json` |
| 11,674 | title-zone patches used in the single frozen application | `logs/sib/p4-purple/de/title_zone.json` |
| 0.0001 | title-zone hotspot rate vs control FPR 0.0215 (NULL) | `logs/sib/p4-purple/de/title_zone.json` |

## Where the records are

- `logs/sib/p4-purple/de/REPORT.md`
- `logs/sib/p4-purple/de/DUAL_FREEZE.md`
- `logs/sib/p4-purple/de/PROTOCOL.md`
- `logs/sib/p4-purple/de/STATUS.md`
- `logs/sib/p4-purple/de/APPLY.md`
- `logs/sib/p4-purple/de/title_zone.json`
- `logs/sib/p4-purple/de/title_zone_diag.json`
- `logs/sib/p4-purple/de/validation.json`
- `logs/sib/p4-purple/de/apply/patches.jsonl.gz`
- `tools/sib/p4-purple/de/`

## Lesson

Fence the target region at the byte level until the method is hash-frozen, and design and validate only on a control.

## Related

- sib-p4-purple
- sib-p4-purple-mo
- sib-p4-highz
- DECL-P4-16
- METRIC-HASH-40

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-purple/de/inventory.py
python tools/sib/p4-purple/de/overlap.py <scratch>
python tools/sib/p4-purple/de/reg.py <scratch>
python tools/sib/p4-purple/de/sites.py <scratch>
python tools/sib/p4-purple/de/labels.py <scratch>
python tools/sib/p4-purple/de/analyze.py fit <scratch>
python tools/sib/p4-purple/de/analyze.py validate <scratch>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
