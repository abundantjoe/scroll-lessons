# Data notice

**The code in this repository is MIT-licensed (see [LICENSE](LICENSE)). The scroll data is not.** Everything in this
repository that is derived from Vesuvius Challenge data is licensed **CC BY-NC 4.0**
(<https://creativecommons.org/licenses/by-nc/4.0/>). That covers the PNG review sheets, the contact sheets, the
prediction-map windows, the CT crops and the figures. Non-commercial use only. Attribution is required, as below.

## What data this repository uses or contains

| Data | Source | Where it appears here |
|---|---|---|
| PHerc0139 segment `20250831000000-w040_2025083102`: native 9.362 µm surface volume and tifxyz mesh (the known-text control) | `s3://vesuvius-challenge-open-data/PHerc0139/segments/20250831000000-w040_2025083102/` | `packages/DRYRUN_PHerc0139_w040/` (CT, forward and reverse map crops, mesh metadata), `review_sheets/reference/`, `examples/` (extracted at run time, not stored) |
| w040 ink labels and supervision mask; for Gate C, the PHerc1667 w028 labels | Hugging Face bucket `hf://buckets/scrollprize/datasets/ink_9um` (`labels/native9-scrollprizeorg-21slices/w040/`; `labels/aligned-scrollprizeorg-21slices/pherc1667-w028/`) | not stored; used to score Gate A and Gate C |
| PHerc0841 segments `20260220213127-w00`, `20260220214732-auto_grown_20260220144552896` and `20260221022814-auto_grown_20260220174252405`: 2.403 µm surface volumes (level 2) and their ink labels (`ink-labels/2.403um-volume-20260319124803/20260918/`), the held-out known-text test R-HELDOUT | `s3://vesuvius-challenge-open-data/PHerc0841/segments/` | not stored; per-segment statistics, reader stats and checksums in `records/release/heldout_2026-10-15/` |
| PHerc1667 segment `w028`, PHerc0826, PHerc0358, PHerc1203, PHerc1447, PHerc0800 volumes, surface predictions and team segments, and the team's published 2.4 µm w028 prediction | `s3://vesuvius-challenge-open-data/` | renders and model outputs in `review_sheets/` (incl. the w028 calibration in `review_sheets/2um/`); seed band PNGs for PHerc0826 and PHerc0358 in `seeds/` |
| PHerc0846A 2.403 µm rescan: volume, surface prediction and our traces on it | `s3://vesuvius-challenge-open-data/` | `review_sheets/2um/`, `review_sheets/qc/`, seed band PNGs in `seeds/` |
| Level-4 CT and surface predictions of the other eligible volumes: seed band PNGs for PHerc0175A, PHerc0191, PHerc0306B, PHerc0343 and PHerc0813; the level-4 survey montage of all 23 eligible volumes | `s3://vesuvius-challenge-open-data/` | `seeds/`, `records/survey_2026-09-16_montage.png` |
| Ink model `scrollprize/ink_9um` (`hybrid_3d2d-seed42/step-075000.pth`) | <https://huggingface.co/scrollprize/ink_9um> | not stored; every 9 µm prediction map shown in this repository is its output |
| Ink model `scrollprize/ink_canonical_2um` (the 2.4 µm route only) | <https://huggingface.co/scrollprize/ink_canonical_2um> | not stored; its output appears only in `review_sheets/2um/` |

All scans used here were released directly by Vesuvius Challenge in 2025 or later. No map, volume, render or model
weight file is committed. Only PNG figures and the small crops listed above are stored, and only the ones needed to
make the results checkable.

## How to cite the data

The text below is quoted from <https://scrollprize.org/data> ("How to Cite" and "Licenses"), retrieved 2026-10-15.

**Vesuvius Challenge scans.** These are all the scans used in this repository. Use this citation for newer scans
released directly by Vesuvius Challenge:

> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau,
> Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker,
> W. Brent Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.

**EduceLab-Scrolls.** This is required only if you apply these tools to Scrolls 1–4 or Fragments 1–6 scanned at DLS
before 2025. This repository itself uses none of them. The data page says these scans "are from the EduceLab-Scrolls
Dataset, copyrighted by EduceLab/The University of Kentucky". It asks you to cite EduceLab-Scrolls as the source of
the data in any published abstract, and in any published manuscript to reference:

> Parsons, S., Parker, C. S., Chapman, C., Hayashida, M., & Seales, W. B. (2023). EduceLab-Scrolls: Verifiable
> Recovery of Text from Herculaneum Papyri using X-ray CT. ArXiv [Cs.CV]. https://doi.org/10.48550/arXiv.2304.02084

It also asks for methods-section language like: "Data used in the preparation of this article were obtained from the
EduceLab-Scrolls dataset [above citation]."

The `ink_9um` model's training data, as recorded in `docs/MASTER_PROMPT_v4.md`, includes PHercParis4 (Scroll 1). Check
the model card for the model's own terms before you redistribute weights or outputs.
