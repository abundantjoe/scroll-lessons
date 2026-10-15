Provenance: Project HERCULES | owner the owner | [id removed]

# reg0841-NA: non-affine PHerc0841 9.366 um <-> 2.403 um map (CT only)

STATUS: DONE

Numbers only: no image, slice or ink map was viewed or produced, and no ink model was run.
Machine-readable: `reg0841na_summary.json`, plus the per-step JSON files in this folder. Runs are logged in `runs.jsonl`; the first two entries were also written to ../reg0841/runs.jsonl. Chunk hashes are in `chunk_sha256_na.jsonl.gz`.

## Verdict (16 NEW held-out patches, pre-registered in `prereg_na.md` at commit 30b4974, before any analysis)
| Bar | Value | Result |
|---|---|---|
| held-out median r >= 0.85 | 0.863 (min 0.563) | **PASS** |
| RMS residual <= 1.5 vox (9 um) | 0.977 (max 1.47); rescan vox 3.81 | **PASS** |
| half-pitch control: median drop >= 0.30 and >= 14/16 clear | median drop 0.695; 15/16 | **PASS** |
| round trip 9 -> 2.4 -> 9 um < 0.5 vox | max 1.1e-11 vox over 2056 points (4 fixed-point iterations) | **PASS** |

Reference numbers on the same 16 patches:
- The affine alone gives RMS 1.79 vox.
- The NCC ceiling after a local shift is a median of 0.881.
- r_lp (both blocks blurred, sigma 1) has a median of 0.915.

Caveats:
- The round trip only checks that the inverse of the map is numerically exact. It is not an accuracy measure; the held-out RMS is.
- The half-pitch estimates vary from 5.0 to 23.5 vox (median 12.0). Patches with a large estimated pitch get a large control shift. N07, with pitch 5.0, is the one patch whose control did not drop clearly (r_ctrl 0.761 against r 0.879).
- r on N03 is only 0.563, but its NCC after a local shift is 0.523. That patch's CT similarity is low whatever the alignment.

## Model
- **Map.** f(p) = A (p + u(p)) + c, with A and c from `../reg0841/affine_final.json` and u in 9 um vox.
- **Data.** The field was fitted on the 40 earlier correspondences (24 fit + 16 old held-out), each measured by converged phase correlation under the affine.
- **Selection.** The model was chosen by 40-point leave-one-out, and frozen and pushed before any new-patch read. `field_final.json`: kind **Q** (quadratic M3: affine plus x^2, xy, y^2 terms in all three components; 21 parameters).
- **LOO RMS.** 1.044 vox (max 2.06), against 1.715 for the affine alone over the same 40 points. The best of the other candidates: thin_plate_spline smoothing 1: 1.084; thin_plate_spline smoothing 0.1: 1.094; thin_plate_spline smoothing 0.01: 1.103.
- **Field size.** |u| has a median of 1.26 and a max of 3.66 vox over the band.
- **Evaluation.** Coefficients are reproducible with `field.load_final()`. It needs the two reg0841 result JSONs.

## Held-out table (frozen map, no refit)
| id | cell (z, radius) | centre (x, y, z) | r | r_lp | residual d_f (x, y, z) | abs(d_f) | affine-only abs(d) | pitch9 | r_ctrl | NCC after local shift |
|---|---|---|---|---|---|---|---|---|---|---|
| N00 | [0, 0] | 3200, 4096, 13632 | 0.898 | 0.945 | +0.09, +0.83, -0.69 | 1.09 | 2.83 | 15.5 | 0.086 | 0.965 |
| N01 | [0, 1] | 2816, 3072, 13824 | 0.847 | 0.913 | +0.49, +0.09, +0.32 | 0.59 | 2.11 | 15.0 | 0.214 | 0.820 |
| N02 | [0, 2] | 2304, 4224, 13680 | 0.873 | 0.931 | -0.30, -0.80, +0.10 | 0.86 | 2.30 | 12.0 | 0.124 | 0.899 |
| N03 | [0, 3] | 2432, 2048, 13776 | 0.563 | 0.660 | -0.79, -0.00, +0.43 | 0.90 | 0.99 | 10.5 | 0.319 | 0.523 |
| N04 | [1, 0] | 4480, 3456, 14400 | 0.912 | 0.949 | +0.45, +0.71, -0.61 | 1.04 | 1.31 | 21.0 | 0.035 | 0.956 |
| N05 | [1, 1] | 2560, 3200, 14544 | 0.875 | 0.935 | +0.65, -0.47, +0.60 | 1.00 | 2.04 | 23.0 | 0.073 | 0.834 |
| N06 | [1, 2] | 2176, 4352, 14736 | 0.807 | 0.881 | -0.56, -1.03, -0.06 | 1.18 | 2.26 | 7.5 | 0.360 | 0.837 |
| N07 | [1, 3] | 1920, 4864, 14016 | 0.879 | 0.923 | -0.18, +0.78, +1.22 | 1.46 | 1.05 | 5.0 | 0.761 | 0.881 |
| N08 | [2, 0] | 4096, 3200, 15312 | 0.878 | 0.931 | +0.34, +0.34, -0.75 | 0.89 | 2.05 | 13.5 | 0.095 | 0.954 |
| N09 | [2, 1] | 4736, 3200, 15264 | 0.897 | 0.940 | +0.18, +0.56, -0.56 | 0.82 | 0.75 | 9.5 | 0.110 | 0.929 |
| N10 | [2, 2] | 2176, 4864, 15024 | 0.810 | 0.883 | -1.08, -0.99, +0.05 | 1.47 | 1.77 | 13.5 | 0.109 | 0.824 |
| N11 | [2, 3] | 896, 3584, 15312 | 0.866 | 0.914 | +0.47, +0.35, -0.28 | 0.65 | 1.22 | 12.0 | 0.177 | 0.882 |
| N12 | [3, 0] | 3456, 4480, 15840 | 0.715 | 0.823 | -0.21, +0.36, -0.38 | 0.56 | 1.80 | 9.5 | 0.106 | 0.814 |
| N13 | [3, 1] | 4096, 2944, 16080 | 0.861 | 0.916 | +0.23, +0.10, -0.56 | 0.62 | 1.77 | 23.5 | 0.134 | 0.919 |
| N14 | [3, 2] | 3200, 5248, 16080 | 0.854 | 0.915 | -0.94, -0.59, +0.41 | 1.18 | 1.71 | 8.0 | 0.165 | 0.853 |
| N15 | [3, 3] | 1024, 3200, 16560 | 0.848 | 0.908 | +0.58, +0.34, +0.01 | 0.68 | 1.26 | 6.5 | 0.172 | 0.885 |

