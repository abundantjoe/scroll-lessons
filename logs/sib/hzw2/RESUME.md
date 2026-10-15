Provenance: Project HERCULES | owner the owner | [id removed]

# hzw2 RESUME (DECL-P4-6-A4: E2 offset sweep, c14-c19, all rows)

- Code: p4-highz stage_off.py at 3e3a5bad277786eb8717f0a21608232c7cf7ef3d (git worktree /home/user/hzcode, detached), unchanged.
  Wrapper tools/sib/hzw2/run_off.py only filters E2 eligible tiles to c in 14..19 (48 tiles, rows 0-7).
- Threshold: p4-highz logs/sib/p4-highz/thresholds_2p4.json T_hi (frozen), read by stage_off.thr("E2").
- Offsets: -60,-45,-30,-15,0,15,30,45,60 um (o_slices = round(o/2.4)).
- Scratch: /home/user/hzw2scr; records append to off_E2_-60_-45_-30_-15_0_15_30_45_60.jsonl, copied to logs/sib/hzw2/off_E2_hzw2.jsonl.
- Resume: re-create the worktree (git worktree add --detach /home/user/hzcode 3e3a5ba), pip install opencv-python-headless tifffile,
  fetch refs sib-pairs0814b and sib-p4-tiles-b, restore the scratch jsonl from logs/sib/hzw2/off_E2_hzw2.jsonl, run /home/user/hzw2scr/run.sh
  (python3 tools/sib/hzw2/run_off.py /home/user/hzcode /home/user/hzw2scr -60,...,60). Done tiles are skipped.
- No screen, no hotspot verdict is computed here (p4-highz aggregates with screen_off.py).

## Task 2 (DECL-P4-14-A4): P4-O PHerc.1667-iteration-5 tile r3 c16 (started 06:44Z)
- Code: ckpt-screen-b 98cd075 in worktree /home/user/ckb (sha256 of p4o_tiles.py, infer_1667.py, fetch.py verified against WORKER.md).
- Env /opt/ckb per WORKER.md section 3; model sha256 verified; cards git-oid ok. Work dir /work/p4o (15-min checkpoints in /work/p4o/it5/ckpt/).
- Resume: in /home/user/ckb re-run the WORKER.md section 3 nohup command with --tiles "3,16" (new container: redo section 3 first).
- On finish: copy tiles/…_r3_c16.png, .png.json and run_<pid>.log from /home/user/ckb/logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/ to this branch, add fleet/hzw2.json, push. The tile is never viewed.

- 06:56Z STOPPED per P4-O-STAGE-O2S1-RESULT (6545727). Job killed, /work/p4o deleted, no output. Do not resume.
