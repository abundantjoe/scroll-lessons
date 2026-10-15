# own-lead RESUME
Last completed (11:05Z): RECIPE_DRAFT.md + recipe.json (fold groups). Earlier: step 1 (tools + synthetic tests ALL OK + timing, commit on branch claude/gifted-bell-gavnl5-sib-own-lead).
Env: uv venv /opt/ckb (python 3.11, torch cpu, opencv-python-headless, tifffile, imagecodecs, zarr<3, requests, scipy);
ckpt-screen-b code: git checkout 98cd075 -- tools/sib/ckpt-screen-b/ (NOT committed here; own_common checks sha256).
Tests: cd tools/sib/own-lead && OWN_WORK=/work/own/test /opt/ckb/bin/python test_own.py
T cert fetched to /work/own/excl (git show origin/claude/gifted-bell-gavnl5-sib-p4-excl:logs/sib/p4-excl/p4own/<f>). When labels_<strip>.json + labels/ land, copy them there too, then:
  OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/build_patches.py --excl /work/own/excl --out /work/own/data --patch 256 --core 192 --max-patches 4000 --count-only
Detached: S1 train.py (pid in /work/own/arm_S1.pid, log /work/own/train_S1.log, out /work/own/arm_S1; resumes from resume_latest.pth). Next after S1: infer.py X tiles into logs/sib/own-s1/maps (order as S2 in orders/order_own-s2.txt).

Driver (15:10Z): run_arms.py pid in /work/own/run_arms.pid, log /work/own/run_arms.log. Restart after a crash or container restart with the same command (all steps resume/skip): cd /home/user/dominion && setsid nohup /opt/ckb/bin/python tools/sib/own-lead/run_arms.py --train-threads 2 --pred-threads 2 >> /work/own/run_arms.log 2>&1 < /dev/null &  (or --sequential). If S1 train.py itself died, re-run its train.py command first (it resumes).
Pending at end: git add -f logs/sib/own-*/maps/run_*.log logs/sib/own-*/heldout_maps/run_*.log (infer run logs, excluded locally to save pushes).

After ANY container restart run (one turn): cd /home/user/dominion && setsid nohup tools/sib/own-lead/watchdog.sh >> /work/own/watchdog.log 2>&1 < /dev/null &   (watchdog relaunches run_arms.py; everything resumes; stops when /work/own/ALL_DONE exists)

[line withheld: prize-candidate detail under review]
