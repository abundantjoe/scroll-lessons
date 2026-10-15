Provenance: Project HERCULES | owner the owner | [id removed]

# FLAT-1 report (sibling task flat1, geometry only)

STATUS: DONE

No image, rendered slice or ink map was produced or viewed. No volume voxels were read, only mesh coordinates and volume metadata.json. No PHerc0841 data was touched. The eligible-volume meshes (PHerc0800, PHerc1447) were used for geometry measurement only, at the orchestrator's request, with no training. Every run, failures included, is in `runs.jsonl`.

## 1. Answer

* **Pre-declared rule, primary set** (5 seeded PHerc0139 rectangles of 4.00 cm^2 on the 9.362 um organizer meshes): **vc_flatten (ABF++) is adopted.** It passes on 5/5 meshes (98.59 to 99.67 % of quads within +-5 %). SLIM (99.59 to 100 %) and ARAP (99.61 to 100 %) also pass 5/5. The fallback was not needed; it was computed anyway (section 6).
* **The primary set does not discriminate.** The unflattened levelled grid already scores 97.39 to 99.55 %. The orchestrator's objection is confirmed.
* **Hard set** (code-chosen most-curved / least-isometric 4 cm^2 windows over all 38 bank meshes): **no method reaches the rule.** vc_flatten passes 0/10 (22.2 to 92.8 %), SLIM 3/10 (77.5 to 97.6 %), ARAP 4/10 (77.4 to 97.7 %), and the grid baseline 0/10 (70.8 to 89.5 %). SLIM and ARAP beat vc_flatten in every hard case, by 2.9 to 55.3 points. vc_flatten flipped triangles in 2/10 cases (12 and 3). SLIM had 0 flips everywhere, by construction (flip-free start plus a barrier energy).
* **Robustness finding:** the official ABF++ can collapse when its LSCM stage shrinks the map. Whole mesh w027: 27.9 % within +-5 %, UVs rescaled x2.58, 3 flips. Hard window BANK_H2_w052: 22.2 %, 3 flips. Hard window BANK_H1_w052: 33.9 %, UVs rescaled x3.36, 12 flips. SLIM and ARAP never collapsed.
* **Recommendation for SG item 10:** flatten R's own mesh with **SLIM** (symmetric Dirichlet, started from the levelled grid). Report vc_flatten alongside it for comparison. On current evidence 93.1 % is reachable on gently curved papyrus and not reachable in crushed regions, whatever the method. The fallback trim cannot help there, because the distortion is inside R (section 6).

## 2. Method (all rules fixed in code before the data they apply to were flattened)

* Meshes: organizer tifxyz `<ts>-on-20250728140407-9.362um.tifxyz` from s3://vesuvius-challenge-open-data (anonymous). Every sha256 is in `selection*.json` / `hard_selection.json`. The voxel size comes from each volume's metadata.json (`scan.tomo.acquisition.detector.samplePixelSize`): 9.362 um (sha256 95917633..., equal to the catalogue), 2.399 um (c788219f...), and 8.64 um for 0800 and 1447.
* Levelling: `hercules.geometry.level_mesh.level_mesh(step_vox=20, method="median")`, one rotation per mesh. Angles 87.8 to 90.2 deg (the tracer rows were already near iso-z). MAD spread 2.8 to 3.7 deg. Iso-z tilt inside each rectangle 0.25 to 3.5 deg.
* Selection: `numpy.random.default_rng(20260925)` permutes the 38 sorted PHerc0139 segment folders (the flatboi title is excluded), and the first 5 with a feasible rectangle are taken. None were skipped: w059, w047, w038, w058, w027. Rectangle: aspect ~ U[1,2], origin uniform over fully valid positions (rng `[20260925, crc32(segment)]`), width adjusted to 4.00 cm^2 +-1 % of 3-D triangle area. Realised 3.988 to 4.033 cm^2, aspect 1.02 to 1.99.
* Triangulation: the one the official ABF++ uses (p10-p01 diagonal). All methods flatten the identical triangle set.
* **vc_flatten**: official villa 41701aa, built in the official deps image (sha-0c371b1d), vc_flatten binary sha256 bc0c7407.... `vc_flatten --uv-only` aborts when saving (OpenCV `imwrite` assertion on the 2-channel uv), so `tools/sib/flat1/abf_uv_dump.cpp` calls the unmodified official `vc::abfFlatten` with vc_flatten's default config (10 iterations, ABF++ then LSCM, scaled to 3-D area) and writes u/v float TIFFs (binary sha256 f07c4e2b...). Cross-check: the official CLI's default mode (a resampled flat tifxyz, scored against its nominal step) gives 98.71 to 99.53 % on the same 5 patches, against 98.59 to 99.67 % from the driver (`flat1_cli.json`).
* **SLIM**: libigl 2.6.3 (PyPI wheel; the same upstream libigl the official VC build fetches), symmetric Dirichlet, free boundary. Start: the levelled grid (u, v) x 20 vox, which is flip-free by construction. Stop when the relative energy decrease over 5 iterations is <= 1e-7 (max 200 iterations).
* **ARAP**: libigl, ELEMENTS energy, 200 iterations, one pinned vertex. The tutorial's with_dynamics=True does not move at voxel scale (measured max move 0.025 vox), so dynamics is off and a single pin removes only translation.
* Sensitivity: Tutte starts give the same SLIM/ARAP results to <= 0.02 points on all 10 primary and secondary patches. vc_flatten at 50 iterations is identical to 10 iterations (ABF converges in 2 to 6 iterations).
* Metric (`flatlib.evaluate`): % of quads whose 4 edges all have flat/3-D length in [0.95, 1.05], after one global area-matching factor s = sqrt(A3/A2); s = 1.0000 +- 0.0012 for every method here, and the raw value is also recorded. Quads with undefined UV count as failing. Also recorded: area ratio (area-weighted mean |log|, % of triangles within 5 %), angle error (deg), sigma1/sigma2, flipped and degenerate triangles, symmetric Dirichlet energy, and angle-defect curvature of the patch.

