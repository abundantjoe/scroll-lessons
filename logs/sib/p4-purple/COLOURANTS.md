Provenance: Project HERCULES | owner the owner | [id removed]

# COLOURANTS: predicted CT detectability of purple, organic and mineral title inks on Paris 4 (DECL-P4-16 item 1)

Builder: p4-purple. Numbers only. No image, tile or CT voxel was opened or read for this table. The inputs are:
- the published reconstruction metadata of the two 2.4 um scans (sha256 below);
- p4-highz's pushed control statistics (noise and grey modes; not re-measured);
- xraylib 4.3.0.

Tool: tools/sib/p4-purple/colourants.py. Tables: tools/sib/p4-purple/colourants_md.py, rendered from colourants.json.

## Sources and inputs
- **Attenuation and refraction:** xraylib 4.3.0 (Schoonjans et al., Spectrochim. Acta B 66 (2011) 776; EPDL97 cross sections, anomalous scattering factors).
  - mu = rho x CS_Total_CP (photoelectric + Compton + Rayleigh).
  - delta = 1 - Refractive_Index_Re; beta = Refractive_Index_Im.
  - Mixtures use the mixture rule.
  - Cross-check: xraylib reproduces p4-highz's NIST XCOM values at 78 keV (HgS 17.1, PbO 22.8, Au 44.9 cm-1).
- **Scans (published metadata.json):**
  - 78 keV, 20260411134726 (sha256 881bf77f...): Paganin delta/beta 1000; unsharp mask coeff 4, sigma 1.2 px; propagation 0.22 m; GHBP; uint8 window [-0.04, 0.22].
  - 137 keV, 20260323153942 (sha256 26792eb8...): Paganin delta/beta 2000; unsharp mask coeff 5, sigma 2.5 px; 0.22 m; window [0.01, 0.16].
- **Grey calibration:** the float unit is taken as cm-1.
  - Check: the control void mode (grey 42) maps to 0.003 cm-1, which is ~0 as it must be.
  - The papyrus mode (112) maps to 0.074 cm-1, i.e. carbonised papyrus of 0.43 g/cm3 with composition C 0.70 / O 0.25 / H 0.05.
  - No other unit yields a physical density.
  - Hence 980.8 grey per cm-1 at 78 keV and 1700 at 137 keV.
- **Noise (p4-highz physics_2p4.json, control C2 = 20260701183125-w028-037, in-sheet slab):** p50 90, p99 158.
  - Gaussian-equivalent sigma = (158 - 90) / 2.326 = 29.2 grey.
  - It includes papyrus texture and grains, so the CNR is conservative per voxel.
  - The tail is heavier than Gaussian: p99.9 is 203 against 180.
- **Layer:** a deposit on the papyrus surface, displacing void.
  - Pigment or dye at volume fraction 0.5 in a carbonised binder (papyrus composition, 1.0 g/cm3). The solid layer is in the JSON.
  - Thicknesses 5, 10 and 20 um. System PSF sigma 1 voxel (0.5 and 1.5 voxel as a sensitivity range in the JSON).
- **Response model (linear TIE regime, 1-D along the sheet normal):**
  - mu_r(k) = [mu(k) + z k^2 delta(k)] / (1 + z c k^2) x U(k) x PSF(k), with c = (delta/beta)_assumed x lambda / 4 pi.
  - U is the published unsharp mask.
  - Voxel box average at 2.4 um. The peak is averaged over sub-voxel phases.
  - Self-tests pass: a delta/beta-matched material returns exactly the absorption slab; a thick layer returns mu.
- **Densities and stoichiometry:** listed per row in colourants.json (components, mass fractions, density, and the source or assumption for each).
  - Tyrian purple: 6,6'-dibromoindigo C16H8Br2N2O2 (Br 38.0 wt%) at an estimated 2.0 g/cm3. Br loss replaces Br by H at constant molar volume.
  - Purpurissum: 5 wt% dye on CaCO3 (dye fraction assumed). The carrier alone is also given.
  - Lakes: 10 wt% alizarin on Al(OH)3 or on gypsum.
  - Organic densities marked "assumed" have no crystal value.

### Table A. Optics of the paint layer (pigment volume fraction 0.5 in carbonised binder)

