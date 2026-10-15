Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (sib/tracer)

Earlier T0 items 1-8 are still open; their full text is in git history (commit b63d6ea). In short: L family (space_line_weight 0.1), T0 generations from meta, gate additions c3/c4, rejected cells count as filled, folds reported not gated, team bar vs m7 consistency, local normal-grid sync at T0, per-seed cache clearing.

## P4-N (DECL-P4-13), 2026-09-26 ~21:40Z
Each question has a default; work continues on the defaults where that is safe.

1. **Seam bar.** The declared bar is "median point distance at the seam ≤ 2 voxels". A resume trace shares the official grid, so I measure the residual of the first new vertex against the quadratic continuation of the official column, normal component, in 2.4 um voxels. The official mesh itself scores 2.40 vox on this measure, one L2 row inside itself, so the literal bar is unreachable even by the official mesh.
   **Default:** pass if the median ≤ max(2 vox, official self-baseline + 0.5 vox) = 2.90 vox. Report both numbers.
2. **Extension height.** The volume ends 9.1-9.6 mm above the top edge, so 1-2 cm is impossible.
   **Default:** extend to the volume top (≤ 9.6 mm).
3. **Tuning on held-out data.** The first preset fails the recovery test (3-6 % sheet jumps).
   **Default:** tune only on the held-out 5 mm of the official mesh, with the selection rule in `p4n/REPORT.md` §4, freeze the setting, then run the real extension once. If nothing passes, report FAIL and do not run.
4. **Resolution.** I trace on the 9.6 um m7 L2 prediction. Recovery vs the 2.4 um official mesh gives median 3.4 native vox (8 um), which matters for a ±15 um thin-slab ink channel.
   **Default:** any render declaration must use a ±30 um slab or re-snap the extension to the 2.4 um data. Rendering is not part of this task.
