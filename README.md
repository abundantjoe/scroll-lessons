<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-M layout map and top-edge check: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-M layout map and top-edge check

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-layout` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0800.

## Question

Numbers-only layout questions for the Paris 4 title search (DECL-P4-13, P4-M): does papyrus continue above the official mesh top edge? Can the organizers' earlier title-search meshes be mapped into the current frame? What column structure do 1 mm profiles of model predictions and raw-CT channels show?

## Method

Arrays were decoded only to sums, indices and distances; no image was viewed. Edge check: mesh edge height vs the spiral-fit limit, organizer-mask coverage above the edge, and a CT sheet index anchored on an organizer labelled mesh, tested against a half-pitch null with bootstrap. Mapping: the transform between scan frames was validated on an open-bucket segment. Profiles: 1 mm bins of the official prediction, the E2 slab mean and the L2 slab max. Later, one further declared layout profile was re-run to check determinism.

## What ran on this branch

2026-09-26 to 2026-09-27: edge check at level 2 (9.6 um), column profile, transform validation, and the further layout profile, with a re-run after a container restart. On 2026-09-30 the branch was reused as First Letters worker fl-pherc0800 (DECL-FL-1); its pipeline launched on the 3 largest organizer segments (2.45 / 1.93 / 1.80 cm2).

## Outcome

The official top edge is a flat z cut at the spiral-fit limit, not a sheet end. Sheet is supported only about 2 mm above it, and scroll material ends 3-5 mm above it. A first patch-correlation tracker failed its own validation and is not used. The prediction profile resolves column pitch on known text (SNR 64 and 102), while the E2 and L2 profiles show no layout signal. The transform is validated (19 um median residual). Mapping the 2024 organizer meshes stayed blocked: the session's safety check refused to use licensed data whose acceptance came only by relay, so the files were deleted. The further layout profile is descriptive only, and its re-run matched exactly. For PHerc0800, all organizer segments are under 4 cm2 and the grow path has no input (ASK-FL-1 open).

| key number | meaning | file on this branch |
|---|---|---|
| ~2 mm | sheet continuation supported above the official mesh top edge | `logs/sib/p4-layout/edge.json` |
| 3-5 mm | height above the edge where the organizers' scroll mask ends | `logs/sib/p4-layout/edge.json` |
| 0.41 vs 0.72 | tracker positive-control r vs shuffled null (p50); tracker failed and is not used | `logs/sib/p4-layout/edge/edge_cont.json` |
| 19 um | median residual of the validated frame transform | `logs/sib/p4-layout/orgmap.json` |
| SNR 64 / 102 | column-pitch detection of the prediction profile on two known-text spans | `logs/sib/p4-layout/profile.json` |

## Where the records are

- `logs/sib/p4-layout/REPORT.md`
- `logs/sib/p4-layout/STATUS.md`
- `logs/sib/p4-layout/ASK.md`
- `logs/sib/p4-layout/edge.json`
- `logs/sib/p4-layout/edge/`
- `logs/sib/p4-layout/orgmap.json`
- `logs/sib/p4-layout/profile.json`
- `logs/sib/p4-layout/profile/profile_detail.json`
- `logs/sib/fl-pherc0800/STATUS.md`
- `logs/sib/fl-pherc0800/ASK.md`

## Lesson

A tracker must beat a shuffled null on known sheet before its continuation distances mean anything; this one did not, so it was discarded.

## Related

- DECL-P4-13
- DECL-P4-12
- DECL-FL-1
- sib-p4-excl
- sib-p4-research
- sib-p4-titulus
- sib-p4-l2
- fl-pherc0800

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-layout/col_profile.py m1 <pred.tif> <meshdir> <grid.json> <out.npz>
python tools/sib/p4-layout/col_profile.py e2 <surface-volume zarr url> <meshdir> <grid.json> <out.npz> <manifest.jsonl>
python tools/sib/p4-layout/l2_profile.py <git ref> <manifest path in ref> <m1 npz> <out.npz>
python tools/sib/p4-layout/profile_analyze.py <out.json> a_m1=<npz> [a_e2=<npz>] [b_m1=<npz>]
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
