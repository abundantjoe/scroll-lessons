Provenance: Project HERCULES | owner the owner | [id removed]

# P4-O sub-siblings (ckpt-screen-c), recorded before any is spawned (2026-09-27T01:10Z)

Material: PHerc.1667-iteration-4 (DECL-P4-14-A2 item 3). Builder: tools/sib/ckpt-screen-c/p4o_run.py around
ckpt-screen-b p4o_tiles.py / infer_1667.py unchanged (sha256 pinned in the driver). Disjoint tile subsets:

| worker | branch | stage (i) tiles (r,c) | precision |
|---|---|---|---|
| parent | claude/gifted-bell-gavnl5-sib-ckpt-screen-c | 0,5 (fp32, then the bf16 check copy outside the material); 1,5; 0,6; 1,6 | fp32 until the check passes |
| s1 | claude/gifted-bell-gavnl5-sib-ckpt-screen-c-s1 | 0,9; 0,10; 0,11; 1,9; 1,10 | fp32 until told the check passed |
| s2 | claude/gifted-bell-gavnl5-sib-ckpt-screen-c-s2 | 0,12; 0,13; 0,14; 1,11; 1,12 | same |
| s3 | claude/gifted-bell-gavnl5-sib-ckpt-screen-c-s3 | 0,7; 0,8; 1,7; 1,8; 1,13; 1,14 | same |

Stages (ii)-(iv) are assigned after stage (i), recorded here first. The parent merges sub-sibling tiles (PNG and JSON
sha256 re-checked) into p4o/PHerc.1667-iteration-4/ and runs the finalize step. Precision is recorded per tile.
