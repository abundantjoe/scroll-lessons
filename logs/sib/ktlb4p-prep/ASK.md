Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task ktlb4p-prep), 2026-09-25

I continue on each default until answered.

1. **Frame gate for a fragment: per window, not per mesh.**
   - The facts: 14 of 46 0500P2 meshes lie 5-15 % on zero CT in the 9.362 um frame (level 4; unchanged at level 2 and with a +-1 voxel dilation). All are 0-0.1 % outside the volume. In their native 4.317 um tracing frame most are <= 5 %, but 3 (00308, 00377, 00346) are 11-15 % there as well.
   - So parts of some traces extend beyond the masked fragment. The 9 um mask may also be tighter; the registration measures the frame mapping directly.
   - A whole-mesh FRAME-UNVERIFIED verdict would discard meshes whose interior is fine.
   - **DEFAULT:** apply the 5 % zero-CT test per candidate WINDOW (on the window's own mesh points). The whole-mesh numbers are still reported (frame_9um.json, frame_4um_L4.json).

2. **High-res level for registration.** The 2.215 um volume is read at level 1 (4.430 um). The C6 prefilter sigma is kept in total (disclosed in prereg_clarification.md). Reason: a level-0 block is about 430 MB, and 40 of them exceed the disk allowance.
   **DEFAULT:** yes, as pre-registered.

3. **Handedness of 0500P2.** The sample is catalogued as a FRAGMENT. Only the 4.317 um volume carries `text_side = -y`. The 9.362 um volume has no `text_side` and a null top-to-bottom flag. Under DECL-HANDED-GEOM a fragment without `text_side` is FLAG.
   **DEFAULT:** carry the 4.317 um `text_side` to the 9.362 um frame through the organizer affine (det > 0, so no reflection). The result is recorded as MEDIUM, single declared source. Up/down on 9.362 um stays unknown (both 180-degree candidates).
   **UPDATE (after measurement):** the mirror part is superseded by item 5 (FLAG: sources contradict). Up/down is NOT unknown: the 4.317 um +z maps to a 9 um direction with z component +0.97, so top-to-bottom = True carries over (image top = low z; MEDIUM, carried; REPORT section 6).

4. **Letters per window for the S estimate.** The J seal gave 0, 6, 2, 5 and 7 letters on J1-J5 (mean 4.0 per 2 x 2 cm window).
   **DEFAULT:** S is estimated as N_independent_text_windows x {2, 4, 7} (low / mid / high), stated as an estimate only. No reference-map letter counting is done (no reader, no viewing).

5. **Mirror state of 0500P2 is FLAG (sources contradict).**
   - The organizer `text_side` gives +1 on 20/20 windows.
   - The valid curvature centre (2 front windows) gives -1 at agreement about 1.0.
   **DEFAULT:** any seal and any read on 0500P2 uses BOTH mirror states as separate declared arms. No geometric mirror claim is made for 0500P2.

6. **No blank candidates.** Among the 1,624 gated windows the minimum reference-ink fraction is 2.26 % (bar < 1 %).
   **DEFAULT:** the L-0500P2 fold borrows its blank windows from the already-declared blank pool (0139 w053 type). The 0500P2 blank definition is not relaxed by this session. The orchestrator decides.

7. **Independent-window set.** The 20 recorded windows are ONE maximal set (greedy, position-ordered). The picker chooses from candidate_windows.json under the same certification rule.
   **DEFAULT:** the recorded 20 are the S-feasibility basis only; they are not a selection.

## Rulings received (orchestrator, 2026-09-26 05:25Z)

- Items 1, 2 and 4: defaults accepted.
- Item 3: up/down carried as MEDIUM (as updated).
- Item 5: FLAG accepted. Any later 0500P2 reading is a declared both-states reading, declared in RULES.md before any render is read.
- Item 6 (blanks): the proposed default applies. The L-0500P2 fold borrows its blanks from the already-declared blank pool (0139 w053 type); the 0500P2 blank definition is not relaxed.
- handed-2 Q6: no organizer request. Up/down stays unknown where unknown until own traces spanning more than one turn exist.
