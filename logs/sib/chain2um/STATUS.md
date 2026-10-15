Provenance: Project HERCULES | owner the owner | [id removed]

# chain2um status (2026-09-26 21:40Z)

- chain2um (2.4 um truth chain on CPU): DONE. See REPORT.md and chain2um_results.json.
- P4-O input support (DECL-P4-14 item 2): DONE at commit 1a00cd6 (p4o/README.md, p4o/manifest.json). It provides a streaming reader, a 108-tile hash manifest (r0-r5 x c0-c17) and a verification that the w010-027 2.4 um SV equals the official --flip-normals render (pooled r >= 0.999997; slab [23, 85) bit-identical).
- No resampled inputs are needed. The only eligible family (PHerc.1667, ckpt-screen-b) uses the native 2.4 um SV. ckpt-screen-b builds its own inputs (tools/sib/ckpt-screen-b/p4o_tiles.py at ca732ae): the same SV, the same slab 23..84, and HTTP byte-range reads of those 62 slices. Its slab is the one verified in p4o/verify_render.json. Its per-tile centre-ROI hashes can be cross-checked against p4o/manifest.json.
- Stopped; nothing running. No further chain2um work is queued.

Integrity: no issues.
