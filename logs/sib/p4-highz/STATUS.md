Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz STATUS

- 2026-09-26 ~18:20Z. State: step 2-3 running (stage_b, level 0, control then E1; ~19 s per tile, ~40 min total). E1 PNG tiles are committed per row under f1/tiles.
- Step 1 done (a9eead1): thresholds.json FROZEN before any tile: T_mid = 80, T_hi = 233 (control in-sheet voxels > 0, 6 % whole-chunk sample; 3.43 G control sheet voxels).
- Physics (physics.json): control sheet p50/p99/p99.9/p99.99 = 80/169/233/255; E1 77/176/234/255. Saturation (voxels at 255): control sheet 0.030 %, E1 0.021 %. Density of voxels > T_hi is the same in the sheet slab and the +-(60-120) um gap slabs (control 0.00097 vs 0.00099; E1 0.00099 vs 0.00085), so strip-level f_in is 0.19-0.22, the depth-uniform value (13/67 = 0.194). KS D control vs E1: sheet voxels 0.022, gap voxels 0.022, per-px sheet maximum 0.076.
- Mesh-valid vertex counts equal the source grids exactly (C 86,593,672; E1 82,137,796).
- Next: screen.json, full-coverage f_in for tiles with n_hi > control p99, f1/manifest.json, REPORT.md.
- Blockers: none. Sub-siblings: none (SUBSIBS.md).
