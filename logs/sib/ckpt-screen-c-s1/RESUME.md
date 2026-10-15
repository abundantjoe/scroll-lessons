# ckpt-screen-c-s1 RESUME

Worker s1 of ckpt-screen-c (logs/sib/ckpt-screen-c/p4o/SUBSIBS.md). Material: PHerc.1667-iteration-4
(commit 9ff9913d, model.safetensors sha256 a1612b1f..., verified true). Tiles in order: 0,9; 0,10; 0,11; 1,9; 1,10.

- Done (fp32, pushed): 0,9 png_sha256 ee5d907e... (03:13:59Z); 0,10 png_sha256 9f68ca79... (08:31Z);
  0,11 png_sha256 dc09520c... (21:16Z)
- In progress: 1,9 (started 2026-09-27T21:16:23Z, 4356 windows, eta 3.99 h). Then 1,10.
- Precision: fp32 (parent: bf16 check failed, everything stays fp32)
- pid: 449 (earlier 659, 392 ended with container reboots)   log: /work/p4o_c/s1.log (appended; also run_449.log)
- Driver update (parent, OOM fix, output-identical): working tree has tools/sib/ckpt-screen-c/p4o_run.py checked out
  from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c (fdd6e2b; pins p4o_tiles.py sha256 a32d7e86...), and
  /work/ckc_bwt is detached at 98cd075. That file was also swept into commit ee19acf by the checkout (blob
  identical to the parent branch; no content of this worker outside its directory). On a new
  container: git fetch origin claude/gifted-bell-gavnl5-sib-ckpt-screen-c claude/gifted-bell-gavnl5-sib-ckpt-screen-b;
  git checkout origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c -- tools/sib/ckpt-screen-c/p4o_run.py;
  worktree add --detach /work/ckc_bwt 98cd075 (instead of fd13b7e).

If the container is new: follow logs/sib/ckpt-screen-c/RESUME.md "If the container is new", then re-run the
command below (finished tiles are skipped; a tile in progress resumes from its 15-min checkpoint in P4O_WORK).

    cd <repo> && mkdir -p /work/p4o_c/fp32 && OMP_NUM_THREADS=4 CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf P4O_WORK=/work/p4o_c/fp32 nohup /opt/hv-1667/bin/python tools/sib/ckpt-screen-c/p4o_run.py --tiles "0,9;0,10;0,11;1,9;1,10" --out logs/sib/ckpt-screen-c-s1/PHerc.1667-iteration-4 --precision fp32 > /work/p4o_c/s1.log 2>&1 &

On "precision bf16" from the parent: same command with --precision bf16 and P4O_WORK=/work/p4o_c/bf16, for
tiles not yet started only.
