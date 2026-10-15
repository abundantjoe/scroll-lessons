Provenance: Project HERCULES | owner the owner | [id removed]

# reg0841: PHerc0841 9.366 um <-> 2.403 um registration (CT only)

STATUS: DONE

Builder report from a sibling compute session. Only numbers appear here: no image, slice or ink map was viewed, rendered or produced, and no ink model was run.
Machine-readable: `reg0841_summary.json`, plus the per-step JSON files in this folder. Every run is logged in `runs.jsonl` (UTC, command, exit code, output sha256).

## Verdict
Pre-registered bars on the 16 held-out patches (`prereg_heldout.md`, committed before any held-out analysis), using the task's affine model:

| Bar | Value | Result |
|---|---|---|
| held-out median r >= 0.85 | 0.724 (min 0.504) | **FAIL** |
| held-out RMS residual <= 1.5 vox, 9 um vox | 1.92 (max 3.38) | **FAIL** |
| same bar in rescan vox | 7.47 | **FAIL** |
| shifted control (half local pitch) drops NCC clearly: median drop >= 0.30 and >= 14/16 patches with r_ctrl < r - 0.15 | median drop 0.405; 16/16 | **PASS** |

The failure comes from the mapping model, not from the data or the measurement:
- **Measurement.** Per-patch phase-correlation correspondences repeat to < 0.25 vox between two independent passes (22 of 24 fit patches; the other two 0.48 and 0.84).
- **Data.** The NCC reaches a median of 0.881 on the held-out patches once each patch gets its own local shift. That is above 0.85.
- **Model.** No single affine maps the two scans to better than about 1.6-1.9 vox. The deformation between the scans is smooth but non-affine. Its dominant term: the rescan sits about 2-3.4 vox (9 um) lower in z near the scroll centre than at the periphery (e.g. P18 dz -2.71, P37 -3.37; fit P25/P27/P29 about -2). There are also quadratic in-plane terms.

## Volumes and voxel sizes (from each metadata.json)
- 9 um: `PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr`, samplePixelSize 0.009366 mm, L0 shape (z, y, x) 19400 x 7703 x 7703.
- Rescan: `PHerc0841/volumes/20260319124803-2.403um-0.2m-77keV-masked.zarr`, samplePixelSize 0.002403 mm, L0 15121 x 30469 x 30469. The scanRadix names sample "PHerc_0841_B"; the 9 um scan names "PHerc_0841". This may mean a separate mount (an inference from the names only).
- F = 9.366 / 2.403 = 3.897627965. uint8, 128^3 chunks, no compressor.
- The pyramid is an exact 2x2x2 mean (rounded; MAE 0 against level 1, `pyr_check.json`). Level-L voxel i therefore sits at level-0 coordinate i 2^L + (2^L - 1)/2.
- All 15,738 chunks read are sha256-logged in `chunk_sha256.jsonl.gz`. Metadata and mesh hashes: `volume_meta_sha256.txt`, `mesh_sha256.txt`.

## Steps and numbers
1. **Flips and remounts** (`coarse.py 1`, 9 um L4 vs rescan L5, 9 slices). For each of 8 orientation candidates: the best whole-slice NCC over a full z scan, plus a 2-D phase-correlation xy refinement. Median NCC: I 0.825, Rz90 0.091, Rz180 0.058, Rz270 0.058, flipX 0.075, flipY 0.093, flipZ 0.76, Rx180 0.1. IQR of the implied dz: I 0, Rz90 5088, Rz180 7648, Rz270 4480, flipX 5216, flipY 3168, flipZ 3200, Rx180 14112.
   - Only the identity is both high and z-consistent. flipZ matches single slices but scatters in dz by 3200 vox.
   - No flip, no 90/180 degree remount rotation. The mesh affine has det > 0 and a 0.17 degree rotation about z.
