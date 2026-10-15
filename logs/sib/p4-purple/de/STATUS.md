Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple-de STATUS

- 2026-09-27: DONE. DUAL_FREEZE.md + REPORT.md pushed; stopped as briefed.
- Part A done (inventory.json, overlap.json).
  - w010-027 geometry only: 3.01 % of valid E2 vertices inside the 137 keV extent (2.30 % inside the reconstruction cylinder);
    per-tile values identical to p4-highz kedge_coverage_e2.json (max abs diff 0.0); title-zone r3_c10-c17 14-27 % (extent),
    9-21 % (cylinder). No 137 keV byte fetched for w010-027.
  - Control w028-037: 4.40 % of valid vertices (1.29 M) inside the extent, in rows r3-r4; sampled non-zero 137 keV fraction
    mostly 0.75-0.97 per tile. Distance fence (amendment A-1): 84 % of those vertices are readable as single bytes, 57 % as
    128^3 block centres; 7,682 of the sampled reads were refused by the fence and skipped.
  - Physics from metadata: both volumes Paganin (delta/beta 1000 at 78 keV, 2000 at 137 keV) + strong unsharp mask; Paganin
    kernel length 16.7 / 17.8 um. Polychromatic BM18 beam; spectrum not published.
- Next: PROTOCOL Part B (registration, decomposition, statistic, validation) before any 137 keV block is read.
- Blockers: none.
- 2026-09-27 12:45Z: METRIC-HASH-40 application done once (title_zone.json, APPLY.md). Title zone r3 c10-c17 (11,674 used patches): 1 isolated hotspot (z < -T, c11); rate 0.0001 vs control FPR 0.0215: dual-energy NULL.
- Sensitivity limits: only CuO, orpiment, gold (10-20 um) are detectable; Tyrian purple (any Br loss), purpurissum, alumina/gypsum lakes, carbon ink, red ochre, cinnabar, lead white are NOT detectable at <= 20 um.
- So a purple, lake or carbon-ink title is "untestable by dual energy", not "absent"; the null excludes only Cu/As/Au-type layers >= 10 um on the covered 14-27 % of r3 c10-c17.
- Defect (reported, not fixed): rows r4 and r3 c0-c9 show positive z drift at the 137 keV volume's lower end / cylinder edge, outside the control domain (title_zone_diag.json); those hotspots are artefacts.
- Integrity: no issues.
- Resume case: the container kept $S/apply/b_*.json (623/1781 blocks at the 11:03Z restart); the three workers were continued with the same code; no block was recomputed. All 39,242 patch records (37,202 used, fv >= 0.5) are pushed in apply/patches.jsonl.gz.
