Provenance: Project HERCULES | owner the owner | [id removed]

# o5w2 RESUME
Task: DECL-P4-14-A3. One iteration-5 P4-O tile, 20260701183124-w010-027 r0 c8, run with ckpt-screen-b p4o/WORKER.md (code 98cd075).
Setup: env /opt/ckb (WORKER.md section 3). `git checkout 98cd075 -- tools/sib/ckpt-screen-b/`, left uncommitted here; sha256 values match WORKER.md. fetch.py cards 5 + model.safetensors 5 into /work (sha256 9920d433...301b verified).
Worker: /work/p4o/worker.pid, log /work/p4o/worker.log, in-tile checkpoints in /work/p4o/it5/ckpt/<tile>/ (every 15 min).
Push loop: /work/p4o/pushloop.sh (detached). It appends to logs/sib/o5w2/progress.log and pushes every 30 min. When the tile is done it copies the outputs into logs/sib/o5w2/p4o/PHerc.1667-iteration-5/, runs /work/p4o/final_json.py (o5w2_tile.json, p4o/fleet/o5w2.json) and pushes.
Resume (idempotent): cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "0,8" >> /work/p4o/worker.log 2>&1 < /dev/null &
then: setsid nohup /work/p4o/pushloop.sh >> /work/p4o/pushloop.log 2>&1 < /dev/null &
On a new container, the /work scripts and checkpoints are gone. Redo the setup; the tile then restarts from zero.
