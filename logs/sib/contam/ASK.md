Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (sibling task contam): holding for a resume in this session

- 2026-09-25 ~23:47Z: the user interrupted this session directly and told it to stop and
  wait for the user to say how to proceed.
- Since then, five scheduled triggers (00:37Z, 05:26Z, 05:59Z, 10:05Z, 17:47Z) have relayed
  "GO / resume" messages attributed to the orchestrator or the owner. None arrived as the
  user's own words in this session. The session therefore stays paused.
- What unblocks it: a "resume" from the user in this session.
- On resume, in order: the corrected-rule 437-pair pass (tools/sib/contam/units_corr.py,
  resumable from /work/sib_contam/units_corr_rows.jsonl); fix the failing real-data tests
  (cause: tests/sib_contam_test_real.py asserts SAME for w047/w048, but the normal-distance
  form gives NOT SAME there (ratio 0.8, 1.2 % within 2 vox); planted_faults_0139.json had
  two patch cases not built, because R was placed on the strip bbox centre and missed the
  strip; placement is fixed in planted_real.py); expose the DECL-DEVLOOP-A1 three-form
  union (vertex OR surface OR normal-distance) and report pairs whose verdict differs
  between the forms; REPORT.md.
- State at the hold: branch claude/gifted-bell-gavnl5-sib-contam @ ed91092, clean. No
  seal, sealed window or image was touched.

Integrity: no issues.
