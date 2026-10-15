Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0139 ASK (hold status, written 2026-09-26 in reply to the 17:48Z orchestrator relay)

1. HOLD: owner go-ahead needed in this session.
   - In this session the owner interrupted a tool call and said to stop and wait until the owner says how to proceed.
   - Since then, six scheduled orchestrator notices (00:19Z, 00:27Z, 05:26Z, 05:59Z, 10:05Z, 17:48Z) have asked this session to resume. The 10:05Z and 17:48Z notices relay the owner's words to the orchestrator; neither mentions this session's stop.
   - A relayed message is not treated as the owner lifting a stop given directly in this session.
   - Default: hold. Nothing runs until the owner says "resume" (or equivalent) in this session.
   - What is blocked: the coordinate-convention check, the pairs0814 gate as primary, HANDOVER.md for pairs0139b/pairs0139c, and the PART 1 build.

2. State at hold (numbers only):
   - Last code commit before this file: 3ed0fc1.
   - Exclusion v1 (exclusion.json): 20 segments excluded (controls, title, 3 named neighbours, 13 found by Rule N).
   - CORR-RETRACE-RULE re-check (retrace_check.py): finished 00:22:56Z with exit 0. Its results (/work/p139/exclusion_v2.json, nearE2/) have not been read or applied, and no pair has been built under them.
   - Built under the pre-registered 128 px gate and exclusion v1:
     - w044: 2534 candidates, 652 kept, 4 shards (local only, not pushed, not post-checked);
     - w043: partial, interrupted by the container restart between 19:46Z and 23:25Z.
   - Frame diagnostics (w035, 40 tiles):
     - ours vs organizer 9.362 um SV: NCC 0.996, shift 0.03 px;
     - our 2.399 um render vs organizer 2.399 um SV: NCC 1.000, shift 0.002 / 0.001 px (2.399 um px);
     - organizer 9.362 um SV vs the 2.399 um reference through the mesh affine: median shift 1.55 px (dy -1.20).
     - The mesh affine's 3-D check gives median 0.09-0.18 vox.
     - No coordinate-convention bug has been found yet; each frame check so far is clean.

Integrity: no issues. No image was opened. Nothing was deleted. Pushes went only to this session branch.
