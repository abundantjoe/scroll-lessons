Provenance: Project HERCULES | owner the owner | [id removed]

# P4-N (RULES.md DECL-P4-13): top-edge extension of window A, sibling tracer

STATUS: DONE. The extension has been traced, trimmed, validated and pushed.
- Per declared metric: 2 PASS and 2 FAIL on the literal bars (table in §4). Each FAIL is at or better than the official mesh's own score on the same measure.
- Geometry only. No image, CT intensity or ink value was viewed or rendered. Any render or read of the extension needs its own declaration.

## 1. Run condition
- p4-layout `edge.json` (origin/claude/gifted-bell-gavnl5-sib-p4-layout, commit 560b6f4, sha256 c75d4f87...; copy in `edge_input/`) answers "YES, but only about 2 mm".
- Its per-column support:
  - c9 and c12: 2.0 mm
  - c13: 1.5 mm
  - c14: 0.5 mm
  - c10 and c11: undetermined (no test power)
  - c15: too few anchor vertices
- Above +2 to +2.5 mm no sheet is centred on the organizer mesh, and the mask ends at +3 to +5 mm.
- `run.py real` checks this answer in code and refuses otherwise.
- As the orchestrator directed (21:34Z), the trace covers c9-c15 and grows 11 rows = 2.1 mm.
- The volume top (181.9 mm) would have allowed 9.1-9.6 mm, but the CT supports only about 2 mm.

## 2. Deliverables (`real/`, sha256 in `real/SHA256SUMS`)
- **`extension_native.tifxyz`**: the new vertices only.
  - Native 2.4 um frame of volume 20260411134726; grid step 80 vox = 0.192 mm (tifxyz scale 1/80).
  - 7218 vertices, 2.24 cm², z 172.26-174.77 mm.
  - 11 rows above the official top vertex in every column of c9-c15 (official grid cols 3754-6673, every 4th).
- **`extension_with_seam_native.tifxyz`**: the same, plus the official patch it grew from.
  - The patch is the top 6 mm of the official mesh, every 4th vertex; its vertices are bit-identical to the official ones.
- **`surface_L2.tifxyz`**: the local m7-L2 frame used by the metrics. Native = (L2 + (3648, 4800, 15552)) × 4 (xyz).
- Also: `metrics.json`, `selfcross.json`, `organizer_check.json`, `params.json`, `trace.log.gz`.

## 3. Method
- **Tracer.** Gated build c5 (patch `tools/sib/tracer/gate_c5_41701aa.patch`; hashes in `build/sha256_c5.txt`) = the T0 build c4 plus `gate_fix_resume_points`: resumed official vertices are held constant in every local solve and are exempt from the final audit.
  - Preset L15 (P + space_line_weight 0.1, reject_dist_th 1.5), unchanged from the T0 proposal, step 20 L2 vox, 4 threads.
  - Resumed from the official mesh; 12 generations; 21:37:14-21:47:47Z (633 s wall); rc 0; the final audit removed 22 vertices.
- **Input.** The official m7 L2 surface prediction (9.6 um), copied chunk-for-chunk into a local zarr (882 keys with sha256; 85 absent in the source).
  - Normal grids were generated with the official vc_gen_normalgrids.
  - Official mesh vs m7 L2: 92 % of vertices within 1.5 L2 vox. New vertices: 100 % within 1.5 L2 vox.
- **Trim** (`deliver.py`, rule fixed before the output was examined): keep new vertices 1-11 rows above an official column inside c9-c15. The side and downward growth outside the window is dropped.
- **Metrics:** `metrics.py`, with unit tests in `tests/sib_tracer_p4n_metrics_test.py` (4/4 pass, including a planted 5-vox seam step that is detected). All distances are in native 2.4 um voxels.

## 4. Results per DECL-P4-13 metric (real extension, trimmed)

