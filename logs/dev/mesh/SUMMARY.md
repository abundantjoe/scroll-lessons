# tools/unr/mesh_checks.py — self-test and first real-surface results

Provenance: Project HERCULES | [id removed]. DECL-UNR-1 item 6 / W3 as amended by DECL-UNR-1-A1 (sheet-level numbers at 8.64 um, level 0).
No letters, no readings, no SHEET/PAIR/FUSED classification here: the tool measures, X2 classifies.

## What the tool does
1. Self-intersection and neighbour-crossing: tifxyz grid (2-cell NaN border handled; -1/NaN/0 = invalid) or OBJ -> triangles;
   uniform-grid broadphase (cell = 2 x median triangle extent), exact Moller-1997 interval test, coplanar pairs by 2-D SAT.
   Triangles sharing a vertex are excluded in self mode. Same-side touching (vertex-on-face, edge-on-edge) is NOT an
   intersection; a crossing that passes exactly through a shared grid line is, pair by pair, identical to touching and is
   not counted either (self-test D2 vs D). Every reported pair on ring1/i96 was re-verified by an independent
   segment-plane-barycentric test (30768 / 30768 agree).
2. Stretch: per-triangle Jacobian of uv -> 3-D; area ratio s1*s2 (= A3d / Auv), conformal ratio s1/s2, L2 stretch, max
   interior-angle deviation; median / p95 / max. "Arc-length uv" = rectilinear uv whose column step is the median 3-D
   step of that column over all rows (rows likewise); the nominal grid uv (1/scale = 20 vox per cell) is reported beside it.
3. W3 clearance: profile along the vertex normal (grid du x dv, like tools/fl4/sheetcheck.py), t in [-80, 80] vox, 1-vox
   step, each sample the mean over a 13-point disc of radius 2 vox in the tangent plane, Gaussian sigma 1 along t;
   peaks = scipy find_peaks, prominence >= 3 x MAD(profile) + 1e-6, width >= 3 vox (core_native crossing_balance
   convention); own lamina = nearest peak within own_tol (8 vox) of the vertex, else OFF_LAMINA; clearance +/- = distance
   from the vertex to the nearest other peak on each side; local spacing = (t+ - t-)/2; ratio = min clearance / spacing.
   Bar: ratio >= 0.5 for >= 98 % of all vertices (OFF_LAMINA / NO_PEAKS / OUT_OF_MASK fail); ratio < 0.3 masked and its
   fraction reported. Level-0 chunks via core_native.L0.slab (3 threads), cached in RAM; bytes stated per run.
   Tolerance-free statistic also reported: distance from the vertex to the nearest peak of any status.

## Self-test (selftest.json): 10 / 10 pass
A flat rippled sheet: 0 self-intersections; arc-length uv isometric (area ratio 1.000, angle dev < 1e-12 deg).
B limacon fold (inner loop through outer): 117 intersecting pairs, all within 60 vox of the known crossing line.
C two parallel sheets 44 vox apart: 0 crossings, nearest-vertex distance 44.000.
D two crossing sheets (crossing between grid lines): 98 pairs, all at x = 1590.0 exactly. D2 touching along an edge: 0.
D3 coplanar overlap (sheet shifted half a cell in-plane): counted. E OBJ round trip with vt: identical stretch.
F synthetic laminae (period 44 vox, Gaussian sigma 4 vox, noise 10/255) in a 300^3 volume read through the same chunk
   plumbing (12 chunks, 6 slab calls): on-lamina mesh 44/44 vox, ratio 1.00, bar pass; +5 vox offset 39/49, ratio 0.886
   (= 39/44), own peak -5; midway (+22) OFF_LAMINA for all 144 vertices, bar fail. F2 20-degree tilted mesh: clearance
   along the normal 47 vs 44/cos(20) = 46.8 expected.