| colourant | class | layer rho g/cm3 | mu78 cm-1 | mu137 cm-1 | R = mu137/mu78 | delta78 (1e-8) | delta/beta 78 | mu78 / papyrus (rho 0.3 / 1.0) |
|---|---|---|---|---|---|---|---|---|
| Tyrian purple, 0 % Br loss | purple (Br) | 1.50 | 0.677 | 0.292 | 0.432 | 5.10 | 596 | 13.2 / 3.9 |
| Tyrian purple, 50 % Br loss | purple (Br) | 1.31 | 0.434 | 0.227 | 0.524 | 4.55 | 829 | 8.4 / 2.5 |
| Tyrian purple, 90 % Br loss | purple (Br) | 1.16 | 0.240 | 0.175 | 0.732 | 4.11 | 1354 | 4.7 / 1.4 |
| purpurissum (5 wt% Tyrian dye on CaCO3) | purple lake (Ca) | 1.82 | 0.445 | 0.284 | 0.639 | 6.30 | 1120 | 8.6 / 2.6 |
| purpurissum, dye fully lost (CaCO3 carrier only) | purple lake (Ca) | 1.85 | 0.430 | 0.284 | 0.662 | 6.41 | 1178 | 8.4 / 2.5 |
| alumina lake (10 wt% alizarin on Al(OH)3) | lake (Al) | 1.67 | 0.302 | 0.243 | 0.804 | 5.87 | 1534 | 5.9 / 1.8 |
| gypsum lake (10 wt% alizarin on CaSO4.2H2O) | lake (Ca,S) | 1.61 | 0.346 | 0.245 | 0.709 | 5.68 | 1297 | 6.7 / 2.0 |
| orchil / orcein (lichen purple) | organic dye | 1.20 | 0.206 | 0.174 | 0.849 | 4.29 | 1649 | 4.0 / 1.2 |
| kermes (kermesic acid) | organic dye | 1.30 | 0.221 | 0.187 | 0.846 | 4.60 | 1642 | 4.3 / 1.3 |
| madder (alizarin) | organic dye | 1.27 | 0.216 | 0.183 | 0.848 | 4.50 | 1648 | 4.2 / 1.3 |
| indigo | organic dye | 1.18 | 0.200 | 0.170 | 0.850 | 4.18 | 1652 | 3.9 / 1.2 |
| orpiment As2S3 | mineral (As) | 2.25 | 1.436 | 0.509 | 0.354 | 7.31 | 402 | 27.9 / 8.4 |
| realgar As4S4 | mineral (As) | 2.28 | 1.598 | 0.542 | 0.339 | 7.35 | 364 | 31.1 / 9.3 |
| lead white (hydrocerussite) | mineral (Pb) | 3.90 | 7.223 | 7.040 | 0.975 | 11.28 | 124 | 140.5 / 42.1 |
| verdigris (neutral, Cu acetate hydrate) | mineral (Cu) | 1.44 | 0.441 | 0.243 | 0.552 | 5.03 | 903 | 8.6 / 2.6 |
| malachite | mineral (Cu) | 2.50 | 1.165 | 0.487 | 0.418 | 8.33 | 566 | 22.6 / 6.8 |
| cinnabar HgS | mineral (Hg) | 4.55 | 8.636 | 8.513 | 0.986 | 12.89 | 118 | 167.9 / 50.4 |
| minium Pb3O4 | mineral (Pb) | 4.95 | 10.554 | 10.307 | 0.977 | 13.81 | 103 | 205.2 / 61.6 |
| red ochre (hematite Fe2O3) | mineral (Fe) | 3.13 | 1.380 | 0.590 | 0.428 | 10.33 | 592 | 26.8 / 8.1 |
| yellow ochre (goethite FeOOH) | mineral (Fe) | 2.63 | 1.070 | 0.484 | 0.452 | 8.84 | 653 | 20.8 / 6.2 |
| Egyptian blue CaCuSi4O10 | mineral (Cu,Ca) | 2.04 | 0.574 | 0.329 | 0.573 | 6.94 | 955 | 11.2 / 3.4 |
| gold | metal (Au) | 10.15 | 22.543 | 22.572 | 1.001 | 27.19 | 95 | 438.4 / 131.5 |
| carbon ink (soot) | carbon ink | 1.40 | 0.232 | 0.197 | 0.852 | 4.86 | 1657 | 4.5 / 1.4 |
| carbon ink + 2 wt% Pb (as PbO) | carbon ink (Pb) | 1.42 | 0.278 | 0.243 | 0.873 | 4.89 | 1390 | 5.4 / 1.6 |
| carbon ink + 10 wt% Pb (as PbO) | carbon ink (Pb) | 1.48 | 0.483 | 0.444 | 0.918 | 5.07 | 829 | 9.4 / 2.8 |

