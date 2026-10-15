Provenance: Project HERCULES | owner the owner | [id removed]

# PROPOSAL-SG-CODE-1 (for the orchestrator to declare, amend or reject)

Proposal only. The builder session does not declare anything. The bars are those of RULES.md DECL-SG and DECL-EMPNULL, copied into tools/sib/sg/sg_constants.py with the item cited on each line. No bar is changed in code.

## A. Proposed declaration text (METRIC-HASH style)

SG code (tools/sib/sg/, runner sg_gate.sg_check, CLI sg_cli.py), hashed with `python -m hercules.records.codehash` before any candidate exists (hashes in logs/sib/sg/sg_report.json, key `code_hashes`). It evaluates DECL-SG items 1, 2, 3, 4, 5, 6, 7, 9, 11, 13 and the rotation part of 14, the DECL-EMPNULL discovery rule and its FDR calibration, and the R rule. Items 0, 8, 10, 12 and the RAW-F/B-profile and unit-test parts of 14 are taken only as attestations that carry a RULES.md record id. A missing input or attestation gives NOT_EVALUATED, which never counts as a pass. SG passes only if discovery, its calibration, R and items 0-14 are all PASS, NOT_APPLICABLE (items 9 and 13 only, by their own conditions) or ATTESTED_PASS. K7 still needs the owner to be present; code never evaluates that.

## B. Interpretations that need a ruling (the code implements the stricter reading)

| # | DECL wording | Implemented | Alternative (less strict) |
|---|---|---|---|
| B1 | DECL-EMPNULL discovery: "non-text-order agreed count <= 1" (the task brief says "F_B <= 1") | Gate on the non-text AGREED count (the declared text). Per-reader F_B (known namings in the non-text order, as hercules.scorer.score defines it) is reported as `F_B_per_reader` and `F_B_max`. | Gate on max per-reader F_B <= 1 (stricter still). A ruling is needed on which one binds. |
| B2 | SG 2 "a blank gets <= 1 naming" | Total namings on the blank, summed over every reader in the batch, unknown characters included. | Per-reader mean (as D1 used, `blank_namings_mean`), or per-reader max. |
| B3 | SG 3 "<= 2 namings in R" (opposite order) | Total namings with their point inside R, summed over readers, unknown characters included. | Agreed count, or per reader. |
| B4 | SG 4 "+-1 slice: >= 80 % re-confirmed" | The -1 and +1 re-reads must each re-confirm >= 80 % of the SG letters (same kind, 150 px, one-to-one). | Pooled over both offsets, or the better one. |
| B5 | SG 5 "names >= 50 % at the same places (150 px)" | Same place AND same identity (the scorer's letter-matching rule everywhere). | Place only. |
| B6 | SG 7 "NCC >= 0.8" | Signed NCC. An intensity-inverted copy (NCC -1) is not flagged. It is still visible as `max_ncc` per letter. | abs(NCC) >= 0.8. |
| B7 | SG 7 "training-label patch" | The caller supplies every patch at the crop's px/mm. When a patch is smaller than a crop, both are compared on the largest centred disc that fits (d = min of the sides). A crop that is flat on its disc is not evaluable, and the item FAILs. | Declared resampling rule and patch geometry. |
| B8 | SG 11 "letter heights 2-4 mm" | Median height of the agreed letters that lie in qualifying rows. Each agreed letter's box is the median of its members' reader-drawn boxes, converted to mm with px/mm from metadata.json. | Every letter within 2-4 mm, or a fraction of them. |
| B9 | SG 11 rows | Coded row finder: centres <= 2.5 mean heights apart horizontally and <= 0.5 vertically link. Rows are connected components with >= 3 letters. The baseline is an OLS line through the box bottoms. The pitch is measured between consecutive qualifying baselines at the mean x, times cos(mean angle). CV is the population standard deviation over the mean. With exactly 2 rows there is one pitch, so CV = 0. | A declared alternative row rule. Note that 2 rows make the CV bar vacuous. |
| B10 | R "computed by code from the discovery namings" | Axis-aligned to the render horizontal. Placement maximises the agreed discovery letters inside, then 3-reader letters, then the minimum letter-to-edge margin (the set is centred in its feasible range), then aspect nearest 1, then wider, then smallest y0 and x0. Widths are scanned in 0.25 mm steps, plus the square and both 2:1 limits. | A rotated R, or other tie-breaks. |
| B11 | R "declared before confirmation reads" | sg_check requires `R_declared = {rect, record}` and FAILs unless it equals the recomputed R within 1e-6 px. The timing itself is the orchestrator's to record. | None. |
| B12 | "letters in R" | A naming counts when its point (x, y) lies in the closed rectangle R. Namings are filtered before clustering. | Filter the groups by their mean position instead. |
| B13 | SG 1 "fresh readers" | Confirmation reader ids must not appear among the discovery reader ids. Other re-reads are not checked. | Freshness across every SG read. |
| B14 | DECL-EMPNULL reader-model mix | Enforced for the discovery and confirmation reads when `available_reader_models` lists >= 2 versions. | Enforce on every SG read. |
| B15 | Inclusive bars on floating-point quantities | Compared with a relative tolerance of 1e-9 (for 4 mm that is 4e-9 mm), so an exact boundary value is not failed by round-off. | None. |

## C. Measured risk that needs a decision before any SG attempt (SG 7 false flags)

Synthetic null (logs/sib/sg/copytest_null.json; independent Gaussian-smoothed fields, so every flag is false by construction). The chance maximum of the SG 7 statistic, taken over 24 rotations, all placements and the label patches, depends steeply on n_eff = disc area / autocorrelation half-max area:
n_eff <= ~13 gave a false flag on every crop; n_eff >= ~30 gave none with 100 patches. The chance maximum rises with the number of patches (1000-patch cells in the JSON).
Consequence: with small label patches or smooth ink maps, SG 7 can FAIL a genuine letter by chance. The code does not change the bar. It reports `n_eff_median` and per-letter `n_eff` as a diagnostic.
Proposed validation (measurable, never a bar change): before any SG attempt, run the copy test on letter crops from >= 40 empirical-null tiles against the real training-label patch set, and record the false-flag count. If it is > 0, record "SG 7 uninformative at this geometry" and settle the patch definition (B7) by declaration before any candidate is read.

## D. What the orchestrator needs to do next

1. Rule on B1-B15, amending the code by declaration if needed. Then hash the code into a METRIC-HASH entry before any candidate exists.
2. Run the SG 7 empirical-null check in section C on the real label-patch set once one is defined (items 8 and 7 need the training-patch inventory).
3. Supply the attested items (0, 8, 10, 12, 14 profile, 14 tests) from their own chains. This code only checks that a record id is present.
