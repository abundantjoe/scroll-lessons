Provenance: Project HERCULES | owner the owner | [id removed]

# regrescan: 9.362 um <-> 2.403 um CT-to-CT affine registration (PHerc1203, PHerc0846A)

STATUS: DONE

RESULT: PHerc1203 PASS; PHerc0846A FAIL (held-out median r 0.8439 < 0.85 with the specified fit iteration 1; RMS and control pass). Open questions are in ASK.md.

## Verdict (bars: held-out median r >= 0.85 AND RMS <= 1.5 vox on 16 NEW patches; control must drop clearly)

| Scroll | held-out median r | held-out RMS (9 um vox) | control median r | median drop | ctrl < aligned | fit RMS (24) | RESULT |
|---|---|---|---|---|---|---|---|
| PHerc1203 | 0.879 | 0.732 | 0.177 | 0.655 | 16/16 | 0.589 | **PASS** |
| PHerc0846A (fit iteration 2, refit; sha256 5dbe5d1f...) | 0.844 | 0.718 | 0.083 | 0.757 | 16/16 | 0.703 | **FAIL** |
| PHerc0846A (fit iteration 1, sha256 bcb9c43f..., as specified by the orchestrator) | 0.844 | 0.720 | 0.083 | 0.757 | 16/16 | 0.704 | **FAIL** |

Two 0846A rows: the pipeline ran fit -> refit (re-measure at the level-0 affine) -> check as one command, as for 1203, so the first check used fit iteration 2 (sha256 5dbe5d1f...), which was not committed before that check. The orchestrator then specified the committed iteration-1 fit (sha256 bcb9c43f...); that check was run once, on the same 16 pre-fixed patches with unchanged bars and control criterion. Both results are reported; neither was selected by outcome.

Archive reference (not used by the fit): 1203 band z 7936-11824, held-out r 0.964; 0846A band z 1856-5744, held-out r 0.946. Our held-out r is lower than the archive's; our r is plain Pearson over the whole 48x256x256 block including air/gaps (no mask, no filtering) at the fitted affine, so it is not directly comparable to an archive r of unknown definition.

## Model and affines

rescan voxel (x, y, z) = F * (p + t(p) - z0 e_z), t(p) = M (p - Pm) + b; p = 9 um level-0 voxel centre (x, y, z); F = samplePixelSize_9 / samplePixelSize_r from each metadata.json = 0.009362 / 0.002403 = 3.8959633791. No axis flip or permutation was found, so the raw rescan frame = canonical. Full 4x4 homogeneous matrices (both directions) are in `<scroll>/final_affine.json`.

### PHerc1203

- 9 um: `s3://vesuvius-challenge-open-data/PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/` (metadata sha256 092c709fb37b7248c2bbbbf8d0e1986cb2f690a4918860c2e4f19489fd807fd0)
- rescan: `s3://vesuvius-challenge-open-data/PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr/` (metadata sha256 1e8f0c743af88744da78c23175f96b152d392e67f825977bd1e88d9fee9e90d2)
- z0 = 7936; b = (20.312, -19.431, -1.838); Pm = (3367.5, 3431.5, 9879.5)
- M = [+0.000269 -0.000391 -0.000386; +0.000431 +0.000199 +0.001446; +0.000337 -0.001195 +0.000093]
- M decomposition: rotation vector (deg, x y z) = (-0.0757, -0.0207, +0.0235); z-axis tilt 0.0858 deg; trace(M) = +0.000561 (volumetric scale deviation)
- H (9 um xyz1 -> rescan raw xyz1) = [3.897010 -0.001523 -0.001505 95.706329; 0.001679 3.896740 0.005634 -139.684374; 0.001315 -0.004655 3.896327 -30917.574063]
- Band (9 um z covered by the rescan array): centre column 7938.0-11822.7; any column 7933.8-11826.9; all columns 7942.2-11818.5; rescan disc centre (x, y) = (3379.6, 3419.4), radius 3399.9 vox
- Held-out model comparison: translation-only RMS 2.899 vox (max 5.101) vs affine 0.732 vox

