Provenance: Project HERCULES | owner the owner | [id removed]

# P4-O fleet worker instructions (DECL-P4-14-A3): one PHerc.1667-iteration-5 tile per worker

Never open, Read, view or describe any tile, PNG, map or CT pixels. Numbers and hashes only.

## 1. Code
- Check out commit 98cd075 of branch claude/gifted-bell-gavnl5-sib-ckpt-screen-b.
  - This commit contains fixes b87d9dd (log crash), 9b0c5b3 (15-min in-tile checkpoints), 4741d69 (bounded chunk reads) and 98cd075 (norm_mean without 9 GB of copies).
  - Command: `git fetch origin claude/gifted-bell-gavnl5-sib-ckpt-screen-b && git checkout 98cd075 -- tools/sib/ckpt-screen-b/ && git fetch origin claude/gifted-bell-gavnl5-sib-pairs0814b`
- File sha256 (verify before running):
  - tools/sib/ckpt-screen-b/p4o_tiles.py a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371
  - tools/sib/ckpt-screen-b/infer_1667.py 29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12
  - tools/sib/ckpt-screen-b/fetch.py e5a3cb8f06e810686ea3fc174db98349d66c074e4d634c7746eb2e64bb291860
- The pairs0814b fetch is required: the builder reads its grid.json and the e2 manifest (strip-a grid, eligibility, mesh sha256).

## 2. Checkpoint
- Source: https://huggingface.co/scrollprize/PHerc.1667-iteration-5/resolve/6288ba60115ce827018926bcb0ea8e5696f33d3b/model.safetensors
- sha256: 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b (333,531,996 bytes).
- fetch.py downloads the file and checks it against data/catalogue/checkpoints.json. It also fetches and git-oid-checks the card and code into /work/cards, where the builder loads them.
- Provenance: logs/sib/ckpt-screen-b/p4o/provenance.json.

## 3. Environment and run (4 vCPU, ~15 GB; ~3.1-3.4 h per tile)
```
uv venv /opt/ckb --python 3.11
VIRTUAL_ENV=/opt/ckb uv pip install torch --index-url https://download.pytorch.org/whl/cpu
VIRTUAL_ENV=/opt/ckb uv pip install "transformers==4.57.6" safetensors numpy opencv-python-headless tifffile imagecodecs "zarr<3" pillow requests
mkdir -p /work/ckpt /work/cards /work/p4o
/opt/ckb/bin/python tools/sib/ckpt-screen-b/fetch.py cards 5
/opt/ckb/bin/python tools/sib/ckpt-screen-b/fetch.py model.safetensors 5
cd "$(git rev-parse --show-toplevel)" && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "R,C" >> /work/p4o/worker.log 2>&1 < /dev/null &
```
- Do not install torchvision or timm: a mismatched torchvision breaks the transformers import.
- Replace R,C with your tile, e.g. "0,7".
- Wait with a harness-tracked background waiter. Do not poll more often than every 10 minutes.
- Geometry, fixed in the code; do not pass options:
  - organizer 2.4 um surface volume 20260701183124-w010-027 at level 0 (no in-plane resampling);
  - slices 23-84, the official centre crop of 62 of 109;
  - card tiling: window 256, stride 128, halo 128, fmask = mesh-valid;
  - clip(0,200)/255, fp32, backbone in channels_last_3d.
- Order: ONE order only, the documented training convention (slices ascending, reverse_layers False, as for l_2). Iteration-5 has no second order.

## 4. Outputs and layout (the parent integrates these)
- Under logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/:
  - `tiles/20260701183124-w010-027_r{R}_c{C}.png`: 1068 x 1068 uint8 greyscale, raw prediction clip(p*255), 0 outside mesh-valid, INTER_AREA from 8343 px, IHDR/IDAT/IEND only;
  - `tiles/20260701183124-w010-027_r{R}_c{C}.png.json`: the per-tile record (png_sha256, stats, chunk counts, timing);
  - `run_<pid>.log`: the run log.
- Commit exactly those three paths and push to YOUR OWN branch.
  - Also add `logs/sib/ckpt-screen-b/p4o/fleet/<worker>.json` containing: worker name, branch, tile, code commit (98cd075), sha256 of p4o_tiles.py and infer_1667.py, png_sha256.
- Do not write manifest.json. The parent merges after verifying png_sha256 and the code commit.
- Commit messages end with "Provenance: Project HERCULES | owner the owner | [id removed]" plus your attribution lines.

## 5. Resume
- Re-run the same nohup command.
  - A finished tile (its .png.json exists) is skipped.
  - A tile in progress resumes from its last 15-min checkpoint in /work/p4o/it5/ckpt/<tile>/ (resume is bit-identical).
- On a new container, redo section 3 first. The checkpoint in /work is then gone and the tile restarts from the beginning.
- A tile that fully covers the mesh peaks at about 5.5 GB RSS with commit 98cd075.
