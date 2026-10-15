Provenance: Project HERCULES | owner the owner | [id removed]

# Census plan for the 11 eligible JULY volumes (task census)

STATUS: DONE

Branch claude/gifted-bell-gavnl5-sib-census. Geometry and CT masks only: no ink model, no tracing, no image opened or rendered, no PHerc0841 access. Official data only: the anonymous S3 bucket vesuvius-challenge-open-data and villa 41701aa source (read for the normal-grid file format). Every run, failures included, is in logs/sib/census/runs.jsonl. Machine-readable results: logs/sib/census/census.json, seeds files logs/sib/census/seeds/PHerc<vol>_seeds.json (+ _dup_pairs.json), sync plans logs/sib/census/sync/PHerc<vol>_sync.json, run sheets logs/sib/census/runsheet/.

## Answers to the orchestrator (ASK.md, all accepted 19:16Z)
1. Duplicates: the hard geometric upper bound is reported, together with walker v2 counts labelled LOW RELIABILITY (validated sensitivity 13/35, false SAME 5/30). The binding duplicate test runs after tracing, on the traced meshes, with CORR-RETRACE-RULE form (b). Of any SAME pair the later seed (higher n) is dropped.
2. Centre: CT-mask centroid where no umbilicus exists. The calibrated error and the resulting +-0.2 wrap-fraction uncertainty are recorded, not corrected.
3. Ranking: the formula below (declared in ASK.md before any seed or ranking number existed). 1203 and 0846A go after all others.

## Method and exact commands
All tools are in tools/sib/census/ and run with /opt/hv/bin/python (Python 3.11, numpy, scipy, boto3, numcodecs, tifffile). Each run was wrapped in tools/sib/census/logrun.sh.
1. Listing: `PYTHONPATH=src python tools/sib/census/list_products.py --out /work/census/products`. This lists the m7 zarr (every level; per-z-chunk listing in parallel), every normal-grid object (sizes per xy / xz / yz slice file), the lasagna top level and the umbilicus JSONs. Small metadata files are sha256-hashed.
2. CT-mask shape: `python tools/sib/census/mask_shape.py --out /work/census/mask --vols <11>`. It reads pyramid level 4 of each masked volume (uncompressed 128^3 chunks, whole chunk rows, never the whole volume). Mask = non-zero with interior holes filled. Per level-4 slice it records area, centroid, second-moment axis ratio, solidity and deepest interior point.
3. Centre: `tools/sib/census/centre.py`. Official umbilicus where the same volume has one (0125, 0211, 0826; volume name checked). Otherwise the mask centroid, running median over 65 level-4 slices, then Gaussian sigma 256 vox in z. Scroll z extent = slices with area >= 0.25 x the median non-empty area.
4. Seeds: `PYTHONPATH=src python -u tools/sib/census/plan_seeds.py --mask /work/census/mask --umb /work/census/umb --out /work/census/seeds --vols <vols>`. Design, fixed before placement:
   - 20 z-levels evenly spaced in [z_lo + 1150, z_hi - 1150].
   - 3 angles 120 deg apart, the triplet rotated (k mod 3) x 40 deg so adjacent levels never stack.
   - Wrap fraction f = 0.35 + 0.35 * frac(0.5 + 0.618034 n), n = 3k + a, on the ray from the centre to the filled-mask boundary.
   - The point must lie inside the mask eroded by 48 level-0 vox (3 px at level 4) and be >= 320 vox from every other seed. Otherwise f, then the angle, is nudged by the smallest step.
   - Snap to the nearest level-0 m7 voxel with value 255 (the m7 zarr is binary 0/255, measured) that also satisfies eroded mask, z margin and spacing.
   - seed_xyz is [x, y, z] in level-0 voxels (the vc_grow_seg_from_seed order). The voxel size, 9.362 um, is taken from metadata.json.
