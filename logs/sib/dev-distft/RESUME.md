Provenance: Project HERCULES | owner the owner | [id removed]

# RESUME (dev-distft)

After any container restart, from the repo root:

```
bash tools/sib/dev-distft/env/setup_env.sh      # only if /opt/hv-ink is missing
/opt/hv-ink/bin/python -m pip show transformers | grep -q 4.57.6 || \
  VIRTUAL_ENV=/opt/hv-ink uv pip install --python /opt/hv-ink/bin/python transformers==4.57.6 opencv-python-headless requests tifffile
setsid nohup tools/sib/dev-distft/p4o_stage.sh > /work/p4o/stage.log 2>&1 &
setsid nohup tools/sib/dev-distft/p4o_push.sh  > /work/p4o/push.log  2>&1 &
```

- p4o_stage.sh is idempotent: finished tiles are skipped, and the bf16 check is skipped once
  `p4o/iteration-2/bf16_check.json` exists.
- A tile interrupted mid-way resumes from its last within-tile save (/work/p4o_ckpt, every 200 windows) and gives a
  bitwise-identical result. At most about 8 min is lost per restart.
- Weights and cards needed (all sha-checked at load): /work/ckpt/PHerc.1667-iteration-2/model.safetensors
  (485ce6e1...) and /work/cards/it2_*. If they are missing, re-download them as in downloads.jsonl
  (HF commit bf6053ca, never the previews).
- /work/p4o/mesh_valid.npy is rebuilt automatically, with the mesh tifs sha-checked against the e2 manifest.
- The DEV DIST-FT recipe: READY.md; the gate is in STATUS.md.
