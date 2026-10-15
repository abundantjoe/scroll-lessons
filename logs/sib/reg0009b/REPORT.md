Provenance: Project HERCULES | owner the owner | [id removed]

# reg0009b: KTLB-M preparation material on PHerc0009B (numbers only)

Sibling builder task. Date 2026-09-25 (UTC). No image, rendered slice or ink map was opened, viewed or written; no ink model was run on PHerc0009B; no 9 um map of anything exists from this task. Only official data (anonymous S3 `vesuvius-challenge-open-data`) and the official label/ink products were used. Every run, failures included, is in `runs.jsonl`. Machine-readable deliverable: `summary.json` (registration, depth, grouping, window counts, sha256 of every other output JSON).

## Headline
- 18 PHerc0009B segments have meshes in both frames, 2.401 um reference ink maps and both surface volumes; 1 of them (20250919125754) has official labels (label_set 20260918).
- Registration 2.401 um -> 8.640 um canvas: **18 / 18 segments pass** the gate (whole-segment NCC >= 0.80 after correction, median residual tile shift <= 2 px). This holds only **with depth correction**: at the nominal slab centre 13 of 18 are below NCC 0.80. Corrected shifts are small, (-0.36..-0.97, +0.02..+1.85) px on the 9 um canvas; the label mapper alone is already within 2 px everywhere.
- Re-trace grouping under CORR-RETRACE-RULE (fail-closed): 119 pairs within 128 vox, **28 SAME**, **6 papyrus units** (U01 9 segments, U02 5, four singletons). All 28 come from the point-to-surface form (b); the literal vertex form (a) finds 0.
- Five further pairs (the May-2025 traces 172639 and 200236 against U01) look like the same sheet traced twice with a smooth 1-5 vox offset field; the rule calls them NOT SAME. A sensitivity grouping that merges them gives 4 units. It does not change the window counts, because those two segments contain no dense windows.
- Candidate windows (2 x 2 cm, dense official reference ink, deduplicated in 3-D across all segments): **23**. Per unit: U01 9, U02 11, U04 2, U06 1, U03 0, U05 0. The count is the same at 24 um and 48 um dedupe tolerance.

## 1. Inventory
Source: `s3://vesuvius-challenge-open-data/PHerc0009B/segments/` (20 prefixes). Full listing with sizes: `inventory_raw.json` (201 downloaded objects, 903,122,426 B, sha256 each).
- 18 segments with `mesh/<id>-on-20250521125136-8.64um.tifxyz` AND `mesh/<id>-on-20250820154339-2.401um.tifxyz`, both surface volumes (`8.64um-1.2m-116keV-volume-20250521125136.zarr`, 31 slices; `2.401um-0.35m-77keV-volume-20250820154339.zarr`, 109 slices; 6 pyramid levels each, uncompressed uint8 chunks) and one reference ink map `ink-detection/PHerc0009B-<id>-2.401um-...-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif` (15.1-54.7 MB; uint8, exactly 20 x the 2.401 um mesh grid).
- Labels: only 20250919125754-auto_grown_20250919055754487_inp_hr has `ink-labels/2.401um-volume-20250820154339/20260918/{inklabels,supervision,validation}.zarr` (zarr v3, sharded, 25360 x 20520, values 0/255; label ink 1.90 % of the canvas, supervision 8.51 %, validation 2.42 %, validation entirely inside supervision).
- 20250910185200: intermediate `_original.obj` only (no frame meshes, no SV, no ink): not usable. `segments/raw/`: 5 PNGs (not downloaded, not opened).
- Voxel sizes from each volume's metadata.json: 8.640 um (samplePixelSize 0.00864 mm) and 2.401 um (0.002401 mm). 2.401 um mesh edges have a median of 19.96-20.05 vox on every segment, so 1 canvas px = 2.401 um and a window of 8340 px = 2.002 cm.
- `volumes/20250521125136-8.640um.../transform.json` (sha256 4f7dcc53...) holds a 6-landmark affine 8.64 -> 2.401 um with landmark residuals up to 17 2.4-um vox (~4.7 9-um vox), mostly along z.

