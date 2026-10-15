Provenance: Project HERCULES | owner the owner | [id removed]

# Pre-registration: PHerc0500P2 registration, attempt 2 (non-affine field)

This is committed and pushed BEFORE any field is fitted and before any block of the 16 new patches is read.

Attempt 1 (affine; prereg_heldout.md) was evaluated once and FAILED on median r: 0.834 < 0.85. RMS was 0.82 vox (PASS) and the control PASSED (heldout_result.json, commit fee8ba5).

Following the REG-0841-NA precedent and the task brief ("try an affine first, then a leave-one-out-selected smooth field"), attempt 2 uses a non-affine map, selected by leave-one-out on the 40 correspondences already measured (24 fit + 16 attempt-1 held-out) and validated once on 16 NEW patches.

New patch plan: `new_heldout_plan.json`, sha256 `eecd71f964f248530a03cf2e10fd0a9657d7bed9a366bb0adb0671b27cd38297`. Seeded rule inside the file: seed 20260927, 4 z-quartiles x 4 radius-quartiles, one site per cell, and every site at least 32 vox from all 40 earlier blocks.

| id | centre (x, y, z), 9 um level-0 vox |
|---|---|
| N00 | [1664.0, 1792.0, 3328.0] |
| N01 | [1664.0, 1408.0, 2080.0] |
| N02 | [1280.0, 1408.0, 3280.0] |
| N03 | [896.0, 1408.0, 4000.0] |
| N04 | [1408.0, 1664.0, 4576.0] |
| N05 | [1280.0, 1920.0, 4288.0] |
| N06 | [896.0, 1664.0, 5008.0] |
| N07 | [768.0, 1664.0, 4960.0] |
| N08 | [1408.0, 1664.0, 5056.0] |
| N09 | [1152.0, 1792.0, 5056.0] |
| N10 | [1152.0, 1536.0, 5392.0] |
| N11 | [3072.0, 1920.0, 5536.0] |
| N12 | [1664.0, 1920.0, 5968.0] |
| N13 | [2048.0, 2048.0, 6064.0] |
| N14 | [2176.0, 1920.0, 5872.0] |
| N15 | [768.0, 1792.0, 5680.0] |

## Map (frozen form)

f(p) = A (p + u(p)) + c, where A and c are the attempt-1 affine (model_final.json, sha256 9a777170...).

The displacement u (9 um vox) is fitted to the 40 residual displacements d_i = A^-1 (q_i - c) - p_i. The candidate forms are the same as in reg0841na `select_field.py`:
- the Q polynomial (features x, y, z, 1, x^2, xy, y^2 of p/1000);
- scipy RBFInterpolator with thin_plate_spline or linear kernels (coords /1000, degree 1), smoothing in {0, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}.

**Selection.** Minimum leave-one-out RMS over the 40 points. Ties within 0.01 vox of the best are broken in this order: prefer Q, then larger smoothing, then the linear kernel.

The selected field goes to `field_final.json`, which is committed and pushed. Only then are the new blocks read.

## Measurement and bars

Identical to prereg_heldout.md, with r = NCC at zero shift under f, and the same prefilter, level handling and control. The 16 NEW patches are evaluated ONCE.
- PASS requires median r >= 0.85, RMS of abs(d9) <= 1.5 vox, and the control (median drop >= 0.30 with >= 14 of 16 clear).
- If attempt 2 fails, the registration is recorded as FAIL. No further attempt is made without an orchestrator decision.

