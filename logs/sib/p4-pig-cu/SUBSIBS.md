Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-cu sub-siblings

Why they exist:
- Level-0 scoring of the four materials streams about 300 GB of range reads.
- One container reaches about 70 MB/s and has only 4 CPU cores.
- Split three ways, alongside my own injection-recovery work, the scoring finishes about 3x sooner.

Rules:
- Sub-siblings may not create further siblings.
- Every sub-sibling runs the FROZEN code and params (params_freeze.json) unchanged. Before any read it verifies their sha256 values.

| id | branch | session id | exact task |
|---|---|---|---|
| a | claude/gifted-bell-gavnl5-sib-p4-pig-cu-a | session_017Q2QGXARsmKNxjBWnfxfvf | `cu.py score E1 0-99 logs/sib/p4-pig-cu/scores/E1`: all 60 eligible E1 tiles (title strip, 1.129 um, level 0) |
| b | claude/gifted-bell-gavnl5-sib-p4-pig-cu-b | session_01CxMMjRcHzpC6T2vChgXCgu | `cu.py score C1 0-99 logs/sib/p4-pig-cu/scores/C1`: all eligible control tiles (w028-037, 1.129 um, level 0) |
| c | claude/gifted-bell-gavnl5-sib-p4-pig-cu-c | session_01Lsk9ow2ZLpJt3BrAxn7yD7 | `cu.py score C2 0-99 .../scores/C2`, then `cu.py score E2 0-99 .../scores/E2` (2.4 um, level 1) |

The parent (p4-pig-cu) runs the injection-recovery (inject.py, all four materials), the on-sheet stage, and the thresholds, hotspots and REPORT.

Created 2026-09-26 18:26Z with NO prompt (idle). Tasks are sent only after this file is pushed. Model opus 5.5, same environment, source = this branch at the freeze commit 359b164.
