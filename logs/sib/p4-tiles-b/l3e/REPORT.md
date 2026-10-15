Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-b report: P4-L3 at 1.129 um (DECL-P4-12-A4): calibration STOP

Builder role only. No tile, map or CT pixel was opened, viewed, displayed or described. Only numbers were computed. **No title-strip number and no L3 tile was produced**, because the calibration stopped.

## Order of pushes
1. calib_selection.json (commit 67a1e40), recorded before any number.
   - 24 control tiles were drawn by seed 20260926 from the M2b tiles with coverage < 0.5.
   - 40 level-0 chunks were drawn per tile (960 in total).
   - The tile level for L3 (level 1) was also recorded there.
2. calib_1129.json (commit 96c8811): the verdict **STOP**, before any title-strip computation.

## Calibration numbers (control 20260623142658-w028-037, level 0, T_hi 233 from p4-highz)
- Chunks used: 826 of 960 drawn. 134 are absent from the bucket (list in calib_1129.json).
- f(o) = fraction of voxels > 233 among mask voxels > 0, over offsets -131..+129 um (116 slices).
  - Median 1.118e-3. Robust SD (1.4826 MAD) 1.60e-4.
- The global max of f - median is at o = +99.35 um (slice 102), inside the +-100 um window, with **z = 1.12 < 3**. Hence STOP.
- The alternative denominator (all mask voxels) gives the same result: peak +99.35 um, z = 1.14, STOP.
- Both mesh sides, best peak within +-100 um:
  - negative side: -2.26 um, z 0.88;
  - positive side: +99.35 um, z 1.12.
- Profile shape: f varies only between 0.84e-3 and 1.29e-3 across all offsets.
  - f is 0.91e-3 in the gap depths (|o| > 100 um) and 1.14e-3 within +-100 um.
  - There is no narrow peak. The half-max run around the global max is 33.9 um wide, with centroid +89.3 um.
- Per-tile peaks (24 tiles) are scattered: median -6.8 um, p10 -114.7 um, p90 +102.5 um.
  - 9 of the 24 tiles would pass individually. That is in line with the measured false-PASS rate of 0.17 of the rule on layer-free profiles, and with there being no common depth.
- Rot-90 sanity on the first chunk: identical counts.

## Verdict
- Under the declared criterion, the known-text control shows **no ink layer at a consistent depth** within +-100 um of the mesh at 1.129 um with T_hi 233. P4-L3 at 1.129 um stops (DECL-P4-12-A3 item 1), and no L3E tiles exist.
- This is a statement about this channel and threshold only. It is not evidence that no ink is present.

## Unit tests (tools/sib/p4-tiles-b/test_l3e.py, 27 pass)
- A synthetic peaked layer is recovered within 5 um. A flat-topped 15.8 um layer is recovered by argmax to within the half thickness, and by the half-max centroid to within 5 um.
- No bright voxels gives STOP. A layer outside +-100 um gives STOP.
- Documented limitations of the rule:
  - on a flat layer-free profile it falsely passes at a measured rate of 0.17;
  - a pure sheet-density bump passes at d* ~ 0.

## Sub-siblings
- None were created. The job took under a minute once started.
