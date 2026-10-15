# p4-titulus questions for the orchestrator (rules I will not decide myself)
Provenance: Project HERCULES | owner the owner | [id removed]

## ASK-1 (2026-09-26 22:30Z): ink-label pixel fractions (REDTEAM N1)
- Proposal: per-tile ink-label pixel fraction (numbers only) of the official labels of segment 20231016151002, mapped onto w010-027 c9-c15 r0-r3. It settles much of QA Q1: does the organizers' own labelling include the c11-c13 r0-r1 block?
- Question: is a numeric sum over a label raster within the RULES viewing rule? No image is displayed and no shape is described.
- I have not run it, and I will not run it without a yes. If yes, a builder (p4-excl has the mapping) is the natural owner.

## ASK-2 (2026-09-26 22:30Z): DECL-P4-15(b) voiding rule for offsets (REDTEAM N2)
- Question: should a verso candidate that matches the facing recto be split into two cases, instead of always being voided?
  - (a) void if the facing recto has matching ink at d*;
  - (b) report as an "offset lead" if the facing recto is blank or damaged there.
- This would be a new declaration (an amendment). I do not change declared rules.

## ASK-3 (2026-09-30 ~04:05Z): DECL-FL-1 PHerc1218 worker blocked
- Request (orchestrator trigger 03:55Z): build tools/sib/fl-pherc1218/pipeline.sh with a nohup watchdog and a restart loop that commits and pushes on its own.
- Setting up the self-restarting, auto-pushing background pipeline was refused by this session's safety check (unauthorized persistence). Per the standing rule it is not routed around.
- Facts gathered (numbers only):
  - PHerc1218 has no organizer tifxyz segments and no umbilicus in the bucket (only photos/, representations/predictions/{lasagna,surfaces}/, volumes/).
  - Volume: 20250521120456-8.640um-1.2m-116keV-masked.zarr. Surface prediction: surface-m7-L0-th0.2, L0 shape 23247 x 7593 x 7593.
  - So it needs the auto-grow path, and the fl-pherc0483a worker's code is the closest template (same MAY/8.64 um case).
- Needed: the owner's explicit approval for this session to run a persistent background pipeline, or a reassignment to a sibling whose session allows it.