2. **Coarse fit from the organizer meshes** (`mesh_fit.py`). The UV-corresponding nodes of the `-on-20250821151531` and `-on-20260319124803` tifxyz of all 3 segments give 105,024 pairs, with canvas offset o = 10 best for every segment. Robust affine residual: median 0.43 and RMS 0.55 rescan vox (86.5 % kept).
   - Caveat: the organizer 2.4 um meshes are therefore an affine image of the 9 um meshes. This is the organizer's own transform, not independent CT evidence.
3. **z band by whole-slice NCC** (`coarse.py 3`). 24 rescan L4 slices, each scanned over dz in [-400, 400] 9 um vox against the 9 um L3 band, refined at 0.5 vox.
   - Peak dz is within +-1 vox of the mesh affine for 23 slices, and -2.5 at the top edge slice.
   - NCC peak 0.72-0.82, peak minus the best sidelobe (|dz| > 40) 0.42-0.54.
   - Linear fit: rescan z = 0 -> 9 um z 12790.6, and rescan z = 15120 -> 16669.3.
4. **3-D phase correlation** (`fit_run.py`). 24 fit patches of 48 x 256 x 256 (9 um L0) with the rescan at L0. The rescan is Gaussian-prefiltered (sigma F/2 rescan vox) and trilinearly sampled on the 9 um grid. The shift is found by iterative phase correlation with a Hann window and a parabolic sub-voxel peak. Two passes: mesh affine -> fitted affine -> refit.
   - Pass 1 changed the mapping by an RMS of 3.24 vox; pass 2 by only 0.08.
   - Fit residual RMS 1.565 9 um vox; leave-one-out 1.895.
5. **16 new patches** (`heldout_run.py`): see the Verdict and the table below.

## Final affine (fitted on the 24 fit patches; `affine_final.json`, sha256 74f239e4...)
q2 = A p9 + c. Level-0 voxels, (x, y, z), p9 in the 9.366 um volume and q2 in the 2.403 um volume.

    A =
    [ 3.899461586, -0.007417620, -0.002026892]
    [ 0.008400943,  3.898951174,  0.002501017]
    [-0.003268341, -0.003858651,  3.896784296]
    c = [324.8250, 217.6003, -49808.3547]

In the task's form, q2 = ((x9+tx)F, (y9+ty)F, (z9+tz-z0)F) with t = M (p - Pm) + b:
- Pm = [2826.17, 3295.50, 14861.50] (mean of the fit-patch centres)
- z0 = 12787.546 (the 9 um z that maps to rescan z = 0 at Pm)
- b = [70.6685, 72.5755, -0.4489]

    M =
    [ 0.000470445, -0.001903111, -0.000520032]
    [ 0.002155399,  0.000339491,  0.000641677]
    [-0.000838546, -0.000990000, -0.000216457]

Rescan z-band covered, in 9 um z under the final affine, over the scroll cross-section (68,533 L4 columns):
- rescan z = 0 -> 12784.8, 12788.1, 12791.0 (min, median, max)
- rescan z = 15120 -> 16665.0, 16668.2, 16671.1

**CHECK of the old estimate "eligible z about 12790-16670": confirmed to within about 2-5 vox** (independently by whole-slice NCC: 12790.6-16669.3). Non-affine terms add about +-2-3 vox locally.

The final affine differs from the mesh affine by an RMS of 3.03 vox (max 5.0) at the 40 patch centres, which lie away from the meshes.

