Provenance: Project HERCULES | owner the owner | [id removed]

# RESUME (o5w6)
Task: DECL-P4-14-A3, PHerc.1667 iteration-5 P4-O tile r1 c16, strip 20260701183124-w010-027.
Pipeline: origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b logs/sib/ckpt-screen-b/p4o/WORKER.md (at 6aa0345), code commit 98cd075.
1. Redo WORKER.md section 3 (venv /opt/ckb, fetch cards + model; `mkdir -p logs/sib/ckpt-screen-b` first, fetch.py logs there).
2. Verify model sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b.
3. Re-run: OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "1,16" >> /work/p4o/worker.log 2>&1 < /dev/null &
   (in-tile 15-min checkpoints live in /work, lost on a new container -> restart from zero.)
4. Progress pusher: nohup bash logs/sib/o5w6/progress.sh & (commits STATUS + log tail every 30 min).
5. On completion: copy tile png, png.json, run log to logs/sib/o5w6/p4o/PHerc.1667-iteration-5/ (same names), write logs/sib/o5w6/result.json and fleet/o5w6.json, push.
