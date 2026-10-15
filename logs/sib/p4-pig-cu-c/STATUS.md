Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-cu-c STATUS (sub-sibling c of p4-pig-cu)

- Branch: claude/gifted-bell-gavnl5-sib-p4-pig-cu-c, created from origin/claude/gifted-bell-gavnl5-sib-p4-pig-cu at a0816ff. The parent's head had moved from 8f82f83 to a0816ff.
- 18:40Z: all 6 sha256 values in logs/sib/p4-pig-cu/params_freeze.json were verified. 0 mismatches.
- Run order: E2 first (DECL-P4-12), then C2.
  - Command: `CU_SCRATCH=/tmp/cu python3 tools/sib/p4-pig-cu/cu.py score {E2,C2} 0-99 logs/sib/p4-pig-cu/scores/{E2,C2}`
  - The code is frozen and unmodified.
- E2 resumed from the parent's 29 tiles already in scores_E2.jsonl: cu.py skips (r, c) pairs that are already done. The code is deterministic, so the overlap is harmless.
- Event 18:43Z, resolved:
  - The first E2 launch failed with `git show origin/...-sib-pairs0814b:.../grid.json`, exit 128. The fresh clone lacked the remote refs that params.json/hz_common.py/analyze.py read.
  - Fix: fetched origin -sib-pairs0814b, -sib-p4-tiles-b and -sib-p4-excl. No code or param change.
  - run.sh then fell through to C2. C2 was killed about 1 min later, before any tile record was written, and restarted in order (E2, then C2).
- Pixels: none viewed. Only numbers are handled.
