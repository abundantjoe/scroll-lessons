# flatcheck

Checks whether a scroll-surface flattening is actually low-distortion, and re-flattens it when it is not.

Every Vesuvius Challenge milestone asks for "a tifxyz mesh ... already including a low-distortion isometric 2D parametrization". flatcheck measures that claim, per quad, on any tifxyz. It finds the region-dependent failure of the official ABF++ flattening (`vc_flatten`) and offers SLIM and ARAP re-flattenings that do better on the same data.

## What it does
- **`flatcheck report <tifxyz>`** scores a tifxyz as a flattening. Its regular grid *is* the flat map: every edge has flat length 1/scale. It reports:
  - % of quads whose four 3-D edges lie within +-5 % of the nominal step (raw, and after one global area-matching factor);
  - fold-overs, i.e. triangles whose normal opposes their 9 x 9 neighbourhood;
  - edge-deviation percentiles;
  - optional per-tile scores (`--tile N`).
- **`flatcheck flatten <tifxyz> --out DIR`** re-flattens the mesh or a crop (`--rect`, or a seeded 4.00 cm^2 rectangle with `--rect4cm2 VOXEL_UM`; `--level` rotates the grid so iso-z runs along rows). It uses:
  - **SLIM** (libigl, symmetric Dirichlet, free boundary, started from the grid itself, which is flip-free);
  - **ARAP** (libigl);
  - optionally the official **ABF++** (`vc_flatten`'s algorithm, through a small driver around the unmodified `vc::abfFlatten`; see `abf/`).

  For each method it reports:
  - the metric above on the method's UVs;
  - triangle area distortion and angle error;
  - flipped triangles;
  - a **collapse flag**: flips > 0, any undefined UV, or an ABF area rescale outside [1/1.5, 1.5].

  It writes a **flat package** per method: the mesh, `u.tif`/`v.tif` and a record with sha256.
- **`flatcheck verify <package>`** recomputes the metric from a package and fails unless it matches the record exactly.

Python API: `flatcheck.flatten`, `metrics`, `collapse_flags`, `grid_report`, `write_package`, `verify_package`.

## Install
```
pip install -e .            # numpy, scipy, tifffile, libigl
pip install -e '.[test,demo]'
pytest -q tests             # 22 pass; 1 skipped unless the ABF++ path is configured (23 pass with it)
```
The ABF++ path is optional. It needs the official volume-cartographer build (docker image `ghcr.io/scrollprize/vc3d-deps/linux`) and `FLATCHECK_ABF_CMD`; see `abf/README.md`.

## Validation (numbers from our study; every mesh is public Vesuvius Challenge open data)
Metric: % of quads whose four edges all lie within +-5 % of their 3-D length (after one global area factor). Bar used below: 93.1 %.

**1. Synthetic ground truth (unit tests).**
- A developable cylinder (R = 300 vox, 60 x 60 quads, grid at 0 or 30 deg to the generators) flattens with >= 99.9 % of quads within **+-1 %** by SLIM, ARAP and official ABF++. The measured value is 100 % with 0 flips, from both grid and Tutte starts.
- Doubly curved sphere patches (R = 6000, 3000, 1000 vox):
  - the angle defects match Gauss-Bonnet;
  - the residual edge strain lies within [1/8, 1] of the analytic 1 - cos(L/2R);
  - distortion grows monotonically with curvature.

**2. Gentle regions pass with every method.** Five seeded 4.00 cm^2 rectangles on PHerc0139 organizer meshes (volume 20250728140407, 9.362 um): segments w059 (20250223000000-w059_2025022312), w047 (20260206000001-w047_2026020613), w038 (20260306000000-w038_2026030608), w058 (20260210000000-w058_2026021020) and w027 (20250108000002-w027_2025010845).

| method | quads within +-5 % |
|---|---|
| ABF++ | 98.59-99.67 % |
| SLIM | 99.59-100 % |
| ARAP | 99.61-100 % |
| the unflattened levelled grid | 97.39-99.55 % |

On these regions the choice of method barely matters.

**3. Hard regions: ABF++ fails, SLIM/ARAP do better.** The 4 cm^2 windows with the highest mean |angle defect| (curvature) or the worst grid isometry, chosen by code over all 38 PHerc0139 segments:

| window (PHerc0139 segment, 9.362 um mesh) | rule | ABF++ (vc_flatten) | SLIM | ARAP | unflattened grid | flips ABF / SLIM / ARAP |
|---|---|---|---|---|---|---|
| 20260220000000-w053_2026022021 | curvature | 75.99 | 84.98 | 85.98 | 76.94 | 0 / 0 / 1 |
| 20260227000000-w052_2026022705 | curvature | 33.88 | 87.96 | 87.75 | 71.26 | 12 / 0 / 6 |
| 20260306000001-w051_2026030600 | curvature | 81.30 | 88.03 | 88.28 | 75.77 | 0 / 0 / 0 |
| 20260215000000-w024_2026021572 | curvature | 88.71 | 95.63 | 95.76 | 87.80 | 0 / 0 / 0 |
| 20260311000000-w023_202603112281 | curvature | 92.75 | 97.56 | 97.74 | 89.47 | 0 / 0 / 0 |
| 20260227000000-w052_2026022705 | non-isometry | 22.23 | 77.48 | 77.35 | 70.75 | 3 / 0 / 4 |
| 20260306000001-w051_2026030600 | non-isometry | 69.68 | 83.01 | 85.67 | 75.10 | 0 / 0 / 1 |
| 20260220000000-w053_2026022021 | non-isometry | 81.01 | 83.93 | 85.74 | 76.40 | 0 / 0 / 0 |
| 20260108000000-w041_2026010816 | non-isometry | 85.77 | 93.68 | 93.68 | 81.51 | 0 / 0 / 0 |
| 20250831000000-w040_2025083102 | non-isometry | 86.82 | 92.83 | 93.77 | 84.38 | 0 / 0 / 3 |

Passing (>= 93.1 %): **ABF++ 0/10, SLIM 3/10, ARAP 4/10, grid 0/10.**
- **ABF++ collapses on crushed papyrus.** On w052 its LSCM stage shrinks the map; the result is rescaled by x3.36, leaving 33.9 % / 22.2 % of quads within +-5 % and 12 / 3 flipped triangles.
- **SLIM beats or equals ABF++ in 33 of 33 comparisons** across the gentle set, the same meshes at 2.399 um (volume 20260102150214), whole-mesh flattening and the hard set. SLIM never flipped a triangle.
- **Whole-segment flattening.** Flattening each 34-55 cm^2 mesh at once gives 93.9-96.0 % for ABF++, except w027: **27.9 %**, a collapse with a x2.58 rescale and 3 flips. SLIM gives 97.8-98.6 %.
- **A 2 mm margin plus trimming outside the region never changed a verdict** (at most +-1 point). The remaining distortion is intrinsic curvature inside the region.

**4. Small eligible-volume meshes.** The PHerc0800 and PHerc1447 auto-grown organizer meshes (8.64 um) fit only 1 cm^2 fully valid windows. All methods score 100 % there, because these meshes are near-perfect isometric grids.

## Demo (public data, reproduces the numbers above)
```
python demo/run_demo.py [--abf]
```
It downloads 3 small organizer meshes anonymously and writes `demo/demo_result.json`. Reproduced results (committed):
- PHerc0139 w052, hard window: ABF++ 22.23 % (3 flips, collapsed) vs SLIM 77.48 % (0 flips) vs ARAP 77.35 %.
- A second w052 window: ABF++ 33.89 % (12 flips) vs SLIM 87.96 %.
- w059, a gentle window: ABF++ 99.30 %, SLIM 99.89 %.

## Known limits
- Flattening cost at 2.4 um: SLIM on 4 cm^2 (about 175k quads) takes 3.5-6 min single-threaded, ABF++ 1-2 min, ARAP about 30 s. For regions over 50 cm^2, flatten a subsampled grid and interpolate (UVs are bilinear inside coarse quads).
- The metric compares edge lengths. It does not detect a globally mirrored map; check handedness separately.
- Curvature limits every method: no flattening of a doubly curved patch can be isometric. Report the numbers; do not expect 100 %.
- libigl ARAP: the tutorial's `with_dynamics=True` does not move at voxel scale. flatcheck pins one vertex instead.

## Licence
MIT (see LICENSE). The ABF++ driver links the official ScrollPrize volume-cartographer library under its own licence.
