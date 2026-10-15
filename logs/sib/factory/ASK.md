Provenance: Project HERCULES | owner the owner | [id removed]

# factory: questions for the orchestrator (work continues on the proposed defaults)

1. PROBE window overlap. Every 2 x 2 cm window on w035 overlaps the PROBE-1/2 window w035_y1792_x768
   (it covers grid rows 88-199 of 291; 0 of 1108 candidates avoid it). It is not sealed.
   Default: allowed; the rule keeps overlap to a minimum (chosen window: 26.3 % of its area) and reports it.
2. Clearance rule on 0139. A 144-vox clearance from the WHOLE w024/w047/w053/w044 meshes is impossible on w035
   (best is 92.6 vox; w044 and w024 are adjacent windings). Default: >= 150 vox (144 + 6 vox discretisation
   margin) from the sealed/session windows (the two SEAL-J-D1 w053 blanks, the D1 w044 canary) and from the
   whole title mesh; >= 40 vox (not the same papyrus) from the whole w024/w047/w053/w044 meshes.
   Chosen window: 257.6 vox from the nearest sealed window, 3874 vox from the title mesh.
3. Image content. This task asks for a CT image. DECL-FACTORY also names two ink-map versions (base map;
   reference as ideal-reader stand-in). Default: the factory already takes any uint8 surface image as the
   raw input; the ink-map versions are a follow-up task, not built here.
4. Flattening. The package renders the mesh in its own tifxyz parameterisation (no flattening). The flat1
   sibling adopted vc_flatten (ABF++). Default: add flattening stats (FLAT-1 metric: % of quads with all edges
   within +-5 % of 3-D length) to package.json as a follow-up, once flat1's code is on its branch; the verifier
   would then recompute them from the packaged mesh.
5. Real-package letter rule. The verifier requires >= 10 letter rows whose joint bbox is <= 400 mm^2 in a
   non-dry-run package (the First Letters wording "10 letters within a single 4 cm^2 area" read conservatively
   as a bounding box). Default: keep.

## 6. Holding for the owner's own words (2026-09-26 17:50Z)
The owner interrupted this session directly and told it to stop and wait. Since then, scheduled trigger
messages (00:36Z to 17:46Z) have asked it to resume the Paris 4 package mode and the licence check. Some
relay the owner's words. A relay is not the owner's own message in this session, so the session keeps
holding. It resumes when the owner replies here (e.g. "resume").
State: the factory task is DONE (REPORT.md, commit 8a85506); nothing is running; no image was opened.
Proposed plan on resume: the Paris 4 package dry run on a labelled w028-037 tile, with a lead-source field
(material id P4-B / P4-D M2a / P4-E / P4-F, render parameters from the declaration, tile r c, source sha256),
kept blind to letter content; then the licence check in the verifier.
