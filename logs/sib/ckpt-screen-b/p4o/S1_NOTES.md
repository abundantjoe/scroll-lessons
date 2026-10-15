Provenance: Project HERCULES | owner the owner | [id removed]

# S1 notes (ckpt-screen-b P4-O sub-sibling S1, builder only)

## Setup
- /opt/ckb venv as specified (torch CPU, transformers 4.57.6; no torchvision/timm).
- fetch.py cards 5 and model.safetensors 5: all checks passed (git_oid_ok true; weights sha256 9920d433...d3301b = catalogue, 333531996 bytes).

## BUG-1 in tools/sib/ckpt-screen-b/p4o_tiles.py (reported, not modified)
- Where: run_tile() ends with `log(rec)`; main()'s `log` does `json.dumps(dict(utc=utc(), **rec))`. `rec` already contains key `utc`, so it raises
  `TypeError: dict() got multiple values for keyword argument 'utc'` after every finished tile.
- Effect: the tile PNG and tiles/<file>.png.json are written completely BEFORE the crash (verified for r0_c14: png sha256 recomputed = png_sha256 in the json).
  The process then exits, so the remaining tiles of that --tiles list are not run, and the per-tile record line is missing from run_<pid>.log
  (the full record is in the png.json).
- Workaround used (no code change): the identical command is re-run in a loop from outside the repo; run_tile() skips tiles whose png.json exists,
  so each re-run continues with the next tile. The loop stops if a run produces no new png.json. Each restart costs ~1 min (model load + layout check),
  and produces one extra run_<pid>.log per tile.
- Suggested fix for the parent: `line = json.dumps(dict(dict(utc=utc()), **rec))` or `json.dumps({'utc': utc(), **rec})`.
- Lost time on r0_c14: the crash at 00:27:14Z was noticed at 01:01Z; r0_c15 started 01:02:59Z.

## BUG-1 resolution (parent fix adopted)
- Parent notice (2026-09-27 01:00Z): fix on the parent branch (b87d9dd, log() uses {**rec, "log_utc": ...}).
- 01:2xZ: tools/sib/ckpt-screen-b/p4o_tiles.py AND infer_1667.py checked out verbatim from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b
  (head fd13b7e; p4o_tiles.py there also calls card_tiling(state=, ckpt_fn=), so both files are taken as a pair). No local edits.
- r0_c14 was built with the pre-fix code; r0_c15 is running with the pre-fix code already loaded (output unchanged: the fix touches logging and
  resume only). From r0_c16 on, the loop restarts with the fixed code, which runs the rest of the list without restarts.

## Parent OOM fix adopted (read_stack bounded batches)
- Parent notice 01:35Z: fix at parent 4741d69. p4o_tiles.py + infer_1667.py checked out verbatim from the parent head (p4o_merge.sh not taken, not used by S1).
- 01:38:30Z checkpoint written for r0_c15 (n=584); worker killed right after, relaunched with the same command; log shows resume_from_window 584 at 01:40:19Z.
  r0_c15 windows 1-584 come from the pre-fix process, 585-3452 from the new one; the fix only bounds read concurrency (same chunk order and bytes),
  and the resumed tile's chunk_records_sha256 is re-computed from a fresh read.

## DECL-P4-14-A3 / A4 lists; container restart
- 02:48Z parent notice (DECL-P4-14-A3, verified in RULES.md and parent SUBSIBS.md): tools/sib/ckpt-screen-b/ synced to parent 98cd075 (norm_mean
  row-band sum, bit-identical value); r0 list reduced to "0,15;0,17;0,5;0,6;0,9" (fleet takes r0 c7, c8, c16). Worker killed right after the
  r0_c15 checkpoint n=2007 (02:55:44Z) and relaunched at 02:56Z; resumed at window 2007.
- The container restarted between 02:57Z and 06:50Z (uptime 0 min at 06:50Z); the worker (pid 2970) died with it and wrote no further checkpoint,
  so ~4 h of wall time were lost. /work (checkpoints) and /opt/ckb survived. Relaunched 06:52Z; r0_c15 resumed from window 2007 again (06:53:13Z).
- 06:50Z parent notice (DECL-P4-14-A4): row r2 list is "2,17;2,5;2,6;2,7;2,8;2,9" (r2 c14, c15, c16 taken by other workers).

## Stop rule (P4-O-STAGE-O2S1-RESULT)
- 07:00Z parent notice; verified in RULES.md (P4-O-STAGE-O2S1-RESULT, 06:52:50Z): iteration-5 failed its known-text gate (0/3); no new tile starts.
- r0_c15 last checkpoint n=2007 of 3452 windows (0.58 > 0.5): it finishes, is pushed, and the worker is then stopped before r0_c17.
  A watcher kills the worker as soon as r0_c15's png.json is complete. r0 c17, c5, c6, c9 and the whole r2 list are NOT started.
