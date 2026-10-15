Provenance: Project HERCULES | owner the owner | [id removed]

# Brief p4-purple-mo: DECL-P4-16 item 4, colour-agnostic morphology on the control strip (numbers only)

Branch: claude/gifted-bell-gavnl5-sib-p4-purple-mo (from origin/claude/gifted-bell-gavnl5-sib-p4-purple). Files: logs/sib/p4-purple/mo/, tools/sib/p4-purple/mo/. Follow logs/sib/p4-purple/brief_common.md.

## Fence
Control strip only: 20260701183125-w028-037 (2.4 um surface volume, 109 slices at 2.4 um, centre 54; grid logs/sib/p4-tiles-b/grid.json on origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b; SV key as C2 in tools/sib/p4-highz/common.py). Optionally the 1.129 um control 20260623142658-w028-037 (grid m2b). No number of any kind on w010-027.

## Goal
Design and validate features of the written stroke that do not depend on ink composition: micro-relief (a deposit adds 5-20 um of material above the papyrus surface) and indentation (pen pressure pushes fibres down). Gate (DECL-P4-16 item 4): pixel AUC >= 0.70 against the known-text labels, with the tile-bootstrap 95 % CI lower bound above 0.60. Report the result whatever it is.

## 1. PROTOCOL.md first (push before any feature number)
- Ground truth: organizer human ink labels mapped onto w028-037, if such labels exist on that canvas in the bucket (existence check only, no pixel read); otherwise the official 2.4 um prediction of w028-037 (key in p4-tiles-b manifest.json): ink >= its pooled p90, background <= pooled p50, 50 um boundary exclusion (the DECL-P4-9 recipe; disclose that it measures agreement with a model). Freeze the choice before any feature number.
- Tiles: fixed seed; <= 4 dev tiles for engineering, >= 12 disjoint gate tiles (eligible = valid_fraction >= 0.5).
- Features, a fixed list of at most 6, each with its declared sign, e.g.:
  - F1 face height residual: per canvas pixel, sub-voxel position along the normal of the papyrus/void boundary on each face (threshold at the midpoint of the control's void and papyrus grey modes, or maximum gradient; declare), minus a Gaussian trend (sigma 0.5 mm). Declared sign: ink = raised. Both faces are reported; which face is recto follows p4-depth's sign convention if published, else both are tested with Bonferroni.
  - F2 local sheet thickness residual (face-to-face distance minus trend); ink = thicker.
  - F3 indentation: height Laplacian at 100-200 um scale; ink = concave.
  - F4 local roughness of the face height (SD in a 100 um window).
  - F5 crackle DoG energy (DECL-P4-9 recipe scaled to 2.4 um) at d* if p4-depth/p4-tiles-b froze one (cite file and commit), else at the face found by F1.
- AUC per feature on the gate tiles, pooled pixels on a ~20 um grid; tile-bootstrap 95 % CI (2000 resamples, fixed seed) and the Bonferroni-adjusted CI for the number of features; rot-90 label null (AUC must be 0.50 +- 0.03).
- Pipeline positive control: plant a synthetic 10 um deposit (letter-shaped, 0.4 mm stroke) into real control CT and show that F1/F2 respond (report the recovered height).

## 2. Run, then REPORT.md
Per-feature and per-tile AUC table, CIs, nulls, positive control, the gate verdict per feature, and the implication for a purple / organic title (a feature that passes becomes a colour-agnostic candidate channel; its title-zone use needs a separate declaration by the orchestrator). No title-zone number, ever, in this task.
