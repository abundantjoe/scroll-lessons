Provenance: Project HERCULES | owner the owner | [id removed]

# S1 resume (ckpt-screen-b P4-O, iteration-5)

Code: tools/sib/ckpt-screen-b/ verbatim at parent commit 98cd075 (log fix, 15-min resumable checkpoints, bounded read_stack, banded norm_mean).
Finished tiles (tiles/*.png.json) are skipped; an interrupted tile resumes from /work/p4o/it5/ckpt/<file>/. If the container is new and /work is
empty: steps 1-3 of the S1 brief (venv /opt/ckb, fetch origin claude/gifted-bell-gavnl5-sib-pairs0814b, fetch.py cards 5 + model.safetensors 5),
and the interrupted tile restarts from window 0.

Current batch (r0, DECL-P4-14-A3 list), exact relaunch command, from the repo root:

    OMP_NUM_THREADS=4 P4O_WORK=/work/p4o nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "0,15;0,17;0,5;0,6;0,9" >> /work/p4o/s1.log 2>&1 &

Next batch (r2, DECL-P4-14-A4 list), same command with:

    --tiles "2,17;2,5;2,6;2,7;2,8;2,9"

Log:
- 01:07Z relaunch on the log fix; 01:38:47Z relaunch on 4741d69 (resume n=584); 02:56Z relaunch on 98cd075 with the A3 list (resume n=2007);
  06:52Z relaunch after a container restart (resume n=2007).
