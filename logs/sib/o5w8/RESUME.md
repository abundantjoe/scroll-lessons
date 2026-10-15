Provenance: Project HERCULES | owner the owner | [id removed]

# o5w8 RESUME (DECL-P4-14-A3)
Tile 20260701183124-w010-027 r2 c16, PHerc.1667-iteration-5, pipeline per ckpt-screen-b p4o/WORKER.md @ 6aa0345, code commit 98cd075.
Output dir (task: under logs/sib/o5w8/, WORKER.md naming): logs/sib/o5w8/p4o/PHerc.1667-iteration-5/{tiles/,run_<pid>.log}

On the same container: re-run
  OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w8/p4o/PHerc.1667-iteration-5 --tiles "2,16" >> /work/p4o/worker.log 2>&1 < /dev/null &
  then: setsid nohup bash /work/p4o/driver.sh >> /work/p4o/driver.log 2>&1 < /dev/null &
On a new container: redo WORKER.md section 1-3 (git checkout 98cd075 -- tools/sib/ckpt-screen-b/, verify sha256, venv, fetch cards + model, mkdir logs/sib/ckpt-screen-b for fetch log), then the above; tile restarts from zero (in-tile ckpts live in /work).
