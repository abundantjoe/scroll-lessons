# p4-inner status (2026-09-26T10:15Z)
Recommendation: w000-009 (~55-80 cm², a core of r ≈ 0.7-1.6 mm with a ~0.1 mm inferred pitch) has no official mesh or 2D ink, so it is truly "somewhere new". Before any commitment, first build VC3D and test whether the surface-m7 L2 prediction separates sheets in one 2×2 cm core window inside the 1.129 um footprint (z 67-135 mm). Measure it by sheet count vs. the expected 10 windings and by seam consistency with w010. Do not start a full-strip trace or a 2.4 um ResNet-152 run on CPU.

## 2026-09-26T17:50Z: DECL-P4-7 items 1-2 (1.129 um), in progress
- Method, fixed before any inner count was read:
  - Centre: the official umbilicus per z, mapped to the 1.129 um frame with the volume's transform.json (landmark residual 0.2-1.9 vox at 2.4 um).
  - w010-w020 per ray: exact crossings of the 20260623141924-w010-027 mesh's per-z spiral polyline, labelled by unwrapped angle. The mesh gives 18 crossings per ray (17 at partial ends).
  - Sampling: 64 rays x 24 z-levels, z 70-133 mm (2.4 um frame); one full-res z-plane per level, read with byte ranges from uncompressed chunks.
  - Smoothing: Gaussian FWHM 20 um (primary); sigma 20 um (sensitivity).
  - Peak detector: find_peaks, distance >= 20 um. The prominence threshold is picked from a fixed grid by the rule "median peak count in the labelled w011-w020 zone closest to 10".
- For p4-core: the reusable pieces are the ray geometry (`spiral.py` polyline + crossings) and the ray/z sampling grid above. The 2.4 um cross-check can use the same ZS and 64 ray angles.

## 2026-09-26T18:45Z: urgent tile-direction answer (tile_winding_m2a.json, tile_winding_a.json)
1. On both grids, along every row, the column index increases TOWARD the core: smaller radius and lower w.
2. M2a / E1 (20260623141924-w010-027; rows 2-4, 20 tiles each): Spearman(column, median radius) is -0.988, -0.940, -0.946. Radius goes from 4.7-5.4 mm at c0 to 1.7-1.9 mm at the last column.
3. Strip-a (20260701183124-w010-027, T 8343; rows 0-7, 20 tiles each): Spearman is -0.898 to -0.995 (median about -0.987). Radius goes from 4.5-5.4 mm at c0 to 1.4-2.0 mm at c19.
4. Implied winding: c0 is about w027 and the last column about w010-011 (Spearman(column, winding) = -0.998 on every row; labels are uncertain by +/-1 at the strip ends). Mesh column 0 is the outer end (w027) of both official strips.
5. Consequence: any code that assumes "column 0 = w010" is reversed. My own DECL-P4-7 count had this bug; it was caught before any inner count was read, and the count was restarted at 18:3xZ with radius-based orientation. The run-1 output is kept in scratch and is not used.

## 2026-09-26T22:00Z: DECL-P4-7 items 1-2 (1.129 um) done: see REPORT-P47.md and count_1129.json
Result: inconclusive. There is no evidence for more than 10 windings inward of w010: only 1.5-6 % of rays count more than 10, against a required 80 %.
The calibrated detector (sigma 20 um) counts a median of 4 crossings inside w010 (IQR 3-5). Its spacing is about the labelled spacing (172 vs 159 um).
Validation fails, so the count cannot settle the question:
- planted-sheet error is <= 1 only for pitch 100-150 um; below ~100 um the detector under-counts by 3-7;
- adjacent-ray steps of >= 2 occur on 19 % of pairs.
For p4-core: please compare the 2.4 um count per z using the same ZS and ray angles, and note the mesh orientation (column 0 = w027).

## 2026-09-27T01:10Z: DECL-P4-15(a) P4-M-OUT build done (logs/sib/p4-inner/mout/manifest.json)
[line withheld: prize-candidate detail under review]
- **Grid:** T = 8327 px (416.37 px/mm); 11 x 18 = 198 tiles.
- **Eligible:** 138 tiles (valid >= 0.5). The declared `norm_manifest.py` imports all 138.
- **Labelled adjacency:** 0 labelled-adjacent tiles; the minimum distance to the labelled segments is 6.8 mm.
- **Blank tiles:** 11 eligible tiles are exactly 0 over their whole mesh-valid area. They are byte-identical PNGs and have no prediction there. Treat them as blank for the gate, not as "no ink".
- **DIRECTION CONFLICT:**
  - The declared rule (tie-averaged Spearman of column vs per-tile median radius) gives +0.127, i.e. weakly outward = increasing column. Rows range from -0.27 to +0.33.
  - A same-angle crossing check gives the opposite. The strip turns about 719 deg (2 windings). At equal angle, radius DECREASES with column in 93 % of 2731 pairs, so outward = DECREASING column and column 0 is the outer end, as on w010-027.
  - Per-tile radius over only 2 windings is dominated by the scroll's out-of-roundness.
  - I recommend the crossing check. The orchestrator decides before any candidates are formed.

Integrity: no issues.

[line withheld: prize-candidate detail under review]
- **Strips** (20260701 set: eligible / blank / labelled-adjacent):
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - Same code, display and manifest format as mout/.
- **Direction (resolves the earlier conflict):** outward = DECREASING column (column 0 = outer end) on all 4 outer strips.
  - Same-angle crossing check: radius increases with column in only 1.8-6.9 % of pairs.
  - The declared per-tile Spearman is wrongly weak-positive (+0.09 to +0.14) on every strip, because of the scroll's out-of-roundness. It should not be used on the outer strips.
[line withheld: prize-candidate detail under review]
  - Median strip lengths: 32.7, 32.3, 32.2 and 31.8 cm; cumulative offsets 0, 32.7, 65.0 and 97.2 cm.
  - Seam gaps between the strips: median 0.69-0.80 mm, but p90 8-15 mm because the strip ends are ragged row to row. Treat cross-strip s as +/- about 1 cm near seams.
[line withheld: prize-candidate detail under review]

Integrity: no issues.
