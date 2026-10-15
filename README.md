<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Reader-free row-structure screen: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Reader-free row-structure screen

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-struct` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0343.

## Question

Can a reader-free numeric screen for regular text rows, at a 3-9 mm row pitch, rank where text-like structure exists on the Paris 4 title strip, validated against known-text controls (P4-I, DECL-P4-8)?

## Method

Each tile was loaded as an array (never viewed) and given S_row: the maximum over orientations of the band power ratio, normalised by the median over orientations. The material threshold T_mat was the p99 of a rot-90 null. A material passed its gate if >= 30 % of non-blank known-text control tiles lay above T_mat within +-10 deg. Materials: M1 (official 2.4 um predictions), M2 (1.129 um predictions) and the E1/E2 raw-CT displays. A Jaccard comparison between materials and validation AUCs were also declared.

## What ran on this branch

The declared run was 2026-09-26 (gates.json at 18:11:58Z). 675 PNGs were sha256-checked with 0 mismatches, and 15 unit tests passed. P4-F was not built, so it was not run. On 2026-09-30 the branch held DECL-FL-1 pipeline code for PHerc0343, which was never launched because the session safety check refused it.

## Outcome

The screen is uninformative by construction. S_row is invariant under a 90-degree rotation, so the rot-90 null equals the data and no material can meet the 30 % gate, whatever the papyrus holds (ASK-1). The gate fails for M1 (2/86 controls) and M2 (2/32). E1 and E2 have no same-material known-text control, so their gate cannot be evaluated (ASK-2). Control vs rot-90 AUC was 0.500 / 0.497, and 0 tiles were STRUCT-positive. An orientation-anchored variant passed 6/6 synthetic tiles (AUC 0.993), where the declared rule passed 0/6. It was coded but never declared or run on real tiles here.

| key number | meaning | file on this branch |
|---|---|---|
| 2/86 (2.3 %) | M1 non-blank controls above T_mat (gate bar 30 %) | `logs/sib/p4-struct/gates.json` |
| 2/32 (6.3 %) | M2 non-blank controls above T_mat | `logs/sib/p4-struct/gates.json` |
| 0.500 / 0.497 | AUC of controls vs their rot-90 copies (chance by construction) | `logs/sib/p4-struct/gates.json` |
| 0 | STRUCT-positive tiles in every material | `logs/sib/p4-struct/positives.json` |
| 0/6 vs 6/6 | synthetic planted-row controls passing: declared rule vs anchored variant | `logs/sib/p4-struct/synthetic_smoke.json` |

## Where the records are

- `logs/sib/p4-struct/REPORT.md`
- `logs/sib/p4-struct/ASK.md`
- `logs/sib/p4-struct/gates.json`
- `logs/sib/p4-struct/struct.json`
- `logs/sib/p4-struct/positives.json`
- `logs/sib/p4-struct/synthetic_smoke.json`
- `logs/sib/p4-struct/tests.txt`
- `tools/sib/p4-struct/`
- `tools/sib/fl-pherc0343/`

## Lesson

Before declaring a null, check that the statistic is not invariant to it: a rot-90 null cannot test a max-over-orientations score.

## Related

- sib-p4-tiles-a
- sib-p4-tiles-b
- sib-p4-highz
- DECL-P4-8
- DECL-P4-5
- DECL-P4-5-A1
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-struct/run_struct.py --data <dir with logs/sib/{p4-tiles-a,p4-tiles-b,pairs0814b/e2,p4-excl,p4-highz/f1}> --out logs/sib/p4-struct
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
