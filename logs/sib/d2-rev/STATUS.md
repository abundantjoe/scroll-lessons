Provenance: Project HERCULES | owner the owner | [id removed]

# d2-rev STATUS

Updated 2026-09-26 ~05:45Z.

State: **PHASE 1 DONE, waiting for GO D2.** No real data has been fetched or trained. No job is running.

- Environment: pinned; trainer copy 8475920 verified; base sha256 verified.
- Tests: units 14/14, integration 12/12.
- Smoke: PASS. REV pairing with P384 is bitwise; save/resume is bitwise.
- Throughput: 147.8 s/step (fp32, no AMX), 9.1 GiB peak.
- Details: READY.md.

Blocked on the three items the orchestrator named:
1. the D2 pair-freeze record;
2. the D2 amendments in RULES.md (recipe: F384, optimiser, filters, FL-09 reading, precision, trainer commit);
3. an explicit "GO D2".

Open points for the orchestrator (for information; defaults are not assumed here):
- This host has no AMX, so bf16 cannot run here. At fp32, one REV seed takes about 20.5 days for 12,000 steps.
- The trainer branch is now at 08d7e42 (newer than the pinned 8475920). This session uses whichever commit the declaration names.