## 2. Per-segment registration (CT only)
Method (`tools/sib/reg0009b/reg.py`, `depthcheck.py`, driver `pipeline.sh`):
- I9 = mean of 8.64 um SV slices 14-16 at level 0 (canvas px). J = 2.401 um SV at level 2 (9.604 um px), mean of 5 slices, resampled onto the 9 um canvas through the label mapper c2 = (c9 + 10) N2/N9 - 10 (N = canvas extents = 20 x mesh grid; checked equal to the zarr shapes). Only the needed slices are streamed, by S3 byte ranges.
- Band-pass (Gaussian 1 minus Gaussian 10 px); 256 px tiles (>= 98 % CT-valid in both); NCC over +-12 px with a parabolic sub-pixel peak. Global shift = median of tiles with peak NCC >= 0.3.
- Shift convention: **c9 = (c2 + 10) * N9 / N2 - 10 + d**, with d = (dx, dy) in 9 um canvas px.
- Depth check: 9 um level-1 slices 11 / 15 / 19 are compared per tile with every 2.401 um level-3 slice 24..84. The slope dk/ds9 is 3.51-3.61 on every segment (expected +3.60): the normal directions agree and are not flipped. The best-matching 2.4 um slice departs from the nominal 54 by -0.23 .. +1.49 9-um vox at the centre, and is tilted across segments (e.g. 172804: plane slope -0.0039 slices per 9 um L1 px, residual 1.9 slices).
- Depth-corrected pass (`reg.py --dc`): the 5-slice 2.4 um slab is centred per pixel on a smooth depth field (per-tile best slice, linear interpolation, Gaussian sigma 256 px); then the same tile NCC.
- Gate (as I operationalised it): whole-segment band-passed NCC after the global shift (erosion 21 px) >= 0.80 AND median per-tile residual shift <= 2 px. The null is the same NCC with the images offset by a further (40, 40) px.

Columns: shift d (depth-corrected) | shift d (nominal depth) | NCC mapper only (nominal) | NCC after shift (nominal) | **NCC after shift (depth-corrected)** | null | median tile residual (px) | fraction of tiles with NCC >= 0.80 and residual <= 2 px | tiles used | affine-fit residual RMS (px) | depth offset at centre (9-um vox) | slope dk/ds9 | gate

| segment | d dc (px) | d nominal | NCC map-only | NCC nom | NCC dc | null | resid | frac tiles | n | aff RMS | depth off | slope | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20250510172639 | -0.45, +0.02 | -0.49, +0.06 | 0.826 | 0.832 | 0.859 | +0.008 | 0.92 | 0.97 | 227 | 0.79 | -0.23 | 3.538 | PASS |
| 20250510172804 | -0.97, +1.74 | -1.07, +1.75 | 0.549 | 0.649 | 0.810 | -0.001 | 0.80 | 0.83 | 290 | 0.98 | +1.12 | 3.599 | PASS |
| 20250511200236 | -0.38, +0.13 | -0.38, +0.10 | 0.828 | 0.833 | 0.863 | +0.004 | 0.87 | 0.99 | 168 | 0.77 | -0.20 | 3.512 | PASS |
| 20250919064353 | -0.69, +1.32 | -0.73, +1.39 | 0.604 | 0.678 | 0.816 | +0.002 | 0.89 | 0.86 | 158 | 1.00 | +1.09 | 3.575 | PASS |
| 20250919123506 | -0.46, +0.23 | -0.44, +0.24 | 0.776 | 0.789 | 0.828 | +0.005 | 0.97 | 0.94 | 376 | 0.90 | +0.11 | 3.572 | PASS |
| 20250919124722 | -0.59, +0.49 | -0.53, +0.50 | 0.790 | 0.806 | 0.830 | +0.002 | 0.93 | 0.91 | 317 | 0.86 | +0.24 | 3.576 | PASS |
| 20250919124917 | -0.58, +0.26 | -0.57, +0.24 | 0.829 | 0.841 | 0.862 | +0.008 | 0.74 | 0.99 | 227 | 0.65 | -0.23 | 3.574 | PASS |
| 20250919125302 | -0.36, +0.75 | -0.41, +0.81 | 0.763 | 0.788 | 0.844 | +0.001 | 0.94 | 0.98 | 127 | 0.88 | +0.19 | 3.583 | PASS |
| 20250919125605 | -0.39, +0.87 | -0.43, +0.94 | 0.751 | 0.775 | 0.841 | +0.004 | 0.88 | 0.96 | 161 | 0.85 | +0.22 | 3.592 | PASS |
| 20250919125754 | -0.81, +1.41 | -0.78, +1.51 | 0.609 | 0.683 | 0.813 | +0.002 | 0.89 | 0.90 | 412 | 1.04 | +1.10 | 3.573 | PASS |
| 20250919130642 | -0.83, +1.38 | -0.78, +1.46 | 0.628 | 0.704 | 0.820 | +0.003 | 0.84 | 0.88 | 182 | 0.85 | +1.10 | 3.596 | PASS |
| 20250919131352 | -0.89, +1.50 | -0.87, +1.61 | 0.574 | 0.660 | 0.813 | +0.004 | 0.93 | 0.88 | 403 | 1.01 | +1.17 | 3.578 | PASS |
| 20250919131642 | -0.90, +1.85 | -1.02, +2.04 | 0.458 | 0.569 | 0.802 | +0.002 | 0.98 | 0.87 | 197 | 0.72 | +1.49 | 3.570 | PASS |
| 20250919132115 | -0.73, +1.23 | -0.76, +1.27 | 0.586 | 0.651 | 0.811 | +0.003 | 0.92 | 0.88 | 480 | 1.08 | +1.02 | 3.592 | PASS |
| 20250919133208 | -0.50, +1.29 | -0.68, +1.38 | 0.683 | 0.734 | 0.823 | +0.004 | 0.89 | 0.87 | 276 | 0.86 | +0.43 | 3.611 | PASS |
| 20250919135433 | -0.49, +0.08 | -0.50, +0.06 | 0.802 | 0.815 | 0.839 | +0.004 | 0.90 | 0.92 | 315 | 0.70 | -0.12 | 3.574 | PASS |
| 20250919135915 | -0.43, +0.78 | -0.41, +0.84 | 0.759 | 0.781 | 0.835 | -0.001 | 0.93 | 0.93 | 321 | 0.98 | +0.36 | 3.593 | PASS |
| 20250919140325 | -0.51, +1.18 | -0.64, +1.24 | 0.700 | 0.748 | 0.832 | +0.002 | 0.92 | 0.93 | 333 | 0.97 | +0.52 | 3.588 | PASS |

