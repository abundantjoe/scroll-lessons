# own-f1 RESUME
Resume at order step "Setup": the checkout of 98cd075 -- tools/sib/ckpt-screen-b/ (+ reset, .git/info/exclude),
once it is approved. Then: RECIPE code sha256 check, WORKER.md section 2 (venv + test_own.py ALL OK), p4-excl inputs,
data build, train --arm F1, predict, AUC, final report. Branch base 6b5bdc5 and RECIPE sha256 already verified.
Received 2026-09-27T13:15Z (scheduled trigger "own-f1 A1"): own-lead amendment RECIPE-A1 (commit c23037b) asks to check out
tools/sib/own-lead/train.py, test_own.py and logs/sib/own-lead/p4own/RECIPE_A1.md from c23037b before training, re-run tests,
record the new train.py sha256 in STATUS.md. NOT applied: it is the same kind of cross-branch code checkout that was denied,
and the worker is blocked earlier anyway. Apply it only once the user approves, right after the ckpt-screen-b step.
