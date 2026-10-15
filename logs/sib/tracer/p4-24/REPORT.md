Provenance: Project HERCULES | owner the owner | [id removed]

# DECL-P4-24 item 2: re-trace of strip-a tile r2_c19 (w010-027), sibling tracer

STATUS: DONE. Verdict: **NOT ADOPTED**.
- The self-intersection gate fails (1 pair; 0 required).
- The seam is worse than the official mesh.
- The tracer filled only 2.3 % of the hole.
- No render and no read.
- Geometry plus 1-D CT normal profiles read as numbers only; no image was viewed.

## Method (the DECL-P4-22 method, unchanged; code `tools/sib/tracer/p4n/`, P4_CFG=p424)
- **Patch.** P = tile r2_c19 in p4-core's tile frame: official rows 834-1250, cols 7925-8342. Worked on every 4th vertex (0.192 mm) in a local frame of the official m7 L2 prediction (2688 chunks, sha256 in `m7l2_chunks_sha256.jsonl`), with a 1-tile ring of official context.
  - 11025 official vertices in P; z 119.8-139.3 mm.
- **Off-sheet test.** p4-core's DECL-P4-24 (d) test, run on EVERY vertex of P rather than 40 samples:
  - ±60 um (±25 vox) L0 normal profile of the 2.4 um volume, Gaussian sigma 1;
  - off-sheet = no peak with prominence ≥ P_MIN = 16.6027 (p4-core holes.json 627b42fc).
  - p4-core's own code was used: mesh_audit.profile and holes.best_prom, pinned with sha256 in `tools/sib/tracer/p4n/ext/p4core/SOURCE.txt`. Normals are central differences on the full-resolution official grid, as in p4-core.
- **Holes.** Off-sheet vertices dilated by 10 steps (1.9 mm), inside P.
- **Trace.** Build c5, preset L15 + `gate_fix_resume_points` (clean official vertices fixed), 15 generations; 12:18:47-12:27:24Z; rc 0.
- **Gate.** DECL-P4-22 item 1, via `metrics22.py` and `eval22.py`, computed identically on the hybrid (official outside the holes + re-trace inside) and on the official mesh over P.

## Holes (`holes.json`)
- **Off-sheet fraction of P: 22.3 %** (2461 of 11025 vertices).
  - p4-core's 40-sample estimate was 37.5 %, whose binomial standard error at 22 % is about ±6.5 %. The difference is about 2.3 standard errors.
  - Same method, but p4-core sampled 40 full-resolution vertices while every 4th vertex is tested here. Both numbers are reported.
- **The holes cover 99.97 % of P** (11022 vertices). The off-sheet vertices are scattered over the whole tile, so the 1.9 mm dilation merges them. The unchanged method is therefore a whole-tile regrowth from the ring.

## Results (`metrics.json`)

| metric | re-trace (hybrid) | official | gate | verdict |
|---|---|---|---|---|
| self-intersection pairs touching P | 1 | 6 | = 0 | **FAIL** |
| seam, normal residual at hole borders (median / p90 vox) | 12.0 / 21.6 (n 29) | 9.1 / 27.5 (n 420, same positions) | ≤ official | **FAIL** |
| neighbour winding, fraction ≥ 0.6 × spacing (over P) | 0.890 (n 254) | 0.861 (n 11024) | ≥ official | pass* |
| flattening, SLIM on P: quads within ±5 % / mean angle error | 100 % / 0.09° (85 quads) | 82.4 % / 1.15° (10816 quads) | ≥ and ≤ | pass* |
| hole fill | 251 / 11022 = **2.3 %** | — | reported | — |
| off-sheet fraction (same profile test) | 5.6 % of the re-traced vertices (n 54 with a valid normal) | 22.3 % | reported | not comparable (n 54) |
| official vertices outside the holes unchanged | yes | — | — | — |

*The re-trace "passes" only because it covers 2.3 % of the tile; they say nothing about a re-traced surface.

## Why the tracer cannot fill r2_c19
- In r2_c19 only **39 %** of the official vertices lie within 1.5 L2 vox of the m7 L2 prediction (threshold 170). 47.6 % are more than 3 vox away, and 10.5 % have no prediction within 12 vox. In window A (P4-N) the same figure was 92 %.
- Gate counters (`gate_counters.json`): 2714 candidates evaluated, 1212 rejected by the distance gate and 152 by cost; growth stalled after 15 generations with 251 vertices inside P.
- The surface prediction this tracer follows is largely absent or displaced in this tile. That is consistent with p4-core's finding that the official mesh is partly off the papyrus here.
- A gated tracer on m7 L2 cannot re-trace r2_c19.
- **Options** (orchestrator's decision; none were run):
  - (a) the 2.4 um recto prediction `20260411134726-surface-20260413141734-surface-recto-2um-ps256-L0-th0.45` with its official normal grids (64× the data of L2);
  - (b) a CT-profile snap: move each off-sheet official vertex along its normal to the nearest sheet peak within ±60 um, with p4-core's profile test as the acceptance rule;
  - (c) more generations (about 55 are needed to cross a 104-step tile). This is not recommended: prediction support is missing, and the P4-N holdout showed sheet jumps rising beyond ~2 mm of growth.

## Files
`metrics.json`, `holes.json`, `gate_counters.json`, `trace_params.json`, `trace.log.gz`, `hybrid_selfcross.json`, `official_prep.json`; `patch_native.tifxyz` (with `retraced_mask.npy`) and `patch_native_flat_uv/`, kept for the record only.

## Incidents
- The first chain run stopped on an import error: the pinned p4-core module needed `trace_metrics` and `flatlib_flat2`. Both are now pinned.
- Three container restarts killed the chain. The off-sheet profiling was made resumable (checkpoint every 500 vertices), and the chain was relaunched each time; no step was redone from scratch except the trace start.

Integrity: no issues.