## 3. Primary results (9.362 um, 187 um quads; `flat1_summary.json`, `flat1_results.json`)

| mesh | method | quads within 5 % | within 1 % | raw 5 % | area x | |log area| (w) | area within 5 % (tri %) | angle err mean / p99 (deg) | sigma1/sigma2 p99 | flipped | undefined uv | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| w059 | vc_flatten | 99.30 | 60.39 | 99.30 | 1.0000 | 0.0178 | 94.69 | 0.081 / 0.481 | 1.0137 | 0 | 0 | 2.3 |
| w059 | slim | 99.89 | 74.95 | 99.89 | 1.0000 | 0.0077 | 99.71 | 0.263 / 1.263 | 1.0348 | 0 | 0 | 4.2 |
| w059 | arap | 99.89 | 74.77 | 99.89 | 1.0001 | 0.0078 | 99.69 | 0.263 / 1.262 | 1.0352 | 0 | 0 | 1.6 |
| w059 | grid_baseline | 98.87 | 57.81 | 98.88 | 1.0008 | 0.0118 | 98.17 | 0.403 / 2.031 | 1.0682 | 0 | 0 | 0.0 |
| w059 | vc_flatten_lscm_only | 52.84 | 7.76 | 52.84 | 1.0000 | 0.1051 | 28.21 | 0.100 / 0.605 | 1.0159 | 0 | 0 | 0.7 |
| w047 | vc_flatten | 99.67 | 64.45 | 99.67 | 1.0000 | 0.0160 | 95.90 | 0.073 / 0.431 | 1.0117 | 0 | 0 | 2.2 |
| w047 | slim | 100.00 | 78.78 | 100.00 | 1.0000 | 0.0069 | 99.99 | 0.235 / 1.031 | 1.0265 | 0 | 0 | 4.2 |
| w047 | arap | 100.00 | 78.70 | 100.00 | 1.0000 | 0.0068 | 99.99 | 0.234 / 1.028 | 1.0265 | 0 | 0 | 1.5 |
| w047 | grid_baseline | 99.00 | 47.12 | 99.03 | 1.0010 | 0.0115 | 98.76 | 0.420 / 1.890 | 1.0570 | 0 | 0 | 0.0 |
| w047 | vc_flatten_lscm_only | 44.81 | 6.78 | 44.81 | 1.0000 | 0.1228 | 22.19 | 0.096 / 0.505 | 1.0134 | 0 | 0 | 0.7 |
| w038 | vc_flatten | 98.59 | 58.93 | 98.59 | 1.0000 | 0.0193 | 93.33 | 0.087 / 0.637 | 1.0190 | 0 | 0 | 2.1 |
| w038 | slim | 99.59 | 75.27 | 99.59 | 1.0000 | 0.0078 | 99.27 | 0.267 / 1.387 | 1.0426 | 0 | 0 | 4.2 |
| w038 | arap | 99.61 | 75.24 | 99.61 | 1.0001 | 0.0078 | 99.30 | 0.268 / 1.401 | 1.0430 | 0 | 0 | 1.5 |
| w038 | grid_baseline | 98.27 | 59.34 | 98.32 | 1.0009 | 0.0111 | 97.96 | 0.371 / 1.929 | 1.0643 | 0 | 0 | 0.0 |
| w038 | vc_flatten_lscm_only | 15.74 | 2.70 | 15.74 | 1.0000 | 0.2915 | 8.81 | 0.140 / 0.728 | 1.0209 | 0 | 0 | 0.7 |
| w058 | vc_flatten | 99.32 | 64.75 | 99.32 | 1.0000 | 0.0163 | 96.19 | 0.071 / 0.420 | 1.0118 | 0 | 0 | 2.4 |
| w058 | slim | 99.97 | 77.09 | 99.97 | 1.0000 | 0.0070 | 99.77 | 0.240 / 1.027 | 1.0285 | 0 | 0 | 4.3 |
| w058 | arap | 99.97 | 77.01 | 99.97 | 1.0001 | 0.0070 | 99.80 | 0.240 / 1.027 | 1.0286 | 0 | 0 | 1.7 |
| w058 | grid_baseline | 99.55 | 57.04 | 99.32 | 0.9973 | 0.0103 | 98.57 | 0.387 / 1.429 | 1.0412 | 0 | 0 | 0.0 |
| w058 | vc_flatten_lscm_only | 50.36 | 7.83 | 50.36 | 1.0000 | 0.1059 | 27.44 | 0.094 / 0.492 | 1.0130 | 0 | 0 | 0.7 |
| w027 | vc_flatten | 98.99 | 49.63 | 98.99 | 1.0000 | 0.0229 | 90.26 | 0.079 / 0.495 | 1.0139 | 0 | 0 | 2.2 |
| w027 | slim | 99.87 | 70.20 | 99.87 | 1.0000 | 0.0084 | 99.38 | 0.291 / 1.465 | 1.0368 | 0 | 0 | 4.7 |
| w027 | arap | 99.87 | 69.98 | 99.87 | 1.0001 | 0.0084 | 99.39 | 0.292 / 1.471 | 1.0370 | 0 | 0 | 1.6 |
| w027 | grid_baseline | 97.39 | 26.56 | 97.59 | 1.0012 | 0.0201 | 95.03 | 0.637 / 2.614 | 1.0669 | 0 | 0 | 0.0 |
| w027 | vc_flatten_lscm_only | 65.59 | 11.74 | 65.59 | 1.0000 | 0.0929 | 34.82 | 0.096 / 0.625 | 1.0167 | 0 | 0 | 0.7 |