## Held-out patches (final affine, zero shift; r = raw 9 um vs prefiltered rescan)
| id | p9 centre (x, y, z) | r | r after local shift | residual d9 (x, y, z) | abs(d9) | abs(A d) rescan vox | pitch9 | r_ctrl | r (M3) |
|---|---|---|---|---|---|---|---|---|---|
| P05 | 4992, 3840, 16608 | 0.704 | 0.763 | -0.18, -0.02, +2.10 | 2.10 | 8.20 | 12.0 | 0.345 | 0.725 |
| P07 | 1920, 2176, 13296 | 0.749 | 0.759 | -0.92, +0.30, +0.51 | 1.09 | 4.26 | 11.5 | 0.423 | 0.770 |
| P11 | 2432, 5248, 12864 | 0.828 | 0.883 | -1.35, -1.32, +0.06 | 1.89 | 7.38 | 5.0 | 0.636 | 0.837 |
| P12 | 4352, 2560, 15888 | 0.852 | 0.901 | +0.81, -0.01, -0.05 | 0.81 | 3.17 | 7.0 | 0.363 | 0.907 |
| P13 | 2304, 5376, 16608 | 0.624 | 0.560 | +0.33, +0.83, +1.95 | 2.15 | 8.37 | 10.0 | 0.135 | 0.663 |
| P14 | 3328, 5248, 15408 | 0.670 | 0.827 | -1.45, -1.15, -0.06 | 1.85 | 7.23 | 9.5 | 0.299 | 0.785 |
| P15 | 4864, 4480, 13440 | 0.742 | 0.895 | -1.30, -0.23, +0.62 | 1.46 | 5.70 | 8.0 | 0.389 | 0.904 |
| P18 | 3328, 3456, 14592 | 0.614 | 0.948 | +0.40, -0.23, -2.71 | 2.75 | 10.73 | 10.0 | 0.074 | 0.840 |
| P26 | 4224, 2560, 13296 | 0.888 | 0.912 | +0.42, +0.17, -0.27 | 0.53 | 2.08 | 8.5 | 0.158 | 0.909 |
| P28 | 3712, 4992, 14064 | 0.715 | 0.882 | -1.35, -0.74, +0.02 | 1.54 | 6.00 | 8.5 | 0.276 | 0.892 |
| P30 | 4352, 5120, 12960 | 0.631 | 0.906 | -2.11, -0.16, +1.13 | 2.40 | 9.37 | 11.0 | 0.032 | 0.889 |
| P31 | 2432, 3968, 15072 | 0.733 | 0.830 | -0.10, -1.43, -1.12 | 1.81 | 7.07 | 26.5 | 0.031 | 0.852 |
| P34 | 1664, 2816, 13872 | 0.852 | 0.851 | -0.87, +1.02, -0.01 | 1.34 | 5.23 | 6.0 | 0.675 | 0.874 |
| P35 | 1408, 2432, 16176 | 0.828 | 0.880 | -0.25, +0.69, +1.31 | 1.50 | 5.83 | 7.5 | 0.068 | 0.861 |
| P37 | 3584, 3840, 13728 | 0.504 | 0.973 | -0.22, +0.13, -3.37 | 3.38 | 13.16 | 17.0 | 0.171 | 0.803 |
| P39 | 2816, 6016, 13248 | 0.641 | 0.587 | +0.47, +0.59, +1.84 | 1.99 | 7.75 | 8.0 | 0.474 | 0.625 |

