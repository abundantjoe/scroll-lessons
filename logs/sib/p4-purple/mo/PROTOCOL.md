Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple-mo PROTOCOL: colour-agnostic morphology gate (DECL-P4-16 item 4), control strip only

Written 2026-09-26, before any feature number, any face position and any voxel value of this task was computed.
The only numbers that exist so far are:
- bucket listings (key names and sizes);
- the zarr metadata;
- a streaming-throughput test (bytes per second only; no value was decoded);
- the tile draw below (indices only).

Builder role only. No image, tile, slice or CT pixel is ever opened, viewed or described. Numbers only.

## 0. Fence
- Material: the control strip 20260701183125-w028-037 only.
  - Surface volume: `surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr`, level 0.
  - Shape 109 x 71600 x 174640, uint8, uncompressed chunks of 109 x 128 x 128.
  - 2.4 um slices; the mesh is at slice 54; offset o(k) = (k - 54) x 2.4 um.
- Nothing on w010-027 is touched: no fetch and no number of any kind. The optional 1.129 um control is not used.

## 1. Ground truth (frozen now)
- Existence check (listing only, no pixel read):
  - `PHercParis4/segments/20260701183125-w028-037/` holds `ink-detection/`, `mesh/`, `surface-renders/` and `surface-volumes/`. There is no `ink-labels/` prefix.
  - Organizer human ink labels exist on other segment canvases (for example `segments/20230702185753/ink-labels/...`), but not on the w028-037 canvas.
  - Therefore the brief's fallback applies.
- Labels: the official 2.4 um prediction of w028-037, as recorded in the p4-tiles-b manifest (sha256 of manifest.json c9a5668c...):
  - key `PHercParis4/segments/20260701183125-w028-037/ink-detection/PHercParis4-20260701183125-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif`;
  - 1207687349 bytes, sha256 698795e1...;
  - a tiled deflate TIFF of 1024 x 1024 tiles, whose shape equals the canvas.
  The file is read by HTTP range requests, tile by tile, and never viewed.
- Label grid: 19.2 um cells, i.e. 8 x 8 canvas px blocks, globally aligned (cell (i, j) = canvas rows 8i..8i+7, cols 8j..8j+7).
  - pred_cell = the mean of the 64 prediction px.
  - A cell is mesh-valid iff all 64 px are mesh-valid. The canvas_mask rule is from p4-tiles-b grid.json: grid (floor(i/20), floor(j/20)) of the official tifxyz on 20260411134726, with x, y, z != -1 and finite.
- Recipe (DECL-P4-9):
  - p90 and p50 are pooled over the mesh-valid cells of all gate tiles;
  - ink = pred_cell >= p90, background = pred_cell <= p50;
  - cells within 50 um of the nearest non-class cell are excluded. The distance is the EDT on the cell grid x 19.2 um; the tile edge counts as non-class (p4-crackle class_masks).