| mesh | quads (h x w) | area cm^2 | aspect | iso-z tilt deg | sum angle defect rad | mean abs defect deg | fallback R-only -> margin -> trimmed (% within 5 %) | trim rounds |
|---|---|---|---|---|---|---|---|---|
| w059 | 106 x 108 | 4.020 | 1.019 | 0.25 | 0.0755 | 0.189 | 99.89 -> 99.93 -> 99.90 | 3 |
| w047 | 86 x 132 | 3.988 | 1.535 | 3.50 | -0.0061 | 0.151 | 100.00 -> 100.00 -> 100.00 | 2 |
| w038 | 80 x 142 | 3.990 | 1.775 | 3.05 | 0.3806 | 0.182 | 99.59 -> 99.47 -> 99.52 | 3 |
| w058 | 83 x 139 | 4.023 | 1.675 | 0.98 | -0.4940 | 0.142 | 99.97 -> 99.97 -> 99.97 | 1 |
| w027 | 76 x 151 | 4.033 | 1.987 | 1.11 | 0.0581 | 0.158 | 99.87 -> 99.72 -> 99.74 | 3 |

LSCM-only (vc_flatten `--lscm-only` equivalent): 15.7 to 65.6 %. The angle-only map drifts in scale across the patch.

## 4. Secondary: 2.399 um organizer meshes, same 5 segments (48 um quads; `flat1_summary_2p4um.json`)