Carbonised papyrus (C 0.70 / O 0.25 / H 0.05): mu78 = 0.0514 / 0.0737 / 0.1714 cm-1 at 0.3 / 0.43 / 1.0 g/cm3; R = 0.849 at any density.

### Table B. Predicted peak voxel contrast of a deposit at 78 keV, 2.4 um (grey levels over void; noise sigma 29.2 grey)

| colourant | (i) absorption 5 / 10 / 20 um | (ii) Paganin 5 / 10 / 20 um | CNR (ii) 5 / 10 / 20 um | (ii) vs carbon ink, 10 um | t for CNR 3: (ii) / (i) um | saturates uint8 at 5 um |
|---|---|---|---|---|---|---|
| Tyrian purple, 0 % Br loss | 441 / 628 / 664 | 595 / 678 / 631 | 20.4 / 23.2 / 21.6 | 1.28 | 0.55 / 0.85 | yes |
| Tyrian purple, 50 % Br loss | 283 / 403 / 426 | 505 / 557 / 491 | 17.3 / 19.1 / 16.8 | 1.05 | 0.65 / 1.35 | yes |
| Tyrian purple, 90 % Br loss | 156 / 223 / 235 | 432 / 460 / 380 | 14.8 / 15.7 / 13.0 | 0.87 | 0.75 / 2.50 | yes |
| purpurissum (5 wt% Tyrian dye on CaCO3) | 290 / 413 / 436 | 675 / 727 / 615 | 23.1 / 24.9 / 21.0 | 1.37 | 0.50 / 1.30 | yes |
| purpurissum, dye fully lost (CaCO3 carrier only) | 280 / 399 / 422 | 683 / 733 / 616 | 23.4 / 25.1 / 21.1 | 1.39 | 0.50 / 1.35 | yes |
| alumina lake (10 wt% alizarin on Al(OH)3) | 197 / 281 / 296 | 611 / 646 / 526 | 20.9 / 22.1 / 18.0 | 1.22 | 0.55 / 1.95 | yes |
| gypsum lake (10 wt% alizarin on CaSO4.2H2O) | 226 / 321 / 339 | 600 / 640 / 531 | 20.5 / 21.9 / 18.2 | 1.21 | 0.55 / 1.70 | yes |
| orchil / orcein (lichen purple) | 134 / 191 / 202 | 445 / 468 / 378 | 15.2 / 16.0 / 12.9 | 0.88 | 0.75 / 2.95 | yes |
| kermes (kermesic acid) | 144 / 205 / 217 | 477 / 502 / 405 | 16.3 / 17.2 / 13.9 | 0.95 | 0.70 / 2.75 | yes |
| madder (alizarin) | 141 / 200 / 212 | 467 / 491 / 396 | 16.0 / 16.8 / 13.6 | 0.93 | 0.70 / 2.80 | yes |
| indigo | 130 / 185 / 196 | 433 / 455 / 368 | 14.8 / 15.6 / 12.6 | 0.86 | 0.75 / 3.05 | yes |
| orpiment As2S3 | 936 / 1333 / 1408 | 924 / 1103 / 1105 | 31.6 / 37.7 / 37.8 | 2.08 | 0.35 / 0.40 | yes |
| realgar As4S4 | 1042 / 1483 / 1567 | 953 / 1153 / 1179 | 32.6 / 39.4 / 40.3 | 2.18 | 0.35 / 0.35 | yes |
| lead white (hydrocerussite) | 4708 / 6704 / 7083 | 2195 / 3115 / 3906 | 75.1 / 106.5 / 133.6 | 5.89 | 0.15 / 0.05 | yes |
| verdigris (neutral, Cu acetate hydrate) | 287 / 409 / 432 | 552 / 605 / 527 | 18.9 / 20.7 / 18.0 | 1.14 | 0.60 / 1.30 | yes |
| malachite | 759 / 1081 / 1142 | 981 / 1124 / 1056 | 33.6 / 38.5 / 36.1 | 2.12 | 0.35 / 0.50 | yes |
| cinnabar HgS | 5629 / 8015 / 8469 | 2566 / 3667 / 4635 | 87.8 / 125.4 / 158.6 | 6.93 | 0.10 / 0.05 | yes |
| minium Pb3O4 | 6880 / 9796 / 10350 | 2949 / 4296 / 5553 | 100.9 / 146.9 / 189.9 | 8.12 | 0.10 / 0.05 | yes |
| red ochre (hematite Fe2O3) | 900 / 1281 / 1353 | 1207 / 1376 / 1282 | 41.3 / 47.1 / 43.9 | 2.60 | 0.25 / 0.40 | yes |
| yellow ochre (goethite FeOOH) | 698 / 993 / 1049 | 1015 / 1146 / 1050 | 34.7 / 39.2 / 35.9 | 2.17 | 0.30 / 0.50 | yes |
| Egyptian blue CaCuSi4O10 | 374 / 533 / 563 | 757 / 825 / 713 | 25.9 / 28.2 / 24.4 | 1.56 | 0.45 / 1.00 | yes |
| gold | 14695 / 20924 / 22108 | 6077 / 8955 / 11739 | 207.9 / 306.3 / 401.5 | 16.92 | 0.05 / 0.01 | yes |
| carbon ink (soot) | 151 / 215 / 227 | 503 / 529 / 427 | 17.2 / 18.1 / 14.6 | 1.00 | 0.65 / 2.60 | yes |
| carbon ink + 2 wt% Pb (as PbO) | 181 / 258 / 273 | 514 / 546 / 449 | 17.6 / 18.7 / 15.4 | 1.03 | 0.65 / 2.15 | yes |
| carbon ink + 10 wt% Pb (as PbO) | 315 / 449 / 474 | 562 / 621 / 547 | 19.2 / 21.2 / 18.7 | 1.17 | 0.60 / 1.20 | yes |