5. Sync and time: `tools/sib/census/sync_plan.py` (called by build_report.py) and `tools/sib/census/run_sheet.py`.
6. Aggregation: `PYTHONPATH=src python tools/sib/census/build_report.py` and `python tools/sib/census/report_tables.py`.
Unit tests: `/opt/hv/bin/python -m pytest -q tests/sib_census_test_geometry.py` (6 passed: ray radius and erosion on a synthetic disc, weighted line centre, smoothers, surface distance, sync ranges).

## Headline
- All 11 volumes have an official m7 prediction and complete normal grids: one file per slice in xy, xz and yz, sparse-volume 1, 10.0-19.8 GB each including previews. Voxel size is 9.362 um for all 11, read from metadata.json.
- Seeds files are written for all 11 volumes: 654 of 660 planned seeds placed, and every placed seed passes all checks (eroded mask, z margin, >= 320 vox spacing, m7 == 255). Snap distance median 1.4-3.0 vox and p90 4.5-9.1 vox per volume; the largest single snap is 58 vox (0358).
- Six seeds had no admissible planned point and are left unplaced, not forced: 0257 s02, 0826 s00, 0846A s00, s01, s02 and s05. All sit at the lowest z-levels, where the eroded mask is narrow.
- Tractability ranking: 0191, 0813, 0211, 0826, 0257, 0125, 0358, 1545, 0846B, then 1203 and 0846A (the public-rescan volumes go last by rule). By raw score, 1203 would be 5th.
- Run sheets for the top 3 (0191, 0813, 0211) are in logs/sib/census/runsheet/. Plan only: nothing is traced before the orchestrator declares T0 and the census run.
- The duplicate share cannot be measured reliably before tracing (walker validation below). The binding test is the post-trace CORR-RETRACE-RULE form (b).

