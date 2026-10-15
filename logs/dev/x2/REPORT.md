# X2 fused-lamina count (tools/unr/fused_count.py) - dev lane x2 report

Provenance: Project HERCULES | [id removed]. DECL-UNR-1 item 4 as amended (count by the along-stacking density periodicity). No letters, no readings, no sheet index are claimed; every number below is a measurement of a code path on synthetic slabs or a measurement of one declared window of PHerc0268 at 8.64 um.

## 1. Method (as implemented)

- 16-section y-slab, stripe removal per xz section; 3-D structure tensor (derivative sigma 2, integration sigma 16 voxels = one pitch) for the layering normal; reliable where coherence >= 0.3 and gradient energy >= 0.2 x the in-mask median; 64 x 64 (z, x) tiles admissible only where reliable normals vary < 15 deg (p95) and the y-tilt <= 15 deg.
- Rays in the section plane along the projected tile normal (every section, every 8th x), cut where a reliable normal departs > 15 deg from the ray; widths and periods x cos(y-tilt). Runs = lamina peaks (prominence >= 3 MAD, the survey definition) merged across valleys that do not reach the gap level (lo + 0.3 contrast), extent at half contrast; classes against w_s = 14 vox (122 um): SHEET <= 1.4 w_s, PAIR 1.4-2.5 w_s, FUSED > 2.5 w_s. Runs touching a ray end are dropped. Rays through one run are pooled by z-interval overlap (IoU >= 0.5) between neighbouring rays, across tiles.
- Periodicity per group of rays (one section; wide runs also split in 128-voxel x-blocks; >= 3 rays): the interface-energy signal |d/ds G_1(density)| of the run with 4 voxels trimmed at each end (dips and level steps at the sheet contacts both become pulses; the sheet-to-sheet density staircase, whose spectrum has a null at the sheet period and a bump near twice it, disappears); periodograms (NFFT 4096, unit band power per ray) and unbiased autocorrelations averaged over the group. Candidates = periodogram maxima in [3 vox, T/1.5]; REJECTED and recorded: periods < 0.8 w_s = 11.2 vox (half-layer ~35 um, fibre bundles 50-100 um and their harmonics) and > 2 w_s = 28 vox (a single sheet inside a run is narrower than the PAIR limit). Pitch = the shortest accepted line with >= 0.5 of the strongest accepted line and a contrast >= 1.5 over the local broadband floor (median of the mean periodogram within a factor 3, the line excluded over one resolution cell).
- Per pooled run (>= 6 groups with a pitch): pitch p10/p50/p90 over groups; count = T_p50 / pitch_p50; range [T_p50 / pitch_p90, T_p50 / pitch_p10]; error = half the range. Integer claimed only if error < 1 sheet AND anchored (the nearest neighbour run on both sides is a gap-resolved SHEET for >= 50 % of the rays that observe both neighbours) AND no sub-harmonic risk (a STRONGER rejected-band line at 1/2 or 1/3 of the pitch in >= 50 % of groups). Statuses: COUNTED, NO_INTEGER, SUBHARMONIC_RISK, UNANCHORED, UNRESOLVED. The internal peak count of the run (n_peaks) is recorded as a cross-check, never as the count.
- Threads: OMP/BLAS 3, fetch 3. Parameters: `{"w_s": 14.0, "reject_below_ws": 0.8, "accept_max_ws": 2.0, "class_sheet": 1.4, "class_pair": 2.5, "sd": 2.0, "si": 16.0, "coh_min": 0.3, "energy_min": 0.2, "stride": 4, "tile": 64, "tile_dev_deg": 15.0, "ytilt_deg": 15.0, "ray_dev_deg": 15.0, "ray_len": 320, "ray_dx": 8, "min_run": 3, "dip_mad": 3.0, "gap_frac": 0.3, "width_frac": 0.5, "min_rays": 6, "group_dx": 128, "min_group_rays": 3, "min_groups": 6, "min_cycles": 1.5, "line_contrast": 1.5, "edge_sigma": 1.0, "edge_trim": 4, "taper": 0.5, "line_frac": 0.5, "smooth": 1.5}`

