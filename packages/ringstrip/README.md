# ringstrip: one continuous strip from many grown patches

Ink models run on small grown patches. Readers need one sheet. `ringstrip` puts every pixel of every patch's map back where it belongs on the unrolled winding, by azimuth and height, and gives you one continuous image per direction; it also stitches overlapping tiles of a flat grid with feathered seams.

## What it does
- `python -m ringstrip.unroll <out.png> <axis_x> <axis_y> <R_ref> <map_name> <patch_dir>...`
  Each patch directory holds `tifxyz/` (x, y, z .tif) and a map rendered on it (same aspect). Every map pixel gets its 3-D position by bilinear interpolation of the tifxyz, then lands at (azimuth × R_ref, z). Overlaps are averaged, 1-3 px holes closed, and a JSON records the cut azimuth, offsets and coverage. Patches from different grows, even different sessions, merge into the same strip.
- `python -m ringstrip.stitch tiles.json out.png`: reassembles overlapping tiles of one grid (20 px per cell by default) with feathered overlaps.

## Validation
- `test_two_adjacent_patches_unroll_into_one_continuous_line`: two synthetic cylinder patches overlapping in azimuth, each carrying one bright line at the same height, unroll into a strip where that line is continuous across the seam (> 90 % of its length bright).
- `test_stitch_reproduces_a_gradient_from_overlapping_tiles`: three overlapping tiles of a gradient reassemble to within 2 grey levels everywhere.
- Real data: `results/PHerc0268_band070_ink9um_forward_strip.png` is five 2 × 2 cm patches of PHerc0268 (band r/R = 0.70, mid-height) unrolled into one 10,513 × 2,507 px strip (the ink map on it is uniform speckle; the surfaces, not the tool, are the problem there, see the `xsec` package).

## Known limits
- Assumes one winding: azimuth is measured about a single axis point; a patch that spans two windings will overlap itself.
- The strip is not an isometric flattening; it is a readable layout for maps that were already rendered on each patch.

## Install and test
`pip install numpy tifffile opencv-python-headless pytest` then `pytest` (2 tests, about 3 s).

## Data and citation
Scans: PHerc0268 (volume 20251110183117, 8.64 µm, 116 keV) from the Vesuvius Challenge open-data bucket (https://scrollprize.org/data; Data Browser https://scrollprize.org/data_browser). Cite:
> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.

Surfaces grown and rendered with the organizers' volume-cartographer (Vesuvius Challenge "villa" repository); ink map from the organizers' public ink_9um model (hybrid_3d2d-seed42, step 75000). Code MIT; `results/` CC BY-NC 4.0.

Built by an individual with the help of AI coding agents (Claude Code).
