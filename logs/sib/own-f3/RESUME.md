Provenance: Project HERCULES | owner the owner | [id removed]
# own-f3 RESUME
Done: branch at 6b5bdc5, RECIPE sha verified. Blocked at ckpt-screen-b checkout (ASK.md).
Next once unblocked: 1) ckpt-screen-b checkout per order; 2) p4-excl inputs to /work/own/excl (git archive 7ea9f34);
3) WORKER.md s2 env + test_own.py ALL OK; 4) build_patches.py (detached, --verify); 5) train --arm F3;
6) infer 24 held-out tiles in order (one commit each); 7) auc.py -> heldout_auc.json; 8) final STATUS.
Amendment received 13:14:55 UTC (RECIPE-A1, own-lead c23037b): before training (between steps 4 and 5), run
  git fetch origin claude/gifted-bell-gavnl5-sib-own-lead && git checkout c23037b -- tools/sib/own-lead/train.py tools/sib/own-lead/test_own.py logs/sib/own-lead/p4own/RECIPE_A1.md
then re-run test_own.py (ALL OK) and record the new train.py sha256 in STATUS.md. Not yet applied: setup is still blocked
(ASK.md), so the tests can't run anyway.
