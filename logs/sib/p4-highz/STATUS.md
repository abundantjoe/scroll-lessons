Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz STATUS

- 2026-09-27 ~07:00Z. DECL-P4-6-A3/-A4 **DONE**. Both calibrations are STOP, so the 9-offset sweep (-60..+60 um, Bonferroni bar) was run on both strips.
- **E1 (screen_dstar_E1.json):** 0 DENSE-HOTSPOT at every offset.
  - Above the bar: r2_c10 (0 um), and r2_c14 (0, 15, 30 um); full-coverage f_in 0.18-0.28.
  - Largest component: 0.41 mm (control 0.46-0.67).
- **E2 (screen_dstar.json = screen_dstar_E2.json; 160 tiles = p4-highz + hzw1 17f8182 + hzw2 fd74bfe; merge checks exact):** 0 DENSE-HOTSPOT at every offset.
  - Per offset, tiles above the bar (full f_in):

    | o (um) | tiles above the bar |
    |---|---|
    | -60 | none |
    | -45 | none |
    | -30 | none |
    | -15 | r7_c19 (0.23) |
    | 0 | r7_c19 (0.26) |
    | 15 | r7_c19 (0.27) |
    | 30 | r7_c18 (0.19), r7_c19 (0.27) |
    | 45 | r7_c18 (0.23), r7_c19 (0.26) |
    | 60 | r7_c18 (0.28), r7_c19 (0.22) |

  - E2 max f_in per offset is 0.38-0.46, against the bar of 0.8.
  - Largest E2 component: 0.52-0.81 mm. The control's is 0.96-1.42 mm.
  - **Title zone c10-c17:** no tile above the bar at any offset; 0 hotspots; max f_in 0.37-0.45; largest component 0.81 mm (at -30 um).
- **panel_ext.json** (DECL-P4-16 item 2) is done. REPORT.md has addendum A3.
- DECL-P4-14-A4 P4-O tile r2 c14 (PHerc.1667 iteration 5): started 06:45Z; STOPPED 06:57Z per P4-O-STAGE-O2S1-RESULT (gate 0/3 FAIL). No tile was produced, and /work/p4o is deleted.
- Blockers: none. Standby (economy mode, no polling).