Reading of the table:
- The shift is stable to <= 0.2 px between the nominal and depth-corrected passes. The tile residual (0.74-0.98 px median; affine-fit RMS 0.65-1.08 px) is at the tile noise level; an affine correction does not reduce it materially, so a translation is sufficient.
- The segments whose shift is largest in y (dy >= 1.2 px: U02, 131642, 172804) are also those with depth offset >= 1 vox. This is consistent with a small tilt of the 2.4 um mesh relative to the 9 um CT (observation only; not investigated further).
- The archive's "(-4, -4) px on one segment" is not reproduced on any CT-registered segment (all |d| < 2.1 px). A (+4.3, +4.3) px offset does appear between the official **labels** and the reference ink map on the 2.401 um canvas (section 2b); that may be the archive's number with the opposite sign convention. Not verified.
- Limitation: the depth field is chosen per tile by maximising coarse CT NCC, so the depth-corrected NCC carries some selection optimism. The 40 px null (~0.00) rules out spurious correlation but does not bound that optimism. A held-out-depth check was not done. The 0.80 gate is passed by 131642 with a 0.002 margin.

### 2b. Official labels vs reference map (segment 125754 only; `labelcheck.py`)
- Of labelled pixels, 81.1 % have ref >= 150; of unlabelled supervised pixels, 5.0 %. Label ink is 22.3 % of supervision; ref >= 150 is 22.0 %.
- NCC(label, ref) is 0.722 at zero offset and 0.722 at the best offset. The best offset is label -> ref = (+4.28, +4.26) canvas px at 2x downsampling ((+4.28, +4.21) at 4x): about 10 um, i.e. 0.5 px on the 9 um canvas. The peak is shallow (NCC gain 0.0007).
- The full-resolution check was killed by the OOM killer (logged, exit 137).
- The label zarr metadata also carries `canvas_offset_yx` (-38.35, -44.94) from its transfer. Our numbers show the label raster is already within ~4 px of the reference map on the canvas, so that offset is not to be applied again.

## 3. Re-trace grouping (papyrus units)
Tools: `overlap.py`, rule module `rules.py`, tests `tests/sib_reg0009b_test_rule.py`.
- Frame: the 8.640 um meshes (vox = 8.64 um). Pairs with raw-vertex distance <= 128 vox: **119 of 153**.
- Both meshes are densified 5 x 5. **Primary rule = CORR-RETRACE-RULE (fail-closed)**: per direction, SAME if (a) nearest-densified-vertex Euclidean bins OR (b) exact point-to-triangulated-surface distance gives >= 1000 points within 2 vox and count[0,1) >= 2 x count[2,3). A pair is SAME if either direction is SAME.
- Result: **28 SAME** (all 28 in both directions; all via form b, 0 via form a). My normal-distance variant (reported, not deciding) gives the identical 28 pairs.
- Units (connected components):