## Fit patches (same metrics, final affine)
Median r 0.748, RMS 1.57 9 um vox, control median drop 0.469 (21/24 clear).
| id | p9 centre (x, y, z) | r | r after local shift | residual d9 (x, y, z) | abs(d9) | abs(A d) rescan vox | pitch9 | r_ctrl | r (M3) |
|---|---|---|---|---|---|---|---|---|---|
| P00 | 1664, 4096, 15936 | 0.759 | 0.809 | -0.10, -1.58, -1.04 | 1.89 | 7.37 | 7.5 | 0.270 | 0.810 |
| P01 | 5248, 3200, 12864 | 0.730 | 0.818 | -0.74, +0.70, +1.93 | 2.18 | 8.49 | 13.5 | 0.344 | 0.861 |
| P02 | 1792, 1792, 14304 | 0.791 | 0.826 | -0.93, +0.56, +0.86 | 1.39 | 5.41 | 9.0 | 0.365 | 0.822 |
| P03 | 2688, 5888, 13680 | 0.615 | 0.594 | -0.38, +0.33, +1.57 | 1.65 | 6.44 | 8.5 | 0.356 | 0.583 |
| P04 | 4992, 3200, 15120 | 0.872 | 0.889 | +0.08, +0.83, +0.63 | 1.05 | 4.08 | 6.0 | 0.346 | 0.895 |
| P06 | 2048, 5504, 14736 | 0.701 | 0.747 | +0.15, +0.71, +0.99 | 1.23 | 4.80 | 8.5 | 0.187 | 0.741 |
| P08 | 5248, 3456, 14064 | 0.795 | 0.851 | -0.72, +0.72, +1.25 | 1.61 | 6.27 | 11.5 | 0.316 | 0.857 |
| P09 | 2048, 1792, 16608 | 0.713 | 0.759 | -0.27, -0.03, +1.49 | 1.51 | 5.89 | 17.0 | 0.166 | 0.740 |
| P10 | 1664, 2048, 15216 | 0.848 | 0.862 | -0.83, +0.83, +0.53 | 1.28 | 5.01 | 10.0 | 0.023 | 0.876 |
| P16 | 1792, 4352, 14160 | 0.846 | 0.873 | -0.34, -1.70, -1.29 | 2.16 | 8.43 | 8.0 | 0.270 | 0.819 |
| P17 | 3968, 4992, 16032 | 0.823 | 0.864 | -0.93, -0.56, +0.04 | 1.08 | 4.22 | 8.5 | 0.363 | 0.879 |
| P19 | 3328, 2048, 13824 | 0.575 | 0.747 | +1.07, -0.39, -0.30 | 1.17 | 4.57 | 10.0 | 0.356 | 0.713 |
| P20 | 896, 4352, 15360 | 0.759 | 0.799 | +0.25, +0.96, +0.88 | 1.33 | 5.17 | 6.0 | 0.365 | 0.797 |
| P21 | 2048, 1664, 15792 | 0.718 | 0.708 | -0.35, +0.11, +0.57 | 0.68 | 2.67 | 12.5 | 0.183 | 0.691 |
| P22 | 768, 3712, 16464 | 0.843 | 0.907 | +0.38, +1.00, +1.22 | 1.62 | 6.31 | 10.5 | 0.177 | 0.874 |
| P23 | 1152, 3328, 14736 | 0.826 | 0.826 | -0.08, +0.81, -0.14 | 0.83 | 3.23 | 8.5 | 0.567 | 0.825 |
| P24 | 2944, 3072, 12864 | 0.629 | 0.835 | +0.92, -1.21, -1.65 | 2.24 | 8.75 | 5.5 | 0.516 | 0.879 |
| P25 | 2688, 4224, 13344 | 0.767 | 0.919 | -0.04, -0.27, -1.98 | 2.00 | 7.79 | 8.0 | 0.203 | 0.831 |
| P27 | 2944, 3200, 15504 | 0.489 | 0.824 | +0.70, -1.02, -1.92 | 2.28 | 8.89 | 12.0 | 0.112 | 0.847 |
| P29 | 3328, 3072, 16368 | 0.398 | 0.817 | +0.85, -0.74, -2.28 | 2.54 | 9.91 | 39.0 | 0.121 | 0.774 |
| P32 | 2432, 1664, 14784 | 0.615 | 0.559 | -0.77, +0.06, +0.37 | 0.85 | 3.33 | 10.0 | 0.470 | 0.592 |
| P33 | 4736, 3840, 15552 | 0.893 | 0.897 | +0.07, +0.29, -0.62 | 0.69 | 2.69 | 17.0 | 0.203 | 0.897 |
| P36 | 3968, 2432, 14256 | 0.737 | 0.814 | +0.57, -0.11, -0.37 | 0.69 | 2.67 | 10.5 | 0.170 | 0.833 |
| P38 | 3456, 2176, 15120 | 0.734 | 0.881 | +0.95, -0.46, -0.71 | 1.28 | 4.99 | 6.0 | 0.699 | 0.869 |

## Secondary / exploratory (pre-registered in addendum 1; not deciding)
Models were chosen by leave-one-out on the fit patches only (`model_loo.json`; LOO RMS in 9 um vox):