### PHerc0846A

- 9 um: `s3://vesuvius-challenge-open-data/PHerc0846A/volumes/20250728152254-9.362um-1.2m-113keV-masked.zarr/` (metadata sha256 0d0d7f3f30f76fd88623ee6357541600d901c54b455880d1cc752ac368d97d00)
- rescan: `s3://vesuvius-challenge-open-data/PHerc0846A/volumes/20260319102732-2.403um-0.2m-77keV-masked.zarr/` (metadata sha256 a6805a556a76715c5e533fbc44184e947d717dab4044006bce94e268fb208de0)
- z0 = 1856; b = (3.053, 4.573, -8.036); Pm = (3791.5, 3791.5, 3799.5)
- M = [+0.000655 -0.000469 -0.001960; +0.000458 +0.000619 -0.004442; +0.002058 +0.004420 +0.000062]
- M decomposition: rotation vector (deg, x y z) = (+0.2539, -0.1151, +0.0265); z-axis tilt 0.2782 deg; trace(M) = +0.001337 (volumetric scale deviation)
- H (9 um xyz1 -> rescan raw xyz1) = [3.898515 -0.001825 -0.007638 38.163308; 0.001784 3.898377 -0.017306 67.655624; 0.008017 0.017221 3.896206 -7358.828174]
- Band (9 um z covered by the rescan array): centre column 1864.2-5748.9; any column 1845.7-5767.4; all columns 1882.7-5730.4; rescan disc centre (x, y) = (3794.0, 3792.5), radius 3797.0 vox
- Held-out model comparison: translation-only RMS 9.422 vox (max 14.764) vs affine 0.718 vox

## 0846A tilt against the archive

| Source | rotation about x (deg) | rotation about y (deg) | rotation about z (deg) |
|---|---|---|---|
| Archive (remount tilt) | 0.26 | 0.12 | n/a |
| M, fit iteration 2 (antisymmetric part) | +0.254 | -0.115 | +0.027 |
| M, fit iteration 1 (antisymmetric part) | +0.254 | -0.115 | +0.027 |

Magnitudes agree with the archive to <= 0.01 deg (iteration 2: |x| 0.254, |y| 0.115); the archive gives no signs or axis convention, so only magnitudes are compared. z-axis tilt implied by M: 0.278 deg.

## Diagnostic only (does not change any verdict): r at each check patch's own optimum

Run after the check. Per check patch, the transform is offset by that patch's own measured residual, so r is the best any registration could reach on that block.

| Scroll | median r at the affine | median r at own optimum | patches >= 0.85 at own optimum |
|---|---|---|---|
| PHerc1203 | 0.8789 | 0.9022 | 16/16 |
| PHerc0846A | 0.8437 | 0.8784 | 10/16 |

Reading: for 0846A the per-patch optimum reaches median 0.878, so the r shortfall under the affine (0.844) is at least partly the mapping model (local non-affine misfit at sub-voxel residuals: residual RMS 0.72 vox), not only the scans' different contrast. A non-affine model would need its own pre-registration and NEW check patches (see ASK.md); nothing of that kind was run.

## Method and step results

