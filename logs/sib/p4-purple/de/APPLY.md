Provenance: Project HERCULES | owner the owner | [id removed]
# One-time application of DUAL_FREEZE (METRIC-HASH-40, RULES.md 2823de4) to w010-027; written before any number
Verified before running: RULES.md METRIC-HASH-40 records sha256 93d04a4d...f9427 = DUAL_FREEZE.md; all 15 section-7 hashes match.
Frozen and applied unchanged (read from fit.json / registration.json, not refitted on w010-027): registration = published
composed affine + affine correction W (control fit); window +-60 um (51 samples at 2.4 um along the mesh normal); patch
83 x 83 canvas px (0.2 mm); px valid iff all 51 samples > 0.5 grey in both volumes; patch used iff >= 50 % px valid;
C_E = mean float over valid px and samples; Z = C137 - (0.67947 C78 + k0); z = (Z - median) / MAD; hotspot |z| > 3.0696
AND C78 >= on-sheet threshold. Normals: d/dj x d/di of the mesh grid, bilinear interpolation (as sites.py).
Application-only rules (no parameter): mesh 20260701183124-w010-027 on 20260411134726-2.4um (E2); patch grid anchored at
canvas (0, 0) in 83-px steps, processed in 6 x 6-patch blocks (498 px); every block containing a mesh vertex inside the
137 keV extent; px whose bilinear mesh neighbourhood or normal is undefined are invalid; patch -> tile (pairs0814b e2
grid, T 8343) by its centre px. Per tile: used patches, on-sheet patches, hotspots with z < -T and z > +T, largest
4-connected hotspot cluster (patches), hotspot rate over used patches vs control FPR 0.0215 (same denominator as the
control), one-sided binomial p. One run only; a crash is resumed, never rerun with other settings.
The 137 keV fence is lifted only for this run (tools/sib/p4-purple/de/apply.py; frozen tool files unchanged).
