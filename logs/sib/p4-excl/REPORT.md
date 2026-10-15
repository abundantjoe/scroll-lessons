Provenance: Project HERCULES | owner the owner | [id removed]

# p4-excl REPORT: labelled-adjacency flags for the Paris 4 tiles (DECL-P4-2 item 1, DECL-P4-4 item 2)

No image, map or CT pixel was opened, viewed or described. The only inputs were mesh coordinates, JSON metadata and hashes.

## Inputs
- The 8 labelled segments (20231016151002, 20230702185753, 20231031143852, 20231106155351, 20231012184424, 20231210121321, 20231007101619, 20230929220926): official tifxyz meshes on 20260411134726, fetched anonymously from s3://vesuvius-challenge-open-data. The sha256 of every file is in downloads.jsonl. Each bbox equals its meta.json bbox exactly (structures.json).
- Voxel size: 0.0024 mm, from the 20260411134726 metadata.json field scan.tomo.acquisition.detector.samplePixelSize (sha256 881bf77f...). So 1.2 mm = 500 vox.
- Tile points: tile_points.npz from the tiles-a/-b branches. The commit, git blob and sha256 are in each output file.
- Strip meshes for the all-vertex check (sha256 in downloads.jsonl):
  - w010-027 / w028-037 (20260701), on 20260411134726. The w028-037 hashes equal the tiles-b manifest.
  - 20260623 M2a / M2b, their 20260411134726-frame meshes.

## Method (tools/sib/p4-excl/surfdist.py)
- Surface: every tifxyz grid quad with 4 valid corners is split into two triangles, (a,b,e) and (a,e,c). Maximum edge L is 38-50 vox per segment.
- Distance: the exact point-to-triangle distance (Ericson closest point, plus edge-segment minima).
- Candidate search: a KD-tree over the vertices. It relies on a covering bound: every point of a triangle lies within Lc = L/sqrt(3) of one of its vertices. Hence:
  - d_s >= d_v - Lc, where d_v is the distance to the nearest vertex;
  - all triangles incident to the vertices within ub + Lc contain the true nearest point.
- Result: exact with no densification, the CORR-RETRACE-RULE form (b).
- Per tile: the minimum over its points of the exact distance, computed per segment. The tile keeps the minimum over segments and the segment that attains it. Flag: min_mm < 1.2.
- All-vertex check (fail-closed): the npz holds 4096 random vertices of about 1.1e5-1.7e5 per tile, so its minimum can overstate the tile minimum. The check therefore also uses every valid vertex of the tile, rebuilt with the tiler's own rule (vertex counts equal the tiler's for all tiles; every npz point is a member of that set).
  - P4-D: the 20260411134726-frame mesh vertices inside the tile's UV rectangle, widened by one grid cell. The UV map is i24 = (i + 0.5)·h24/h1129 - 0.5; my recomputation of the builder's same-UV points gives a maximum error of 0.004 vox over 433,934 points.
  - Refinement stops early once an exact distance <= 0.5 vox is attained; this only affects tiles far below the threshold.
- labelled_adjacent = the npz flag OR the all-vertex flag.

## Tests
- tests.json: 21 of 21 pass on synthetic sheets. The batched method, the per-point loop and brute force agree to 0 on random curved sheets with holes. The cases are:
  - a plane at known heights, including cell centres where the nearest vertex is 14 vox away;
  - a V fold (inside, below the crease, normal offset);
  - a U fold between layers;
  - a hole rim;
  - an equilateral lattice (the worst case for the L/sqrt(3) radius);
  - a far point at 3000 vox.
- realcheck_20231016151002.json: on the real mesh, 200 on-surface points give a maximum of 1.6e-11 vox. Points offset along the normal by h are never measured above h.

## Results
| file | strip | tiles | npz flag | all-vertex flag | labelled_adjacent |
|---|---|---|---|---|---|
| excl_a.json | w010-027 | 160 | 120 | 120 | 120 |
| excl_b.json | w028-037 | 171 | 138 | 139 | 139 |
| excl_d_b.json | M2b 20260623142658-w028-037 | 106 | 106 | 106 | 106 |
| excl_d_a.json | M2a 20260623141924-w010-027 (= E1 grid) | 100 | 100 | 100 | 100 |

- Flag change: w028-037 r6_c15 reads 1.342 mm from the npz points but 1.188 mm from all vertices, so it becomes adjacent.
- The largest npz-minus-all-vertex gap is 0.252 mm (b) and 0.200 mm (a).
- Single tile, w010-027 r6_c4: all 174,306 vertices give 4.967 mm (20231012184424), so it is not adjacent.
- Tiles near the threshold on w010-027 (all-vertex): r5_c18 at 0.82 mm and r5_c19 at 1.03 mm, both flagged.

- M2a: npz points via the builder's published affine; my pixel-centre same-UV map agrees with them to median 0.01 vox, max 19.83 vox (the affine's own landmark residual is about 1-2 vox), so the grids do correspond. Largest tile minimum 0.793 mm.
- The M2a and E1 grids are numerically identical (grid_equality_m2a_e1.json).

## Timings (4 vCPU)
- Build of the 8 structures: 91 s.
- npz pass: 123 s (b) and 474 s (a).
- All-vertex pass: 2135 s (b) and about 15,000 s (a, run concurrently with other jobs).
- P4-D M2b, both passes: 2447 s.
- Per-segment timings are in each JSON.

## Limits
- The distances are to the official triangulated meshes; mesh error relative to the papyrus is not assessed.
- The quad diagonal choice changes the surface by less than a quad's non-planarity.
- Tile surface points between vertices are within Lc_strip of a tile vertex, and distance is 1-Lipschitz, so the true tile-surface minimum can be up to Lc_strip (about 0.04-0.06 mm) below the all-vertex minimum. A flagged tile stays flagged, because a measured value is never below the true minimum. An unflagged tile below 1.30 mm needs a dense check: only w028-037 r6_c7 (1.254 mm), whose check is running (tools/sib/p4-excl/dense_tile.py, triangles sampled at barycentric step 1/8, output dense_w028-037_r6_c7.json). Result: dense min 1.253468 mm (20231012184424), sample gap bound 2.716 vox, lower bound 1.24695 mm >= 1.2: certified not adjacent. Every unflagged tile in excl_a, excl_b and excl_d_b is therefore certified >= 1.2 mm.