1. **Flips and remounts first.** 9 um level 4 (149.8 um) and rescan level 5 (76.9 um, area-downsampled by F/2 onto the level-4 grid) streamed whole. Exhaustive search at ~600 um (bin 4): z flip x x mirror x in-plane rotation 0-358 deg in 2 deg steps (720 candidates; y flip = mirror + 180 deg), full 3-D translation, whole-volume NCC by FFT. Then rotation refined at ~300 um (0.5 deg, then 0.1 deg steps).
2. **Coarse z-band by whole-slice 3-D NCC** of the full rescan against every z placement of the 9 um volume (~300 um).
3. **Coarse tilt**: 3-D phase correlation of 18 sub-blocks (2 z x 3 x 3) at 150 um -> affine; both rotation sign conventions tried, better kept.
4. **Mid level**: 9 um level 1 vs rescan level 2 (F/2), 24 patches of 64x256x256 9 um voxels, 2 iterations -> affine.
5. **Level 0** (only at the patches): 48x256x256 9 um blocks vs the rescan area-integrated (exact box) onto the 9 um grid; 3-D phase correlation (sub-voxel, window-bias-corrected, c6.phase_correlate_3d) at 24 fit patches -> affine (3-sigma MAD rejection; none rejected); re-measured once at the new affine (refit).
6. **Check on 16 NEW patches** (patch list committed before any level-0 read; min distance to a fit patch in the table below): r = Pearson between the 9 um block and the resampled rescan at the fitted affine; residual = phase-correlation shift at the fitted affine; RMS = sqrt(mean |residual|^2) (3-D).
7. **Control**: the same block with the transform shifted by half the local sheet pitch along the local sheet normal. Normal = dominant structure-tensor eigenvector; pitch = first local maximum of the block autocorrelation along it. Criterion fixed before the check (in patches.json): median(r - r_ctrl) >= 0.20 and r_ctrl < r in >= 15/16.

| Scroll | remount best (600 um) | best NCC | best distinct alternative | refined rotation (deg) | z-band peak (9 um z of rescan top) | peak NCC | 2nd peak >4 bins | mid median r | mid RMS (L1 vox) | min check-fit dist (vox) |
|---|---|---|---|---|---|---|---|---|---|---|
| PHerc1203 | zflip=False mirror=False rot=0 | 0.9869 | zflip=False mirror=False rot=348: 0.9066 | 0.426 | 7936 | 0.9862 | 0.9568 | 0.939 | 0.252 | 664 |
| PHerc0846A | zflip=False mirror=False rot=0 | 0.9963 | zflip=False mirror=False rot=12: 0.8733 | 0.145 | 1856 | 0.9936 | 0.9387 | 0.892 | 0.297 | 693 |

The remount rotation from step 1 is not physical tilt: the fully fitted M at level 0 absorbs it (see M decomposition). The 300 um z-band profile is monotone on both sides of its single peak for both scrolls (no competing z placement).

## Per-patch held-out results (16 NEW check patches)

### PHerc1203

| # | centre (x, y, z) | r | r_ctrl | residual (x, y, z) vox | pitch vox | PC peak |
|---|---|---|---|---|---|---|
| 0 | (1728, 3576, 10956) | 0.856 | 0.062 | (+0.23, -0.05, -0.16) | 11.2 | 0.688 |
| 1 | (5132, 2544, 9492) | 0.825 | 0.181 | (-0.06, -0.14, +0.89) | 6.2 | 0.674 |
| 2 | (3644, 2928, 10482) | 0.896 | 0.058 | (-0.15, +0.04, -0.84) | 10.7 | 0.819 |
| 3 | (4902, 2370, 10634) | 0.889 | 0.459 | (-0.18, +0.04, +0.63) | 7.0 | 0.664 |
| 4 | (1568, 4702, 9896) | 0.864 | 0.010 | (-0.17, -0.14, +0.01) | 16.1 | 0.650 |
| 5 | (5404, 3104, 10106) | 0.885 | 0.219 | (+0.07, +0.14, +0.60) | 15.3 | 0.673 |
| 6 | (3276, 3594, 7994) | 0.880 | 0.061 | (+0.05, +0.69, +0.08) | 15.3 | 0.839 |
| 7 | (4546, 2034, 11762) | 0.715 | 0.174 | (-0.28, -0.11, +1.44) | 8.3 | 0.619 |
| 8 | (4092, 4304, 11722) | 0.898 | 0.067 | (-0.17, -0.31, -0.16) | 13.2 | 0.660 |
| 9 | (2920, 4722, 9630) | 0.844 | 0.126 | (+0.04, -0.11, -0.51) | 15.6 | 0.816 |
| 10 | (4014, 3568, 9130) | 0.965 | 0.482 | (-0.18, +0.13, -0.62) | 46.4 | 0.833 |
| 11 | (3578, 2534, 8566) | 0.885 | 0.031 | (+0.06, -0.15, -0.24) | 11.8 | 0.787 |
| 12 | (2400, 4922, 8064) | 0.915 | 0.354 | (+0.07, +0.04, -0.08) | 12.1 | 0.705 |
| 13 | (2744, 1840, 10388) | 0.878 | 0.306 | (+0.08, -0.08, +0.32) | 6.7 | 0.716 |
| 14 | (5400, 3152, 8002) | 0.843 | 0.209 | (+0.16, +0.09, +1.02) | 18.0 | 0.660 |
| 15 | (5406, 3392, 11490) | 0.864 | 0.431 | (-0.19, -0.08, +1.12) | 28.6 | 0.612 |

