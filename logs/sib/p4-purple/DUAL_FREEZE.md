Provenance: Project HERCULES | owner the owner | [id removed]

# DUAL_FREEZE: 78/137 keV dual-energy method, frozen on the control strip only (DECL-P4-16 item 3)

Branch claude/gifted-bell-gavnl5-sib-p4-purple-de. Protocol: logs/sib/p4-purple/de/PROTOCOL.md (Part A, A-1, Part B, B-1).
No 137 keV or dual-energy number exists for w010-027; there only geometry was computed. Numbers only; no image viewed.

## 1. Inventory (inventory.json)
- 137 keV: 20260323153942-2.400um-0.2m-137keV-masked, uint8 zarr (6625, 8431, 8431), chunks 128^3, uncompressed; Paganin delta/beta 2000, unsharp 5 / 2.5 px, GHBP; window [0.01, 0.16]; helical, BM18, 2026-03-15; double-flat ring correction on; SAM2 mask.
- 78 keV: 20260411134726-2.400um-0.2m-78keV-masked, (75784, 32693, 32693); Paganin 1000, unsharp 4 / 1.2 px; window [-0.04, 0.22]; 2026-03-10/11.
- Both: z 0.22 m, 2.4 um, polychromatic beam (nominal energies; spectrum and float units not published). Paganin kernel L 16.7 / 17.8 um.

## 2. Overlap (overlap.json)
- w010-027 (geometry only): 3.01 % of valid vertices inside the 137 keV extent (2.30 % inside the reconstruction cylinder); per tile identical to p4-highz (max abs diff 0.0); r3_c10-c17 14-27 %.
- Control w028-037: 4.40 % (1,292,391 vertices), rows r3-r4; sampled non-zero 137 keV mostly 0.75-0.97 per tile.
- Fence (A-1): no 137 keV chunk within 146 voxels (0.35 mm) of any w010-027 vertex; enforced on every chunk fetch (dcommon.fence_check).

## 3. Registration (registration.json; control only)
- Published composed affine, then 128^3 block NCC matching (sigma 1.5, +-16 vox, parabolic sub-voxel), 30 FIT / 30 HELD-OUT blocks split by tile-column parity; model = affine correction (LOO median 2.02 um vs local-translation 2.19 um).
- Published affine offset: median 7.8 um. Held-out block residual after correction: median 1.72 um, p90 3.24 um (n 29).
- Sheet-surface residual (half-max boundary along the normal, held-out sites, n 235,529): median |d| 2.36 um, p90 18.4 um, signed median 0.025 um. Goal < 5 um met on the median; heavy tail.
- Correction matrix W (rows x, y, z, 1 -> dxyz, REF voxels): [[0.0012815, -5.19e-05, -0.0001262], [0.0010769, -0.0001927, -0.0010286], [-0.0004466, 0.0010534, 5.42e-05], [-15.1669734, -46.6689376, 13.8269524]]

## 4. Decomposition and statistic (fit.json; 40 FIT sites, 1440 patches)
- Calibration: f = w_min + g (w_max - w_min)/255. Checks FAIL: 137 keV void 0.044 (78: 0.0038); implied papyrus density 78 0.43 vs 137 0.56 g/cm3; contrast ratio gives 137 keV gain 0.630. The 137 keV scale is not mu in cm^-1.
- Basis: papyrus line (any density or void mixture) + excess. Per 0.2 x 0.2 mm patch, depth column +-60 um (51 samples, 7 Paganin lengths): C_E = mean f_E. Z = C137 - (k C78 + k0), k = 0.67947 [0.662, 0.696], k0 = 0.037889 cm^-1 (Theil-Sen; Pearson C78-C137 0.892).
- z = (Z - -0.000217) / 0.004711. HOTSPOT: |z| > T = 3.0696 (FIT p99) AND C78 >= 0.01855 cm^-1 (on-sheet). Two-sided: Br/Ca/As/Cu/Fe (R 0.35-0.73) push z < 0; heavy K-edge pigments saturate the 8-bit windows and also give z < 0 (clipping), not the ideal z > 0.
- Secondary (report only): +-15 um column, k15 0.5837.

