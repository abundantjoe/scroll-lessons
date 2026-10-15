Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz sub-siblings

None created (2026-09-26). Reason, measured: this container sustains ~450-480 level-0 range requests/s (6 processes x 24 threads, 13-slice ranges, 206 Partial Content), so the full level-0 work (~0.6 M chunk reads for E1 + control) is ~25 min here. Splitting rows across sub-siblings would add spawn, briefing and merge overhead of the same order and would not finish materially sooner.

## Update 2026-09-26 ~18:40Z: one sub-sibling for the 2.4 um control screen
Reason: the orchestrator's addenda (DECL-P4-6-A1/A2, DECL-P4-12) added E2 (2.4 um, 160 tiles) and its known-text control C2 (171 tiles), ~1.4 M level-0 chunk reads, ~110 min serial here. Splitting C2 off halves the wall time.

- Name: p4-highz-c2
- Branch: claude/gifted-bell-gavnl5-sib-p4-highz-c2
- Model: opus 5.5, same environment and repo
- Session id: session_01N1JCePQ76r3udBKYcNZxTP (created 18:33:41Z with no prompt; the task above is delivered only after this record is pushed)
- Exact task (verbatim):

```
You are sub-sibling p4-highz-c2 of sibling p4-highz, Project HERCULES (owner the owner, [id removed]). Repo abundantjoe/dominion. Work and push ONLY on branch claude/gifted-bell-gavnl5-sib-p4-highz-c2 (create it from origin/claude/gifted-bell-gavnl5-sib-p4-highz). Your files go under logs/sib/p4-highz-c2/.
Standing rules: numbers only. You never open, view or describe any image, tile or CT pixel. No seals, no decryption, no scoring, no reading. You may not create siblings or sub-siblings. Keep >= 5 GB disk free (run df first). Commit early and push often. Write logs/sib/p4-highz-c2/STATUS.md at each milestone. If a rule blocks you, write logs/sib/p4-highz-c2/ASK.md, push it, and continue with whatever is unblocked; never route around a safety check or a refusal. Do not modify any tool, threshold or protocol.
TASK: run the pre-registered per-tile numeric screen (DECL-P4-6 item 3; logs/sib/p4-highz/PROTOCOL.md and PROTOCOL_2p4.md) on the 2.4 um known-text control C2 = 20260701183125-w028-037, with the pushed tool, unchanged:
1. pip install numpy requests opencv-python-headless tifffile scipy pillow; git fetch origin claude/gifted-bell-gavnl5-sib-p4-tiles-b claude/gifted-bell-gavnl5-sib-pairs0814b claude/gifted-bell-gavnl5-sib-p4-highz.
2. Wait until logs/sib/p4-highz/thresholds_2p4.json exists on origin/claude/gifted-bell-gavnl5-sib-p4-highz (re-fetch that branch every 2 minutes; compute nothing before it exists). Then git merge origin/claude/gifted-bell-gavnl5-sib-p4-highz into your branch.
3. mkdir -p /tmp/hz and run from the repo root: python3 tools/sib/p4-highz/stage_b.py /tmp/hz "$PWD" tiles C2 > /tmp/hz/stage_b_c2.log 2>&1 (run it as a background job; ~171 tiles, ~20 s each).
4. About every 30 tiles, copy /tmp/hz/stage_b_C2.jsonl to logs/sib/p4-highz-c2/stage_b_C2.jsonl, commit and push. At the end push the final stage_b_C2.jsonl, the log, and STATUS.md (state done, tile count, any errors). If the run stops, restart the same command: it resumes from the jsonl.
Final report: tiles done, commit sha, and one closing line: "Integrity: no issues", or the integrity event.
```
