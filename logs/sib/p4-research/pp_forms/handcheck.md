# handcheck: contribution text
<!-- Numbers from sib-handed REPORT; re-check against the pp-handcheck README. 1447 results are flags, not errors. -->
handcheck predicts, from geometry alone, whether a tifxyz render will read mirrored, and which way is up.

(1) Data: organizer tifxyz meshes and metadata of PHerc0139, 0009B, 0841, 0800 and 1447, and the metadata of 26 volumes, all from the public open-data bucket.

(2) A mirrored render wastes ink detection and label transfer, and it is hard to spot on faint text. handcheck multiplies the mesh chirality, sign(det[∂P/∂u, ∂P/∂v, r_out]), by the frame parity from metadata.json. It cross-checks r_out from the official umbilicus, a CT-mask centroid and the mesh's own normal-line centre, and returns mirrored or unmirrored with a confidence level. Up/down is handled separately (z_direction_is_top_to_bottom).

(3) It gives a check that runs before any rendering.
- Synthetic scenes (69 tests): planted glyphs read unmirrored in 32/32 cases, and the wrong-sign controls come out mirrored in 32/32.
- Real meshes: every organizer mesh of 0139 (46), 0009B (18), 0841 (3) and 0800 (6) is predicted unmirrored as stored, under every independent r_out source.
- 9 of the 15 PHerc1447 meshes are flagged for review.
- Limitation: this is a geometric prediction, not a reading test.

(4) Evidence: synthetic and package test suites, a per-volume table, per-mesh votes, and a CLI over a folder of tifxyz. Code MIT.
