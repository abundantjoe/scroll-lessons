# own-f2 RESUME
State: blocked at order setup step (ckpt-screen-b checkout denied). Nothing built, no /work/own state.
Resume after ASK.md is resolved:
1. Setup step of order_own-f2.txt (ckpt-screen-b tools), recheck RECIPE sha256.
2. p4-excl inputs to /work/own/excl. 3. WORKER s.2 env + tests (ALL OK). 4. build_patches (verify).
5. train --arm F2. 6. infer 24 tiles (one commit each). 7. auc.py -> heldout_auc.json. 8. final STATUS.
