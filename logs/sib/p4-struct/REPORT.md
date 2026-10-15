# P4-I report (RULES.md DECL-P4-8): numeric ink-structure screen of the Paris 4 title strip w010-027

Provenance: Project HERCULES | owner the owner | [id removed]
Sibling p4-struct. Numbers only: every tile was read as a uint8 array (cv2/numpy). No image, tile or CT pixel was opened, displayed or described.

## Result
**No material passed its sensitivity gate, so every material is uninformative. There are 0 STRUCT-positive tiles.**
This is not a negative result about the papyrus. As declared, the gate cannot be passed by any data (ASK-1 below). E1 and E2 have no control on their own material, so their gate cannot be evaluated at all (ASK-2).

| material | strips (tiles) | px_per_mm (manifest) | band 3-9 mm in canvas px | T_mat = p99 rot-90 null | non-blank controls | above T_mat and within +-10 deg | gate (bar 30 %) | AUC control vs rot-90 | status |
|---|---|---|---|---|---|---|---|---|---|
| M1 | M1 160 + M1-b 171 | 417.131 (a) / 415.039 (b) | 1251-3754 / 1245-3735 | 98.46 | 86 | 2 (2.3 %) | fail | 0.500 | uninformative |
| M2 | M2a 60 + M2b 64 | 443.622 (a) / 443.468 (b) | 1331-3993 / 1330-3991 | 81.23 | 32 | 2 (6.3 %) | fail | 0.497 | uninformative |
| E1 | E1-A1 60 | 443.622 | 1331-3993 | 32.47 | none | - | not evaluable | - | uninformative |
| E2 | E2 160 | 417.131 (grid.json; the manifest has none) | 1251-3754 | 40.22 | none | - | not evaluable | - | uninformative |
| P4-F | not built yet | - | - | - | - | - | - | - | not run |

- All tiles are at the display scale of 53.4 px/mm (1068 px per 20 mm). The 3-9 mm band is 160-481 display px, or 40-120 px at the analysis scale of 13.35 px/mm.
- Control median theta* (the axial median over non-blank controls): 90 deg for both M1-b and M2b. The wavevector is along the canvas rows, so the lines run along the canvas x axis.
- STRUCT-positive lists (positives.json) are empty for M1, M2a, E1-A1 and E2.
- Labelled adjacency: M1 and E2 use excl_a (labelled_adjacent_union), with 120 flagged and 40 not flagged. excl_d_a (M2a, E1) is not yet pushed, so those tiles are fail-closed.

## Validation (item 6)
- Gate numbers: see the table and gates.json.
- AUC of S_row for control tiles against their rot-90 copies: 0.500 (M1-b) and 0.497 (M2b). That is chance, and it is chance by construction (ASK-1).
- Jaccard of STRUCT-positive sets on the shared grid:
  - M2a vs E1-A1: undefined, because both sets are empty (60 common tiles).
  - P4-F: not built. The permutation p is undefined.
  - The code is in place (jaccard_perm_p, 10^4 permutations, seed 20260926).

## Why the gate cannot pass (ASK-1, a declaration defect)
- S_row is a maximum over all orientations, normalised by the median over all orientations. A 90 deg rotation only permutes the 2 deg orientation grid. So S_row(rot90 tile) = S_row(tile), and theta* moves by exactly 90 deg.
  - Unit test: relative difference < 1e-3 on synthetic tiles.
  - On the real tiles, the median relative difference is 5e-6 to 2e-3. A few tiles differ by up to 9 %, where float32 rounding flips between near-tied band peaks.
- So the rot-90 null is the material's own S_row distribution, and T_mat is its own p99. At most about 1 % of tiles exceed it, and the 30 % control bar cannot be met.
- Synthetic smoke of the full runner (synthetic_smoke.json): 12 control tiles with obvious planted text rows.
  - Declared rule: 0 of 6 non-blank controls pass, AUC 0.507, "uninformative".
  - The proposed orientation-anchored variant (not declared; tested on synthetic tiles only): 6 of 6 pass, AUC 0.993, and all 3 planted title tiles are above T.
  - No real-tile number of the variant exists.

