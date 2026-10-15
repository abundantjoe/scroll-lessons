Provenance: Project HERCULES | owner the owner | [id removed]

# T0 proposal (gated build c4) — for the orchestrator to declare; NOT run

**Status:** nothing of the T0 test set has been read, synced or run. `tools/sib/tracer/t0_run.py` refuses to run unless `--declaration <ID>` names an existing `## <ID>` heading in RULES.md.

## What is run (once)
- **Build.** Villa 41701aa + `tools/sib/tracer/gate_c_41701aa.patch`, built with `tools/sib/tracer/vc_build_sib.sh` (`BDIR=hrc-gated-c4`) in the official deps image `ghcr.io/scrollprize/vc3d-deps/linux@sha256:09b8d6c7565fd27af4f030b421881525079520ee9e5d27490eeb476dadb57128`.
  - The patch sha256 and the built binary sha256 are in `logs/sib/tracer/build/sha256_c4.txt`.
  - The binary hash is per build (it embeds build paths). For a rebuild, the check is the patch hash plus the unit tests.
- **Presets (frozen).** `logs/sib/tracer/presets/L15.json`, `L20.json`, `L25.json`; sha256 in `logs/sib/tracer/presets/SHA256SUMS`.
  - Task P + `space_line_weight` 0.1 (ASK item 1), with `reject_dist_th` 1.5 / 2.0 / 2.5 and compactness on.
  - Gate: cost threshold 0.1, ref_max 6, final audit on, negative control off.
  - `generations` from each seed's meta.json (`vc_gsfs_params.generations`, per DECL-TSURF; ASK item 2).
  - `voxelsize` 9.362 um (samplePixelSize in the m7 store's metadata.json).
- **Volume.** `s3://vesuvius-challenge-open-data/PHerc1203/representations/predictions/surfaces/20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr` (streamed).
- **Normal grids.** The same prediction's `.normal-grids` store. Only at T0 time, for each seed, sync slices xy/xz/yz at seed ± (generations × 20 + 100) vox, recording a sha256 per file.
- **Command.** `python tools/sib/tracer/t0_run.py --declaration <DECL-ID> --family L` runs 5 seeds × 3 presets in sequence and clears the remote chunk cache between seeds.
  - Each run: `vc_grow_seg_from_seed --volume <m7> --target-dir D --params P --seed X Y Z`.
  - Then `vc_tifxyz_selfcross`, v2 truncation, area, edges, team distance and the half-pitch control, via `surfmetrics.py` and `dev_control.py`.

## Metrics (fixed, as in the dev runs)
- **Crossings/cm².** Distinct transverse quad pairs (either triangulation) divided by raw area.
- **v2 truncation.** Keep generations < min over crossings of max(g(quad1), g(quad2)), where quad g = max of its corner generations. A re-run of selfcross on the truncated surface must give 0.
- **Area.** Of the v2 surface, in cm²; a seed that saves nothing counts 0.
- **Edges.** Fraction of edges within ±10 % of 20 vox, on the v2 surface.
- **Team agreement.**
  - Fraction of v2 vertices within 3 vox of the team surface. The team surface is densified to ≤ 1 vox (nearest-densified-vertex form, overestimate ≤ 0.71 vox; fail-closed side for the "within" test).
  - Control: the same vertices shifted ± half-pitch along their normals; control = max of the two.
  - Half-pitch = median, over 300 sampled vertices, of the distance to the next m7 sheet along the normal, divided by 2.
- **Reported alongside, not a bar.** m7-consistency of both surfaces, coplanar contact counts, and gate counters.

## Expectation from the dev set (c4, 6 dev seeds, 45 generations; not a prediction bar)

| preset | median crossings/cm² | median v2 area (cm²) | edges | median team ≤3 vox | median margin vs control |
|---|---|---|---|---|---|
| L15 | 0.0 | 0.46 | 0.998 | 0.78 | 0.68 |
| L20 | 0.0 | 0.86 | 0.998 | 0.61 | 0.51 |
| L25 | 3.6 | 0.61 | 0.998 | 0.54 | 0.48 |

- 1 of 6 dev seeds dies at the seed under every preset.
- **The area bar (median ≥ 3.0 cm²) is expected to FAIL.** At 45 generations the best raw area is 1.70 cm². Single-seed growth adds at most about one ring per generation, so even at 75 generations the geometric cap is about 3.8 cm² before truncation. Measured: the 75-generation self-test on the best dev seed (163331524, L15) gave raw 3.34 cm², 511 crossings, a v2 cutoff at generation 46 and v2 area 1.60 cm².
- **Timing.** 4 cores, 3 concurrent single-thread runs: 149-526 s per seed-preset (median about 250 s) at 45 generations. At 75 generations the measured time is 1000 s for one seed-preset (single run). The whole T0 (15 runs) would take about 1.5-2 h wall at 3 parallel, plus the normal-grid sync of about 9600 files (about 6 GB) per seed band.
- **Disk.** Keep ≥ 16 GB free. The VC3D remote cache stores decoded chunks, up to 13 GB per seed region.

## Needs the orchestrator
1. Rulings on ASK.md items 1 (space_line_weight), 2 (generations from meta) and 3 (gate additions).
2. A declaration ID (for example DECL-T0-A1) plus a METRIC-HASH over `presets/SHA256SUMS`, `gate_c_41701aa.patch`, `surfmetrics.py`, `dev_control.py`, `m7probe.py`, `t0_run.py` and `dev_run.py`.
