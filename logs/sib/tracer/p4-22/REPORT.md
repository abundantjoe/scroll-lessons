Provenance: Project HERCULES | owner the owner | [id removed]

# DECL-P4-22: local re-trace of the w010-027 low patch (strip-a r5-r8 x c14-c19), sibling tracer

STATUS: DONE. Verdict: **NOT ADOPTED** (the self-intersection gate fails).
- Per DECL-P4-22 item 3, the metrics are recorded and the task stops: there is no read on this mesh.
- Geometry only. No image or CT intensity was viewed.

## Method (fixed in code before any trace existed; commits 8eec2f2 and dba4386)
- **Patch P.** Official grid rows ≥ round(5T) × cols [round(14T), round(20T)), T = 8343/20.
  - Worked on every 4th official vertex (0.192 mm), in a local frame of the official m7 L2 prediction (9.6 um).
  - 5460 chunks, sha256 in `m7l2_chunks_sha256.jsonl`; normal grids from the official generator.
  - Plus a 25-step (4.8 mm) ring of official context.
- **Defects** on that grid:
  - vertices of transversely self-intersecting quads (vc_tifxyz_selfcross): 1148 pairs, 1709 vertices;
  - severe close approaches (clearance to another winding < 0.3 × per-tile median spacing): 4073 vertices;
  - 4399 defect vertices in total.
- **Holes** = defects dilated by 10 steps (1.9 mm), inside P: 47986 vertices, 22.7 % of P (`holes.json`).
  - Local holes rather than a full re-trace: regrowing all of P from its border would mean ~350 generations. The P4-N holdout showed sheet jumps rising past ~2 mm of growth (0.1 % in the first 2 mm, 5.6 % over 5.4 mm).
- **Trace.** Build c5, preset L15 + `gate_fix_resume_points`, resumed from the official mesh with the holes removed. Clean official vertices are fixed.
  - 15 generations; 06:11:22-06:31:15Z (1193 s); rc 0; the final audit removed 448 vertices.
- **Hybrid H** = official outside the holes (bit-identical, checked) + traced vertices inside the holes.
- **Comparison.** Each metric is computed on H and on the official mesh O over P by the same code (`metrics22.py`, `eval22.py`).
  - Same-winding exclusion: 40 grid steps. One winding here is ~60-80 steps, so P4-N's 60 would drop true neighbours.
  - The same setting is used for both surfaces.

## Results (`metrics.json`)

| metric | re-trace H | official O | gate | verdict |
|---|---|---|---|---|
| self-intersection pairs touching P | 1720 | 1148 | H = 0 | **FAIL** |
| seam, normal residual at hole borders (median / p90 vox) | 4.17 / 13.4 (n 1999) | 4.65 / 17.4 (n 9294, O's own vertices at the same positions) | H ≤ O | pass |
| neighbour winding, fraction ≥ 0.6 × spacing (over P) | 0.942 (< 0.3: 1.4 %) | 0.889 (< 0.3: 1.9 %) | H ≥ O | pass* |
| flattening, SLIM on P: quads within ±5 % / mean angle error | 87.6 % / 0.98° | 64.4 % / 1.72° | H ≥ O and ≤ | pass* |
| official vertices outside the holes unchanged | yes | — | — | — |
| hole fill | 14902 / 47986 = 31 % | — | reported | — |

*Neighbour winding and flattening favour H mostly because 69 % of the hole vertices, the worst regions of O, are **missing** from H: the tracer did not fill them. These two "passes" are not evidence of a better surface.

**Where the crossings are** (pair classes by quad): 1158 new-new, 477 new-official, 84 mixed-new, 1 mixed-official. Every crossing involves re-traced quads; the kept official vertices outside the holes do not cross. The tracer fails in exactly the regions where the official mesh is defective. These are compressed zones where the 9.6 um prediction does not separate the windings: the official mesh already has 1148 crossings there at this grid.

Seam note: the first evaluation returned n = 0 for both surfaces, because the normal was undefined at the first official vertex next to a hole. The fix falls back to the second fixed vertex. The seam numbers above were recomputed with it; the verdict is unchanged.

## Consequence
- The patch is not adopted, so there is no P4-O inference on it.
- A re-trace of this crushed zone would need either a surface prediction that separates the windings there (for example the 2.4 um recto prediction, 64× the data), or a different method. It cannot be done by the gated tracer on m7 L2.

## Files
- `metrics.json`, `holes.json`, `spacing_by_tile.json`, `official_prep.json`, `trace_params.json`, `trace.log.gz`, `hybrid_selfcross.json`.
- `patch_native.tifxyz`: the hybrid on P in the native 2.4 um frame, grid step 80 vox; `retraced_mask.npy` marks the traced vertices.
- `patch_native_flat_uv/`: SLIM u, v of the hybrid, -1 where undefined.
- These are kept for the record only: the patch is NOT adopted.

Integrity: no issues.
