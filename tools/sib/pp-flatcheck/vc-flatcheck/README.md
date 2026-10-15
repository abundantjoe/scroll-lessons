# flatcheck

Checks tifxyz scroll-surface flattenings for distortion, fold-overs and collapse, and re-flattens with SLIM or ARAP.

## Why it matters

Letters are read from the flattened surface, so any stretch or shear in the flattening distorts the letter shapes and spacing. Vesuvius Challenge milestone prizes ask for "a low-distortion isometric 2D parametrization" of a segment, but there has been no standard, per-quad test for that in the tifxyz format. `flatcheck` supplies that test, together with a detector for the failure modes we measured on real segments:

* **Measurement:** the percentage of grid quads whose four edges keep their 3-D length within ±5 % after flattening, fold-overs (flipped triangles), and area and angle distortion.
* **Collapse detection:** the flattening shrank (or grew) and had to be globally rescaled, has fold-overs, or has undefined UV.
* **Explanation:** intrinsic curvature (discrete Gaussian curvature, as angle defects) shows how much distortion *no* flattening can remove from a region.
* **Repair:** re-flatten a region with SLIM (flip-free by construction) or ARAP.

It addresses the "detecting failure-cases of existing methods on real scroll data" criterion of the Progress Prizes. The findings below are failure cases of the official ABF++ flattener on public PHerc0139 segments.

## Install

```bash
git clone https://github.com/abundantjoe/flatcheck && cd flatcheck
pip install -e .            # numpy, tifffile, libigl==2.6.3
pip install pytest && pytest -q
```

Python >= 3.9. Tested on Linux x86-64 with Python 3.11, numpy 2.4, libigl 2.6.3 and tifffile 2026.3.

## Quick start (public data)

```bash
# Download one PHerc0139 surface mesh (x/y/z.tif + meta.json, 2.3 MB; no CT volume)
python scripts/fetch_segment.py PHerc0139 20260227000000-w052_2026022705 20250728140407-9.362um data_cache
M=data_cache/PHerc0139/20260227000000-w052_2026022705/20260227000000-on-20250728140407-9.362um.tifxyz

# The 3 most curved ~4 cm^2 windows, each scored for the grid itself, SLIM and ARAP
python -m flatcheck scan $M --voxel-um 9.362 -k 3
```

Expected output (Linux x86-64, 1 CPU, about 40 s):

```
rows      26:114 cols     327:458 | mean |defect| 1.023 deg | grid  68.78 % f0 | slim  86.92 % f0 | arap  86.44 % f10
rows     259:347 cols     209:340 | mean |defect| 0.791 deg | grid  87.98 % f0 | slim  95.89 % f0 | arap  95.81 % f0
rows      86:174 cols      13:144 | mean |defect| 0.726 deg | grid  79.61 % f0 | slim  89.81 % f0 | arap  90.09 % f0
```

`%` is the percentage of quads within ±5 %, and `f` is the number of fold-overs. The most curved window cannot reach 93.1 % with any of the three methods. ARAP folds over 10 triangles there, and SLIM folds none.

## CLI

All commands read a tifxyz directory: `x.tif`, `y.tif` and `z.tif` hold float32 voxel coordinates, -1 marks an invalid vertex, an optional `mask.tif` is honoured, and `meta.json` gives `scale`, so the grid step is `1/scale` voxels. `--rows a:b` and `--cols a:b` restrict any command to a window of grid vertices.

| command | what it does |
|---|---|
| `flatcheck report MESH` | Scores the flattening implied by the grid itself, (u, v) = (col, row) × step. This is the canvas a tifxyz render uses. |
| `flatcheck report MESH --uv U.tif V.tif [--rescale F]` | Scores an existing flattening, for example `vc_flatten` output. U and V are float TIFFs on the mesh grid, with -1 meaning undefined. `F` is the global rescale factor the flattener reported, if any, and is used by the collapse check. |
| `flatcheck report MESH --compare` | Scores the grid, SLIM and ARAP side by side. |
| `flatcheck flatten MESH --method slim\|arap --out DIR` | Writes `DIR/u.tif`, `DIR/v.tif` (float32, -1 = undefined) and `DIR/report.json`. |
| `flatcheck scan MESH --voxel-um V [--area-cm2 4 --aspect 1.5 \| --window H W] [-k 5]` | Finds the k non-overlapping, fully valid windows with the highest mean \|angle defect\| and scores each one. |

Common options: `--bar 93.1` sets the pass bar in % of quads within ±5 %, `--json FILE` writes the full result, and `--step` overrides the grid step. Exit codes: 0 on success; 1 with `report --strict` when any result fails the bar or collapses; 2 on a usage error.

