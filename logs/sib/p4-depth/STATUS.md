Provenance: Project HERCULES | owner the owner | [id removed]

# p4-depth STATUS (DECL-P4-12-A3, P4-L3 builder)

## VERDICT: STOP (frozen; calib.json). No ink layer by the declared rule; P4-L3 stops. No title-strip voxel was read.

- Control 20260701183125-w028-037 2.4 um SV, level 0, 24 of 168 tiles (seed 20260927, frozen at faccba7), all 109 slices,
  1.55e9 mesh-valid px per slice; T_hi 203 (p4-l2, ca715bc1...).
- f(o) (frac of voxels > 203): smooth and broad, range 8.24e-4 (o = +43 um) .. 1.074e-3 (o = -31.2 um); median 9.42e-4,
  robust SD 6.8e-5.
- d* = -31.2 um (slice 41), z_peak = 1.94 < 3 -> STOP. It is within +-100 um, but the z bar fails.
- Both sides: minus (o < 0) best -31.2 um z 1.94; plus (o > 0) best +129.6 um (the range edge) z 0.14.
- Sign convention (sign.json, measured):
  - SV slice index grows along -(du x dv): 360/360 vertices; median profile r 0.989 vs -0.125 against the 2.4 um volume 20260411134726.
  - du x dv points outward: geometric centre 99.1 % of 92.7 % clear vertices; the volume-axis centre gives the same sign (79 %).
  - Therefore o > 0 = toward the umbilicus (inward) = RECTO (papyrological convention), and o < 0 = outward = VERSO.
  - d* lies on the verso side.
- Diagnostics, reported only (none enters the verdict):
  - peak FWHM 57.6 um (-62.4 .. -7.2), broad, not a 10-20 um deposit;
  - per-tile argmax within 5 um of d* in 4/24 tiles (the per-tile argmaxes are scattered from -130 to +130 um);
  - 1/24 tiles pass alone;
  - bands: r0-r1 STOP (z 2.68 at +129.6), r2-r8 STOP (z 1.75);
  - Bonferroni bar 4.22 is not met;
  - the rot90 check is identical.
- Gap depths (my frozen interpretation, ASK item 1): the pooled median voxel is < T_mid 93 at all 109 slices (max 91), so every
  slice is "gap" and the definition is uninformative here. The on-sheet baseline is empty. Reported as such.
- Unit tests (unit_tests.json):
  - asserted parts pass: a 15 um layer with a 2.4 um PSF gives d* within 2.4 um (21/21), and a noise-free uniform sheet gives STOP;
  - finding (ASK item 2): the declared rule gives PASS on 25/100 iid-noise sheets and on 10/10 no-ink sheet+gap profiles.
    Here the real verdict is STOP anyway, so the finding does not change the outcome. It limits what a PASS would have meant.
- Skipped because of STOP:
  - task item 2 (L3 tiles);
  - orchestrator addendum items 2-3 (P4-V verso-face tiles, vpc, raw arrays at d*).
  - This is consistent with p4-tiles-b's 1.129 um STOP.
- blockers: none. next: none unless the orchestrator declares an amendment.