| unit | n seg | segments | summed valid area cm^2 (re-traces double-count) | dense windows (all, before dedupe) | dense windows after 3-D dedupe |
|---|---|---|---|---|---|
| U01 | 9 | 20250919123506, 20250919124722, 20250919124917, 20250919125302, 20250919125605, 20250919133208, 20250919135433, 20250919135915, 20250919140325 | 180.9 | 29 | 9 |
| U02 | 5 | 20250919064353, 20250919125754, 20250919130642, 20250919131352, 20250919132115 | 114.7 | 35 | 11 |
| U03 | 1 | 20250510172639 | 14.4 | 0 | 0 |
| U04 | 1 | 20250510172804 | 17.1 | 8 | 2 |
| U05 | 1 | 20250511200236 | 11.2 | 0 | 0 |
| U06 | 1 | 20250919131642 | 12.3 | 4 | 1 |

**Sensitivity (not the primary grouping; `overlap_offset.py`, `sens_units.py`).**
- For the 53 pairs with >= 1000 surface points within 2 vox, a per-64-vox-cell median signed normal offset was removed.
- Rule-SAME pairs have within-cell MAD 0.05-0.4 vox (0.74 for one small contact). By contrast, the 5 pairs 172639-200236, 172639-124917, 172639-135433, 200236-124917 and 200236-135433 have 300k-500k points near-coincident (MAD 0.57-0.69 vox) under a smooth offset field (cell medians p10..p90 about -4.5..+3 vox), with 15-35 % of their points within 2 vox. The rule calls them NOT SAME because the [2,3) bin is too full.
- A neighbouring sheet cannot coincide with a trace over a third of its area, so these are most likely the same papyrus traced by two trace generations (May 2025 vs Sep 2025), offset by a cross-frame error.
- Strict criterion (MAD <= 0.8 vox and >= 20000 residual points within 2 vox): units S01 = U01 + 172639 + 200236 (11 segments), S02 = U02, S03 = 172804, S04 = 131642.
- **Consequence for any exclusion or FL-09 use:** treat 172639 and 200236 as the same papyrus as U01 (the stricter choice). This needs a declaration (proposal below).
- Not run: the same grouping on the 2.401 um meshes. 5 x 5 densification there needs ~27 GB RAM (> 15 GB); logged as stopped.

## 4. Candidate-window statistics (reference maps only)
Tools: `windows.py` and `dedupe.py`; outputs `windows.json` and `windows_dedupe.json`.
- The official 2.401 um reference ink maps are reduced to per-mesh-cell counts (20 x 20 px).
- Windows: 417 x 417 cells = 8340 px = 2.002 cm, stride 1 cm. Per window: mesh-valid fraction, ink fraction (px >= 150, and >= 128, of valid px), and spread (fraction of ~1 mm blocks with >= 5 % ink).
- **Dense (primary)** = valid >= 0.90, ink150 >= 0.05, spread >= 0.25.
- Across the 18 segments: 76 dense windows before dedupe.
- Global 3-D dedupe: greedy by ink150, across all segments regardless of unit. A window is rejected if >= 10 % of its mesh points lie within 10 (or 20) 2.4-um vox of an accepted window. Both tolerances give 23.
- Other bars (summed over segments, before dedupe; `windows.json` counts_grid): valid >= 0.75 with ink >= 0.02 gives 161; valid >= 0.90 with ink >= 0.10 and spread >= 0.50 gives 23.
- Ink map values: on every segment the 10-90 % deciles lie at 0-175; the background level is ~31-36.

The 23 deduplicated windows. Boxes are x0, y0, x1, y1 in px. The 9 um canvas box comes from the corrected mapper, as coordinates only; a box starting at canvas-2 x = 0 maps to about -8 px and must be clamped to 0.