### PHerc0846A

| # | centre (x, y, z) | r | r_ctrl | residual (x, y, z) vox | pitch vox | PC peak |
|---|---|---|---|---|---|---|
| 0 | (2606, 5250, 2628) | 0.857 | 0.044 | (+0.39, +0.37, +0.02) | 12.0 | 0.746 |
| 1 | (5568, 4404, 1956) | 0.739 | 0.259 | (+0.24, +0.10, +0.13) | 8.1 | 0.503 |
| 2 | (3008, 5090, 1950) | 0.835 | 0.088 | (+0.59, +0.38, -0.16) | 17.9 | 0.725 |
| 3 | (1470, 4942, 5684) | 0.804 | 0.108 | (-0.26, -0.03, +1.23) | 15.3 | 0.595 |
| 4 | (5410, 2220, 5278) | 0.834 | 0.197 | (+0.08, -0.00, +0.74) | 8.0 | 0.630 |
| 5 | (5168, 3614, 4900) | 0.873 | 0.176 | (-0.11, +0.00, -0.39) | 6.7 | 0.741 |
| 6 | (4114, 4668, 1950) | 0.693 | 0.065 | (-0.53, +1.20, -0.16) | 15.3 | 0.645 |
| 7 | (1936, 5546, 2016) | 0.776 | 0.102 | (+0.27, +0.20, +0.54) | 9.9 | 0.562 |
| 8 | (1730, 4190, 4004) | 0.843 | 0.075 | (-0.03, +0.17, +0.00) | 11.3 | 0.659 |
| 9 | (4648, 3240, 5458) | 0.847 | 0.103 | (-0.19, +0.15, -0.83) | 12.0 | 0.758 |
| 10 | (3100, 3474, 5660) | 0.804 | 0.035 | (+0.36, +0.10, -1.00) | 8.3 | 0.842 |
| 11 | (3970, 5462, 2576) | 0.879 | 0.099 | (+0.29, +0.29, -0.15) | 8.6 | 0.794 |
| 12 | (2958, 5590, 5650) | 0.845 | 0.026 | (+0.04, +0.01, +0.48) | 12.2 | 0.646 |
| 13 | (2596, 5612, 3456) | 0.876 | 0.019 | (+0.35, +0.35, -0.22) | 9.8 | 0.724 |
| 14 | (5288, 4370, 3344) | 0.890 | -0.027 | (-0.03, +0.25, -0.31) | 10.0 | 0.756 |
| 15 | (3554, 2232, 4672) | 0.846 | 0.077 | (+0.10, -0.03, -0.31) | 8.6 | 0.686 |

Fit-patch tables (24 each, with residuals against the final affine) are in `<scroll>/final_affine.json` under `fit.patches`.

## Round-trip tests

`tests/sib_regrescan_test_roundtrip.py` (run: `source /opt/hv/bin/activate && PYTHONPATH=src pytest -q tests/sib_regrescan_test_roundtrip.py`): level-pyramid transform conversions exact (< 1e-8); 9 -> 2.4 -> 9 um round trip on the fitted affines of both scrolls: exact < 1e-6 vox and, with the rescan coordinate rounded to the nearest stored voxel, < 0.5 vox (5000 random band points each); synthetic flips; NCC-map vs brute force; template search with out-of-volume placement; pitch estimator on synthetic sheets. Result recorded in `tests_result.txt`:

