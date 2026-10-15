<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="PHerc0841 9 um <-> 2.4 um registration: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# PHerc0841 9 um <-> 2.4 um registration

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-reg0841` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **PASSED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0841, PHerc0175B.

## Question

Can the PHerc0841 9.366 um scan and its 2.403 um rescan be mapped onto each other well enough to carry a 2.4 um chain check (CHAIN VALID)? The pre-registered held-out bars were median r >= 0.85, RMS <= 1.5 vox, and a clear NCC drop for a shifted control.

## Method

CT only, no ink model. Steps:
1. An orientation search over 8 flip and remount candidates.
2. A coarse fit from the organizer mesh pairs, then per-patch phase-correlation correspondences.
3. An affine fitted on 24 patches, with 16 held-out patches pre-registered (prereg_heldout.md) before any analysis.
4. After the affine failed, a second model (affine plus a smooth quadratic field) was chosen by leave-one-out on the earlier correspondences, frozen, and tested once on 16 new pre-registered patches.

## What ran on this branch

- 2026-09-25: 15,738 chunks read and hashed; the affine fit and its held-out test; then the non-affine model and its new held-out test.
- 2026-09-25 to 2026-09-26: CHAIN VALID preparation. The organizer meshes were mapped to 2.4 um with the frozen map, a fail-closed check kept every rendered sample >= 144 vox from the sealed J points, and inference was timed on CPU.
- 2026-09-30: the branch was reused for an FL-2 PHerc0175B lane, held before launch pending the owner's direct confirmation.

## Outcome

The single affine FAILS (REG-0841-R1): held-out median r 0.724 and RMS 1.92 vox, though the control passes. The deformation between the scans is smooth but non-affine. The affine plus quadratic field PASSES all bars on the new patches (REG-0841-NA): median r 0.863, RMS 0.977 vox, and a control drop of 0.695 (15/16 clear). The CHAIN VALID check itself stayed at WAITING FOR GO and never ran, so no PHerc0841 ink map was made.

| key number | meaning | file on this branch |
|---|---|---|
| 0.724 | single-affine held-out median r (bar 0.85, FAIL) | `logs/sib/reg0841/heldout_result.json` |
| 1.92 vox | single-affine held-out RMS residual in 9 um voxels (bar 1.5, FAIL) | `logs/sib/reg0841/REPORT.md` |
| 0.863 | non-affine model held-out median r on 16 new patches (PASS) | `logs/sib/reg0841na/reg0841na_summary.json` |
| 0.977 vox | non-affine model held-out RMS (PASS) | `logs/sib/reg0841na/reg0841na_summary.json` |
| 144.07 vox | minimum clearance of the mapped meshes from the J points in the CHAIN VALID preparation | `logs/sib/reg0841/chainvalid/REPORT.md` |

## Where the records are

- `logs/sib/reg0841/REPORT.md`
- `logs/sib/reg0841/reg0841_summary.json`
- `logs/sib/reg0841/heldout_result.json`
- `logs/sib/reg0841/prereg_heldout.md`
- `logs/sib/reg0841/affine_final.json`
- `logs/sib/reg0841na/reg0841na_summary.json`
- `logs/sib/reg0841/chainvalid/REPORT.md`
- `logs/sib/reg0841/chainvalid/ASK.md`

## Lesson

Separate measurement error from model error: the correspondences repeated to under 0.25 vox, so the affine model was what failed.

## Related

- sib-regrescan
- sib-reg0009b
- DECL-CHAINVALID
- REG-0841-R1
- REG-0841-NA
- DECL-FL-2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv/bin/python tools/sib/reg0841/mesh_fit.py logs/sib/reg0841/mesh_fit.json
/opt/hv/bin/python tools/sib/reg0841/coarse.py 1
/opt/hv/bin/python tools/sib/reg0841/coarse.py 3
/opt/hv/bin/python tools/sib/reg0841/plan_patches.py
/opt/hv/bin/python tools/sib/reg0841/fetch_blocks.py fit
/opt/hv/bin/python tools/sib/reg0841/fit_run.py
/opt/hv/bin/python tools/sib/reg0841/fetch_blocks.py heldout
/opt/hv/bin/python tools/sib/reg0841/heldout_run.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
