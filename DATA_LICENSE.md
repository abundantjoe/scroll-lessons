# Data and citation

**Code** in this repository is MIT licensed (see [LICENSE](LICENSE)).

**Scroll data.** Every CT volume behind the files in the table below is a newer scan released directly by the Vesuvius Challenge. The volumes,
and any image or number derived from them, are licensed **CC BY-NC 4.0** (non-commercial use, with attribution). Raw
volumes are not redistributed; the scripts fetch them from the official open-data bucket.

| scroll | volume | voxel size, energy | used for | derived files here |
|---|---|---|---|---|
| PHerc0343 | `20250521140437-8.640um-1.2m-116keV-masked.zarr` | 8.64 µm, 116 keV | positive control (renders, ink maps, scores); banner CT slice | `figures/fig3*`, `figures/fig4*`, `figures/fig5*`, `figures/dominion_banner.png`, `results/control_strips*`, `results/blind_read/` |
| PHerc0268 | `20251110183117-8.640um-1.2m-116keV-masked.zarr` | 8.64 µm, 116 keV | the blank-margin artifact on real strips (aggregate numbers only) | `results/margin_artifact/`, `figures/fig1*`, `figures/fig2*` |

Please cite the dataset:

> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro
> Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent
> Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.

Data: https://scrollprize.org/data · Data Browser: https://scrollprize.org/data_browser

The experiment map ([docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)) describes work on further Vesuvius Challenge volumes and
quotes numbers from it (scores, counts, registration and flattening statistics). It includes no image or map of them,
and no letter, reading or location on any scroll that has not been officially read. These numbers are under the same
CC BY-NC 4.0 terms; cite the dataset for each scan.

**Third-party inputs** (fetched by the scripts, not redistributed here):
- The PHerc0343 positive-control segment, letter boxes and scroll axis are Erwin Nieuwlaar's public First Letters
  release (`github.com/Nieuwlaar/pherc343-first-letters`, MIT, commit `e8370f1`). Its letters were published there by
  their author. This repository shows them only as a positive control.
- The ink models are the organizers' `scrollprize/ink_9um` (seeds 42 and 43) and Erwin Nieuwlaar's
  `Nieuwlaar/ink9um-dense-native` on Hugging Face, under their own licences.
- The renderer and the ink inference are ScrollPrize/villa (volume-cartographer `vc_render_tifxyz`, `vesuvius`), commit
  `41701aa`.
- Banner fonts: Cinzel and Inter (SIL Open Font License), downloaded from Google Fonts by `scripts/make_banner.py`.