Declared before download: a resolution check, outside the adoption rule. Rectangles come from the same rule and per-segment seeds, so they sit at nearly the same relative positions. vc_flatten: 98.60 / 99.92 / 98.94 / 98.59 / **93.50** (passes 4/5 or 5/5, but w027 sits on the bar). SLIM: 99.29 / 100 / 99.73 / 99.92 / 99.12. ARAP: 99.29 / 100 / 99.77 / 99.92 / 99.13. Grid: 98.24 / 99.78 / 98.74 / 98.85 / 93.90. Full table:

| mesh | method | quads within 5 % | within 1 % | raw 5 % | area x | |log area| (w) | area within 5 % (tri %) | angle err mean / p99 (deg) | sigma1/sigma2 p99 | flipped | undefined uv | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| w059 | vc_flatten | 98.60 | 59.74 | 98.60 | 1.0000 | 0.0204 | 92.69 | 0.036 / 0.278 | 1.0091 | 0 | 0 | 96.7 |
| w059 | slim | 99.29 | 73.34 | 99.29 | 0.9999 | 0.0089 | 98.99 | 0.303 / 1.765 | 1.0550 | 0 | 0 | 420.1 |
| w059 | arap | 99.29 | 73.24 | 99.29 | 1.0001 | 0.0089 | 98.99 | 0.303 / 1.760 | 1.0547 | 0 | 0 | 38.4 |
| w059 | grid_baseline | 98.24 | 52.15 | 98.21 | 0.9995 | 0.0143 | 97.58 | 0.484 / 2.857 | 1.1001 | 0 | 0 | 0.0 |
| w059 | vc_flatten_lscm_only | 15.10 | 2.60 | 15.10 | 1.0000 | 0.5132 | 8.41 | 0.072 / 0.429 | 1.0129 | 0 | 0 | 18.1 |
| w047 | vc_flatten | 99.92 | 80.53 | 99.92 | 1.0000 | 0.0122 | 97.85 | 0.019 / 0.148 | 1.0045 | 0 | 0 | 69.7 |
| w047 | slim | 100.00 | 87.81 | 100.00 | 1.0000 | 0.0057 | 99.95 | 0.196 / 0.800 | 1.0217 | 0 | 0 | 237.3 |
| w047 | arap | 100.00 | 87.79 | 100.00 | 1.0000 | 0.0057 | 99.95 | 0.195 / 0.801 | 1.0217 | 0 | 0 | 36.2 |
| w047 | grid_baseline | 99.78 | 70.18 | 99.85 | 1.0045 | 0.0087 | 99.72 | 0.331 / 1.414 | 1.0423 | 0 | 0 | 0.0 |
| w047 | vc_flatten_lscm_only | 32.54 | 5.93 | 32.54 | 1.0000 | 0.1757 | 14.93 | 0.029 / 0.181 | 1.0053 | 0 | 0 | 17.5 |
| w038 | vc_flatten | 98.94 | 69.93 | 98.94 | 1.0000 | 0.0173 | 93.77 | 0.025 / 0.178 | 1.0052 | 0 | 0 | 68.9 |
| w038 | slim | 99.73 | 79.76 | 99.73 | 1.0000 | 0.0077 | 99.36 | 0.246 / 1.317 | 1.0436 | 0 | 0 | 201.5 |
| w038 | arap | 99.77 | 79.68 | 99.77 | 1.0001 | 0.0077 | 99.37 | 0.246 / 1.308 | 1.0431 | 0 | 0 | 36.1 |
| w038 | grid_baseline | 98.74 | 70.17 | 98.83 | 1.0022 | 0.0099 | 98.47 | 0.349 / 1.852 | 1.0615 | 0 | 0 | 0.0 |
| w038 | vc_flatten_lscm_only | 30.43 | 4.92 | 30.43 | 1.0000 | 0.1681 | 13.56 | 0.035 / 0.229 | 1.0064 | 0 | 0 | 17.8 |
| w058 | vc_flatten | 98.59 | 63.50 | 98.59 | 1.0000 | 0.0194 | 92.58 | 0.031 / 0.212 | 1.0062 | 0 | 0 | 81.4 |
| w058 | slim | 99.92 | 68.41 | 99.92 | 1.0000 | 0.0088 | 99.30 | 0.297 / 1.214 | 1.0329 | 0 | 0 | 273.5 |
| w058 | arap | 99.92 | 68.30 | 99.92 | 1.0001 | 0.0088 | 99.32 | 0.298 / 1.212 | 1.0329 | 0 | 0 | 36.3 |
| w058 | grid_baseline | 98.85 | 54.22 | 98.82 | 0.9995 | 0.0124 | 97.09 | 0.464 / 1.999 | 1.0553 | 0 | 0 | 0.0 |
| w058 | vc_flatten_lscm_only | 19.08 | 3.81 | 19.08 | 1.0000 | 0.2847 | 9.97 | 0.047 / 0.283 | 1.0074 | 0 | 0 | 18.9 |
| w027 | vc_flatten | 93.50 | 24.17 | 93.50 | 1.0000 | 0.0428 | 65.98 | 0.036 / 0.211 | 1.0060 | 0 | 0 | 76.9 |
| w027 | slim | 99.12 | 41.06 | 99.13 | 0.9999 | 0.0157 | 97.09 | 0.505 / 2.122 | 1.0564 | 0 | 0 | 388.2 |
| w027 | arap | 99.13 | 41.24 | 99.14 | 1.0002 | 0.0157 | 97.12 | 0.506 / 2.128 | 1.0569 | 0 | 0 | 35.9 |
| w027 | grid_baseline | 93.90 | 10.55 | 92.58 | 0.9960 | 0.0307 | 87.47 | 0.819 / 3.143 | 1.0892 | 0 | 0 | 0.0 |
| w027 | vc_flatten_lscm_only | 10.60 | 1.86 | 10.60 | 1.0000 | 0.4744 | 5.25 | 0.055 / 0.268 | 1.0069 | 0 | 0 | 16.3 |

