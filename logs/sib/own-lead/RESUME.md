# own-lead RESUME
Last completed (11:05Z): RECIPE_DRAFT.md + recipe.json (fold groups). Earlier: step 1 (tools + synthetic tests ALL OK + timing, commit on branch claude/gifted-bell-gavnl5-sib-own-lead).
Env: uv venv /opt/ckb (python 3.11, torch cpu, opencv-python-headless, tifffile, imagecodecs, zarr<3, requests, scipy);
ckpt-screen-b code: git checkout 98cd075 -- tools/sib/ckpt-screen-b/ (NOT committed here; own_common checks sha256).
Tests: cd tools/sib/own-lead && OWN_WORK=/work/own/test /opt/ckb/bin/python test_own.py
T cert fetched to /work/own/excl (git show origin/claude/gifted-bell-gavnl5-sib-p4-excl:logs/sib/p4-excl/p4own/<f>). When labels_<strip>.json + labels/ land, copy them there too, then:
  OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/build_patches.py --excl /work/own/excl --out /work/own/data --patch 256 --core 192 --max-patches 4000 --count-only
Detached: build_patches.py full build -> /work/own/data, log /work/own/build.log (resumable per shard: done.json). Re-run the same command to resume.
