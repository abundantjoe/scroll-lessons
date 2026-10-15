New chain variant C2-NT and its C3 gate (a changed recipe after C3-R1-VERDICT FAIL; not a re-declaration of C2).
- Disclosure: this variant was chosen AFTER seeing that the base model without --tta-mirror scored forward 0.9968 / 0.99347 and reverse 0.5027 / 0.58142 inside the supervision mask on the two w040 crops already used (C3-RUN1, C3-R1-VERDICT). Those crops are excluded; the crop-choice code tools/c3/pick_crop_nt.py was written after those numbers existed and applies the same rule as DECL-C3-R1 with both earlier crops excluded. This gate is a fidelity check on base-trained papyrus only, never evidence of generalisation.
- C2-NT: identical to C2 (official infer CLI, both orders, batch 4, --no-compile, CPU) but WITHOUT --tta-mirror.
- Data: w040 as in DECL-C3; crop = output of tools/c3/pick_crop_nt.py (2048 px, 256 px grid, no overlap with crops (2048, 1152) and (2560, 4096), fully mesh-valid, maximum supervision pixels), run once, before any render or map of it exists.
- Metrics: as DECL-C3-R1 (tools/c3/fidelity.py, tools/c3/auc_eval.py with C3_X0/C3_Y0, METRIC-HASH-7; supervision-mask AUC).
- Bars (section 4.C3 values, unchanged): pooled render Pearson >= 0.999; C2-NT forward AUC >= 0.987 and reverse AUC < 0.60. Auditor re-derivation before the verdict.
- Consequence: PASS -> the D1 BASE arm uses C2-NT (base maps without TTA) and C2-NT replaces C2 wherever a 9 um base map is read; FAIL -> no 9 um base-map read until a new official checkpoint or chain passes C3 on fresh data; D1 then runs with RAW only.
- Default: FAIL at 24 h past 2026-09-27.
