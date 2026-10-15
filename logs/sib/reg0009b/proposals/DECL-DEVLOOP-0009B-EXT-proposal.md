Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal (for the orchestrator to record; not a declaration): 0009B DEV registry extension

Rule: DECL-DEVLOOP-A1 item 7, as ruled 2026-09-26 05:59Z: outside every KTLB-M candidate window + 144 vox, point-to-surface, in native 2.401 um vox; 0009B is never trained on (known-text pool rule).

Clearance: vertex-to-vertex distance >= 173 2.4-um vox = 144 + 2h (h = 14.2 vox, the half-diagonal of the 20-vox mesh cell). This bounds the point-to-surface distance at >= 144. Every item below has a minimum vertex clearance >= 173 (column clr).

Items are deduplicated in 3-D: no two share >= 10 % of vertices within 10 vox.

Numbers only. No map of any item exists, and none is made before this is recorded.

## PRIMARY: exclusion = all 76 dense KTLB-M candidate windows

2 x 2 cm windows: 1, of which ink150 >= 0.05: 0. 1 x 1 cm blanks (coverage >= 0.90, ink150 < 0.01): 6. Minimum clearance 187.4 vox.

| # | kind | segment | 2.401 um canvas box (x0,y0,x1,y1 px) | valid | ink150 | clr (2.4-um vox) |
|---|---|---|---|---|---|---|
| 1 | 2cm | 20250510172639 | [4160, 8320, 12500, 16660] | 1.0 | 0.0129 | 217.2 |
| 2 | blank1cm | 20250919124917-auto_grown_20250919054917419_inp_hr | [0, 2080, 4160, 6240] | 0.9406 | 0.00881 | 319.5 |
| 3 | blank1cm | 20250510172639 | [8320, 4160, 12480, 8320] | 1.0 | 0.00116 | 243.5 |
| 4 | blank1cm | 20250510172639 | [10400, 0, 14560, 4160] | 0.9671 | 0.00942 | 215.0 |
| 5 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [2080, 0, 6240, 4160] | 0.9592 | 0.00219 | 204.0 |
| 6 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [8320, 6240, 12480, 10400] | 1.0 | 0.00934 | 197.3 |
| 7 | blank1cm | 20250511200236 | [4160, 2080, 8320, 6240] | 1.0 | 0.0 | 187.4 |

## ALTERNATIVE: exclusion = the 23-window deduplicated pool

2 x 2 cm windows: 4, of which ink150 >= 0.05: 0. 1 x 1 cm blanks (coverage >= 0.90, ink150 < 0.01): 7. Minimum clearance 182.2 vox.

| # | kind | segment | 2.401 um canvas box (x0,y0,x1,y1 px) | valid | ink150 | clr (2.4-um vox) |
|---|---|---|---|---|---|---|
| 1 | 2cm | 20250919124917-auto_grown_20250919054917419_inp_hr | [0, 4160, 8340, 12500] | 0.9798 | 0.0237 | 198.6 |
| 2 | 2cm | 20250510172639 | [0, 8320, 8340, 16660] | 0.9187 | 0.0208 | 227.1 |
| 3 | 2cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [0, 8320, 8340, 16660] | 0.9127 | 0.0201 | 182.2 |
| 4 | 2cm | 20250511200236 | [4160, 0, 12500, 8340] | 0.9762 | 0.0066 | 188.8 |
| 5 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [2080, 0, 6240, 4160] | 0.9592 | 0.00219 | 1905.7 |
| 6 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [18720, 6240, 22880, 10400] | 1.0 | 0.00202 | 574.4 |
| 7 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [2080, 4160, 6240, 8320] | 1.0 | 0.00553 | 477.6 |
| 8 | blank1cm | 20250510172639 | [0, 0, 4160, 4160] | 0.9073 | 0.00541 | 326.9 |
| 9 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [6240, 18720, 10400, 22880] | 1.0 | 0.00031 | 268.6 |
| 10 | blank1cm | 20250919135433-auto_grown_20250919065433578_inp_hr | [6240, 4160, 10400, 8320] | 1.0 | 0.00225 | 247.3 |
| 11 | blank1cm | 20250510172639 | [10400, 0, 14560, 4160] | 0.9671 | 0.00942 | 215.0 |

## Consequence

Under either exclusion set, 0009B supplies no text DEV window: every allowed 2 x 2 cm window has ink150 < 0.05. The blanks also still need the model-based blob-f180 <= 0.0272 check, which is not computable before a map exists.

0009B therefore cannot count as a DEV scroll toward FINALIST (it needs text windows and >= 4 blanks) unless KTLB-M seals a subset of its candidate pool and releases the rest. Recording this extension is still useful, because it freezes the blank list and the geometry.

## Hashes (sha256)

- tools/sib/reg0009b/devzone.py: 8690bb94608a43e4543bf09cd4e63c6088ca5591fd176870dff05a28beafd15a
- tools/sib/reg0009b/devreg_proposal.py: 5b017b3e21877547e60fb0358436193c368dc6fe2f3cf15f02db186dcd37d6de
- tools/sib/reg0009b/windows.py: 5d969e2705cd6c9d5beb38ad7fcffafc55353e70c2efd938bb2eb65adb951559
- tools/sib/reg0009b/dedupe.py: ecc9f102c5317278d4e4db9835c3b429f3fff550c03e332bd53e07c7455b9ecf
- logs/sib/reg0009b/devzone.json: 4f96725632989b8bddf04fdf4b0b03292fa45d15a00b200791373d5cbcdbb252
- logs/sib/reg0009b/windows.json: 2c8d75659262ac6d0e11a6fad5adce19d46f2f6d3ca8ef54f0080c00c2d484f0
- logs/sib/reg0009b/windows_dedupe.json: 4ddd8d3ecfe602e3e3994a54f51649f2e044e136424ed97d3d9c7cd1c1f4ac6e
- logs/sib/reg0009b/overlap_frame9.json: 73ccdae2b5ab1225df5fcf201e2490915a2e503512a391f6f5440c8fbec9a478
- logs/sib/reg0009b/proposals/devreg_0009b_extension.json: 98d06140824cfdd30c1aa1c03c76bfc94becf5bdeb26ba537f040b12dfc3f7e4
