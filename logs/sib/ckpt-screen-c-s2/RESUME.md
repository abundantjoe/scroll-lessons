Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c-s2 RESUME

Task: P4-O PHerc.1667-iteration-4 (DECL-P4-14-A2), s2 subset per logs/sib/ckpt-screen-c/p4o/SUBSIBS.md:
tiles 0,12; 0,13; 0,14; 1,11; 1,12. Precision: fp32 (until the parent sends "precision bf16").
Checkpoint verified: model.safetensors sha256 a1612b1fc97dea039aec3a1d06ff65fe0ee217b91dbe6db9785eb2e5befb3ffe.
Builder worktree: /work/ckc_bwt at 98cd075 (OOM fix, 2026-09-27T18:58Z per parent). Driver: tools/sib/ckpt-screen-c/p4o_run.py checked out (working tree only, not committed here) from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c (pins p4o_tiles.py sha256 a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371). Precision fp32 final (parent: bf16 check failed).

Status: done (fp32): r0_c12 03:32:06Z png_sha256 1545f8b5ec16edf1b258f23dfe565676cd9ed5cab797d3fd659fbc5120828a23; r0_c13 08:48:25Z png_sha256 40251727e47063178468e1c831c5d88d856ee0946bb2944d0ba9200dee0c02a3. r0_c14 21:10:36Z png_sha256 f820e7c088bb2fef0469c76d3d306645517e0009cd41dbcac32a9a35c2709267. Last tile done: 0,14 (r1_c11 in progress, eta 3.99 h).
Run relaunched 2026-09-27T18:59Z with the updated driver after pid 393 died during r0_c14 with no r0_c14 checkpoint (r0_c14 restarts from scratch). pid 460 (/work/p4o_c/s2.pid), log /work/p4o_c/s2.log, checkpoints /work/p4o_c/fp32 (15 min).

Exact command (idempotent; finished tiles skipped, a tile in progress resumes):
  cd /home/user/dominion && mkdir -p /work/p4o_c/fp32 && OMP_NUM_THREADS=4 CKB_CARDS_DIR=/work/cards CKB_CKPT_DIR=/work/ckpt CKB_HF_DIR=/work/hf P4O_WORK=/work/p4o_c/fp32 nohup /opt/hv-1667/bin/python tools/sib/ckpt-screen-c/p4o_run.py --tiles "0,12;0,13;0,14;1,11;1,12" --out logs/sib/ckpt-screen-c-s2/PHerc.1667-iteration-4 --precision fp32 > /work/p4o_c/s2.log 2>&1 &
If the container is new: follow logs/sib/ckpt-screen-c/RESUME.md "If the container is new" first, then: git checkout origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c -- tools/sib/ckpt-screen-c/p4o_run.py; git -C /work/ckc_bwt checkout --detach 98cd075.
Provenance: Project HERCULES | owner the owner | [id removed]
