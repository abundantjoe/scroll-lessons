Provenance: Project HERCULES | owner the owner | [id removed]

# S3 relaunch (iteration-5; finished tiles are skipped, interrupted tiles resume from /work/p4o/it5/ckpt/)

Builder in use: tools/sib/ckpt-screen-b/p4o_tiles.py sha256 a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371,
infer_1667.py sha256 29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12 (both = parent 98cd075: bounded read_stack + masked_norm_mean).

Row r1:

    cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "1,14;1,17;1,5;1,6;1,8;1,9" >> /work/p4o/s3.log 2>&1 < /dev/null &

Row r3 (after r1): same command with --tiles "3,14;3,17;3,5;3,6;3,7;3,8;3,9" >> /work/p4o/s3_r3.log.

Current state (2026-09-27T07:02Z): STOPPED per P4-O-STAGE-O2S1-RESULT (iteration-5 gate FAIL). Do not relaunch.