## 5. Control validation (validation.json; 40 HELD-OUT sites, 1440 patches; thresholds from FIT only)
- (a) Known-text carbon ink vs blank: AUC 0.483 [0.334, 0.629] (ink 185, blank 690 patches); hotspot rate ink 0.011, blank 0.023. As expected: no composition difference.
- False-positive rate (held-out, uninjected): 0.0215 per patch (nominal 0.01). +-15 um: 0.0118.
- (c1) rot-90 labels: AUC 0.484 [0.329, 0.634] (chance). (c2) misregistered 250 um: AUC 0.430, false-positive rate 0.118 (registration is required).
- (b) Injection, '+' glyph 0.4 mm strokes, phi 0.5 paint, layer on the + sheet surface, 12 patches x 40 sites = 480 per cell; forward model = linear Paganin with each scan's published parameters (unit gain at k = 0 verified: 1.0008 / 0.9994); colourants match colourants.json 143e1e6 to 1.4e-05. Recovery (fraction of injected patches that are hotspots):

| class | t um | Paganin | gain137 (B-1) | absorption | +reg. residual | misreg. 250 um | z mean (Paganin) |
|---|---|---|---|---|---|---|---|
| CuO | 5 | 0.64 | 0.68 | 0.00 | 0.64 | - | -3.20 |
| CuO | 10 | 0.99 | 1.00 | 0.00 | 0.99 | 0.92 | -5.72 |
| CuO | 20 | 1.00 | 1.00 | 0.00 | 1.00 | - | -7.92 |
| Fe2O3 (red ochre) | 5 | 0.00 | 0.00 | 0.00 | 0.00 | - | -1.37 |
| Fe2O3 (red ochre) | 10 | 0.20 | 0.35 | 0.00 | 0.24 | 0.36 | -2.38 |
| Fe2O3 (red ochre) | 20 | 0.76 | 0.84 | 0.00 | 0.76 | - | -3.48 |
| Tyrian purple 0% Br loss | 5 | 0.00 | 0.00 | 0.00 | 0.00 | - | -0.72 |
| Tyrian purple 0% Br loss | 10 | 0.01 | 0.01 | 0.00 | 0.02 | 0.20 | -1.57 |
| Tyrian purple 0% Br loss | 20 | 0.24 | 0.29 | 0.00 | 0.28 | - | -2.42 |
| Tyrian purple 50% Br loss | 5 | 0.00 | 0.00 | 0.00 | 0.00 | - | -0.14 |
| Tyrian purple 50% Br loss | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.10 | -0.58 |
| Tyrian purple 50% Br loss | 20 | 0.00 | 0.00 | 0.00 | 0.01 | - | -1.01 |
| Tyrian purple 90% Br loss | 5 | 0.01 | 0.03 | 0.02 | 0.01 | - | 0.33 |
| Tyrian purple 90% Br loss | 10 | 0.00 | 0.01 | 0.00 | 0.00 | 0.09 | 0.21 |
| Tyrian purple 90% Br loss | 20 | 0.00 | 0.00 | 0.00 | 0.00 | - | 0.07 |
| alumina lake | 5 | 0.01 | 0.04 | 0.01 | 0.01 | - | 0.45 |
| alumina lake | 10 | 0.01 | 0.03 | 0.00 | 0.01 | 0.09 | 0.52 |
| alumina lake | 20 | 0.00 | 0.01 | 0.00 | 0.00 | - | 0.54 |
| carbon ink | 5 | 0.02 | 0.04 | 0.03 | 0.02 | - | 0.48 |
| carbon ink | 10 | 0.01 | 0.03 | 0.00 | 0.01 | 0.09 | 0.49 |
| carbon ink | 20 | 0.00 | 0.01 | 0.00 | 0.00 | - | 0.48 |
| cinnabar | 5 | 0.00 | 0.69 | 0.00 | 0.09 | - | -1.69 |
| cinnabar | 10 | 0.12 | 0.89 | 0.00 | 0.30 | 0.28 | -2.54 |
| cinnabar | 20 | 0.50 | 0.95 | 0.00 | 0.54 | - | -3.02 |
| gold | 5 | 0.46 | 0.96 | 0.00 | 0.53 | - | -2.96 |
| gold | 10 | 0.83 | 0.99 | 0.00 | 0.80 | 0.71 | -3.59 |
| gold | 20 | 0.94 | 1.00 | 0.00 | 0.92 | - | -4.06 |
| gypsum lake | 5 | 0.01 | 0.03 | 0.01 | 0.01 | - | 0.31 |
| gypsum lake | 10 | 0.00 | 0.01 | 0.00 | 0.00 | 0.09 | 0.26 |
| gypsum lake | 20 | 0.00 | 0.00 | 0.00 | 0.00 | - | 0.20 |
| lead white | 5 | 0.00 | 0.58 | 0.00 | 0.07 | - | -1.45 |
| lead white | 10 | 0.06 | 0.86 | 0.00 | 0.21 | 0.22 | -2.34 |
| lead white | 20 | 0.39 | 0.95 | 0.00 | 0.46 | - | -2.87 |
| orpiment | 5 | 0.21 | 0.21 | 0.00 | 0.21 | - | -2.33 |
| orpiment | 10 | 0.89 | 0.90 | 0.00 | 0.90 | 0.78 | -4.35 |
| orpiment | 20 | 1.00 | 1.00 | 0.00 | 1.00 | - | -6.30 |
| purpurissum (5% dye on CaCO3) | 5 | 0.00 | 0.01 | 0.00 | 0.00 | - | 0.15 |
| purpurissum (5% dye on CaCO3) | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.09 | 0.06 |
| purpurissum (5% dye on CaCO3) | 20 | 0.00 | 0.00 | 0.00 | 0.00 | - | -0.06 |

