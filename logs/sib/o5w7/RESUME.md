Provenance: Project HERCULES | owner the owner | [id removed]

# o5w7 RESUME (DECL-P4-14-A3): PHerc.1667 iteration-5, tile r2 c15, strip 20260701183124-w010-027

Pipeline: ckpt-screen-b p4o/WORKER.md at 6aa0345 (code commit 98cd075), followed exactly. One deviation in output location only: `--out logs/sib/o5w7/p4o/PHerc.1667-iteration-5` (orchestrator brief: outputs under logs/sib/o5w7/, WORKER.md naming/layout kept below that prefix).

On a new container:
1. `git fetch origin claude/gifted-bell-gavnl5-sib-ckpt-screen-b && git checkout 98cd075 -- tools/sib/ckpt-screen-b/ && git fetch origin claude/gifted-bell-gavnl5-sib-pairs0814b`; verify sha256 (WORKER.md section 1). The same files are also committed on this branch (added in 1st commit, blobs identical to 98cd075).
2. `mkdir -p logs/sib/ckpt-screen-b` (fetch.py appends downloads.jsonl there; not committed), then WORKER.md section 3 env + fetch (checkpoint sha256 9920d433...3301b).
3. Relaunch:
   `OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w7/p4o/PHerc.1667-iteration-5 --tiles "2,15" >> /work/p4o/worker.log 2>&1 < /dev/null &`
   Same container: resumes from /work/p4o/it5/ckpt/. New container: restarts from zero.

## 2026-09-27T07:10:53Z: STOPPED, do not resume
Tile r2 c15 stopped at 1748/4356 per RULES.md P4-O-STAGE-O2S1-RESULT (it5 gate 0/3 FAIL). /work/p4o deleted. Do not relaunch; stand by for a new order.
