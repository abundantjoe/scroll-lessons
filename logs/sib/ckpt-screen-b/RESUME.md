Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-b RESUME (OWNER-STANDING-ORDER-3)

Task: P4-O (DECL-P4-14, -A1): PHerc.1667-iteration-5 on the strip-a tiles c0-c17, r0-r5 first.
Last completed: iteration-5 r0 c10 (parent), r0 c14 (s1), r1 c10 (s2); interim manifest.json. Builder at 4741d69 (log fix, 15-min checkpoints, bounded read_stack). Merge sub-sibling and fleet tiles with tools/sib/ckpt-screen-b/p4o_merge.py, then p4o_tiles.py --finalize and add the stage_reading block (see STATUS.md).
Detached processes (container-local):
- worker W0: /work/p4o/w0.pid, log /work/p4o/w0.log, checkpoints /work/p4o/it5/ckpt/<tile>/
- push loop: /work/p4o/pushloop.sh (commits and pushes tiles as they appear)
Exact next command (idempotent; finished tiles are skipped and a tile in progress resumes from its checkpoint):
  cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "0,10;0,11;0,12;0,13;0,0;0,1;0,2;0,3;0,4" >> /work/p4o/w0.log 2>&1 &
  then /work/p4o/pushloop.sh in the background.
If the container is new: rebuild /opt/ckb (SPECS.json wrapper.env), then run tools/sib/ckpt-screen-b/fetch.py cards 5 and fetch.py model.safetensors 5.
Sub-siblings s1-s3 (p4o/SUBSIBS.md) push to their own branches. The parent merges their tiles (hash-checked) and runs p4o_tiles.py --finalize --iteration 5.