### Table C. Dual-energy signature, 10 um deposit on a 100 um carbonised papyrus column (rho 0.43)

| colourant | R (true) | Paganin peak ratio 137/78 | column ratio shift dR | CNR_DE per 0.2 mm patch (correlated-noise estimate; upper bound) | dR at 5 / 20 um |
|---|---|---|---|---|---|
| Tyrian purple, 0 % Br loss | 0.432 | 0.58 | -0.200 | -32.0 | -0.131 / -0.270 |
| Tyrian purple, 50 % Br loss | 0.524 | 0.61 | -0.120 | -14.9 | -0.074 / -0.176 |
| Tyrian purple, 90 % Br loss | 0.732 | 0.64 | -0.029 | -2.8 | -0.016 / -0.046 |
| purpurissum (5 wt% Tyrian dye on CaCO3) | 0.639 | 0.63 | -0.079 | -9.6 | -0.049 / -0.115 |
| purpurissum, dye fully lost (CaCO3 carrier only) | 0.662 | 0.63 | -0.069 | -8.2 | -0.042 / -0.101 |
| alumina lake (10 wt% alizarin on Al(OH)3) | 0.804 | 0.64 | -0.013 | -1.3 | -0.008 / -0.020 |
| gypsum lake (10 wt% alizarin on CaSO4.2H2O) | 0.709 | 0.64 | -0.045 | -4.8 | -0.027 / -0.068 |
| orchil / orcein (lichen purple) | 0.849 | 0.65 | +0.000 | +0.0 | +0.000 / +0.000 |
| kermes (kermesic acid) | 0.846 | 0.65 | -0.001 | -0.1 | -0.000 / -0.001 |
| madder (alizarin) | 0.848 | 0.65 | -0.000 | -0.0 | -0.000 / -0.000 |
| indigo | 0.850 | 0.65 | +0.000 | +0.0 | +0.000 / +0.000 |
| orpiment As2S3 | 0.354 | 0.54 | -0.327 | -89.8 | -0.244 / -0.393 |
| realgar As4S4 | 0.339 | 0.53 | -0.349 | -105.1 | -0.265 / -0.414 |
| lead white (hydrocerussite) | 0.975 | 1.04 | +0.114 | +79.8 | +0.105 / +0.120 |
| verdigris (neutral, Cu acetate hydrate) | 0.552 | 0.61 | -0.111 | -13.8 | -0.068 / -0.162 |
| malachite | 0.418 | 0.57 | -0.264 | -60.1 | -0.190 / -0.327 |
| cinnabar HgS | 0.986 | 1.05 | +0.126 | +102.9 | +0.117 / +0.131 |
| minium Pb3O4 | 0.977 | 1.06 | +0.119 | +117.8 | +0.112 / +0.123 |
| red ochre (hematite Fe2O3) | 0.428 | 0.58 | -0.275 | -70.3 | -0.204 / -0.332 |
| yellow ochre (goethite FeOOH) | 0.452 | 0.58 | -0.235 | -49.6 | -0.167 / -0.295 |
| Egyptian blue CaCuSi4O10 | 0.573 | 0.62 | -0.121 | -16.8 | -0.077 / -0.168 |
| gold | 1.001 | 1.10 | +0.148 | +294.0 | +0.143 / +0.150 |
| carbon ink (soot) | 0.852 | 0.65 | +0.001 | +0.1 | +0.000 / +0.001 |
| carbon ink + 2 wt% Pb (as PbO) | 0.873 | 0.66 | +0.007 | +0.6 | +0.004 / +0.010 |
| carbon ink + 10 wt% Pb (as PbO) | 0.918 | 0.72 | +0.028 | +3.2 | +0.017 / +0.039 |

