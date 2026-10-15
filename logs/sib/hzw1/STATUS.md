Provenance: Project HERCULES | owner the owner | [id removed]

# hzw1 STATUS

- 2026-09-27T06:24Z: COMPLETE (40/40 tiles x 9 offsets, EXIT 0). 40/40 tiles done.
- Note: the first run stopped at 7/40 during the usage-limit pause (container restart, no EXIT line); it was resumed at 05:57Z and skipped the done tiles, no restart.
- Code: p4-highz 3e3a5ba stage_off.run_tiles unchanged; tools/sib/hzw1/run_cols.py only filters tiles to c9-c13.
- Validation: offset-0 records vs p4-highz stage_b_E2.jsonl (n_hi, stroke, acf, acf_rot90): exact 40 / 40. Record keys identical to off_C2.jsonl.
- No screen or hotspot verdict is computed here (DECL-P4-6-A4); p4-highz aggregates with screen_off.py.
- Blockers: none.

## Task 2: P4-O it5 tile r3 c15 (DECL-P4-14-A4)
- 2026-09-27T06:46Z: running (code 98cd075, file hashes verified, checkpoint sha256 verified). 4356 windows, ETA ~4.0 h.
- 2026-09-27T06:57Z: **STOPPED** (RULES.md P4-O-STAGE-O2S1-RESULT, 6545727; iteration-5 gate 0/3 FAIL). The job was killed at about 13 min of ~4 h, and /work/p4o was deleted. No tile output. The partial run log run_563.log (start lines only, no tile numbers) stays in the branch as the record.
- Standby. No jobs running.