## 5. Whole-mesh flattening (patch-size effect; `flat1_whole.json`)

Each whole levelled 9.362 um mesh is flattened at once (34 to 55 cm^2, 97k to 157k quads, one component). Figures are % within +-5 % over all quads / over R's quads:
vc_flatten w059 95.97/98.75, w047 94.88/99.78, w038 93.86/98.43, w058 94.47/99.25 (6 flips), **w027 27.90/46.55** (LSCM shrink, x2.58 rescale, 3 flips).
SLIM 97.78 to 98.62 / 98.86 to 100; ARAP 97.80 to 98.68 / 98.95 to 100; grid 96.22 to 97.38. With no flips.
Distortion grows with patch size. The team figure of 93.1 % is close to whole-segment ABF++ values, so it most likely refers to whole-segment flattening; that is an inference, not verified.

## 6. Fallback (R + 2 mm margin = 11 quads at 9.362 um / 42 quads at 2.399 um, SLIM, up to 3 rounds trimming margin quads outside +-5 %, never inside R)

Primary: R-only SLIM, then margin, then trimmed: w059 99.89 -> 99.93 -> 99.90; w047 100 -> 100 -> 100; w038 99.59 -> 99.47 -> 99.52; w058 99.97 -> 99.97 -> 99.97; w027 99.87 -> 99.72 -> 99.74. 2.399 um: 99.29 -> 99.25 -> 99.27; 100 -> 100 -> 100; 99.73 -> 99.22 -> 99.43; 99.92 -> 99.36 -> 99.58; 99.12 -> 99.16 -> 99.19. Hard set: fallback after trim is always within 1 point of R-only SLIM (for example w052 H2 77.48 -> 77.36). **The fallback never changes a verdict.** Distortion in R comes from R's own intrinsic curvature (angle defects), and trimming outside R cannot remove it.

## 7. Hard set (orchestrator request 19:11Z; `flat1_hard.py`, `flat1_hard_summary.json`, `hard_selection.json`)

Rules: every fully valid 4.00 cm^2 aspect-1.5 window of all 38 bank meshes is scored by H1 = mean |angle defect| (curvature) and H2 = grid non-isometry (% of quads failing +-5 % against the nominal step). Take the top 5 meshes per score. Amendment A1, recorded in the code before any eligible flattening: no eligible mesh fits a fully valid 4 cm^2 window (0800 meshes 0.35 to 2.3 cm^2, 1447 up to 7.3 cm^2 but irregular), so eligible windows fall back to the largest of 3/2/1 cm^2 that fits. All that fitted were 1 cm^2, so **they are not FLAT-1-size results.**