```
.............................                                            [100%]
29 passed in 14.11s
round trip 9 -> 2.4 -> 9 um, 5000 random band points per scroll (seed 6):
PHerc1203: exact max 1.82e-12 vox; rounded-to-stored-voxel max 0.215 vox, median 0.127 vox (bar < 0.5)
PHerc0846A: exact max 1.82e-12 vox; rounded-to-stored-voxel max 0.214 vox, median 0.127 vox (bar < 0.5)
```

## Exact commands

```
# environment (fresh container): uv venv /opt/hv --python 3.11; uv pip install numpy scipy 'zarr<3' numcodecs pytest s3fs fsspec ...
# every stage via the logger (appends to logs/sib/regrescan/runs.jsonl):
export PYTHONPATH=src OMP_NUM_THREADS=4
for S in PHerc1203 PHerc0846A; do for STAGE in meta coarse patches mid fit refit check final; do
  tools/sib/regrescan/run.sh /opt/hv/bin/python tools/sib/regrescan/regrescan.py $STAGE $S; done; done
/opt/hv/bin/python tools/sib/regrescan/make_report.py
```

Data read: anonymous S3 only (`s3://vesuvius-challenge-open-data/`), 9 um levels 0, 1, 4 and rescan levels 0, 2, 5; level 0 only in the patch boxes (~9 GB of rescan level 0 per scroll per pass). sha256 of every metadata.json, .zattrs and level .zarray is in `<scroll>/meta.json`. Voxel sizes from metadata.json (`scan.tomo.acquisition.detector.samplePixelSize`).

## Failed or killed runs (from runs.jsonl)

25 runs logged; 4 did not exit 0:

| utc start | utc end | exit | command |
|---|---|---|---|
| 2026-09-25T18:35:27Z | 2026-09-25T18:48:56Z | 143 | `coarse PHerc1203` |
| 2026-09-25T18:49:39Z | 2026-09-25T18:58:27Z | 137 | `coarse PHerc1203` |
| 2026-09-25T18:58:27Z | 2026-09-25T19:01:01Z | 143 | `coarse PHerc0846A` |
| 2026-09-25T19:32:00Z | 2026-09-25T19:32:51Z | None | `fit PHerc1203` |

## Failures and deviations (all logged in runs.jsonl)

- Coarse run 1 (1203) killed by me to add FFT caching (exit 143); run 2 killed by the container OOM (exit 137) in a 150 um NCC-map rotation pass (>14 GB); replaced by a second 300 um pass at 0.1 deg steps (M is fitted fully downstream, so the coarse rotation only initialises).
- Coarse run 3 (0846A, exit 143) killed by me because it had started with the pre-fix code (it would have hit the same OOM).
- First level-0 fit run of 1203 killed after 4 patches (its runs.jsonl line is reconstructed from the surviving output log; exit code not recorded): the spectral-peak sheet-pitch estimator gave ~47 vox (low-frequency leakage). Replaced by the structure-tensor/autocorrelation estimator (median ~9 vox); stale rows deleted; no control number from the old estimator is used.
- The stage-position z0 prior in meta.json (1203: ~7965) is a hint only and was not used; it ignores zarr_export crops.
- The pyramid convention (level-k voxel centred at 2^k i + (2^k-1)/2) is assumed for the coarse and mid levels only; level 0 is exact and absorbs any bias.
- Flip handling on non-power-of-two shapes is approximate at coarse levels (not exercised: no flip was found).

## Integrity

CT only. No ink model was run on any volume. No image, slice or map was written or viewed; only numbers and hashes. No manual annotation; no training. No PHerc0841 data touched. No seals, keys or encrypted files touched.

## What the orchestrator needs to declare next

1. Accept or reject each scroll's registration against the C6 bars (table above) and record the affines by the sha256 of `<scroll>/final_affine.json` (1203 09d7caeb021d8ffc..., 0846A c7081081f1f257b3...).
2. Declare the T-RESCAN band extents per scroll (proposal in `proposals/DECL-REGRESCAN.md`), including the 128-vox exclusion rule for windows found with 2.4 um help.
3. Before any 2.4 um ink result exists (I11): commit each band's 9 um search order. Nothing here produced any ink output.

