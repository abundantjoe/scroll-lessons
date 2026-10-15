Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz REPORT: P4-F dense / mineral-pigment channel on the Paris 4 inner strips (DECL-P4-6, -A1, -A2; DECL-P4-12 addendum)

Builder role only. No image, tile or CT pixel was opened, viewed or described. Everything below is numbers computed from level-0 CT bytes, and the PNG bytes were hashed, never read back. The protocols were pushed before any number existed: PROTOCOL.md (e65c967) and PROTOCOL_2p4.md (cbc67b4).

## Bottom line
- **0 DENSE-HOTSPOT tiles**, on E1 (1.129 um, 60 tiles), E2 (2.4 um, 160 tiles, including all 64 title-zone tiles c10-c17), and both known-text controls.
- **No dense signal is on-sheet and letter-scale anywhere.**
  - The brightest voxels are compact 3-D grains spread evenly in depth, not surface layers.
  - In every numeric respect the title strip looks like the known-text control.
- **Sensitivity.** Injection-recovery into real control CT says a Hg/Pb/Au pigment stroke would have been caught at far below 1 um thickness (>= 80 % recovery):
  - at 0.05-0.1 um under the ideal linear model;
  - at about 0.3 um on a conservative floor anchored to the control's own undetected carbon ink.
  - Such a stroke must be 0.4 mm wide and lie within +-14 um of the traced surface.
  - Cu pigments need about 0.5 um, Fe2O3 0.5-1 um and Egyptian blue about 2 um (model); the floors are about 1.3, 2.2 and 6 um.
  - Real painted layers are 5-30 um thick. A mineral-pigment title **on the traced surfaces of these tiles** is therefore ruled out at high sensitivity.
- **What remains open:**
  - organic red lakes and dyes, which carbonise and are invisible to every CT channel;
  - pigment on surfaces that are not traced, or where the mesh is off by more than 15 um;
  - rows and tiles outside the eligible sets.
- **K-edge lead (geometry only).** The 137 keV 2.4 um scan is registered and brackets the Au, Hg and Pb K-edges with the 78 keV scans. It covers a band along E2 row r3, including 14-27 % of each title-zone tile r3_c10..c17 (kedge_coverage_e2.json). A K-edge ratio test there is physically possible. It needs its own declaration; nothing was computed.

