# Verso-mode S1 map brief (RULES.md DECL-P4-26-A2, P4-OFF offset channel)
Provenance: Project HERCULES | [id removed]

Numbers only: never open, display or describe any map, tile or CT image. Push only to your own branch.

1. Code, unchanged: own-lead's tools/sib/own-lead/ (infer.py, own_common.py ddf90770) plus the wrapper tools/p4/infer_verso.py from origin/claude/gifted-bell-gavnl5.
   - Fetch: git fetch origin claude/gifted-bell-gavnl5 claude/gifted-bell-gavnl5-sib-own-lead; git checkout origin/claude/gifted-bell-gavnl5-sib-own-lead -- tools/sib/own-lead/ tools/sib/ckpt-screen-b/; git checkout origin/claude/gifted-bell-gavnl5 -- tools/p4/infer_verso.py tools/p4/BRIEF_VERSO.md logs/p4/verso_assign.json
   - Record the sha256 of infer_verso.py, infer.py and own_common.py in STATUS.md.
2. Model and environment: the S1 model (own-lead logs/sib/own-s1/model/model_final.pth + summary.json, sha256 bfa9f7a6...), as in tools/p4/BRIEF_S1MAP.md steps 2-3 (/opt/ckb venv: torch cpu, numpy, opencv-python-headless, tifffile, imagecodecs, zarr<3, requests, scipy, pillow). A new session sets this up first.
3. Your tiles: logs/p4/verso_assign.json, under helpers.<you> or new.<you> (own-lead: key "own-lead").
   - verso list: python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
   - forward list: python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
   - Do each tile's verso and forward maps back to back, so its CT chunks are downloaded once. Keep the list order. Use 2 lanes (one staging dir per lane) as before.
   - Push each tile (.png and .png.json) as soon as it is written: logs/sib/<you>/verso/tiles/ and logs/sib/<you>/fwd_x/tiles/.
4. Liveness: keep a harness-tracked Bash run_in_background wait (timeout 7200000) on your lanes until your list is pushed.
5. Never change infer.py, own_common.py, the wrapper, the model, the options or the lists.
6. New sessions only (p4v-*): before any listed tile, re-make the FORWARD map of 20260701183124-w010-027:0,11 with infer.py into logs/sib/<you>/fwd_x/repro/. Its png_sha256 must equal own-lead's (logs/sib/own-s1/maps/tiles/20260701183124-w010-027_r0_c11.png.json). Push it and record "REPRO PASS/FAIL" in STATUS.md. Maps from a session that fails this are not used.
7. Staging dirs (erratum to BRIEF_S1MAP step 4): verso runs must use per-lane staging dirs whose path contains "verso" (the wrapper refuses others), e.g. --out /work/own/verso_A and /work/own/verso_B. Forward runs use /work/own/fwdx_A and /work/own/fwdx_B. After each tile, copy its .png and .png.json into logs/sib/<you>/verso/tiles/ or logs/sib/<you>/fwd_x/tiles/ under the shared git lock and push. Code for ckpt-screen-b: git checkout 98cd075 -- tools/sib/ckpt-screen-b/ (as BRIEF_S1MAP step 1). The venv needs pillow too.
