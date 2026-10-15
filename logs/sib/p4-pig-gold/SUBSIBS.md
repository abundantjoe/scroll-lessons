Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-gold sub-siblings

Why: after the params freeze, the remaining work is injection-recovery (about 64 patches x 12 variants) plus full scoring of E1 (60 tiles, level 0) and E2 (160 tiles, level 1). Measured at about 45 s per level-0 tile x 4 in parallel, that is CPU-bound here, about 60+ min serially. Running E1 and E2 scoring in separate containers parallel to the injection saves about 25 min.

Each sub-sibling is gated: it does nothing until this file lists it (step 0), and it computes nothing on its material before logs/sib/p4-pig-gold/params.json is on this branch (step 1). The exact tasks are in brief_e1.txt and brief_e2.txt on this branch. The sub-siblings use the frozen code unmodified.

| sub-sibling | session id | branch | exact task |
|---|---|---|---|
| p4-pig-gold-e1 | session_015oakmsir6nzVppSMZ8r2ND | claude/gifted-bell-gavnl5-sib-p4-pig-gold-e1 | logs/sib/p4-pig-gold/brief_e1.txt: run_tiles.py E1 (level 0, 60 eligible E1 tiles, all rows) + score.py E1 (flags excl_d_a if available, else pending) |
| p4-pig-gold-e2 | session_01UZxD1gPkoE3Z3EoBuPGAWV | claude/gifted-bell-gavnl5-sib-p4-pig-gold-e2 | logs/sib/p4-pig-gold/brief_e2.txt: run_tiles.py E2 (level 1, 160 eligible E2 tiles) + score.py E2 --excl logs/p4/excl/excl_a_union_e2.json |

Created 2026-09-26 18:29Z (model claude-opus-5-5, same environment and repo). They may not create further sessions. A third sub-sibling was not needed.

## Outcome (2026-09-27)
Both sub-siblings stopped at about 18:50Z with 'session limit' (account five-hour usage limit). They computed nothing and pushed nothing: no branch -e1 or -e2 exists on origin. The parent runs E2 and E1 scoring itself with the same frozen code (params.json sha256 84ab70b9...).
