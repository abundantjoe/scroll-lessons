Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple-mo STATUS

- 2026-09-26: started. PROTOCOL.md pushed (7e8ab53) before any feature number. The ground truth is the official 2.4 um prediction (no human labels exist on the w028-037 canvas).
- Unit tests: all pass (unit_tests.json).
- T_face = 79, from the mode midpoint (modes 43 and 115) on the dev tiles (tface.json).
- Dev r2_c3 had a face fraction of 0.48 < 0.5, so amendment A1 (sheet anchor) was written and pushed (4657434) before any control or gate number. Under A1 the face fraction in the r2_c3 region is 0.87 (both faces 0.86).
- Positive control (posctl.json): FAIL on both faces by the declared rule.
  - Recovered height at D = 10 um: F1+ 7.3 um, F1- 6.4 um, F2 7.0 / 9.0 um, all inside [5, 13].
  - The glyph AUC is only 0.60 (+) and 0.58 (-), below the 0.90 bar. At D = 20 um it is 0.68 / 0.65.
  - Meaning: the pipeline measures relief correctly, but the natural face-height variability of the control makes a 10 um deposit only weakly separable per 9.6 um cell.
  - Per the protocol, F1/F2 cannot pass the gate, and a FAIL there is "pipeline insensitive" at 10 um.
- Gate done: 0 of 9 tests pass (gate.json, 161da9d). REPORT.md pushed. Task complete.
- Blockers: none.