## Organizer-mapping offset (item 4; numbers only; ASK.md defaults 1-3)
D = f^-1(q2_org) - p9, in 9 um vox. p9 is the 9 um mesh point at a canvas position; q2_org is the organizer's 2.4 um mesh point at the corresponding canvas position, c2 = (c9 + 10) N2/N9 - 10. D is split along the 9 um mesh normal.

**Exact 288 fold-A pool tiles** (orchestrator answer to ASK 1): `inputs/d3_pool_fa_origins.json` from the work branch. Its source manifest sha256 is 8b127e10..., equal to d3_stage1.json. All 288 are inside the geometric superset and valid in both meshes (w00 118, 214732 100, 022814 70).
- |D| (mesh pair, primary): median 1.20, p95 2.07, max 2.84
- normal |D_n|: median 0.22, p95 0.80, max 1.50
- in-surface: median 1.14, p95 1.98, max 2.41
- mean vector (x, y, z): +0.94, +0.33, -0.76
- organizer mesh affine instead of the mesh pair: |D| median 1.31, p95 2.01, max 2.31; normal median 0.22, p95 0.75, max 1.14
- per segment, |D| median / max: w00 1.23 / 2.84; 214732 1.06 / 2.14; 022814 1.26 / 2.14

**The 18 dropped tiles:** |D| median 0.86, max 2.25; normal |D_n| max 0.87.

**Fold-A tiles, geometric superset** (ASK 1): 128 px tiles, stride 64, >= 90 % mesh-valid, with all nodes >= 110 vox from J, which guarantees the set contains the 288.
- 871 tiles are valid in both meshes (w00 328, 214732 325, 022814 244).
- |D|: median 1.28, p95 2.16, max 2.84
- normal |D_n|: median 0.28, p95 0.92, max 1.72
- in-surface: median 1.22, p95 2.07, max 2.55
- mean vector (x, y, z): +0.99, +0.28, -0.84

The organizer's mesh affine in place of the mesh pair gives the same picture: |D| median 1.37, p95 2.12, max 2.45.

(Superset view of the same 18 dropped tiles:) |D| median 0.86, max 2.25.

J-window centres (mesh geometry and field only; no J CT data):
| J | segment | abs(D) mesh pair | normal | in-surface | abs(D) mesh affine |
|---|---|---|---|---|---|
| J1 | 214732 | 0.78 | -0.60 | 0.50 | 0.72 |
| J2 | w00 | 0.49 | -0.34 | 0.35 | 0.76 |
| J3 | 214732 | 1.98 | -0.26 | 1.97 | 1.91 |
| J4 | 022814 | 1.26 | -0.58 | 1.12 | 1.27 |
| J5 | 022814 | 0.36 | -0.35 | 0.10 | 0.68 |

What these offsets mean:
- **Label positions.** The organizer's canvas correspondence places points about 1.3 vox (median; ~12 um) from where our CT map puts them. At most it is 2.8 vox, almost all in-surface (normal median 0.28, max 1.72). For the J seal (letter matching at 150/250 px) this is negligible. For ref9 pixel labels it means an in-plane shift of about 1-2.5 px at 9 um, below the ink-stroke width scale but not zero.
- **Uncertainty.** These offsets are of the same size as the field's own leave-one-out error (RMS 1.04 vox at patch sites). The field is only interpolated near the meshes: no patch lies within 160 vox of J, and the fold-A tiles are near J by construction. So they bound the misalignment at about <= 2-3 vox; they do not measure it precisely. A precise local number would need CT blocks that are allowed near the tiles, which the J rule forbids for blocks that overlap the J shell.

## Failures and deviations
- `org_offsets.py` first ran with a 124-vox node threshold. That did not guarantee a superset of the 288, so it was corrected to 110 and rerun. Both runs are logged (na_org_offsets, na_org_offsets_v2); only v2 is reported.
- The 288-tile list arrived after the first report (ASK 1 answered). The exact 288 are now reported alongside the superset (runs na_org_offsets_v3, which failed on a dict-key bug, and v4).
- ASK.md items 1-4 were answered by the orchestrator; every default was accepted.

## What the orchestrator needs to declare next
1. Record REG-0841-NA: the non-affine map (affine + quadratic field, frozen `field_final.json`) PASSES all pre-registered held-out bars and the round trip. It can serve as the validated 0841 cross-resolution mapping, within the band (9 um z about 12788-16668) and the tested cross-section.
2. Record the organizer-offset bound on the 288 fold-A tiles: median 1.20 vox, max 2.84; normal max 1.50; mostly in-surface. It is within the field's error, so no correction to the J seal is indicated. ref9 teacher labels may carry up to ~2-3 px of in-plane shift.
3. Optional: a denser patch grid would tighten the field near the meshes, for example outside the J shell but within 160-400 vox of the organizer meshes.
