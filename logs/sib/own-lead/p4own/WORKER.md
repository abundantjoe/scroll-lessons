Provenance: Project HERCULES | owner the owner | [id removed]

# P4-OWN arm worker instructions (DECL-P4-23 item 5). One arm per worker.

Never open, Read, view or describe any tile, PNG, map, label or CT pixel. Numbers and hashes only. No reading, no
scoring, no seals. If a rule blocks you, write logs/sib/own-<arm>/ASK.md, push it, continue with what is unblocked.
You may NOT create further sessions.

## 1. Code and frozen recipe
- Branch: work and push ONLY on your branch claude/gifted-bell-gavnl5-sib-own-<arm> (arm in lower case), created from
  the RECIPE commit named in your order (RECIPE_SHA below).
- `git fetch origin claude/gifted-bell-gavnl5-sib-own-lead claude/gifted-bell-gavnl5-sib-ckpt-screen-b claude/gifted-bell-gavnl5-sib-pairs0814b claude/gifted-bell-gavnl5-sib-p4-excl`
- `git checkout -b claude/gifted-bell-gavnl5-sib-own-<arm> <RECIPE_SHA> && git checkout 98cd075 -- tools/sib/ckpt-screen-b/ && git reset -q tools/sib/ckpt-screen-b`
- Verify `sha256sum logs/sib/own-lead/p4own/RECIPE.md` equals logs/sib/own-lead/p4own/RECIPE.md.sha256, and the code
  sha256 listed in RECIPE.md. Stop and ASK if anything differs.

## 2. Environment (4 vCPU, ~15 GB RAM)
```
uv venv /opt/ckb --python 3.11
VIRTUAL_ENV=/opt/ckb uv pip install torch --index-url https://download.pytorch.org/whl/cpu
VIRTUAL_ENV=/opt/ckb uv pip install safetensors numpy opencv-python-headless tifffile imagecodecs "zarr<3" pillow requests scipy
mkdir -p /work/own && df -h /
cd tools/sib/own-lead && OWN_WORK=/work/own/test /opt/ckb/bin/python test_own.py   # must end ALL OK
```

## 3. Data (deterministic rebuild; checked against the lead's manifest)
The exact build command is in RECIPE.md section "Data". It ends with `--verify logs/sib/own-lead/p4own/build_manifest.json`
and exits with VERIFY FAILED if any shard sha256 differs: then stop and ASK. Keep >= 5 GB free (df before and after).

## 4. Train (detached, resumable)
`cd <repo> && OWN_WORK=/work/own setsid nohup /opt/ckb/bin/python tools/sib/own-lead/train.py --arm <ARM> --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_<ARM> >> /work/own/train_<ARM>.log 2>&1 < /dev/null &`
- Re-running the same command resumes from the last 15-min checkpoint; a finished arm exits at once.
- Wait with a harness-tracked background waiter; do not poll more often than every 10 minutes.
- Push logs/sib/own-<arm>/STATUS.md (state, step, s/step, loss, ETA) at start, about hourly, and at the end, plus
  logs/sib/own-<arm>/train/{summary.json,train_manifest.json,train_log.jsonl} when done. Never push model weights
  unless RECIPE.md says so.

## 5. Predict (after training)
- F arms: your held-out tiles, as listed in RECIPE.md for your fold, in that order. Then
  `auc.py --arrays <maps>/arrays --tiles <same list> --excl <p4-excl p4own dir> --out logs/sib/own-<arm>/heldout_auc.json`.
- S arms and NULL: X tiles in this order: col. -1 (r0-r1 x c11-c13); then r0-r5 x c14-c17; then the rest of
  r0-r7 x c9-c19 (row-major). Use --save-npz for the col. -1 tiles.
- Command: `OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py --model /work/own/arm_<ARM>/model_final.pth --summary /work/own/arm_<ARM>/summary.json --tiles "<list>" --out logs/sib/own-<arm>/maps [--save-npz] [--tile-dist <json>]`
- Push ONE commit per tile: tiles/<seg>_r<R>_c<C>.png, its .png.json, the updated maps/manifest.json (and arrays/<tile>.npz
  for col. -1). Never open the PNG.

## 6. Final report (in logs/sib/own-<arm>/STATUS.md, <= 30 lines)
What was done, numbers (steps, final loss, held-out AUC for F arms), commit sha, and one closing line:
"Integrity: no issues" or the integrity event.
