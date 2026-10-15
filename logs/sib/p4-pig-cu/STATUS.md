Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-cu STATUS

- 2026-09-26: step 1 done: MEMO.md, physics.json (NIST SRD 126), calib.json (control-only grey-level probe: air mode 41, papyrus mode 109).
  - Key numbers: Egyptian blue is 11.4x papyrus mu at 78 keV, versus augite 10x, calcite 8x and quartz 6x. Intensity cannot separate them.
  - Egyptian blue saturates uint8. Occupancy of 0.18-0.30 is enough to exceed T_hi 233.
  - Cu has no K-edge test in the Paris 4 energies.
- Next: step 2, params.json plus the frozen detector code, before any title-strip number.
- Blockers: none.
- Step 2 done: params.json FROZEN, with code sha256 in params_freeze.json. This precedes any E1 or E2 number.
  - Detector: grain = 26-connected component > T_g (C1/E1 233, C2/E2 199), >= 2 voxels, z-extent <= 13 slices. Per-cell occupancy at 0.1 mm, 0.3 mm stroke smoothing, 3.1 mm local-median background, z > 3, letter-scale clusters, score = cluster z-sum.
  - Control-only pre-freeze checks:
    - permutation null = 0 on 7 control tiles;
    - an injected Egyptian-blue letter scores ~1000-1600 against blank blocks at 0-83;
    - the sparse levels S2 and F1 are missed at conservative contrast, so the detection limit is bracketed.
- Next: sub-siblings a (E1), b (C1) and c (C2, E2) score the tiles. The parent runs the injections on all 4 materials.
- 18:30Z: step 3/4 running in this container with the frozen code (sha256 verified): scoring C1 -> E1 -> C2 -> E2, injection C1 -> E1 -> C2 -> E2, auto-push every 8 min. ~28 s per level-0 tile.
  - Blocker (ASK.md Q1): the 3 sub-sibling sessions were created idle and cannot be tasked from here. They are unused, and no further sessions will be created.
- 18:45Z: orchestrator addendum (DECL-P4-12, verified on origin), applied:
  - E2 (2.4 um, all 160 strip-a tiles) now has priority. Order: score E2 -> C2 -> C1 -> E1; inject E2 -> C2 -> E1 -> C1 (niced).
  - c10-c17 is reported separately.
  - Labelled-adjacency flags are reported, not used to exclude (item 3).
  - The detection limit is reported at 2.4 um.
  - C1 progress is kept: 4 tiles and 1 injection site, resumed later.
  - The frozen code and params are unchanged; only the run order and the analysis script changed.
- 2026-09-30T04:13:45Z: container restart at ~04:07Z killed all jobs. p4-pig-cu is INCOMPLETE, although the orchestrator trigger called it complete. Saved (0c15643): E2 160/160 scored, C2 31 tiles, C1 5, E1 0; injection E2 12/12, C2 12/12, E1 8/12, C1 1/12; no thresholds, REPORT or verdict yet. Resume with tools/sib/p4-pig-cu/run_all.sh + inj_all.sh (frozen code; resumes). Superseded by the FL PASS 3 assignment; waits for the orchestrator.
