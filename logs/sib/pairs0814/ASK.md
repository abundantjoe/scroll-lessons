Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814: open questions (work continues on the defaults)

Status 2026-09-25T19:37Z: stage A done for all 19 PHerc0814 segments; stage B 90 of 376 blocks (1536 px, 4 x 4
patches of 384 px) done, ~33 s per block (render 3 threads, pipelined with the 2.4 um range reads and gate), about
2.6 h left in this container. Per-segment blocks: 222237 16, 051122 65, 165636 33, 203608 29, 235953 71, 235954 1,
040153 10, 083742 23, 060526 28, 46527 (20260226000000) 3, 212701 7 left; five 2026 _abf/small segments have 0
candidate patches (0.2-0.3 cm^2 each; no 384 px patch reaches 90 % valid).
Split option: a sibling can take whole segments with tools/sib/pairs0814/stage_b.py <SEG_ID> (needs stage A outputs;
re-run stage_a.py <SEG_ID> first, ~5-20 min per segment). DEFAULT: no split; this session finishes all.

Q1 Patch and window geometry (DECL-D2 does not fix it). DEFAULT: 384 px patches on the 9.362 um canvas, stride 384 from
   the canvas origin, candidate if >= 90 % valid on both canvases; 3 x 3 windows of 128 px.
Q2 "align within 1 px". DEFAULT: integer NCC search +-3 px, 1-D parabolic refinement per axis, Euclidean norm <= 1.0,
   window needs >= 50 % both-valid pixels, a best shift on the search edge counts as not aligned.
Q3 "9 vs 2.4 um CT NCC". DEFAULT: render slice 15 (surface) vs organizer 2.399 um SV slice 54 of 109 (surface),
   exact area average onto the 9 um canvas, zero shift, both-valid pixels; slices 53-55 mean reported, not gating.
Q4 Stored depth. DEFAULT: render slices 5..25 of the -n 31 stack (the D3 pool window); all 31 reproducible from the
   registry crop and logged command.
Q5 Base papyrus and duplicates. DEFAULT: flagged, never dropped (CORR-RETRACE-RULE fail-closed form); the orchestrator
   decides exclusions and which member of each duplicate group to keep.
Q6 Shards on git. DEFAULT: all shards (20 patches, < 90 MB each, est. 1-1.5 GB total) pushed to this session branch in
   batches of <= ~500 MB; a refused push is recorded, not worked around.
