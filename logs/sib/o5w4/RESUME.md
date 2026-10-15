Provenance: Project HERCULES | owner the owner | [id removed]

STATE: COMPLETE (2026-09-27 06:37Z). Nothing to resume.

# o5w4 RESUME
Task: DECL-P4-14-A3, one tile: PHerc.1667-iteration-5, 20260701183124-w010-027 r0 c16, ckpt-screen-b pipeline.
Code worktree: /work/o5w4/cb (detached at the ckpt-screen-b commit recorded in STATUS.md). Env /opt/ckb. Weights /work/ckpt (fetch.py model.safetensors 5).
Work dir: P4O_WORK=/work/o5w4/p4o (in-tile checkpoints resume automatically).
Code commit 98cd075 (WORKER.md). Exact resume command (idempotent; resumes from 15-min in-tile checkpoint):
  cd /work/o5w4/cb && OMP_NUM_THREADS=4 P4O_WORK=/work/o5w4/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out /home/user/dominion/logs/sib/o5w4/p4o/PHerc.1667-iteration-5 --tiles "0,16" >> /work/o5w4/p4o/worker.log 2>&1 < /dev/null &
  then setsid nohup /work/o5w4/pushloop.sh & (30-min progress pushes). New container: redo WORKER.md section 3 first.
