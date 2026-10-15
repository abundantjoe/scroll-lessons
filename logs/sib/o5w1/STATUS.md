Provenance: Project HERCULES | owner the owner | [id removed]

# o5w1 status

Task: RULES.md DECL-P4-14-A3. One PHerc.1667-iteration-5 P4-O tile, 20260701183124-w010-027 r0 c7 (known-text gate tile), with ckpt-screen-b's pipeline exactly as documented in its p4o/WORKER.md (found 02:42Z at ckpt-screen-b 6aa0345).
- Code: ckpt-screen-b commit 98cd075 (git worktree /work/o5w1/ckb). File sha256 all match WORKER.md: p4o_tiles.py a32d7e86..c371, infer_1667.py 29444f37..cb12, fetch.py e5a3cb8f..1860.
- Env: /opt/ckb rebuilt exactly per WORKER.md section 3 (uv; torch 2.14.0+cpu, transformers 4.57.6, numpy 2.4.6, opencv 5.0.0; no torchvision/timm).
- Checkpoint: scrollprize/PHerc.1667-iteration-5 @ 6288ba60, model.safetensors sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b (333,531,996 B), equal to the catalogue, WORKER.md and the ckpt-screen-b manifest. Cards git-oid ok 4/4.
- Run: started 2026-09-27T02:43:55Z, OMP_NUM_THREADS=4, --tiles "0,7" only; no geometry option passed. 3792 model windows, builder ETA 3.48 h. Order: forward (single documented order for iteration 5).
- Layout: WORKER.md section 4 re-rooted under logs/sib/o5w1/ as the task instructs: logs/sib/o5w1/p4o/PHerc.1667-iteration-5/{tiles/<file>.png, tiles/<file>.png.json, run_<pid>.log} and logs/sib/o5w1/p4o/fleet/o5w1.json. Task json: logs/sib/o5w1/o5w1_r0_c7.json. No manifest.json is written.
- r0 c7 is eligible in the pairs0814b e2 manifest (valid_fraction 0.89972).
- No image, tile or CT pixel is opened or viewed; numbers and hashes only.

## Progress (2026-09-27T05:21:09Z)
- worker alive: False; tile r0 c7 started 2026-09-27T02:43:55Z; windows total 3792; last 15-min checkpoint at window 3672 (2026-09-27T05:15:49Z); done: True.

## DONE (2026-09-27T05:54Z)
- Tile r0 c7 finished 05:20:55Z; runtime 9420 s (2.62 h) at 4 threads, 3792 windows, one order (forward).
- png_sha256 9caf041bcfa59e8f203580faba12207d2817a7ec5e3d9473883f2d807f7675fc (recomputed from the pushed file: match); PNG chunks IHDR/IDAT/IEND only.
- valid_fraction 0.8997225067178096 equals the e2 manifest value; coverage_of_valid 0.98657; frac_nonzero_outside_valid 0; chunks read 4130, missing 426 (404, zero-filled as in the builder).
- Records: logs/sib/o5w1/o5w1_r0_c7.json (task json), logs/sib/o5w1/p4o/fleet/o5w1.json (WORKER.md fleet record). No manifest.json written. Worker stopped; nothing left running.
