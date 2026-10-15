Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-b P4-O sub-sibling S2 RESUME

## STOP STATE (orchestrator ruling P4-O-STAGE-O2S1-RESULT, 2026-09-27T07:00Z): iteration-5 failed its known-text gate
- Start no new tile.
- r1_c11 was more than half done (checkpoint n=2293 of 4356 windows = 0.53), so it alone is finished, pushed, and then everything stops.
- Driver v3 is retired. Do NOT run driver3.sh again.
- If the container restarts before r1_c11 is done, relaunch that single tile only (it resumes from its checkpoint):
  `swapon /work/swapfile; cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "1,11" >> /work/p4o/s2.log 2>&1 &`
- Then commit and push the tile.
- The sections below are historical.

- Task: iteration-5, row r1 (c10 c11 c12 c13 c0 c1 c2 c3 c4), then row r3 (same column order). Progress is in S2_progress.jsonl; bugs and events are in S2_NOTES.md.
- Code: tools/sib/ckpt-screen-b/p4o_tiles.py and infer_1667.py. The whole directory is identical to the parent (98cd075): the b87d9dd log fix, 15-min resumable checkpoints, the bounded read_stack (4741d69) and the banded norm_mean (98cd075).
- Container-local state:
  - venv /opt/ckb
  - weights /work/ckpt
  - mesh cache and full-res arrays /work/p4o
  - in-tile checkpoints /work/p4o/it5/ckpt/<tile>/
  - swapfile /work/swapfile (16 GiB)
  - driver /work/p4o/driver3.sh, log /work/p4o/driver.log
- Swap is required: the peak is about 13.9 GB against a 13.36 GiB memory cgroup (S2_NOTES.md, bug report 1). Swap is lost when the container restarts.

## Exact relaunch (idempotent: finished tiles are skipped, an interrupted tile resumes from its checkpoint)
```
swapon /work/swapfile   # if `swapon --show` does not list it
cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "1,10;1,11;1,12;1,13;1,0;1,1;1,2;1,3;1,4" >> /work/p4o/s2.log 2>&1 &
```
When row r1 is complete, run the same command with `--tiles "3,10;3,11;3,12;3,13;3,0;3,1;3,2;3,3;3,4"`.

The driver runs both rows in order, commits and pushes each finished tile, and appends to S2_progress.jsonl:
`bash /work/p4o/driver3.sh >> /work/p4o/driver.log 2>&1` (run it with no worker running, because it starts its own).

## If the container is new
1. Rebuild /opt/ckb as in the S2 setup: uv venv, then torch CPU, transformers==4.57.6, safetensors, numpy, opencv-python-headless, tifffile, imagecodecs, zarr<3, pillow, requests.
2. Run `tools/sib/ckpt-screen-b/fetch.py cards 5` and `fetch.py model.safetensors 5` (sha256-verified).
3. Recreate the swapfile: `fallocate -l 16G /work/swapfile && chmod 600 /work/swapfile && mkswap /work/swapfile && swapon /work/swapfile`.
