Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal (not a declaration): record the regrescan C6 results

- PHerc1203 (9 um 20250820131727 <-> 2.403 um 20260319130212): PASS. Held-out median r 0.879, RMS 0.732 vox, control median drop 0.655 (16/16 lower). Affine: logs/sib/regrescan/PHerc1203/final_affine.json, sha256 09d7caeb021d8ffcd6dfcd68daa8edb2711414e30f1eb553b48da0307eaa8f33. Band (9 um z covered by the rescan array): 7933.8-11826.9 in any column, 7942.2-11818.5 in all columns. No flip or axis permutation; z-axis tilt 0.086 deg.
- PHerc0846A (9 um 20250728152254 <-> 2.403 um 20260319102732): FAIL on the r bar. Held-out median r 0.8439 (< 0.85), RMS 0.720 vox (pass), control drop 0.757 (16/16 lower); fit iteration 1, sha256 bcb9c43fab0675ca2c752fb60f37092b80a7787f712cbc8cbf1f5f4bb85b956f. The affine must not be recorded as a C6-validated registration. No flip; rotation about x/y 0.254/0.115 deg (archive 0.26/0.12).
- Round trip 9 -> 2.4 -> 9 um: < 2e-12 vox exact; <= 0.215 vox after rounding to a stored rescan voxel, on both scrolls.
- I11 unchanged: CT-to-CT mapping only; no ink model and no rendering; the affines never choose a region.