## 2. Self-test on synthetic fused slabs (W1 of item 4)

Generator (hashed `7ab7c38b436c0dc0`, seed 1): 16 x 384 x 192 slabs, k = 2..8 sheets of nominal thickness U(10, 18) vox (per-sheet jitter +-0.5) at zero gap; contact interfaces = density dips of depth U(0.10, 0.50) x (sheet - gap) contrast and width 1.5-3 vox; per-sheet density +-0.06; half-layer modulation period 4 vox (amp 0.02-0.08); fibre-bundle texture period 6-12 vox along the normal (amp 0.02-0.08) and in-plane in x and y (amp 0.03-0.10, phase random per sheet); tilt_x U(-12, 12) deg, y-tilt U(-12, 12) deg, undulation 0-4 vox; embedded between 1-3 gap-resolved sheets per side (gaps 6-40 vox, gap level 0.12-0.28 of full scale, sheet 0.55-0.80); 3-D Gaussian blur sigma U(0.6, 1.2); noise sigma U(0.03, 0.10); uint8. 210 slabs (30 per k).

**Bar W1 (count within +-1 of k on >= 90 % of slabs): pass fraction 0.676 -> FAIL.**

| stratum | n | within +-1 |
|---|---|---|
| k = 2 | 30 | 0.17 |
| k = 3 | 30 | 0.70 |
| k = 4 | 30 | 0.73 |
| k = 5 | 30 | 0.80 |
| k = 6 | 30 | 0.77 |
| k = 7 | 30 | 0.73 |
| k = 8 | 30 | 0.83 |
| t < 0.8 w_s (11.2 vox) | 33 | 0.212 |
| t >= 0.8 w_s | 177 | 0.763 |
| noise < 0.065 | | 0.689 |
| noise >= 0.065 | | 0.663 |

Status counts (main suite): `{"COUNTED": 135, "NO_INTEGER": 22, "SUBHARMONIC_RISK": 5, "UNANCHORED": 1, "UNRESOLVED": 47, "NOT_FOUND": 0}`. Integer claimed AND correct within +-1: 0.595. |count - k| p50 0.18, p90 1.682 (claimed runs); claimed error p50 0.19; true k inside the reported count range (+-0.5): 0.89.

Wrong integers (claimed integer off by >= 2): [{"k": 4, "t": 11.7, "integer": 2, "count": 1.95, "count_err": 0.11, "pitch_p50": 23.49, "noise": 0.083, "subharmonic_flag_frac": 0.1}, {"k": 4, "t": 10.56, "integer": 2, "count": 1.89, "count_err": 0.1, "pitch_p50": 22.07, "noise": 0.096, "subharmonic_flag_frac": 0.0}, {"k": 4, "t": 10.16, "integer": 2, "count": 1.83, "count_err": 0.04, "pitch_p50": 22.1, "noise": 0.082, "subharmonic_flag_frac": 0.0}, {"k": 5, "t": 11.21, "integer": 3, "count": 2.97, "count_err": 0.97, "pitch_p50": 18.52, "noise": 0.092, "subharmonic_flag_frac": 0.0}, {"k": 7, "t": 10.02, "integer": 3, "count": 2.7, "count_err": 0.09, "pitch_p50": 25.87, "noise": 0.041, "subharmonic_flag_frac": 0.0}, {"k": 7, "t": 11.38, "integer": 5, "count": 5.29, "count_err": 0.08, "pitch_p50": 15.06, "noise": 0.054, "subharmonic_flag_frac": 0.0}, {"k": 7, "t": 11.16, "integer": 3, "count": 3.03, "count_err": 0.06, "pitch_p50": 25.66, "noise": 0.039, "subharmonic_flag_frac": 0.0}, {"k": 7, "t": 10.65, "integer": 3, "count": 3.13, "count_err": 0.4, "pitch_p50": 23.45, "noise": 0.037, "subharmonic_flag_frac": 0.2}, {"k": 8, "t": 10.94, "integer": 4, "count": 3.65, "count_err": 0.86, "pitch_p50": 23.67, "noise": 0.093, "subharmonic_flag_frac": 0.08}, {"k": 8, "t": 11.68, "integer": 3, "count": 3.28, "count_err": 0.99, "pitch_p50": 27.57, "noise": 0.061, "subharmonic_flag_frac": 0.43}]