## What the numbers say (with their limits)
1. **In the published 78 keV, 2.4 um Paganin volume, a written deposit is seen mainly through its electron density (delta), not its atomic number.**
   - With delta/beta = 1000 plus a 5x unsharp gain at high frequency, every light colourant gives a peak 0.9-1.4x that of an equally thick carbon-ink deposit. This covers the purples, the lakes, the organic dyes (orchil, kermes, madder, indigo), verdigris and Egyptian blue (Table B).
   - Only the As, Fe and Cu minerals (about 2-2.6x) and the Pb, Hg and Au pigments (6-17x) differ strongly.
   - The claim that "a purple title is invisible to CT" is therefore false for any deposit with thickness. It is as visible as the carbon-ink body text of the same thickness.
   - The deciding variable is deposit thickness and geometry, not colour. So a colour-agnostic deposit channel at the calibrated ink depth (P4-L3 at d*, DECL-P4-12-A3/-A4) covers a purple title exactly as well as it covers the body text, and no better.
2. **In a pure absorption reconstruction (i), composition matters more.**
   - Intact Tyrian purple gives 2.9x the contrast of carbon ink.
   - With 90 % Br loss it gives 1.0x.
   - Purpurissum and the Ca/Al lakes give 1.3-1.9x; organic dyes 0.9-1.0x.
   - The published volumes are Paganin-retrieved, so (ii) is the relevant row. (i) sets the composition-driven part that survives at low spatial frequency.
3. **The absolute numbers are optimistic, and the control contradicts them for carbon ink inside the +-15 um slab.**
   - The model predicts that a 5 um carbon-ink paint layer saturates the uint8 range.
   - On the known-text control, however, only 0.064 % of per-pixel sheet-slab maxima are saturated (p4-highz). The text covers roughly 10 % of the area, which would give about 10 %.
   - So within +-15 um of the mesh, the real carbon-ink deposits are much thinner, less dense or sparser than a 5 um paint layer, or they lie outside the slab. The second possibility is the d* hypothesis of DECL-P4-12-A3; p4-depth's calibration will decide it.
   - Until then, the absolute CNRs and the detection limits (0.5-0.75 um for purple and organic deposits, CNR 3 per voxel) are **ideal upper bounds**.
   - The robust quantity is the ratio to carbon ink at equal thickness (Table B). Composition-independent unknowns (depth, porosity, PSF) scale colourant and ink alike.
   - That ratio still assumes equal thickness. A dye wash that soaks into the fibres, as opposed to a pigment or carbon deposit, may leave far less material. That case is not predictable from tables.
