Provenance: Project HERCULES | owner the owner | [id removed]

# BLOCK_FREEZE (DECL-P4-17 item 2), depth L2S (slab 48..60, +-14.4 um about the mesh)

Frozen 2026-09-27T01:13:22Z, before any title-zone (c9-c19) cell of w010-027 is computed. The rules are in block_freeze.py's docstring, written before its first run.
- Control strip: 20260701183125-w028-037 2.4 um, level 0. Tiles: all eligible intercolumn tiles c11, c15 and c19 (24), plus 40 text-column tiles (c0-c9, c12-c14, c16-c18), seed 20260927.
- Cells: 5 x 5 mm (4 x 4 per 2 cm tile). A cell is used iff >= 50 % mesh-valid and >= 50 % max > 0. Statistic: the fraction of in-cell px with slab max > T.
- Split by tile, seed 20260928. Train 303 text / 181 intercol cells; held-out 303 / 187.
- T_d = 161, chosen as argmax train recall over T in 140..254 at F(T) = the train intercol p95. Cell threshold F = 0.050776.
- Held-out: text recall 0.0891, intercol FPR 0.0321. Bar: recall >= 0.90 at FPR <= 0.05. **Verdict: FAIL.** The detector is uninformative at L2S depth, and no title-zone run is made at this depth.
- Title-zone rule (for the d* re-run only; it applies only after a PASS and after the orchestrator's METRIC-HASH): a cell is flagged iff f_Td > the intercol P99 (0.075572 here). A block candidate is a 4-connected cluster of >= 4 flagged cells.
- The d* re-run uses the same code, applied to d* cells, once p4-depth freezes d*.

```
e3e3568ffc1bdbd0782d1cab62f9dfa51e90453a98a5b12c8a31360f789da7b5  tools/sib/p4-l2/block_freeze.py
7d2e3097a2d3ccfed37ad9f69bd1d927a79b3d0e496ff471f85b41e1aa740dfe  tools/sib/p4-l2/block_ctl.py
c6dad892e4fc1b3595ca57f329020f5646d5a57d6d7534b08f2b61eaa37806a1  tools/sib/p4-l2/l2.py
e83b2d635dc699cd4f7bd06c263592f2e675c5101c2e48f7341c22ed23078e50  logs/sib/p4-l2/block/freeze_l2s.json
07d03e7927fd2e1a13c53037c1a706ec2f21509dedc1e020848a55c33a85da28  logs/sib/p4-l2/block/ctl_cells_l2s.jsonl.gz
```