Interface-contrast sensitivity sweep (dip depth fixed, everything else random, 36 slabs per depth; reported, no bar):

| dip depth (x contrast) | within +-1 | count claimed |
|---|---|---|
| 0.02 | 0.639 | 0.778 |
| 0.05 | 0.667 | 0.778 |
| 0.08 | 0.694 | 0.778 |
| 0.12 | 0.528 | 0.778 |
| 0.2 | 0.611 | 0.75 |
| 0.3 | 0.611 | 0.75 |

Negative control (y-tilt 18-28 deg -> rays inadmissible): 20 slabs, counts claimed 1, integers claimed 1 -> FAIL.

Figure: `selftest_profiles.png` (profiles, runs, group autocorrelations). Full table: `selftest.json`. Wall time 889 s.

## 3. Real window, PHerc0268 level 0 (8.64 um)

Window y 5820..5835 (16 sections), z 7936..8704, x 1280..2304 (chunks 128^3, 48 of 48 present, 4.4 s, 13 MB); slab sha256 `25b416f65ff6e968033e85c2b16f67214df6e8ccd4f72397ba5d5ea7f7b5cd4e`. Tiles admissible 94 of 192 (rejections {"normal varies >= 15 deg": 66, "mask": 10, "y-tilt > 15 deg": 22}). Rays 11984 (cut 48). SHEET-class run width at half contrast: n 12604, p10 5.0, p50 9.0, p90 16.8 vox (43, 78, 145 um). Ray runs: PAIR 8972, FUSED 8182; pooled runs 1211, of which 267 with >= 6 rays. Statuses (>= 6 rays): {"COUNTED": 8, "NO_INTEGER": 2, "SUBHARMONIC_RISK": 0, "UNANCHORED": 23, "UNRESOLVED": 234}.

Runs with a pitch (window coordinates = offsets from z 7936, x 1280; T and pitch in um; count +- error = half the p10-p90 range; integer only for COUNTED):