4. **Composition is identified only by dual energy, and only through depth-integrated values.**
   - The true ratio R = mu137/mu78 separates the classes:
     - papyrus, carbon ink and organics: 0.85;
     - gypsum and alumina lakes: 0.71 / 0.80;
     - purpurissum or CaCO3: 0.64-0.66;
     - Egyptian blue: 0.57;
     - Tyrian purple: 0.43 / 0.52 / 0.73 at 0 / 50 / 90 % Br loss;
     - Fe and Cu minerals: 0.42-0.55;
     - As: 0.34;
     - Pb, Hg, Au: 0.98-1.00, with their K-edges between the two energies.
   - Peak values in the two Paganin volumes do **not** carry R. Thin layers are delta-dominated, and delta scales as E^-2 for every material. The peak ratio is 0.53-0.65 for all light classes (Table C).
   - The retrieval chain has unit gain at zero frequency, so the **depth-integrated column** (a window of at least about 3 Paganin lengths, 17 um at 78 keV and 18 um at 137 keV, across the whole sheet) carries the true mu x t at both energies.
   - This is the design rule passed to p4-purple-de. It also makes the ratio insensitive to registration error along the normal, provided the window encloses the sheet.
5. **Dual-energy sensitivity (Table C; noise at 137 keV not measured, assumed equal in grey; correlated-noise estimate still an upper bound):**
   - 10 um of intact Tyrian purple shifts the column ratio by -0.20 (CNR about 32 per 0.2 mm patch).
   - With 50 % Br loss: -0.12 (about 15). With 90 % Br loss: -0.03 (about 3).
   - Purpurissum: -0.08 (about 10). Gypsum lake: -0.045 (about 5). Alumina lake: -0.013 (about 1).
   - Organic dyes and carbon ink: 0.000 (**undetectable by composition**). Carbon ink with 10 % Pb: +0.03 (about 3).
   - The real null is the control's own spread of the column ratio: papyrus carbonisation state, mineral grains and ash (Ca, Si, Fe). It must be measured on the control before any use (p4-purple-de, DUAL_FREEZE).
   - Coverage is limited to the E2 r3 band: 14-27 % of r3_c10-c17 (p4-highz).
6. **Not modelled:**
   - lateral letter edges (3-D);
   - scatter;
   - chemical change during carbonisation, other than Br loss and the dehydration notes in the JSON;
   - dye loss by sublimation (dibromoindigo sublimes or decomposes near 390 C);
   - the fraction of dye retained on its carrier.
   - The Paganin model is linear. mu x t stays below 0.1 for every row except the thickest Pb/Hg/Au layers, which are detectable anyway.

## Validation still owed (measurable)
- Carbon-ink anchor: once d* is frozen, the measured deposit contrast of the known text at d* (p4-depth, control only) replaces the model's carbon-ink row. Every colourant's expected contrast is then that measured value x the Table B ratio.
- Dual energy: the empirical control spread of the column ratio, and injection-recovery of each class through the registered pair (p4-purple-de).
- Injection limits for the Br, Ca, Al/S and As classes in the P4-F panel: DECL-P4-16 item 2, p4-highz. The mu values here are theirs to use.

## Empirical update (2026-09-27, p4-purple-de, DUAL_FREEZE.md 6d12337)
The dual-energy CNR in Table C is superseded by the control measurement. The real control spread of the column ratio (FPR 0.022 at |z| > 3.07 per 0.2 mm patch) and the 137 keV calibration failure (void 0.044, gain ~0.63, empirical papyrus line k 0.679) make the method insensitive where the model was optimistic. In injection-recovery (recovery >= 0.8):
- Tyrian purple (0 / 50 / 90 % Br loss) is NOT detected at <= 20 um; the best case is 0.24-0.29 at 20 um with 0 % loss.
- Purpurissum (0.00), the lakes and carbon ink are NOT detected.
- Only CuO, orpiment and gold are detected, at 10-20 um.
The Table C "upper bound" wording was correct, but the bound is far from reality: the noise model (independent photon noise only) omitted papyrus composition variability and calibration error.
