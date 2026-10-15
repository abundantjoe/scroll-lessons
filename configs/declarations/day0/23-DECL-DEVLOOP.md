DEV-LOOP metric (section 6.5), declared before any DEV data exists.
- DEV data: known text outside every sealed set, fold K, T/C4 shells and base-training papyrus, KD-tree certified (clean 0139, 0814 per-arm hold-out, 0009B outside KTLB-M, 0332/0500P2/1451 once confirmed).
- Metric: sigma_eq = the Gaussian blur sigma (mm) of the 2.4 um reference map that maximises Pearson r with the text-order model map on DEV windows (grid 0.00-0.60 mm in 0.025 mm steps, after registration, computed by code hashed in a METRIC-HASH entry before first use). Constraint: non-text-order blob-f180 on DEV blanks <= 0.0272.
- FINALIST: sigma_eq <= sigma_crit + 0.05 mm on >= 3 DEV scrolls. DEV ranks only; letters are claimed only from sealed blind reads. <= 2 finalists + NULL + REV + reference arm per sealed decision (K6).
- Default: no finalist.
