Provenance: Project HERCULES | owner the owner | [id removed]

# reg0841-NA: pre-registration (committed before any non-affine analysis and before any new-patch CT read)

Already known before this file (from the reg0841 task, disclosed): the affine (affine_final.json, sha256
74f239e4...), the 40 old correspondences, and fit-only LOO of polynomial models on the old 24 (model_loo.json).
No non-affine field has been fitted on the 40 points, and no new held-out patch has been read.

## New held-out set
logs/sib/reg0841na/new_heldout_plan.json (sha256 51b146d1bb8b18025557b39d150f3f429153ec7f6fcb4958f32ebfb5ead4e8fe).
The set comes from tools/sib/reg0841na/plan_new_heldout.py with seed 20260926: 16 sites, one per z-quartile x radius-quartile cell.
Blocks keep >= 32 vox from the 40 old blocks, and the fail-closed point-to-surface J clearance is >= 156 vox (minimum 170.9).

## Model (fitted on the 40 old patches only)
Data: q_i = the correspondence measured by converged phase correlation under the frozen affine, which is q_meas in
logs/sib/reg0841/fit_eval_result.json (24) and heldout_result.json (16). Residual field samples u_i = d_i (9 um vox):
q_i = A (p_i + d_i) + c.
Map: f(p) = A (p + u(p)) + c, with u a smooth field. Candidates:
- (T) scipy RBFInterpolator, kernel thin_plate_spline, degree 1, coordinates /1000, smoothing in {0, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100};
- (L) the same with kernel linear (the 3-D biharmonic spline), same smoothing grid;
- (Q) the quadratic polynomial M3 (affine + x^2, xy, y^2 terms in all components).
The candidate and smoothing with the lowest 40-point leave-one-out RMS |u_i - u_-i(p_i)| is chosen; ties within 0.01 vox go to the larger smoothing / simpler model.
The choice is frozen and committed (hash in runs.jsonl) before any new-patch analysis.

## Held-out metrics (16 new patches, frozen field, no refit)
- r = Pearson NCC over the 48x256x256 block: raw 9 um vs the rescan prefiltered with a Gaussian of sigma F/2, trilinearly sampled at f(p) for every voxel,
  zero shift. u is evaluated on a 3x5x5 lattice spanning the block and trilinearly interpolated between lattice nodes.
- Residual d_f = the converged iterative 3-D phase-correlation shift under the local linearisation of f at the block centre (9 um vox).
- Control: the rescan sampled at f(p + (pitch/2) n) and at f(p - (pitch/2) n), with n and pitch from reg_core.sheet_normal_pitch; the higher NCC counts.

Bars:
- median r >= 0.85
- RMS |d_f| <= 1.5 vox (9 um); RMS in rescan vox is also reported
- control: median (r - r_ctrl) >= 0.30 and r_ctrl < r - 0.15 on >= 14/16

Secondary (not deciding): the same NCC after a sigma 1 vox Gaussian on both blocks.

## Round trip 9 -> 2.4 -> 9 um (bar < 0.5 vox)
Inverse by fixed-point iteration p <- A^-1 (q - c) - u(p) (at most 50 iterations, until the step is < 1e-6).
Test points: 2000 seeded random points (seed 20260927) inside the scroll mask (9 um L4 > 0) within the band, plus the
56 patch centres. Report max and RMS of |p_rt - p|. PASS if max < 0.5 vox.

## Organizer-mapping offsets (ASK.md defaults)
At each canvas point: p9 = the 9 um mesh point, and q2_org = the 2.4 um mesh point at the UV-corresponding canvas position (o = 10).
Displacement D = f^-1(q2_org) - p9 (9 um vox), split into the mesh-normal component and the in-surface component.
Also reported: the same with q2_org = the organizer mesh affine.
Point sets:
- the centres of the geometric superset of the fold-A tiles (ASK 1);
- the 18 dropped tiles;
- the 5 J-window centres (mesh geometry and the field only).
Reported: median, max, the normal and tangential components, and the field's LOO uncertainty.
