<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Submission gate (SG) as code: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Submission gate (SG) as code

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-sg` · ink-model training and checkpoint screening · 2026-09-25..2026-09-26 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Can every bar of the submission gate (DECL-SG items 0-14) and the discovery and empirical-null rules (DECL-EMPNULL) be implemented as mechanical, unit-tested code that fails closed?

## Method

The session encoded each bar as a constant citing its item, and implemented the discovery rule with FDR calibration, the 4 cm^2 R rectangle rule, SG items 1-7, 9, 11, 13 and the rotation part of 14, and a CLI with exit codes. Items 0, 8, 10, 12 and the rest of 14 are attestations that need a RULES.md record. A synthetic null measured the SG 7 copy-test statistic. Follow-ups added an SG 11 REF-calibration runner (coded, not run), a licence-lineage checker, and DRY RUN First Letters and Paris 4 submission kits with owner-only fields left empty.

## What ran on this branch

From 2026-09-25 to 2026-09-26: unit tests, a synthetic known-answer SG run, the SG 7 null sweep, a label-height survey and a line-spacing survey on PHerc0139 organizer labels and predictions (calibration only), live prize-page fetches, and the kit dry runs. No real candidate was ever evaluated.

## Outcome

Delivered as SG code v1.2.0: the merged-layout suite gave 721 passed, 7 skipped, 0 failed (726 after the follow-up package). The synthetic known-answer run passed all items, and each computed item has a test in which it alone fails. Findings: the SG 7 copy test flags genuine letters by chance at low n_eff; only 75-78 % of 68 official PHerc0139 label blobs lie in 2-4 mm, which led to a median-only SG 11 height bar; and the base lineage is BLOCKS for permissive release (CC BY-NC 4.0 data). The SG code was never applied to a real candidate on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 721 passed, 7 skipped | merged-layout test suite for SG code v1.2.0 (726 passed after the sg-pkg2 additions) | `logs/sib/sg/REPORT.md` |
| 122 passed | SG-specific tests (gate, region, copy test, CLI) | `logs/sib/sg/REPORT.md` |
| PASS (all items) | synthetic known-answer SG run | `logs/sib/sg/synthetic_pass_result.json` |
| n_eff <= 13: all flagged; n_eff >= 30: none | SG 7 copy-test false-flag behaviour on independent smooth fields | `logs/sib/sg/copytest_null.json` |
| 0.75-0.78 of 68 | fraction of official PHerc0139 label blobs within 2-4 mm | `logs/sib/sg/label_survey_0139.json` |
| BLOCKS | overall licence lineage of the base model and data for permissive release | `logs/sib/sg/licence/lineage_base_ink9um.json` |

## Where the records are

- `logs/sib/sg/REPORT.md`
- `logs/sib/sg/STATUS.md`
- `logs/sib/sg/ASK.md`
- `logs/sib/sg/sg_report.json`
- `logs/sib/sg/synthetic_pass_result.json`
- `logs/sib/sg/copytest_null.json`
- `logs/sib/sg/proposals/`
- `logs/sib/sg/licence/`
- `logs/sib/sg/submit_kit/`
- `logs/sib/sg/p4kit/`
- `tools/sib/sg/`

## Lesson

The SG 7 copy test can fail a genuine letter by chance when n_eff is low, so n_eff has to be reported with every copy test.

## Related

- sib-factory
- sib-tribunal
- DECL-SG
- DECL-EMPNULL
- DECL-KILL
- DECL-SG11-REFCAL-1 (proposal)
- DECL-P4-2
- DECL-P4-2-A1
- DECL-P4-2-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
env PYTHONPATH=tools/sib/sg/submit_kit /opt/hv/bin/python tools/sib/sg/submit_kit/generate.py --sg logs/sib/sg/synthetic_pass_result.json --manifest tools/sib/sg/submit_kit/dryrun_manifest.json
python tools/sib/sg/submit_kit/p4_generate.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
