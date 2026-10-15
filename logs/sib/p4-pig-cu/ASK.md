Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-cu ASK (2026-09-26 ~18:30Z)

## Q1: three idle sub-sibling sessions have no task
- To honour "record ... and push BEFORE it starts", I created the 3 sub-siblings with no prompt:
  - a: session_017Q2QGXARsmKNxjBWnfxfvf
  - b: session_01CxMMjRcHzpC6T2vChgXCgu
  - c: session_01Lsk9ow2ZLpJt3BrAxn7yD7
- I recorded them in SUBSIBS.md (8f82f83) and meant to send each its task afterwards.
- This session has no tool that can message a cloud session. The tasks were never sent, and the sessions are idle with no work done.
- I will not create further sessions (the cap is 3), and I will not archive them without a human's acknowledgement.
- Meanwhile I run all the scoring myself, so nothing waits on this.

Options for the orchestrator:
- (a) Send each session the task below. The code is deterministic, so any overlap with my own run is harmless, and I will merge whichever finishes first.
- (b) Archive the three sessions.

Task text for the orchestrator to send (replace X / MATERIALS):

> You are sub-sibling p4-pig-cu-X of HERCULES (parent session_01BGvjN5PqxUioDsG1cJPaYj). Work only on branch claude/gifted-bell-gavnl5-sib-p4-pig-cu-X, created from origin/claude/gifted-bell-gavnl5-sib-p4-pig-cu at 8f82f83. Standing rules of RULES.md apply: never open or view any image or CT pixel; numbers only; no sub-siblings.
> 1. Install the dependencies: `pip install numpy scipy opencv-python-headless requests tifffile`.
> 2. Verify every sha256 in logs/sib/p4-pig-cu/params_freeze.json, and stop if any differs.
> 3. For each M in MATERIALS, run `CU_SCRATCH=/tmp/cu python3 tools/sib/p4-pig-cu/cu.py score M 0-99 logs/sib/p4-pig-cu/scores/M`. Commit and push logs/sib/p4-pig-cu/scores/M every ~10 tiles.
> 4. Write logs/sib/p4-pig-cu-X/STATUS.md. Report the commit sha.

MATERIALS: a = E1; b = C1; c = C2 then E2.
