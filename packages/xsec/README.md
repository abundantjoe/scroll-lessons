# xsec: see whether a grown surface really follows one papyrus sheet

`xsec` draws a tifxyz surface on raw CT slices at several heights, so a person can check in seconds whether the surface stays on one sheet or jumps between layers. It ships with the synthetic case that shows why the usual numeric gate cannot catch a jump, and with the real PHerc0268 case where only the cross-section caught it.

## Why
Auto-grown surfaces (`vc_grow_seg_from_seed`) are the input to every render and every ink model. If a surface crosses from one winding to the next, the render is a collage of different sheets and no ink map on it means anything. We lost a full day of compute to exactly that before looking at a cross-section.

## What it does
- `python -m xsec.xsections <tifxyz> <volume.zarr|s3://...> <out> [--level 1]`: writes `<out>_xsec.png`, four raw-CT slices through the surface's z range with the surface points drawn in colour, and `<out>_xsec.json`.
- `python -m xsec.radial_gate <tifxyz> <axis_x> <axis_y>`: the radial-normal gate (median |cos| between surface normal and radial direction, radial spread), for comparison.
- `xsec.synth`: synthetic cylinder patches with and without a layer jump, and shell volumes, with known geometry.

## What the gate cannot see (validated)
- Synthetic: an on-sheet patch and a patch that steps to the next shell halfway both score median |cos| > 0.95 on the radial gate (test `test_radial_gate_is_blind_to_a_layer_jump`). A jumped surface still faces outward.
- Real data, PHerc0268 (volume 20251110183117, 8.64 µm, 116 keV), a 2 × 2 cm patch grown with the organizers' normal grids from seed (6154.6, 7869.5, 4744): radial gate median |cos| 0.928, 75 % of normals above 0.8, radial spread 0.90 mm per cm. It passed every numeric bar we had. The cross-section (`results/PHerc0268_grown_surface_old_vs_normalgrid_z4744.png`, right panel) shows it holding one layer between cracks and jumping to the neighbouring layer at each crack. The left panel is the same seed grown without normal grids: it cuts straight across windings.
- An automated 'fraction of surface points on predicted papyrus' test did NOT discriminate on this crushed scroll: 0.676 for the good patch, 0.676 for a jumped one, 0.628 for the surface that cuts across windings (dense cores put papyrus everywhere). It discriminates only on synthetic data (test 2). We report it so nobody repeats it.
- `results/PHerc0268_normalgrid_surface_4_heights.png`: the same patch at four heights; `results/PHerc0268_band070_renders_montage.png`: five patches at 70 % radius whose render centre layers show fibres radiating from the seed, the signature of a surface that is not flat on one sheet.

## Known limits
- The picture is for a human. There is no number that replaces it on crushed scrolls; that is the finding.
- Level-1 CT (17 µm/px) is used for speed; pass `--level 0 --scale 1` for full resolution.

## Install and test
`pip install numpy tifffile zarr opencv-python-headless s3fs pytest` then `pytest` (3 tests, about 6 s, synthetic data only).

## Data and citation
Scans: PHerc0268 from the Vesuvius Challenge open-data bucket (https://scrollprize.org/data, Data Browser https://scrollprize.org/data_browser). Cite:
> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.

Surfaces were grown with the organizers' volume-cartographer (`vc_grow_seg_from_seed`, `vc_render_tifxyz`; Vesuvius Challenge "villa" repository) and the organizers' published normal grids. Code MIT; files under `results/` CC BY-NC 4.0 (see `results/LICENSE-DATA`).

Built by an individual with the help of AI coding agents (Claude Code); every number above is reproducible from the files in this repository or the public bucket.
