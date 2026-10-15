Provenance: Project HERCULES | owner the owner | [id removed]
# p4-purple-mo REPORT: DECL-P4-16 item 4, colour-agnostic morphology, control strip w028-037 only. GATE: FAIL (0 of 9 tests)
- Pre-registration: PROTOCOL.md (7e8ab53), pushed before any feature number. Amendment A1 (sheet anchor, 4657434) came after the dev face-fraction trigger and before any control or gate number. Numbers only; no image was viewed. No number exists on w010-027.
- Ground truth: no human ink labels exist on the w028-037 canvas (listing check), so the labels are the official 2.4 um prediction. Ink >= pooled p90 (211.5), background <= p50 (33.5), 50 um exclusion. This measures agreement with a model.
- Data: 2.4 um surface volume, level 0, 16 gate tiles (seed 20260928, all 81 windows each, ~120 GB streamed), 19.2 um cells: 1,351,721 ink and 6,986,386 background.
- Face threshold: T_face = 79, the midpoint of the grey modes 43/115 on 4 dev tiles. Faces were found on 75-95 % of mesh-valid cells.
| test (declared sign) | AUC | 95 % CI | Bonferroni(9) CI | rot-90 null | gate |
|---|---|---|---|---|---|
| F1+ face height, raised | 0.533 | 0.525-0.539 | 0.521-0.541 | 0.505 | FAIL |
| F1- face height, raised | 0.477 | 0.471-0.482 | 0.469-0.484 | 0.501 | FAIL |
| F2 thickness, thicker | 0.504 | 0.498-0.509 | 0.495-0.511 | 0.505 | FAIL |
| F3+ indentation, concave | 0.467 | 0.460-0.476 | 0.458-0.482 | 0.497 | FAIL |
| F3- indentation, concave | 0.533 | 0.528-0.539 | 0.526-0.541 | 0.502 | FAIL |
| F4+ roughness, rougher | 0.529 | 0.505-0.554 | 0.495-0.563 | 0.483 | FAIL |
| F4- roughness, rougher | 0.512 | 0.493-0.530 | 0.486-0.537 | 0.485 | FAIL |
| F5+ crackle at face, higher | 0.656 | 0.636-0.675 | 0.630-0.683 | 0.508 | FAIL |
| F5- crackle at face, higher | 0.545 | 0.529-0.563 | 0.522-0.569 | 0.516 | FAIL |
- Nulls: all 9 rot-90 AUCs lie in [0.47, 0.53]. Unit tests pass (face error 0.08 um). The original face rule (without A1, descriptive only) changes no AUC by more than 0.03.
- Per tile, F5+ ranges 0.604-0.724 (median 0.641; above 0.5 on 16/16 tiles). F1+ ranges 0.475-0.551.
- Positive control (posctl.json): FAIL by the declared rule.
  - A planted 10 um deposit is recovered as 7.3 um (+) and 6.4 um (-), with the expected ~30 % trend loss. So the relief is measured correctly.
  - But the glyph AUC is only 0.60 / 0.58 at 10 um and 0.68 / 0.65 at 20 um.
  - So natural face-height variability sets a detection floor: a real 10-20 um relief deposit could not reach AUC 0.70 per 19.2 um cell with F1/F2.
- Physics reading (UNCERTAIN):
  - At model-ink cells, face + sits +3.0 um higher and face - 2.2 um lower, while thickness is unchanged (-0.2 um). This looks like a small displacement of the sheet toward +, not an added deposit.
  - Crackle at the + face (0.656) is the strongest colour-agnostic cue. It beats the P4-H mesh-slab crackle (0.584) but stays below the bar.
  - Face + may be the ink face. p4-depth's sign should confirm that before anyone relies on it.
- Implication for a purple or organic title: no morphology channel passes, so none becomes a candidate channel. The hypothesis register entry I4 stays "untested with a validated colour-agnostic channel". A relief-only title below ~20 um is below this pipeline's per-cell detection floor, and F5+ would need a new declaration (for example block-level aggregation) before any title-zone use.
- Records: PROTOCOL.md, unit_tests.json, tface.json, posctl.json, gate.json and runs.jsonl at commit 161da9d; code in tools/sib/p4-purple/mo/.
Integrity: no issues
