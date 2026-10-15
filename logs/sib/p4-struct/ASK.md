# p4-struct ASK (to the orchestrator)

Provenance: Project HERCULES | owner the owner | [id removed]
Written 2026-09-26, before any real-tile S_row existed. The declared run goes ahead exactly as declared; nothing below is applied without a declaration.

## ASK-1: the declared rot-90 null cannot separate anything (a declaration defect)
DECL-P4-8 item 2 defines S_row as a **max over all orientations** (0-180 deg), normalised by the **median over all orientations** at the same |k|.
- A 90 deg rotation of a tile rotates its power spectrum by 90 deg. On the 2 deg grid that only permutes the orientations: theta -> theta + 90.
- So S_row(rot90 tile) = S_row(tile) exactly, and theta* moves by exactly 90 deg.
- Unit test `test_rot90_invariance_of_declared_statistic` confirms it to float32 precision (relative difference < 1e-3; theta* differs by exactly 90.0).

Consequences for the rules as declared:
1. Null (item 3). The rot-90 null is the same set of numbers as the tiles themselves (title and control pooled). T_mat is then the p99 of the material's own S_row.
2. Gate (item 3). At most about 1 % of the pooled tiles exceed their own p99. For M1 (331 tiles), at most 4 tiles are above T_mat, so at most 4/171 (about 2 %) of control tiles can clear it. The 30 % bar cannot be met by any material, whatever the data. Every material will be "uninformative" by construction, not because of the papyrus.
3. Validation AUC (item 6). The AUC of S_row for control tiles against their rot-90 copies is exactly 0.5 by construction.

A proposed fix, for the orchestrator to declare or reject. I have computed no real-tile number with it.
- S_anch(theta_c) = max over theta in [theta_c - 10, theta_c + 10] of R(theta). R(theta) is the item-2 per-orientation ratio: the band peak over the median at the same |k|.
- theta_c = the axial median theta* of the non-blank control tiles. It is fixed from the control strip, not from the tile being scored.
- Null: S_anch(theta_c) on the rot-90 copy of every tile. Rotation moves real row structure to theta_c + 90, so the null keeps the texture but loses the row alignment.
- T_mat = the p99 of that null. The gate and the positive rule are otherwise as declared.
- The declared S_row and theta* would still be reported.

Its code is `struct_core.s_anch` and `run_struct.py --variant anchored --decl <id>`. Without an id, the runner exits.
- On synthetic tiles only (logs/sib/p4-struct/synthetic_smoke.json), the declared rule fails its gate on obvious planted rows: 0 of 6 pass, AUC 0.507.
- On the same tiles the variant passes: 6 of 6 pass, AUC 0.993.

Caveat for the declaration: a rot-90 null tests orientation-aligned periodic structure, not text specifically. Sheet contacts or seams along the winding also sit at theta 90, so the control/title contrast remains the evidence.

## ASK-2: E1 and E2 have no known-text control on the same material
DECL-P4-8 item 1 lists known-text controls only for M1 (M1-b) and M2 (M2b). E1-A1 and E2 are raw-CT displays, and no raw-CT w028-037 tiles exist.
- So for E1 and E2 the gate (item 3) cannot be evaluated, and M_ink has no control p95 there.
- As declared, both are reported "uninformative (gate not evaluable)". Their S_row, theta* and rot-90 T_mat are still reported.
- To make them informative, a builder would need raw-CT control tiles of 20260623142658-w028-037 (1.129 um, DECL-P4-5-A1 display) and 20260701183125-w028-037 (2.4 um, DECL-P4-5 display). These are the same displays and grids as M2b and M1-b.

## ASK-3: missing inputs (not blocking the run)
- excl_d_a (M2a, E1 and P4-F flags) is not yet on p4-excl. Until it lands, M2a and E1 tiles are never STRUCT-positive (fail-closed).
- P4-F: p4-highz has not pushed f1/. When it lands, `run_struct.py` re-runs with P4-F added.