| case | area cm^2 | score | mean abs defect deg | vc_flatten | slim | arap | grid | fallback trimmed | flips ABF/SLIM/ARAP | ABF area x |
|---|---|---|---|---|---|---|---|---|---|---|
| BANK_H1_w053 | 3.97 | 0.882 | 0.885 | 75.99 | 84.98 | 85.98 | 76.94 | 84.95 | 0/0/1 | 1.000 |
| BANK_H1_w052 | 3.98 | 0.707 | 0.705 | 33.88 | 87.96 | 87.75 | 71.26 | 87.58 | 12/0/6 | 1.003 |
| BANK_H1_w051 | 3.97 | 0.641 | 0.644 | 81.30 | 88.03 | 88.28 | 75.77 | 87.77 | 0/0/0 | 1.000 |
| BANK_H1_w024 | 3.97 | 0.591 | 0.595 | 88.71 | 95.63 | 95.76 | 87.80 | 94.75 | 0/0/0 | 1.000 |
| BANK_H1_w023 | 3.96 | 0.554 | 0.557 | 92.75 | 97.56 | 97.74 | 89.47 | 97.42 | 0/0/0 | 1.000 |
| BANK_H2_w052 | 3.98 | 0.348 | 0.643 | 22.23 | 77.48 | 77.35 | 70.75 | 77.36 | 3/0/4 | 1.004 |
| BANK_H2_w051 | 3.96 | 0.282 | 0.618 | 69.68 | 83.01 | 85.67 | 75.10 | 82.20 | 0/0/1 | 1.000 |
| BANK_H2_w053 | 3.97 | 0.280 | 0.688 | 81.01 | 83.93 | 85.74 | 76.40 | 83.90 | 0/0/0 | 1.000 |
| BANK_H2_w041 | 3.98 | 0.212 | 0.424 | 85.77 | 93.68 | 93.68 | 81.51 | 93.11 | 0/0/0 | 1.000 |
| BANK_H2_w040 | 3.96 | 0.181 | 0.463 | 86.82 | 92.83 | 93.77 | 84.38 | 92.29 | 0/0/3 | 1.000 |
| ELIG_H1_PHerc0800_20251028222030 | 0.99 | 0.173 | 0.173 | 99.88 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H2_PHerc0800_20251028222030 | 0.99 | 0.000 | 0.156 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H1_PHerc1447_20250502182142 | 1.00 | 0.088 | 0.088 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H2_PHerc1447_20250502182142 | 1.00 | 0.000 | 0.086 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H1_PHerc1447_20250703025628 | 0.99 | 0.095 | 0.094 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H2_PHerc1447_20250703025628 | 1.00 | 0.000 | 0.077 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H1_PHerc1447_20250703034159 | 0.99 | 0.176 | 0.177 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |
| ELIG_H2_PHerc1447_20250703034159 | 0.99 | 0.000 | 0.130 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0/0/0 | 1.000 |

Pass counts (>= 93.1 %). BANK (10 windows): vc_flatten 0, SLIM 3, ARAP 4, grid 0, fallback 3. ELIGIBLE (8 windows, 1 cm^2): all methods 8/8. Those auto-grown organizer meshes are almost exactly isometric grids (H2 = 0) and small, so they test nothing hard.
The ABF log rescale factor of the hard runs reached 3.36 (w052 H1), with UVs shrunk before rescaling. Across cases, % within +-5 % falls monotonically with the patch's mean |angle defect| for every method: an intrinsic, curvature-caused limit.

## 8. Unit tests (`tests/sib_flat1_test_flatten.py`, 13 pass)

`PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python -m pytest -q tests/sib_flat1_test_flatten.py`
* Developable cylinder (R = 300 vox, 60 x 60 quads, grid at 0 deg and 30 deg to the generators, grid and Tutte starts): SLIM, ARAP and official ABF++ each give **>= 99.9 % of quads within +-1 %**. Measured 100 %, 0 flips.
* Doubly curved sphere patches (R = 6000, 3000, 1000 vox): angle defects sum to A/R^2 (Gauss-Bonnet, rel 8 %); the edge-ratio spread lies in [1/8, 1] of the analytic strain 1 - cos(L/2R); within-1 % is monotone in curvature and < 50 % at R = 1000; SLIM beats the raw grid. Metric sanity: scale normalisation, anisotropic stretch, undefined UV counted as failing, flip detection, deterministic rectangle rule, fallback never trims R.
* Repository suite: 591 passed (unchanged).

