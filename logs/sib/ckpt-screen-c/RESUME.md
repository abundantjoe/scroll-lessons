Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c RESUME (OWNER-STANDING-ORDER-3)

Task: P4-O PHerc.1667-iteration-4 (DECL-P4-14-A2), stage (i) r0-r1 x c5-c14. Split: p4o/SUBSIBS.md.
Detached (container-local): parent chain tools/sib/ckpt-screen-c/p4o_parent.sh, pid /work/p4o_c/parent.pid,
log /work/p4o_c/parent.log; checkpoints /work/p4o_c/{fp32,bf16}/it4/ckpt/<tile>/ (15 min).
Exact next command (idempotent; finished tiles skipped, a tile in progress resumes):
  cd /home/user/dominion && nohup tools/sib/ckpt-screen-c/p4o_parent.sh >> /work/p4o_c/parent.log 2>&1 &
If the container is new: /opt/hv-1667 (py3.11: torch cpu, transformers==4.57.6, safetensors, numpy,
opencv-python-headless, tifffile, imagecodecs, requests, pillow, scipy); git worktree add --detach /work/ckc_bwt
origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b (at fd13b7e; driver pins its file hashes); in /work/ckc_bwt:
fetch.py cards 4 and fetch.py model.safetensors 4 (sha256 a1612b1f...).
After stage (i): merge s1-s3 tiles (sha re-check), p4o_run.py --finalize --out logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4, push.
