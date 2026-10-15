<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Rescan registration, 1203 and 0846A: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Rescan registration, 1203 and 0846A

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-regrescan` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc1203, PHerc0846A, PHerc0490A.

## Question

Can the 2.403 um rescan band of each eligible scroll (PHerc1203, PHerc0846A) be mapped to its 9.362 um volume by a single affine? The pre-registered bars were held-out median r >= 0.85 AND RMS <= 1.5 vox on 16 new patches, with a clear drop for a shifted control.

## Method

CT-to-CT only. A remount and orientation search at 600 um, coarse and mid fits, then a fine affine fit on 24 patches. The model is q = F(p + M(p - Pm) + b - z0 e_z), with F taken from the metadata.json files. The fit was checked once on 16 pre-fixed held-out patches with a shifted control, and a round-trip test went 9 -> 2.4 -> 9 um.

## What ran on this branch

2026-09-25 to 2026-09-26: both scrolls were fitted and checked, and 29 unit tests pass. For PHerc0846A, two fits were each checked once on the same patches: the refit (iteration 2) and the committed iteration-1 fit that the orchestrator specified.

On 2026-09-30 the branch was reused to write an FL-1 pass-2 pipeline for PHerc0490A. It was not launched, because the permission check refused the detached launch.

## Outcome

Split result:
- PHerc1203 PASSES: held-out median r 0.879, RMS 0.732 vox, control 16/16.
- PHerc0846A FAILS on median r (0.844 < 0.85) under either fit iteration; its RMS (0.720 vox) and control pass.

No flip or axis permutation was found on either scroll. The round trip is exact to 1.82e-12 vox, with a median of 0.127 vox after rounding to stored voxels.

| key number | meaning | file on this branch |
|---|---|---|
| 0.879 | PHerc1203 held-out median r (PASS) | `logs/sib/regrescan/summary.json` |
| 0.844 | PHerc0846A held-out median r, below the 0.85 bar (FAIL) | `logs/sib/regrescan/REPORT.md` |
| 0.732 / 0.720 vox | held-out RMS residual for PHerc1203 / PHerc0846A (both within 1.5) | `logs/sib/regrescan/REPORT.md` |
| 29 passed | unit tests, including round-trip checks | `logs/sib/regrescan/tests_result.txt` |

## Where the records are

- `logs/sib/regrescan/REPORT.md`
- `logs/sib/regrescan/summary.json`
- `logs/sib/regrescan/PHerc1203/final_affine.json`
- `logs/sib/regrescan/PHerc0846A/final_affine.json`
- `logs/sib/regrescan/tests_result.txt`
- `logs/sib/regrescan/proposals/DECL-REGRESCAN.md`
- `logs/sib/regrescan/ASK.md`

## Lesson

Report every pre-specified fit that was checked, not the best-scoring one; both PHerc0846A iterations are in the report.

## Related

- sib-reg0841
- sib-reg0009b
- DECL-TRESCAN
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
for st in meta coarse patches mid fit refit check final ceiling; do tools/sib/regrescan/run.sh /opt/hv/bin/python tools/sib/regrescan/regrescan.py $st PHerc0846A; done
tools/sib/regrescan/run.sh /opt/hv/bin/python tools/sib/regrescan/regrescan.py check_fititer1 PHerc0846A
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
