# flatcheck: contribution text (form field "What is your contribution?")
<!-- Numbers from sib-flat1 REPORT (PHerc0139 bank meshes); re-check against the pp-flatcheck README before pasting. -->
flatcheck scores and repairs the 2-D flattening of tifxyz meshes.

(1) Data: organizer tifxyz meshes of PHerc0139 (38 segments at 9.362 µm; 5 at 2.399 µm) and small meshes of PHerc0800 and PHerc1447, from the public open-data bucket. Only mesh geometry and metadata.json are used.

(2) Every milestone prize requires "a low-distortion isometric 2D parametrization". flatcheck reports, per mesh or window:
- the % of quads whose edges are within ±5 % of true length;
- fold-overs;
- area and angle distortion.
It also flags ABF++ collapse, and re-flattens with SLIM or ARAP (libigl). Entrants can see, before rendering, where letters will be stretched.

(3) It shows a failure mode of the official flattener. On five random 4 cm² windows all methods pass: vc_flatten gets 98.6–99.7 % of quads within ±5 %. On the 10 most curved or least isometric 4 cm² windows of the PHerc0139 meshes, however, no method reaches 93.1 %:
- vc_flatten passes 0/10 (22–93 %);
- SLIM 3/10;
- ARAP 4/10.
ABF++ can collapse (22–34 %, UVs rescaled up to 3.4×, up to 12 flipped triangles). SLIM never flipped and scored at least as high as vc_flatten in 33/33 comparisons.

(4) Evidence: per-window metric tables with segment IDs and mesh sha256s, a complete run log including failures, and unit tests. Code MIT.
