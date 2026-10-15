Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task handed-2), 2026-09-25. I continue on each default until answered.

1. **Frame gate.** A mesh whose vertices lie > 5 % on zero CT, or > 1 % outside the volume bounds (level-4 check), is FRAME-UNVERIFIED. Such a mesh is excluded from any reading, and no handedness is claimed for it, because a render from it would not come from the scroll at the declared place.
   Calibration: 0139 at most 3.6 % on zero CT, 0800 at 0 %, the in-frame 1447 meshes at most 1.4 %; the 10 bad 1447 meshes are at 41-91 %.
   **DEFAULT: yes, exclude.** No both-states reading for them.
2. **Reversed patches.** Take the vertices whose chirality is reversed under every valid r_out source (a fold or sheet jump).
   - If they are at most 20 % of the clear vertices: mask them out of the read, read the rest in the predicted state, and report the masked area.
   - If more than 20 %: FLAG, with a declared both-states reading.
   **DEFAULT: yes.**
3. **Validity of the mesh normal-line centre.** It counts as a source only if the median condition number of its per-band 2x2 system is <= 10. Calibration: 0139 at most 3.0; every 1447 source conflict has a condition number >= 15.
   **DEFAULT: yes.**
4. **Single valid source** (centroid only, not umbilicus-validated). MEDIUM if its vote agreement is >= 0.95 and reversed <= 2 %; otherwise FLAG.
   **DEFAULT: yes.**
5. **Package.** `src/hercules/geometry/handed_rule.py`, function `orient_for_reading(points, volume, *, frame=None, keep=None)` returning a `HandedDecision` (mirror_u, flip_v, confidence, sources, flags, keep_mask). Tests in `tests/test_geometry_handed_rule.py`. The existing `level_mesh.orient_for_reading` is not changed.
   **DEFAULT: yes.**

## Status of the defaults (end of handed-2)

All five defaults were applied. The results under them are in REPORT sections 10-12 and `h2/rule_applied.json`.

- If the orchestrator changes default 3 (condition number <= 10), 0800 and 2 of the 3 0841 meshes would move from MEDIUM back to HIGH. No mirror state changes.
- If default 1 is rejected, the 10 1447 traces would need an explicit decision on whether they may be read at all. Their CT is not at their declared place.

New question:

6. **Organizer up/down flags.** Should the orchestrator (via the owner) ask the organizers to fill `z_direction_is_top_to_bottom` for 0125, 0846A, 1203, 0490A and 0490B? The alternative is waiting for own traces spanning more than one turn.
   **DEFAULT: no external request by this session.** Both 180-degree candidates are shown until traces exist.

## Answers received (2026-09-25 19:28Z)

Defaults 1-5 were ACCEPTED by the orchestrator, including the SG 10 note that a masked (reversed) area inside a candidate rectangle R vetoes it. Question 6 is still open, and its default applies.

## handcheck packaging (DECL-PP-1), 2026-09-27

1. **Location.** The dispatch names pp/handcheck/. My standing write scope is logs/sib/handed/ and tools/sib/handed/. DECL-PP-1 names no path.
   **DEFAULT:** the package is at tools/sib/handed/handcheck/. It is self-contained (14 files; no import from the repo), so the orchestrator can copy it verbatim to pp/handcheck/ or publish it from there. The scrub was run on this exact folder.
2. **PHerc1447 count: 11 of 15 flagged, not 9 of 15.**
   - "9 of 15" is the superseded handed-1 count (9 chirality FLAGs, before the frame gate).
   - Under the packaged rule, 10 meshes are FRAME_UNVERIFIED and 1 is a chirality FLAG; 4 are OK MEDIUM.
   - Double-checked: the standalone package gives identical decisions on all 15, and a level-3 frame recheck with +-1 dilation gives identical gate outcomes (logs/sib/handed/pp/check_1447.json).
   **DEFAULT:** the README reports "11 of 15 flagged (10 FRAME_UNVERIFIED, 1 FLAG); to be confirmed by the organizers".
3. **Licence holder.** The MIT LICENSE reads "Copyright (c) 2026 The handcheck contributors", so no personal information is in the package.
   **DEFAULT:** keep it. If the form requires a named holder, the orchestrator edits that one line, and the scrub's personal-information check will then flag it by design.
4. **Provenance line.** It is left out of the package files (DECL-PP-1 item 2: no governance coupling). It appears in the logs, the REPORT and every commit.
   **DEFAULT:** as done.
