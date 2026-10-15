Provenance: Project HERCULES | owner the owner | [id removed]

# hzw2 STATUS

- 06:56Z Task 2 STOPPED (P4-O-STAGE-O2S1-RESULT, 6545727: it5 known-text gate 0/3 FAIL). r3 c16 job killed at ~12 min (under half done); /work/p4o deleted; no tile output exists or was pushed. Standing by.

## Task 1

- 2026-09-27T06:05Z. DONE: E2 (20260701183124-w010-027, 2.4 um vol 20260411134726) offset sweep, c14-c19, rows 0-7.
- 48/48 tiles x 9 offsets (-60..+60 um, 15 um steps). File logs/sib/hzw2/off_E2_hzw2.jsonl, sha256 c88f781a1930f426242dafaca6cf7e4063b9427c56612c3f4697669fbd88ca83.
- Code p4-highz 3e3a5ba stage_off.py (unchanged) via tools/sib/hzw2/run_off.py (tile filter only). Thresholds: p4-highz thresholds_2p4.json T_hi.
- Record keys identical to off_C2.jsonl; sheet slabs per offset match C2 (e.g. -60 um -> [23,36], 0 -> [48,61]).
- Run interrupted once (container pause, 03:09Z after 31 tiles, all 31 records intact) and resumed 05:53Z, skipping done tiles.
- No screen or hotspot verdict computed here (for p4-highz screen_off.py). Blockers: none.
