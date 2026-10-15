# RESUME p4-core
Provenance: Project HERCULES | owner the owner | [id removed]
- ALL ASSIGNED WORK DONE:
  - DECL-P4-7 count: a5a7d82.
  - B mesh audit: 1284733.
  - A P4-TAG: e223569.
- DONE: DECL-P4-26/-A1 facing surfaces: naive 0/90 pass; reg rejected (0/36 controls); fallback (4) controls 18/36, title 32/54 pass (facing/). Nothing running.
- Chain order (DECL-P4-24-A1 ruling): holes -> holes_agg -> (e2) validate v1+v2 -> (e2) beyond with a VALID variant -> DECL-P4-26 facing (control, title). Outputs in /home/user/scratch (e2_*.json, facing/). If the container restarts: rerun chain_after_holes.sh (every step resumable or skipped if done).
- Disclosure: (e2) smoke tests on 3 known-mesh columns (v1 and v2, P_MIN provisional) were run and discarded; v2 was defined after the v1 smoke test.
