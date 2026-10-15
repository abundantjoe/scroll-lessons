Provenance: Project HERCULES | owner the owner | [id removed]

# TRIBUNAL sibling status (2026-09-26T11:22:31Z)

REAL-TRIB-2 (orchestrator 2026-09-26 00:39Z), pre-registered in real_trib2/PREREG.md (commit 817a237):
- (i) done: preread thresholds are injectable, with no short-circuit and no rounding. Unrounded re-analysis:
  real_trib2/retrib1_unrounded.json.
- (ii) running: null_dryrun (mock R on clean 0139; m7 read along the normals; geometry-only centre curve).
- (iii) running: gate_2p4um (12 windows on the 2.399 um volume). pick_windows was replaced by an exact fast
  equivalent that gives identical windows (real_trib2/pick_windows_equivalence.json).
- (iv) running: p4_tiles_check (manifest numbers from p4-tiles-a/b; pixel faults on synthetic arrays only).
- Corrections in progress: w028 added to the base-training list. Clearance part B is being re-run. The
  example manifest is unchanged by w028, but it is now disjoint from used/DEV/D1 windows: 4 of its 6
  earlier windows overlapped DEV windows, and it now has 3.
Blocking decisions: none (no ASK.md).
Container note: dockerd and background jobs die when the session idles for hours. Restart:
tools/sib/tribunal/setup_render.sh; jobs resume from cached renders.

Update 11:3xZ: REAL-TRIB-2 is complete, and REPORT.md holds the round-3 section.
- (ii) INSUFFICIENT.
- (iii) margins are not >= 3x at 2.4 um.
- (iv) PASS.
The one job still running is clearance part B with w028 (killed once at idle, relaunched).
- 12:50Z: clearance part B with w028 complete, no change (w028 >= 17.3 vox from every bank segment and blank). REAL-TRIB-2 fully complete; no job running.
