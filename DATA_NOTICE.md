# Data notice

**Code** in this repository is MIT-licensed (see [`LICENSE`](LICENSE)).
**Data** — and anything derived from data — is not covered by the MIT license. It comes from the Vesuvius Challenge and is used under
**[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)** (non-commercial, with attribution), the license stated on
<https://scrollprize.org/data> ("Content licensed CC BY-NC 4.0 unless otherwise specified"; checked 2026-10-15).

## What in this repository is derived from Vesuvius Challenge data

| Path | Derived from |
|---|---|
| `inkeval/data/example_scroll1.npz` | two 15 mm crops of Scroll 1 (PHerc. Paris. 4) surface volumes, Grand-Prize hand labels and the team ink prediction, pooled 8× |
| `docs/figures/*.png` that show papyrus (`banner.png`, `fig2_*`, `fig3_*`, `figS_*`), `docs/figures/reading_runs/*.png`, `archive/review_sheets/s1/*.png` | the same sources, rendered (CT, labels, detector and team maps; label outlines on the team overview) |
| `models/*.pt` | weights trained on the above |
| `stats/`, `results/` | numbers measured or fitted on the above (crop coordinates, registrations, AUCs; E1 weights and kernels in `stats/explore/*.npz`) |

The full research data (`data/`, ≈ 19 GB on the release machine) are **not** redistributed; [`docs/REPRODUCE.md`](docs/REPRODUCE.md)
fetches the Scroll 1 inputs from their public sources: the 12 label, ink-overview and render images are verified by SHA-256
([`results/input_manifest.json`](results/input_manifest.json)), and the surface volumes, streamed per crop, are pinned by their
versioned URL and the SHA-256 of their `.zarray`/`.zattrs` metadata.

## Sources and required citations

**1. 2.4 µm surface volumes, ink-detection overviews and surface renders (Scroll 1 segments 20231005123336, 20231210121321,
20230929220926, 20231012184424; and PHerc. 1667 segment w028 in the early calibration gates).** Released by Vesuvius Challenge in the
open-data bucket `s3://vesuvius-challenge-open-data/`. These are newer scans released directly by Vesuvius Challenge; cite:

> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone,
> Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales.
> *Vesuvius Challenge - CT Scans of Herculaneum Papyri.* Vesuvius Challenge.

The early calibration gates also used the 9.362 µm surface volume of segment w040 (GATE-T2(b)) and the ink labels
`pherc1667-w028_inklabels.zarr` (Hugging Face) and `w040_inklabels.zarr`, the labels only to exclude labelled letters from the
reference; E1's unfinished resolution probe read a low-resolution level of the 1.129 µm surface volume of segment 20231210121321.
None of these files is redistributed here.

**2. Grand-Prize hand ink labels (the evaluation reference).** Drawn in 2023 on the Scroll 1 segments of the legacy **EduceLab-Scrolls**
dataset (scanned at Diamond Light Source before 2025; copyright EduceLab / University of Kentucky, used by Vesuvius Challenge with
permission). Obtained from the archived repository of the 2023 Grand-Prize winners (Youssef Nader, Luke Farritor, Julian Schilliger),
`https://github.com/younader/Vesuvius-Grandprize-Winner/tree/main/all_labels`; that repository has no license file, and its successor,
`https://github.com/ScrollPrize/villa`, is MIT-licensed for code. We treat the labels as Vesuvius Challenge data under CC BY-NC 4.0 and
redistribute only pooled derivatives. As the data page requires for EduceLab-Scrolls data:

> Data used in the preparation of this work were obtained from the EduceLab-Scrolls dataset.
> Parsons, S., Parker, C. S., Chapman, C., Hayashida, M., & Seales, W. B. (2023). *EduceLab-Scrolls: Verifiable Recovery of Text from
> Herculaneum Papyri using X-ray CT.* arXiv [cs.CV]. https://doi.org/10.48550/arXiv.2304.02084

**3. The team's 2.4 µm ink-detection predictions** (used as the positive control; to place the hand labels by registration; as the
reference of the w028 calibration gates and of the reading-run agreement statistic; and to veto training negatives in v6b and v7, and
in the invalid v6) are Vesuvius Challenge open data under the same license as (1).

## Owner checklist before publishing

- The repository is currently **private**; judges and users cannot see it until its visibility is changed.
- The label source repository carries no license file of its own (checked 2026-10-15). If in doubt, ask the Vesuvius Challenge team
  before redistributing label-derived files; removing `inkeval/data/example_scroll1.npz` disables `inkeval demo` and makes
  `tests/test_published.py::test_demo_runs_and_controls_behave` fail; the table above lists the other derived files.
