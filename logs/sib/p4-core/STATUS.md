# p4-core status

2026-10-01T00:16Z p4-core: FACING_ALL done 189/189 - w010-027 facing geometry both directions (facing_all/index.json): OUTER coverage median 0.889 (135 tiles >= 0.8, 15 < 0.2), INNER median 0.860 (123 >= 0.8, 9 < 0.2); w027 has no outer and w010 no inner target in this mesh.

[line withheld: prize-candidate detail under review]

## 2026-09-27: DECL-P4-26 / -A1 facing surfaces
- **Naive rule (declared)** (facing/rules_naive_reg.json): 0 of 90 tiles pass the gate.
  - Found >= 95.9 % everywhere, but 137-27448 self-intersections per tile.
  - check (v) median 31-149 um (5 of 90 tiles pass (v)).
  - Stage 2 reproduces the committed r0_c11 mesh exactly (sha256 match, all vertices).
- **Regularised rule (A1 item 1):** REJECTED (reg_acceptance.json).
  - 0 of 36 control tiles pass the gate and (v): only 53-65 % of vertices found.
  - So it was not applied to c11-c19.
- **Fallback (4)** (official adjacent inner-winding surface; facing/fallback4.json):
  - Controls: 18 of 36 tiles pass the gate.
  - Title windows: 32 of 54 pass (r3-r4 almost all; c11-c12 and c17-c18 in most rows). The failures are coverage below 80 % (inner neighbour more than 250 um away), mostly c13-c17 in r0-r2.
  - Median gap is 137-157 um.
- **Rebuild:** the facing offsets per tile are in fallback4_sface_um.tgz. Rebuild with facing.rebuild(official tile grid, inward normals, s_face).


## 2026-09-27 ~07:45Z: DECL-P4-24 holes.json (all 180 tiles)
- **Flagged, specific:**
  - (c) flattening area ratio in r6_c15, r6_c18 and r7_c16. This is the same patch as the L10 self-intersections.
  - (d) mesh off the papyrus in r2_c19 (37.5 %) and r5_c18 (22.5 %).
- **Flagged, not specific:** (e) straight, 22 r0/r8 tiles. The reference behaves the same way; see the extrapolation check.
- **Clean:** 0 interior holes in the whole grid; zero or missing input is at or below the reference.
- **(e2) NOT VALID:** v1 passes 2.3 % of columns and v2 12 %; >= 80 % is required.
  - v2's P_MIN came out as 0, its most permissive setting, and it still failed.
  - So (e2) is not applied, and (e) stays "not specific beyond about 1 mm".
- **Next:** DECL-P4-26 facing meshes (running: controls, then title windows).


## 2026-09-27 ~02:45Z: B and A done (orchestrator tasks of 21:53Z; economy mode)
- **B, L10 mesh audit** (mesh_audit.json, 189 tiles):
  - No whole-sheet switch in c9-c19: 0 winding jumps, normal flips <= 0.0003.
  - CT sheet offset is the same as the c0-c8 reference (median edge 0.000 vs 0.001 mm, centre 0.007 mm in both).
  - Local anomalies: self-intersections in 13/99 tiles against 5/81 reference tiles, concentrated in r5-r8 x c15-c19 (w012-017).
  - Close approaches in r6-r7 x c14-c15 (w017-018): 6.4-6.6 % of vertices below 0.3 of the spacing (reference max 2.9 %).
- **A, P4-TAG** (tag.json): NOT TESTABLE for detached tags. The SAM2 mask zeroes 99.5-100 % of the 0.5-5 mm search shell.
  - In the unmasked data no separate sheet was found; every sheet-like component touches the body.
  - Planted tabs: 17/24 detected.
- Next: the orchestrator may declare a per-vertex CT check of the B anomaly patches. An unmasked volume would be needed for A.


Provenance: Project HERCULES | owner the owner | [id removed]

Updated 2026-09-26 ~22:00Z. **State: DECL-P4-7 items 1-2 (2.4 um) and item 3 preparation DONE. No trace was run; the gate is not met.**

## Numbers
- **Count** (count.json):
  - Grid: 25 z-levels (40-160 mm), 128 rays each, 3161 valid ray samples. Volume: 2.4 um, level 0, 9-slice slab. Smoothing: Gaussian FWHM 20 um, prominence 0.25 x the calibration-span range.
  - Peaks inward of w010: median 5, IQR 4-6, p5-p95 2-9.
  - Per-level medians: 3.5-6.
  - Inside the 1.129 um footprint: median of the per-level medians 4.
  - Rays with >= 1 peak: 100 %. Rays with > 10 peaks: 1.8 %. **The DECL-P4-7 "> 10 over >= 80 % of rays" criterion is NOT met.**
- **Spacing:**
  - inner peaks along the ray: median 0.130 mm, IQR 0.084-0.211;
  - labelled w010-w020 along the ray: median 0.162 mm, IQR 0.117-0.227;
  - outermost inner peak to w010: median 0.11-0.25 mm per level.
  - The inner structure continues at about the labelled pitch. It is not a sub-resolution compressed core.
- **Mesh geometry** (w010_loop_geometry.json): the w010 loop is a flattened ellipse, about 3.6-5.4 x 1.1-3.2 mm, with area 2.8-10 mm^2. The official umbilicus lies inside it at every z. Normal spacing w010-020 is 0.09-0.19 mm, which explains p4-inner's apparent "0.07-0.15 vs 0.22 mm" discrepancy: 0.22 mm was a radial fit.
- **Validation (item 2):**
  - Calibration (peaks between the w010 and w020 mesh crossings, expected 10): median 12, and 32 % of rays within +-1. The counter over-counts labelled sheets by about 20 %; calibration-scaled inner median is 2.7-5.7 per level.
  - Continuity: the count changes on 61 % of adjacent-ray pairs (by >= 2 on 20 %), and on 82 % of adjacent-z pairs 5 mm apart (by >= 2 on 50 %).
  - Synthetic tests (synthetic_tests.json, 192 cases): **NOT PASSED overall.** 63 % of cases have |per-z error| <= 1, with a bias of -1.33. The bar holds in 30 of 30 cases at an inner pitch of 0.12 mm with an exact umbilicus; the pass rate is 37 % at 0.04 mm pitch and 48 % with a 0.15 mm umbilicus offset. Amorphous-core controls give 0-1 false windings.
- **Reading:** the 2.4 um data show sheet-like periodic structure inward of w010 at about the labelled pitch. On raw peaks there are about 4-6 crossings per ray, not 10 and not > 10. The counter is not validated to +-1 winding, so the exact number is unresolved. There is no evidence for windings beyond the labelled numbering.
- **Item 3:** the metrics module is done (17 tests pass). trace_plan.md holds the window rule, seeds rule and commands. Metric (e) waits on a declaration (ASK 1).

## Next step
Proposed:
- a z-coherent peak tracker and an umbilicus refinement, then a re-run and a re-test on synthetics that also reproduce the real over-count;
- the gate waits on p4-inner's 1.129 um count.

## Blockers
None hard. ASK.md items 1-3 are open.