- The class masks are identical for every test. Each test uses the class cells where its own feature is finite.
- Disclosure: the AUC measures agreement with a model (the organizers' ink detector), not with human ground truth. A feature could be right where the model is wrong, or share the model's biases (the model sees the same CT). A pass means "carries the same information as the model's ink call on known text", not "is ink".

## 2. Tiles (fixed seed, drawn before any voxel read)
- Grid: p4-tiles-b grid.json, T = 8301 px (20 mm), 9 x 22.
- Eligible: valid_fraction >= 0.5 in the p4-tiles-b manifest, 171 tiles, in sorted (r, c) order.
- perm = numpy.random.default_rng(20260928).permutation(171).
  - Dev tiles are perm[:4]: r2_c3, r4_c6, r4_c17, r6_c9.
  - Gate tiles are perm[4:20] (16 tiles, disjoint from dev): r0_c20, r1_c9, r2_c9, r2_c14, r2_c17, r3_c6, r3_c12, r3_c17, r4_c7, r5_c1, r5_c8, r5_c15, r5_c17, r6_c15, r7_c16, r7_c18.
- A cell belongs to a tile iff its 8 x 8 block lies fully inside [rT, (r+1)T) x [cT, (c+1)T).
- Dev tiles are used ONLY for the following, and no AUC or ink/background statistic of any feature is computed on them:
  - (a) T_face (section 3);
  - (b) the planted positive control (section 6);
  - (c) engineering diagnostics: fraction of cells with a face found, and runtime.
- Engineering changes are allowed only on face-finding failure (for example a found-face fraction < 0.5 on mesh-valid cells). They must be written as a dated amendment before any gate-tile voxel is read.

## 3. Per-column profile and faces (shared by all features)
Processing is in chunk-aligned windows of 1024 x 1024 canvas px (8 x 8 chunks), covering every chunk that overlaps the tile. Chunks are streamed, reduced and discarded. A 404 chunk makes its cells invalid.
1. Block profile: the 4 x 4 canvas px mean of each slice gives a 9.6 um cell profile P(k), k = 0..108. It is smoothed along k with a Gaussian of sigma 1 slice (scipy gaussian_filter1d, mode nearest).
2. T_face (frozen from the dev tiles before any gate read):
   - Pool the 256-bin histogram of the smoothed P over all k and all mesh-valid 9.6 um cells. The cells come from the central 2 x 2 windows (2048 x 2048 px, chunk-aligned at the tile centre) of each of the 4 dev tiles.
   - Smooth the histogram with a Gaussian of sigma 2 bins.
   - The two modes are the two highest local maxima that are at least 20 grey levels apart. T_face is their midpoint (the brief's "midpoint of the void and papyrus grey modes").
   - If no two such maxima exist, T_face = the Otsu threshold of the same histogram. Which rule was used is reported.
3. Centre validity: a cell is analysable iff P(54) >= T_face, i.e. the mesh lies inside papyrus.
4. Face '+': the first k > 54 with P(k) < T_face and P(k+1) < T_face (2-slice persistence against internal pores).
   - The sub-voxel crossing is z+ = (k-1) + (P(k-1) - T_face) / (P(k-1) - P(k)).
   - Height h+ = (z+ - 54) x 2.4 um.
   Face '-' is the same with k < 54, giving h- = (54 - z-) x 2.4 um.
   - Both heights are positive outward, so "raised" = larger h on each face.
   - A face is missing if no crossing is found in 0..108.
   - A face is also missing if its |offset| > 120 um (volume edge or a touching neighbour winding).
5. Pooling to the label grid: a 19.2 um feature value = the mean of its 2 x 2 child 9.6 um values. It is finite only if all 4 children are finite.
Trend maps and filters (features below) are computed per tile on the 9.6 um cell grid, by normalized convolution over finite cells (the Gaussian of the value x mask divided by the Gaussian of the mask), before pooling. Cells that were not finite stay not finite.

## 4. Features (fixed list: 5 features, 9 tests), with declared signs
Each AUC is P(feature at an ink cell > feature at a background cell), with the declared sign applied.
- F1 face height residual, per face (tests F1+, F1-): h - G_0.5mm * h (sigma 500 um = 52.083 cells). Sign: ink = raised (larger).
- F2 sheet thickness residual (test F2): t = h+ + h- (face-to-face distance), t - G_0.5mm * t. Sign: ink = thicker.
- F3 indentation, per face (tests F3+, F3-): F3 = sigma^2 x LoG_sigma(h) with sigma = 150 um (15.625 cells; scipy gaussian_laplace on h, with non-finite cells filled by the 0.5 mm trend value before filtering and re-masked afterwards). Sign: ink = concave (a depression gives F3 > 0; larger).
- F4 roughness, per face (tests F4+, F4-): the local SD of the F1 residual in an 11 x 11 cell box (105.6 um), by normalized box filters over finite cells, requiring >= 61 finite cells in the box. Sign: ink = rougher (larger).
- F5 crackle DoG energy at the face, per face (tests F5+, F5-).
  - Recipe (DECL-P4-9, scaled to 2.4 um): per slice, at full canvas resolution in the window, the DoG with sigma 1.411 and 5.645 px (1.5 and 6 px x 2.258/2.4; cv2.GaussianBlur, ksize = 2*ceil(3 sigma)+1, BORDER_REFLECT), squared, then the 4 x 4 block mean.
  - For each cell and face: the mean over slices round(z) - 4 .. round(z) + 4 (+-9.6 um about that face's crossing), clipped to 0..108.
  - Sign: ink = higher energy.
  - p4-depth and p4-tiles-b have frozen no d* (checked at p4-depth c39d977: calibration running; no calib.json). The face found by F1 is therefore used, as the brief directs.
- Faces: p4-depth's recto/verso sign is not yet published (calib_params.json only describes how it will be measured). Both faces are therefore tested, with Bonferroni over all 9 tests.
- Secondary descriptive quantities (not gated):
  - median(ink) - median(bg) in um for F1+/-, F2 and raw h+/-;
  - the fraction of cells with each face found.

## 5. Statistics and gate
- Point AUC: exact, from ranks with average ties (scipy rankdata), over the pooled gate-tile class cells where the test's feature is finite.
- Tile bootstrap:
  - 2000 resamples of the 16 gate tiles with replacement, numpy default_rng(20260929);
  - the AUC from 4096-bin histograms whose bin edges are the pooled quantiles of that test's feature over its class cells (the histogram AUC counts ties as 1/2);
  - the histogram point AUC is also reported, to show the discretisation error.
- CIs: the percentile 95 % CI, and the Bonferroni-adjusted CI for m = 9 tests (percentiles 100 x 0.05/18 and 100 x (1 - 0.05/18), i.e. 0.278 % and 99.722 %).
- Rot-90 label null, per tile:
  - the 19.2 um prediction map and its mesh-valid mask are placed in a square of side ceil(T/8) = 1038 cells (padded not-valid) and rotated by np.rot90 (k = 1);
  - the analysis cells are mesh-valid AND rotated-mesh-valid;
  - p90/p50 are recomputed on the rotated pool, and the same 50 um exclusion is applied;
  - the features are not rotated.
  - Required for each test: null AUC in [0.47, 0.53].
- Per-tile AUC table for every test (aligned and rot-90), with ink/background cell counts.
- GATE per test: PASS iff all of the following hold. Otherwise FAIL.
  - point AUC >= 0.70;
  - the Bonferroni-adjusted CI lower bound > 0.60 (which implies the 95 % lower bound > 0.60; both are reported);
  - rot-90 null in [0.47, 0.53];
  - for F1 and F2 only, the positive control (section 6) passed for that face.
- A test with AUC <= 0.30 is reported as a strong reversed association, NOT a pass. Any use of it needs a new declaration.
- No threshold, sign, scale, feature or tile is changed after any gate-tile number exists.

## 6. Pipeline positive control (dev tile r2_c3, central 2048 x 2048 px region)
- Glyph mask (canvas px, centred in the region):
  - a ring of outer radius 1.2 mm and stroke 0.4 mm;
  - plus a straight bar 0.4 mm wide through the ring centre at 45 degrees, 3.0 mm long.
  It is a generic synthetic shape, not a letter of any text. 1 mm = 416.67 px (2.4 um per px).
- Planting, into the real control voxels in memory (never written back, never viewed):
  - face positions are first computed on the unplanted data (section 3);
  - for each canvas px in the glyph, on the chosen face, voxels outward of the face crossing, from the crossing to crossing + D, are set to max(V, v_pap). The partial last slice is set to V + f (v_pap - V), where f is its fractional overlap;
  - v_pap = the median of that 9.6 um cell's smoothed profile over the 5 slices just inside the face.
- Runs: D = 5, 10, 20 um, on face '+' and on face '-' separately (6 runs). The full section 3-4 pipeline is rerun on the planted data, with the trend etc. computed over the region.
- Reported, on 9.6 um cells, for the planted-face F1 and for F2:
  - recovered = median over glyph cells eroded by 50 um, minus median over non-glyph cells >= 100 um from the glyph;
  - AUC of glyph against those non-glyph cells;
  - the opposite face's F1 recovered height (specificity; expected ~0).
- Pass (per face): at D = 10 um, F1 recovered in [5, 13] um and F1 AUC >= 0.90, and F2 recovered in [5, 13] um.
  - The bound 0.5 D is chosen because the 0.5 mm trend is predicted to absorb part of a 0.4 mm stroke; the ~30 % loss is an analytic estimate for an isolated line.
- If the positive control fails for a face, F1/F2 on that face cannot pass. A gate FAIL there is reported as "pipeline insensitive", not as a physical null.
- The D = 5/10/20 series gives the detection curve (recovered vs planted).

## 7. Unit tests (synthetic arrays, before any real voxel is processed)
- Synthetic sheet profiles with known faces (sub-voxel positions, noise SD 8 grey levels): recovered face error, median < 0.5 um.
- The 2-slice persistence rejects a 1-slice internal pore.
- The AUC on identical distributions is 0.5; a shifted distribution matches the analytic value.
- A rot-90 of a square array round-trips.

## 8. Outputs
- logs/sib/p4-purple/mo/: PROTOCOL.md (this file), STATUS.md, tface.json, posctl.json, gate.json, REPORT.md.
- tools/sib/p4-purple/mo/: code.
- Per-tile cell maps stay in the scratch space and are summarised by sha256 in gate.json. No image files are produced.

## 9. Implication rule (for REPORT)
- A test that passes becomes a colour-agnostic candidate channel. Its title-zone use needs a separate declaration by the orchestrator.
- No title-zone number is ever computed in this task.

## Amendment A1 (2026-09-27, before any positive-control, gate-tile or AUC number)
Trigger (PROTOCOL section 2 (c), engineering on face-finding failure). tface.json at commit 55d564f+1 recorded the following on the dev regions:
- T_face = 79 (mode midpoint, modes 43 and 115);
- on dev tile r2_c3, the fraction of mesh-valid cells with P(54) >= T_face is 0.482, and the face '+' fraction is 0.479, below 0.5 (other dev tiles: 0.54-0.65).
The dominant loss is the centre rule: at slice 54 the official mesh is not in above-threshold papyrus in ~40-50 % of cells.
Change (it replaces section 3 items 3-4; everything else is unchanged):
- Sheet anchor: k* = the argmax of P(k) over |k - 54| <= 12 slices (+-28.8 um). A cell is analysable iff P(k*) >= T_face.
- Face '+': the first k > k* with P(k) < T_face and P(k+1) < T_face. Face '-': the first k < k* with P(k) < T_face and P(k-1) < T_face.
- Interpolation, heights (still measured from the mesh, slice 54: h+ = (z+ - 54) x 2.4, h- = (54 - z-) x 2.4), the 120 um limit, and all features are unchanged.
- A face whose crossing lies on the wrong side of slice 54 (h < 0) is kept; heights are signed.
Sensitivity: gate-tile AUCs under the original rule (section 3 items 3-4) are also computed and reported. They are descriptive only, not gated and not Bonferroni-counted.
T_face stays 79: its rule does not depend on the change.