## 9. Failures and deviations (all in runs.jsonl)

1. `vc_flatten --uv-only` aborts on save (exit 134, OpenCV imwrite channel assertion); replaced by the driver in section 2.
2. The first `flat1_run.py all` failed after all 5 meshes were done: numpy int64 in the summary JSON. Fixed, and the summary was re-run from checkpoints; the numbers are unchanged.
3. libigl ARAP with dynamics does not move at voxel scale; replaced by one pinned vertex (section 2).
4. The dockerd started by this session died at 20:42Z. Every ABF run before that had exit 0 (checked in runs.jsonl). The first hard-set attempt then failed its first ABF call (exit 1) and was killed and discarded. dockerd was restarted, and the hard run now aborts on any ABF infrastructure failure instead of scoring it. Two other hard attempts failed before flattening (LZW TIFF needed imagecodecs, installed; `evaluate` crashed on an all-undefined UV, fixed to report 0 %).
5. `flatlib.evaluate` got an empty-set guard after the primary, 2.4 um and whole runs. The guard only affects the all-undefined path, so earlier numbers are unaffected. `flat1_run.py` got the variant switch and subset workers during the runs; the 9um code path is unchanged from commit d2c1ce5, which produced the primary results.
6. The 2.399 um run used 3 parallel workers (subset filter) for time. Each mesh was computed exactly once.

## 10. For the orchestrator to declare

See `proposals/FLAT1-RESULT.md`. In short: (a) record FLAT-1: vc_flatten adopted by the pre-declared rule on the primary set (5/5); (b) record the non-discrimination and the hard-set result (no method meets the bar at crushed or curved windows; SLIM/ARAP dominate vc_flatten); (c) decide whether SG-10 flattening uses SLIM instead (recommended: it scores >= vc_flatten in 33 of 33 comparisons, with 0 flips and no collapse); (d) note that eligible-volume organizer meshes are too small for a 4 cm^2 test.