## 1. Thresholds (frozen before any tile)
| material | control used | T_mid | T_hi | file / commit |
|---|---|---|---|---|
| E1 (1.129 um) | 20260623142658-w028-037 1.129 um SV, 6 % whole-chunk sample, 3.43 G sheet voxels > 0 | 80 | 233 | thresholds.json a9eead1 |
| E2 (2.4 um) | 20260701183125-w028-037 2.4 um SV (p4-l2's sample, pushed first; adopted verbatim per PROTOCOL_2p4) | 93 | 203 | thresholds_2p4.json 39a2e1d |

My own 2.4 um sample (voxels > 0) gives T_hi = 203 and T_mid = 90 (physics_2p4.json). The T_hi is identical to p4-l2's.

## 2. Physics sanity (physics.json, physics_2p4.json; 6 % samples)
| | sheet p50/p99/p99.9/p99.99 | gap p50/p99/p99.9/p99.99 | saturated (=255) sheet voxels | saturated per-px sheet max | density > T_hi sheet vs gaps | strip f_in |
|---|---|---|---|---|---|---|
| control 1.129 | 80/169/233/255 | 65/167/234/255 | 0.030 % | 0.098 % | 0.00097 vs 0.00099 | 0.192 |
| E1 | 77/176/234/255 | 64/173/228/255 | 0.021 % | 0.086 % | 0.00099 vs 0.00085 | 0.220 |
| control 2.4 | 90/158/203/255 | 82/156/200/255 | 0.029 % | 0.064 % | 0.0010 vs 0.0009 | 0.214 |
| E2 | 88/161/199/255 | 79/160/194/255 | 0.020 % | 0.040 % | 0.0009 vs 0.0008 | 0.221 |

- **Depth profile.** The papyrus sits on the mesh: the mean grey peaks within ~15 um below the surface slice (82-88) and drops to 68-77 at +25-45 um.
- **The "gap" slabs are not air.** At +-(60-120) um they hold neighbouring papyrus (mean 70-83).
- **Consequence for f_in.** A depth-uniform bright population gives f_in = 13/67 = 0.19 (E1) or 13/65 = 0.20 (E2). Every strip sits at that value.
- **KS D, control vs title strip (voxel histograms; correlated voxels, so no p-value):**
  - sheet 0.022 (1.129 um) and 0.022 (2.4 um);
  - gaps 0.022 and 0.017;
  - per-px sheet maximum 0.076 and 0.056.

## 3. Numeric screen (screen.json, screen_2p4.json; full-coverage level 0)
| | tiles | control tile p99 of n_hi | tiles > p99 | their full-coverage f_in | DENSE-HOTSPOT | letter-scale comps (tiles) | largest component | median ridge width | 2-4 mm ACF peak median / max |
|---|---|---|---|---|---|---|---|---|---|
| control 1.129 | 64 | 1,895,795 | 1 (r2_c9) | 0.270 | 0 | 0 | 0.49 mm | 2.26 um (1 px) | 0.0008 / 0.0056 |
| E1 | 60 | same | 2 (r2_c10, r2_c14) | 0.277, 0.275 | **0** | 0 | 0.40 mm | 2.26 um | 0.0009 / 0.0047 |
| control 2.4 | 171 | 1,748,479 | 2 (r3_c9, r6_c11) | 0.330, 0.247 | 0 | 13 tiles, up to 3 each | 1.26 mm | 2.4 um (p90 4.3) | 0.0009 / 0.0073 |
| E2 | 160 | same | 1 (r7_c19) | 0.261 | **0** | 4 tiles, 1 each | 0.57 mm | 2.4 um | 0.0008 / 0.0066 |
| E2 title zone c10-c17 | 64 | same | 0 | - | **0** | 1 (r7_c10, 0.57 mm, f_in 0.20) | 0.57 mm | 2.4 um | 0.0008 / 0.0046 |

- **The DENSE-HOTSPOT bar (f_in >= 0.8) is never approached.** The maximum f_in of any tile is 0.41 (E1/E2 samples) and 0.61 (control).
- **KS on per-tile n_hi density:**
  - E1 vs control: D 0.21, p 0.11.
  - E2 vs control: D 0.18, p 0.006, because E2 is *less* dense in low rows. p4-l2 reported row-dependent medians.
- **KS on the ACF peak:** D 0.16, p 0.37 (E1) and D 0.14, p 0.08 (E2).
- **Rot-90 null.** It was recomputed on every tile: radial statistics are identical and directional peaks swap in all 455 tiles. n_hi, f_in and the radial ACF are rotation-invariant by construction, so this null cannot discriminate. The known-text control is the discriminating null, and the title strips are indistinguishable from it.
- **Labelled adjacency.** excl_a (union) flags are in screen_2p4.json per tile. They are reported, not excluding (DECL-P4-12 item 3). 48 of the 64 title-zone tiles are flagged.

## 4. Point-like vs layer-like (morph3d.json; 1000 whole 116-slice chunks per material; 26-connected components of voxels > T_hi)
| | components >= 64 vox | share of hi voxels in them | median lambda3/lambda2 | planar (< 0.1) | centroid within +-15 um | uniform expectation |
|---|---|---|---|---|---|---|
| control 1.129 | 2,919 | 88 % | 0.51 | 1.4 % | 11.0 % | 11.2 % |
| E1 | 4,158 | 82 % | 0.50 | 1.7 % | 13.7 % | 11.2 % |

- The bright material is compact grains: inclusions, mineral sand or ash, 87-99 % of which reach 255.
- It is neither planar nor concentrated at the surface, and E1 matches the control.
- No saturated layer-like population exists.

## 5. Pigment physics (pigments.json; NIST mass attenuation, mixture rule)
Carbonised papyrus is taken as C 0.70 / O 0.25 / H 0.05 at 0.8 g/cm3 (0.4 and 1.2 are in the file). Linear attenuation at 78 keV, in cm-1, with the ratio to papyrus in parentheses:
- Au 45.0 (328)
- HgS 17.1 (125)
- Pb3O4 21.0 (153)
- PbO 22.9 (167)
- CuO 4.3 (31)
- Egyptian blue 0.98 (7.2)
- Fe2O3 2.6 (19)
- soot carbon ink 0.29 (2.1)

Au, Hg and Pb have mass attenuation coefficients 2.3-2.6 cm2/g at 78 keV, which rise about 1.7x at 110 keV, above their K-edges.

The grey model is linear, anchored on the void mode (39 / 42) and the papyrus mode (109 / 112).

| pigment | t_min to exceed T_hi, ideal, 1.129 / 2.4 um | injection limit (recovery >= 0.8), sigma 0 / 1 vox: 1.129 um | same: 2.4 um | conservative floor (see caveat) |
|---|---|---|---|---|
| Au | 0.012 / 0.010 um | 0.02 / 0.05 | 0.01 / 0.05 | ~0.13 um |
| HgS | 0.032 / 0.025 | 0.05 / 0.1 | 0.05 / 0.1 | ~0.34 um |
| Pb3O4 / PbO | 0.026 / 0.021 | 0.05 / 0.1 | 0.02 / 0.05 | ~0.3 um |
| CuO | 0.13 / 0.10 | 0.2 / 0.5 | 0.1 / 0.5 | ~1.3 um |
| Egyptian blue | 0.65 / 0.51 | 1 / 2 | 0.5 / 2 | ~6 um |
| Fe2O3 | 0.22 / 0.17 | 0.5 / 1 | 0.2 / 0.5 | ~2.2 um |
| soot (carbon ink) | not reached / - | not detected up to 20 um | 10 / 20 | - |

**Injection-recovery setup (inject_C.json, inject_C2.json).**
- 20 real control regions per voxel size, each 3.5 or 3.7 mm square, >= 95 % mesh-valid and in present chunks.
- Glyph: H-like, 3 x 2 mm, 0.4 mm stroke.
- Layer: from the surface slice outward, with partial-volume fill.
- Blur: sigma 0 or 1 voxel.
- Detection: the screen's own letter-scale criterion.
- False positives without injection: 0 of 40 regions.
- At the limits, one injected letter adds 0.15-1.0 M hi voxels, the same order as the control's tile p99 minus its median (~1 M). A letter would therefore also lift n_hi.

**Caveat: the linear model is optimistic.**
- It predicts that 10-20 um of soot carbon ink would be detectable at 2.4 um. Yet the control's real carbon-ink text gives no letter-scale hi structure beyond grain clusters (sections 3-4).
- Real blur, phase retrieval, noise and reconstruction non-linearity therefore reduce contrast.
- The "conservative floor" column assumes, as a worst case, that anything with mu*t below that of a 20 um soot layer stays undetected.
- Even on that floor, Hg, Pb and Au layers need only ~0.1-0.3 um, which is 15-100x thinner than any painted layer.
- Fe2O3 and Egyptian blue are the weakest: floors of ~2 and ~6 um, still below typical paint thickness.
- These are model plus injection numbers, not physical phantoms.

## 6. Scan inventory (scans.json)
| volume | keV | pixel | date | registered to 20260411134726 | w010-027 coverage (E1 / E2 mesh points inside; non-zero) |
|---|---|---|---|---|---|
| 20260310170716 | 74 | 45.5 um | 2026-03-10 | yes (via canonical 20230205180739; landmark rms 66 canon vox ~0.5 mm) | 100 % / 100 %; 94-96 % |
| 20260310173927 | 110 | 45.5 um | 2026-03-10 | **no transform.json published** | - |
| 20260323153942 | 137 | 2.4 um | 2026-03-15 | yes (via canonical; rms 0.76 canon vox) | 4.7 % / 3.0 %; 78-79 % |
| 20260411134726 | 78 | 2.4 um | 2026-03-10/11 | reference | 100 % / 100 % |
| 20260608103018 | 78 | 1.129 um | 2026-03-15/16 (mosaic of 19) | yes (direct affine; rms 1.2 vox) | 71 % / 46 %; 98 % |

**K-edge-bracketing registered pairs (FLAG):**
- 137 keV (2.4 um) with 78 keV (2.4 um or 1.129 um): brackets Au 80.7, Hg 83.1 and Pb 88.0.
  - Overlap with the strip is the r3 band on E2 (r3_c0..c20, 12-49 % per tile), including the title zone r3_c10..c17 (14-27 %).
- 74 keV with 137 keV brackets the same edges, but only at 45.5 um.
- The 74/110 keV pair brackets them too but is not registered; 110 keV comes from the same session as 74 keV, 35 min later, so a registration is plausible but unpublished.

**Registration caveat.** Pairing through the canonical frame carries landmark residuals of ~6-20 um. A ratio map would need local refinement to better than the stroke width.

## 7. Outputs
- **f1/** (E1, 1068 px): 60 PNG tiles, manifest.json in the p4-tiles-b e1 format (png_sha256, valid_fraction, stats incl. frac_mesh_points_outside_1129_volume, n_hi). Valid fractions were recomputed and equal the source manifest on all 60 tiles.
- **E2 tiles** are p4-l2's (DECL-P4-12); none were built here.
- **Per-tile records:** stage_b_{C,E1,C2,E2}.jsonl, and stage_b_gap_*.jsonl for the full-coverage f_in.
- **Sub-sibling p4-highz-c2** ran C2 tiles 1-151. It stopped at its account usage limit. This session resumed tiles 152-171 from its pushed checkpoint (d85310a) with the same tool, and the tool resumes by (r, c).

## 8. Honest assessment
- This channel finds no evidence of a dense-pigment (Hg, Pb, Au, Cu, Fe) title on the traced recto surfaces of the Paris 4 inner strips, including the expected title zone c10-c17.
- The measured sensitivity makes "not seen" mean "absent above ~0.1-0.3 um for Hg, Pb or Au, and a few um for Cu, Fe or Egyptian blue", within +-15 um of these meshes.
- That does not rule out a red title:
  - an organic red (madder or other lakes) would be invisible;
  - a mineral title on an untraced winding (DECL-P4-7) or outside the scanned rows would be missed.
- The one physically distinct follow-up available is a declared 78/137 keV K-edge test on the E2 r3 band.

## Addendum A3 (2026-09-27): depth scope, offset sweeps (DECL-P4-6-A3/-A4) and the extended panel (DECL-P4-16 item 2)
**Scope correction.** The result above holds only for ink within +-15 um of the mesh (DECL-P4-6-A3). Both depth calibrations recorded STOP:
- p4-tiles-b 1.129 um (l3e/calib_1129.json): peak excess 1.12 robust SD.
- p4-depth 2.4 um (calib.json): z 1.94, candidate -31.2 um, 4 of 24 tiles consistent.

The declared STOP branch was therefore run on both strips: the unchanged screen at o = -60 .. +60 um in 15 um steps.
- The n_hi bar is the control tile percentile 100 (1 - 0.01/9) at each offset (Bonferroni).
- f_in is at full coverage for every tile above the bar.
- Protocol: PROTOCOL_dstar.md (463369e). Gap slices outside the surface volume are dropped and the rest rescaled, so at +-60 um only 4-5 of 26-27 slices remain on one side (disclosed per tile).

**E1 sweep (screen_dstar_E1.json).** 0 DENSE-HOTSPOT at all 9 offsets.
- Above the bar: r2_c10 at 0 um, and r2_c14 at 0, 15 and 30 um, with full-coverage f_in 0.28, 0.28, 0.23 and 0.18.
- Largest component: 0.40-0.41 mm at every offset. The control's is 0.46-0.67 mm.

**E2 sweep (screen_dstar_E2.json = screen_dstar.json).** 160 tiles, merged from p4-highz (c0-c8, c20), hzw1 (c9-c13, 17f8182) and hzw2 (c14-c19, fd74bfe).
- Merge checks: 0 duplicates, identical record keys, and offset-0 records equal to stage_b_E2 on all 160 tiles.
- **0 DENSE-HOTSPOT at every offset.**

| o (um) | n_hi bar | E2 tiles > bar (full f_in) | E2 max f_in | E2 largest comp | tiles with letter-scale comp: E2 / control C2 | control largest comp |
|---|---|---|---|---|---|---|
| -60 | 2,964,243 | - | 0.39 | 0.52 mm | 1 / 20 | 1.42 mm |
| -45 | 2,751,565 | - | 0.42 | 0.54 | 1 / 18 | 1.16 |
| -30 | 2,355,555 | - | 0.43 | 0.81 | 2 / 15 | 1.20 |
| -15 | 2,043,958 | r7_c19 (0.23) | 0.46 | 0.69 | 3 / 17 | 1.23 |
| 0 | 1,877,647 | r7_c19 (0.26) | 0.41 | 0.57 | 4 / 13 | 1.26 |
| 15 | 1,688,136 | r7_c19 (0.27) | 0.38 | 0.57 | 3 / 11 | 1.10 |
| 30 | 1,557,553 | r7_c18 (0.19), r7_c19 (0.27) | 0.39 | 0.56 | 3 / 10 | 1.09 |
| 45 | 1,686,295 | r7_c18 (0.23), r7_c19 (0.26) | 0.38 | 0.56 | 5 / 11 | 0.96 |
| 60 | 1,972,711 | r7_c18 (0.28), r7_c19 (0.22) | 0.43 | 0.57 | 4 / 12 | 1.00 |

**Title zone c10-c17 (64 tiles).**
- No tile is above the bar at any offset. Max f_in is 0.37-0.45, and there are 0 hotspots.
- Letter-scale components: one tile each at -30, -15 and 0 um. The largest component is 0.81 mm (at -30 um), within the control's range at every offset.

**Rot-90.** Radial statistics are identical on all tiles at all offsets (a structural identity; the known-text control is the discriminating null).

**Extended panel (panel_ext.json; control C2 only; NIST attenuation; densities marked as assumed).** Injection-recovery limits (>= 0.8, sigma 1 voxel) are nearly independent of offset from -60 to +60 um:

| class | limit |
|---|---|
| Au, PbO | 0.05 um |
| HgS, Pb3O4 | 0.05-0.1 um |
| orpiment, realgar | 0.5 um |
| CuO, Fe2O3 | 0.5 um |
| Egyptian blue | 2 um |
| Tyrian purple, Br intact | 2 um |
| Tyrian purple, 50 % Br loss | 2-5 um |
| Tyrian purple, 90 % Br loss | 10 um |
| purpurissum (on CaCO3) | 2 um |
| alumina and gypsum lakes | 5 um |
| soot carbon ink | 20 um or not detected |

- Conservative floors, scaled to the control's undetected 20 um carbon ink:
  - As ~2 um;
  - Tyrian purple ~6 um intact and ~18 um with 90 % Br lost;
  - purpurissum ~8 um;
  - lakes ~12-14 um.
- 0 false positives in 180 uninjected regions.

**Assessment (updated).**
- Between -60 and +60 um of both meshes, no mineral-pigment title is seen on either strip or in the title zone. The same holds for any carrier-laked or bromine-retaining purple with strokes >= 0.4 mm and layers above the limits above.
- Still untestable with this channel:
  - organic dyes without a mineral carrier;
  - Tyrian purple that has lost most of its Br and is thinner than ~10-18 um;
  - depths beyond +-60 um or untraced windings.