| # | unit | segment | 2.401 um canvas box | 8.64 um canvas box | ink150 | spread | valid |
|---|---|---|---|---|---|---|---|
| 1 | U06 | 20250919131642 | [4160, 12480, 12500, 20820] | [1148.5, 3459.5, 3467.3, 5775.0] | 0.244 | 0.68 | 1.000 |
| 2 | U02 | 20250919125754 | [8320, 12480, 16660, 20820] | [2303.1, 3458.7, 4619.7, 5773.9] | 0.236 | 0.65 | 1.000 |
| 3 | U01 | 20250919140325 | [0, 16640, 8340, 24980] | [-7.7, 4616.9, 2307.8, 6933.9] | 0.235 | 0.66 | 0.966 |
| 4 | U02 | 20250919131352 | [8320, 16640, 16660, 24980] | [2303.0, 4613.8, 4619.7, 6929.1] | 0.224 | 0.62 | 1.000 |
| 5 | U01 | 20250919133208 | [0, 12480, 8340, 20820] | [-7.7, 3459.6, 2310.5, 5775.5] | 0.221 | 0.63 | 0.981 |
| 6 | U02 | 20250919125754 | [8320, 4160, 16660, 12500] | [2303.1, 1149.0, 4619.7, 3464.2] | 0.199 | 0.60 | 1.000 |
| 7 | U02 | 20250919132115 | [8320, 12480, 16660, 20820] | [2302.8, 3461.2, 4619.0, 5778.2] | 0.188 | 0.53 | 1.000 |
| 8 | U02 | 20250919131352 | [8320, 8320, 16660, 16660] | [2303.0, 2304.0, 4619.7, 4619.4] | 0.186 | 0.53 | 1.000 |
| 9 | U02 | 20250919130642 | [8320, 8320, 16660, 16660] | [2302.6, 2304.2, 4618.8, 4619.8] | 0.158 | 0.50 | 0.928 |
| 10 | U01 | 20250919133208 | [4160, 4160, 12500, 12500] | [1148.6, 1149.2, 3466.8, 3465.2] | 0.150 | 0.52 | 1.000 |
| 11 | U01 | 20250919140325 | [4160, 4160, 12500, 12500] | [1147.3, 1149.7, 3462.9, 3466.7] | 0.150 | 0.57 | 1.000 |
| 12 | U02 | 20250919132115 | [8320, 4160, 16660, 12500] | [2302.8, 1149.7, 4619.0, 3466.8] | 0.148 | 0.48 | 1.000 |
| 13 | U02 | 20250919132115 | [0, 16640, 8340, 24980] | [-8.0, 4616.9, 2308.3, 6934.0] | 0.127 | 0.42 | 0.942 |
| 14 | U04 | 20250510172804 | [8320, 4160, 16660, 12500] | [2302.9, 1150.7, 4619.6, 3468.6] | 0.113 | 0.50 | 1.000 |
| 15 | U01 | 20250919123506 | [8320, 8320, 16660, 16660] | [2305.3, 2303.8, 4623.7, 4620.1] | 0.101 | 0.40 | 1.000 |
| 16 | U02 | 20250919125754 | [0, 12480, 8340, 20820] | [-8.0, 3458.7, 2308.6, 5773.9] | 0.091 | 0.31 | 0.972 |
| 17 | U01 | 20250919140325 | [8320, 12480, 16660, 20820] | [2302.3, 3461.2, 4617.9, 5778.2] | 0.079 | 0.36 | 0.919 |
| 18 | U01 | 20250919123506 | [8320, 16640, 16660, 24980] | [2305.3, 4614.5, 4623.7, 6930.8] | 0.078 | 0.36 | 1.000 |
| 19 | U02 | 20250919132115 | [0, 4160, 8340, 12500] | [-8.0, 1149.7, 2308.3, 3466.8] | 0.073 | 0.29 | 0.905 |
| 20 | U01 | 20250919124722 | [4160, 8320, 12500, 16660] | [1147.7, 2303.7, 3464.4, 4619.6] | 0.072 | 0.31 | 1.000 |
| 21 | U02 | 20250919125754 | [0, 4160, 8340, 12500] | [-8.0, 1149.0, 2308.6, 3464.2] | 0.071 | 0.33 | 0.970 |
| 22 | U04 | 20250510172804 | [0, 4160, 8340, 12500] | [-8.2, 1150.7, 2308.5, 3468.6] | 0.065 | 0.27 | 0.963 |
| 23 | U01 | 20250919135915 | [8320, 8320, 16660, 16660] | [2304.4, 2303.5, 4622.0, 4619.0] | 0.058 | 0.26 | 1.000 |

- Windows on the labelled segment 125754 (`window_labels.json`): window 2 has 30.2 % of its area in the official supervision region (6.2 % in validation); window 16 has 7.2 %; windows 6 and 21 have 0 %.
- Nothing here judges letters. Whether a window holds >= 5 nameable letters is the picker's call, made on 2.4 um displays only.

