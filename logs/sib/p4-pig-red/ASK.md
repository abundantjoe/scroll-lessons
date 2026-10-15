Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-red ASK

## ASK-1 (2026-09-26): CT streaming blocked by the session safety check
The first CT read of this sibling was refused by the session's auto-mode safety check. That read was a numbers-only depth histogram of 400 random chunks of the control surface volume 20260623142658-w028-037 (1.129 um), streamed from the public vesuvius-challenge-open-data bucket with a throughput test. The check said the refusal came from earlier conversation content, not from the action, and that it would keep firing for the rest of this session.

Per the standing rules, it is not routed around: no rewording, no other host, no sub-sibling spawned to do the same fetch.

Blocked: every step that reads CT, which is params calibration on the control, injection-recovery (item 3) and scoring (item 4).
Done and pushed: MEMO.md (item 1) and xcom.json (attenuation table).

Question for the orchestrator or owner: re-launch the RED CT steps in a fresh sibling session, or in this session with default permissions, so that each fetch can be approved. The memo and the detector design carry over unchanged.
