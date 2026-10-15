# ASK (sib/p4-core)

Provenance: Project HERCULES | owner the owner | [id removed]

1. **Metric (e), fibre-orientation coherence, needs a texture of the traced surface.** DECL-P4-7 item 3 lists it as a trace validation metric. Item 4 says any render of a new core surface needs its own declaration first. The code (`tools/sib/p4-core/trace_metrics.py: fibre_coherence`) is written and unit-tested on synthetic arrays only.
   - **Proposed default:** metrics (a)-(d) are computed from geometry alone. Metric (e) stays NOT RUN until the orchestrator declares a numbers-only surface sampling of the trace. That sampling would be a structure-tensor/power-spectrum statistic computed in memory, with no image written or viewed. The w010 reference median would be computed the same way.
   - p4-core does nothing on (e) until that declaration exists.
2. **Interpretation of "20 um smoothing" (DECL-P4-7 item 1).** This was fixed in code before any CT value was fetched (commit b7b6a4a).
   - Primary: a Gaussian with FWHM 20 um.
   - Secondary: a Gaussian with sigma 20 um.
   - Both are reported. If the orchestrator intended a different kernel, the runner re-runs from the same streamed data in about 2 min per level.
3. **Pass rule for metric (d), flattening distortion.** The rule text gives no threshold.
   - **Proposed default:** report only. The orchestrator declares thresholds before any trace is run (e.g. the FLAT-1 bar of 93.1 % of quads within +-5 %).

4. **DECL-P4-24 (e) is not specific beyond about 1 mm** (2026-09-27; `holes_extrap_check.json`, mesh geometry only).
   - Declared method: a straight extrapolation of the edge tangent, fitted on the last 10 vertices, then a +-60 um profile.
   - Tested on known surface: the same fit, predicted into the mesh, misses the true sheet perpendicularly by these medians:

     | distance | r0 | r8 | rays within +-60 um (r0 / r8) |
     |---|---|---|---|
     | 0.5 mm | 3 um | 5 um | - |
     | 1 mm | 50 um | 69 um | - |
     | 2 mm | 137 um | 250 um | 24 % / 11 % |
     | 5 mm | 343 um | 887 um | 8 % / 1 % |

   - The sheet spacing is about 165 um. At >= 1-2 mm, a peak in the +-60 um window mostly shows that some sheet is near, not that the same sheet continues.
   - The declared (e) flag at 2 mm is applied unchanged and reported, but it cannot be read as "the papyrus continues beyond the edge".
   - **Proposed amendment** (to declare before any run): a sheet-following test. Step 0.1 mm at a time and re-centre on the profile peak at each step.
     - Validate it first by following INTO the known mesh from the edge. It passes if the mean offset from the true vertices is <= 30 um at 2 mm on >= 80 % of columns.
     - Only then apply it beyond the edge.
   - p4-core will not run it until it is declared.

5. **DECL-P4-26 facing mesh: the declared per-vertex rule gives a jagged surface** (2026-09-27, first tile r0_c11).
   - Results:
     - 97.3 % of vertices find a peak.
     - L1 agrees with L0 (median 0.8 um; 92 % within 10 um).
     - 137 self-intersections, so the gate FAILS.
     - The grid flattening is poor: 12.6 % of quads within +-5 %, and 19 % of triangles with area ratio > 2 or < 0.5. ARAP fails on it.
   - The gap (facing peak minus own peak) has median 77 um, IQR 50-125 um, while the sheet spacing is about 165 um.
   - So "the first peak beyond own + 30 um" often lands on the own sheet's second fibre layer (the same two-layer structure that broke (e2)), not on the neighbour sheet. Neighbouring vertices then alternate between the two.
   - The declared run continues unchanged for all 90 tiles, and the gate is reported per tile.
   - **Proposed amendment** (not run until declared). Validate it on the control tiles c3-c8 first. It is accepted only if the controls pass the declared gate (0 self-intersections, >= 80 % found).
     1. The facing peak must lie >= 0.6 x the local labelled spacing beyond the own peak. The spacing comes from the mesh's own neighbour-winding distance (mesh_audit), about 100 um.
     2. Among those peaks, take the one nearest to the 9 x 9 median-filtered s_face of step 1, within +-20 um.
     3. Remove isolated vertices whose s_face differs by > 20 um from that median.
