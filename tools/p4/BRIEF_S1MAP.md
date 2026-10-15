# S1 map helper brief (RULES.md DECL-P4-25-A10)
Provenance: Project HERCULES | [id removed]

You make P4-OWN S1 ink-prediction maps of assigned PHerc. Paris 4 tiles with own-lead's code, UNCHANGED. Numbers only: never open, display or describe any map, tile or CT image. Push only to your own branch.

Your assignment: `logs/p4/s1map_assign.json` on branch `claude/gifted-bell-gavnl5`, under `helpers.<your sibling name>`. It lists tiles `seg:r,c` in three groups: `repro` (1 tile own-lead already made; the reproducibility check), `pool` (0 or 1 tile; the most urgent) and `rest`.

1. Code, in your checkout of abundantjoe/dominion:
   ```
   git fetch origin claude/gifted-bell-gavnl5 claude/gifted-bell-gavnl5-sib-own-lead
   git checkout origin/claude/gifted-bell-gavnl5 -- logs/p4/s1map_assign.json tools/p4/BRIEF_S1MAP.md
   git checkout origin/claude/gifted-bell-gavnl5-sib-own-lead -- tools/sib/own-lead/
   git checkout 98cd075 -- tools/sib/ckpt-screen-b/
   ```
   Record the sha256 of tools/sib/own-lead/infer.py and own_common.py in your STATUS.md.
2. Environment (own-lead's packages):
   ```
   uv venv /opt/ckb --python 3.11
   uv pip install --python /opt/ckb/bin/python torch --index-url https://download.pytorch.org/whl/cpu
   uv pip install --python /opt/ckb/bin/python numpy opencv-python-headless tifffile imagecodecs 'zarr<3' requests scipy
   ```
3. Model: wait until `origin/claude/gifted-bell-gavnl5-sib-own-lead` holds `logs/sib/own-s1/model/model_final.pth` and `summary.json`. Copy both to `/work/own/arm_S1/`. The sha256 of model_final.pth must equal `bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5`; stop if it does not.
4. Tiles: run TWO lanes at the same time, each with --threads 2. Lane A makes the `repro` tile, then every second `rest` tile. Lane B makes the `pool` tile first, then the other `rest` tiles. Start both lanes as soon as the model is verified. Command per tile (with --threads 2):
   ```
   OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py --model /work/own/arm_S1/model_final.pth \
     --summary /work/own/arm_S1/summary.json --tiles "<seg>:<r>,<c>" --out /work/own/stage_<lane> --threads 2
   ```
   Each lane writes to its own staging dir (/work/own/stage_A or /work/own/stage_B), because infer.py rewrites a manifest.json in its --out dir. After each tile, under one lock shared by both lanes (flock /work/own/git.lock), copy that tile's tiles/<seg>_r<r>_c<c>.png and .png.json from the lane's staging dir into logs/sib/<you>/s1maps_O/tiles/, then git add both files. Commit as "<you>: S1 map <seg>_r<r>_c<c> (DECL-P4-25-A10)" and push to your own branch, retrying up to 4 times with backoff.
5. Liveness: a cloud container is reclaimed a few minutes after its session goes idle, and a detached process alone does not keep it alive. Run the tile loop detached (setsid nohup), AND keep a harness-tracked wait on it: the Bash tool with run_in_background=true and timeout=7200000, exiting when the loop ends. Each time you are re-invoked, check the loop (restart it if it died; infer.py resumes), push anything unpushed, and re-arm the wait. Stop when your whole list is pushed.
6. STATUS.md at logs/sib/<you>/STATUS.md: one UTC line at start, one per tile, one at the end.
7. Never change infer.py, own_common.py, ckpt-screen-b, the model, the options or the lists. Never view an image. Every commit message ends with "Provenance: Project HERCULES | [id removed]".