Deviations met and fixed during the self-test: (i) crossings exactly on shared grid lines are undetectable pair-wise
(test moved off the grid lines, documented); (ii) single-voxel profiles with thin laminae (sigma 2) let smoothed noise
exceed 3 MAD (5 % false own-lamina) -> 13-point tube average, laminae sigma 4 (81 um FWHM) in the phantom.

## Real surfaces on this branch (ring1, PHerc0268, vc_grow_seg_from_seed, 122 x 122 grid, 20 vox cells, ~4.7 cm^2)
Self-intersection (bar = 0):
| patch | pairs | triangles involved | grid distance of pairs median / p95 (cells) | fold-over (> 5 cells) |
|---|---|---|---|---|
| i96 | 30768 | 48 % | 7.0 / 38.7 | 58 % |
| i97 | 10421 | 18 % | 4.3 / 17.0 | 43 % |
| i99 | 2224 | 6 % | 3.0 / 14.0 | 27 % |
| i101 | 14610 | 27 % | 5.3 / 28.0 | 51 % |
Every ring1 patch fails the bar; the grids cover the same region more than once (fold-over) and crumple at the 2-4 cell
scale. Row/column tangents are far from orthogonal (i96 angle(du,dv) p05/p95 = 29 / 139 deg).
Neighbour crossing: i100 vs i101 0 pairs (nearest vertices 40 vox); i101 vs i102 403 pairs (nearest vertices 2.6 vox).
Stretch, arc-length uv, median / p95: i96 area ratio 0.78 / 1.61, s1/s2 2.11 / 9.30, angle dev 32 / 94 deg;
i99 (best) 1.00 / 1.60, 1.34 / 2.97, 12 / 49 deg. Nominal grid uv is worse (i96 area 1.12 / 2.02). A rectilinear uv of
these grids is not a usable flattening; the stretch bar for the phantom should be set on a non-overlapping grow.

W3 on i96 (full piece, 13924 vertices; 470 chunks = 986 MB level 0, 97 s fetch, 200 s total):
status OK 3315, ONE_SIDED 1505, OFF_LAMINA 8482, NO_PEAKS 284, ISOLATED 338; ratio >= 0.5 for 31.6 % of all vertices
(87 % of the OK ones); masked (< 0.3 or unmeasurable) 65.7 %; bar FAIL. Measured vertices: clearance +/- median 28 vox,
local spacing median 35 vox = 302 um (p05-p95 147-518 um), ratio median 0.83. Tolerance-free: nearest peak at
p25/50/75/90 = 6 / 12 / 21 / 33 vox; a peak within 8 vox for 38 % of vertices, within 12 for 52 %, within 16 for 64 %.
Sensitivity (real_ring1_i96_w3_sensitivity.json): own_tol 8 / 12 / 16 -> ratio >= 0.5 for 32 / 44 / 54 %; tube 3 + sigma 2
makes it worse (30 %). Smoothed normals (box 7 x 7 cells): see real_ring1_i96_normalsmooth3.json and the line below.
Smoothed normals (7 x 7 cells) give the same result: ratio >= 0.5 for 31.1 % of all vertices, nearest peak median
12 vox, within 8 / 12 / 16 vox for 36 / 50 / 62 %. The normals are not the confound; the vertex positions are.

Reading (no bar lowered): on these grown ring1 grids the vertex normals and positions are not consistently on a lamina
peak; the fold-over result says the grid itself is multi-valued, so W3 here measures a crumpled grid, not a sheet. The
pass numbers on the synthetic laminae show the measurement works where the mesh is a single sheet. The real W3 bar
is to be run on X4's assembled pieces (both grows), after the 0-intersection bar, as item 6 orders.

## Not done / caveats
- No OBJ surface from VC3D was available on the branch; OBJ reading is exercised only on the self-test round trip.
- Spacing is "locally measured" as the half-distance between the two neighbouring peaks of the probe; PAIR/FUSED status
  is X2's and is not produced here.
- Threads: OMP/BLAS 3, L0 fetch 3.
