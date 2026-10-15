<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-L3 ink-depth calibration (2.4 um): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-L3 ink-depth calibration (2.4 um)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-depth` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

In the 2.4 um volume, does a surface ink layer sit at a constant depth offset d* from the official mesh? If so, a depth-calibrated thin-slab channel (P4-L3, DECL-P4-12-A3) can be built.

## Method

Calibration on the known-text control strip only. f(o) is the fraction of voxels above T_hi (203), computed at each of 109 offsets (+-129.6 um) over 24 of 168 tiles drawn by fixed seed. Parameters were frozen at faccba7 before any depth number. Rule: PASS if the peak has robust z >= 3 and lies within +-100 um, with a rot-90 check. The mesh sign convention (recto/verso) was measured separately. The rule's specificity was unit-tested on synthetic no-ink sheets.

## What ran on this branch

2026-09-26 to 2026-09-27: all 109 slices of the control surface volume at level 0, 1.55e9 mesh-valid px per slice; calibration computed 2026-09-27T00:55:41Z; synthetic unit tests (unit_tests.json). No title-strip voxel was read.

## Outcome

STOP: the largest excess lies at -31.2 um with robust z 1.94, below the bar of 3. The peak is broad (FWHM 57.6 um), and only 4 of 24 tiles agree within 5 um. L3 tiles and the verso follow-ups were therefore not built. The unit tests showed that the declared rule also passes 25/100 i.i.d.-noise sheets and 10/10 no-ink sheet profiles, so a PASS would have lacked specificity. This was disclosed and did not change the outcome.

| key number | meaning | file on this branch |
|---|---|---|
| 1.94 | robust z of the best offset (bar 3); verdict STOP | `logs/sib/p4-depth/calib.json` |
| -31.2 um | offset of the largest f(o) excess (verso side) | `logs/sib/p4-depth/calib.json` |
| 4/24 | tiles whose own argmax lies within 5 um of the pooled peak | `logs/sib/p4-depth/calib.json` |
| 25/100 | i.i.d.-noise synthetic sheets that the declared rule would PASS | `logs/sib/p4-depth/unit_tests.json` |

## Where the records are

- `logs/sib/p4-depth/STATUS.md`
- `logs/sib/p4-depth/ASK.md`
- `logs/sib/p4-depth/calib.json`
- `logs/sib/p4-depth/calib_params.json`
- `logs/sib/p4-depth/sign.json`
- `logs/sib/p4-depth/unit_tests.json`
- `logs/sib/p4-depth/cal_w0.jsonl`
- `logs/sib/p4-depth/specificity/`
- `tools/sib/p4-depth/`

## Lesson

Unit-test a peak rule on no-signal synthetic sheets before trusting a PASS: this declared rule passed structure-free data a quarter of the time.

## Related

- DECL-P4-12
- DECL-P4-12-A3
- DECL-P4-18
- P4-L3-CALIB-RESULT
- sib-p4-l2
- sib-p4-highz
- sib-p4-tiles-b

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-depth/test_depth.py logs/sib/p4-depth/unit_tests.json
N=3 sh tools/sib/p4-depth/run_calib.sh   # depth.py calib workers (control only)
python3 tools/sib/p4-depth/depth.py calib-merge <ctl_mesh_dir> <out_dir> <thresholds.json>
python3 tools/sib/p4-depth/depth.py sign <ctl_mesh_dir> <out_dir>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