`report --json` schema (all numbers are plain JSON numbers):

```
{mesh, window: {rows, cols}, grid_shape: [H, W], step_vox,
 curvature: {n_interior_vertices, sum_angle_defect_rad, mean_abs_angle_defect_deg, area_vox2},
 results: {<grid|slim|arap|given_uv>: {
    pct_quads_within_5pct, passes_bar, bar_pct, fold_overs,
    collapse: {flipped, undefined_uv, rescale_factor, rescale_out_of_range, collapsed},
    curvature: {...},
    metrics: {n_quads, n_triangles, n_triangles_uv_undefined, area_3d_vox2, area_scale_factor,
              pct_quads_within_5pct_norm, pct_quads_within_5pct_raw,
              pct_quads_within_{1,2,5,10}pct, edge_ratio_pctl, edge_abs_log_ratio_mean,
              flipped_triangles, degenerate_triangles, n_triangles_good,
              area_ratio: {weighted_mean_abs_log, pct_tri_within_5pct, p1, p50, p99},
              conformal_sigma_ratio: {weighted_mean, p50, p99},
              angle_abs_err_deg: {mean, p50, p99, max}, sym_dirichlet_area_weighted}}}}
```

`scan --json` returns `{mesh, step_vox, voxel_um, window_quads, bar_pct, windows: [{r0, c0, rows, cols, h_quads, w_quads, area_cm2, mean_abs_angle_defect_deg, results: {<method>: {pct_quads_within_5pct, fold_overs, collapsed, passes_bar}}}]}`.

## API

```python
import flatcheck as fc
points, meta = fc.read_tifxyz("segment.tifxyz")          # (H, W, 3) voxels, -1 invalid
uv, info = fc.flatten(points[100:200, 50:250], "slim")   # (H, W, 2), NaN undefined
rep = fc.report(points[100:200, 50:250], uv)             # metrics + collapse + curvature + pass/fail
fc.collapse_flags(fc.metrics(points, my_uv), rescale_factor=2.58)["collapsed"]   # True
fc.worst_windows(points, h=88, w=131, k=3)               # most curved windows
```

## The metric

The flat mesh uses the ABF++ triangulation of VC3D (two triangles per quad, split along the p10-p01 diagonal), so every method flattens the same triangles.

* **Main number:** the % of quads whose four edges all have flat length / 3-D length in [0.95, 1.05], after a single global area-matching factor s = sqrt(A3/A2). An arbitrary global scale is therefore not penalised. The raw value (s = 1) is reported too.
* **Undefined UV:** quads with undefined UV count as failing; they are never dropped.
* **Also reported:** per-triangle area ratio and angle error, singular-value ratio, symmetric Dirichlet energy, flipped and degenerate triangles, and the edge-ratio percentiles.
* **Collapse:** fold-overs > 0, any undefined UV, or a global rescale outside [1/1.5, 1.5].
* **Pass bar:** the default `--bar 93.1` is the reference value used in our study; set your own with `--bar`. It is a parameter, not a claim of this tool.

## Validation

**Tests:** `pytest -q` runs **21 tests, all passing**, on synthetic surfaces with known geometry:

* **Developable cylinder** (R = 300 voxels, 60 × 60 quads, grid at 0° and 30° to the generators): SLIM and ARAP give ≥ 99.9 % of quads within ±1 %, with 0 fold-overs and an area factor of 1 ± 0.002.
* **Sphere patches** (R = 1000, 3000 and 6000 voxels):
  * the angle defects sum to A/R² (Gauss-Bonnet) within 8 %;
  * the edge-ratio spread after SLIM or ARAP lies in [1/8, 1] of the analytic strain 1 − cos(L/2R);
  * distortion grows monotonically with curvature;
  * SLIM lowers the symmetric Dirichlet energy compared with the raw grid.
* **Metric sanity:** a global scale passes and an anisotropic stretch fails, undefined UV counts as failing, holes are excluded, and folds are detected.
* **Collapse detector:** rescale factors of 2.58 and 0.6 are flagged, and so are a shrunken map and a real fold.
* **Other:** `worst_windows` finds a Gaussian bump and skips holes, the tifxyz and UV round trips are exact, and the CLI runs end to end.

**Real data** (reproducible, geometry only): `bash scripts/reproduce.sh` downloads three public PHerc0139 meshes (about 7 MB) and writes `results/*.json` and `results/SUMMARY.md`, in about 2 min on 1 CPU. It runs a whole-mesh report of the grid flattening and the `scan` of the 3 most curved ≈ 4 cm² windows per mesh. A second run reproduced every number in table A exactly.