## Exact commands (all logged in runs.jsonl with utc, exit code and output sha256)
```
uv venv /opt/hv --python 3.11; uv pip install numpy scipy opencv-python-headless tifffile imagecodecs zarr(>=3) numcodecs pytest boto3 s3fs fsspec
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/fetch.py             # inventory + downloads (sha256)
tools/sib/reg0009b/pipeline.sh    # per segment: reg.py <seg>; depthcheck.py <seg>; reg.py --dc <seg>
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/overlap.py 9
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/overlap_offset.py 9
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/sens_units.py
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/windows.py
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/dedupe.py
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/window_labels.py
LC_F=4|2 tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/labelcheck.py 20250919125754-auto_grown_20250919055754487_inp_hr
tools/sib/reg0009b/runlog.sh <out> /opt/hv/bin/python tools/sib/reg0009b/summarize.py
/opt/hv/bin/python -m pytest -q tests/sib_reg0009b_test_rule.py tests/sib_reg0009b_test_ncc.py   # 8 passed
```
(PYTHONPATH=src for scripts importing hercules.geometry.)

## Failures and deviations (all recorded)
- A recursive S3 listing descended into SV chunks: too slow, stopped, and replaced by a per-directory walk.
- First reg.py run crashed (IndexError in the sub-pixel helper, bound off by one). Fixed, and all outputs of that version were discarded and recomputed.
- First overlap run stopped to add a histogram. The normal-distance-only grouping was superseded by the CORR-RETRACE-RULE fail-closed form: same 28 pairs and 6 units.
- 2.401 um-frame overlap sensitivity not run (memory). windows.py was OOM-killed once when run beside the full-resolution label check; it was rerun cleanly. The full-resolution label check itself was OOM-killed and not rerun (2x and 4x agree).
- Three wait loops ended with exit 144 when I killed them: they were waiting on themselves (`pgrep -f` matched their own command line). No data job was affected.
- The first registration version used a nominal 2.4 um slab only. The depth check showed that is insufficient, so the depth-corrected pass was added before any gate was reported.

## What the orchestrator needs to declare next
1. **Registration record:** adopt the per-segment corrected mapper (the `d` column, depth-corrected) for KTLB-M, with the gate numbers above. Decide whether the depth-corrected gate is acceptable given its selection optimism, or require a held-out-depth check (131642 margin 0.002).
2. **Units:** primary = the 6 units under CORR-RETRACE-RULE. Decide whether the 5 offset-field pairs merge 172639 and 200236 into U01 for exclusions (recommended: fail-closed, merge). Window counts are the same either way.
3. **Picker material:** the 23 deduplicated windows (U01 9, U02 11, U04 2, U06 1) are the candidate pool. The picker needs >= 5 nameable letters per window on the 2.4 um references, and sealing must happen before any 9 um map of them. Decide whether windows overlapping official labels/supervision (window 2: 30 %; window 16: 7 %) are allowed in a sealed benchmark.
4. Before any 9 um MAY read (DECL-HANDED): 0009B's depth direction relative to its 2.4 um volume is the same (slope +3.5..+3.6). That is not the reading-handedness test, which is still owed.
5. Proposal text: `proposals/DECL-KTLBM-MATERIAL-proposal.md`.

## Addendum 2026-09-26: 0009B DEV room under DECL-DEVLOOP-A1 item 7 (devzone.py, devzone.json)
- The registry v3 same-papyrus union (vertex, point-to-surface and normal-distance forms) gives the same 28 SAME pairs and 6 units as above. The vertex form finds 0; the surface and normal forms find 28 each, and the pair sets are identical.
- Area outside every KTLB-M candidate window + 144 vox, strict reading (8.64 um vox, plus a 2h vertex-sampling margin: threshold 550 2.4-um vox):
  - with the 23-window pool excluded: 99.4 cm^2, 0 fully allowed 2 x 2 cm windows, 5 blanks;
  - with all 76 dense windows excluded: 34.1 cm^2, 0 windows, 0 blanks.
- Lenient reading (144 2.4-um vox): 188.7 / 136.6 cm^2, 15 / 2 windows (none with ink150 >= 0.05), 67 / 46 blanks.
- 0009B therefore cannot supply inked DEV windows unless KTLB-M seals a subset and the rest of the pool is released. This is in ASK.md.
- Blob-f180 on blanks needs a model map and is not computed.
