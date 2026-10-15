Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal (not a declaration): DECL-HANDED-GEOM (final draft, task handed-2)

Written by the sibling builder. The orchestrator edits, declares or rejects it. The evidence is in logs/sib/handed/REPORT.md, sections 1-10.

**Handedness (SG item 12) is settled by geometry, not by readers.** This replaces the reader bar of DECL-HANDED, -R2 and -R3B, which returned AMBIGUOUS three times at chance (decided votes A 12 : B 14).

## Rule (code: src/hercules/geometry/handed_rule.py, function orient_for_reading)

The package is `tools/sib/handed/pkg/`, to be merged as `src/hercules/geometry/{handed_rule,handed_synth}.py` and `tests/test_geometry_handed_rule.py`. Record the merged file hashes when merging.

- **Mirror.** `convention_sign = parity`. Parity is +1 if the root catalogue says `left_handed_coordinates = false` and the zarr axes are a permutation of z, y, x; -1 if the flag is true; 0 otherwise, which gives PARITY_UNKNOWN. A mesh is read unmirrored iff its chirality `sign(det[dP/du, dP/dv, r_out])` after the flips equals the parity. The acquisition z direction is not used.
- **Up/down.** `z_direction_is_top_to_bottom`: True puts low z at the image top, False puts high z at the top. Null leaves up/down unknown: the mirror state is still decided, and both 180-degree candidates are shown until up/down is resolved (section "Up/down" below).
- **r_out.** Use the official umbilicus of the volume, or of a sibling volume mapped by the organizer affine. Otherwise use the CT-mask centroid (level 4, z-smoothed, sigma 256 vox). The centroid is only informational when an umbilicus exists. The mesh normal-line centre is also a source, valid only when the median condition number of its per-band 2x2 systems is <= 10. Fragments use `n_out = -text_side`.

## Gates, in order

| # | Gate | Outcome if it fails |
|---|---|---|
| 1 | Parity known | PARITY_UNKNOWN (FLAG) |
| 2 | Frame check in the declared volume: <= 5 % of sampled vertices on zero CT and <= 1 % outside the volume (level 4) | FRAME_UNVERIFIED: the mesh is not read at all |
| 3 | At least one valid r_out source | FLAG |
| 4 | Valid sources agree on the whole-mesh sign | FLAG: read both mirror states, as separate declared arms |
| 5 | Vertices reversed under every valid source are <= 20 % of clear vertices | Above 20 %: FLAG, both mirror states. At or below: those vertices (dilated by one grid step) are masked out of `keep` and never read |

**Confidence:**
- HIGH: >= 2 valid sources, each agreeing on >= 0.98, pairwise per-vertex agreement >= 0.95, reversed <= 2 %.
- MEDIUM: every source >= 0.9 and pairwise >= 0.8; or a single source at >= 0.95 with reversed <= 2 %.
- FLAG: anything else.

## What counts as passing SG 12 for a volume and a candidate mesh

All of the following must hold:
1. `tests/test_geometry_handed_rule.py` passes on the merged code, with its hash recorded. It includes the planted-glyph cases for the volume's frame class: parity +1 or -1, and top-to-bottom True, False or null. It also includes the frame, reversed-patch, conditioning, source-disagreement, umbilicus-precedence and fragment gates.
2. The candidate mesh's decision is `state == "OK"` with confidence HIGH or MEDIUM, and the frame check was measured, not "frame not checked". PHerc0841 is the exception: CT sampling near J is not allowed, so the frame check there must be run away from J or be declared waived.
3. Only vertices in `keep` are read.
4. If `z_direction_is_top_to_bottom` is null, SG 12 passes for the MIRROR only. Up/down must then be resolved by the method below, or both 180-degree candidates are shown. They are rotations, not mirror images, of each other.

A mesh that fails any of these is not a SG 12 pass. Either both mirror states are read as separate declared arms (a FLAG from gate 4 or 5), or the mesh is not read (FRAME_UNVERIFIED).

## Current status under this rule

Source: `logs/sib/handed/h2/rule_applied.json`.

| Scroll | Result (meshes) | Note |
|---|---|---|
| PHerc0139 | OK HIGH 38/38 | umbilicus + normal-line centre |
| PHerc0009B | OK MEDIUM 18/18 | text_side, single source; frame not checked |
| PHerc0841 | OK 3/3 (HIGH 1, MEDIUM 2) | frame not checked (J rule); J-excluded vertices only |
| PHerc0800 | OK MEDIUM 6/6 | normal-line centre ill-conditioned (13-23), so centroid only |
| PHerc1447 | FRAME_UNVERIFIED 10, OK MEDIUM 4, FLAG 1 (20250502205333) | see below |

PHerc1447 detail:
- The 10 FRAME_UNVERIFIED meshes are the 2025-05-02 traces at z 20,400-24,970. They lie 41-91 % on zero CT and 0-19 % outside the volume; the traces predate the volume export and no transform is catalogued. Do not read them.
- FLAG 20250502205333: 3.1 % reversed patch and weak centroid agreement 0.76. Read both mirror states, or exclude it.

In every OK decision the organizer grid is read as stored (`mirror_u = False`, `flip_v = False`).

## Up/down for volumes with z_direction_is_top_to_bottom = null

The volumes are 0125, 0846A, 1203, 0490A and 0490B. The method is F5: rolls read inward, so text-top is at low z iff `w * parity = +1`. The winding sense w is measured either:
- (a) along any mesh row spanning more than one turn (validated 36/36 on 0139); or
- (b) from the CT pitch angle (`tools/sib/handed/spiral_sense.py`): tested and REJECTED, see below.

The CT-only pitch-angle estimator was tested and REJECTED: on 0139 the per-slice scatter is about 20 times the signal (REPORT 12.2). So up/down on a null-flag volume is settled only by:
- (a) >= 2 frame-checked traces with a row spanning >= 1.05 turns, >= 200 pairs, pair agreement >= 0.8, a valid r_out, and agreement on w; or
- (b) the organizers filling `z_direction_is_top_to_bottom`.

Until then, both 180-degree candidates are shown. They are never mirror images of each other. Per-volume needs are in REPORT 12.3.