Artifacts: tools/sib/flat1/ (flatlib.py, flat1_run.py, flat1_whole.py, flat1_cli.py, flat1_hard.py, abf_uv_dump.cpp, build_abf_uv_dump.sh, run_abf.sh, logrun.sh, table.py); logs/sib/flat1/*.json; runs.jsonl. Compute: about 5 CPU core-h; no GPU.

---

# FLAT-2 (orchestrator task 2026-09-26 00:38Z)

STATUS: DONE (FLAT-2). Geometry only: no prediction, render or CT pixel was read; no image was produced. Data: `p4_flat.json`, `flatpkg_timing.json`, runs in `runs.jsonl`.

## A. Official flattening of PHercParis4 segments (DECL-P4-2 item 7 support)

The delivered flattening is the organizer tifxyz `<ts>-on-20260411134726-2.4um.tifxyz`: its regular grid is the flat parameterisation, and the prediction canvas is that grid x 20 px (tile builders' grid.json). The metric is % of valid quads whose four 3-D edges lie within +-5 % of the nominal flat step, 20 vox ("raw"). "norm" applies one global area-matching factor. Voxel 2.4 um, from the volume metadata.json. "Folds" are triangles whose normal points against the 9 x 9 neighbourhood mean normal; a regular grid cannot flip in (u, v), so folds are its flip equivalent. The OBJ pair (_original/_flattened) was not used; the tifxyz is the delivered product.

| segment | quads | whole, raw | whole, norm | within 1 % | within 10 % | folds | read-eligible tiles | tiles >= 93.1 % (raw / norm) | tile % min / median / max | tiles with folds |
|---|---|---|---|---|---|---|---|---|---|---|
| w010-027 | 28.2 M | **84.30** | 84.63 | 19.15 | 95.54 | 1605 | 160 | 56 / 65 | 30.1 / 90.8 / 99.4 | 27 |
| w028-037 | 29.4 M | **86.46** | 86.47 | 11.71 | 96.77 | 2929 | 171 | 61 / 61 | 47.2 / 89.9 / 99.8 | 24 |

Tile grid: DECL-P4-2 item 2, with T = 8343 px (w010-027) and 8301 px (w028-037) from the builders' grid.json. A quad belongs to the tile that contains its centre. A tile is read-eligible if >= 50 % of its canvas pixels are mesh-valid. Per-tile numbers are in `p4_flat.json` (`tiles_official`).
**Most read-eligible tiles (65 % of w010-027, 64 % of w028-037) fail the 93.1 % bar on the official flattening.**

Our flattening of one seeded 4.00 cm^2 crop per segment (FLAT-1 rectangle rule, rng [20260926, crc32(segment)], on the official grid):

| segment | crop (quads, cm^2, tile) | official on crop | vc_flatten | SLIM | ARAP | flips | ABF rescale |
|---|---|---|---|---|---|---|---|
| w010-027 | 402 x 434, 3.96, tile (3, 5) | 92.48 | 94.15 | 97.72 | 97.83 | 0 / 0 / 0 | 0.992 |
| w028-037 | 336 x 516, 4.03, tile (7, 14) | 86.11 | 91.45 | 95.41 | 95.41 | 0 / 0 / 0 | 1.007 |

Local re-flattening gains +1.7 to +5.3 points (vc_flatten) and +5.2 to +9.3 points (SLIM) over the official flattening. vc_flatten still fails the bar on the w028-037 crop; SLIM and ARAP pass on both crops.

## B. Packaged module

* `tools/sib/flat1/flatpkg.py` provides:
  * `flatten(points, "vc_flatten" | "slim" | "arap")`;
  * `metrics()`, the FLAT-1 metric with flips, area and angle distortion;
  * `collapse_flags()`, which flags flips > 0, any undefined UV, or an ABF rescale outside [1/1.5, 1.5];
  * `write_package` / `read_package` (tifxyz mesh + u.tif / v.tif float32 + quads.npy + flat_record.json with sha256);
  * `verify_package()`, which recomputes the metric and requires exact JSON equality with the record plus every sha256.
* `tools/sib/flat1/p4_package.py` implements DECL-P4-2 item 7: crop the official tifxyz to tile +- 1 cm by the canvas rule, flatten with vc_flatten (plus SLIM as secondary), report tile and crop % against 93.1, write and verify packages. `p4_package.py <tifxyz> <T_px> <px_per_mm> <row> <col> <out> --voxel-um 2.4`.
* Tests: `tests/sib_flat1_test_pkg.py` (7), `tests/sib_flat1_test_p4pkg.py` (3, synthetic meshes, including the official ABF++ through docker) and `tests/sib_flat1_test_flatten.py` (13): **23 pass**. They cover the round trip, tampered UV (sha and metric both catch it), an edited record (the exact diff key is reported), the collapse detector, the crop-rule arithmetic, and the tile quad count.
* Timings per 4 cm^2 (flatten; package write + verify 0.1 to 2.6 s; all packages verified, none collapsed):

| resolution | grid | vc_flatten (3 CPU) | SLIM (1 thread) | ARAP (1 thread) |
|---|---|---|---|---|
| 9.362 um | 107 x 109 / 87 x 133 | 2.0 / 1.7 s | 3.7 / 3.7 s | 1.5 / 1.3 s |
| 2.399 um | 415 x 421 / 338 x 516 | 86 / 60 s | 344 / 212 s | 36 / 31 s |
| 2.4 um Paris 4 crops | 402 x 434 / 336 x 516 | 91 / 134 s | 286 / 383 s | 35 / 33 s |

* A P4 candidate package (tile +- 1 cm, about 4 x 4 cm, about 830 x 830 quads, about 4x a 4 cm^2 crop) should take about 6 to 10 min for vc_flatten and about 25 to 40 min for SLIM. These are estimates scaled from the table, not measured. Both fit the one-hour target.

## C. Failures and notes

* The container was reclaimed twice while jobs ran (idle between turns). Processes died and dockerd left a stale /var/run/docker.pid, which was removed on restart. p4_flat.py is resumable, and its results come from the completed run. **Lesson: keep the session active (a foreground wait) while jobs run.**
* No Paris 4 candidate image was produced, and none can be produced by this code.

## D. For the orchestrator

1. Record: the official PHercParis4 flattenings of w010-027 / w028-037 reach 84.30 / 86.46 % of quads within +-5 % overall, and 56 / 61 read-eligible tiles reach 93.1 % (raw).
2. Consequence for DECL-P4-2 item 7: a candidate's package must be re-flattened locally; the official flattening usually fails the bar. vc_flatten may still fail (91.45 % on the w028-037 crop), where SLIM passed (95.41 %). Consider allowing SLIM (FLAT-1 proposal) as the package flattening, with vc_flatten reported alongside.
