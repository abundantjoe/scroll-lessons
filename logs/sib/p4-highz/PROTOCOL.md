Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz protocol (DECL-P4-6 builder), fixed before any P4-F computation

Written and pushed before any histogram, threshold, tile or screen number exists. It fixes the operational details that DECL-P4-6 leaves open. Nothing here changes a declared bar. Builder role only: no image, tile or CT pixel is ever opened, viewed or described; numbers only.

## Materials and grids (reused exactly)
- E1: `PHercParis4/segments/20260623141924-w010-027/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr`, level 0 (2.258 um isotropic, 116 slices, uint8, uncompressed, chunks 116x128x128). Grid = p4-tiles-b e1/grid.json: T = 8872, 6 x 21 tiles from origin (0, 0); the 60 eligible tiles of p4-tiles-b e1/manifest.json (valid >= 0.5 and frac outside the 1.129 um volume < 0.5; the latter copied from that manifest).
- Control C: `PHercParis4/segments/20260623142658-w028-037/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr`, level 0. Grid = p4-tiles-b m2b/grid.json: T = 8869, 6 x 22 tiles; eligible = valid >= 0.5 and stats.frac_mesh_points_outside_1129_volume < 0.5 from m2b/manifest.json (the METRIC-HASH-27 --coverage rule).
- Mesh-valid mask: tifxyz vertex (gi, gj) valid iff x, y, z are all != -1 and finite; canvas px (i, j) -> vertex (i // 10, j // 10); px outside the canvas are not valid. Check: recomputed per-tile valid fractions must equal the source manifests.
- Chunks absent from the bucket (HTTP 404) are fill 0 and are excluded from every histogram and count; their share is reported.

## Slabs (centre index 58 = n // 2, the p4-tiles-b convention; 2.258 um per slice)
- Sheet slab: slices 52..64 (13 slices, +-13.5 um), as DECL-P4-6 item 2.
- Gap slabs: offsets d with 60 <= 2.258 d <= 120, d = 27..53: slices 5..31 (gap_lo) and 85..111 (gap_hi), 27 slices each.

## Step 1: physics sanity and thresholds
- Sample: each material's level-0 chunk positions that intersect an eligible tile; a random 6 % of them (numpy default_rng(20260926), per material, sorted), fetched whole. Voxels counted only at mesh-valid px of eligible tiles.
- Per material and per tile: 256-bin histograms of the sheet, gap_lo and gap_hi slabs, the per-slice mean profile over all 116 slices, and the histogram of the sheet-slab maximum per px.
- Reported: p50, p99, p99.9, p99.99 (percentile of a uint8 histogram = smallest v with CDF(v) >= q), with zeros excluded (primary) and included; fraction of voxels at 255 (dtype max) and at 0.
- Frozen, from the control's sheet-slab histogram over mesh-valid voxels with value > 0 (0 = masked or no data, as in DECL-P4-5-A1): T_mid = p50, T_hi = p99.9. The same T_mid and T_hi serve E1 (same 1.129 um scan). Written to thresholds.json and pushed before any per-tile number is computed.

## Step 2: numeric screen (every eligible E1 and control tile)
- n_hi = number of sheet-slab voxels > T_hi at mesh-valid px (full coverage, level 0).
- In-sheet fraction f_in = n_sheet / (n_sheet + n_gap_lo + n_gap_hi), raw counts of voxels > T_hi, from the step-1 sampled chunks of that tile (same px for all three slabs). The per-slice-normalised ratio is also reported. For any tile with n_hi > the control's tile p99, f_in is recomputed at full coverage (all chunks, slices 5..111) and that value is the one used.
- Control tile p99 = numpy.percentile(n_hi over eligible control tiles, 99) (linear interpolation).
- DENSE-HOTSPOT: n_hi > control tile p99 AND f_in >= 0.8.
- Autocorrelation: D = per-px count of sheet voxels > T_hi, area-summed to the 1068 x 1068 display grid (53.4 px/mm), divided by the valid px count, on display px that are >= 50 % valid. Masked, mean-subtracted, normalised autocorrelation (FFT, zero-padded, divided by the overlap count and the variance); radial average in 1-px bins; peak = max over radii 2-4 mm (107-214 px) and its radius. Also directional peaks along the display rows and columns (+-2 px strip).
- Rot-90 null: the same statistics on np.rot90 of the tile's arrays. n_hi, f_in and the radial peak are rotation-invariant by construction and are reported to confirm that; the directional peaks swap axes.
- Stroke width of the hi mask (sheet-slab maximum > T_hi at mesh-valid px, level 0): Euclidean distance transform, ridge px = local 3x3 maxima inside the mask, width = (2 DT - 1) x 2.258 um; median, p10, p90 over ridge px. Also: 8-connected components (count, area quantiles), count of components whose bounding box is 0.5-5 mm (letter scale), and mean hi depth (hi voxels per hi px x 2.258 um).

## Step 3: P4-F tiles (E1)
- Per canvas px: m = max over the sheet slab (level 0); value = clip(255 (m - T_mid) / (T_hi - T_mid), 0, 255) as float32; 0 at px that are not mesh-valid; cv2.INTER_AREA from T x T to 1068 x 1068; rounded to uint8; builder.png_bytes; chunks IHDR/IDAT/IEND asserted.
- Output logs/sib/p4-highz/f1/{manifest.json, tiles/}, manifest format of p4-tiles-b e1 (png_sha256, valid_fraction, stats incl. frac_mesh_points_outside_1129_volume). Control tiles get screen numbers only, no PNG.

## Validation reported
- In-sheet vs gap fraction; control vs E1 KS statistic (voxel histograms and per-tile n_hi density); the rot-90 null; stroke widths vs the 15-60 um thin-layer expectation; depth profile (sheet brighter than gaps confirms the slab is on papyrus).

## Sub-siblings
- None planned. Measured: ~450-480 range requests/s from this container (6 processes x 24 threads), so level 0 for both strips (~0.6 M chunk reads) takes ~25 min here. Spawning, briefing and merging sub-siblings would not finish materially sooner. Recorded in SUBSIBS.md.
