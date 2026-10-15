Provenance: Project HERCULES | owner the owner | [id removed]

# d2-p128 questions for the orchestrator (each has the default I continue on; nothing trains before GO D2)

1. **DEV hold-outs versus D2 pairs (finding).**
   - holdout_check.json: 121 of the 329 patches in the trainer's DRY-RUN allowlist for pairs0814 (sha256 6b1fc52f...)
     lie on 5 PHerc0814 DEV segments of the devloop dev_registry.json (ref a6af0cb9):
     20250925204843 (21), 20250925212701 (11), 20250925222237 (23), 20250926165636 (22), 20251001060526 (44).
   - DECL-DEVLOOP-A1 item 6 excludes DEV segments, plus same-papyrus +16 vox, from every D2 training set.
   - The dry run lists no hold-outs (holdout_ids_total 0).
   - My independent recomputation of the DECL-D2 filter (NCC >= 0.8, >= 7/9 windows within 1 px) reproduces the 329
     exactly.
   - Default: I train only on the allowlist named by the GO D2 freeze record. If that record lacks the DEV hold-out,
     I stop and ask before step 1.
2. **Trainer commit.**
   - The brief pins 8475920f, and my copy is that commit.
   - The freeze spec (PAIR_FREEZE_SPEC.md) needs the `blockpairs` / `stagec` block-file adapters and `pair_freeze.py`.
     These exist only in the later trainer commits (5bc29e1, 08d7e42). 8475920f cannot load a blockpairs source.
   - d2_train.py and d2_data.py differ between the two commits (sha256 in trainer_08d7e42_sha256.txt).
   - The 08d7e42 test suite passed here: 30/30, 1370 s (preparation only).
   - Default: I switch the copy only when GO D2 names the commit. I then re-run the tests and the smoke on it and record
     the new config sha256 before step 1.
3. **Checkpoints on reclaim.**
   - The run is about 61 h at fp32 on this CPU (READY.md section 6).
   - Resume states are local only. A remote ckpt ref would be a push to another branch, so it needs explicit
     permission.
   - Default: local only.
4. **Precision.** This container has no AMX. Default: fp32.