| Model | Params | LOO RMS | Held-out RMS | Held-out median r | Held-out median r_lp |
|---|---|---|---|---|---|
| M0 affine | 12 | 1.895 | 1.916 | 0.724 | 0.825 |
| M1 affine + rho^2 z term | 13 | 1.274 | 1.468 | 0.794 | 0.884 |
| M3 affine + quadratic in (x, y), all outputs | 21 | 0.910 | 1.259 | 0.846 | 0.909 |

r_lp adds a Gaussian blur of sigma 1 (9 um vox) to both blocks.
- M3 would meet the RMS bar in 9 um vox but not in rescan vox, and misses r >= 0.85 by 0.004.
- It is exploratory and was chosen after the fit residuals were seen. It is not a pass.

## J exclusion (144 vox, 3-D)
- **J points.** The 9 um organizer meshes (`-on-20250821151531-9.366um`), sampled every 0.25 grid node (<= 5 vox) over each J window. The windows come from `logs/bank0841/summary.json` and were checked equal to `d3_feas_count_A.json`: 2136 px, grown by 20 px, own segment. Total: 829,890 points.
- **Admissibility.** A patch needs its 9 um block, grown by 6 vox, to lie >= 144 + 12 vox (Euclidean box distance) from every J point. The rescan footprint of that grown block is what was read.
- **Result.** Minimum over the 40 patches: 162.1 vox; 37 of 40 have no J point within 206 vox.
- **Nothing else was read or computed near J at level 0.** The coarse whole-slice scans (L3-L5, >= 75 um voxels) covered the full cross-section, J included, to find orientation and z-band only. They are CT-only NCC numbers, with no rendering, no ink inference and no surface sampling.

### Re-check under CORR-RETRACE-RULE (fail-closed; point-to-surface distance)
`jexcl_surface.py` -> `jexcl_surface_check.json`.
- **Surface.** The J-window 9 um meshes triangulated: 104,190 triangles, max edge 38.8 vox.
- **Method.** Each triangle near a patch is sampled barycentrically at 1/24 of an edge, and the sampling-gap bound (1.62 vox) is subtracted. Clearance = min(this point-to-surface lower bound, the densified-vertex distance), measured from the patch block grown by 6 vox.
- **Result.** Minimum clearance over all 40 patches: **160.5 vox** (P27, fit). The next lowest are P37 169.2 and P18 174.4 (held-out). All 40 are >= 144: **all admissible**; the patch set and results are unchanged.

## Failures and deviations
- The first `plan_patches.py` run crashed while printing an infinite distance, after writing a non-strict JSON. It was fixed and rerun with a deterministic, identical selection. Both runs are logged.
- The task says "RMS <= 1.5 vox" without a unit, so both units are reported. Both fail for the affine.
- `model_loo.py` was run once through `head` (broken pipe, not logged). It was rerun in full and logged; the output is deterministic.
- Timing and sanity: fit patch P00 was run alone once, before the pre-registration was written. It is disclosed there.

## What the orchestrator needs to declare next
1. Record reg0841 as the affine registration of PHerc0841, 9.366 -> 2.403 um: **held-out FAIL on r and RMS, control PASS**.
   - Orientation: identity (no flip or remount rotation).
   - Rescan band: 9 um z 12785-12791 -> 16665-16671 (CT-verified).
2. A single affine is not adequate at the 1.5-vox level. If a sub-voxel mapping is needed (e.g. for T-RESCAN or for 0841 cross-resolution work), declare a non-affine model **before** new data are used. A smooth displacement field (quadratic, or a thin-plate/B-spline on a denser patch grid of about 100 or more patches outside the J shell) fitted on fit patches, with a FRESH held-out set of 16 or more new patches: the current 16 are spent.
3. Near the organizer meshes, and hence the J windows, the organizer's mesh affine already agrees with the CT. B0841-BANK diagnostic: <= 1.4 px (9 um). Registration there can rely on it; registration elsewhere in the band needs item 2.
