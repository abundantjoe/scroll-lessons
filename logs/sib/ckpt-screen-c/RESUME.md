Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c RESUME (OWNER-STANDING-ORDER-3)

Last completed: interim manifest, 12 tiles (c048fe2). In progress: r0 c5 bf16 check copy (/work/p4o_c/bf16check), then 1,5; 0,6; 1,6.
Task: P4-O PHerc.1667-iteration-4 (DECL-P4-14-A2), stage (i) r0-r1 x c5-c14. Split: p4o/SUBSIBS.md.
Detached (container-local): parent chain tools/sib/ckpt-screen-c/p4o_parent.sh, pid /work/p4o_c/parent.pid,
log /work/p4o_c/parent.log; checkpoints /work/p4o_c/{fp32,bf16}/it4/ckpt/<tile>/ (15 min).
bf16 check FAILED -> fp32 only. ckpt-screen-b worktree now at 98cd075 (bounded chunk reads; the old code was OOM-killed on r1 c5 at 12:37Z).
Exact next command (idempotent; finished tiles skipped, a tile in progress resumes):
  cd /home/user/dominion && nohup tools/sib/ckpt-screen-c/p4o_parent2.sh "1,9;1,10;1,11;1,12;1,7;1,8;1,13;1,14;2,9;2,10;2,11;2,12;2,13;2,14;2,5;2,6;2,7;2,8" >> /work/p4o_c/parent2.log 2>&1 &
  and the merge loop: nohup tools/sib/ckpt-screen-c/p4o_mergeloop.sh >> /work/p4o_c/mergeloop.log 2>&1 &
  (s1-s3 are archived; the parent holds all remaining tiles; SUBSIBS.md)
If the container is new: /opt/hv-1667 (py3.11: torch cpu, transformers==4.57.6, safetensors, numpy,
opencv-python-headless, tifffile, imagecodecs, requests, pillow, scipy); git worktree add --detach /work/ckc_bwt
98cd075 (ckpt-screen-b; driver pins its file hashes); in /work/ckc_bwt:
fetch.py cards 4 and fetch.py model.safetensors 4 (sha256 a1612b1f...).
Merge loop (detached): tools/sib/ckpt-screen-c/p4o_mergeloop.sh, pid /work/p4o_c/mergeloop.pid, log /work/p4o_c/mergeloop.log.
  Every 30 min it merges s1-s3 tiles (sha re-check), finalizes the interim manifest once gate (c5-c8) >= 3 and title (c9-c19) >= 4
  (DECL-P4-14-A3 item 2), and commits and pushes. Restart: nohup tools/sib/ckpt-screen-c/p4o_mergeloop.sh >> /work/p4o_c/mergeloop.log 2>&1 &
After stage (i): merge s1-s3 tiles (sha re-check), p4o_run.py --finalize --out logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4, push.