| z | x | class | rays | groups w/ pitch | T um | T / w_s | pitch um | count | range | err | integer | status | anchored | n_peaks p50 | subharm. flag | line contrast p50 | rejected periods p50 vox (n) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 648 | 136 | FUSED | 78 | 13/14 | 569 | 4.70 | 129 | 4.40 | [3.6, 5.26] | 0.83 | 4 | COUNTED | 0.50 | 1.0 | 0.23 | 2.06 | 4.69 (101) |
| 160 | 187 | FUSED | 87 | 8/11 | 360 | 2.98 | 128 | 2.82 | [1.82, 3.2] | 0.69 | 3 | COUNTED | 0.75 | 1.0 | 0.0 | 9.06 | 4.15 (30) |
| 743 | 338 | PAIR | 92 | 7/16 | 306 | 2.53 | 162 | 1.90 | [1.75, 2.19] | 0.22 | 2 | COUNTED | 0.89 | 1.0 | 0.29 | 1.90 | 4.61 (66) |
| 158 | 433 | PAIR | 72 | 7/14 | 264 | 2.18 | 154 | 1.72 | [1.58, 1.99] | 0.21 | 2 | COUNTED | 0.75 | 1.0 | 0.0 | 2.13 | 4.71 (37) |
| 430 | 682 | PAIR | 112 | 9/16 | 296 | 2.44 | 173 | 1.71 | [1.52, 2.31] | 0.40 | 2 | COUNTED | 0.58 | 1.0 | 0.0 | 2.08 | 4.51 (58) |
| 424 | 689 | FUSED | 87 | 14/16 | 406 | 3.35 | 164 | 2.47 | [2.01, 3.58] | 0.79 | 2 | COUNTED | 0.82 | 1.0 | 0.29 | 1.89 | 5.25 (77) |
| 428 | 819 | PAIR | 63 | 8/12 | 268 | 2.21 | 117 | 2.28 | [2.02, 2.48] | 0.23 | 2 | COUNTED | 0.80 | 1.0 | 0.0 | 2.46 | 4.65 (45) |
| 166 | 1000 | PAIR | 111 | 8/16 | 302 | 2.49 | 152 | 1.99 | [1.64, 2.74] | 0.55 | 2 | COUNTED | 0.67 | 1.0 | 0.12 | 3.13 | 4.97 (53) |
| 475 | 63 | FUSED | 111 | 15/16 | 680 | 5.62 | 154 | 4.41 | [3.65, 5.81] | 1.08 | None | UNANCHORED | 0.21 | 2.0 | 0.13 | 2.23 | 4.94 (107) |
| 491 | 72 | FUSED | 138 | 15/16 | 575 | 4.75 | 145 | 3.96 | [2.97, 5.29] | 1.16 | None | UNANCHORED | 0.07 | 2.0 | 0.07 | 2.26 | 4.54 (116) |
| 543 | 96 | FUSED | 107 | 15/16 | 773 | 6.39 | 137 | 5.63 | [4.72, 7.79] | 1.54 | None | UNANCHORED | 0.37 | 2.0 | 0.0 | 2.79 | 4.74 (128) |
| 93 | 107 | PAIR | 107 | 11/16 | 261 | 2.16 | 122 | 2.15 | [1.94, 2.29] | 0.18 | None | UNANCHORED | 0.46 | 1.0 | 0.0 | 2.80 | 4.96 (40) |
| 228 | 109 | FUSED | 72 | 9/12 | 420 | 3.47 | 175 | 2.40 | [2.1, 3.95] | 0.93 | None | UNANCHORED | 0.00 | 1.0 | 0.0 | 3.00 | 5.23 (55) |
| 589 | 124 | FUSED | 307 | 16/16 | 1066 | 8.81 | 130 | 8.23 | [6.25, 9.07] | 1.41 | None | NO_INTEGER | 0.52 | 2.0 | 0.12 | 1.78 | 5.19 (128) |
| 467 | 136 | FUSED | 104 | 7/16 | 403 | 3.33 | 124 | 3.25 | [1.77, 3.37] | 0.80 | None | UNANCHORED | 0.00 | 1.0 | 0.57 | 2.03 | 4.79 (68) |
| 691 | 191 | FUSED | 79 | 14/16 | 912 | 7.54 | 162 | 5.61 | [4.69, 8.67] | 1.99 | None | UNANCHORED | 0.00 | 2.0 | 0.21 | 2.10 | 5.3 (128) |
| 224 | 220 | PAIR | 85 | 6/11 | 271 | 2.24 | 169 | 1.61 | [1.5, 1.84] | 0.17 | None | UNANCHORED | 0.26 | 1.0 | 0.0 | 3.78 | 4.46 (26) |
| 159 | 247 | FUSED | 104 | 12/16 | 366 | 3.03 | 134 | 2.72 | [2.06, 3.36] | 0.65 | None | UNANCHORED | 0.00 | 1.0 | 0.25 | 2.14 | 4.9 (48) |
| 670 | 282 | FUSED | 56 | 10/15 | 418 | 3.46 | 119 | 3.51 | [1.86, 4.27] | 1.21 | None | UNANCHORED | 0.33 | 1.0 | 0.1 | 2.00 | 5.21 (88) |
| 515 | 321 | FUSED | 643 | 8/16 | 497 | 4.11 | 176 | 2.83 | [2.54, 3.56] | 0.51 | None | UNANCHORED | 0.23 | 1.0 | 0.0 | 1.79 | 4.79 (94) |
| 32 | 419 | FUSED | 88 | 7/14 | 397 | 3.28 | 164 | 2.42 | [2.14, 4.05] | 0.96 | None | UNANCHORED | 0.00 | 1.0 | 0.0 | 2.71 | 4.65 (55) |
| 415 | 463 | FUSED | 102 | 9/16 | 534 | 4.42 | 120 | 4.47 | [2.69, 4.93] | 1.12 | None | NO_INTEGER | 0.83 | 1.0 | 0.11 | 1.64 | 4.97 (109) |
| 539 | 493 | FUSED | 60 | 12/16 | 549 | 4.54 | 162 | 3.39 | [2.38, 4.49] | 1.06 | None | UNANCHORED | 0.42 | 2.0 | 0.17 | 2.25 | 5.03 (125) |
| 495 | 568 | FUSED | 48 | 10/12 | 453 | 3.74 | 134 | 3.38 | [2.81, 3.72] | 0.45 | None | UNANCHORED | 0.00 | 1.0 | 0.0 | 1.85 | 5.22 (78) |
| 155 | 661 | FUSED | 30 | 9/10 | 509 | 4.21 | 110 | 4.62 | [2.99, 4.77] | 0.89 | None | UNANCHORED | 0.00 | 1.0 | 0.11 | 2.33 | 5.18 (52) |
| 262 | 733 | PAIR | 87 | 6/16 | 249 | 2.06 | 109 | 2.29 | [1.9, 2.45] | 0.27 | None | UNANCHORED | 0.26 | 2.0 | 0.0 | 3.25 | 5.14 (36) |
| 431 | 823 | FUSED | 81 | 6/16 | 302 | 2.50 | 102 | 2.96 | [1.44, 3.06] | 0.81 | None | UNANCHORED | 0.31 | 1.0 | 0.0 | 1.99 | 4.91 (62) |
| 320 | 857 | FUSED | 1807 | 45/48 | 412 | 3.41 | 150 | 2.76 | [2.16, 3.57] | 0.70 | None | UNANCHORED | 0.20 | 1.0 | 0.07 | 1.77 | 5.27 (382) |
| 542 | 869 | FUSED | 768 | 8/16 | 361 | 2.99 | 176 | 2.06 | [1.87, 2.27] | 0.20 | None | UNANCHORED | 0.40 | 1.0 | 0.0 | 1.59 | 5.24 (111) |
| 221 | 916 | FUSED | 346 | 14/16 | 378 | 3.12 | 154 | 2.46 | [2.25, 3.27] | 0.51 | None | UNANCHORED | 0.30 | 2.0 | 0.07 | 1.83 | 5.0 (116) |
| 137 | 921 | PAIR | 32 | 6/6 | 310 | 2.56 | 189 | 1.64 | [1.51, 1.86] | 0.18 | None | UNANCHORED | 0.00 | 1.0 | 0.0 | 2.13 | 4.77 (21) |
| 324 | 965 | FUSED | 74 | 8/16 | 310 | 2.57 | 104 | 2.98 | [2.13, 3.2] | 0.54 | None | UNANCHORED | 0.21 | 1.0 | 0.25 | 2.41 | 4.79 (47) |
| 534 | 978 | PAIR | 301 | 7/16 | 265 | 2.19 | 103 | 2.58 | [2.25, 2.7] | 0.23 | None | UNANCHORED | 0.23 | 1.0 | 0.14 | 1.83 | 5.51 (63) |

