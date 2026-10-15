Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz RESUME (2026-09-27 ~01:00Z)

- DECL-P4-6-A3:
  - The p4-tiles-b 1.129 um calibration is STOP (logs/sib/p4-tiles-b/l3e/calib_1129.json, 96c8811), so the E1 offset sweep is running: control C, then E1, at o = -60..+60 um in 15 um steps, via stage_off.py.
  - Then the 6 % f_in samples at every offset (C, E1, C2).
  - Then Bonferroni bars and full-coverage f_in for tiles above them, giving screen_dstar.json (E1 part).
- E2: waiting for the p4-depth verdict (logs/sib/p4-depth/calib.json is absent as of 00:55Z).
  - The control C2 sweep at the 9 offsets is done: off_C2.jsonl, 171 tiles.
- DECL-P4-16 item 2: panel_ext is running on the 2.4 um control, offsets 0, -60, -45 done, then -30 .. +60. panel_ext.py aggregates the results.
- Scripts in scratch (not needed to resume): /tmp/claude-0/run_e1sweep.sh, /tmp/claude-0/run_panel.sh. Scratch records live in /tmp/claude-0/hz. Commands are in stage_off.py's docstring.

## Update 2026-09-27 01:45Z
- p4-depth 2.4 um calibration: **STOP** (logs/sib/p4-depth/calib.json, z_peak 1.94 < 3, candidate -31.2 um, 4/24 tiles consistent). So E2 also takes the 9-offset sweep (queued after E1: /tmp/claude-0/run_e2sweep.sh), using the existing C2 control records.
- Progress: control C at 54/64 tiles; panel at offset -30 (slow, 3 jobs on 4 cores).

## Update 2026-09-27 06:40Z
- DONE: E1 sweep (screen_dstar_E1.json), panel_ext.json, E2 c0-c8 and c20 (off_E2_p4highz.jsonl), all f_in samples (fin_off_*.json).
- TODO once hzw1 (c9-c13) is complete:
  - concatenate off_E2_p4highz.jsonl + hzw1 + hzw2 into scratch off_E2_-60_..._60.jsonl;
  - screen_off.py C2 E2 ... candidates -> stage_off.py gap for listed tiles -> screen_off.py (screen_dstar_E2.json; copy it as screen_dstar.json);
  - REPORT addendum.

## Update 2026-09-27 06:46Z: DECL-P4-14-A4, one P4-O tile (PHerc.1667 iteration 5, r2 c14)
- Setup follows logs/sib/ckpt-screen-b/p4o/WORKER.md (branch ckpt-screen-b, code 98cd075). The p4o_tiles.py, infer_1667.py and fetch.py sha256 values match. Venv /opt/ckb. Checkpoint verified (sha256 9920d433...).
- Started 06:45Z; 4356 windows, ETA ~4 h. Log: /work/p4o/worker.log. In-tile checkpoints: /work/p4o/it5/ckpt/.
- Resume on the same container: re-run the WORKER.md section 3 nohup command with --tiles "2,14". On a new container, redo section 3 first; the tile then restarts.
- Progress is pushed every 30 min to logs/sib/p4-highz/p4o_progress.json.
- When done, commit only these paths:
  - logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/tiles/20260701183124-w010-027_r2_c14.png and .png.json;
  - run_<pid>.log;
  - logs/sib/ckpt-screen-b/p4o/fleet/p4-highz.json.
  Leave the checked-out tools/sib/ckpt-screen-b/ out of the commit.
- Disclosure: commit 59d1343 accidentally included the checked-out tools/sib/ckpt-screen-b/ (8 files). They were staged by WORKER.md's `git checkout 98cd075 -- tools/...` and swept into that commit. Every blob is byte-identical to 98cd075 (checked with git rev-parse), so this is a verbatim copy and no code changed.
- The in-progress run outputs under logs/sib/ckpt-screen-b/ are excluded locally (.git/info/exclude) until final. The final PNG, png.json and run log are then added with git add -f.

## Update 2026-09-27 06:57Z: P4-O tile r2 c14 STOPPED
- Per RULES.md P4-O-STAGE-O2S1-RESULT (iteration-5 known-text gate 0/3, FAIL) and the orchestrator's order, the detached job was killed at about 12 min in (well under half done). /work/p4o, including its in-tile checkpoints, is deleted. The 30-min progress loop is stopped.
- No tile, PNG or png.json was produced, and nothing from the run is committed. No fleet/p4-highz.json was written.
- The model checkpoint in /work/ckpt and the venv /opt/ckb remain. They are regenerable and unused.
- State: standby, economy mode, no polling.