'absorption' (pure mu, no Paganin spreading) clips at the 8-bit windows and recovers nothing; it is not the physical model of these volumes.
Detectable (recovery >= 0.8 in BOTH Paganin and gain137, per B-1): CuO: [10, 20] um; gold: [10, 20] um; orpiment: [10, 20] um. NOT detectable at <= 20 um: Fe2O3 (red ochre), Tyrian purple 0% Br loss, Tyrian purple 50% Br loss, Tyrian purple 90% Br loss, alumina lake, carbon ink, cinnabar, gypsum lake, lead white, purpurissum (5% dye on CaCO3).

## 6. Thresholds for any later title-zone use (to be applied unchanged)
All numbers of section 4 (k, k0, median, MAD, T, on-sheet threshold, window, patch grid rule, registration model W). Expected false-positive rate ~0.022 per patch on control; a title-zone claim needs a cluster of hotspots well above that rate and must be read against sections 5(a)-(c). Purple (Tyrian purple, purpurissum), alumina and gypsum lakes and carbon ink are NOT detectable by this method at <= 20 um; a null there means 'untestable by dual energy', never 'absent'.

## 7. sha256 of tool files
- tools/sib/p4-purple/de/analyze.py: fb0b26e4b58e6af5aa2b6d78d8b95f4fc15e26c650010fd5035b4a3e48790cde
- tools/sib/p4-purple/de/dcommon.py: e69fadd7e4fa93c682ccba4c2f86555a01d0b2039b7eb4801a611c1993707b4a
- tools/sib/p4-purple/de/inventory.py: a5efa962fd9e81b1409ff8021cceb5fa1e1d6ac360f487ff879affe8e555e1c9
- tools/sib/p4-purple/de/labels.py: 3e822a72d1a880cf3c472ba26733c9745149a10a01b1efcec2da6df11c3925f1
- tools/sib/p4-purple/de/overlap.py: 49a385c461ed51592ef9fea56842b6e73ecc08ec2bf4bdaad2d7834ab62bf2e0
- tools/sib/p4-purple/de/reg.py: cf98feeb2c67ad116a0ca6daa94e96f8f870bbfaef4dbc67afd90b9e7698e969
- tools/sib/p4-purple/de/sites.py: 544e3ad0e022fc1624754a76ed72ece90ea4b8e40baed3a3993339b55a40984a
- logs/sib/p4-purple/de/fit.json: 742fd9eeb1a2c020098ea01a32b6eecdb7cd92a5f08d1c82ebc8e0ad954fbf7f
- logs/sib/p4-purple/de/registration.json: f7bf013b74389a1de7dc5f4090bbcf94cc7b372fe24ef1595cc730e307bc2edb
- logs/sib/p4-purple/de/validation.json: 25018e932c09ac1fdfa82be255161a355f3ac7d604625c1463ddf6d460978aff
- logs/sib/p4-purple/de/overlap.json: 4a9575a83fe8c9aaf0c066bc24aa46746c6fa91efbcd9bd8f7d6d01e18af1372
- logs/sib/p4-purple/de/inventory.json: ff7c66b86d5b1dfa62dc485ba0f242e9971216434359167341d7b8bffe4f7f64
- logs/sib/p4-purple/de/sites.json: 985091177143919a4b029708007b63c4cda58b4fcf7321f3cbe5f4691ccad6fa
- logs/sib/p4-purple/de/labels.json: 8d1964ad72e29089829a97f94d5bd0e0f6f72c83d24e3b72555014010db6c209
- logs/sib/p4-purple/de/PROTOCOL.md: 4bc22d7aef1e3ea356e944cc144db2987ba87833fc0ce2fd7ab757a1e6f19cfe
