Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz protocol addendum for DECL-P4-6-A3 (P4-F at the calibrated depth d*, or the offset sweep)

Written and pushed at ~21:50Z, before any d* exists (neither p4-depth calib.json nor p4-tiles-b calib_1129.json is on its branch) and before any offset number. Everything not listed here is unchanged from PROTOCOL.md / PROTOCOL_2p4.md: thresholds (thresholds.json, thresholds_2p4.json), the hotspot rule, and the autocorrelation, stroke and injection definitions.

## Offset
- The offset o (um, positive = increasing slice index, the p4-highz slice convention) is converted to slices as round(o / voxel): 2.258 um for E1, 2.4 um for E2. If a calibration reports d* in another sign convention, it is converted to this one and recorded in screen_dstar.json.
- Sheet slab: centre + o_s +- 6 slices (13 slices, +-15 um).
- Gap slabs: offsets 27..53 (E1) or 25..50 (E2) slices from centre + o_s, on both sides, as declared.

## Gap slabs outside the surface volume (a geometric limit, disclosed)
- The surface volumes hold only 116 x 2.258 um (+-131 um) and 109 x 2.4 um (+-130 um). For |o| above ~10 um, part of one declared gap slab falls outside the volume.
- Rule: gap slices outside the volume are dropped, and the gap count is rescaled to the declared number of gap slices (n_gap x declared / available). The rescaled f_in keeps the declared depth-uniform baseline (13/67 or 13/65).
- If one side has 0 available slices, only the other side is used, rescaled the same way. The number of available slices per side is reported.
- Nothing is read from the full volume. Doing so would need a normal-direction resampling that is not declared.

## f_in sample
- The same 6 % whole-chunk sample positions (default_rng(20260926)) as step 1, recomputed at each offset. The full-coverage f_in for tiles above the control p99 is also at each offset.

## Sweep (only if every calibration STOPs)
- o = -60, -45, ..., +60 um (9 offsets). Hotspot n_hi bar = numpy.percentile(control tile n_hi at that same offset, 100 x (1 - 0.01/9)), linear interpolation.
- The f_in bar stays at 0.8.
- The control is screened at every offset too.

## Injection-recovery
- The glyph layer's lower face is at centre + o_s. Everything else is as inject.py.

## Outputs
- screen_dstar.json and inject_dstar.json, plus a REPORT addendum. c10-c17 are reported separately for E2.