## Findings on real data

**A. In this repository** (`scripts/reproduce.sh`; PHerc0139, 9.362 µm meshes `<id>-on-20250728140407-9.362um.tifxyz`; windows of 88 × 131 quads, 3.79 to 3.98 cm², at the most curved places the scan finds, on the mesh as distributed):

| segment | window (rows, cols) | mean \|angle defect\| (deg) | grid % | SLIM % | ARAP % | fold-overs SLIM / ARAP |
|---|---|---|---|---|---|---|
| 20260227000000-w052_2026022705 | 26:114, 327:458 | 1.023 | 68.78 | 86.92 | 86.44 | 0 / 10 |
| 20260227000000-w052_2026022705 | 259:347, 209:340 | 0.791 | 87.98 | 95.89 | 95.81 | 0 / 0 |
| 20260227000000-w052_2026022705 | 86:174, 13:144 | 0.726 | 79.61 | 89.81 | 90.09 | 0 / 0 |
| 20260220000000-w053_2026022021 | 25:113, 323:454 | 1.264 | 75.17 | 82.77 | 83.94 | 0 / 1 |
| 20260220000000-w053_2026022021 | 239:327, 209:340 | 0.916 | 87.46 | 94.36 | 94.46 | 0 / 0 |
| 20260220000000-w053_2026022021 | 68:156, 12:143 | 0.669 | 86.96 | 92.12 | 92.49 | 0 / 0 |
| 20260306000001-w051_2026030600 | 27:115, 323:454 | 0.873 | 75.87 | 87.68 | 88.09 | 0 / 1 |
| 20260306000001-w051_2026030600 | 254:342, 200:331 | 0.715 | 87.67 | 97.01 | 97.19 | 0 / 0 |
| 20260306000001-w051_2026030600 | 43:131, 44:175 | 0.591 | 87.78 | 92.89 | 93.55 | 0 / 3 |

* **The distributed flattening fails whole-mesh:** the grid flattening of the three whole meshes (56.5 to 57.8 cm²) has 90.05 % (w052), 92.94 % (w053) and 91.83 % (w051) of quads within ±5 %, all below 93.1 %.
* **Re-flattening helps:** in 9/9 windows SLIM and ARAP improve on the grid's own flattening, by 5.1 to 18.1 points.
* **Curvature sets a ceiling:** in the most curved window of each mesh, no method reaches 93.1 %. The distortion there is intrinsic (angle defects of 0.87 to 1.26°) and cannot be flattened away.
* **SLIM is the safer choice:** SLIM never folds over, while ARAP folds over in 4 of the 9 windows (1 to 10 triangles).

**B. From our earlier study** (same metric and code, plus the official ABF++; not re-run by `scripts/reproduce.sh`, because the ABF++ side needs the VC3D build and the meshes were first levelled, rotated so that grid rows follow iso-z; evidence: `results/study_summary.json`, the per-case numbers and window positions, with the sha256 of the 9.362 µm and 8.64 µm input meshes):

* **Setup:** the official ABF++ is VC3D `vc::abfFlatten` with the `vc_flatten` defaults (ABF++ then LSCM, rescaled to the 3-D area). It was compared with SLIM and ARAP on identical triangles.
* **10 hard windows** (the 5 most curved and the 5 least isometric 4 cm² windows over 38 PHerc0139 meshes at 9.362 µm; segments `20260220000000-w053_2026022021`, `20260227000000-w052_2026022705`, `20260306000001-w051_2026030600`, `20260215000000-w024_2026021572`, `20260311000000-w023_202603112281`, `20260108000000-w041_2026010816` and `20250831000000-w040_2025083102`): windows reaching the 93.1 % bar: **ABF++ 0/10, SLIM 3/10, ARAP 4/10**, grid 0/10. SLIM and ARAP beat ABF++ in every one of the 10 windows, by 2.9 to 55.3 points.
* **SLIM vs ABF++ overall:** SLIM ≥ ABF++ in **33 of 33** comparisons:
  * 5 seeded 4 cm² windows at 9.362 µm and the same 5 at 2.399 µm;
  * 5 whole meshes;
  * the 10 hard windows above;
  * 8 small 1 cm² windows on PHerc0800 and PHerc1447 meshes (8.64 µm), where every method scores 100 % (ties).

  The largest gap is 70.2 points.