| metric | extension | official-mesh control (same measure) | declared bar | verdict |
|---|---|---|---|---|
| seam continuity: median normal residual of the first new row vs the quadratic continuation of the official column | 2.40 vox (p90 6.72; 3-D residual 2.89; kink 2.7°) | 2.40 vox (p90 6.70), official vs its own continuation one row inside itself | ≤ 2 vox | **FAIL** (literal). Equals the official self-baseline; see ASK P4-N 1 |
| self-intersection (vc_tifxyz_selfcross, official patch + extension) | 0 transverse pairs | — | none | **PASS** |
| neighbour-winding distance ≥ 60 % of local spacing (fail-closed point-to-surface; spacing = per-tile median of official top-2-mm clearance, 54-88 vox) | 98.07 % of new vertices pass; min ratio 0.42, p1 0.56; min clearance 29 vox | official top 2 mm: 97.48 % pass, min 0.30, p1 0.54 | every vertex | **FAIL** (literal: 139 vertices below). Better than the official mesh on this measure |
| flattening (FLAT-2: SLIM, flatlib sha256 bc5056bf...) | 100.0 % of quads within ±5 %; area \|log\| mean 0.0039, 100 % of triangles within 5 %; angle error mean 0.14°, p99 0.62°, max 1.71°; 0 flips | — | report area and angle error | **PASS** (no failing quad) |
| official vertices unchanged (not a declared bar) | 33006/33006, max displacement 0 | — | — | PASS |

## 5. Held-out validation (the same pipeline inside the official mesh)
The top 5 mm of the official mesh in c9-c15 ± 5 mm was removed and regrown with the same build and preset, then trimmed with the same rule (11 rows). Files: `holdout_L15_trim2mm/`; untrimmed run in `holdout_L15/`.
- Recovery vs the held-out official vertices:
  - median 3.07 vox, p90 8.3; 61 % within 4 vox;
  - in the first 2 mm, 0.09-0.17 % of vertices are more than 20 vox off, and 0 % more than 40 vox (the neighbouring winding is about 75 vox away).
- The same four metrics on this surface:
  - seam 2.62;
  - 0 crossings;
  - neighbour winding 98.97 % (min 0.49);
  - flattening 100 %.
- The untrimmed 5.4 mm regrowth jumps sheets much more (5.6 % > 20 vox, 17 crossings), mostly higher up and outside the window. This is why the trim and the ~2 mm limit matter.
- The 9.6 um trace sits a median 3 native vox (about 7 um) from the 2.4 um official surface. A ±15 um thin-slab render would need re-snapping or a wider slab.

## 6. Independent check against the organizers' 20231016151002 2.4 um mesh (geometry only; `organizer_check.json`)
- It coincides with the official mesh within 4 vox in only 50 of 782 columns, so the check is weak and secondary.
- In those columns:
  - new vertices sit a median 8.2 vox from it, against 2.9 for the official top band;
  - the distance grows with height: rows 1-4 median 7.3, rows 5-8 median 8.2, rows 9-11 median 11.0, with 20.6 % > 20 vox and 3.7 % > 40 vox in rows 9-11.
- In the held-out test the same check read 8.0 vox while the true error was 3.1. So about 8 vox against this mesh is the expected level for a correct regrowth.
- The rise in rows 9-11 (1.7-2.1 mm) agrees with p4-layout: no sheet is centred on the organizer mesh above about +2 mm.

## 7. Support caveat for any later render declaration
- The extension covers all of c9-c15 to 2.1 mm. The CT edge test supports only c9 and c12 to 2.0 mm, c13 to 1.5 mm and c14 to 0.5 mm.
- c10, c11 and c15 are untested there. Their held-out recovery was as good as elsewhere (c10 median 2.05, c11 2.33, c15 5.05 vox), but held-out recovery does not show that papyrus exists above the edge.
- **Recommendation:** a render declaration should restrict each column to its supported height, or label the unsupported parts.

## 8. History
- Run 1 (holdout, untrimmed 5.4 mm): FAIL (see §5).
- Holdout variant reject_dist_th 1.0 was started and then stopped after 3 min, once the trimmed-2mm validation of run 1 answered the question; it gave no result.
- Headroom finding (9.1-9.6 mm to the volume top) as before.

Integrity: no issues.