Figure: `real_profiles.png`. Full record (tiles, every pooled run with its groups and rejected periods): `real_y5820.json`. Fetch script used: class L0.slab of tools/umb/core_native.py, 3 threads.

## 4. Findings and deviations (read before the numbers above are used)

1. **Bar W1 FAILS as written** (0.676 within +-1 over k = 2..8, t = 10-18 vox). Stratified: k = 2 0.17 (a two-sheet run has one contact and no periodicity; the periodogram of a single pulse has no line, so the periodicity method is the wrong instrument for PAIR runs and this is intrinsic, not a tuning matter); t < 0.8 w_s = 11.2 vox 0.21 (the declared rejection band contains the sheet period itself; the fundamental is rejected by rule and what survives is its 2x sub-harmonic, which the guard catches only when the rejected line is the stronger one); k >= 3 and t >= 11.2 vox: 0.84 (n 155); k >= 4 and t >= 11.2: 0.86. Of the failures at t >= 11.2, 30 of 42 are UNRESOLVED (fewer than 6 of 16 ray groups reach line contrast 1.5), i.e. withheld, not wrong. Wrong integers (off by >= 2) occur at t = 10.2-11.7 vox with pitch = 2t and small quoted errors: the quoted error (p10-p90 over groups) does not cover a consistently mis-picked line. No threshold was lowered to approach the bar; the thresholds are those in `params`.
2. **The phantom range conflicts with the rejection rule**: thickness 10-18 vox overlaps 0.8 w_s = 11.2 vox (33 of 210 slabs below it). Either the rule or the phantom range must be amended by declaration before W1 is re-run; this tool implements the rule as declared.
3. **What the method actually measures**: the interface-contrast sweep (dip depth 0.02-0.30 x contrast) shows NO dependence of the pass rate on the contact-dip depth (0.74-0.86 for k >= 3, t >= 11.2 at every depth). The sheet period is therefore carried by what changes at every contact in this generator: the per-sheet density level (+-0.06) and the per-sheet random phase of the half-layer and fibre textures, which the interface-energy signal |d/ds G_1(density)| turns into pulses. If real fused sheets were identical in density and texture phase across a contact, the method would see nothing there. The real-window lines (section 3, contrast 1.6-9 over the floor, autocorrelation at the pitch <= 0.1) are evidence of SOME change repeating at 100-190 um inside those runs, not evidence of what the change is.
4. **y-tilt negative control FAILS 1 of 20**: a slab with true y-tilt 18.1 deg was admitted (estimated tilt < 15 deg by the structure tensor, which underestimates the y-tilt of a 16-section slab); its count was 8.3 +- 0.11 for k = 8 (the cos correction uses the estimated tilt). The 15-deg admissibility gate therefore admits true tilts up to about 18 deg; the other 19 slabs (18-28 deg) had no admissible tile.
5. **Real window**: the SHEET-class run width at half contrast is p50 9.0 vox (78 um), below the survey's w_s = 14 vox (122 um, half-prominence width on the mean image of 18 vertical profiles). The class limits were kept at the declared w_s = 14 vox; the window-measured width is reported, not used. 8 runs COUNTED (integers 2, 2, 2, 2, 2, 2, 3, 4), 2 NO_INTEGER, 23 UNANCHORED, 234 UNRESOLVED of 267 pooled runs with >= 6 rays; pitches 102-189 um (0.84-1.55 w_s) with line contrast p50 1.6-9.1; the internal half-contrast peak count (n_peaks p50 1-2) is below the periodicity count in every run, as expected when the contacts do not reach half contrast. These are numbers about one 6.6 x 8.8 mm x 0.14 mm window; nothing is claimed beyond them and no sheet index crosses any of these runs.
6. **Environment deviation**: /opt/hv was built with the package list of docker/env/setup_env.sh step 4 (plus matplotlib) directly, not by running the whole script (its docker image pull and volume-cartographer build are not needed by this tool and would have taken ~15 min and several GB).
7. **Design departures from the literal brief, all recorded in the module header**: the periodicity is measured on the interface-energy signal rather than on the raw density (the raw-density spectrum of a stack with per-sheet density levels has a null at the sheet period and its maximum near twice it, so the raw-density rule picked 2x-3x the sheet period on the first synthetic runs); periods > 2 w_s are rejected in addition to < 0.8 w_s; the ray's own end transitions are trimmed; the pitch is the shortest accepted line above half the strongest (a fundamental is the shortest member of its harmonic series); rays are averaged in groups (periodograms, phase-free) because single rays at the real noise level carry no usable line; the p10-p90 error is over ray groups, not single rays.
