Provenance: Project HERCULES | owner the owner | [id removed]

# hzw1 RESUME

Task: RULES.md DECL-P4-6-A4. E2 (20260701183124-w010-027, 2.4 um SV 20260411134726) offset sweep, c9-c13, all rows (40 eligible tiles, strip-a grid from pairs0814b e2/manifest.json), o = -60..+60 um step 15. No screen, no verdicts.

To resume after a restart:
1. `git fetch origin claude/gifted-bell-gavnl5-sib-p4-highz claude/gifted-bell-gavnl5-sib-pairs0814b claude/gifted-bell-gavnl5-sib-p4-tiles-b`; `pip install opencv-python-headless tifffile`.
2. `git worktree add --detach <scr>/hzrepo 3e3a5ba` (p4-highz code and frozen thresholds_2p4.json, T_hi 203).
3. Copy logs/sib/hzw1/off_E2_hzw1.jsonl to <scr>/hz/off_E2_-60_-45_-30_-15_0_15_30_45_60.jsonl (run_tiles skips done tiles).
4. Detached: `python3 tools/sib/hzw1/run_cols.py <scr>/hzrepo <scr>/hz E2 9 13 -60,-45,-30,-15,0,15,30,45,60`.
5. Check: `python3 tools/sib/hzw1/regress0.py <scr>/hzrepo <scr>/hz` (offset 0 must equal stage_b_E2.jsonl exactly).

## 2026-09-27 06:25Z: DONE
off_E2_hzw1.jsonl holds all 40 tiles (c9-c13, r0-r7) x 9 offsets. Nothing left to run. For p4-highz: copy it to <scr>/off_E2_-60_-45_-30_-15_0_15_30_45_60.jsonl (merged with hzw2 and the rest of E2) and run screen_off.py.

## Task 2 (RULES.md DECL-P4-14-A4, 245805a): P4-O PHerc.1667-iteration-5 tile r3 c15
Follows logs/sib/ckpt-screen-b/p4o/WORKER.md (branch claude/gifted-bell-gavnl5-sib-ckpt-screen-b), code 98cd075. The three file sha256 were checked and match WORKER.md section 1; the checkpoint sha256 9920d433... was verified.
- Started 06:44Z, detached; 4356 windows, ETA ~4.0 h. Log /work/p4o/worker.log; 15-min checkpoints in /work/p4o/it5/ckpt/.
- Resume, same container: re-run the section 3 nohup command with --tiles "3,15".
- Resume, new container: redo section 3 first. Also run `mkdir -p logs/sib/ckpt-screen-b`, because fetch.py logs to downloads.jsonl there. Do not commit downloads.jsonl.
- When done: commit only tiles/..._r3_c15.png, .png.json, run_<pid>.log and logs/sib/ckpt-screen-b/p4o/fleet/hzw1.json. Never view the png.
- 2026-09-27 06:57Z: STOPPED per RULES.md P4-O-STAGE-O2S1-RESULT (6545727): iteration-5 failed its known-text gate 0/3. The job was killed about 13 min in (under 1/2 done, so the "may finish" clause does not apply), and /work/p4o was deleted. No tile, png or png.json exists; fleet/hzw1.json was not written. Do NOT resume this task.
- State: standby, economy mode, no polling. Nothing is running.
