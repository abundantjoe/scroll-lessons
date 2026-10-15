<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Handedness from geometry (handed-1/2): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Handedness from geometry (handed-1/2)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-handed` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **PASSED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHerc0009B, PHerc0841, PHerc0800, PHerc1447, PHercParis4, PHerc0500P2, PHerc0813.

## Question

Can the mirror state of a rendered tifxyz sheet be predicted from geometry and catalogue metadata alone (SG item 12)? Readers had failed to tell mirrored maps from normal ones, so the aim was that they would never be shown a mirrored map.

## Method

The rule: mirror state = sign(det[dP/du, dP/dv, r_out]) times the frame parity given by the metadata flag left_handed_coordinates. r_out comes from the official umbilicus, the CT-mask centroid or the mesh's own normal-line centre, with confidence grades. The rule was validated on synthetic volumes with planted glyphs and a wrong-sign control. It was then applied to every organizer mesh of PHerc0139, PHerc0009B, PHerc0841, PHerc0800 and PHerc1447, with CT-frame checks. Numbers only: no image was opened.

## What ran on this branch

2026-09-25 to 2026-09-27:
- handed-1 and handed-2, including the PHerc1447 frame checks and an attempt to settle up/down for the 5 volumes with a null z flag.
- A reading-orientation check of the PHercParis4 canvases.
- KTLB-4P preparation on the fragment PHerc0500P2 (logs/sib/ktlb4p-prep/).
- The handcheck Progress Prize package (112 tests pass, 1 skipped).

On 2026-09-30 the branch was reused for an FL-2 PHerc0813 environment build (status file only).

## Outcome

The rule gives convention +1 for all 26 volumes. In synthetic validation 32/32 renders read unmirrored and the wrong-sign control came out mirrored 32/32. These organizer meshes are all predicted to read unmirrored as stored: 38 + 8 of PHerc0139, 18 of PHerc0009B, 3 of PHerc0841 and 6 of PHerc0800. On PHerc1447, 9 of 15 meshes are flagged (11 of 15 under the packaged rule). The PHercParis4 canvases need no flip. A letter-level real-data check is impossible because the official labels carry no letter identities. KTLB-4P: the 9.362 <-> 2.215 um registration passed on its pre-registered second attempt. Up/down for the 5 volumes with a null z flag stays open: the winding-sense check (F5) agreed with the organizer flag on 36/36 PHerc0139 meshes but needs traces spanning more than one turn, which these volumes lack, and the CT-only pitch-angle estimator failed on real PHerc0139 data (per-slice signs split 8 positive / 8 negative), so its 26-volume run was stopped and no CT-only up/down claim is made (REPORT.md section 12).

| key number | meaning | file on this branch |
|---|---|---|
| 32/32 | synthetic renders read unmirrored under the rule; the wrong-sign control was mirrored 32/32 | `logs/sib/handed/handed_summary.json` |
| 38/38 | PHerc0139 9.362 um organizer meshes predicted to read unmirrored as stored | `logs/sib/handed/handed_summary.json` |
| 114/114 | organizer affines whose determinant sign agrees with the metadata parity flags (100 same-flag det > 0, 14 different-flag det < 0) | `logs/sib/handed/handed_summary.json` |
| 9 of 15 | PHerc1447 meshes flagged by handed-1 | `logs/sib/handed/REPORT.md` |
| 0.929 | KTLB-4P PHerc0500P2 registration held-out median r on attempt 2 (PASS; attempt 1 was 0.834, FAIL) | `logs/sib/ktlb4p-prep/REPORT.md` |

## Where the records are

- `logs/sib/handed/REPORT.md`
- `logs/sib/handed/handed_summary.json`
- `logs/sib/handed/p4orient.json`
- `logs/sib/handed/ASK.md`
- `logs/sib/ktlb4p-prep/REPORT.md`
- `tools/sib/handed/handcheck/`

## Lesson

The mirror state follows from one sign plus the frame parity; human readers could not judge it, so geometry has to decide.

## Related

- sib-pp-handcheck
- DECL-HANDED
- DECL-HANDED-R2
- DECL-HANDED-R3B
- DECL-PP-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
source /opt/hv/bin/activate
PYTHONPATH=src python -m pytest -q tests/sib_handed_synthetic.py tests/sib_handed_maas.py
PYTHONPATH=src python tools/sib/handed/synthetic_scores.py logs/sib/handed/synthetic_scores.json
python tools/sib/handed/fetch_meshes.py /work/handed/s3 logs/sib/handed/downloads_meshes.json <tifxyz prefixes>
tools/sib/handed/run_centroids.sh
PYTHONPATH=src python tools/sib/handed/analyze_meshes.py logs/sib/handed/mesh_predictions.json
PYTHONPATH=src python tools/sib/handed/build_table.py logs/sib/handed/mesh_predictions.json logs/sib/handed/volume_table.json logs/sib/handed/volume_table.md
python tools/sib/handed/summarize.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