## Descriptive only (not a rule, not a claim): theta* distribution from struct.json
Share of tiles whose theta* is within +-10 deg of 90. Pure noise gives about 12 % (11 of 90 orientation bins).

| strip | share of tiles | median S_row |
|---|---|---|
| M1-b (control) | 0.78 | 17.6 |
| M2b (control) | 0.66 | 18.7 |
| M1 (title) | 0.47 | 11.0 |
| M2a (title) | 0.48 | 11.8 |
| E1-A1 (raw CT) | 0.18 (0.47 near 0 deg) | 8.8 |
| E2 (raw CT) | 0.24 (0.34 near 0 deg) | 8.5 |

- Row-direction structure (theta about 90) is common in the known-text prediction maps and less common in the title strip's.
- Caution: other anisotropic structure along the winding direction can also sit at theta 90, such as sheet contacts, compression or mesh seams. A rot-90 null does not separate those from text; only the control/title contrast is informative.
- The raw-CT displays lean to the orthogonal axis.
- None of this is a reading, and none of it is used for selection.

## Method as implemented (fixed before any real-tile number; code sha256 in struct.json meta)
- Support (item 2, "mesh-valid, in-scan"):
  - tiles are 0 outside mesh-valid and, on the 1.129 um materials, 0 out of scan;
  - support = the complement of connected zero regions of >= 2 mm^2;
  - smaller zero blobs are valid dark pixels (for example the 1 % clip of the CT stretch) and stay in.
- Check against the manifests: on M1 and M1-b, the PNG zero fraction equals 1 - valid_fraction (median difference 0.0000).
- Field:
  - INTER_AREA /4 to 13.35 px/mm;
  - subtract the local mean (normalised Gaussian, sigma 4 mm; the pass band at 9 mm is > 99 %);
  - taper at the support edge (erode 1 mm, blur sigma 0.5 mm);
  - apply a radial Tukey window (rotation-symmetric, so there is no axis leakage).
- Spectrum:
  - |FFT|^2 zero-padded to 1024;
  - polar sampling with 48 radii linear in |k| over periods 3-9 mm, and theta 0-178 deg in 2 deg steps.
- S_row = max over theta of P(k*(theta), theta) / median over theta' of P(k*(theta), theta'), where k*(theta) is the band peak. theta* is the angle of that max.
- Flat or insufficient tiles:
  - weighted RMS < 0.25 grey level, or support < 25 % after erosion, gives S_row = None;
  - such a tile is never positive and is left out of the null;
  - 0 tiles were flat or insufficient.
- M_ink = the fraction of support pixels above the control strip's pixel p95 (M1-b p95 = 235; M2b p95 = 227). Non-blank means M_ink >= the control median.
- Eligibility:
  - M1, M1-b and E2: all manifest tiles (>= 50 % valid);
  - M2a, M2b and E1-A1: DECL-P4-4-A1 under METRIC-HASH-29 semantics, giving 60, 64 and 60 tiles.
- Inputs: every PNG's sha256 matches its manifest (675 tiles, 0 mismatches). Branch commits and manifest sha256 are in struct.json inputs.
- Tests: tools/sib/p4-struct/test_struct.py, 15 passed. They cover:
  - planted gratings at 6 pitch/orientation pairs: theta* within 5 deg, and S_row above the noise rot-90 p99;
  - pure noise above the rot-90 p99 at <= 2 %;
  - blank tiles never positive;
  - a straight invalid half-tile edge not read as rows;
  - small zero blobs kept in the support;
  - rot-90 invariance (ASK-1);
  - angle, AUC and Jaccard helpers;
  - the gate and positive rules;
  - the proposed variant.
- Sensitivity on synthetic text-like rows at random pitch 3.5-8.5 mm and random orientation, with noise sd 25:
  - planted rows exceed the noise-only p99 with theta* within 10 deg in 10-12 of 12 tiles for amplitudes 20-90;
  - theta* error: median 0.8-1.5 deg, max 5.7 deg.

## Reproduce
```
python3 tools/sib/p4-struct/run_struct.py --data <dir with logs/sib/{p4-tiles-a,p4-tiles-b,pairs0814b/e2,p4-excl,p4-highz/f1}> --out logs/sib/p4-struct
```
The run takes 33 s on 4 CPUs and is deterministic.
