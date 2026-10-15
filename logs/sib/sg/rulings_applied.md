Provenance: Project HERCULES | owner the owner | [id removed]

# Rulings on PROPOSAL-SG-CODE-1: how each was applied

Rulings received 2026-09-25T19:09:30Z (scheduled check-in "Rulings to sib sg"). Code is in `tools/sib/sg/pkg/src/hercules/sg/` (merge layout; ASK.md Q1), and tests are in `tools/sib/sg/pkg/tests/test_sg_*.py`. The version was bumped to `hercules-sg-1.1.0`. Merged-layout suite: 719 passed, 7 skipped (`run_merged_tests.sh`, logged in runs.jsonl).

| Ruling | Change | Where | Test where it alone fails | Commit |
|---|---|---|---|---|
| B1 | Discovery needs the non-text agreed count <= 1 AND the max per-reader F_B <= 1. The calibration applies the same full rule (ASK Q3). | `gate.discovery_rule`, `calibrate_discovery_k`, `constants.DISCOVERY_FB_MAX` | `test_B1_per_reader_FB_fails_alone`; `test_B1_calibration_uses_full_rule`; `test_B1_unknown_nontext_namings_are_not_FB` | 7c83418 |
| B2, B3, B4, B5 | Unchanged (as implemented). | - | Existing tests | a8d0906 |
| B6 | A copy is |NCC| >= 0.8. Reported per letter: `max_abs_ncc`, `signed_ncc_at_max`, `max_signed_ncc`, `min_signed_ncc`. | `copytest.copy_test`, `constants.SG7_ABS_NCC` | `test_B6_inverted_copy_is_a_copy`; `test_B6_precomputed_abs` (runner) | 7c83418 |
| B7 | A crop is evaluable only if n_eff >= 30 in every patch-size group (ASK Q4); otherwise, or if the crop is flat, SG 7 FAILs. `copy_test_null_check` needs >= 40 null tiles and 0 false flags (INFORMATIVE). The runner requires a `copy_test_null` record for an SG 7 PASS. | `copytest.copy_test`, `copytest.copy_test_null_check`, `gate.sg_check` | `test_B7_crop_below_neff_floor_fails_closed`; `test_B7_floor_applies_per_patch_size_group`; `test_B7_copy_test_null_check`; `test_B7_copy_test_null_required`; `test_B7_precomputed_neff_floor` | 7c83418 |
| B8 | Height median in 2-4 mm AND >= 80 % of the letters in qualifying rows in 2-4 mm. Every letter's height is reported (`letter_heights_mm`, `row_letter_heights_mm`). | `gate.layout_metrics`, `constants.SG11_HEIGHT_FRACTION_MIN` | `test_B8_median_in_band_but_under_80_percent_fails`; `test_B8_fails_alone_via_runner` | 7c83418 |
| B9 | SG 11 needs >= 3 qualifying rows. With exactly 2, `pitch_cv_status` is NOT_EVALUATED and the item fails. Line-spacing statistics from the official 0139 labels are not computable: the labels are too sparse (PROPOSAL-SG-LINESPACING-1, ASK Q6). | `gate.layout_metrics`, `constants.SG11_MIN_ROWS_FOR_CV` | `test_B9_two_rows_fail_with_cv_not_evaluated`; `test_B9_fails_alone_via_runner` | 7c83418; statistics in this commit series |
| B10, B11, B12, B15 | Accepted as implemented. | - | Existing tests | a8d0906 |
| B13 | No reader id appears in two SG reads. The reads are discovery, confirmation, slice -1, slice +1, second lineage, re-trace, rotation, arm NULL, arm REV, arm CTRL and band sealers (ASK Q2). Top-level gate `readers_fresh`. | `gate.collect_reads`, `gate.readers_fresh`, `constants.FRESH_READS` | `test_B13_reader_reused_across_reads_fails_alone` (3 reads); `test_B13_arms_and_sealers_count` | 7c83418 |
| B14 | The model mix is enforced on every SG read listed under B13 when >= 2 versions are available. A reader without a recorded version fails its read. Top-level gate `model_mix`. | `gate.model_mix_all` | `test_B14_model_mix_every_read` (one read single-version; one reader unrecorded) | 7c83418 |
| Next (2) | Staged as `hercules.sg` with plain-pytest tests. `MERGE.md` gives the two `cp` commands. | `tools/sib/sg/pkg/` | `run_merged_tests.sh`: 719 passed, 7 skipped | 7c83418 |

Structural note on B1: a non-text agreed count >= 2 needs >= 2 readers who each name >= 2 known non-text letters, which already means max F_B >= 2. The agreed-count bar can therefore never fail on its own under B1; the F_B bar subsumes it. Both are coded as ruled.

Measured follow-ups, which need your attention and are not code changes:
- B8 may reject genuine text: 75-78 % of known-text letters fall in 2-4 mm (ASK Q5).
- The B7 floor still holds under |NCC| (0 false flags at n_eff >= 30; highest chance value 0.743), but the margin shrinks as the patch count grows (PROPOSAL-SG-LINESPACING-1, P3).

## Revision after the answers of 2026-09-25T19:41:05Z

| Ruling | Change | Where | Test where it alone fails | Commit |
|---|---|---|---|---|
| B8 (revised) | The binding bar is the literal DECL-SG 11 one: the median height of the agreed letters in qualifying rows lies in 2-4 mm. The fraction in 2-4 mm and every height are reported, with no bar (`SG11_HEIGHT_FRACTION_MIN = None`) until one is declared from REF reads of sealed known-text bank windows. Version `hercules-sg-1.2.0`. | `constants.SG11_HEIGHT_FRACTION_MIN`, `gate.layout_metrics` | `test_B8_median_alone_fails`; `test_B8_median_fails_alone_via_runner`; `test_B8_revised_fraction_reported_not_barred`; `test_B8_fraction_under_80_percent_passes_via_runner` | 5443aa6 |
| Q6 | Line spacing on organizer predictions: calibration only, labelled as organizer model output. | `tools/sib/sg/pred_spacing.py`, PROPOSAL-SG-LINESPACING-1 section 5 | `tests/sib_sg_label_spacing.py` (7) | this commit series |
