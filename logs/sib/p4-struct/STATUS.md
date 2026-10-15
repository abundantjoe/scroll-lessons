# p4-struct STATUS

Provenance: Project HERCULES | owner the owner | [id removed]

- State: the DECL-P4-8 declared run is DONE for M1, M2 (M2a + M2b), E1-A1 and E2. P4-F is pending (p4-highz f1/ not pushed).
- Numbers:
  - Gates: M1 2/86 = 2.3 % and M2 2/32 = 6.3 %; both fail the 30 % bar. E1 and E2 have no control, so their gate is not evaluable. All four materials are uninformative.
  - T_mat: M1 98.46, M2 81.23, E1 32.47, E2 40.22.
  - AUC control vs rot-90: 0.500 (M1-b), 0.497 (M2b).
  - STRUCT-positive: 0 in every material. Jaccard: undefined (both sets empty).
- Inputs: 675 PNGs sha256-checked, 0 mismatches. Tests: 15 passed.
- Blockers / ASK.md:
  - ASK-1: the declared rot-90 null is degenerate (S_row is invariant under rot-90), so the gate cannot pass. A proposed orientation-anchored variant is coded and tested on synthetic tiles only.
  - ASK-2: E1 and E2 need raw-CT w028-037 control tiles.
  - ASK-3: excl_d_a and P4-F are missing.
- Next step: re-run when P4-F, excl_d_a or an amendment lands. The runner is ready.
