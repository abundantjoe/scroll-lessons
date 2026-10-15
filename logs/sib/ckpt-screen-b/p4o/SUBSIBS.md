Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-b P4-O sub-siblings (recorded before they start; DECL-P4-14 item 6)

Checkpoint first: PHerc.1667-iteration-5 (the latest eligible iteration, provenance.json). Early iteration next: PHerc.1667-iteration-1.
Builder: tools/sib/ckpt-screen-b/p4o_tiles.py, identical code in every worker. Each worker writes tiles/<file>.png and tiles/<file>.png.json under logs/sib/ckpt-screen-b/p4o/<ckpt>/. The parent merges them and writes manifest.json (p4o_tiles.py --finalize).
Cost: about 3.3-4.2 h of CPU per 2 x 2 cm tile per checkpoint (4 vCPU, fp32, stride 128 as on the card).

| worker | branch | checkpoint | tiles (r,c), in this order |
|---|---|---|---|
| W0 parent | claude/gifted-bell-gavnl5-sib-ckpt-screen-b | iteration-5 | r0: c10 c11 c12 c13 c0 c1 c2 c3 c4 |
| S1 | claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s1 | iteration-5 | r0: c14 c15 c16 c17 c5 c6 c7 c8 c9 |
| S2 | claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s2 | iteration-5 | r1: c10 c11 c12 c13 c0 c1 c2 c3 c4 |
| S3 | claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s3 | iteration-5 | r1: c14 c15 c16 c17 c5 c6 c7 c8 c9 |

Then rows r2-r5 of c0-c17 for iteration-5, split the same way by row. Orchestrator 21:17Z: ckpt-screen-a runs iteration-0 and ckpt-screen-c a third iteration, so an early iteration here (iteration-1) starts only if it is not already taken by -c. Tiles that are ineligible in e2 are skipped.
Sub-sibling rules: the parent's integrity rules apply unchanged. Never view a tile. Push only to your own branch. Write only under logs/sib/ckpt-screen-b/ and tools/sib/ckpt-screen-b/. No weights in git.

## 2026-09-27 02:45Z: DECL-P4-14-A3 fleet (o5w1-o5w8) takes r0 c7, r0 c8, r1 c7, r0 c16, r1 c15, r1 c16, r2 c15, r2 c16
Remaining lists (fleet tiles removed; code commit 98cd075):
- W0: r0 c11 (running) c12 c13 c0 c1 c2 c3 c4
- S1: r0 c15 (running) c17 c5 c6 c9
- S2: r1 c11 (running) c12 c13 c0 c1 c2 c3 c4
- S3: r1 c14 c17 c5 c6 c8 c9
Rows r2 and r3 (after r0-r1): skip r2 c15 and r2 c16 (fleet).

## 2026-09-27 06:45Z: DECL-P4-14-A4 adds p4-highz r2 c14, hzw1 r3 c15, hzw2 r3 c16 (also dropped from our lists)
- S1 r2 list becomes "2,17;2,5;2,6;2,7;2,8;2,9" (r2 c14 -> p4-highz; r2 c15, r2 c16 -> fleet).
- S3 r3 list becomes "3,14;3,17;3,5;3,6;3,7;3,8;3,9" (r3 c15 -> hzw1, r3 c16 -> hzw2).
