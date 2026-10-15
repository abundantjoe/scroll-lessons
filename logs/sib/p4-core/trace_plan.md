# p4-core trace plan: 2 x 2 cm core window inward of w010 (DECL-P4-7 item 3)

Provenance: Project HERCULES | owner the owner | [id removed]

**Gate status: NOT MET. No trace has been run.** The task gate requires items 1-2 from both p4-core (2.4 um) and p4-inner (1.129 um) to show papyrus inward of w010.
- p4-core's count shows periodic structure inward of w010 on 100 % of rays (median 5 peaks). It does not pass item 2's validation. The synthetic error bar holds in only 63 % of cases, the real-data calibration over-counts (median 12 vs 10), and ray-to-ray continuity is poor. See count.json and synthetic_tests.json.
- p4-inner has not yet reported its 1.129 um count.

## Window
- **Rule** (code: `tools/sib/p4-core/plan_window.py`, fixed before any trace):
  - a 20 mm z band inside the 1.129 um footprint (67.4-135.3 mm);
  - the band is chosen by the best real-data calibration (fraction of rays with |calibration count - 10| <= 1), with ties broken by the lowest count IQR;
  - 2 cm of sheet length along the candidate w009;
  - seeds are the outermost inner peak (the w009 candidate) on the median-count ray whose calibration equals 10, at the band's bottom, middle and top.
- The w010 loop is about 4-5 x 1-3 mm (`w010_loop_geometry.json`), so 2 cm of length is about 2 turns of w009.

## Tracer
- **Build:** the tracer sibling's VC3D build c4, `tools/sib/tracer/vc_build_sib.sh` + `gate_c_41701aa.patch` (binary sha256 in `logs/sib/tracer/build/`).
  - Its distance gate passed T1: two sheets 8 vox apart were never bridged.
  - That matters here, because the measured inner spacing is 0.084-0.21 mm (IQR), i.e. 35-88 vox at 2.4 um.
- **Input:** `20260411134726-surface-20260413141734-surface-recto-2um-ps256-L0-th0.45.zarr` (2.4 um recto prediction) with its `.normal-grids`, synced locally per seed band (tracer ASK item 7). The chunk cache is cleared between seeds (tracer ASK item 8).
- **Preset:** L20 (`space_line_weight` 0.1, `reject_dist_th` 1.5), with `voxelsize` 2.4 and step 20. Generations are sized for 2 cm: about 20 mm / (20 vox x 2.4 um) ≈ 420 rings from one seed is too many, so the plan uses 3 seeds x 75 generations and merges them only if metric (b) gives the same offset.

## Validation (all code in `tools/sib/p4-core/trace_metrics.py`, 17 synthetic tests pass in `tests/sib_p4core_test_metrics.py`)

| metric | implementation | pass rule |
|---|---|---|
| (a) self-intersection | exact Moller tri-tri with KD-tree broadphase; 1.3e6 triangles in 15 s | 0 intersecting pairs |
| (b) winding continuity with w010 | ray casting to the w010 mesh triangles; integer offset and jumps | 0 jumps, all vertices inward of w010, offset mode = the planted/expected offset (-1 for w009) |
| (c) neighbour-distance ratio | exact point-to-triangle distance to the w010 mesh / local w010-w011 spacing | p5 of the ratio >= 0.6; fraction >= 0.6 and the minimum also reported |
| (d) flattening area/angle error | FLAT-2 flatlib (byte copy `flatlib_flat2.py`, blob sha checked by test) with SLIM | report only until thresholds are declared (ASK 3) |
| (e) fibre-orientation coherence | hv4 power-spectrum moment per 64 px window, vs the w010 strip median | NOT RUN: it needs a surface sampling, which needs its own declaration (DECL-P4-7 item 4; ASK 1) |

## Before any trace, the orchestrator must decide
1. Whether a count that fails the item-2 synthetic bar (63 %) and the real calibration (32 % of rays within +-1) can open the gate. Proposed: no. Fix the counter first:
   - a z-coherent peak tracker that follows peaks across adjacent slices;
   - a umbilicus refinement: the centre that maximises count agreement across rays.

   Then re-run.
2. The ASK items 1 and 3.