* **ABF++ collapse:** on the whole mesh `20250108000002-w027_2025010845` (PHerc0139, 9.362 µm) ABF++ gives 27.9 % of quads within ±5 %. Its LSCM stage shrank the map, which was then rescaled ×2.58, and it has 3 fold-overs; SLIM gives 98.1 % on the same mesh with 0 fold-overs. On hard windows of `20260227000000-w052_2026022705`, ABF++ gives 33.9 % (rescale ×3.36, 12 fold-overs) and 22.2 % (3 fold-overs). SLIM never collapsed. `flatcheck report --uv ... --rescale F` flags all three cases.
* **Gentle patches don't separate the methods:** on the 5 seeded windows all three methods pass (ABF++ 98.6 to 99.7 %, SLIM 99.6 to 100 %). The unflattened grid alone already scores 97.4 to 99.6 % there.

## Limitations

* **Curvature ceiling:** distortion caused by intrinsic curvature cannot be removed by any flattening. `flatcheck` measures it (`curvature`) but does not cut or segment the surface to lower it.
* **ABF++ is not bundled:** it needs the VC3D build. Score its output with `report --uv u.tif v.tif --rescale F`, where F is the "Scaling UVs by" value that `vc_flatten` logs. `vc_flatten --uv-only` in VC3D build 41701aa aborted on save in our tests (an OpenCV `imwrite` assertion on 2-channel UV). We called `vc::abfFlatten` directly instead.
* **Window positions:** `scan` works on the mesh as distributed. The earlier study (B) used levelled meshes, so its window positions differ from those in table A.
* **Runtime:** SLIM runs single-threaded, about 4 s per 4 cm² window at 9.362 µm and about 4 to 6 min at 2.4 µm (≈ 400 × 400 quads). On a whole 57 cm² mesh as distributed (≈ 160k quads, 9.362 µm), `report --compare` did not finish within 12 min in our test. Use windows (`--rows/--cols` or `scan`) for large meshes.
* **Nominal step:** the raw ±5 % number (`pct_quads_within_5pct_raw`) assumes the grid step is the intended flat spacing; the main (area-normalised) number and the area and angle numbers do not.
* **Pass bar:** the 93.1 % bar is a reference value, not a validated threshold for readability.

## Data and citation

The numbers in this README and in `results/` were computed from public PHerc0139 surface meshes (volume `20250728140407`, 9.362 µm) from the Vesuvius Challenge open-data bucket. The earlier study (B) also used PHerc0139 meshes at 2.399 µm and PHerc0800 and PHerc1447 meshes at 8.64 µm. Segments are named by their official IDs above; browse them in the Data Browser: https://scrollprize.org/data_browser. Please cite the dataset:

> Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.

https://scrollprize.org/data

No CT volume, surface volume or mesh is included in this repository. `scripts/fetch_segment.py` downloads meshes from the official bucket.

## Licences

* **Code:** MIT (`LICENSE`).
* **Results:** the files in `results/` are derived from Vesuvius Challenge data and licensed CC BY-NC 4.0 (`results/LICENSE-DATA.md`).
* **Dependencies:** libigl (Python bindings, `libigl` on PyPI) is MPL-2.0; numpy is BSD-3-Clause; tifffile is BSD-3-Clause.

## Credits

* **SLIM:** M. Rabinovich, R. Poranne, D. Panozzo, O. Sorkine-Hornung. "Scalable Locally Injective Mappings." ACM Transactions on Graphics 36(2), 2017.
* **ARAP parametrisation:** L. Liu, L. Zhang, Y. Xu, C. Gotsman, S. J. Gortler. "A Local/Global Approach to Mesh Parameterization." Computer Graphics Forum 27(5) (SGP), 2008.
* **ABF++ (compared against):** A. Sheffer, B. Lévy, M. Mogilnitsky, A. Bogomyakov. "ABF++: Fast and Robust Angle Based Flattening." ACM Transactions on Graphics 24(2), 2005.
* **libigl:** A. Jacobson, D. Panozzo, et al. libigl: a simple C++ geometry processing library, https://libigl.github.io (MPL-2.0). It provides the SLIM and ARAP solvers used here.
* **VC3D / `vc_flatten` and the tifxyz format:** Vesuvius Challenge, https://github.com/scrollprize/villa.

## AI assistance

Developed with the help of AI coding agents; all numbers are produced by the scripts and tests in this repository. The one exception is section B of the findings, which comes from our earlier study and is labelled with its evidence.

## Contributing

Issues and pull requests are welcome at https://github.com/abundantjoe/flatcheck/issues. Please include the segment ID, the voxel size and the `--json` output.
