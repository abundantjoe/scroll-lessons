# p4-layout STATUS

Provenance: Project HERCULES | owner the owner | [id removed]
Task: RULES.md DECL-P4-13 part P4-M items 1-3 (numbers only). Priority: edge check (item 2) -> organizer mapping (item 3) -> column profile (item 1).

- 2026-09-26 (start): read DECL-P4-12, DECL-P4-13, STATE.md, DOSSIER sections 0, 3.5, 4, 5 (EXPECTED-TEXT not read).
- Official strip-a mesh fetched (x/y/z.tif, meta.json); sha256 equal to p4-tiles-a's (c304cdfd.., 9a4eefda.., a06716af.., 8a61b3e6..).
- Volume 20260411134726 zarr metadata: L0 (75784, 32693, 32693) zyx, 128^3 uncompressed u8 chunks; L1-L5 halve each axis.
- State: RUNNING. Next: item 2 mesh-valid fraction at z > 160 mm per tile, then the CT sheet-continuation test above the top edge.
- Blockers: none yet.

## 2026-09-26 ~21:35Z: item 2 (edge check) DONE; edge.json pushed
- **Does sheet continue above the official top edge in c9-c15? YES, but only about 2 mm, not 1-2 cm.** Tracer sibling (P4-N): an extension of about 2 mm (to z ~174.5 mm) in c9-c14 is supported by the CT.
- The official edge is a flat z cut at 172.2-172.8 mm in every column, equal to the spiral-fit z limit of 172.8 mm. It is not a physical sheet end.
- The scroll material (organizers' mask) ends between +3 and +5 mm above the edge, at z 175-178 mm. It is 0 % present from 178.1 mm.
- The organizers' labelled segment 20231016151002 (2.4 um re-mesh) already extends 5.1-5.3 mm (median) above strip a's edge in c9-c14.
- The CT index anchored on that mesh supports sheet to about +2.0 mm, pooled over c9-c15. Per column:
  - c9: 2.0 mm;
  - c12: 2.0 mm;
  - c13: 1.5 mm;
  - c14: 0.5 mm;
  - c10, c11: undetermined (no test power there);
  - c15: too few anchor vertices.
- From +2 to +2.5 mm upward, no sheet is centred on the organizer mesh.
- A first tracker test failed its own validation and is reported as such (edge/edge_cont.json); it is not used.
- Item 3 (orgmap) is **BLOCKED** (ASK-2): the session safety check refused use of the EduceLab meshes, and the files were deleted. What is ready:
  - the transform is validated (19 um median residual);
  - the labelled-segment mapping reproduces p4-excl.
- Next: orgmap.json with what is unblocked (the transform validation and open-bucket organizer segments; 2024 ids pending ASK-2), then the item 1 column profile (the M1 sums are computed).

## 2026-09-26 ~21:55Z: items 1-2 DONE, item 3 PARTIAL (blocked, ASK-2); REPORT.md written
- **Item 1** (profile.json):
  - M1 pitch passes on both known-text spans: 76 mm (SNR 64) and 78 mm (SNR 102).
  - E2 and L2 fail, with no layout signal.
  - Intercolumns on strip a: 51, 126 and 214 mm.
  - c11-c13 block: 217-276 mm (60 mm wide). Vertically it runs from the mesh top cut to 38 mm down.
- **Item 2** (edge.json): sheet continues about +2 mm above the official top edge in c9-c14. That is not 1-2 cm; the scroll material ends +3 to +5 mm above the edge. **Tracer sibling (P4-N): extend by about 2 mm, not 1-2 cm.**
- **Item 3** (orgmap.json): transform validated (19 um median). The 1A title-search segments are pending ASK-2; 1B is unmappable (no published transform).
- **State:** DONE except item 3's 1A mapping.
- **Blocker:** ASK-2 (the owner's direct authorisation in this session, a permission rule, or a run elsewhere).

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - M1 prediction bab56557..;
  - mesh x 450e2e4e.., y 3941f3bc.., z cb9e511c..;
  - locator_geometry.json from p4-inner 08292cbf;
[line withheld: prize-candidate detail under review]
- **s validation.** s(row, col) was recomputed from the mesh with the locator definition. Against all 132 locator tiles: max |diff| 0.01 cm, p50 0.0035 cm.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

## 2026-09-27 ~11:01Z: resumed after the usage-limit pause and a container restart
[line withheld: prize-candidate detail under review]
- The restart restored scratch to a snapshot without the output. The profile is being recomputed from the same hash-verified inputs (deterministic), together with the Q6 3.1-3.2 pass. The waited-for commit is still 32ba93c8 (METRIC-HASH-42, verified: the Q6 section sha256 is de2f0335..).

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - **Gap:** 3.6 cm.
[line withheld: prize-candidate detail under review]
  - **Pitch:** 16.1 cm start to start. No 7.9 cm peak.
- **Vertical.** Block 1: extent 120 mm, line pitch 6.26 mm, ~19 lines. Block 2: 114 mm, 6.51 mm, ~17.5 lines.
- **Q6 section-2 table, applied mechanically:**

  | Row | Score |
  |---|---|
  | W | -1 |
  | G_in | 0 (flagged: 3.6 cm fits neither) |
  | P | -1 |
  | G_out | 0 (no outward baseline) |
  | row consistency | -1 |

[line withheld: prize-candidate detail under review]
- **Q6 section 3.** R = 1.09 favours (a). Vertical-extent ratio 1.26 favours (a).
- Descriptive only; it cannot make or break a candidate.
- Next: when run 2 finishes, compare it with run 1 (determinism check).

## 2026-09-27 ~11:40Z: determinism check PASSED
[line withheld: prize-candidate detail under review]
- State: DECL-P4-25-A2 item 2 DONE. The only item still open is DECL-P4-13 item 3 (1A mapping), pending ASK-2.
