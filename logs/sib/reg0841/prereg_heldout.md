Provenance: Project HERCULES | owner the owner | [id removed]

# reg0841 held-out evaluation: pre-registration (written before any held-out patch is analysed)

Written 2026-09-25 (UTC) after one fit patch (P00) was run as a timing/sanity check
(P00: NCC 0.755 at zero shift under the mesh affine, 0.809 after its local shift). No held-out
patch had been analysed yet. The held-out blocks may already be on disk, but none has been compared.

Patch plan: logs/sib/reg0841/patch_plan.json (16 role == "heldout" sites, frozen before any level-0 read).
Affine: logs/sib/reg0841/affine_final.json, produced from the 24 fit patches only; its sha256 is
recorded in runs.jsonl before the held-out run.

Per held-out patch, all under the final affine, with no per-patch refit:
- r (PRIMARY) = Pearson NCC over the full 48x256x256 block between the raw 9 um block and the rescan
  prefiltered with a Gaussian (sigma = F/2 rescan vox), trilinearly sampled at the mapped 9 um voxel centres, at zero shift.
- residual = the converged iterative 3-D phase-correlation shift d (9 um vox), also expressed in rescan vox as |A d|.
- r_ctrl (shifted control): the same NCC with the rescan sampled at p + (pitch/2) n, where n is the
  block's structure-tensor normal and pitch is the first autocorrelation period along n (reg_core.sheet_normal_pitch).
  A second control at p - (pitch/2) n is also reported. The worse (higher) of the two is used for the criterion.

Bars (from the task):
- held-out median r >= 0.85
- RMS |d| <= 1.5 vox. The unit is unstated, so both interpretations are reported: 9 um vox (primary, the
  frame the task model is written in) and rescan vox (strict).
- control "drops NCC clearly", operationalised here BEFORE seeing data as: median (r - r_ctrl) >= 0.30 AND
  r_ctrl < r - 0.15 on >= 14 of 16 patches.

SECONDARY (reported, never deciding): r_lp = the same NCC after also blurring both the 9 um block and the
sampled rescan block with a Gaussian of sigma = 1.0 (9 um vox) (matched low-pass), and its shifted-control
analogue. Chosen now, without looking at any held-out numbers and without a sweep.

## Addendum 1 (written after the fit run, still before any held-out patch is analysed)

Fit-patch findings (fit_result.json, model_loo.json): the pass-2 affine leaves fit residuals of RMS 1.57
9 um vox (leave-one-out 1.90). They are systematic, not noise: phase-correlation repeatability between
passes is mostly < 0.2 vox, and the rescan sits ~2 vox lower in z near the scroll centre than at the
periphery. Leave-one-out on the 24 fit correspondences only: M0 affine 1.895, M1 affine + rho^2 z term 1.274,
M2 1.283, M3 affine + (x^2, xy, y^2) in all outputs 0.910, M4 full quadratic 1.002.

Held-out evaluation, unchanged for the PRIMARY: the bars are decided on M0 (the task's affine model,
affine_final.json) exactly as above.
SECONDARY / EXPLORATORY (reported, never deciding the task bars): M1 and M3, refitted on the same 24 fit
correspondences. Per held-out patch: residual = |q_meas - f(p_c)| (9 um vox via A^-1), where q_meas =
A (p_c + d) + c is the correspondence measured under the frozen affine; r_model = NCC as for r, with the rescan
sampled under the model's local linearisation (Jacobian and value at the block centre).
Selection of M1/M3 used fit-patch leave-one-out only; the held-out set is used once.