## 1. m7 prediction and normal grids
The m7 prediction is <vol>-surface-20260413222639-surface-m7-L0-th0.2.zarr: 6 levels, blosc/zstd 192^3 chunks, uint8 with values 0/255. The normal grids are the matching .normal-grids/ directory. Full paths, per-level object counts and bytes, and per-file sizes are in census.json (m7_levels, ngrid_planes); per-slice file sizes are in /work/census/products/*_ngrid_sizes.npz (not committed).

Normal-grid bytes per z-band of 500 slices (xy plane only):
- Only the xy plane is indexed by z. The xz files (one per y) and yz files (one per x) each span the whole z range and are needed whole.
- Band sizes: median 94-166 MB, max 136-445 MB per 500-slice band. Per-band values are in census.json xy_bytes_per_500_band.
- A 0 MB band on 0813 is real: xy files for z < 1152 exist but are empty (0 bytes), below the scroll.

## 2. Lasagna, umbilicus and centre
- Lasagna: model 20260419180421 for 9 of 11 (cos, grad_mag, nx, ny OME-Zarrs plus the lasagna JSON). None for 0846A and 0846B.
- Official umbilicus: 0125, 0211 and 0826 only; each names its own volume in metadata.volume (checked).

Centroid calibration against the official umbilicus (mask centroid at the same z):

| Vol | median err vox | p90 | max | median / r_eq | p90 / r_eq |
|---|---|---|---|---|---|
| 0125 | 298 | 647 | 708 | 0.14 | 0.28 |
| 0211 | 328 | 1047 | 1296 | 0.17 | 0.45 |
| 0826 | 386 | 764 | 1045 | 0.21 | 0.37 |

- For the 8 volumes that use the centroid, expect a comparable centre error: ~300-400 vox median, up to ~0.45 r_eq on oval volumes. The seed wrap fraction is therefore uncertain by about +-0.2 on oval volumes. This is recorded, not corrected (ASK answer 2).
- Flag rule: UNRELIABLE if the median axis ratio is < 0.65 or solidity p10 is < 0.85; otherwise caution. Flagged UNRELIABLE: 0257, 0358, 0846A, 0846B and 1545. 0846B is the most crushed (solidity median 0.65, p10 0.54). 0846A is irregular (solidity p10 0.79, axis ratio 0.50). 0125 is oval (axis ratio 0.51) but uses its umbilicus.
- Negative result: a CT-free centre from m7 sheet normals (structure-tensor normal-line intersection, levels 2 and 3) is worse than the centroid on both test volumes. Median error 396-448 vox on 0125 and 425-444 vox on 0211, against 231-304 vox for the centroid at the same z. Not used.

## 3. Axis direction
- Descending acquisition z (z_start > z_end, z_step 0): 0358 and 0846B. The other 9 are ascending.
- The root catalogue's z_direction_is_top_to_bottom is a different field and disagrees with this in places: 0358 is True, 0846B is False, and it is null for 0125, 0846A and 1203. Both fields are recorded per volume in census.json axis. Handedness must be settled by geometry where needed.

## 4. Seeds and duplicates
The design is in Method item 4. Per-seed records (id, level, angle, f planned / nudged / at seed, ray radius, planned and snapped xyz, snap distance, min separation, checks) are in logs/sib/census/seeds/PHerc<vol>_seeds.json.

Duplicates:
- Hard geometric upper bound: pairs whose trace neighbourhoods can overlap (surface distance <= 2R), as a share of all seed pairs. 4.7-14.6 % at 45 generations and 18.3-34.2 % at 75. 0846B and 0846A are highest.
- Walker v2 counts are LOW RELIABILITY.
  - Validated on 48 same-sheet pairs from official 1203 dev-set team segments (the T0 five are never opened) and 47 adjacent-sheet negatives: SAME on 13 of 35 determined positives and 5 of 30 determined negatives. AUC of |dr| is 0.60.
  - Two other walkers were rejected: v1 (radial snap) at 3 of 36 vs 2 of 35, AUC 0.47; v2 at step 2 / shift 1 at 8 of 35 vs 5 of 33.
  - On the census seeds, v2 calls 0-4 pairs SAME per volume. Most pairs in reach are undetermined, because the walker loses the sheet on long paths.
  - Per-pair verdicts, dr and reasons are in seeds/*_dup_pairs.json. The validation data is in valwalk_*.json.
- Binding rule (accepted): after tracing, apply CORR-RETRACE-RULE form (b) (point-to-triangulated-surface) to the traced meshes. For any SAME pair, drop the later seed.

## 5. Sync and time per seed
Sync model, from the official loader NormalGridVolume.cpp at villa 41701aa:
- Whole files xy/<z>.grid, xz/<y>.grid and yz/<x>.grid are read; the *_img previews are never opened.
- Reach is R = 20 vox x generations. The archive check: all six 75-generation team traces fill the L1 ball of radius 1500 vox (area 4,438,400 vox^2), and every bbox side is within 1471 vox of its seed.
- Upper bound per seed: files within +-(R+1) in all three planes. Typical per seed: the axis nearest the radial direction is shrunk to +-0.41 R (the archive's normal-axis extent is <= 603 vox).

Measured consequence:
- The union of the 60 seeds' files covers 87-94 % of the volume's xy+xz+yz planes at 45 generations. Per-seed local syncs therefore save almost nothing over one full-plane sync per volume: 8.4-16.5 GB without the previews. That fits the ~30 GB disk of this container type.
- Recommended: sync the full xy/xz/yz planes of one volume at a time, and delete them before the next volume. The per-level bands are still listed in the run sheets for smaller disks.

Time per seed:
- Organizer archive (vc_grow_seg_from_seed, thread_limit 1, six 75-generation 1203 traces): 133-238 s, median 193 s. Scaled by (g/75)^2 that is 70 s at 45 generations.
- Measured on this container type by the tracer sibling (gated build c, 1203 dev seed 163231537, 45 generations, 1 thread): 259.7 s, about 3.7 times the archive-scaled figure. Scaled, that is 722 s at 75 generations.
- Planning numbers use the measured figure. 60 seeds at 4 in parallel take 1.08 h per volume at 45 generations and 3.01 h at 75. The archive-scaled figures are 0.29 h and 0.81 h.

## 6. Ranking
The formula was declared in ASK.md before any seed or ranking number existed. Score = mean of five components, each 0-1:
- shape = clip((axis ratio median - 0.45) / 0.35);
- crushing = clip((solidity p10 - 0.60) / 0.33);
- centre = 1 with an umbilicus, 0.5 for a centroid with axis ratio >= 0.7, else 0.25;
- data = 0.5 x lasagna + 0.5 x z direction known in the root catalogue;
- seeding = share of 60 seeds passing every check.
1203 and 0846A (public rescans) then go after all others. Note that 0826 was publicly attempted by an outside team (D0-PRIZE-CHECK); this is not scored.

## Top-3 run sheets (plan only)
Files: logs/sib/census/runsheet/PHerc0191_runsheet.json, PHerc0813_runsheet.json, PHerc0211_runsheet.json. Each holds:
- the 60 seeds in 20 z-levels;
- per level, the xy / xz / yz slice ranges with their bytes and the sync command (tools/sib/tracer/sync_normalgrids.py from the tracer branch);
- the params.json at 45 and 75 generations: step 20, thread_limit 1, voxelsize 9.362 from metadata, normal_grid_path local, and <PRESET> = reject_dist_th / compactness / space_line_weight as declared after T0;
- 60 docker command lines for the gated build c (vc_grow_seg_from_seed --volume <m7 zarr on S3> --target-dir --params --seed x y z), per generation count.

| Vol | union sync GB (45 / 75 gen) | largest single-level band GB (45 / 75) | h for 60 seeds at 4 parallel (measured-scaled, 45 / 75) |
|---|---|---|---|
| 0191 | 15.06 / 15.90 | 8.95 / 10.39 | 1.08 / 3.01 |
| 0813 | 11.12 / 11.74 | 6.59 / 7.78 | 1.08 / 3.01 |
| 0211 | 10.98 / 11.82 | 6.25 / 7.49 | 1.08 / 3.01 |

## Failures and corrections (all in runs.jsonl)
- The first product listing was too slow (serial level-0 listing, then recursive lasagna listing). I killed it twice and relaunched with parallel per-z-chunk listing and top-level lasagna listing. The final listing is complete for all 11.
- The first seed planner (serial chunk fetch) was killed, then relaunched with parallel prefetch. A relaunch without the patch was killed within seconds.
- Walker v1 failed validation, so its duplicate counts were discarded (seed files moved to /work/census/seeds_v1_invalid, not committed).
- Snapping was corrected to enforce the z margin and spacing inside the snap search (before the fix, 4 of 60 seeds on 0191 left the z margin and 2 broke spacing).
- Batch 2 crashed on a seed with no admissible point (KeyError), fixed by skipping unplaced seeds in the spacing check. A second crash (walker v2 defined after the main block) was fixed by moving the entry point.
- Two of my kill commands also killed my own shell (pgrep -f matched the command line); the killed jobs were relaunched and logged.

## What the orchestrator needs to declare next
1. T0 for the gated tracer build and preset (fills <PRESET> in the run sheets).
2. The census run itself: volumes (default: top 3 of the ranking, 0191, 0813, 0211), generations (45 for coverage, 75 to match the team), and the full-plane sync per volume.
3. The post-trace duplicate test and drop rule (accepted: CORR-RETRACE-RULE form (b), drop the later seed of each SAME pair), plus the v2 truncation and core metrics that feed a* and K2.
4. Whether 0846B (most crushed, no lasagna, UNRELIABLE centroid) and the rescan volumes enter the census at all.

## Tables (generated by tools/sib/census/report_tables.py from census.json)

### Products (m7 prediction, normal grids, lasagna, umbilicus)

| Vol | volume id | vox um | shape z,y,x | m7 GB (6 levels) | NG total GB | NG xy / xz / yz GB | NG previews GB | lasagna | umbilicus |
|---|---|---|---|---|---|---|---|---|---|
| 0125 | 20250821151825 | 9.362 | 20840,8387,8387 | 22.77 | 16.83 | 5.34 / 3.82 / 4.96 | 2.71 | yes | official (83 pts) |
| 0191 | 20250821151635 | 9.362 | 18977,8387,8387 | 29.87 | 19.83 | 5.87 / 5.14 / 5.43 | 3.38 | yes | none |
| 0211 | 20250821151803 | 9.362 | 19416,7948,7948 | 19.22 | 14.42 | 4.50 / 3.49 / 4.10 | 2.33 | yes | official (87 pts) |
| 0257 | 20250821151750 | 9.362 | 18872,8388,8388 | 21.47 | 14.65 | 4.51 / 3.90 / 3.87 | 2.36 | yes | none |
| 0358 | 20250821151737 | 9.362 | 14744,7783,7783 | 18.89 | 12.48 | 3.83 / 3.27 / 3.30 | 2.08 | yes | none |
| 0813 | 20250821151723 | 9.362 | 16993,7947,7947 | 21.72 | 14.60 | 4.27 / 3.67 / 3.97 | 2.68 | yes | none |
| 0826 | 20250821151701 | 9.362 | 16920,8169,8169 | 12.05 | 11.36 | 3.50 / 2.84 / 3.14 | 1.87 | yes | official (49 pts) |
| 0846A | 20250728152254 | 9.362 | 14019,7726,7726 | 13.47 | 9.98 | 2.99 / 2.51 / 2.89 | 1.60 | no | none |
| 0846B | 20250804142305 | 9.362 | 13926,7859,7859 | 15.71 | 11.08 | 3.30 / 2.76 / 3.21 | 1.80 | no | none |
| 1203 | 20250820131727 | 9.362 | 18977,6844,6844 | 18.96 | 13.11 | 3.81 / 3.22 / 3.70 | 2.38 | yes | none |
| 1545 | 20250821151648 | 9.362 | 20961,7506,7506 | 17.98 | 13.41 | 4.19 / 3.24 / 3.85 | 2.13 | yes | none |

### Normal-grid xy bytes per 500-slice z band

| Vol | bands | median MB | min MB | max MB | mean xz file MB | mean yz file MB |
|---|---|---|---|---|---|---|
| 0125 | 42 | 130 | 61 | 183 | 0.585 | 0.601 |
| 0191 | 38 | 166 | 61 | 240 | 0.613 | 0.648 |
| 0211 | 39 | 105 | 56 | 304 | 0.491 | 0.515 |
| 0257 | 38 | 129 | 49 | 149 | 0.465 | 0.521 |
| 0358 | 30 | 139 | 56 | 154 | 0.436 | 0.425 |
| 0813 | 34 | 137 | 0 | 161 | 0.517 | 0.525 |
| 0826 | 34 | 94 | 69 | 445 | 0.348 | 0.384 |
| 0846A | 29 | 109 | 40 | 136 | 0.325 | 0.373 |
| 0846B | 28 | 101 | 23 | 196 | 0.370 | 0.409 |
| 1203 | 38 | 95 | 31 | 136 | 0.541 | 0.540 |
| 1545 | 42 | 94 | 55 | 169 | 0.497 | 0.513 |

### Axis direction and CT-mask shape (level 4)

| Vol | acquisition z | root catalogue top-to-bottom | scroll z extent (vox) | axis ratio med / p10 | solidity med / p10 | r_eq med (vox) | centre source | centroid flag |
|---|---|---|---|---|---|---|---|---|
| 0125 | ascending (-376.3 -> -190.2584 mm) | None | 760-20744 | 0.51 / 0.38 | 0.95 / 0.90 | 2204 | umbilicus | n/a (umbilicus) |
| 0191 | ascending (-359.3 -> -191.8626 mm) | False | 888-18904 | 0.82 / 0.65 | 0.98 / 0.95 | 2607 | mask centroid | caution |
| 0211 | ascending (-362.3 -> -185.5604 mm) | True | 760-18904 | 0.58 / 0.51 | 0.96 / 0.90 | 1969 | umbilicus | n/a (umbilicus) |
| 0257 | ascending (-356.3 -> -188.8626 mm) | False | 760-18040 | 0.59 / 0.50 | 0.95 / 0.92 | 2169 | mask centroid | UNRELIABLE |
| 0358 | descending (-185.3 -> -315.5292 mm) | True | 1144-14648 | 0.59 / 0.48 | 0.98 / 0.88 | 2366 | mask centroid | UNRELIABLE |
| 0813 | ascending (-341.3 -> -192.4666 mm) | False | 1656-16664 | 0.83 / 0.67 | 0.98 / 0.93 | 2365 | mask centroid | caution |
| 0826 | ascending (-338.3 -> -189.4666 mm) | True | 8-16888 | 0.49 / 0.31 | 0.94 / 0.87 | 1947 | umbilicus | n/a (umbilicus) |
| 0846A | ascending (-312.3 -> -191.373 mm) | None | 8-13768 | 0.50 / 0.38 | 0.87 / 0.79 | 1908 | mask centroid | UNRELIABLE |
| 0846B | descending (-185.3 -> -306.227 mm) | False | 1240-13608 | 0.49 / 0.37 | 0.65 / 0.54 | 1834 | mask centroid | UNRELIABLE |
| 1203 | ascending (-358.3 -> -190.8626 mm) | None | 1016-18984 | 0.74 / 0.61 | 0.97 / 0.95 | 2016 | mask centroid | caution |
| 1545 | ascending (-378.3 -> -192.2584 mm) | True | 760-20504 | 0.48 / 0.39 | 0.97 / 0.93 | 1812 | mask centroid | UNRELIABLE |

### Seeds

| Vol | placed / 60 | all checks pass | snap vox p50 / p90 / max | nudged | f at seed (min-max) | pairs in reach 45 / 75 gen | v2 SAME / DIFF / UNDET (45) | v2 SAME / DIFF / UNDET (75) | upper bound share 45 / 75 |
|---|---|---|---|---|---|---|---|---|---|
| 0125 | 60 | 60 | 2.0 / 6.1 / 14.5 | 0 | 0.35-0.69 | 105 / 364 | 2 / 36 / 67 | 3 / 93 / 268 | 0.059 / 0.206 |
| 0191 | 60 | 60 | 2.2 / 8.4 / 31.7 | 1 | 0.35-0.70 | 84 / 324 | 0 / 13 / 71 | 0 / 22 / 302 | 0.047 / 0.183 |
| 0211 | 60 | 60 | 1.9 / 4.5 / 14.5 | 0 | 0.35-0.69 | 136 / 401 | 0 / 45 / 91 | 0 / 96 / 305 | 0.077 / 0.227 |
| 0257 | 59 | 59 | 2.2 / 7.4 / 11.8 | 1 | 0.35-0.69 | 133 / 370 | 0 / 24 / 109 | 1 / 37 / 332 | 0.078 / 0.216 |
| 0358 | 60 | 60 | 1.4 / 9.0 / 58.0 | 0 | 0.35-0.69 | 201 / 484 | 1 / 47 / 153 | 2 / 70 / 412 | 0.114 / 0.273 |
| 0813 | 60 | 60 | 2.3 / 6.4 / 9.6 | 0 | 0.35-0.69 | 135 / 409 | 4 / 24 / 107 | 4 / 43 / 362 | 0.076 / 0.231 |
| 0826 | 59 | 59 | 2.0 / 9.1 / 26.2 | 0 | 0.35-0.69 | 184 / 436 | 3 / 62 / 119 | 3 / 103 / 330 | 0.108 / 0.255 |
| 0846A | 56 | 56 | 2.0 / 7.0 / 33.0 | 1 | 0.35-0.70 | 183 / 505 | 0 / 48 / 135 | 0 / 76 / 429 | 0.119 / 0.328 |
| 0846B | 60 | 60 | 1.7 / 6.7 / 10.0 | 0 | 0.35-0.69 | 259 / 605 | 3 / 66 / 190 | 3 / 110 / 492 | 0.146 / 0.342 |
| 1203 | 60 | 60 | 3.0 / 6.4 / 11.8 | 0 | 0.35-0.69 | 124 / 374 | 0 / 28 / 96 | 0 / 56 / 318 | 0.070 / 0.211 |
| 1545 | 60 | 60 | 2.1 / 6.4 / 11.9 | 0 | 0.35-0.70 | 122 / 386 | 2 / 35 / 85 | 4 / 75 / 307 | 0.069 / 0.218 |

### Sync plan and time per seed

| Vol | per-seed upper GB (median, 45 / 75 gen) | per-seed typical GB (median, 45 / 75) | union 60 seeds GB (45 / 75) | full xy+xz+yz GB | s/seed 45 / 75 (archive-scaled, 1 thread) | 60 seeds h at 4 parallel (45 / 75) |
|---|---|---|---|---|---|---|
| 0125 | 3.65 / 5.75 | 2.76 / 4.41 | 12.92 / 13.76 | 14.12 | 70 / 193 | 0.29 / 0.81 |
| 0191 | 4.24 / 6.69 | 3.22 / 5.14 | 15.06 / 15.90 | 16.45 | 70 / 193 | 0.29 / 0.81 |
| 0211 | 3.23 / 5.05 | 2.44 / 3.88 | 10.98 / 11.82 | 12.09 | 70 / 193 | 0.29 / 0.81 |
| 0257 | 3.30 / 5.19 | 2.50 / 3.99 | 11.14 / 11.86 | 12.28 | 70 / 193 | 0.29 / 0.81 |
| 0358 | 2.86 / 4.52 | 2.22 / 3.55 | 9.40 / 10.00 | 10.40 | 70 / 193 | 0.29 / 0.81 |
| 0813 | 3.30 / 5.20 | 2.52 / 4.07 | 11.12 / 11.74 | 11.92 | 70 / 193 | 0.29 / 0.81 |
| 0826 | 2.41 / 3.82 | 1.84 / 2.92 | 8.53 / 9.18 | 9.48 | 70 / 193 | 0.29 / 0.81 |
| 0846A | 2.39 / 3.78 | 1.83 / 2.95 | 7.26 / 7.86 | 8.38 | 70 / 193 | 0.29 / 0.81 |
| 0846B | 2.58 / 4.10 | 1.96 / 3.15 | 8.42 / 8.96 | 9.27 | 70 / 193 | 0.29 / 0.81 |
| 1203 | 3.17 / 4.95 | 2.41 / 3.78 | 10.07 / 10.62 | 10.73 | 70 / 193 | 0.29 / 0.81 |
| 1545 | 3.07 / 4.80 | 2.31 / 3.70 | 10.28 / 10.98 | 11.28 | 70 / 193 | 0.29 / 0.81 |

### Ranking

| Final rank | Vol | score | shape | crushing | centre | data | seeding | raw rank | rescan |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0191 | 0.900 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1 | no |
| 2 | 0813 | 0.900 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 2 | no |
| 3 | 0211 | 0.854 | 0.36 | 0.91 | 1.00 | 1.00 | 1.00 | 3 | no |
| 4 | 0826 | 0.785 | 0.12 | 0.82 | 1.00 | 1.00 | 0.98 | 4 | no |
| 5 | 0257 | 0.720 | 0.41 | 0.96 | 0.25 | 1.00 | 0.98 | 6 | no |
| 6 | 0125 | 0.719 | 0.17 | 0.92 | 1.00 | 0.50 | 1.00 | 7 | no |
| 7 | 0358 | 0.699 | 0.39 | 0.85 | 0.25 | 1.00 | 1.00 | 8 | no |
| 8 | 1545 | 0.668 | 0.10 | 0.99 | 0.25 | 1.00 | 1.00 | 9 | no |
| 9 | 0846B | 0.370 | 0.10 | 0.00 | 0.25 | 0.50 | 1.00 | 11 | no |
| 10 | 1203 | 0.763 | 0.82 | 1.00 | 0.50 | 0.50 | 1.00 | 5 | yes |
| 11 | 0846A | 0.381 | 0.15 | 0.57 | 0.25 | 0.00 | 0.93 | 10 | yes |
