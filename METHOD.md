# METHOD.md

Provenance: Project HERCULES | owner the owner | [id removed]

Only methods that passed their unit tests and gates appear here, each with code hash.
Nothing below is yet validated on real data in this restart.

## Status (2026-09-24)

| Method | Code | Unit tests | Real-data gate | Status |
|---|---|---|---|---|
| RULES.md chain | `src/hercules/records/rules_append.py` | pending | n/a | building |
| Scorer | `src/hercules/scorer/` | pending | synthetic validation | building |
| level_mesh + handedness | `src/hercules/geometry/level_mesh.py` | pending | REF readers on 0139 and 0009B | building |
| v2 truncation | `src/hercules/geometry/truncation.py` | pending | n/a | building |
| Contamination / FL-09 certificate | `src/hercules/geometry/contamination.py` | pending | planted re-trace fault | building |
| 9 um render (C1) | official `vc_render_tifxyz` (villa 41701aa) | n/a | C3: Pearson 0.99999 on 4 crops, 2 segments | VALIDATED (C3-NT-R1-VERDICT) |
| 9 um reader C2 (with --tta-mirror) | official `vesuvius.ink_detection.inference.infer` | n/a | C3-R1: forward 0.97795 < 0.987 | FAILED (C3-R1-VERDICT) |
| 9 um reader C2-NT (no TTA) | same CLI, both orders, batch 4, --no-compile, CPU | n/a | C3-NT-R1: 0.99960 / 0.58558 | VALIDATED (C3-NT-R1-VERDICT) |
| Reader prompt P / display D* | not frozen | n/a | READ-CAL | frozen only after READ-CAL |

## READ-CAL frozen (READCAL-FREEZE, 2026-09-25)
- D* = K_D2: key sheet (configs/briefs/probe2_keysheet.png, sha256 5da96bde...) first, then 2 x 2 cm windows at 1/2 scale (1068 px), no contrast change.
- P* = configs/briefs/k_d2_task.txt (sha256 74a0cbe8...) for single images; configs/briefs/k_d2_pairs_task.txt (sha256 bd03427e...) for LEFT/RIGHT pairs (METRIC-HASH-14).
- Reader model: fable. SG-FEAS NOT PASSED. sigma_crit from the D1 REF ladder.
