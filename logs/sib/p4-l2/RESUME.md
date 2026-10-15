Provenance: Project HERCULES | owner the owner | [id removed]

# p4-l2 RESUME
- DONE: L2 (160) and L2S (160) manifests. Raw store /work/l2/raw (160 npz; keep for p4-highz).
- DONE also: P4-W w_l2s (70) + wpc_l2s (56) manifests complete; BLOCK_FREEZE L2S FAIL.
- (former running items, all complete):
  - control cells for the block detector: block_ctl.py x4 -> /work/l2/block/ctl_cells_w{0..3}.jsonl (64 control tiles). Resume: rerun the same 4 commands (skip done).
  - P4-W windows: run_windows.sh -> logs/sib/p4-l2/{w_l2s,wpc_l2s}/ (70 + 56 windows), pushes every 10 min. Resume: rerun run_windows.sh.
- DONE: BLOCK_FREEZE (L2S depth) FAIL: held-out recall 0.089 at FPR 0.032. NEXT: d* re-run when p4-depth freezes d*; nothing on the title zone before that and before a METRIC-HASH.
- L3 windows/detector: wait for p4-depth d*.
- DECL-P4-18 (L4): DONE; control pre-gate FAIL both faces (PREGATE_L4.json). No title-strip L4 work.
