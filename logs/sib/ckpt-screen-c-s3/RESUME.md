Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c-s3 RESUME

Task: PHerc.1667-iteration-4 stage (i) tiles 0,7; 0,8; 1,7; 1,8; 1,13; 1,14 (fp32). Authority: DECL-P4-14 / DECL-P4-14-A2; subset in logs/sib/ckpt-screen-c/p4o/SUBSIBS.md.
Setup verified 2026-09-27: model.safetensors sha256 a1612b1fc97dea039aec3a1d06ff65fe0ee217b91dbe6db9785eb2e5befb3ffe (verified true); worktree /work/ckc_bwt created at fd13b7e.
OOM fix (parent order 2026-09-27T18:57Z): p4o_run.py from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c (pins p4o_tiles.py a32d7e86...); /work/ckc_bwt now at 98cd075 (git -C /work/ckc_bwt checkout --detach 98cd075).
Last tile done: 0,8 (fp32, png_sha256 96b5c656060ed5e090e18bf405f6b62f6def428f04c1ea61ab61c8508477e052); 0,7 done (ecc0857e...). 1,7 in progress (from zero 2026-09-27T18:59Z; second container restart, no checkpoint survived). Precision stays fp32 (parent: bf16 check failed).
Detached run: pid in /work/p4o_c/s3.pid (442), log /work/p4o_c/s3.log, checkpoints under /work/p4o_c/fp32.
Exact command (idempotent; finished tiles skipped, tile in progress resumes from its 15-min checkpoint):
  cd /home/user/dominion && mkdir -p /work/p4o_c/fp32 && OMP_NUM_THREADS=4 CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf P4O_WORK=/work/p4o_c/fp32 nohup /opt/hv-1667/bin/python tools/sib/ckpt-screen-c/p4o_run.py --tiles "0,7;0,8;1,7;1,8;1,13;1,14" --out logs/sib/ckpt-screen-c-s3/PHerc.1667-iteration-4 --precision fp32 > /work/p4o_c/s3.log 2>&1 &
If the container is new: follow logs/sib/ckpt-screen-c/RESUME.md "If the container is new", then the command above.
If told "precision bf16": same command with --precision bf16 and P4O_WORK=/work/p4o_c/bf16 for tiles not yet started only.
